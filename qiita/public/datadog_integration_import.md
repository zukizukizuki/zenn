---
title: Datadog AWSインテグレーションを Terraform import する手順
private: false
tags:
  - terraform
  - datadog
  - AWS
  - CI/CD
  - CloudFormation
updated_at: '2025-06-01T01:52:53.640Z'
id: null
organization_url_name: null
slide: false
---

このドキュメントでは、既存のDatadog AWSインテグレーション設定をTerraformで管理するために、`terraform import` コマンドを使用する手順を詳細に解説します。

**背景**
Terraform importは、既にDatadog上で手動またはCloudFormationなどで設定済みのAWSインテグレーションを、Terraformの管理下に取り込む際に使用します。これにより、インフラ構成をコードとして管理し、変更履歴の追跡や自動化が可能になります。

**前提条件**

* **Terraform CLI のインストール:** Terraform CLI がインストールされている必要があります。
* **Datadog Terraform Provider の設定:** Terraform設定ファイル (`.tf`) に Datadog Provider の設定 (`provider "datadog"`) が記述済みであること。APIキーとアプリケーションキーが環境変数または変数で設定されていること。
* **Datadog APIキーとアプリケーションキー:** Datadog API にアクセスするための APIキーとアプリケーションキーが必要です。Organization Settings > API Keys / Application Keys で確認または生成してください。
* **AWSアカウントID:** Terraform import 対象の AWS アカウントID を把握している必要があります。
* **Datadog インテグレーション IAMロール名:** Datadog AWSインテグレーションで作成した IAMロールの名前 (`DatadogIntegrationRole` など) を把握している必要があります。
* **Datadog インテグレーション External ID:** CloudFormation スタックの出力などから、Datadog AWSインテグレーションの External ID を把握している必要があります。

**手順**

1. **Terraform 設定ファイル (`.tf`) の準備:**

   Terraform import を実行する前に、Terraform 設定ファイル (`.tf`) に `datadog_integration_aws` リソースブロックを **空で定義** しておきます。

   ```terraform
   resource "datadog_integration_aws" "aws_integration" {
     # このリソースブロックは空で開始します (設定は import 後に記述します)。
   }
   ```

   * `datadog_integration_aws`: リソースタイプ
   * `aws_integration`: リソース名 (任意。`terraform import` コマンドで指定するアドレスと一致させる)

2. **環境変数の設定:**

   ターミナル (または PowerShell) で、Datadog APIキーとアプリケーションキーを環境変数として設定します。

   **Linux/macOS の場合:**

   ```bash
   export DATADOG_API_KEY="YOUR_DATADOG_API_KEY"  # ← 実際のAPIキーに置き換え
   export DATADOG_APP_KEY="YOUR_DATADOG_APP_KEY"  # ← 実際のアプリケーションキーに置き換え
   ```

   **PowerShell の場合:**

   ```powershell
   $env:DATADOG_API_KEY = "YOUR_DATADOG_API_KEY" # ← 実際のAPIキーに置き換え
   $env:DATADOG_APP_KEY = "YOUR_DATADOG_APP_KEY" # ← 実際のアプリケーションキーに置き換え
   ```

   * `YOUR_DATADOG_API_KEY` と `YOUR_DATADOG_APP_KEY` は、実際のDatadog APIキーとアプリケーションキーに置き換えてください。

3. **`terraform import` コマンドの実行:**

   環境変数を設定したターミナル (または PowerShell) で、以下の `terraform import` コマンドを実行します。

   ```bash
   terraform import datadog_integration_aws.aws_integration <AWSアカウントID>:<IAMロール名>
   ```

   * `datadog_integration_aws.aws_integration`: Terraform設定ファイルで定義したリソースアドレス
   * `<AWSアカウントID>`: Terraform import 対象の AWS アカウントID に置き換えてください (例: `545009854777`)
   * `<IAMロール名>`: Datadog インテグレーション IAMロール名 (`DatadogIntegrationRole` など) に置き換えてください。

   **例:**

   ```bash
   terraform import datadog_integration_aws.aws_integration 545009854777:DatadogIntegrationRole
   ```

   または、`EXTERNAL_ID` 環境変数を使用する方法 (Datadog公式ドキュメント推奨):

   ```bash
   export EXTERNAL_ID="YOUR_EXTERNAL_ID" # ← 実際の External ID に置き換え
   terraform import datadog_integration_aws.aws_integration <AWSアカウントID>:<IAMロール名>
   ```

   * `YOUR_EXTERNAL_ID` は、実際の External ID に置き換えてください。

