---
title: "【AWS】SSMで管理しているEC2にportforwardしてローカルからRDSに接続する"
emoji: "🕸️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , SSM, mysql, RDS , EC2]
published: true
---

## 概要
下図の通りEC2 にSSM agentをinstallしてそこから繋ぐことが出来るRDSにローカルアクセスします。

![](https://storage.googleapis.com/zenn-user-upload/394a17b598e8-20240709.png)

## 前提
- EC2 に SSM agentをinstall 済
- EC2 から RDSにアクセス出来るVPC設定
- RDS は パスワードで管理
- ローカルではGUIツールを使用(この記事ではHeidiSQL)

## 手順
1. EC2のinstance-IDを確認する

2. portforwardを実施

windows
```
aws ssm start-session ^
--target i-xxxxx ^
--document-name AWS-StartPortForwardingSessionToRemoteHost ^
--parameters "{\"portNumber\":[\"3306\"],\"localPortNumber\":[\"3306\"],\"host\":[\"rds-dev.xxxxx.ap-northeast-1.rds.amazonaws.com\"]}" ^
--profile iamuser-xxxxx
```

mac
```
aws ssm start-session \
--target i-xxxxx \
--document-name AWS-StartPortForwardingSessionToRemoteHost \
--parameters '{"portNumber":["3306"],"localPortNumber":["3306"],"host":["rds-dev.xxxxx.ap-northeast-1.rds.amazonaws.com"]}' \
--profile iamuser-xxxxx
```


3. RDSにアクセス

以下の値を入力し、「開く」

|項目|値|
|----|----|
|ネットワーク種別|MariaDB or MySQL(TCP/IP)|
|ホスト名/IP|localhost|
|ユーザー|${user名}|
|パスワード|${パスワード}|
|ポート|3306|

![](https://storage.googleapis.com/zenn-user-upload/3629e29a85f3-20240709.png)

## 参考

https://blog.serverworks.co.jp/ssm-session-manager-rds