---
title: 【AWS】Lambdaを使ってRDSのdumpファイルをS3に保存する
private: false
tags:
  - aws
  - lambda
  - RDS
  - dump
  - S3
updated_at: '2025-06-01T01:52:44.498Z'
id: null
organization_url_name: null
slide: false
---

以下の手順で、LambdaとRDSを同一VPCに配置し、S3にデータベースのdumpファイルを保存する環境を構築します。

## 前提条件

- AWS CLIがインストールされ、適切に設定されていること（バージョン2.0以上推奨）
- Terraformがインストールされていること（バージョン1.0以上推奨）
- Python 3.8以上がインストールされていること（Lambda関数の開発用）

## 手順

### VPCの設定

既存のVPCを使用するか、新しいVPCを作成します。VPCには少なくとも2つのサブネット（プライベートサブネット）が必要です。

Terraformを使用してVPCを作成する例：

```
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "main-vpc"
  }
}

resource "aws_subnet" "private_1" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-west-2a"

  tags = {
    Name = "Private Subnet 1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.2.0/24"
  availability_zone = "us-west-2b"

  tags = {
    Name = "Private Subnet 2"
  }
}
```

### S3バケットの作成

データベースダンプを保存するためのS3バケットを作成します。

Terraformを使用してS3バケットを作成する例：

```
resource "aws_s3_bucket" "db_dump" {
  bucket = "my-db-dump-bucket"

  tags = {
    Name = "DB Dump Bucket"
  }
}

resource "aws_s3_bucket_public_access_block" "db_dump" {
  bucket = aws_s3_bucket.db_dump.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### VPCエンドポイントの設定

S3へのアクセスを可能にするため、VPCエンドポイントを作成します。

```
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.us-west-2.s3"
}

resource "aws_vpc_endpoint_route_table_association" "private_s3" {
  route_table_id  = aws_route_table.private.id
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
}
```

### RDSインスタンスの設定

VPC内のプライベートサブネットにRDSインスタンスを作成します。

```
resource "aws_db_instance" "default" {
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  storage_type         = "gp2"
  db_name              = "mydb"
  username             = "admin"
  password             = "password" # 注意: 本番環境では安全な方法で管理してください
  parameter_group_name = "default.mysql8.0"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.default.name

  skip_final_snapshot = true
}

resource "aws_db_subnet_group" "default" {
  name       = "main"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "My DB subnet group"
  }
}
```

### Lambda関数の作成

データベースダンプを実行し、S3にアップロードするLambda関数を作成します。この関数もVPC内のプライベートサブネットに配置します。
※lambdaレイヤーを設定し、pymysqlを使えるようにする必要があります。([手順](https://zukkie.link/%e3%80%90aws%e3%80%91lambda%e3%83%ac%e3%82%a4%e3%83%a4%e3%83%bc%e3%81%ae%e4%bd%9c%e6%88%90%e3%81%a8%e3%82%a2%e3%83%83%e3%83%97%e3%83%ad%e3%83%bc%e3%83%89%e6%89%8b%e9%a0%86/))

Lambda関数の Python コード例（`lambda_function.py`）：

```
import boto3
import pymysql
import os
from datetime import datetime

def lambda_handler(event, context):
    # RDS接続情報
    rds_host  = os.environ['RDS_HOST']
    db_name = os.environ['DB_NAME']
    user = os.environ['DB_USER']
    password = os.environ['DB_PASSWORD']
    
    # S3バケット名
    s3_bucket = os.environ['S3_BUCKET']
    
    # 現在の日時を取得
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d-%H-%M-%S")
    
    # ダンプファイル名
    dump_file = f"/tmp/dump-{date_string}.sql"
    
    # MySQLデータベースに接続
    conn = pymysql.connect(host=rds_host, user=user, passwd=password, db=db_name, connect_timeout=5)
    
    try:
        with conn.cursor() as cur:
            # ダンプコマンドを実行
            cur.execute(f"SELECT * INTO OUTFILE '{dump_file}' FROM your_table")
        
        # S3クライアントを作成
        s3 = boto3.client('s3')
        
        # ダンプファイルをS3にアップロード
        s3.upload_file(dump_file, s3_bucket, f"dumps/dump-{date_string}.sql")
        
        print(f"Database dump uploaded to s3://{s3_bucket}/dumps/dump-{date_string}.sql")
        
    finally:
        conn.close()
        
    return {
        'statusCode': 200,
        'body': 'Database dump completed successfully'
    }
```

### IAMロールの設定

Lambda関数用のIAMロールを作成し、必要な権限（RDSアクセス、S3アクセス、VPC内でのネットワーキング）を付与します。

```
resource "aws_iam_role" "lambda_role" {
  name = "lambda_db_dump_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "lambda_s3_access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.db_dump.arn,
          "${aws_s3_bucket.db_dump.arn}/*"
        ]
      }
    ]
  })
}
```

### セキュリティグループの設定

LambdaとRDS用のセキュリティグループを作成し、必要な通信を許可します。

```
resource "aws_security_group" "lambda" {
  name        = "lambda_sg"
  description = "Security group for Lambda function"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name        = "rds_sg"
  description = "Security group for RDS instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
}
```

### Lambda関数のデプロイ

作成したLambda関数をデプロイします。

```
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "lambda_function.py"
  output_path = "lambda_function.zip"
}

resource "aws_lambda_function" "db_dump" {
  filename      = "lambda_function.zip"
  function_name = "db_dump_function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"

  vpc_config {
    subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      RDS_HOST     = aws_db_instance.default.endpoint
      DB_NAME      = aws_db_instance.default.db_name
      DB_USER      = aws_db_instance.default.username
      DB_PASSWORD  = aws_db_instance.default.password
      S3_BUCKET    = aws_s3_bucket.db_dump.id
    }
  }
}
```

### スケジューリングの設定（オプション）

定期的なダンプ実行のため、Amazon EventBridgeを使用してLambda関数をスケジュールします。

```
resource "aws_cloudwatch_event_rule" "daily_db_dump" {
  name                = "daily-db-dump"
  description         = "Trigger DB dump Lambda function daily"
  schedule_expression = "cron(0 1 * * ? *)"  # 毎日午前1時（UTC）に実行
}

resource "aws_cloudwatch_event_target" "db_dump_lambda" {
  rule      = aws_cloudwatch_event_rule.daily_db_dump.name
  target_id = "TriggerLambdaFunction"
  arn       = aws_lambda_function.db_dump.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.db_dump.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_db_dump.arn
}
```

## 最後に

- VPC内でのリソース配置により、インターネットアクセスが制限されます。必要に応じてNATゲートウェイを設定してください。
- RDSインスタンスのバックアップ方法として、このアプローチを使用する場合は、整合性とパフォーマンスに注意してください。大規模なデータベースの場合、ダンプ中にデータベースがロックされる可能性があります。
- 大規模なデータベースの場合、Lambda関数のタイムアウト設定（デフォルトは3秒）と割り当てメモリ（最小128MB、最大10,240MB）を調整する必要があります。
- ダンプファイルの保管期間や、S3のライフサイクルポリシーの設定を検討してください。長期保存が不要な場合は、古いダンプファイルを自動的に削除するポリシーを設定することをお勧めします。
- 本番環境では、データベースのパスワードなどの機密情報をAWS Secrets Managerなどのサービスを使用して安全に管理することを強く推奨します。
