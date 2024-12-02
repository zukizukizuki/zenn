---
title: "Terraformでリソースを`import`ブロックなしでインポートする方法"
emoji: "🧹"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , GitHub Actions, Github , terraform]
published: true
---

Terraform v1.5.0以降では、`terraform plan --generate-config-out`を使用することで、従来の`terraform import`コマンドや[importブロック](https://zukkie.link/terraform%e3%81%a7%e3%83%ad%e3%83%bc%e3%82%ab%e3%83%ab%e3%81%8b%e3%82%89import%e3%81%99%e3%82%8b%e6%96%b9%e6%b3%95/)を使用せずに、リソースをTerraform管理下にインポートできる機能が追加されました。この方法では、直接リソースのARNやIDをリソースブロック内に記載し、設定を生成することができます。

## 手順

### 1. リソースブロックの定義
対象リソースのARNまたはIDを使用して、Terraformファイル内に以下のようなリソースブロックを記述します。

```
resource "aws_lambda_function" "event_call_cloud_workflows" {
  arn = "arn:aws:lambda:ap-northeast-1::function:"
}

resource "aws_security_group" "example_sg" {
  id = ""
}
```

### 2. 設定の自動生成
次に、`terraform plan --generate-config-out`コマンドを実行してリソースの設定を自動生成します。

コマンド例:

```
terraform plan --generate-config-out imported_resources.tf
```

このコマンドを実行すると、指定したファイル（例: `imported_resources.tf`）に対象リソースの設定が自動生成されます。

## 利点
1. 従来の`terraform import`コマンドを使用せず、一括で複数リソースの設定を生成できる。
2. 生成された設定をそのまま利用することで、手動でのリソース記述を省略できる。

## 注意事項
- 生成された設定には不要な属性や追加修正が必要な場合があるため、必ず確認して適切に修正してください。
- この機能はTerraform v1.5.0以降で使用可能です。


## 関連リンク
公式ドキュメントや実装例については以下を参照してください:
- [Terraform v1.5.0 リリースノート](https://www.hashicorp.com/releases)
- [Terraform Import機能の詳細](https://developer.hashicorp.com/terraform/cli/import)
