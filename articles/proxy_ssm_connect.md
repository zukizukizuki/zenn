---
title: "オンプレミス環境のubuntuでProxyを使うようにAWS SSM Agentを設定した時にハマったこと"
emoji: "🤔"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [ubuntu , linux, aws, proxy, ssm]
published: true
---

## 概要
オンプレミスの閉鎖環境にあるubuntu 22.04に踏み台からじゃなくてAWS SSMで直接アクセスしたいと思い作業をしましたが、公式ドキュメントに書いてない事でハマったので備忘録を残す。

## 公式の手順でやってみたところ・・・

snapを使ってAWS SSM agentをインストールしたので[公式ドキュメント](https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/configure-proxy-ssm-agent.html)にある通り

1. `sudo systemctl edit snap.amazon-ssm-agent.amazon-ssm-agent` でproxyサーバ等を環境変数として指定
2. `sudo systemctl daemon-reload && sudo systemctl restart snap.amazon-ssm-agent.amazon-ssm-agent` で再起動

すればいいはずが以下のエラーが出て上手くいかない

```
ubuntu@ubuntu:~/$ sudo /snap/amazon-ssm-agent/current/amazon-ssm-agent -register -code "$コード" -id "$ID" -region "ap-northeast-1"
Initializing new seelog logger
New Seelog Logger Creation Complete
2024-04-26 20:20:57 INFO No initial fingerprint detected, generating fingerprint file...
2024-04-26 20:21:06 ERROR Registration failed due to error registering the instance with AWS SSM. RequestError: send request failed
caused by: Post "https://ssm.ap-northeast-1.amazonaws.com/": dial tcp: lookup ssm.ap-northeast-1.amazonaws.com on 127.0.0.53:53: server misbehaving
ubuntu@ubuntu:~/$
```

以下のコマンドで確認すると環境変数が正しく設定されていない

```
ubuntu@ubuntu:~/$ sudo /snap/amazon-ssm-agent/current/amazon-ssm-agent
Initializing new seelog logger
New Seelog Logger Creation Complete
2024-04-26 20:27:50 INFO Proxy environment variables:
2024-04-26 20:27:50 INFO https_proxy:
2024-04-26 20:27:50 INFO http_proxy:
2024-04-26 20:27:50 INFO no_proxy:
```

[別のドキュメント](https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/sysman-install-managed-linux.html)にはexportで環境変数を指定する手順があったので試してみるも状況は変わらず

## 解決策

`/etc/systemd/system/snap.amazon-ssm-agent.amazon-ssm-agent.service`の`EnvironmentFile`に`/etc/enviroment`が指定されていた。

```
ubuntu@ubuntu:~/$ cat /etc/systemd/system/snap.amazon-ssm-agent.amazon-ssm-agent.service
[Unit]
# Auto-generated, DO NOT EDIT
Description=Service for snap application amazon-ssm-agent.amazon-ssm-agent
Requires=snap-amazon\x2dssm\x2dagent-7628.mount
Wants=network.target
After=snap-amazon\x2dssm\x2dagent-7628.mount network.target snapd.apparmor.service
X-Snappy=yes

[Service]
EnvironmentFile=-/etc/environment
ExecStart=/usr/bin/snap run amazon-ssm-agent
SyslogIdentifier=amazon-ssm-agent.amazon-ssm-agent
Restart=always
WorkingDirectory=/var/snap/amazon-ssm-agent/7628
TimeoutStopSec=60
Type=simple
KillMode=process
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
ubuntu@ubuntu:~/$
```

なので`/etc/enviroment`に以下の環境変数を設定する。

```
http_proxy=http://$proxyのIP:$port
https_proxy=http://$proxyのIP:$port
no_proxy=169.254.169.254
```

すると環境変数が正しく指定され上手くいった。

```
ubuntu@ubuntu:~/$ sudo /snap/amazon-ssm-agent/current/amazon-ssm-agent
Initializing new seelog logger
New Seelog Logger Creation Complete
2024-04-26 20:27:50 INFO Proxy environment variables:
2024-04-26 20:27:50 INFO https_proxy:http://$proxyのIP:$port
2024-04-26 20:27:50 INFO http_proxy:http://$proxyのIP:$port
2024-04-26 20:27:50 INFO no_proxy:169.254.169.254
```

```
ubuntu@ubuntu:~/$ sudo /snap/amazon-ssm-agent/current/amazon-ssm-agent -register -code "$コード" -id "$ID" -region "ap-northeast-1"
Initializing new seelog logger
New Seelog Logger Creation Complete
2024-04-26 20:37:06 INFO Successfully registered the instance with AWS SSM using Managed instance-id: mi-xxxxxxxxxxxxxxxxxxx
ubuntu@ubuntu:~/$
```