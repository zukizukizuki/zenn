---
title: "DatadogでSlack通知時にインスタンスIDではなく名前を表示する方法"
emoji: "🪆"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [datadog , slack, EC2 , 自動化]
published: true
---

先日、Datadogで設定したモニターからSlackに通知を送信する際、通知内でインスタンスIDではなく、わかりやすいインスタンス名を表示したいという課題に直面しました。この記事では、その解決方法を共有します。

## 問題の背景

Datadogのモニターを設定し、アラートをSlackに通知すると、デフォルトではホスト名がインスタンスIDとして表示されます。これではどのインスタンスで問題が発生したのか直感的に把握しづらいです。

## 解決策

Datadog Agentが使用するホスト名は、以下の優先順位で決定されます。

1. **agent-hostname**: Datadog Agentの設定ファイルで明示的に設定されたホスト名（`ip-`や`domu`で始まらない場合）。
2. **hostname**: システムのDNSホスト名（EC2のデフォルトでない場合）。
3. **instance-id**: AgentがEC2のメタデータエンドポイントにアクセスできる場合。
4. **hostname**: EC2のデフォルトのDNSホスト名。

現在、インスタンスIDがホスト名として設定されているため、Datadog Agentの設定ファイルでホスト名を指定することで解決できます。

## 手順

1. **Datadog Agentの設定ファイルを編集**

    Datadog Agentのメイン設定ファイルである`datadog.yaml`を開き、以下のように`hostname`を設定します。

    ```yaml
    hostname: <あなたのインスタンス名>
    ```

    `<あなたのインスタンス名>`を実際のホスト名に置き換えてください。

2. **Datadog Agentの再起動**

    設定を反映させるため、Datadog Agentを再起動します。

    - **Linuxの場合**:

        ```bash
        sudo systemctl restart datadog-agent
        ```

    - **Windowsの場合**:

        サービスマネージャから`DatadogAgent`サービスを再起動します。

3. **変更の確認**

    Datadogのダッシュボードでホスト名が更新されていることを確認します。また、Slack通知でもインスタンス名が表示されていることを確認します。

## まとめ

Datadog Agentの設定ファイルで`hostname`を指定し、Agentを再起動することで、Slack通知に表示されるホスト名をインスタンス名に変更することができました。同じ問題でお困りの方の参考になれば幸いです。

## 参考資料

- [How does Datadog determine the Agent hostname?](https://docs.datadoghq.com/agent/faq/how-datadog-agent-determines-the-hostname/)

