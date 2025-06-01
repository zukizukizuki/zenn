---
title: '【MYSQL】Failed to connect to database: (1045, "Access denied for user が出る'
tags:
  - AWS
  - RDS
  - error
private: false
updated_at: '2024-09-06T15:14:55+09:00'
id: b0b7c0bd2b58fdb0e01f
organization_url_name: null
slide: false
ignorePublish: false
---
## エラーログ
```
Failed to connect to database: (1045, "Access denied for user 'dev_admin'@'172.31.1.129' (using password: YES)")
```

## 原因
このエラーは、データベースユーザー名またはパスワードが正しくない場合に発生します。

## 対処方法
1. AWS Secrets Managerの確認
   - Secrets Managerに保存されているユーザー名とパスワードが正しいか確認
   - 必要に応じて、以下のようにTerraformコードを修正:
   ```
   resource "aws_secretsmanager_secret_version" "db_credential" {
     secret_id = aws_secretsmanager_secret.db_credential.id
     secret_string = jsonencode({
       username = "${var.environment}_${var.DB_USERNAME}"
       password = var.DB_PASSWORD
     })
   }
   ```

2. RDSインスタンスでのユーザー確認
   - RDSインスタンスに直接接続し、ユーザーが正しく作成されているか確認
   - 必要に応じて、以下のSQLコマンドでユーザーを作成または権限を付与:
   ```
   CREATE USER 'dev_admin'@'%' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON *.* TO 'dev_admin'@'%';
   FLUSH PRIVILEGES;
   ```

3. Lambda関数の環境変数確認
   - Lambda関数の環境変数が正しく設定されているか確認
   - Terraformコードで以下のように設定されていることを確認:
   ```
   resource "aws_lambda_function" "db_dump" {
     # 他の設定...
     environment {
       variables = {
         RDS_USER     = "${var.environment}_${var.DB_USERNAME}"
         RDS_PASSWORD = var.DB_PASSWORD
         # 他の環境変数...
       }
     }
   }
   ```
