---
title: "windows で SSM がインストールされている端末にportforwardする"
emoji: "🦴"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [windows , linux, AWS , SSM]
published: true
---

## 概要
windows で SSM がインストールされている端末にportforwardする
linux はSSMでRDPがサポートされていないのでlinuxにRDPしたい時とかに使う

## 前提
- linuxの場合、対象サーバにXRDPがインストールされている
- 対象サーバにSSM Agentが入っている
- 対象サーバがインターネットに接続できる

## 手順

1. AWS CLI install ※してない場合のみ
https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/getting-started-install.html

2. アクセスキー作成 ※してない場合のみ
aws ログイン→セキュリティ認証情報→アクセスキー→作成
※secretは作成直後しか確認出来ないので漏洩しない場所に保存してください。"

3. aws configureコマンドでAWS接続設定 ※してない場合のみ
アクセスキーとregionを入力すればOK

4. セッションマネージャープラグインのインストール ※してない場合のみ
https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/install-plugin-windows.html"

5. ポートフォワーディング
コマンドプロンプトで以下のコマンドを実行する
```
aws ssm start-session --target $インスタンスID --document-name AWS-StartPortForwardingSession --parameters "portNumber=3389, localPortNumber=13389"
```

6. RDPを開き以下を入力しアクセスし認証情報を入力
localhost:13389"

## 備考
- 認証後すぐRDPが落ちる場合は対象サーバ内で以下のコマンドを実行してgnomeセッションを一旦KILLする
```
pkill gnome-session
```

- 重い場合はRDPの設定で画面を小さくして色の深度も浅くしてください
