---
title: "TerraformでDify AIプラットフォームをAWSに構築する完全ガイド"
emoji: "👨‍✈️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [Dify , AI, AWS , クラウド]
published: true
---

## はじめに
この記事では、AIアプリケーション開発プラットフォーム「Dify」をAWS上にTerraformで構築する方法を詳しく解説します。実際のプロダクション環境で運用している構成をベースに、セキュリティ、可用性、コスト効率を両立した実装方法をお伝えします。
## Difyとは
DifyはオープンソースのAIアプリケーション開発プラットフォームで、LLMを活用したチャットボットやワークフローを直感的に構築できるツールです。
**主な特徴：**
- 🤖 ChatGPT、Claude、Geminiなど複数のLLMに対応
- 🔧 ノーコード/ローコードでAIアプリケーション構築
- 📊 チャット履歴や使用量の分析機能
- 🔌 API提供によるシステム連携
## アーキテクチャ設計
今回構築するインフラストラクチャは以下のような構成になります。
```
┌─────────────────┐
│   Internet      │
│   Gateway       │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Public ALB    │  ← 社内IP制限
│   (HTTPS Only)  │
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Private Subnet  │
│   EC2 + EBS     │  ← Docker Compose
│ (Session Mgr)   │
└─────────┬───────┘
          │
┌─────────▼───────┐
│  Dify Services  │
│ - Web UI(Nginx) │
│ - API Server    │
│ - PostgreSQL    │
│ - Redis         │
│ - Weaviate      │
└─────────────────┘
```
### 設計のポイント
**セキュリティ重視**
- プライベートサブネット配置でEC2への直接アクセスを制限
- 社内IPアドレスからのみALB経由でアクセス可能
- Session Managerによるセキュアなサーバーアクセス
**データ保護**
- EBSボリュームによるデータ永続化
- 暗号化済みストレージ
- インスタンス終了時もデータを保持
**可用性とコスト**
- 環境別のインスタンス構成（dev: 1台、prd: 2台マルチAZ）
- Auto Scaling対応の基盤設計
## Terraformモジュール実装
### ディレクトリ構造
```
terraform/
├── modules/
│   └── dify/
│       ├── main.tf          # メインリソース
│       ├── variables.tf     # 変数定義
│       ├── data.tf          # データソース
│       └── user_data.sh     # 初期化スクリプト
├── environments/
│   ├── dev/
│   ├── stg/
│   └── prd/
└── docs/
```
### メインリソース（main.tf）
まずは基本的なリソースを定義します。
```hcl
# セキュリティグループ設定
resource "aws_security_group" "dify_alb" {
  name_prefix = "dify-${var.env}-alb-"
  vpc_id      = data.aws_vpc.main.id
  # 社内IPからのHTTPS接続のみ許可
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = local.office_cidr_blocks
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_security_group" "dify_ec2" {
  name_prefix = "dify-${var.env}-ec2-"
  vpc_id      = data.aws_vpc.main.id
  # ALBからの80番ポートのみ許可
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.dify_alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```
### データ永続化設定
EC2のライフサイクルに依存しないデータ保存のため、EBSボリュームを利用します。
```hcl
# EBSボリューム作成
resource "aws_ebs_volume" "dify_data" {
  count             = var.instance_count
  availability_zone = count.index == 0 ? 
    data.aws_subnet.private_a.availability_zone : 
    data.aws_subnet.private_c.availability_zone
  size              = var.data_volume_size
  type              = "gp3"
  encrypted         = true
  tags = {
    Name = "dify-${var.env}-data-${count.index + 1}"
  }
}
# EC2インスタンス
resource "aws_instance" "dify" {
  count = var.instance_count
  
  subnet_id = count.index == 0 ? 
    data.aws_subnet.private_a.id : 
    data.aws_subnet.private_c.id
  launch_template {
    id      = aws_launch_template.dify.id
    version = "$Latest"
  }
  # UserData変更時の自動置換
  user_data_replace_on_change = true
  tags = {
    Name = var.instance_count > 1 ? 
      "dify-${var.env}-${count.index + 1}" : 
      "dify-${var.env}"
  }
}
# EBSボリュームアタッチ
resource "aws_volume_attachment" "dify_data" {
  count       = var.instance_count
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.dify_data[count.index].id
  instance_id = aws_instance.dify[count.index].id
}
```
### Application Load Balancer設定
```hcl
resource "aws_lb" "dify" {
  name               = "dify-${var.env}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.dify_alb.id]
  subnets            = data.aws_subnets.public.ids
  enable_deletion_protection = false
}
resource "aws_lb_target_group" "dify" {
  name     = "dify-${var.env}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.main.id
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/apps"  # Nginxリダイレクト対応
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 20
    unhealthy_threshold = 5
  }
}
# HTTPS リスナー
resource "aws_lb_listener" "dify_https" {
  count = var.certificate_arn != null ? 1 : 0
  
  load_balancer_arn = aws_lb.dify.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.dify.arn
  }
}
```
## UserDataスクリプトによる自動化
EC2起動時にDifyを自動インストールするスクリプトを作成します。
```bash
#!/bin/bash
# システム更新
yum update -y
# EBSボリューム検出・マウント
sleep 30
if ! lsblk | grep -q xvdf; then
    echo "Waiting for EBS volume..." >> /var/log/dify-install.log
    sleep 60
fi
# 初回時のみフォーマット
if ! file -s /dev/xvdf | grep -q filesystem; then
    echo "Formatting EBS volume..." >> /var/log/dify-install.log
    mkfs -t ext4 /dev/xvdf
fi
# マウント設定
mkdir -p /opt/dify-data
mount /dev/xvdf /opt/dify-data
echo '/dev/xvdf /opt/dify-data ext4 defaults,nofail 0 2' >> /etc/fstab
# データディレクトリ作成
mkdir -p /opt/dify-data/{postgres,redis,weaviate}
# Docker & Docker Compose インストール
amazon-linux-extras install docker -y
systemctl enable docker && systemctl start docker
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
# Difyセットアップ
mkdir -p /opt/dify && cd /opt/dify
git clone https://github.com/langgenius/dify.git .
# 環境設定
cp docker/.env.example docker/.env
sed -i 's/CONSOLE_WEB_URL=.*/CONSOLE_WEB_URL=${dify_url}/' docker/.env
sed -i 's/APP_WEB_URL=.*/APP_WEB_URL=${dify_url}/' docker/.env
# 永続ボリューム設定
cat > docker/docker-compose.override.yml << 'EOF'
version: '3'
services:
  db:
    volumes:
      - /opt/dify-data/postgres:/var/lib/postgresql/data
  redis:
    volumes:
      - /opt/dify-data/redis:/data
  weaviate:
    volumes:
      - /opt/dify-data/weaviate:/var/lib/weaviate
EOF
# 権限設定
chown -R ec2-user:ec2-user /opt/dify /opt/dify-data
# Dify起動
cd /opt/dify/docker
/usr/local/bin/docker-compose up -d
echo "Dify installation completed at $(date)" >> /var/log/dify-install.log
```
## 変数定義（variables.tf）
```hcl
variable "env" {
  type        = string
  description = "Environment name"
}
variable "vpc_name" {
  type        = string
  description = "VPC name"
}
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.medium"
}
variable "instance_count" {
  type        = number
  description = "Number of EC2 instances"
  default     = 1
}
variable "data_volume_size" {
  type        = number
  description = "EBS volume size in GB"
  default     = 20
}
variable "certificate_arn" {
  type        = string
  description = "SSL certificate ARN"
  default     = null
}
variable "zone_id" {
  type        = string
  description = "Route53 zone ID"
  default     = null
}
variable "common_office_ip_list" {
  type        = map(list(string))
  description = "Office IP addresses for ALB access"
  default = {
    office_a = ["xxx.xxx.xxx.xxx/32"]
    office_b = ["yyy.yyy.yyy.yyy/32"]
  }
}
```
## 環境別設定
### 開発環境（dev）
```hcl
module "dify" {
  source = "../modules/dify"
  
  env                   = "dev"
  vpc_name              = "development-vpc"
  private_subnet_name_a = "private-subnet-a"
  private_subnet_name_c = "private-subnet-c"
  instance_type         = "t3.medium"
  # instance_count はデフォルト(1)を使用
  certificate_arn       = "arn:aws:acm:ap-northeast-1:xxxxxxxxxxxx:certificate/xxxxxxxx"
  zone_id               = "Z123456789ABCDEFGH"
  zone_name             = "dev.example.com"
}
```
### 本番環境（prd）
```hcl
module "dify" {
  source = "../modules/dify"
  
  env                   = "prd"
  vpc_name              = "production-vpc"
  private_subnet_name_a = "private-subnet-a"
  private_subnet_name_c = "private-subnet-c"
  instance_type         = "t3.large"
  instance_count        = 2  # マルチAZ構成
  data_volume_size      = 50
  certificate_arn       = "arn:aws:acm:ap-northeast-1:xxxxxxxxxxxx:certificate/xxxxxxxx"
  zone_id               = "Z987654321ZYXWVUTSR"
  zone_name             = "example.com"
}
```
## デプロイ手順
### 1. 初期化とプランニング
```bash
# Terraform初期化
terraform init
# 実行計画の確認
terraform plan -var-file="environments/dev/terraform.tfvars"
```
### 2. デプロイ実行
```bash
# 開発環境デプロイ
terraform apply -var-file="environments/dev/terraform.tfvars"
# アクセス確認
curl -I https://dify-dev.example.com
```
## 運用・監視
### ログ確認
```bash
# EC2にSession Manager経由で接続
aws ssm start-session --target i-xxxxxxxxxxxx
# インストールログ確認
sudo tail -f /var/log/dify-install.log
# Docker状況確認
sudo docker ps
sudo docker logs dify-web-1
```
### ヘルスチェック
```bash
# ALBターゲット状況確認
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:xxxxxxxxxxxx:targetgroup/dify-dev-tg/xxxxxxxxxxxxxxxx
```
### バックアップ
```bash
# EBSスナップショット作成
aws ec2 create-snapshot \
  --volume-id vol-xxxxxxxxxxxx \
  --description "Dify backup $(date +%Y%m%d_%H%M%S)"
```
## トラブルシューティング
### 502 Bad Gateway エラー
**原因1: セキュリティグループ設定ミス**
ALBからEC2への通信が80番ポートで許可されているか確認：
```bash
# セキュリティグループ確認
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxxxxxxxx \
  --query 'SecurityGroups[0].IpPermissions'
```
**原因2: Docker起動失敗**
EC2内でDocker状況を確認：
```bash
sudo docker ps -a
sudo docker logs dify-nginx-1
# 必要に応じてディスククリーンアップ
sudo docker system prune -a -f
```
### アクセス権限エラー
Session Managerでの接続確認：
```bash
# IAMロール確認
aws sts get-caller-identity
# Session Manager接続テスト
aws ssm start-session --target i-xxxxxxxxxxxx
```
## セキュリティ考慮事項
### ネットワークセキュリティ
1. **社内IP制限**: ALBレベルで特定IPからのみアクセス許可
2. **プライベート配置**: EC2はプライベートサブネットに配置
3. **最小権限**: 必要最小限のポート開放
### データセキュリティ
1. **EBS暗号化**: データ保存時の暗号化
2. **強力なSecret Key**: 自動生成による推測困難なキー
3. **アクセスログ**: ALBでのアクセスログ記録（オプション）
## コスト最適化
### インスタンスサイジング
| 環境 | インスタンス | 台数 | 月額概算 |
|------|-------------|------|---------|
| dev | t3.medium | 1台 | $30 |
| stg | t3.medium | 1台 | $30 |
| prd | t3.large | 2台 | $120 |
### ストレージコスト
- EBS gp3 20GB: 約$2/月
- スナップショット: 使用量に応じて従量課金
### 運用コスト削減のヒント
```bash
# 開発環境の夜間停止（自動化例）
aws ec2 stop-instances --instance-ids i-xxxxxxxxxxxx
# 不要なDockerイメージクリーンアップ
sudo docker system prune -a -f
```
## 今後の改善案
### 短期的改善
1. **監視強化**: CloudWatch Logsへのログ集約
2. **アラート設定**: ALBエラー率・レスポンス時間監視
3. **Auto Scaling**: トラフィック増加への自動対応
### 長期的改善
1. **コンテナ化**: EKSへの移行検討
2. **データベース分離**: RDS/ElastiCacheの利用
3. **Multi-Region**: 災害対策としての複数リージョン展開
## まとめ
この記事では、TerraformによるDify AIプラットフォームのAWS構築方法を解説しました。
**実現したポイント：**
- ✅ 完全自動化されたデプロイメント
- ✅ セキュアなネットワーク設計
- ✅ データ永続化による障害対策
- ✅ 環境別の最適なリソース配分
- ✅ 運用コストの最適化
この構成により、AI開発チームは素早く安全にDify環境を立ち上げ、AIアプリケーション開発に集中できるようになります。
皆さんもぜひこの構成を参考に、自社のAI基盤構築にチャレンジしてみてください！
---
**参考リンク：**
- [Dify公式サイト](https://dify.ai/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)