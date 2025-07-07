---
title: "【AWS】DKIM設定が突然無効化された話"
emoji: "💀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , SES, DKIM, メール, DNS, CloudFlare]
published: true
---

## キッカケ：AWSからの通知メール

最初に以下のようなメールがAWSから届いていました：

```
We detected that the DNS records required for the DKIM setup of example.com are no longer present in your DNS settings.

To protect your email deliverability, we have temporarily disabled DKIM signing for emails originating from example.com.

If the removal of the DNS records was intentional, you do not need to take any additional action. In 5 days, example.com will no longer be considered to be configured for the purpose of DKIM signing.

If it was unintentional, please restore the DNS records to your DNS settings within 5 days.
```

そして5日後：

```
Since 5 days have elapsed and the DNS records have not been restored, Amazon SES and Amazon Pinpoint will no longer consider example.com to be configured for the purpose of DKIM signing.
```

さらに3日間の検証失敗後：

```
We have been attempting to verify the DKIM setup of example.com for the last 3 days. We have not been able to detect the required DNS records in your DNS settings.
```

## 発生した問題

### 症状
- お問い合わせフォームからのメール送信でエラーが発生
- AWS SESコンソールでDKIM設定が「保留中」になっている
- ドメイン検証エラー：「DNS サーバーが指定されたドメイン名を見つけることができませんでした」

### DNS移行の背景

今回の問題の発端は、**独自ドメインメール**を設定するためにDNSプロバイダーをRoute53からCloudflareに移行したことでした。
https://zenn.dev/zuzuzu/articles/cloudflare-email-setup

独自ドメインメール設定の流れ：
1. **メールサービスの検討** - Gmail、Outlook等でのカスタムドメイン利用
2. **DNS管理の見直し** - より柔軟なDNS管理のためCloudflareを選択
3. **Route53からCloudflareへの移行** - ネームサーバー変更とレコード移行
4. **AWS SES設定の引き継ぎ** - 既存のメール送信機能の維持

## 原因調査

### CloudTrailでの履歴確認

まず、Route53でDNSレコードが削除された履歴がないかCloudTrailで調査しました。

検索条件：
- イベント名：`ChangeResourceRecordSets`
- 時間範囲：警告メール受信の前後数日

結果：該当するイベントは見つかりませんでした。

### DNS設定の確認

#### Cloudflare（現在のDNSプロバイダー）
必要なレコードは正しく設定されていました：

```
# DKIMレコード（3つ）
[selector1]._domainkey.example.com → [selector1].dkim.amazonses.com
[selector2]._domainkey.example.com → [selector2].dkim.amazonses.com
[selector3]._domainkey.example.com → [selector3].dkim.amazonses.com

# カスタムMAIL FROMドメイン
mail.example.com MX → 10 feedback-smtp.ap-northeast-1.amazonses.com
mail.example.com TXT → "v=spf1 include:amazonses.com ~all"

# DMARC
_dmarc.example.com TXT → "v=DMARC1; p=none;"
```

すべて「DNS のみ」（プロキシ無効）で設定済みでした。

#### Route53（旧DNSプロバイダー）の確認

ここで**重大な発見**がありました。Route53に**古いDKIMレコード**が残っていました：

```
# 古いDKIMレコード（削除し忘れ）
[old-selector1]._domainkey.example.com
[old-selector2]._domainkey.example.com
```

## 根本原因：DNS権威サーバーの競合

### DNS移行時の見落とし

独自ドメインメール設定に集中するあまり、既存のAWS SES関連レコードの完全な移行を見落としていました：

**移行対象として認識していたレコード**：
- A, AAAA, CNAME（ウェブサイト用）
- MX, TXT（メール用）
- NS, SOA（基本レコード）

**見落としていたレコード**：
- AWS SESのDKIMレコード（`._domainkey`サブドメイン）
- 過去に設定したSES関連のカスタムレコード

### 問題の構造

DNS移行時に発生した問題：

1. **ネームサーバー**: Cloudflareに変更済み ✅
2. **新しいDKIMレコード**: Cloudflareに追加済み ✅  
3. **古いDKIMレコード**: Route53に残存 ❌

