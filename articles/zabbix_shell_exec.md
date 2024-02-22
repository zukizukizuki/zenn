---
title: "zabbix で監視対象側のshell scriptを実行した結果を取得する方法"
emoji: "👮"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [zabbix , linux , apache , Bash , ShellScript ]
published: true
---

## 概要
zabbixで柔軟な監視をするためにshell scriptを実行してその値を取得したい時がある。
最終的にshell scriptで取得した値はトリガーにかけてその値によってアラートをあげる事になるが今回はzabbix agent 経由で監視対象サーバ内にあるshell scriptを実行する方法まで説明します。

## 前提
### zabbix server
OS : Ubuntu 22.04
Version : 6.4

### 監視対象
OS : Ubuntu 22.04
zabbix-agent2

## scriptを実行する監視対象側の設定
1. zabbix agent でscriptを実行出来る様に以下の記述を **/etc/zabbix/zabbix_agent2.conf** に記載する。

```
AllowKey=system.run[*]
```

2. 対象のscriptを入れる **zabbix** ユーザーのhomeディレクトリに作る。
今回は **sh** という名前のディレクトリを作ります。

```
mkdir /home/zabbix/sh
```

3. scriptを2で作ったディレクトリに作る。

```
sudo vim /home/zabbix/sh/your_script.sh
```

4. scriptに実行権限を付与する。

```
sudo chmod +x /home/zabbix/sh/your_script.sh
```

5. scriptのownerをzabbixに変える。

```
sudo chmod +x /home/zabbix/sh/your_script.sh
```

## zabbix サーバ側の設定

1. ブラウザからzabbixを開き監視対象で **アイテムの作成** を実行
![](https://storage.googleapis.com/zenn-user-upload/9cb532385deb-20240222.png)

2. **キー** に 以下を指定し、必須項目を入力する事でアイテムがscript実行後の値を取得してくれる
```
system.run[~/sh/your_script.sh]
```
![](https://storage.googleapis.com/zenn-user-upload/799050f17a2b-20240222.png)

## 終わりに
後はscriptで取得した値をトリガーにかけてアラート発報するなりすれば幸せになれます。