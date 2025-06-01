---
title: "【AWS】[instance value (\"AUTO\") not found in enum] エラーの対応方法"
emoji: "🥬"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , error, SQS , IAM , AWS IoT Core]
published: true
---


## 概要
AWSコンソールでIAMロールを作成しようとしたところ以下のようなエラーメッセージが表示される

```
[instance value ("AUTO") not found in enum (possible values: ["DE","EN","ES","FR","IT","JA","KO","PT_BR","ZH_CN","ZH_TW"])]
```

## 原因
エラーメッセージは言語コードが予期しない値（"AUTO"）になっている際に発生します。

## 解決方法

### ソース言語とターゲット言語を正しく指定する

1. AWSコンソールのログアウト
2. ブラウザのキャッシュクリア
3. AWSコンソールに再度ログイン
4. 右上のアカウント名をクリックし、「言語設定」を選択
5. ドロップダウンメニューから明示的に言語を選択（例：「English (US)」や「日本語」）
6. 変更を保存し、ページをリロード

### プライベートブラウジングモードでAWSコンソールにアクセス

## 最後に
私の場合、恐らくChromeの翻訳プラグインが作動していたことが原因
翻訳に関連する機能をオフにするだけでも解決する可能性はあります