---
title: "【2025年最新版】AIレビューツール (CodeRabbit) 導入手順"
emoji: "🐳"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [github actions , コードレビュー , CodeRabbit , CI/CD , 自動化]
published: true
---

![](https://storage.googleapis.com/zenn-user-upload/42216e16abc9-20250227.jpg)

[この記事](https://zenn.dev/minedia/articles/7928ef7545b393)を参考に記載しました。
AIレビューツール CodeRabbit (fluxninja/openai-pr-reviewer) を GitHub Actions に導入し、今後の運用に役立てるための手順とコストについて、2025年最新版としてまとめました。

### 1. 導入手順

**前提条件:**

* **OpenAI APIキー:** OpenAI API を利用するためのAPIキーが必要です。OpenAI Platform ([https://platform.openai.com/](https://platform.openai.com/)) でアカウントを作成し、APIキーを発行してください。
* **GitHubアカウント:** CodeRabbit を導入する GitHub リポジトリへの管理者権限が必要です。

**手順:**

1. **GitHub Actions workflow ファイルの作成:**
   リポジトリの `.github/workflows` ディレクトリに、workflow ファイル (例: `code-review.yml`) を作成します。

```yaml
name: Code Review

permissions:
  contents: read
  pull-requests: write

on:
  pull_request:
  pull_request_review_comment:
    types: [created]

concurrency:
  group: ${{ github.repository }}-${{ github.event.number || github.head_ref || github.sha }}-${{ github.workflow }}-${{ github.event_name == 'pull_request_review_comment' && 'pr_comment' || 'pr' }}
  cancel-in-progress: ${{ github.event_name != 'pull_request_review_comment' }}

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
    - uses: fluxninja/openai-pr-reviewer@1.16.2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      with:
        debug: false
        review_simple_changes: false
        review_comment_lgtm: false
        openai_light_model: gpt-3.5-turbo
        openai_heavy_model: gpt-4
        system_message: |
          あなたは `@openai` (a.k.a. `github-actions`) です。
          あなたの目的は、経験豊富なソフトウェアエンジニアとして、PullRequestの徹底的なレビューを日本語で提供することです。
          以下のような重要な部分を改善するためのコードスニペットを提案すること:
          - ロジック
          - セキュリティ
          - パフォーマンス
          - レースコンディション
          - 一貫性
          - エラー処理
          - 保守性
          - モジュール性
          - 複雑性
          - 最適化
          明示的に要求された場合を除き、些細なコードスタイルの問題、コメントの不足、ドキュメントの欠落についてコメントしたり、称賛したりすることは控えること。
          コード全体の品質を向上させるために、重大な懸念事項を特定して解決することに集中し、些細な問題は無視すること。
          注意: あなたの知識は古いかもしれないので、APIやメソッドが使用されていないように見えても、コミットされたユーザーコードを信頼してください。
        summarize: |
          最終的な回答を `markdown` フォーマットで以下の内容で書いてください:
          - 高レベルの要約（特定のファイルではなく、全体的な変更点についてのコメント日本語200文字以内)
          - ファイルとその要約のtableを書くこと
          - 同じような変更点のあるファイルをスペースを節約するために、同じような変更を持つファイルを1つの行にまとめてよい
          この要約は、GitHub の PullRequest にコメントとして追加されるので、追加コメントは避けること
        summarize_release_notes: |
          この PullRequest のために `markdown` フォーマットで簡潔なリリースノートを作成すること。
          コードの目的とユーザーストーリーに焦点を当てること。
          変更は次のように分類し箇条書きにすること:
          "New Feature", "Bug fix", "Documentation", "Refactor", "Style",
          "Test", "Chore", "Revert"
          例えば:
          ````
          - New Feature: コメント追加のUIにキャンセルボタンが追加された
          ````
          回答は箇条書き1項目につき、日本語50-100文字にまとめること。
          この回答はリリースノートでそのまま使用されます。
          リリースノートの下に、この PullRequest の変更点についての短いお祝いのポエムを追加してください。
          このポエムを引用（ `>` ）として追加してください。ポエムには絵文字を使用できる
```

   **主要な設定項目:**

   * **`uses: fluxninja/openai-pr-reviewer@v2`**:  CodeRabbit アクションの利用を指定。最新タグは [Releases ページ](https://github.com/fluxninja/openai-pr-reviewer/releases) で確認
   * **`env.OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}`**:  OpenAI APIキーを GitHub Secrets から取得して設定。`OPENAI_API_KEY` は GitHub Secrets に登録する名前と一致させる。
   * **`openai_light_model: gpt-3.5-turbo`**: 高速レビュー用の OpenAI モデル。`gpt-3.5-turbo` は常に最新版が利用可能。
   * **`openai_heavy_model: gpt-4`**: 高品質レビュー用の OpenAI モデル。
   * **`system_message`**:  AIレビューの役割や指示を記述するプロンプト。日本語で詳細な指示を与えることで、より質の高いレビューが期待できる。
   * **`summarize`, `summarize_release_notes`**:  レビュー結果の要約やリリースノートの生成に関するプロンプト。出力フォーマットや内容を細かく指示できる。

2. **OpenAI APIキーを GitHub Secrets に登録:**
   リポジトリの設定画面 (Settings) > Secrets > Actions に移動し、「New repository secret」をクリックします。

   * **Name:** `OPENAI_API_KEY` (workflow ファイルの `env.OPENAI_API_KEY` で指定した名前と一致させる)
   * **Value:** OpenAI Platform で発行した APIキーを貼り付けます。

   「Add secret」ボタンをクリックして保存します。

3. **workflow の実行確認:**
   プルリクエストを作成または更新すると、workflow が自動的に実行されます。Actions タブで workflow の実行状況を確認できます。
   正常に完了すると、AIレビュー結果がプルリクエストにコメントとして投稿されます。

### 2. コスト (2025年最新版)

* **CodeRabbit (fluxninja/openai-pr-reviewer) 自体は無料** で利用できます。
* **OpenAI API の利用料金** が別途発生します。料金は従量課金制で、利用するモデルやトークン数によって変動します。

**OpenAI API 料金体系 (2025年時点):**

最新の料金体系は、必ず OpenAI Platform の料金ページ ([https://openai.com/pricing](https://openai.com/pricing)) で確認してください。

以下は2024年時点の料金例です (2025年には変更されている可能性があります):

| モデル                     | 入力 (1Kトークンあたり) | 出力 (1Kトークンあたり) |
|--------------------------|-----------------------|-----------------------|
| gpt-3.5-turbo (最新版)    | $0.001                | $0.002                |
| gpt-4                      | $0.03                 | $0.06                 |

* **無料枠:** OpenAI API は、新規アカウントに対して一定期間の無料利用枠を提供している場合があります。無料枠の範囲内であれば費用は発生しません。無料枠の有無や期間、トークン数は OpenAI のポリシーによって変更される場合があります。

**コストを抑えるためのポイント:**

* **`openai_light_model` の活用:** `openai_heavy_model` (gpt-4) よりも `openai_light_model` (gpt-3.5-turbo) の方が大幅に安価です。高速なレビューやコストを抑えたい場合は、`openai_light_model` を中心に利用しましょう。
* **レビュー頻度の調整:** 全てのプルリクエストで毎回レビューを実行するのではなく、必要に応じてレビューの実行頻度を調整します。例えば、規模の大きいプルリクエストや重要な変更を含むプルリクエストのみレビューを実行するなどの運用を検討します。
* **トークン制限の設定:** `summary_token_limits`, `review_token_limits` パラメータでトークン数を制限することで、API 利用量を抑制できます。ただし、制限を厳しくしすぎるとレビュー品質が低下する可能性があります。
* **レビュー対象ファイルの制限:** `path_filters` パラメータでレビュー対象ファイルを制限することで、API 利用量を削減できます。

### 3. トラブルシューティング (APIキー関連エラー)

`Error: OpenAI error 401: Incorrect API key provided` のような APIキー関連のエラーは、以下の原因が考えられます。

* **APIキーの入力ミス:** GitHub Secrets に登録したAPIキーが間違っている (タイプミス、コピーミスなど)。
* **APIキーの権限不足:** 設定したAPIキーが、利用しようとしているモデル (`gpt-3.5-turbo`, `gpt-4`) へのアクセス許可を持っていない。
* **APIキーの有効期限切れ/無効化:** APIキーが有効期限切れになっている、または OpenAI 側で無効化された。
* **workflow ファイルの設定ミス:** workflow ファイルで参照している GitHub Secrets 名が間違っているなど。

**対策:**

1. **APIキーの再確認:**
   * OpenAI Platform ([https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)) で APIキーを確認し、GitHub Secrets に登録しているキーと一致するか確認します。
   * 必要であれば、新しいAPIキーを生成し、GitHub Secrets に再設定します (古いキーは削除推奨)。

2. **GitHub Secrets の確認:**
   * GitHub リポジトリの Settings > Secrets > Actions で、`OPENAI_API_KEY` シークレットの設定を確認します。
   * シークレット名、値が workflow ファイルの設定と一致しているか確認します。

3. **workflow ファイルの確認:**
   * workflow ファイル (`.github/workflows/code-review.yml`) の `env.OPENAI_API_KEY` の設定が、GitHub Secrets のシークレット名を正しく参照しているか確認します。

4. **APIキーの権限確認:**
   * OpenAI Platform で、APIキーが利用可能なモデル (gpt-3.5-turbo, gpt-4) を確認します。APIキーの利用制限 (プロジェクト紐付けなど) がないか確認します。

5. **OpenAI API のステータス確認:**
   * OpenAI API のステータスページ ([https://status.openai.com/](https://status.openai.com/)) で、API サービスが正常に稼働しているか確認します (API 側の障害が原因の場合も稀にあります)。

### 4. まとめ
CodeRabbit は無料で高機能なAIレビューを GitHub Actions で実現できる強力なツールです。導入手順は比較的簡単で、YAML ファイルの設定とAPIキーの登録のみで利用開始できます。

運用コストは OpenAI API の利用料金に依存するため、モデル選択やレビュー頻度、トークン制限などを調整して、コストを最適化することが重要です。`gpt-3.5-turbo` と `gpt-4` を適切に使い分けることで、レビュー品質とコストのバランスを取ることが可能です。
