---
title: 'Terraform importブロックでError: Too many command line argumentsが出る'
private: false
tags:
  - AWS
  - GitHub Actions
  - Github
  - terraform
updated_at: '2025-06-01T01:53:15.481Z'
id: null
organization_url_name: null
slide: false
---

## 概要

以下のimportブロックで

```
import {
  to = aws_iam_openid_connect_provider.github_actions_cicd_provider
  id = "arn:aws:iam::${var.AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
}
```

以下のコマンドを実行すると
```
terraform plan -generate-config-out=generated.tf
```

以下のエラーが出てしまう
```
terraform plan -generate-config-out=generated.tf
╷
│ Error: Too many command line arguments
│
│ To specify a working directory for the plan, use the global -chdir flag.
╵

For more help on using this command, run:
  terraform plan -help
```

## 解決策
VScodeでpowershellだと発生する事象なのでCMDを使う

## 参考
https://github.com/hashicorp/terraform-provider-aws/issues/31978
