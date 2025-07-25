---
title: "【上級編】bashシェルスクリプト 裏技 4選"
emoji: "🏦"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [bash , 裏技, trap]
published: true
---

bashシェルスクリプトには、効率的で強力なコードを書くための様々な裏技があります。本記事では、知られざる4つの裏技を紹介します。これらのテクニックを使いこなせば、より柔軟で堅牢なスクリプトを作成できるでしょう。

## 1. プロセス置換

プロセス置換を使うと、コマンドの出力を一時ファイルを作らずに他のコマンドの入力として使えます。

従来の方法：

```
ls dir1 > temp1.txt
ls dir2 > temp2.txt
diff temp1.txt temp2.txt
rm temp1.txt temp2.txt
```

プロセス置換を使用：

```
diff <(ls dir1) <(ls dir2)
```

プロセス置換を使うと、一時ファイルの作成と削除が不要になり、コードがシンプルになります。また、ディスクI/Oを減らせるので、特に大量のデータを扱う場合にパフォーマンスが向上します。

## 2. ヒアドキュメント

ヒアドキュメントを使えば、複数行のテキストを簡単にコマンドの入力として扱えます。

例：

```
cat <<EOF | sed 's/bash/zsh/g' > output.txt
This is a bash script.
We love bash!
EOF
```

このスクリプトは、テキスト内の「bash」を「zsh」に置換してoutput.txtに保存します。

## 3. 連想配列の活用

bashの配列と連想配列を活用すると、複雑なデータ構造を扱えるようになります。

配列の例：

```
fruits=("apple" "banana" "cherry")
echo ${fruits[1]}  # banana
```

連想配列の例：

```
declare -A colors
colors[apple]="red"
colors[banana]="yellow"
echo ${colors[apple]}  # red
```

## 4. トラップを使った特定シグナルの処理

トラップ機能を使うと、特定のシグナルに対して処理を指定できます。これにより、スクリプトの終了時やユーザーの割り込み時など、特定の状況下で適切な処理を行うことができます。

以下は、SIGINTシグナル（Ctrl+Cによる中断）とEXITイベント（スクリプトの終了）を処理する完全なスクリプト例です：

```
#!/bin/bash

# 一時ファイルの作成
touch tempfile.txt

# クリーンアップ関数の定義
cleanup() {
    echo "Cleaning up..."
    rm -f tempfile.txt
}

# SIGINT（Ctrl+C）のハンドラ
handle_sigint() {
    echo "Caught SIGINT (Ctrl+C)"
    cleanup
    exit 1
}

# EXITイベントとSIGINTシグナルにトラップを設定
trap cleanup EXIT
trap handle_sigint SIGINT

# メインの処理
echo "Script is running. Press Ctrl+C to interrupt."
count=0
while [ $count -lt 10 ]; do
    echo "Working... $count"
    sleep 1
    count=$((count + 1))
done

echo "Script completed normally."
```

このスクリプトの特徴：

1. `cleanup` 関数: 一時ファイルを削除するクリーンアップ処理を定義しています。

2. `handle_sigint` 関数: Ctrl+Cが押された時の処理を定義しています。クリーンアップを実行してから終了します。

3. `trap cleanup EXIT`: スクリプトが終了する際（正常終了、エラー終了問わず）に `cleanup` 関数を実行します。

4. `trap handle_sigint SIGINT`: Ctrl+Cが押された時に `handle_sigint` 関数を実行します。

5. メインの処理: 10秒間カウントアップしながら処理を行います。この間にCtrl+Cを押すと、`handle_sigint` 関数が呼び出されます。

このスクリプトを実行すると、以下のような動作が期待できます：

- 正常に完了した場合: 10秒後に処理が終了し、`cleanup` 関数が呼び出されます。
- Ctrl+Cで中断した場合: `handle_sigint` 関数が呼び出され、その後 `cleanup` 関数が実行されます。
- 他の方法で終了した場合（例：`kill`コマンド）: `cleanup` 関数のみが実行されます。

トラップを使用することで、スクリプトの終了時や特定のシグナルを受信した際の動作を細かく制御できます。これにより、リソースの適切な管理や、予期せぬ終了時の適切な対応が可能になります。

以上の4つの裏技を使いこなせば、より柔軟なbashスクリプトを作成できるでしょう。特に、プロセス置換とトラップの使用は、コードの簡潔さと堅牢性を大きく向上させます。ぜひ実際に試してみてください。