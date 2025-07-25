---
title: "【Ver6.4対応】zabbixのスクリプトでslackに通知する"
emoji: "👀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [zabbix , Mac, apache , PHP , postgres]
published: true
---

## 概要
[以前Macにzabbixサーバを立てた](https://zenn.dev/zuzuzu/articles/mac_zabbix_install)のでそれにslackに通知する機能を持たせる。しかし、1番簡単なwebhookからの通知設定を実施すると[zabbix_serverがクラッシュしてしまう事象](https://www.zabbix.jp/node/1036)が発生する。(ソースインストールした時のオプションが不足していた？)

そこでスクリプトを用いてslackに通知する機能を実装したのでその手順について説明する。

## 手順

### Slackの「Incoming Webhooks」を作成してチャネルに通知するアプリを作る
slackの左下の**アプリを追加する**を押下

![](https://storage.googleapis.com/zenn-user-upload/de95deed8cde-20231230.png)

検索窓で**Incoming Webhooks**と入力してアプリを探し、**追加**を押下
![](https://storage.googleapis.com/zenn-user-upload/a846321e08f9-20231230.png)

**slackに追加する**を押下
![](https://storage.googleapis.com/zenn-user-upload/b7a9afaa6e66-20231230.png)

追加したいチャンネルを設定して **Incomming Webhookインテグレーションの追加** を押下
![](https://storage.googleapis.com/zenn-user-upload/d65261bfa0a6-20231230.png)

**Webhook URL**は今後必要になるので書き控えておきます。
![](https://storage.googleapis.com/zenn-user-upload/1f1acf313954-20231230.png)

### 通知用シェルスクリプトを作成する
**slack.sh**という名前のscriptを作成します。

`sudo vim /usr/local/share/zabbix/alertscripts/slack.sh`

```
#!/bin/bash

# Slack incoming web-hook URL
SLACK_WEBHOOKSURL='${Webhook URL}'

# Slack UserName
SLACK_USERNAME='Zabbix(bot)'


# "Send to" for Zabbix User Media Setting
NOTIFY_CHANNEL="$1"

# "Default subject" for Action Operations Setting
ALERT_SUBJECT="$2"

# "Default message" for Action Operations Setting
ALERT_MESSAGE="$3"

if [ "${ALERT_SUBJECT%%:*}" == 'Recover' ]; then
        ICON=':smile:'
        COLOR="good"
elif [ "${ALERT_SUBJECT%%:*}" == 'Problem' ]; then
        ICON=':skull:'
        COLOR="danger"
else
        ICON=':innocent:'
        ICON=':sushi:'
        COLOR="#439FE0"
fi

# Create JSON payload
PAYLOAD="payload={
    \"channel\": \"${NOTIFY_CHANNEL//\"/\\\"}\",
    \"username\": \"${SLACK_USERNAME//\"/\\\"}\",
    \"icon_emoji\": \"${ICON}\",
    \"attachments\": [
        {
            \"color\": \"${COLOR}\",
            \"text\": \"${ALERT_MESSAGE//\"/\\\"}\"
        }
    ]
}"

# Send it as a POST request to the Slack incoming webhooks URL
curl -m 5 --data-urlencode "${PAYLOAD}" $SLACK_WEBHOOKSURL
```

### メディアの設定
ブラウザからzabbixを開き **通知** → **メディアタイプ** を押下
メディアタイプ**slack**を有効にし、さらに**slack**を押下し設定していく
![](https://storage.googleapis.com/zenn-user-upload/14a9be63f018-20231230.png)

以下の様に設定していく。

| 項目名 | 設定内容 |
| ---- | ---- |
| 名前 | slack |
| タイプ | スクリプト |
| スクリプト名 | slack.sh |
| スクリプトパラメータ1 | {ALERT.SENDTO} |
| スクリプトパラメータ2 | {ALERT.SUBJECT} |
| スクリプトパラメータ3 | {ALERT.MESSAGE} |

![](https://storage.googleapis.com/zenn-user-upload/5ebf0c257e40-20231230.png)

### zabbix ユーザーの設定
ユーザーの項目を開き**ユーザーを作成**を押下

![](https://storage.googleapis.com/zenn-user-upload/dd9dfe485809-20231230.png)

ユーザー名(今回はzabbix)とパスワードを入力し **メディア**を押下し、**追加**を押下し**送信先**にslack通知したいチャンネルを入力

![](https://storage.googleapis.com/zenn-user-upload/fe4feec26f97-20231230.png)

最後に追加を忘れずに
![](https://storage.googleapis.com/zenn-user-upload/94561de92649-20231230.png)

**権限**で **Super Admin role**を付与して**追加**を押下します。

![](https://storage.googleapis.com/zenn-user-upload/495275afa11c-20231230.png)

### トリガーアクションの設定
通知 → アクション → トリガーアクション を押下し**アクションの作成**を押下する。

![](https://storage.googleapis.com/zenn-user-upload/ff6e7790b42d-20231230.png)

**アクション名**を命名して、**実行条件**を追加する。
今回は警告以上でメンテナンス期間でない場合 実行するアクションにしています。

![](https://storage.googleapis.com/zenn-user-upload/47012795c7af-20231230.png)

**実行内容**を押下し**デフォルトのアクション実行ステップの間隔**を60秒を設定します。

![](https://storage.googleapis.com/zenn-user-upload/a8b51a3b0d25-20231230.png)

実行内容を以下の様に設定していきます。

| 項目名 | 設定内容 |
| ---- | ---- |
| 処理内容 | メッセージの送信 |
| ユーザーに送信 | zabbix(さっき作ったuser名) |
| 次のメディアのみ使用 | slack |
| メッセージのカスタマイズ | ☑️ |
| 件名 | Problem |

メッセージは以下の内容にしてください。
```
以下の障害が発生しました。

発生時刻　　{EVENT.DATE} {EVENT.TIME}
発生ホスト　{HOST.NAME}
深刻度　　　{EVENT.SEVERITY}
発生障害　　{EVENT.NAME}

障害の説明
------------------------------------
{TRIGGER.DESCRIPTION}
```

![](https://storage.googleapis.com/zenn-user-upload/002b11dff057-20231230.png)

復旧時の実行内容を以下の様に設定してアクションを追加します。

| 項目名 | 設定内容 |
| ---- | ---- |
| 処理内容 | 障害通知済のユーザーすべてにメッセージを送信 |
| メッセージのカスタマイズ | ☑️ |
| 件名 | Recover |

メッセージは以下の内容にしてください。
```
以下が復旧しました。

発生時刻　　{EVENT.DATE} {EVENT.TIME}
復旧時刻        {EVENT.RECOVERY.DATE} {EVENT.RECOVERY.TIME}
発生ホスト　{HOST.NAME}
深刻度　　　{EVENT.SEVERITY}
発生障害　　{EVENT.NAME}

障害の説明
------------------------------------
{TRIGGER.DESCRIPTION}
```

![](https://storage.googleapis.com/zenn-user-upload/631d473c4b54-20231230.png)

完成

![](https://storage.googleapis.com/zenn-user-upload/950bd546127f-20231230.png)

### 障害テスト

zabbix_agentを落として通知されるか確認します。

ターミナルを開き以下のコマンドを実行します
```
pkill -f zabbix_agent
```
3分くらいすると以下の様にslack通知されます。

![](https://storage.googleapis.com/zenn-user-upload/a88d835f1296-20231230.png)

## 復旧テスト

落としたzabbix_agentを起動して復旧通知されるか確認します。

ターミナルを開き以下のコマンドを実行します
```
sudo /usr/local/sbin/zabbix_agentd
```

以下の様にslack通知されます。

![](https://storage.googleapis.com/zenn-user-upload/7e488b4c10e1-20231230.png)

## 参考
https://colabmix.co.jp/tech-blog/install-zabbix-slack/