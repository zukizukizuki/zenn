---
title: "【AWS】DKIM設定が突然無効化された話"
emoji: "💀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , SES, DKIM, メール]
published: true
---

## はじめに

ブログを運営していて、お問い合わせフォームからのメール送信にAWS SESを利用しています。ある日突然、メール送信でエラーが発生するようになりました。調査してみると、AWS SESのDKIM設定が無効化されていることが判明しました。

この記事では、その原因調査から解決までの過程を記録として残します。

## 発生した問題

### 症状
- お問い合わせフォームからのメール送信でエラーが発生
- AWS SESコンソールでDKIM設定が「保留中」になっている

### AWSからの通知メール

最初に以下のようなメールがAWSから届いていました：

```
We detected that the DNS records required for the DKIM setup of [ドメイン名] are no longer present in your DNS settings.

To protect your email deliverability, we have temporarily disabled DKIM signing for emails originating from [ドメイン名].

If the removal of the DNS records was intentional, you do not need to take any additional action. In 5 days, [ドメイン名] will no longer be considered to be configured for the purpose of DKIM signing.

If it was unintentional, please restore the DNS records to your DNS settings within 5 days.
```

そして5日後：

```
Since 5 days have elapsed and the DNS records have not been restored, Amazon SES and Amazon Pinpoint will no longer consider [ドメイン名] to be configured for the purpose of DKIM signing.
```

## 原因調査

### CloudTrailでの履歴確認

まず、Route53でDNSレコードが削除された履歴がないかCloudTrailで調査しました。

検索条件：
- イベント名：`ChangeResourceRecordSets`
- 時間範囲：警告メール受信の前後数日

結果：該当するイベントは見つかりませんでした。

### 現状確認

Route53のコンソールを確認すると、DKIMに必要なCNAMEレコードは**存在している**状態でした：

```
pzrbrkmsxosgxifdheh3jkmxtrqsltbk._domainkey.[ドメイン名] → [hash].dkim.amazonses.com
ximwiugqvcs46ogvtfzagkdtfeysmfpx._domainkey.[ドメイン名] → [hash].dkim.amazonses.com
emafy4errojen5squeaq4l2x4gzadr4x._domainkey.[ドメイン名] → [hash].dkim.amazonses.com
```

## 根本原因の調査

この問題について調査したところ、**AWSの一般的な動作**であることが判明しました。

### AWSの定期チェック機能

AWS公式ドキュメント¹によると：

> Amazon SES can no longer find the required CNAME records (if you used Easy DKIM) or the required TXT record (if you used BYODKIM) records on your DNS server. The notification email will inform you of the length of time in which you must re-publish the DNS records before your DKIM setup status is revoked and DKIM signing is disabled.

AWSは定期的にDKIMのDNSレコードの存在確認を行っており、何らかの理由でレコードが見つからなくなると警告メールを送信し、5日間の猶予期間後にDKIM署名を無効化します。

### よくある原因

コミュニティでの報告²³⁴を調査した結果、以下のような原因が考えられます：

1. **DNS伝播の一時的な問題** - DNSレコードが一時的に到達不能になる
2. **DNSサーバーの応答エラー** - SERVFAILエラーなど
3. **Route53での設定変更時の副作用** - 他の設定変更時にレコードが一時的に見えなくなる
4. **自動化ツールによる意図しない変更**

実際に、MailWizzフォーラムでは「何も触っていないのにDKIMが無効化された」という同様の報告があり、レコードを削除・再追加することで解決したという事例が報告されています⁴。

## 解決方法

### 1. 現状のレコード確認

まず、Route53でDKIMレコードが正しく設定されているか確認します。

### 2. レコードの再設定

以下の手順でDKIMレコードを再設定します：

1. **Route53で現在のDKIMレコードを削除**
   - 3つのCNAMEレコードをすべて削除

2. **SESコンソールで新しいレコードを生成**
   - SESコンソール → 認証 → DKIM → 編集
   - 「保存」をクリックして新しいレコードを生成

3. **新しいCNAMEレコードをRoute53に追加**
   - SESで表示される3つのCNAMEレコードをすべて追加

### 3. 検証

設定後、通常は数分から数時間でDKIMが「検証済み」になります。

> **注意**: SESコンソールで「検証済み」と表示されていれば、外部のDKIMチェックツールが認識しなくても実際には正常に動作している場合があります⁵。

## まとめ

今回の問題は、AWSが提供する保護的な機能による一時的な無効化でした。DNSレコードが実際に削除されていなくても、何らかの理由でAWSのチェック機能がレコードを確認できない場合にこのような事象が発生します。

CloudTrailに履歴が残っていなかったことからも、手動での削除ではなく、DNS伝播やサーバー応答の一時的な問題が原因と考えられます。

同様の問題に遭遇した場合は、まずRoute53（またはDNSプロバイダー）でレコードが存在することを確認し、必要に応じてレコードの再設定を行うことで解決できます。

## 参考資料

1. [AWS公式: Troubleshooting DKIM problems in Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/troubleshoot-dkim.html)
2. [AWS re:Post: DKIM issue not sure if relevant](https://repost.aws/questions/QUfyHhcyHbSk24UOSuQ6qZGg/dkim-issue-not-sure-if-relevant)
3. [AWS re:Post: DKIM not propagating after more than 5 days](https://repost.aws/questions/QUOFUiCPjDSwGwBIW2bmJa8Q/dkim-not-propagating-after-more-than-5-days)
4. [MailWizz Forum: Amazon SES DKIM verification got deleted](https://forum.mailwizz.com/threads/amazon-ses-dkim-verification-got-deleted.2279/)
5. [Stack Overflow: DKIM and DMARC problems with Route53](https://stackoverflow.com/questions/58885953/dkim-and-dmarc-problems-with-route53)