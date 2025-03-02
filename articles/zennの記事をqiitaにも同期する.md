---
title: "zennの記事をQiitaにも同期する"
emoji: ✨
type: tech
topics: ["zenn", "qiita", "sync"]
---

# zennの記事をQiitaにも同期する

この記事では、Zennの記事をQiitaに同期するために、[zenn-qiita-sync](https://github.com/C-Naoki/zenn-qiita-sync) ツールを使用し、GitHub Actions で自動化する手順を説明します。

1.  **Qiitaのトークンを取得** (readとwriteの権限が必要です)。以下の手順でQiitaの個人用アクセストークンを作成します。
    1.  [Qiita](https://qiita.com/) にアクセスします。
    2.  右上のプロフィールアイコンをクリックし、設定に移動します。
    3.  左側のメニューから「アプリケーション」を押下します。
    4.  「個人用アクセストークン」セクションで、「新しいトークンを発行する」をクリックします。
    5.  `read_qiita` と `write_qiita` のチェックボックスをオンにし、「発行する」をクリックします。
    6.  表示されたトークンを安全な場所に保管してください。
2.  **GitHubのトークンを取得** (repoとworkflowの権限が必要です)。以下の手順でGitHubの個人用アクセストークンを作成します。
    1.  [GitHub](https://github.com/) にアクセスします。
    2.  右上のプロフィールアイコンをクリックし、「Settings」に移動します。
    3.  左側のメニューから「Developer settings」をクリックします。
    4.  「Personal access tokens」 -> 「Tokens (classic)」をクリックします。
    5.  「Generate new token (classic)」をクリックします。
    6.  Note にトークンの説明 (例: "Qiita sync") を入力します。
    7.  `repo` と `workflow` のチェックボックスをオンにします。
    8.  「Generate token」をクリックします。
    9.  表示されたトークンを安全な場所に保管してください。
3.  **GitHub Secrets にトークンを設定**。 GitHubリポジトリのSettings -> Secrets -> Actions から、`QIITA_TOKEN` と `GITHUB_TOKEN` を登録します。
4.  Zennに記事を作成し、mainブランチにpushすると、GitHub Actions が実行され、Qiitaに記事が同期されることを確認します。このリポジトリでは、`.github/workflows/publish.yml` にて [C-Naoki/zenn-qiita-sync@main](https://github.com/C-Naoki/zenn-qiita-sync) アクションが設定されており、mainブランチへのpushをトリガーに自動的にQiitaへの同期が行われます。
5.  Qiitaで記事が正しく同期されていることを確認します。