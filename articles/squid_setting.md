---
title: "ubuntuにsquidをinstallしてLinuxとブラウザからインターネットアクセス"
emoji: "🪮"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [windows , windows_server, AWS , SSM]
published: true
---

## 概要
閉鎖環境でもaptを使いたかったり、インターネットにアクセスしたい場合がある。
そんな時はsquidというproxyサーバが広く利用されている。
今回の記事では以下の方法を説明する。
- ubuntu に squidをinstallしてproxyサーバ構築
- Linux からproxy経由でインターネットアクセス
- ブラウザ からproxy経由でインターネットアクセス

## proxyサーバ設定

おっしゃる通りです。Linux環境でSquidを使用する場合、aptの設定や環境変数の設定が必要です。以下に、その手順を追加した修正版の記事を示します。

UbuntuにSquidをインストールしてLinuxとブラウザからインターネットアクセスする方法
この記事では、UbuntuにSquidをインストールして、Linuxマシンおよびブラウザからインターネットアクセスをする方法について解説します。Squidは、プロキシサーバーとして広く使われており、ネットワーク内のコンピューターがインターネットにアクセスする際の通信をキャッシュし、効率的に管理することができます。

1. Squidのインストール
まず、UbuntuにSquidをインストールします。ターミナルを開き、以下のコマンドを実行します。

```
sudo apt update
sudo apt install squid
```

2. Squidの設定
Squidを設定して、インターネットアクセスを可能にします。Squidのメイン設定ファイルである/etc/squid/squid.confを編集します。

```
sudo vim /etc/squid/squid.conf
```

設定ファイル内で、適切な箇所に以下のような設定を追加します。ここでは、特定のIPアドレス（例: 192.168.1.100）だけを許可します。

```
# 特定のIPアドレスからの接続のみ許可する
acl allowed_ip src 192.168.1.100
http_access allow allowed_ip
http_access deny all
```

設定を保存してエディターを終了します。

3. Squidの再起動
設定を反映させるために、Squidを再起動します。

```
sudo systemctl restart squid
```

4. ブラウザの設定
ブラウザからSquidを利用するために、プロキシ設定を行います。
ブラウザを開き、設定メニューを選択します。
プロキシ設定の項目を探し、手動でプロキシを設定します。
プロキシサーバーのアドレスには、UbuntuサーバーのIPアドレスを入力します。デフォルトのポートは3128です。

5. linux CLIの設定
一部のLinuxシステムでは、プロキシサーバーの設定に関連する環境変数を設定する必要があります。
これには、http_proxyおよびhttps_proxy変数が含まれます。


```
export http_proxy=http://<SquidサーバーのIP>:3128
export https_proxy=http://<SquidサーバーのIP>:3128
```
これで、LinuxマシンおよびブラウザからSquidを経由してインターネットにアクセスする準備が整いました。

## 結論
UbuntuにSquidをインストールして設定し、Linuxマシンおよびブラウザからインターネットにアクセスする方法を解説しました。
Squidのようなproxyを使うことで、ネットワーク内の通信を効率的に管理し、セキュリティを向上させることができます。
