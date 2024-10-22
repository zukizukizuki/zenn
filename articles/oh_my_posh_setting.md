---
title: "Windows環境でOh My Poshをインストール・テーマ切り替え手順"
emoji: "🥪"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [windows , powershell, Terminal]
published: true
---

## Oh My Poshのインストール

まずは、Wingetを使ってOh My Poshをインストールします。

```
winget install JanDeDobbeleer.OhMyPosh -s winget
```

## PowerShellのプロファイルに設定を追加

PowerShellのプロファイルファイルに、Oh My Poshの初期化コードを追加して、PowerShellを起動するたびにOh My Poshが有効になるようにします。

### 手順

1. プロファイルファイルを編集します。

   ```
   notepad $PROFILE
   ```

2. ファイルに以下のコードを追加して、テーマ`paradox`を使用するように設定します。

   ```
   Import-Module posh-git
   oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\paradox.omp.json" | Invoke-Expression
   ```

3. 保存して閉じ、PowerShellを再起動します。

## テーマの確認と切り替え

### 利用可能なテーマの一覧表示

現在インストールされているOh My Poshのテーマを確認するには、以下のコマンドを実行します。

```
Get-PoshThemes
```

### テーマのプレビュー

特定のテーマを一時的にプレビューするには、以下のコマンドを使用します。`<theme-name>`にはプレビューしたいテーマ名を入力します。

```
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\<theme-name>.omp.json" | Invoke-Expression
```

### テーマの切り替えを永続化

気に入ったテーマを永続的に使用するためには、プロファイルファイルにそのテーマを設定します。

1. プロファイルファイルを再度開きます。

   ```
   notepad $PROFILE
   ```

2. 既存のテーマ設定を新しいテーマに変更します。例えば、`jandedobbeleer`に変更する場合:

   ```
   oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\jandedobbeleer.omp.json" | Invoke-Expression
   ```

3. 保存してPowerShellを再起動します。

## フォントの設定

Oh My Poshのシンボルを正しく表示するためには、対応するフォント（例：Nerd Fonts）をインストールし、VSCodeやWindows Terminalに設定する必要があります。フォントの設定手順については、以下のリンクから詳細を確認してください。

- [Nerd Fonts](https://www.nerdfonts.com/)

---

これで、Oh My Poshをインストールして、テーマを切り替える手順は完了です。自分に合ったテーマを見つけて、ターミナル環境をカスタマイズしましょう！
