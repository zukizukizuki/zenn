---
title: ' 【AWS】TerraformでECRの差分解消！state rmとimportで再作成を防ぐ方法'
private: false
tags:
  - terraform
  - aws
  - ECR
updated_at: '2025-06-01T01:52:59.181Z'
id: null
organization_url_name: null
slide: false
---

TerraformでECRを管理している際に、リソースに変更がないにもかかわらず再作成が求められる場合があります。ECRリポジトリの再作成は、既存のイメージ削除や意図しない影響を引き起こすため、事前に差分が出るはずのない状態を確認した上で、`state rm`と`import`を使って解決する方法を解説します。

## 前提条件の確認

ECRに差分が出る理由を確認するため、以下のようなログでECRの状態やTerraformの状態を確認します。これにより、差分が出るはずがない状態であることを確認します。

### 1. ECRのPlanのログ例

Terraformで`plan`を実行した際のログを確認します。差分がないにも関わらず、`create`アクションが出てしまう場合があります。

#### Planログ

```
# module.main.aws_ecr_repository.admin will be created
+ resource "aws_ecr_repository" "admin" {
    + arn                  = (known after apply)
    + id                   = (known after apply)
    + image_tag_mutability = "MUTABLE"
    + name                 = "dev-admin"
    + registry_id          = (known after apply)
    + repository_url       = (known after apply)
    + tags_all             = (known after apply)

    + encryption_configuration {
        + encryption_type = "AES256"
        + kms_key         = (known after apply)
      }

    + image_scanning_configuration {
        + scan_on_push = false
      }
  }
```

上記のように、ECRの設定に変更がないにもかかわらず、リポジトリが再作成されようとしています。

### 2. Terraformのstateリストでリソースの確認

次に、`terraform state list`コマンドで、Terraformが管理しているリソースの一覧を確認します。ECRリポジトリがすでにTerraformによって管理されているか確認します。

#### `terraform state list` のログ例

```
terraform state list

module.main.aws_ecr_repository.admin
module.main.aws_ecr_repository.device_data
module.main.aws_ecr_repository.irregularity_detection_api
module.main.aws_ecr_repository.lambda_webadapter
```

### 3. Terraformの状態を詳細に確認

特定のECRリポジトリについて、`terraform state show`コマンドを使用して、Terraformが認識しているリソースの状態を確認します。

#### `terraform state show` のログ例

```
terraform state show module.main.aws_ecr_repository.admin

# module.main.aws_ecr_repository.admin:
resource "aws_ecr_repository" "admin" {
    arn                  = "arn:aws:ecr:ap-northeast-1:123456789012:repository/dev-admin"
    id                   = "dev-admin"
    image_tag_mutability = "MUTABLE"
    name                 = "dev-admin"
    registry_id          = "123456789012"
    repository_url       = "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/dev-admin"
    tags                 = {}
    tags_all             = {}

    encryption_configuration {
        encryption_type = "AES256"
        kms_key         = null
    }

    image_scanning_configuration {
        scan_on_push = false
    }
}
```

### 4. AWS CLIでECRの状態を確認

AWS CLIを使用して、AWS側でECRリポジトリがどのような状態で存在しているか確認します。AWSとTerraformの状態が一致していることを確認することで、不要な再作成が発生しないことが期待できます。

#### AWS CLIでの確認例

```
aws ecr describe-repositories --repository-names dev-admin

{
    "repositories": [
        {
            "repositoryArn": "arn:aws:ecr:ap-northeast-1:123456789012:repository/dev-admin",
            "registryId": "123456789012",
            "repositoryName": "dev-admin",
            "repositoryUri": "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/dev-admin",
            "createdAt": 1726562681.161,
            "imageTagMutability": "MUTABLE",
            "imageScanningConfiguration": {
                "scanOnPush": false
            },
            "encryptionConfiguration": {
                "encryptionType": "AES256"
            }
        }
    ]
}
```

## 解決手順

ECRリポジトリの設定がAWS側とTerraform側で一致しているにもかかわらず、差分が生じて再作成が発生する場合は、`state rm`と`import`を使用して解決します。

### 1. TerraformのstateからECRリポジトリを一時的に削除

差分の解消に向けて、Terraformの管理状態からECRリポジトリを一時的に削除します。これにより、次のステップでAWS上の既存リポジトリを再インポートすることが可能になります。

#### `terraform state rm` の実行例

```
terraform state rm module.main.aws_ecr_repository.admin
```

### 2. AWS上のECRリポジトリをTerraformに再インポート

削除したECRリポジトリを`terraform import`を使って再度インポートします。これにより、Terraformの状態とAWSの実際の設定が同期され、不必要な差分が解消されます。

#### `terraform import` の実行例

```
terraform import module.main.aws_ecr_repository.admin arn:aws:ecr:ap-northeast-1:123456789012:repository/dev-admin
```

### 他のECRリポジトリに対する対応

複数のECRリポジトリを管理している場合も同様の手順で、`state rm`と`import`を用いて差分を解消できます。以下に複数のリポジトリに対する`state rm`と`import`の例を示します。

#### `state rm`と`import`の例

```
terraform state rm module.main.aws_ecr_repository.device_data
terraform import module.main.aws_ecr_repository.device_data arn:aws:ecr:ap-northeast-1:123456789012:repository/dev-device-data
```

## まとめ

以上の手順を通じて、TerraformでECRリポジトリの不要な再作成を防ぐことができました。`state rm`と`import`を活用することで、TerraformとAWSの状態を一致させ、予期しないリソースの変更を防ぐことが可能です。この手順を覚えておくことで、ECRの管理がよりスムーズになります。
