---
title: OpenHandsを導入してAIアシスタントを活用する方法
private: false
tags:
  - OpenHands
  - AI
  - Docker
  - GitHub
updated_at: '2025-03-07T16:51:47+09:00'
id: e8e0e4fa41e51f398af1
organization_url_name: null
slide: false
---

## OpenHandsとは

OpenHandsは、AIアシスタントを活用してプログラミングやその他のタスクをサポートするツールです。Claude AIを搭載し、GitHubとの連携機能を持ち、開発作業を効率化します。

この記事では、Windows 11環境でOpenHandsを導入する手順を解説します。Windows 11が既にインストールされていることを前提としています。

## 導入手順

### 1. Dockerイメージのプルとコンテナの起動

まず、OpenHandsのDockerイメージをプルし、コンテナを起動します。

Windows PowerShellを開き、以下のコマンドを実行します：

```bash
# イメージをプル
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.27-nikolaik

# コンテナを起動
docker run -it --rm --pull=always `
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.27-nikolaik `
    -e LOG_ALL_EVENTS=true `
    -v /var/run/docker.sock:/var/run/docker.sock `
    -v ~/.openhands-state:/.openhands-state `
    -p 3000:3000 `
    --add-host host.docker.internal:host-gateway `
    --name openhands-app `
    docker.all-hands.dev/all-hands-ai/openhands:0.27
```

※ Windows powershellでは、バックスラッシュ（`\`）ではなく（`）を使用して複数行のコマンドを記述します。

### 2. GitHub Personal Access Tokenの取得

OpenHandsをGitHubと連携させるには、GitHub Personal Access Token (PAT) が必要です。

1. GitHubにログインします
2. 右上のプロフィールアイコンをクリックし、「Settings」を選択
3. 左側のメニューから「Developer settings」をクリック
4. 「Personal access tokens」→「Tokens (classic)」を選択
5. 「Generate new token」→「Generate new token (classic)」をクリック
6. トークンの名前を入力（例：「OpenHands」）
7. 以下のスコープを選択：
   - `repo` (すべてのリポジトリ権限)
   - `workflow` (ワークフロー権限)
   - `read:org` (組織の読み取り権限)
8. 「Generate token」をクリック
9. 表示されたトークンをコピーして安全な場所に保存（このトークンは再表示されないので注意）

### 3. API Keyの作成

OpenHandsはClaude AIを利用するため、API Keyが必要です。

#### Gemini APIキーの取得手順
1. **Google Cloud Platform (GCP) プロジェクトの作成**:
   - Google Cloud Platform ([https://cloud.google.com/](https://cloud.google.com/)) にアクセスし、Googleアカウントでログインします。
   - プロジェクトを作成します（まだプロジェクトがない場合）。プロジェクト名は任意で構いません。

2. **Gemini API の有効化**:
   - GCPのコンソール画面で、左上のメニューから「APIとサービス」 > 「有効なAPIとサービス」を選択します。
   - 「+ APIとサービスの有効化」をクリックし、検索窓に「Gemini API」と入力して検索します。
   - 「Gemini API」をクリックし、「有効にする」ボタンをクリックします。

3. **APIキーの作成**:
   - GCPのコンソール画面で、左上のメニューから「APIとサービス」 > 「認証情報」を選択します。
   - 「+ 認証情報を作成」をクリックし、「APIキー」を選択します。
   - APIキーが生成されます。このAPIキーはOpenHandsからGemini APIを呼び出す際に使用しますので、安全に保管してください。

#### Anthropic APIキーの取得手順
1. [Anthropicのウェブサイト](https://www.anthropic.com/)にアクセスし、アカウントを作成またはログイン
2. ダッシュボードから「API Keys」セクションに移動
3. 「Create API Key」をクリック
4. キーの名前を入力（例：「OpenHands」）
5. 生成されたAPI Keyをコピーして安全な場所に保存

### 4. OpenHandsの初期設定

コンテナを起動したら、ブラウザで以下のURLにアクセスします：

```
http://localhost:3000
```

初回アクセス時に、以下の情報の入力を求められます：

1. Claude API Key：ステップ3で取得したAPI Keyを入力
2. GitHub Personal Access Token：ステップ2で取得したトークンを入力

入力が完了すると、GitHubとの連携が確立され、OpenHandsを使用する準備が整います。

## OpenHandsの使い方

OpenHandsの基本的な使い方は以下の通りです：

1. ホーム画面からGitHubリポジトリを選択または新しいリポジトリを作成
2. リポジトリが読み込まれたら、AIアシスタントとチャットを開始
3. 自然言語でコードの作成や修正、質問などを行うことができます

例えば、以下のような指示を出すことができます：

- 「新しいReactコンポーネントを作成して」
- 「このコードのバグを修正して」
- 「このAPIの使い方を説明して」

AIアシスタントは指示に基づいてコードを生成したり、既存のコードを修正したり、説明を提供したりします。

