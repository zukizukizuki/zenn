---
title: "【AWS】Parameter Store を使用して機密情報を terraform で安全に管理する方法"
emoji: "🐫"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , Parameter Store, Systems Manager , セキュリティ ,terraform]
published: true
---

AWS インフラストラクチャを Terraform で管理する際、データベースのパスワードや API キーなどの機密情報を安全に扱うことは非常に重要です。今回は、AWS Systems Manager Parameter Store を使用して機密情報を SecureString として保存し、それを Terraform で取得および復号化する方法を紹介します。

## 前提
- AWSアカウントを持っている
- AWS CLIをインストールしている
- terraform をインストールしている

## 1. Parameter Store に機密情報を SecureString として保存

まず、AWS CLI を使用して Parameter Store に機密情報を SecureString として保存します。以下のコマンドを実行してください：

```
aws ssm put-parameter --name "/app/database/password" --type "SecureString" --value "your-secret-password" --description "Database password for the application"
```

`your-secret-password` を実際の機密情報（この例ではデータベースパスワード）に置き換えてください。

## 2. Terraform で Parameter Store から SecureString を取得し復号化

次に、Terraform の設定ファイル（例：`main.tf`）に以下のコードを追加して、Parameter Store から機密情報を取得し、復号化します：

```
data "aws_ssm_parameter" "db_password" {
  name = "/app/database/password"
  with_decryption = true
}

locals {
  database_password = data.aws_ssm_parameter.db_password.value
}
```

ここでの重要なポイントは `with_decryption = true` の設定です。これにより、Terraform は自動的に SecureString パラメータを復号化します。

## 3. 取得した値の使用例

復号化された機密情報を使用する場面で、以下のように `local.database_password` を参照できます：

```
resource "aws_db_instance" "example" {
  engine         = "mysql"
  engine_version = "5.7"
  instance_class = "db.t3.micro"
  username       = "admin"
  password       = local.database_password

  # その他の設定...
}
```

## なぜ Secrets Manager を使わないのか？

AWS Secrets Manager も機密情報管理のための優れたサービスですが、Parameter Store にはいくつかの利点があります：

1. コスト効率：
   Parameter Store は基本的に無料で使用できます（高度なパラメータには少額の料金がかかります）。一方、Secrets Manager はストアされている秘密ごとに料金が発生します。

2. 単純さ：
   Parameter Store はより単純で、学習曲線が緩やかです。基本的な機密情報の保存と取得には十分な機能を提供しています。

3. 統合の容易さ：
   多くの AWS サービスが Parameter Store と直接統合されており、設定が簡単です。

4. 汎用性：
   Parameter Store は機密情報だけでなく、設定データなど様々な種類のデータを保存できます。これにより、一つのサービスで多様なデータ管理ニーズに対応できます。

5. 既存のインフラとの互換性：
   多くの既存のインフラストラクチャやツールが Parameter Store をサポートしており、移行が容易です。

ただし、自動ローテーションや詳細なバージョニングが必要な場合は、Secrets Manager の使用を検討する価値があります。プロジェクトの要件、予算、既存のインフラストラクチャに基づいて、適切なサービスを選択することが重要です。