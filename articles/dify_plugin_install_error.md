---
title: "[Dify]openAIプラグイン インストールエラーを解決した話"
emoji: "🌺"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [Dify , AI, AWS , クラウド ,terraform]
published: true
---

## 問題の概要

Dify アプリケーションでプラグインシステムのエラーが発生していました。

```
plugin_unique_identifier is not valid:
```

このエラーが30秒間隔で継続的に発生し、OpenAI プラグインのインストールができない状態でした。

## 根本原因

**データベースとS3ストレージの不整合**

- データベースの `plugin_declarations` テーブルには OpenAI プラグインの宣言データが存在
- しかし、実際のプラグインファイルは S3 に存在しない
- プラグインデーモンが検証時にこの不整合を検出してエラーを発生

## 解決へのアプローチ
という事でDBをいじって不整合を治す方向で動く

### 1. CloudShell からの直接アクセス (失敗)

最初に CloudShell から RDS に直接アクセスを試みました。RDS セキュリティグループに CloudShell からのアクセスを許可するルールを追加しました。

```bash
# CloudShell のパブリック IP を確認
curl -s ifconfig.me
# → 203.0.113.0 (例)

# RDS セキュリティグループにルールを追加
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 5432 \
    --cidr 203.0.113.0/32

# CloudShell から DB 接続を試行
psql -h dify-dev-cluster.cluster-xxxxxxxxx.ap-northeast-1.rds.amazonaws.com -U dify -d dify
```

**エラーログ:**
```
psql: error: connection to server at "dify-dev-cluster.cluster-xxxxxxxxx.ap-northeast-1.rds.amazonaws.com" (10.1.xx.xxx), port 5432 failed: Connection timed out
	Is the server running on that host and accepting TCP/IP connections?
```

**失敗要因:**
- CloudShell の IP アドレスが頻繁に変更される
- VPC 内のプライベート RDS への直接アクセス制限
- CloudShell から VPC へのルーティングが確立されていない

### 2. ECS Exec を使用したコンテナアクセス (失敗)

次に 既に作ってあるDBと通信出来るECSの ECS Exec を有効にしてコンテナから直接 DB にアクセスを試みました。

```bash
# ECS セキュリティグループを確認
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx

# ECS Exec を有効にしてコンテナにアクセス
aws ecs execute-command \
    --cluster dify-dev \
    --task arn:aws:ecs:ap-northeast-1:xxxxxxxxxxxx:task/dify-dev/xxxxxxxxxxxxxxx \
    --container dify-api \
    --interactive \
    --command "/bin/bash"
```

**エラーログ:**
```bash
# コンテナ内で PostgreSQL クライアントをインストール試行
apt-get update && apt-get install -y postgresql-client
# → E: Unable to locate package postgresql-client

# Python経由でDB接続を試行
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='dify-dev-cluster.cluster-xxxxxxxxx.ap-northeast-1.rds.amazonaws.com',
    database='dify',
    user='dify',
    password='${DB_PASSWORD}'
)
"
# → psycopg2.OperationalError: connection to server at "dify-dev-cluster.cluster-xxxxxxxxx.ap-northeast-1.rds.amazonaws.com" (10.1.xx.xxx), port 5432 failed: Connection timed out

# ECS Exec 自体のエラー
The Session Manager plugin was installed successfully. Use the AWS CLI to start a session.

An error occurred (InvalidParameterException) when calling the ExecuteCommand operation: The execute command failed because execute command was not enabled when the task was run or the execute command agent isn't running.
```

**失敗要因:**
- ECS タスクで `enableExecuteCommand` が有効になっていない
- コンテナ内に PostgreSQL クライアントツールが存在しない
- ECS タスクの IAM 権限不足
- セキュリティグループの設定でもタイムアウトが発生

### 3. Terraform で踏み台 EC2 構築 (成功)

最終的に Terraform で踏み台 EC2 を構築し、Session Manager 経由でアクセスする方法で解決しました。

## 実装した解決策

### 踏み台 EC2 の構築

**bastion.tf**
```hcl
resource "aws_instance" "bastion" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  subnet_id     = data.aws_subnet.private_a.id
  vpc_security_group_ids = [aws_security_group.bastion.id]
  
  iam_instance_profile = aws_iam_instance_profile.bastion.name
  
  user_data = base64encode(templatefile("${path.module}/scripts/bastion_userdata.sh", {
    region = var.region
    env    = var.env
  }))
  
  tags = {
    Name = "dify-${var.env}-bastion"
  }
}

resource "aws_iam_role" "bastion" {
  name = "dify-${var.env}-bastion-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "bastion" {
  name = "dify-${var.env}-bastion-policy"
  role = aws_iam_role.bastion.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "rds:DescribeDBClusters",
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "bastion" {
  name = "dify-${var.env}-bastion-profile"
  role = aws_iam_role.bastion.name
}

resource "aws_iam_role_policy_attachment" "bastion_ssm" {
  role       = aws_iam_role.bastion.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
```

**security_groups.tf**
```hcl
resource "aws_security_group" "bastion" {
  name_prefix = "dify-${var.env}-bastion-"
  vpc_id      = data.aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "dify-${var.env}-bastion-sg"
  }
}
```

### 改良された UserData スクリプト

元の bastion_userdata.sh は psql クライアントが正しくインストールされない問題がありました。

