---
title: "windows server をNTPサーバとしてLinuxとWindowsでそのサーバを参照し時刻同期する"
emoji: "🕰️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [windows , ntp, w32time , linux]
published: true
---


# windows server をNTPサーバとしてLinuxとWindowsでそのサーバを参照し時刻同期する

## はじめに

この記事では、Windows ServerをNTP(Network Time Protocol)サーバとして設定し、LinuxとWindowsからそのサーバを参照する方法について説明します。

## Windows Serverのファイアウォール設定の解除手順

Windows ServerのファイアウォールがNTP通信をブロックしている場合は、以下の手順で解除します。

1. 管理者としてログインします。
2. コントロールパネルを開きます。
3. 「システムとセキュリティ」を選択します。
4. 「Windows Defender ファイアウォール」をクリックします。
5. 左側のパネルで、「高度な設定」をクリックします。
6. 左側のパネルで、「受信規則」を選択します。
7. 右側のパネルで、「新しい規則」をクリックします。
8. 「プログラム」を選択し、「次へ」をクリックします。
9. 「このプログラムのパス」に、NTPサーバのプログラムパスを指定します。通常は`C:\Windows\System32\w32time.exe`です。
10. 「次へ」をクリックします。
11. 「接続を許可する」を選択し、「次へ」をクリックします。
12. 「すべてのプロファイル」にチェックを入れて、「次へ」をクリックします。
13. 名前を適切に入力し、必要に応じて説明を追加します。
14. 「完了」をクリックして設定を保存します。

## Windows Serverの設定

1. Windows Serverで管理者としてログインします。
2. PowerShellを開きます。
3. 以下のコマンドを実行して、NTPサーバの設定を行います。

```
w32tm /config /manualpeerlist:"ntp.example.com" /syncfromflags:manual /reliable:YES /update
```

4. NTPサービスを再起動します。
```
Restart-Service w32time
```

## LinuxからWindows Serverを参照し、時刻同期する方法
1. Linuxマシンで管理者権限でターミナルを開きます。
2. NTPクライアントをインストールします。例えば、Ubuntuの場合は以下のコマンドを実行します。

```
sudo apt-get update
sudo apt-get install ntp
```

3. NTP構成ファイル(/etc/ntp.conf)を編集します。以下のように追記します。
```
server ntp.example.com
```

4. NTPサービスを再起動します。

```
sudo systemctl restart ntp
```
これで、LinuxマシンはWindows ServerをNTPサーバとして参照できるようになります。


## WindowsからWindows Serverを参照し、時刻同期する方法

1. Windowsマシンで管理者としてログインします。
2. コントロールパネルを開きます。
3. 「日付と時刻」を選択します。
4. 「インターネット時間」タブをクリックします。
5. 「設定」ボタンをクリックします。
6. 「インターネット時間の設定」ダイアログボックスで、チェックボックスをオフにし、「変更」ボタンをクリックします。
7. 「サーバーの追加」ダイアログボックスで、NTPサーバのIPアドレスを入力します。例えば、`192.168.1.100`など。
8. 「OK」ボタンをクリックして設定を保存します。

これで、Windowsマシンは指定したWindows ServerのIPアドレスをNTPサーバとして参照し、時刻を同期します。

## まとめ
この記事では、Windows ServerをNTPサーバとして設定し、LinuxとWindowsからそのサーバを参照する方法について説明しました。正確な時刻同期はネットワーク環境において重要ですので、適切な設定を行うことをお勧めします。