4. **`terraform plan` の実行と設定の確認:**

   `terraform import` コマンドが成功したら、`terraform plan` コマンドを実行し、インポートされた設定内容を確認します。

   ```bash
   terraform plan
   ```

   `terraform plan` の出力で、`datadog_integration_aws.aws_integration` リソースが Terraform state ファイルに追加されたことが示されます。

5. **Terraform コードに設定を記述:**

   `terraform plan` の出力や、Datadog Web UI (Integrations > AWS > [対象アカウント] > Metric Collection など) の設定を確認し、`integration.tf` ファイルの `datadog_integration_aws.aws_integration` リソースブロックに、必要な属性 (`account_id`, `role_name`, `metrics_collection_enabled`, `account_specific_namespace_rules` など) を記述します。

   Datadog Terraform Provider のドキュメント ( https://registry.terraform.io/providers/DataDog/datadog/latest/docs/resources/integration_aws ) を参照し、適切な属性と値を設定してください。

   **例:**

   ```terraform
   resource "datadog_integration_aws" "aws_integration" {
     account_id = "YOUR_AWS_ACCOUNT_ID" # 実際の AWS アカウントID に置き換え
     role_name  = "DatadogIntegrationRole" # 実際の IAMロール名 に置き換え

     metrics_collection_enabled = true
     excluded_regions         = ["ap-southeast-2", "ca-central-1"]

     account_specific_namespace_rules = {
       "AWS/ApiGateway" = true
       "AWS/EC2"        = true
       # ... 他のサービス ...
     }

     resource_collection_enabled = false
     cspm_resource_collection_enabled = false
   }
   ```

6. **`terraform apply` の実行:**

   Terraform コードに設定を記述したら、再度 `terraform plan` を実行して変更内容を確認し、問題なければ `terraform apply` コマンドを実行して設定を適用します。

   ```bash
   terraform apply
   ```

**トラブルシューティング**

* **`Error: resource address "datadog_integration_aws.aws_integration" does not exist in the configuration.` エラー:**
    * Terraform 設定ファイル (`.tf`) に `datadog_integration_aws` リソースブロックが定義されているか確認してください (手順 1)。
* **`Error: error importing aws integration resource. Resource with id \`...\` does not exist` エラー:**
    * `terraform import` コマンドで指定した AWSアカウントID または IAMロール名 が正しいか、Datadog Web UI と照らし合わせて確認してください。
    * Datadog APIキーとアプリケーションキーが正しいか、有効期限切れになっていないか確認してください。
    * Datadog API へのネットワーク接続に問題がないか確認してください (ファイアウォール、プロキシなど)。
* **`Error: error updating AWS integration from /api/v1/integration/aws: 400 Bad Request: {"errors":["Additional properties are not allowed ... "]}` エラー:**
    * `account_specific_namespace_rules` で指定しているサービス名が、Datadog API が認識する正しい名前空間と一致しているか確認してください。
    * Datadog API の利用可能な名前空間リスト (`https://api.datadoghq.com/api/v2/integration/aws/available_namespaces`) を取得し、Terraform コードのサービス名と突き合わせて、スペルミスや大文字小文字の違いがないか確認してください。

**注意事項**

* **APIキーとアプリケーションキーの保護:** APIキーとアプリケーションキーは機密情報です。Terraform Cloud の変数機能や、HashiCorp Vault などのシークレット管理ツールを使用して安全に管理することを推奨します。
* **Terraform State ファイルの管理:** Terraform State ファイルはインフラの状態を記録する重要なファイルです。リモートのストレージ (S3など) で適切にバックアップ・管理し、ロック機構を導入することを推奨します。
* **`external_id` の手動設定:** `datadog_integration_aws` リソースの `external_id` は、Terraform で自動生成されません。CloudFormation スタックの出力などから取得した値を、Terraform コードに手動で設定する必要があります。
* **`import` ブロックは Terraform v1.5 以降:** `import` ブロックを使用する場合は、Terraform v1.5 以降が必要です。古いバージョンの Terraform を使用している場合は、`terraform import` コマンドを使用してください。

**まとめ**

この手順に従うことで、既存のDatadog AWSインテグレーション設定をTerraformに取り込み、コードとして管理を開始できます。Terraform を活用することで、Datadogの設定変更を安全かつ効率的に行うことが可能になります。