**改良版 bastion_userdata.sh**
```bash
#!/bin/bash
yum update -y
yum install -y postgresql15 aws-cli

# DB接続スクリプト
cat > /home/ec2-user/connect_db.sh << 'SCRIPT'
#!/bin/bash
export ENV=${env}
export REGION=${region}

# DB接続情報を取得
DB_HOST=$(aws rds describe-db-clusters --region $REGION --db-cluster-identifier dify-$ENV-cluster --query 'DBClusters[0].Endpoint' --output text)
DB_PASSWORD=$(aws ssm get-parameter --region $REGION --name "/dify/$ENV/db/password" --with-decryption --query 'Parameter.Value' --output text)
DB_NAME=$(aws rds describe-db-clusters --region $REGION --db-cluster-identifier dify-$ENV-cluster --query 'DBClusters[0].DatabaseName' --output text)
DB_USER=$(aws rds describe-db-clusters --region $REGION --db-cluster-identifier dify-$ENV-cluster --query 'DBClusters[0].MasterUsername' --output text)

echo "Connecting to database..."
echo "Host: $DB_HOST"
echo "Database: $DB_NAME"
echo "User: $DB_USER"

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -p 5432
SCRIPT

chmod +x /home/ec2-user/connect_db.sh
chown ec2-user:ec2-user /home/ec2-user/connect_db.sh

# テーブルクリーンアップスクリプト
cat > /home/ec2-user/cleanup_plugins.sh << 'SCRIPT'
#!/bin/bash
export ENV=${env}
export REGION=${region}

# DB接続情報を取得
DB_HOST=$(aws rds describe-db-clusters --region $REGION --db-cluster-identifier dify-$ENV-cluster --query 'DBClusters[0].Endpoint' --output text)
DB_PASSWORD=$(aws ssm get-parameter --region $REGION --name "/dify/$ENV/db/password" --with-decryption --query 'Parameter.Value' --output text)
DB_NAME=$(aws rds describe-db-clusters --region $REGION --db-cluster-identifier dify-$ENV-cluster --query 'DBClusters[0].DatabaseName' --output text)
DB_USER=$(aws rds describe-db-clusters --region $REGION --db-cluster-identifier dify-$ENV-cluster --query 'DBClusters[0].MasterUsername' --output text)

echo "Cleaning up plugin tables..."

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -p 5432 << 'SQL'
-- すべてのプラグイン関連テーブルをクリーンアップ
DELETE FROM plugin_declarations;
DELETE FROM plugin_installations;
DELETE FROM plugins;
DELETE FROM account_plugin_permissions;

-- 結果の確認
SELECT 'plugin_declarations' as table_name, COUNT(*) as count FROM plugin_declarations
UNION ALL
SELECT 'plugin_installations' as table_name, COUNT(*) as count FROM plugin_installations
UNION ALL
SELECT 'plugins' as table_name, COUNT(*) as count FROM plugins
UNION ALL
SELECT 'account_plugin_permissions' as table_name, COUNT(*) as count FROM account_plugin_permissions;
SQL

echo "Plugin cleanup completed!"
SCRIPT

chmod +x /home/ec2-user/cleanup_plugins.sh
chown ec2-user:ec2-user /home/ec2-user/cleanup_plugins.sh
```

### セキュリティグループの設定

RDS セキュリティグループに踏み台サーバーからのアクセスを許可する設定を追加しました。

```bash
# 踏み台サーバーのプライベートIPを確認
aws ec2 describe-instances --instance-ids i-xxxxxxxxx --query 'Reservations[0].Instances[0].PrivateIpAddress'

# RDSセキュリティグループにルールを追加
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 5432 \
    --cidr 10.1.xx.xxx/32
```

## 解決手順

### 1. 踏み台サーバーへのアクセス

```bash
# Session Manager で踏み台サーバーにアクセス
aws ssm start-session --target i-xxxxxxxxx
```

### 2. データベースの状態確認

```bash
# データベースに接続
./connect_db.sh

# プラグインテーブルの状態確認
SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%plugin%';
```

### 3. 不整合データのクリーンアップ

```bash
# プラグインテーブルをクリーンアップ
./cleanup_plugins.sh
```

実行結果:
```sql
DELETE FROM plugin_declarations;
DELETE 4

DELETE FROM plugin_installations;
DELETE 0

DELETE FROM plugins;
DELETE 0

DELETE FROM account_plugin_permissions;
DELETE 0
```

### 4. ECS サービスの再起動

```bash
# 新しい設定でタスクを再起動
aws ecs update-service \
    --cluster dify-dev \
    --service dify-dev \
    --force-new-deployment
```

### 5. プラグインの再インストール

Dify の Web UI から OpenAI プラグインを再インストールしました。

## 結果

✅ **問題解決！**

- プラグインエラーが完全に解消
- OpenAI プラグインが正常にインストール
- データベースと S3 の整合性が保たれた状態

## 学んだこと

### 1. 直接アクセスの制限
- CloudShell や ECS Exec は環境によって制限が多い
- セキュリティグループやネットワークの設定だけでは解決しない場合がある

### 2. Infrastructure as Code の重要性
- Terraform で踏み台サーバーを構築することで、再現可能で管理しやすい
- 必要な権限やツールを事前に準備できる

### 3. プラグインシステムの仕組み
- データベースとファイルストレージの整合性が重要
- `PLUGIN_AUTO_INSTALL_BUILTIN` 設定の影響が大きい

### 4. トラブルシューティングのアプローチ
- 複数のアプローチを試して、最適な解決方法を見つける
- ログの詳細な分析が問題特定に重要

## 改善点

今後は以下の点を改善することで、同様の問題を予防できます：

1. **プラグインの整合性チェック機能の追加**
2. **データベース移行時の整合性確認**
3. **プラグインファイルの自動バックアップ**
4. **踏み台サーバーの常時稼働**

この問題解決により、Dify アプリケーションは正常に動作し、OpenAI プラグインも問題なく使用できるようになりました。
