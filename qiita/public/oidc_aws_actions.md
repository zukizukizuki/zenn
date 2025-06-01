---
title: github actions で OIDCでAWSを認証しようとしたらエラーがNot authorized to perform
private: false
tags:
  - AWS
  - GitHub Actions
  - Github
  - OIDC
updated_at: '2025-06-01T01:53:07.423Z'
id: null
organization_url_name: null
slide: false
---

## 概要
[この記事](https://zenn.dev/kou_pg_0131/articles/gh-actions-oidc-aws)を参考にgithub actions で OIDCでAWSを認証しようとしたら以下のエラー
```
Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

## 解決策
以下の部分が良くなかった

```
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                }
```

IAMロールの**信頼されたエンティティ**を以下に修正

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::${AWSアカウント}:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:${githubリポジトリ}:*"
                }
            }
        }
    ]
}
```

## 最後に
このポリシー条件は、GitHub Actionsから送られたOIDCトークンの aud クレームが sts.amazonaws.com と等しい場合にのみ、sts:AssumeRoleWithWebIdentity アクションを許可するという意味です。これにより、トークンが確かにAWSのSTSを対象として発行されたものであることを確認しています。

aud クレームは、トークンが使用されるべき対象（オーディエンス）を示します。

それが異なっていた？