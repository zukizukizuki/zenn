---
title: 【AWS】amplifyでreactアプリをデプロイしたが404エラー
private: false
tags:
  - aws
  - amplify
  - react
updated_at: '2025-06-01T01:52:36.782Z'
id: null
organization_url_name: null
slide: false
---

## 概要
掲題の通りamplifyを使ってreactをデプロイしたが実際にアクセスすると404エラーになる。

## エラーが再現する手順
1. gihubリポジトリを作成
2. 作ったリポジトリをgit clone
3. cloneしたリポジトリ内で以下のコマンドを実行
```
npx create-react-app amplifyapp
```
4. git add .
5. git commit -m "コメント"
6. git push origin main
7. AWSコンソールからamplifyを開いてgithubからデプロイ

その際の`amplify.yml`

```
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd amplifyapp
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: build
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

## 原因
`baseDirectory: build` となっており`amplifyapp/build`と階層構造で指定してなくてbuildしたリソースが使われてなかった。

修正後の`amplify.yml`
```
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd amplifyapp
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: amplifyapp/build
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

これでURLからreactアプリが見れるようになった。