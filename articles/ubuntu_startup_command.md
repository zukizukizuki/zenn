---
title: "Ubuntu 22.04で起動時に特定のコマンドを実行する方法"
emoji: "🐊"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [windows , windows_server, AWS , ssm]
published: true
---

## 概要

Ubuntu 22.04で起動時に特定のコマンドを実行したい場合、いくつかの方法があります。ここでは、最も一般的な方法である/etc/rc.localファイルにコマンドを記述する方法を紹介します。

## 手順

1. ターミナルを開きます。
2. 以下のコマンドを実行して、nanoエディタで**/etc/rc.local**ファイルを開きます。

```
sudo nano /etc/rc.local
```
3. ファイル末尾に、実行したいコマンドを記述します。

```
# ↓実行したいコマンドの例
route add -host 192.168.10.10 gw 10.100.140.2
route add -host 192.168.10.12 gw 10.100.140.2
route add -host 192.168.10.13 gw 10.100.140.2

export http_proxy=http://192.168.10.13:8080/
export https_proxy=http://192.168.10.13:8080/
```


4. ファイルを保存して閉じます。

```
CtrlキーとXキーを同時に押します。
保存の確認メッセージが表示されるので、Yキーを押します。
Enterキーを押します。
```
5. システムを再起動します。

6. システムを再起動後、コマンドが実行されたかどうかを確認するには、以下のコマンドを実行します。

```
tail -n 10 /var/log/syslog
```

## 注意事項

**/etc/rc.local**ファイルは、すべてのユーザーが実行できる権限を持っています。そのため、このファイルに記述するコマンドは、セキュリティ上のリスクがないことを確認する必要があります。
複雑なコマンドを実行する場合は、シェルスクリプトを作成して、そのスクリプトを/etc/rc.localファイルから実行することをおすすめします。


## 参考記事
Ubuntuで起動時に自動でShellScriptを実行する方法
Qiita: https://qiita.com/MAI_onishi/items/74edc40a667dd2dc633e
