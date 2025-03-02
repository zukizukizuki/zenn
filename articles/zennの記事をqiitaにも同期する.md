---
title: "zennの記事をQiitaにも同期する"
emoji: ✨
type: tech
topics: ["zenn", "qiita", "sync"]
---

# zennの記事をQiitaにも同期する

この記事では、Zennの記事をQiitaに同期するために、[zenn-qiita-sync](https://github.com/C-Naoki/zenn-qiita-sync) ツールを使用し、GitHub Actions で自動化する手順を説明します。

1.  **Qiitaのトークンを取得** (readとwriteの権限が必要です)。Qiitaの個人設定画面からトークンを発行してください。
2.  **GitHubのトークンを取得** (repoとworkflowの権限が必要です)。GitHubの個人設定画面からトークンを発行してください。
3.  **GitHub Secrets にトークンを設定**。 GitHubリポジトリのSettings -> Secrets -> Actions から、`QIITA_TOKEN` と `GITHUB_TOKEN` を登録します。
4.  Zennに記事を作成し、mainブランチにpushすると、GitHub Actions が実行され、Qiitaに記事が同期されることを確認します。このリポジトリでは、`.github/workflows/publish.yml` にて [C-Naoki/zenn-qiita-sync@main](https://github.com/C-Naoki/zenn-qiita-sync) アクションが設定されており、mainブランチへのpushをトリガーに自動的にQiitaへの同期が行われます。
5.  Qiitaで記事が正しく同期されていることを確認します。