---
title: /etc/rc.local が機能しない時の対処法
private: false
tags:
  - ubuntu
  - linux
  - rc.local
  - bash
updated_at: '2025-06-01T01:53:00.688Z'
id: null
organization_url_name: null
slide: false
---

## 問題の概要
UbuntuなどのLinux環境で、`/etc/rc.local`に記述したコマンドが起動時に実行されないことがあります。

## 解決策

### ログファイルを確認する
/var/log/syslogなどのログファイルを確認し、起動時にrc.localが実行されているか確認します。

### **シェルのパスを指定する**

`rc.local`ファイルの1行目にシェルのパスを指定します。
   ```bash
   #!/bin/bash
   ```

### 権限を設定する
rc.localファイルに実行権限を付与します。

```
sudo chmod +x /etc/rc.local
```

### 代替手段を検討する
rc.localが意図通りに動作しない場合は、次のいずれかの方法を利用できます。

#### ログイン時のスクリプト
ログイン時に特定の処理を実行したい場合は、以下のログイン時のスクリプトを活用します。

- ~/.bashrc
ユーザーがログインする度に実行されるスクリプトです。以下のように編集します。

```bash
#!/bin/bash

# ここに起動時に実行したいコマンドを追加
cd /desired/directory
```

- ~/.bash_profile または ~/.profile
ユーザーがログインする際に一度だけ実行されるスクリプトです。以下のように編集します。

```
#!/bin/bash

# ここに起動時に実行したいコマンドを追加
cd /desired/directory
```

#### systemdサービス

systemdを使用して、起動時に実行されるサービスを作成することができます。以下は、systemdサービスを使用した方法です。

サービスファイルの作成
**/etc/systemd/system**ディレクトリに、サービスファイル（例: **myservice.service**）を作成します。

```
[Unit]
Description=My Service
After=network.target

[Service]
ExecStart=/desired/directory/mycommand
Type=simple

[Install]
WantedBy=multi-user.target
```

作成したサービスを有効化し、起動します。

```
sudo systemctl enable myservice
sudo systemctl start myservice
```
サービスファイルには、サービスの説明や起動時のコマンドなどを指定します。ExecStartに起動時に実行したいコマンドを記述します。

## 注意事項
rc.localはシステム起動時に実行されるため、システム全体に影響を与える可能性があります。慎重に設定してください。
最新のUbuntuバージョンではrc.localが非推奨となっています。代わりにsystemdや他の仕組みを使用することが推奨されます。

## 参考記事
https://forums.ubuntulinux.jp/viewtopic.php?id=20914
