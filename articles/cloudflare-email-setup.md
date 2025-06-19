---
title: "独自ドメインメールをCloudflare Email Routingで無料構築する方法"
emoji: "📨"
type: "tech"
topics: ["Cloudflare", "Route53", "mail", "smtp", "個人開発"]
published: true
---

## はじめに：法人で個人アプリ開発時の意外な落とし穴

法人として個人アプリを開発していると、思わぬところで独自ドメインのメールアドレスが必要になることがあります。

- App StoreやGoogle Playへの申請時にサポート用メールアドレスが必要
- 利用規約やプライバシーポリシーに記載する問い合わせ先
- ユーザーからの問い合わせ対応用のメールアドレス

しかし、Google WorkspaceやMicrosoft 365などの法人向けメールサービスは月額680円〜と、個人アプリの運用コストとしては割高です。

そこで今回は、**Cloudflare Email Routing**を使って**完全無料**で独自ドメインメール（例：info@yourdomain.com）を構築する方法をご紹介します。

## 必要なもの

- 独自ドメイン（取得済み）
- Cloudflareアカウント（無料）
- Gmailアカウント（転送先として使用）

## 構築手順

### 1. Cloudflareにドメインを追加

1. [Cloudflare](https://www.cloudflare.com/)にログイン
2. 「サイトを追加」をクリック
3. ドメイン名を入力（例：yourdomain.com）
4. 無料プランを選択

### 2. ネームサーバーをCloudflareに変更

Cloudflareから指定されたネームサーバーに変更します：

```
例：
chase.ns.cloudflare.com
dara.ns.cloudflare.com
```

#### AWS Route 53の場合

1. Route 53コンソール → 登録済みドメイン
2. 対象ドメインを選択
3. 「ネームサーバーを編集」
4. Cloudflareのネームサーバーに変更

#### その他のレジストラ

各レジストラの管理画面でネームサーバーを変更してください。

**注意：** 変更の反映には2〜48時間かかることがあります。

### 3. CloudflareでEmail Routingを設定

Cloudflareがアクティブになったら：

1. Cloudflare管理画面 → 左メニュー「Email」
2. 「Email Routing」タブを選択
3. 「Get started」をクリック
4. カスタムアドレスを作成：
   ```
   例：info@yourdomain.com → your-gmail@gmail.com
   ```

### 4. Gmailで送信設定（重要）

独自ドメインから送信するための設定です。

#### 4-1. Googleアカウントでアプリパスワードを生成

1. [Googleアカウントのセキュリティ設定](https://myaccount.google.com/security)にアクセス
2. 2段階認証を有効化（まだの場合）
3. [アプリパスワード](https://myaccount.google.com/apppasswords)を生成
   - アプリを選択：メール
   - デバイスを選択：その他（カスタム名）
   - 名前を入力：「独自ドメインSMTP」など
4. 16文字のパスワードをメモ

#### 4-2. Gmailでメールアドレスを追加

1. Gmail → ⚙️設定 → すべての設定を表示
2. 「アカウントとインポート」タブ
3. 「名前」セクションの「他のメールアドレスを追加」
4. 以下を入力：
   ```
   名前: あなたの名前
   メールアドレス: info@yourdomain.com
   ☑ エイリアスとして扱います
   ```

5. SMTP設定：
   ```
   SMTPサーバー: smtp.gmail.com
   ポート: 587
   ユーザー名: your-gmail@gmail.com
   パスワード: [生成したアプリパスワード]
   ☑ TLS を使用したセキュリティで保護された接続
   ```

6. 確認メールのリンクをクリック

### 5. デフォルトの返信モードを設定

Gmail設定で「デフォルトの返信モード」を「メールを受信したアドレスから返信する」に変更すると、自動的に適切なアドレスから返信できます。

## トラブルシューティング

### Q: ネームサーバーの変更がどこでできるか分からない

```bash
# ターミナルでWHOIS情報を確認
whois yourdomain.com
```
「Registrar:」の行でレジストラを確認できます。

### Q: Gmailでパスワードエラーが出る

通常のGmailパスワードではなく、**アプリパスワード**を使用してください。

### Q: 確認メールが届かない

- Cloudflare Email Routingが有効か確認
- スパムフォルダを確認
- MXレコードが正しく設定されているか確認

## まとめ

この方法により、法人での個人アプリ開発時に必要な独自ドメインメールを**完全無料**で構築できます。

### メリット

- ✅ 初期費用・月額費用0円
- ✅ 使い慣れたGmailインターフェースで送受信
- ✅ スマホアプリでも利用可能
- ✅ 複数のメールアドレスを作成可能

### 注意点

- ⚠️ 大量送信には向かない（通常のGmail制限が適用）
- ⚠️ メールボックスはGmailの容量を使用

法人として個人アプリを開発する際、プロフェッショナルな印象を与える独自ドメインメールは重要です。この方法なら、コストを抑えながら信頼性の高いメール環境を構築できます。

---

**関連情報**
- [Cloudflare Email Routing公式ドキュメント](https://developers.cloudflare.com/email-routing/)
- [Gmail送信制限について](https://support.google.com/mail/answer/22839)