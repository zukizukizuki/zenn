---
title: AWS SSMを使ってオンプレミスのlinuxを管理する
private: false
tags:
  - linux
  - AWS
  - ssm
updated_at: '2025-06-01T01:53:14.482Z'
id: null
organization_url_name: null
slide: false
---

## 概要
以前まで特定の端末にアクセスするための中継役となる踏み台サーバを
使用するのが一般的でしたが実装コスト、管理コスト、セキュリティ面から
現在ではAWS SSMが使われています。

今回はオンプレミスのlinuxをSSMの管理対象としてRDPするところまで説明します。

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

2. 該当するディストリビューションで以下の「項番3」を実行する
https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/sysman-install-managed-linux.html

### インスタンス名の変更(必要な場合のみ)

1. AWSへアクセス
2. AWS Systems Manager を押下
3. **ノード管理 > フリートマネージャー** を押下
4. 対象のノードIDを押下
5. **ノードアクション > ノード設定 > タグの追加** から以下の形式でタグを作成する

```
キー：Name 値：インスタンス名
```
