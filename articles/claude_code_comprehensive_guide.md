---
title: "【最新版】Claude Codeをより便利に使いたいあなたへ"
emoji: "💭"
type: "tech"
topics: ["claude", "ai","setup"]
published: true
---

## はじめに

この記事は、https://www.youtube.com/watch?v=n7iT5r0Sl_Y の動画を見て実際に使い込みながら機能を深掘りして調べた内容をまとめたものです。

動画で紹介されていた基本的な機能に加えて、公式ドキュメントや実際の使用体験を通じて発見した便利な機能、隠れた機能、そして実際に開発で使ってみて「これは便利！」と感じた機能を中心に整理しています。
Claude Codeを始めて使う方から、既に使っているけれどもっと効率的に活用したい方には役立つ情報かと思います。

## この記事で取り扱わない情報
* CLAUDE.md
* .claude/ ディレクトリでのカスタマイズ

これらは使用者に大きく依存するので人に聞くより自分で考えて君だけの最強のClaudeを作ろう！

## 基本操作

*   **VS Code拡張機能**: VS CodeやCursorから簡単にClaude Codeを起動するための拡張機能が提供されています。
*   **複数ペイン**: 複数のClaude Codeセッションを同時に開いて、並行して作業を進めることが可能です。
*   **メッセージキューイング**: Claudeが応答を生成している最中に、次のプロンプトを入力してキューに入れておくことができます。これにより、待ち時間なしで連続してタスクを依頼できます。
*   **タブ補完**: リポジトリ内のファイルやフォルダを素早く参照できます。
*   **URLの直接ペースト**: プロンプトと一緒にURLを貼り付けることで、Claudeが内容を取得して読み込めます。
*   **画像のペースト**: `Ctrl + V` を使用します（macOSでも `Cmd + V` ではなく `Ctrl + V`）。
*   **ファイルのドラッグ＆ドロップ**: `Shift` キーを押しながらファイルをターミナルにドラッグ＆ドロップすると、ファイルを開かずにパスを挿入できます。
*   **応答の停止**: `Esc` キー
*   **履歴の参照**:
    *   `↑` (上矢印キー): 過去のプロンプトを遡る。
    *   `Esc` → `Esc`: 現在のセッション内のメッセージ一覧を表示してジャンプする。

## スラッシュコマンド

*   `/model`: 使用するAIモデルを切り替えます。
    *   `Opus`: 最も高性能なモデル。複雑なタスク向け。
    *   `Sonnet`: 高速でコスト効率が良いモデル。
    *   `Default`: 使用量に応じてOpusとSonnetを自動で切り替える推奨設定。
*   `/clear`: 会話履歴（コンテキスト）を完全に消去します。新しいタスクを始める際に実行することで、トークンを節約し、AIの応答精度を高めることができます。
*   `/compact`: 会話履歴を要約してコンテキストを管理します。`/clear`と異なり、重要な情報を保持しながら古い部分を圧縮します。
*   `/install-github-app`: リポジトリにGitHub Appをインストールし、プルリクエストの自動レビュー機能を有効にします。
*   `/terminal-setup`: `Shift+Enter`で改行できるようにキーバインドを設定します。
*   `/vim`: Vimモードを有効/無効にします。
*   `/ide`: IDE連携を有効にして、開いているファイルやリンターの警告を確認できるようにします。

## モード

### プランモード（Plan Mode）
*   **手動プランモード**: `Shift+Tab`を2回押すことで有効化。読み取り専用環境でコードベースを探索し、ファイルに触れることなく包括的な戦略を策定できます。
*   **利点**: 実装前に計画を立てて確認する、経験豊富なエンジニアの自然な作業フローを模倣し、アーキテクチャの一貫性を保ちます。

### 拡張思考モード
プロンプトに特定のキーワードを含めることで、Claudeにより多くの計算時間を与えることができます：
*   `think` < `think hard` < `think harder` < `ultrathink`
*   それぞれ段階的により多くの思考バジェットが割り当てられ、複雑な問題により深く取り組めます。

## 生産性を高める使い方

*   **権限確認のスキップ**: 毎回ファイル編集やコマンド実行の許可を求められるのを防ぐため、以下のコマンドでClaude Codeを起動すると、すべての操作が自動で許可されます。
    ```bash
    claude --dangerously-skip-permissions
    ```
*   **GitHub PRレビューのプロンプトカスタマイズ**: `/.github/workflows/claude-code-review.yml` ファイルを編集することで、PRレビューの指示をカスタマイズできます。バグとセキュリティ問題に絞って簡潔に報告させるプロンプト例：
    ```yaml
    # direct_prompt: の下を編集
    Please review this pull request and look for bugs and security issues. Only report on bugs and potential vulnerabilities you find. Be concise.
    ```

## 個人的に特に良かった機能

*   **権限確認のスキップ**: 毎回ファイル編集やコマンド実行の許可を求められるのは、スムーズな開発の妨げになります。以下のコマンドでClaude Codeを起動することで、すべての操作が自動で許可され、思考を中断することなく作業に集中できます。
    ```bash
    claude --dangerously-skip-permissions
    ```
*   **プランモード**: `Shift+Tab`を2回押すだけで、安全な読み取り専用環境でアーキテクチャを理解し、実装前に包括的な計画を立てられます。
*   **画像のペースト**: 通常の `Cmd+V` ではペーストできませんが、`Ctrl+V` を使うことでクリップボードの画像を直接Claudeに貼り付けられます。
*   **GitHub PRの自動レビュー**: `/install-github-app` コマンド一つで、プルリクエストのコードレビューを自動化できます。

## 参考元

本まとめは、以下の動画の内容に基づき、最新の機能情報を追加して作成しています。

*   **元動画**: https://www.youtube.com/watch?v=n7iT5r0Sl_Y
*   **関連ブログ記事**: [builder.io/blog/claude-code](https://builder.io/blog/claude-code)
*   **関連ツール (Fusion)**: [fusion.builder.io](https://fusion.builder.io)
*   **公式ドキュメント**: [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/overview)
*   **Anthropic公式ベストプラクティス**: [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)