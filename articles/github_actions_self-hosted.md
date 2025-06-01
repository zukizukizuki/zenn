---
title: "【CI/CD】オンプレミス環境にgithub actionsで自動デプロイする"
emoji: "🐈‍⬛"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [github , github actions , CI , CD]
published: true
---

## 1. GitHub Actions Self-Hosted Runnerの構築

GitHub Actions Self-Hosted Runnerを構築するためには、以下の手順に従います。

1. GitHubリポジトリの設定から、Settings > Actions >runnerセクションに移動し、**new self-hosted runner**を押下します。

2. 適切なOSとアーキテクトを選択し、表示されているコマンドを実行

3. GitHub側で接続できていることを確認する。接続すると、表示が「Idle」に変わる。

### 注意
2で実行するコマンドにTOKENが含まれていますが有効期間が1時間です
参考：https://github.com/actions/runner/issues/1882?ref=pangyoalto.com

## 2. actions-runner/run.sh自動起動設定

自動で「Self-hosted runner」の「actions-runner/run.sh」を実行させる必要があります。
これには「rc.local」を利用します。
rootでrc.local作成

```
sudo su -
sudo vi /etc/rc.local
```
既にインストール済みの「actions-runner/run.sh」を絶対パスで記述
rc-local.serviceで実行する場合は、rc.localファイルに「RUNNER_ALLOW_RUNASROOT="1"」を設定するのがポイントです。
そうしないとrc-local.serviceで実行できません。

```
#!/bin/bash
export RUNNER_ALLOW_RUNASROOT="1"
/home/****/actions-runner/run.sh &
```

実行権限を与えましょう

```
chmod +x /etc/rc.local
```
続いて、rc-local.serviceの自動起動設定、サービスリスタート、ステータス確認をします。

```
systemctl enable rc-local.service
systemctl restart rc-local.service
systemctl status rc-local.service
```
rc-local.serviceが以下のように正常起動していればOKです。

```
● rc-local.service - /etc/rc.local Compatibility
     Loaded: loaded (/etc/systemd/system/rc-local.service; enabled; vendor preset: enabled)
    Drop-In: /usr/lib/systemd/system/rc-local.service.d
             └─debian.conf
     Active: active (running) since Mon 2021-11-22 15:32:43 UTC; 12s ago
    Process: 1643 ExecStart=/etc/rc.local start (code=exited, status=0/SUCCESS)
   Main PID: 1644 (run.sh)
      Tasks: 15 (limit: 37282)
     Memory: 35.0M
     CGroup: /system.slice/rc-local.service
             ├─1644 /bin/bash /home/***/actions-runner/run.sh
             └─1648 /home/***/actions-runner/bin/Runner.Listener run

Nov 22 15:32:43 ********* systemd[1]: Starting /etc/rc.local Compatibility...
Nov 22 15:32:43 ********* systemd[1]: Started /etc/rc.local Compatibility.
Nov 22 15:32:45 ********* rc.local[1648]: √ Connected to GitHub
Nov 22 15:32:46 ********* rc.local[1648]: Current runner version: '2.284.0'
Nov 22 15:32:46 ********* rc.local[1648]: 2021-11-22 15:32:46Z: Listening for Jobs
```

## 3. Workflowの作成

GitHub ActionsのWorkflowを構築します。このWorkflowでは、リポジトリからのコード変更を検知し、自動的にデプロイプロセスを開始します。
**.github\workflows**というフォルダ構成にしてその配下にymlで以下のworkflowを記述します。

```yaml
name: Deploy On-Premise

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v2

      # デプロイしたいファイルをオンプレミス環境にコピーするステップを追加
      - name: Copy To On-Premise
        run: sudo cat ${{ github.workspace }}/${githubリポジトリにあるデプロイしたいファイル} | sudo tee ${オンプレのデプロイしたいフォルダ} >/dev/null
      # その他に実施したい処理を記載
```

##　参考記事

https://qiita.com/hanaokatomoki/items/af47da39a61948fb123f
https://qiita.com/renave/items/b557aca674b4be0876f1