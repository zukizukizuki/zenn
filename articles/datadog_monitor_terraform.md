---
title: "Datadog モニターを Terraform で管理するための import 手順"
emoji: "🐾"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [terraform , datadog, monitor , 自動化]
published: true
---

# Datadog モニターを Terraform で管理するための import 手順

## Terraform ログイン

まず、Terraform Cloud にログインします（Terraform Cloud を使用している場合）

```bash
terraform login
```

## import ブロックの作成
適切な Terraform 設定ファイル(例:main.tf) import ブロックを作成します。

```hcl
import {
  to = datadog_monitor.url_access_check
  id = "${monitorのID}"
}
```

## Terraform 設定ファイルの生成
以下のコマンドを実行して、既存のリソースに基づいて Terraform 設定ファイルを生成します。

```bash
terraform plan -generate-config-out=generated.tf
```

このコマンドにより、generated.tf ファイルが作成され、インポートされるリソースの設定が含まれます。

## 生成された設定の確認と調整
generated.tf ファイルの内容を確認し、必要に応じて調整します。リソース名、パラメータ、その他の設定が正しいことを確認。

## Terraform plan の実行
変更内容を確認するために、Terraform plan を実行します。

```bash
terraform plan
```

出力を確認し、予期しない変更がないことを確認します。

## Terraform apply の実行
問題がなければ、変更を適用します。

```bash
terraform apply
```

確認プロンプトが表示されたら、yes と入力して実行を続行します。

## 確認
適用が完了したら terraform show コマンドを使用して、Terraform の状態ファイルに正しくリソースが追加されていることを確認できます。

```
terraform show
```