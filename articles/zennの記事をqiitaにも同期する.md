---
title: "zennの記事をQiitaにも同期する"
emoji: ✨
type: tech
topics: ["zenn", "qiita", "sync"]
---

# zennの記事をQiitaにも同期する

この記事では、Zennの記事をQiitaに同期するために、[zenn-qiita-sync](https://github.com/C-Naoki/zenn-qiita-sync) ツールを使用した手順を説明します。

1.  Zennで記事を作成します。
2.  `zenn-qiita-sync` をインストールします。
   ```bash
   npm install -g zenn-qiita-sync
   ```
3.  `zenn-qiita-sync` を実行して、Zennの記事をQiitaに同期します。Qiitaのアクセストークンなどの環境変数を設定する必要がある場合があります。
   ```bash
   zenn-qiita-sync
   ```
4.  Qiitaで記事が正しく同期されていることを確認します。