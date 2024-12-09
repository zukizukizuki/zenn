---
title: "Terraform Stateで\"unsupported attribute\" エラーが発生した際の対処方法"
emoji: "🔥"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , Github , terraform]
published: false
---

## 問題の背景
Terraformでリソースを `terraform state rm`（stateファイルからリソースを除去）しようとした際、以下のようなエラーが発生することがあります。

```
Error saving the state: unsupported attribute "metrics_config"

The state was not saved. No items were removed from the persisted
state. No backup was created since no modification occurred. Please
resolve the issue above and try again.
```

このエラーは、Terraformの状態ファイルに現在使用しているProviderやTerraformバージョンではサポートされていない属性（例：`metrics_config`）が残っている場合に起こります。

## 対処手順

### **ProviderやTerraformを最新版にアップデート**
   不要または非対応な属性が新バージョンで取り除かれている場合があります。
   ```
   terraform init -upgrade
   terraform plan
   ```

   上記コマンドでProviderやTerraform本体を最新化し、状態とコードの整合性を確認します。

### **問題のリソースを先に削除**
   `metrics_config`など問題を引き起こしているリソースを先に `terraform state rm` で削除します。
   たとえば、`aws_lambda_event_source_mapping.my_lambda_event` が原因の場合：
   ```
   terraform state rm module.xyz.aws_lambda_event_source_mapping.my_lambda_event
   ```

   これでエラーが解消され、他のリソースを削除できるようになる場合があります。

### **再度該当リソースを削除**
   問題リソースを取り除いた後、`terraform state rm`を再度実行して、残りの削除対象リソースを正常に除去できるか試します。
   例えば：
   ```
   terraform state rm module.xyz.aws_s3_bucket.example_bucket
   terraform state rm module.xyz.aws_s3_bucket_lifecycle_configuration.example_lifecycle
   ```

### **手動でStateファイルを修正（最終手段）**
   上記方法で解決できない場合は、状態ファイルを手動で編集します。
   ```
   terraform state pull > state.json
   ```

   `state.json`をエディタで開き、`metrics_config`等の該当属性を削除してください。その後、
   ```
   terraform state push state.json
   ```
   で修正した状態ファイルを反映します。

## 対処結果の例

以下は、Providerアップデート後に問題リソースを削除し、他のリソースも正常に削除できるようになった例です。

```
terraform init -upgrade
terraform state rm module.xyz.aws_lambda_event_source_mapping.my_lambda_event
terraform state rm module.xyz.aws_s3_bucket.example_bucket
terraform state rm module.xyz.aws_s3_bucket_lifecycle_configuration.example_lifecycle
...
```

このように、Providerのアップデートと問題リソースの事前除去によって、`unsupported attribute`エラーを回避し、Terraformの状態ファイルを正常な状態に戻すことができます。
