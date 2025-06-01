# Zenn記事クロスポストツール

このディレクトリには、Zennの記事を他のプラットフォーム（Qiita、WordPress、はてなブログなど）に展開するためのツールが含まれています。

## 必要なパッケージ

以下のパッケージをインストールしてください：

```bash
pip install requests pyyaml markdown
```

## 使用方法

### 1. 記事のエクスポート

`export_articles.py`を使用して、Zennの記事を他のプラットフォーム用にエクスポートできます。

```bash
# Qiita形式にエクスポート
python scripts/export_articles.py --format qiita --output ./exported_qiita

# WordPress形式にエクスポート
python scripts/export_articles.py --format wordpress --output ./exported_wp

# はてなブログ形式にエクスポート
python scripts/export_articles.py --format hatena --output ./exported_hatena
```

### 2. 記事の自動投稿

`cross_post.py`を使用して、Zennの記事を他のプラットフォームに自動投稿できます。

#### 設定

初回実行時に`~/.cross_post_config.json`が作成されます。このファイルに各プラットフォームのAPIキーなどを設定してください：

```json
{
  "qiita": {
    "access_token": "あなたのQiita APIトークン",
    "enabled": true
  },
  "wordpress": {
    "url": "あなたのWordPressサイトのURL",
    "username": "ユーザー名",
    "password": "パスワードまたはアプリケーションパスワード",
    "enabled": true
  }
}
```

#### 実行

```bash
python scripts/cross_post.py path/to/your/article.md
```

### 3. GitHub Actionsによる自動クロスポスト

`.github/workflows/cross_post.yml`を使用すると、GitHubリポジトリにプッシュされた記事を自動的に他のプラットフォームに投稿できます。

#### 設定

GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」で以下のシークレットを設定してください：

- `QIITA_TOKEN`: QiitaのAPIトークン
- `QIITA_ENABLED`: `true`または`false`
- `WP_URL`: WordPressサイトのURL
- `WP_USERNAME`: WordPressのユーザー名
- `WP_PASSWORD`: WordPressのパスワードまたはアプリケーションパスワード
- `WP_ENABLED`: `true`または`false`

これらを設定すると、`main`ブランチに記事がプッシュされたときに自動的にクロスポストされます。

## 注意事項

- 各プラットフォームのAPIの利用制限に注意してください。
- APIキーやパスワードは安全に管理してください。
- 画像やリンクのパスは、各プラットフォームに合わせて調整が必要な場合があります。