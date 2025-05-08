---
title: "【解決済】Macでインストール済みのコマンドが \"command not found\" になった時の対処法"
emoji: "🍎"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [terraform , Mac, brew , error]
published: true
---

## 前提
- チップ : Apple M3 Pro
- OS : Sequoia 15.4

Macで開発作業をしていると、ある日突然、いつも使っていたはずのコマンド (`terraform` や `brew` など) が「command not found」と表示されて焦ることがありますよね。
```bash
❯ terraform init
zsh: command not found: terraform
❯ brew
zsh: command not found: brew
❯ tree
zsh: command not found: tree
```
こんな状況に陥った方向けに、私が実際に解決した手順を共有します。多くの場合、**環境変数 `PATH` の設定**に問題があることが原因です。`PATH` とは、コマンドを実行する際にシェルが実行ファイルを探しに行くディレクトリのリストのことです。

## 原因の特定と解決ステップ
主に以下のステップで確認・修正していきます。ここでは `zsh` (Z Shell) と `Homebrew` を利用している環境を前提とします。

### ステップ1: Homebrew が正しく機能しているか確認する (フルパス指定)
まず、Homebrew 自体がインストールされていて、実行ファイルが存在するかを確認します。お使いの Mac の種類によって Homebrew のインストールパスが異なります。
*   **Apple Silicon Mac (M1, M2 など) の場合:**
    Homebrew の実行ファイルは通常 `/opt/homebrew/bin/brew` にあります。
    ```bash
    /opt/homebrew/bin/brew --version
    ```
*   **Intel Mac の場合:**
    Homebrew の実行ファイルは通常 `/usr/local/bin/brew` にあります。
    ```bash
    /usr/local/bin/brew --version
    ```
このコマンドを実行して、Homebrew のバージョン情報が表示されれば、Homebrew 自体は存在しています。もしここでエラーが出る場合は、Homebrew の再インストールが必要かもしれません。
今回、私の環境 (Apple Silicon Mac) では、以下のように `brew shellenv` というHomebrewの環境設定を出力するコマンドをフルパスで実行できました。これは Homebrew のコア機能が生きている証拠です。

```bash
❯ /opt/homebrew/bin/brew shellenv
export HOMEBREW_PREFIX="/opt/homebrew";
export HOMEBREW_CELLAR="/opt/homebrew/Cellar";
export HOMEBREW_REPOSITORY="/opt/homebrew";
# ... (中略) ...
PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/Users/shuhei.yamaoka/.rd/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin"; export PATH;
# ... (以下略) ...
```

この出力の中にある `PATH="/opt/homebrew/bin:/opt/homebrew/sbin:..."; export PATH;` という部分が、Homebrew のコマンドを使えるようにするための重要な設定です。これが現在のシェルに読み込まれていないため、コマンドが見つからない状態になっていました。

### ステップ2: Homebrew の環境設定をシェル設定ファイルに追加する
次に、ステップ1で確認した Homebrew の環境設定を、シェルの設定ファイル (`.zshrc`) に自動的に読み込ませるようにします。これにより、ターミナルを起動するたびに手動で設定する必要がなくなります。
以下のコマンドを実行して、`brew shellenv` の実行結果を評価・実行するコマンドを `.zshrc` ファイルの末尾に追記します。

*   **Apple Silicon Mac (M1, M2 など) の場合:**
    ```bash
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
    ```
*   **Intel Mac の場合:**
    ```bash
    echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
    ```
私の場合は Apple Silicon Mac なので、上のコマンドを実行しました。

```bash
❯ echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
```

**ポイント:**
`eval "$(...)"` という形式は、括弧内のコマンド (`/opt/homebrew/bin/brew shellenv`) を実行し、その標準出力を現在のシェルでコマンドとして評価・実行するという意味です。Homebrew の `shellenv` コマンドは、必要な環境変数 (主に `PATH`) を `export` するコマンド文字列を出力するので、それを `eval` で実行することで設定が適用されます。

### ステップ3: シェル設定ファイルを再読み込みする
`.zshrc` に変更を加えただけでは、現在のターミナルセッションには反映されません。以下のコマンドで設定を再読み込みするか、ターミナルウィンドウを一度閉じて新しく開きます。

```bash
source ~/.zshrc
```

これを実行すると、`.zshrc` が読み込まれ、新しい `PATH` 設定が適用されます。
(もし `source ~/.zshrc` 実行時に `.zshrc` 内の他のコマンドでエラーが出る場合は、そのエラーも別途対処が必要な場合がありますが、今回は `PATH` の問題が主目的です。私の場合、`sheldon` というコマンドに関するエラーが出ましたが、Homebrew の `PATH` が通ったことで、もし `sheldon` が Homebrew で管理されていれば、次回ターミナル起動時や再度 `source ~/.zshrc` した際に解決する可能性があります。)

### ステップ4: コマンドが使えるか確認する
最後に、問題のコマンドが使えるようになったか確認しましょう。

```bash
brew --version
terraform --version
tree --version
```

私の環境では、これで以下のように各コマンドのバージョン情報が無事表示されるようになりました！🎉

```
❯ brew --version
terraform --version
tree --version
Homebrew 4.5.1
Terraform v1.11.4
on darwin_arm64
+ provider registry.terraform.io/hashicorp/aws v5.43.0
+ provider registry.terraform.io/hashicorp/awscc v1.4.0
tree v2.2.1 © 1996 - 2024 by Steve Baker, Thomas Moore, Francesc Rocher, Florian Sesser, Kyosuke Tokoro
```

## まとめ
Mac で Homebrew 経由でインストールしたコマンドが `command not found` になった場合、多くは `PATH` 環境変数の設定がシェルの設定ファイル (`.zshrc` など) から漏れてしまっているか、正しく設定されていないことが原因です。
Homebrew が推奨する `eval "$(/path/to/brew shellenv)"` (お使いの Mac の種類に合わせたパスで) をシェルの設定ファイルに追記し、再読み込みすることで、この問題は解決できます。
もし同様の症状で困っている方がいれば、この手順が助けになれば幸いです！
