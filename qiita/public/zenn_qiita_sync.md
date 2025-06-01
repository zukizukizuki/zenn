---
title: zennの記事をQiitaにも同期する
private: false
tags:
  - zenn
  - qiita
  - sync
updated_at: '2025-03-02T17:59:24+09:00'
id: 773ea061b9c0875922e1
organization_url_name: null
slide: false
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
3.  **GitHub Secrets にトークンを設定**。 GitHubリポジトリのSettings -> Secrets -> Actions から、`QIITA_TOKEN` と `GH_TOKEN` を登録します。
4.  **GitHub Actionsの設定を確認**。このリポジトリでは、`.github/workflows/publish.yml` にて [C-Naoki/zenn-qiita-sync@main](https://github.com/C-Naoki/zenn-qiita-sync) アクションが設定されており、mainブランチへのpushをトリガーに自動的にQiitaへの同期が行われます。設定内容は以下の通りです。
    ```yaml
    name: Publish articles

    on:
      push:
        branches:
          - main
          - master
      workflow_dispatch:

    permissions:
      contents: write

    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: false

    jobs:
      publish_articles:
        runs-on: ubuntu-latest
        timeout-minutes: 5
        steps:
          - name: Checkout
            uses: actions/checkout@v4
            with:
              fetch-depth: 0

          - name: Setup Node.js
            uses: actions/setup-node@v3
            with:
              node-version: '20'

          - name: Get changed markdown files
            id: files
            run: |
              # Create an empty file first to ensure it exists even if no files match
              touch $GITHUB_WORKSPACE/changed_files.txt
              
              # Try to find changed markdown files, but don't fail if none are found
              git diff --name-only ${{ github.event.before }} ${{ github.sha }} | grep "^articles/.*\.md$" > $GITHUB_WORKSPACE/changed_files.txt || true
              
              # If running manually or if before/after SHAs aren't available, check the last commit
              if [ -z "${{ github.event.before }}" ] || [ "$(wc -l < $GITHUB_WORKSPACE/changed_files.txt)" -eq 0 ]; then
                echo "No files found in normal diff, checking last commit..."
                git diff --name-only HEAD~1 HEAD | grep "^articles/.*\.md$" > $GITHUB_WORKSPACE/changed_files.txt || true
              fi
              
              # If still no files found and this is a PR for a specific article, add it manually
              if [ "$(wc -l < $GITHUB_WORKSPACE/changed_files.txt)" -eq 0 ] && [[ "${{ github.event.pull_request.title }}" == *"#"* ]]; then
                PR_NUM=$(echo "${{ github.event.pull_request.title }}" | grep -o '#[0-9]*' | tr -d '#')
                if [ -n "$PR_NUM" ] && [ -f "articles/openhands_introduction.md" ]; then
                  echo "articles/openhands_introduction.md" > $GITHUB_WORKSPACE/changed_files.txt
                fi
              fi
              
              echo "📋 Changed markdown files:"
              cat $GITHUB_WORKSPACE/changed_files.txt
              
              # Set output variable to indicate if we found any files
              if [ "$(wc -l < $GITHUB_WORKSPACE/changed_files.txt)" -gt 0 ]; then
                echo "found_files=true" >> $GITHUB_OUTPUT
              else
                echo "found_files=false" >> $GITHUB_OUTPUT
              fi
            shell: bash

          - name: Install qiita-cli
            if: steps.files.outputs.found_files == 'true'
            run: |
              npm install @qiita/qiita-cli --save-dev
            shell: bash

          - name: Run zenn-qiita-sync
            if: steps.files.outputs.found_files == 'true'
            uses: C-Naoki/zenn-qiita-sync@main
            with:
              qiita-token: ${{ secrets.QIITA_TOKEN }}
    ```
5.  Zennに記事を作成し、mainブランチにpushすると、GitHub Actions が実行され、Qiitaに記事が同期されることを確認します。