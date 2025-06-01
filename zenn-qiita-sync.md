# ZennとQiitaの記事同期ガイド

このリポジトリでは、[zenn-qiita-sync](https://github.com/C-Naoki/zenn-qiita-sync)を使用して、Zennの記事を自動的にQiitaにも投稿しています。

## セットアップ手順

### 1. Qiitaアクセストークンの取得

1. [Qiitaのトークン発行ページ](https://qiita.com/settings/tokens/new)にアクセス
2. 以下の設定でトークンを作成
   - 説明: `zenn-qiita-sync用`
   - スコープ: `read_qiita`と`write_qiita`にチェック
3. 生成されたトークンをコピー（このトークンは一度しか表示されないので注意）

### 2. GitHubリポジトリにシークレットを設定

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」に移動
2. 「New repository secret」をクリック
3. 名前に`QIITA_TOKEN`、値に先ほどコピーしたQiitaアクセストークンを入力
4. 「Add secret」をクリック

### 3. 記事の書き方

通常のZenn記事と同じように記事を書きます。記事のフロントマターに`published: true`を設定すると、GitHub Actionsによって自動的にQiitaにも投稿されます。

```md
---
title: "記事タイトル"
emoji: "😊"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["JavaScript", "React", "TypeScript"]
published: true
---

記事の内容...
```

### 4. 記事の同期

1. 記事を`articles/`ディレクトリに保存
2. 変更をコミットしてGitHubにプッシュ
3. GitHub Actionsが自動的に実行され、Qiita形式の記事が`qiita/public/`ディレクトリに生成され、Qiitaにも投稿されます

## 注意点

- 画像ファイルは`images/`ディレクトリに保存してください
- Zennの記事を削除すると、対応するQiitaの記事も削除されます
- `books/`ディレクトリの本はQiitaに同期されません

## トラブルシューティング

GitHub Actionsの実行結果は「Actions」タブで確認できます。エラーが発生した場合は、ログを確認して対処してください。