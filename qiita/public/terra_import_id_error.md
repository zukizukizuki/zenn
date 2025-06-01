---
title: TerraformのIDプロバイダのimportでexpected "url" to have a hostが出る
private: false
tags:
  - AWS
  - GitHub Actions
  - Github
  - terraform
updated_at: '2025-06-01T01:53:15.979Z'
id: null
organization_url_name: null
slide: false
---

## 概要
以下のterraformのimportブロックを書く
```
resource "aws_iam_openid_connect_provider" "github_actions_cicd_provider" {
  client_id_list  = ["sts.amazonaws.com"]
  tags            = {}
  tags_all        = {}
  thumbprint_list = ["1b511abead59c6ce207077c0bf0e0043b1382612"]
  url             = "token.actions.githubusercontent.com"
}

import {
  to = aws_iam_openid_connect_provider.github_actions_cicd_provider
  id = "arn:aws:iam::${var.AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
}
```

するとIDプロバイダのimportで次のエラーが発生する場合があります。

```
Error: expected "url" to have a host, got token.actions.githubusercontent.com
│  ...
│  445:   url = "token.actions.githubusercontent.com"
```

## 解決策
このエラーを解決するために、URLに https:// を追加します。

```
resource "aws_iam_openid_connect_provider" "github_actions_cicd_provider" {
  client_id_list  = ["sts.amazonaws.com"]
  tags            = {}
  tags_all        = {}
  thumbprint_list = ["1b511abead59c6ce207077c0bf0e0043b1382612"]
  url             = "https://token.actions.githubusercontent.com"
}
```

## 参考
https://github.com/hashicorp/terraform-provider-aws/issues/26483