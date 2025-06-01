---
title: TerraformでローカルからImportする方法
private: false
tags:
  - AWS
  - GitHub Actions
  - Github
  - terraform
updated_at: '2025-06-01T01:53:16.477Z'
id: null
organization_url_name: null
slide: false
---

## 概要

Terraformを使ってTerraform Cloudで管理しているStateファイルをローカルからterraform importする手順を以下に説明します。

## 手順

### 1. Terraformにログイン

stateはterraform cloud で管理しているのでCMDで以下のコマンドを実行しプロンプトに従ってログインを実施

```
terraform login
```

2. AWS CLIを設定

実際にAWSリソースを触るのでCMDで以下のコマンドを実行しアクセスキーとシークレットアクセスキーを登録する

```
aws configure
```

3. importブロックを作成
次のようにimportブロックを作成します。
例としてIDプロバイダとロールをimportします。

```
import {
  to = aws_iam_openid_connect_provider.github_actions_cicd_provider
  id = "arn:aws:iam::***:oidc-provider/token.actions.githubusercontent.com"
}

import {
  to = aws_iam_role.github_actions_cicd_role
  id = "github-actions-cicd-role"
}
```

4. 設定ファイルを生成

```
terraform plan -generate-config-out=generated.tf
```

5. Terraformプランの確認

```
terraform plan
```
※IDプロバイダをimportする際に以下のエラーが出る可能性がある
https://zukkie.link/%e3%80%90terraform%e3%80%91id%e3%83%97%e3%83%ad%e3%83%90%e3%82%a4%e3%83%80%e3%81%aeimport%e3%81%a7expected-url-to-have-a-host%e3%81%8c%e5%87%ba%e3%82%8b/

6. Terraform適用
```
terraform apply
```

以上の手順で、Terraform Cloudで管理されているStateファイルをローカルからインポートすることができます。
