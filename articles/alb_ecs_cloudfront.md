---
title: "ECS+ALB構成なのにCloudFrontの403エラー？ ハマりどころ満載のアセット表示トラブル解決記"
emoji: "🤔"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["aws", "ecs", "cloudfront", "s3", "rails"]
published: true
---

## はじめに

こんにちは！現在、AWS上で `ECS on Fargate` + `ALB` の構成でRailsアプリケーションを開発しています。
先日、ステージング環境でアセット（JavaScriptやCSS）が全く読み込まれず、画面が崩れてしまうという問題に直面しました。

ブラウザの開発者コンソールには、`403 Forbidden` や `CORS policy` といったエラーがずらり。Route 53の設定はALBを向いており、CloudFrontを使っているつもりはなかったのに、なぜかCloudFrontのエラーが出ている...。

この記事では、この一見不可解なエラーから始まり、AWSの設定を一つずつ見直してたどり着いた根本原因と、その解決までの全記録をまとめます。同じような構成でハマっている方の助けになれば幸いです。

### 対象の環境構成
- **アプリケーション:** Ruby on Rails (ECS on Fargateで実行)
- **ルーティング:** Route 53 -> ALB -> ECS
- **アセット配信:** CloudFront -> S3

## 遭遇したエラー：全ての始まり

最初にブラウザの開発者コンソールで確認したエラーは以下の通りです。

```
Access to script at 'https://xxxxxxxxxxxxxx.cloudfront.net/assets/application-[ハッシュ値].js' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.

GET https://xxxxxxxxxxxxxx.cloudfront.net/assets/application-[ハッシュ値].js net::ERR_FAILED 403 (Forbidden)
```

「CORSエラー」と「403 Forbidden」。これはWeb開発でよく見るエラーですが、奇妙な点がありました。

### 謎1：なぜCloudFrontにアクセスしているのか？

私たちのDNS設定は `app.example.com` (ALB) を指しており、CloudFrontを経由するレコードはありません。

```sh
; <<>> DiG 9.11.4-P2 <<>> app.example.com
;; ANSWER SECTION:
app.example.com. 60	IN	A	[ALBのIPアドレス]
app.example.com. 60	IN	A	[ALBのIPアドレス]
```

**原因の特定**:
調査の結果、ECSタスクの環境変数に `RAILS_ASSET_HOST` が設定されており、その値がCloudFrontのドメイン (`xxxxxxxxxxxxxx.cloudfront.net`) になっていました。
Railsの `asset_host` は、`javascript_include_tag` などで生成されるURLのホスト名を指定する設定です。つまり、**アプリケーションが返すHTML自体が「アセットはCloudFrontから読み込んでね」と指示していた**のです。

これで謎は解けました。トラブルの原因はCloudFrontにあると判断し、調査の的を絞りました。

## 第1の関門：403 Forbiddenとの戦い

CloudFrontが `403 Forbidden` を返す主な原因は、オリジン（今回はS3）へのアクセスに失敗していることです。これは通常、CloudFrontとS3間のアクセス許可設定に問題がある場合に発生します。

### 対応1：S3バケットポリシーの見直し

まず、CloudFrontディストリビューションとS3バケットポリシーを確認しました。

- **CloudFrontディストリビューションID**: `[今回のディストリビューションID]`
- **オリジンアクセス設定**: OAC (Origin Access Control) を使用

次に、S3バケットポリシーを確認すると、驚きの事実が判明しました。

```json:bad
{
    "Sid": "AllowCloudFrontServicePrincipal",
    "Effect": "Allow",
    "Principal": {
        "Service": "cloudfront.amazonaws.com"
    },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::[S3バケット名]/*",
    "Condition": {
        "ArnLike": {
            // 全く別のディストリビューションIDが指定されていた！
            "AWS:SourceArn": "arn:aws:cloudfront::[AWSアカウントID]:distribution/[別のディストリビューションID]"
        }
    }
}
```

ポリシーが許可していたのは、**全く別のCloudFrontディストリビューション**からのアクセスでした。これでは `[今回のディストリビューションID]` からのアクセスは当然ブロックされます。

そこで、既存のポリシーを壊さないように、新しいディストリビューションからのアクセス許可を追記しました。

```json:good
{
    "Version": "2008-10-17",
    "Id": "PolicyForCloudFrontPrivateContent",
    "Statement": [
        // ... 既存のStatement ...
        {
            "Sid": "AllowCloudFront-[今回のディストリビューションID]", // 一意なSidを追加
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::[S3バケット名]/*",
            "Condition": {
                "StringEquals": {
                    // 今回の正しいディストリビューションARNを指定
                    "AWS:SourceArn": "arn:aws:cloudfront::[AWSアカウントID]:distribution/[今回のディストリビューションID]"
                }
            }
        }
    ]
}
```

このポリシーを適用し、CloudFrontのデプロイを待ちました。

## 第2の関門：純粋なCORSエラーに変化

S3バケットポリシーを修正後、`403 Forbidden` は消えましたが、代わりに純粋なCORSエラーが残りました。

```
Access to script at 'https://xxxxxxxxxxxxxx.cloudfront.net/assets/...' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

これは大きな前進です。CloudFrontがS3からオブジェクトを取得できるようになったものの、そのレスポンスにCORSヘッダー（`Access-Control-Allow-Origin`など）が含まれていないことを意味します。

### 対応2：S3のCORS設定を追加

CloudFrontのビヘイビアには、ブラウザからの `Origin` ヘッダーをオリジン(S3)に転送する `Managed-CORS-S3Origin` ポリシーがアタッチされていました。このため、**S3バケット自体にCORS設定を追加する**必要があります。

S3バケットの「アクセス許可」タブから「CORS」設定を編集し、以下を追加しました。

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "HEAD"
        ],
        "AllowedOrigins": [
            "https://app.example.com" // アプリケーションのドメイン
        ],
        "ExposeHeaders": []
    }
]
```

設定後、CloudFrontのキャッシュを `/*` ですべて無効化しました。

## 最終関門：再び現れた403 Forbiddenと根本原因

これで解決かと思いきや、エラーは再び `403 Forbidden` に戻ってしまいました。しかし、今度のエラーは以前とは意味合いが異なります。

CORSエラーが消えた後の `403` は、多くの場合**「ファイルが存在しない」**ことを示唆しています。
セキュリティが設定されたS3バケットは、ファイルが存在しない場合でも `404 Not Found` ではなく `403 Forbidden` を返す仕様になっています。これは、攻撃者にファイル有無の情報を与えないためです。

### 原因の特定：デプロイの不整合

ブラウザがリクエストしているアセットのファイル名を改めて確認します。

`https://xxxxxxxxxxxxxx.cloudfront.net/assets/application-[ハッシュ値].js`

このハッシュ値を持つファイルが、本当にS3バケット内に存在するか検索したところ... **ありませんでした！**

**根本原因は、アプリケーションが参照しているアセットファイルと、実際にS3にデプロイされているアセットファイルが異なっていたことでした。**

### 最終的な解決策

原因がデプロイの不整合だとわかったので、やることは一つです。
**アプリケーションのデプロイパイプラインを再実行**し、`assets:precompile` で生成された最新のアセットをS3にアップロードしました。

結果、S3に正しいアセットファイルが配置され、無事に画面が表示されるようになりました。
