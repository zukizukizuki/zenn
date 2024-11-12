---
title: "【2024年版】RundeckとSlackを連携し、ジョブ結果をSlackに通知する方法"
emoji: "🪥"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rundeck , linux, aws, slack]
published: true
---

Rundeckでジョブ実行の結果をSlackに通知するために、Slack Incoming Webhookプラグインを使って設定する方法を解説します。

## 前提条件

- Rundeck バージョン: 5.7.0
- Slack バージョン: プロダクション 4.41.96 64-bit
- rundeck は EC2(amazon_linux_2)にinstall

## 手順

### 1. SlackのWebhook URLを取得

1. [Slack API](https://api.slack.com/apps)のページにアクセスし、「Create New App」から新しいAppを作成します。
2. 「Incoming Webhooks」を有効化します。
3. 「Add New Webhook to Workspace」をクリックし、通知先のチャンネルを選択します。
4. Webhook URL（例：`https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`）が生成されるので、これをコピーしておきます。このURLは後で使用します。

### 2. RundeckでSlack Notificationプラグインのインストール

Slack Incoming WebhookプラグインがRundeckにインストールされていない場合、以下の手順でインストールしてください。

1. GitHubからプラグインをダウンロードし、`/var/lib/rundeck/libext/` に配置します：
   ```
   wget -O /var/lib/rundeck/libext/slack-incoming-webhook-plugin.jar https://github.com/rundeck-plugins/slack-incoming-webhook-plugin/releases/download/v1.2.5/slack-incoming-webhook-plugin-1.2.5.jar
   ```

   - **補足**: `/var/lib/rundeck/libext/` に配置するだけでOKです。再起動は不要です。

### 3. Rundeckのプロジェクト設定でSlack Notificationを設定

#### GUIでの設定方法

1. Rundeckにログインし、対象のプロジェクトを選択します。
2. 「PROJECT SETTINGS」から「Edit Configuration」を選択します。
3. 「Edit Configuration file」をクリックし、以下の内容を追加します。

   ```
   project.plugin.Notification.SlackNotification.channel=\#ex-rundeck-job
   project.plugin.Notification.SlackNotification.webhook_base_url=https\://hooks.slack.com/services
   project.plugin.Notification.SlackNotification.webhook_token=T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
   ```

   - `channel`には通知先のSlackチャンネルを指定します。
   - `webhook_base_url`にはSlackのWebhook URLのベース部分 `https://hooks.slack.com/services` を設定します。
   - `webhook_token`にはWebhook URLのトークン部分を指定します（例：`T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`）。

4. 「Save」をクリックして設定を保存します。

   - **注意点**: `vim /etc/rundeck/project.properties` などでCLIから設定ファイルを直接編集しても、設定が反映されないことがあります。必ずGUIから設定を行ってください。

### 4. ジョブでSlack通知を設定

1. 対象のジョブを開き、「Notifications」タブに移動します。
2. 「成功時」と「失敗時」の通知タイプを「Slack Incoming Webhook」に設定します。
3. 必要に応じて通知の詳細（チャンネルやユーザー名など）を設定します。

   - **補足**: 通知の詳細設定が空欄の場合でも、`Edit Configuration file`で設定しているのでデフォルトで動作します。

### 5. 設定の確認

ジョブを実行して、設定したSlackチャンネルに通知が届くか確認してください。

![](https://storage.googleapis.com/zenn-user-upload/bb8641c1d256-20241112.png)

## まとめ

以上の手順で、RundeckとSlackを連携して、ジョブの実行結果をSlackに通知することができます。特にプロジェクト設定の変更はGUIから行うよう注意しましょう。
