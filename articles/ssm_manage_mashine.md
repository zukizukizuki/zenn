---
title: "AWS SSMを使ってオンプレミスのwindowsを管理する"
emoji: "⛷️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [windows , windows_server, AWS , ssm]
published: true
---

## 概要
以前まで特定の端末にアクセスするための中継役となる踏み台サーバを
使用するのが一般的でしたが実装コスト、管理コスト、セキュリティ面から
現在ではAWS SSMが使われています。

今回はオンプレミスのwindowsをSSMの管理対象としてRDPするところまで説明します。

## 手順

### アクティベーションの設定

1. AWSへアクセス
2. AWS Systems Manager を押下
3. **ノード管理 > ハイブリッドアクティベーション** を押下
4. **アクティベーションを作成する** を押下
5. 必要項目を設定する

- アクティベーションの説明
  - 説明を記載します。(optional)
- インスタンス制限
  - SSM管理下にしたいインスタンスの数を記載
- アクティベーションの有効期限
  - このアクティベーションの有効期限。期限が切れると登録できなくなる。(空白は1日後になる)
- デフォルトのインスタンス名
  - コンソールに表示される名前(optional)

6. ポップアップが表示されるので"activation-code" と "activation-id" をメモする。
　 ※ポップアップ以外では二度と確認出来ないので注意

### SSM Agentを対象端末にインストールする

公式手順：https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/sysman-install-managed-win.html

1. プロキシ変数の設定

HTTP プロキシサーバーの場合は、次の変数を設定します。
```
http_proxy=http://hostname:port
https_proxy=http://hostname:port
```

HTTPS プロキシサーバーの場合は、次の変数を設定します。
```
http_proxy=http://hostname:port
https_proxy=https://hostname:port
```

2. 管理者権限でWindows PowerShell を開く
3. 以下のコマンドを実行する

```
$code = **"activation-code"**
$id = **"activation-id"**
$region = **"region"**
$dir = $env:TEMP + "\ssm"
New-Item -ItemType directory -Path $dir -Force
cd $dir
(New-Object System.Net.WebClient).DownloadFile("https://amazon-ssm-$region.s3.$region.amazonaws.com/latest/windows_amd64/AmazonSSMAgentSetup.exe", $dir + "\AmazonSSMAgentSetup.exe")
Start-Process .\AmazonSSMAgentSetup.exe -ArgumentList @("/q", "/log", "install.log", "CODE=$code", "ID=$id", "REGION=$region") -Wait
Get-Content ($env:ProgramData + "\Amazon\SSM\InstanceData\registration")
Get-Service -Name "AmazonSSMAgent"
```

エラーが出た場合は以下を参照してください。
https://zukkie.link/1000-2/#toc2

### RDPの有効にする

1. 対象のwindows端末で 設定 > システム > リモートデスクトップ
2. リモートデスクトップを有効にする

### インスタンス名の変更(必要な場合のみ)

1. AWSへアクセス
2. AWS Systems Manager を押下
3. **ノード管理 > フリートマネージャー** を押下
4. 対象のノードIDを押下
5. **ノードアクション > ノード設定 > タグの追加** から以下の形式でタグを作成する

```
キー：Name 値：インスタンス名
```
