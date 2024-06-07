---
title: "github actions で OIDCでAWSを認証しようとしたらエラーがNot authorized to perform"
emoji: "🐺"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , GitHub Actions, Github , OIDC]
published: true
---

## 概要
以下の記事を参考にgithub actions で OIDCでAWSを認証しようとしたら以下のエラー
```
Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

## 解決策
以下の部分が良くなかった

```
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
```

**信頼されたエンティティ**を以下に修正

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
原因は後日調査