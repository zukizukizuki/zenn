---
title: "ubuntu22.04 LTSへxrdpでログイン出来なかったけど解決した話"
emoji: "🌍"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [ubuntu , linux , xrdp , Bash , ShellScript ]
published: true
---

## 概要
ubuntuでもGUIを操作したくてxrdpをインストールしたが上手くいかなかった時の対処法と備忘録

## 前提
### 接続先
OS : Ubuntu 22.04 LTS
xrdp Version : 0.9.23.1

### 接続元
OS : Windows 11 home
クライアント : RDP

## xrdpと.xsession-errorsのログの確認

### 1. xrdpログの確認

#### 確認手順：

1. SSHを使用してUbuntuサーバーに接続します。
2. xrdpのログファイルを確認します。
```bash
   sudo less /var/log/xrdp.log
```

#### xrdpログの内容：
```
[20240314-12:55:07] [INFO ] connection problem, giving up
[20240314-12:55:07] [INFO ] some problem
[20240314-12:55:07] [ERROR] xrdp_sec_send_fastpath: xrdp_fastpath_send failed
[20240314-12:55:07] [ERROR] xrdp_rdp_send_fastpath: xrdp_sec_send_fastpath failed
[20240314-12:55:07] [ERROR] xrdp_orders_send: xrdp_rdp_send_fastpath failed
...
```

#### 解析結果
接続問題に関連するエラーメッセージが多数含まれています。これらのエラーがxrdp接続の問題の原因となっている可能性があります。

### 2. .xsession-errorsログの確認と解析
#### 確認手順：

1. SSHを使用してUbuntuサーバーに接続します。
2. xrdpのログファイルを確認します。
```bash
   sudo less /home/$user名/.xsession-errors
```

#### .xsession-errorsログの内容：
```
dbus-update-activation-environment: setting DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
...
/etc/X11/Xsession.d/30x11-common_xresources: line 16: has_option: command not found
...
/etc/X11/Xsession.d/90x11-common_ssh-agent: line 9: has_option: command not found
...
```

#### 解析結果
.xsession-errorsログには、has_option: command not found エラーが複数回記録されています。これは、関連するスクリプト内で使用されるコマンドが見つからないことを示しています。

## 対処法
以下の有益な記事がありました。どうやらubuntu 22.04 LTSのバグっぽいです。
https://ubuntu-mate.community/t/xsession-d-errors-how-to-fix-line-has-option-command-not-found/25673

記事の通り以下のコマンドを実行しxrdpを再起動することで解消します。
```bash
cat <<\EOF | sudo tee /etc/X11/Xsession.d/20x11-add-hasoption
# temporary fix for LP# 1922414, 1955135 and 1955136 bugs
# read OPTIONFILE
OPTIONS=$(cat "$OPTIONFILE") || true

has_option() {
 if [ "${OPTIONS#*
$1}" != "$OPTIONS" ]; then
   return 0
 else
   return 1
 fi
}
EOF
```

