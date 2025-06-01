---
title: "ubuntuにsquidをinstallしてLinuxとブラウザからインターネットアクセス"
emoji: "🦑"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [ubuntu , linux, squid, proxy, apt]
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
UbuntuにSquidをインストールしてLinuxとブラウザからインターネットアクセスする方法

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

## クライアント側の設定

### Google Chrome
1. Google Chromeを開き、右上のメニューアイコン（3つの点）をクリックします。
2. メニューから「設定」を選択します。
3. 下にスクロールし、"プライバシーとセキュリティ"を展開し、「セキュリティ」を選択します。
4. 「プロキシを変更する」をクリックします。
5. プロキシ設定のウィンドウが開きますので、手動でプロキシを設定します。
6. 設定を保存してウィンドウを閉じます

### Mozilla Firefox
1. Mozilla Firefoxを開き、右上のメニューアイコン（3つの水平な線）をクリックします。
2. メニューから「設定」を選択します。
3. 左側のサイドバーで「一般」を選択します。
4. 下にスクロールし、"ネットワーク設定"のセクションで「設定...」ボタンをクリックします。
5. プロキシ設定のウィンドウが開きますので、「手動でプロキシを設定する」を選択し、アドレスとポートを入力します。
6. 必要に応じて、ネットワーク設定を使用するにチェックを入れます。
7. 「OK」をクリックして設定を保存し、ウィンドウを閉じます。

### Microsoft Edge
1. Microsoft Edgeを開き、右上の「...」アイコンをクリックします。
2. メニューから「設定」を選択します。
3. 左側のメニューから「プライバシー、検索、およびサービス」を選択します。
4. 下にスクロールし、「プロキシ」のセクションで「プロキシ設定の変更」をクリックします。
5. 「手動でプロキシを設定する」を選択し、アドレスとポートを入力します。
6. 必要に応じて、プロキシ設定をオンまたはオフに切り替えます。

### linux 環境変数の設定
一部のLinuxシステムでは、プロキシサーバーの設定に関連する環境変数を設定する必要があります。
これには、http_proxyおよびhttps_proxy変数が含まれます。squidのデフォルトポートの**3128**を指定してます。

```
export http_proxy=http://<SquidサーバーのIP>:3128
export https_proxy=http://<SquidサーバーのIP>:3128
```

### aptの設定

apt.confファイルにProxy設定を追加する
シェルにて以下を実行

```
sudo vim /etc/apt/apt.conf
```
これにより開いたapt.confファイルに以下を記述し、保存
※ファイルがなかったら新規作成する

```/etc/apt/apt.conf
Acquire::http::Proxy "http://<SquidサーバーのIP>:3128";
Acquire::https::Proxy "http://<SquidサーバーのIP>:3128";
```

これで、LinuxマシンおよびブラウザからSquidを経由してインターネットにアクセスする準備が整いました。
実際にapt installやブラウザでのインターネットアクセスが出来るはずです。

### dockerの設定

**systemctl edit docker**　で設定ファイルを開いて以下を追記する

```/etc/systemd/system/docker.service.d/override.conf
[Service]
Environment = 'http_proxy=http://192.168.0.10:8080' 'https_proxy=http://192.168.0.10:8080' # 必要なら 'no_proxy=...'
```

**~/.docker/config.json** を以下の様に編集する。なければ作る。

```~/.docker/config.json
{
  "proxies": {
    "default": {
      "httpProxy": "http://192.168.0.10:8080",
      "httpsProxy": "http://192.168.0.10:8080"
    }
  }
}
```

参考：https://qiita.com/dkoide/items/ca1f4549dc426eaf3735

## 結論
UbuntuにSquidをインストールして設定し、Linuxマシンおよびブラウザからインターネットにアクセスする方法を解説しました。
Squidのようなproxyを使うことで、ネットワーク内の通信を効率的に管理し、セキュリティを向上させることができます。