### なぜ問題が発生したのか

AWSのDKIM検証プロセスが：

1. **複数のDNSサーバーを参照**（権威サーバー分散の確認）
2. **Cloudflare**: 新しいDKIMレコードを返す
3. **Route53**: 古いDKIMレコード（または削除済みレコード）を返す
4. **異なる応答により検証失敗**

### DNS移行時の一般的な落とし穴

DNS移行時によくある問題：
- 旧DNSプロバイダーに古いレコードが残存
- 異なるDNSサーバーが異なる応答を返す
- AWSなどのサービスが複数のDNSサーバーをチェックして混乱

## 解決方法

### Route53の古いレコードを完全削除

**最も重要な対処法**：

1. **Route53にログイン**
2. **該当ドメインのホストゾーンを開く**
3. **以下の古いDKIMレコードを削除**：
   - `[old-selector1]._domainkey.example.com`
   - `[old-selector2]._domainkey.example.com`
   - その他のAWS SES関連の古いレコード

### DNS伝播の確認

レコード削除後、以下で確認：

```bash
# 古いレコードが削除されたことを確認
dig CNAME [old-selector1]._domainkey.example.com
# → 応答が「NXDOMAIN」になれば削除完了

# 新しいレコードが正常に応答することを確認
dig CNAME [selector1]._domainkey.example.com
```

### AWSでの検証完了を待機

古いレコード削除後：
- **15分〜2時間**: DNS伝播完了
- **数時間以内**: AWS SESでDKIM検証完了
- **結果**: 「検証済み」ステータスに変更、メール送信復旧

## 実際の解決過程

### タイムライン

1. **Route53の古いDKIMレコード6件を削除**
2. **約30分後**: AWS SESのDKIM設定が「検証済み」に変更
3. **ドメインIDステータス**: 「検証済み」に変更
4. **メール送信テスト**: 正常動作を確認

### 最終的な設定状態

```
✅ DKIM設定: 検証済み
✅ ドメインIDステータス: 検証済み  
✅ メール送信: 正常動作
✅ DNS権威: Cloudflareに統一
```

## 学んだ教訓

### DNS移行時のベストプラクティス

1. **旧DNSプロバイダーの完全クリーンアップ**
   - すべてのレコードを確実に削除
   - 特にサードパーティサービス関連のレコード

2. **移行後の検証**
   - 複数のDNSサーバーから応答確認
   - サービス連携の動作確認

3. **段階的な移行**
   - 重要なサービスは移行前後でテスト実施
   - ロールバック計画の準備

### AWS SESの特性理解

- **複数DNSサーバーをチェック**する検証プロセス
- **権威サーバーの一貫性**が重要
- **最大72時間**の検証期間設定

## まとめ

今回の問題は、**DNS移行時の古いレコード残存**が原因でした。独自ドメインメール設定のためのCloudflare移行時に、AWS SES関連の古いレコードを完全に削除しきれていなかったことで、AWSの検証プロセスが混乱していました。

**重要なポイント**：
- DNS移行時は旧プロバイダーのレコードを完全削除する
- サードパーティサービス（AWS SES等）は複数DNSサーバーをチェックする
- 権威サーバーの一貫性が重要
- `._domainkey`などの特殊なサブドメインレコードを見落としやすい

この経験により、DNS移行時の注意点と、AWS SESの検証プロセスについて深く理解することができました。同様の問題に遭遇した方の参考になれば幸いです。

## 参考資料

1. [AWS公式: Creating and verifying identities in Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#just-verify-domain-proc)
2. [AWS公式: Troubleshooting DKIM problems in Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/troubleshoot-dkim.html)
3. [Cloudflare公式: Managing DNS records](https://developers.cloudflare.com/dns/manage-dns-records/)
4. [AWS re:Post: DKIM issue not sure if relevant](https://repost.aws/questions/QUfyHhcyHbSk24UOSuQ6qZGg/dkim-issue-not-sure-if-relevant)
5. [Stack Overflow: DKIM and DMARC problems with Route53](https://stackoverflow.com/questions/58885953/dkim-and-dmarc-problems-with-route53)