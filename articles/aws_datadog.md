---
title: "【AWS】datadogでAWS EC2インスタンスをDatadogで監視する方法"
emoji: "🫀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , datadog, ec2 , cloud]
published: true
---


# AWS EC2インスタンスをDatadogで監視する方法

## はじめに

このガイドでは、Amazon Web Services (AWS) のElastic Compute Cloud (EC2) インスタンスをDatadogを使って監視する方法を説明します。Datadogを活用することで、EC2インスタンスのパフォーマンスや健全性をリアルタイムで把握し、問題が発生した際に迅速に対応することができます。

## 前提条件

- AWSアカウント
- Datadogアカウント
- EC2インスタンスへのアクセス権限

## 手順

### 1. AWSとDatadogの統合設定

1. Datadogダッシュボードにログインします。
2. 左側のメニューから「Integrations」を選択します。
3. 検索バーに「AWS」と入力し、AWS integrationを選択します。
4. 「Install Integration」をクリックします。
5. AWSアカウントIDを入力し、必要な権限を持つIAMロールを作成します。
6. 作成したIAMロールのARNをDatadogの設定ページに入力します。
7. EC2サービスが有効になっていることを確認します。
8. 「Install Integration」をクリックして設定を完了します。

### 2. EC2インスタンスへのDatadogエージェントのインストール

より詳細なメトリクスを収集するために、EC2インスタンスにDatadogエージェントをインストールします。

1. EC2インスタンスにSSH接続します。
2. 以下のコマンドを実行してDatadogエージェントをインストールします：

   ```bash
   DD_API_KEY=YOUR_API_KEY bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"
   ```
`YOUR_API_KEY`はDatadogのAPI keyに置き換えてください。

インストールが完了したら、エージェントが正常に動作していることを確認します：
```bash
sudo systemctl status datadog-agent
```
### 3. モニターの設定

1. Datadogダッシュボードで「Monitors」→「New Monitor」を選択します。
2. 「Metric」を選択し、EC2関連のメトリクスを指定します。
3. 以下のようなクエリを使用して、EC2インスタンスの状態を監視します：
```
avg(last_15m):avg:aws.ec2.host_ok{*} by {name} < 1
```


4. アラート条件とメッセージを設定します。
5. 通知先（例：Slack、Eメール）を指定します。
6. モニターを保存します。

### 4. ダッシュボードの作成

1. 「Dashboards」→「New Dashboard」を選択します。
2. EC2関連のウィジェットを追加します（例：CPU使用率、ネットワークトラフィック、ディスク使用量）。
3. 各ウィジェットにEC2メトリクスを設定します。
4. ダッシュボードをカスタマイズし、保存します。

### まとめ
以上の手順により、AWS EC2インスタンスをDatadogで効果的に監視することができます。定期的にモニターとダッシュボードを見直し、必要に応じて調整することで、EC2インスタンスの最適なパフォーマンスと可用性を維持できます。