---
title: WSL上のLinuxのバックアップとリストア
private: false
tags:
  - linux
  - wsl
  - bash
  - windows
updated_at: '2025-06-01T01:53:19.996Z'
id: null
organization_url_name: null
slide: false
---

## 概要
WSL上のLinuxのバックアップとリストアの手順を残します。

## 前提
以下の通りVersion2で実施します。

```
C:\Windows\System32>wsl -l -v
  NAME      STATE           VERSION
* Ubuntu    Running         2

C:\Windows\System32>
```

## 手順

### wsl上のLinuxのエクスポート

#### コマンド使用方法
`wsl --export ${ディストリビューション名} ${exportするbackup fileのフルパス}`

#### コマンド例
`wsl --export Ubuntu C:\Users\asaka\Downloads\backup_20231024.tar`

### エクスポート確認
`dir C:\Users\asaka\Downloads\`

### リストア

#### コマンド使用方法
`wsl --import ${ディストリビューション名} ${インストール先パス} ${exportしたbackup fileのフルパス}`

#### コマンド例
`>wsl --import Ubuntu-restore-test C:\Users\asaka\OneDrive\Documents\WSL-OS\Ubuntu C:\Users\asaka\Downloads\backup_20231024.tar`

#### 備考
- ${ディストリビューション名}が重複すると以下のメッセージが出るので一意の名前にする。
```
C:\Windows\System32>wsl --import Ubuntu C:\Users\asaka\OneDrive\Documents\WSL-OS\Ubuntu C:\Users\asaka\Downloads\wsl_no2_backup_20231024.tar
指定された名前のディストリビューションは既に存在します。
C:\Windows\System32>
```

### importの確認
問題なくimport出来れば${インストール先パス}にDiskファイルが出来ている事と
`wsl -l`で${ディストリビューション名}が出来ている事を確認する。

```
C:\Windows\System32>wsl -l
Linux 用 Windows サブシステム ディストリビューション:
Ubuntu (既定)
Ubuntu-restore-test

C:\Windows\System32>
```

### 規定のディストリビューションの指定
リストアしたディストリビューションを既定に設定する。

#### コマンド使用方法
`wsl --set-default ${ディストリビューション名}`

#### コマンド例
`wsl --set-default Ubuntu-restore-test`

#### 確認
```
C:\Windows\System32>wsl --list
Linux 用 Windows サブシステム ディストリビューション:
Ubuntu-restore-test (既定)
Ubuntu

C:\Windows\System32>
```

### 規定のユーザーをrootユーザーから変更する(rootユーザーのみ使うなら不要)
上記の手順でリストアしたディストリビューションは規定のユーザーがrootユーザーとなる。
既定のユーザーを一般ユーザーで運用するのであれば以下の対応が必要。

1. ログイン(この時点ではrootユーザーで実行される)
`wsl -d ${ディストリビューション名}`

2. sudoerの準備とユーザーの準備

```
apt update -y && apt install passwd sudo -y
myUsername=${ユーザー名}
adduser -G wheel $myUsername
echo -e "[user]\ndefault=$myUsername" >> /etc/wsl.conf
passwd $myUsername
```

3. wslから抜ける
`exit`コマンドで抜ける

4. wsl 落とす

#### コマンド使用方法
`wsl --terminate ${ディストリビューション名}`

#### コマンド例
`wsl --terminate Ubuntu-restore-test`

5. wsl 立ち上げる

#### コマンド使用方法
`wsl -d ${ディストリビューション名}`

#### コマンド例
`wsl -d Ubuntu-restore-test`

#### 参考
https://learn.microsoft.com/ja-jp/windows/wsl/use-custom-distro#add-wsl-specific-components-like-a-default-user

#### 備考
本件の場合`規定のディストリビューションの指定`を実行しただけで
`Ubuntu-restore-test`の既定のユーザーでログインされることを確認したので不要の可能性もある。

## 参考
https://www.aise.ics.saitama-u.ac.jp/~gotoh/HowToBackupLinuxOnWSL.html