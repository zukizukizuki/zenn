---
title: "サーバーレスを小学生でも分かる様に解説する試み"
emoji: "🚣‍♂️"
type: "idea" # tech: 技術記事 / idea: アイデア
topics: [AWS , SSM, EC2 , lambda , サーバレス]
published: true
---

## 従来の方式が抱えていた課題
昔のシステム開発では、オンプレミスのサーバーにOSをインストールし、その上にアプリケーションやミドルウェア(Webサーバー、DBMSなど)を設定するのが一般的でした。その後、仮想化技術の普及により、EC2などのクラウド上の仮想サーバーを利用するケースが増えました。しかし、これらの方式には以下のような課題があります。

- (オンプレミスの場合) サーバーのハードウェア調達とOSのインストールに手間と時間がかかる
- OSやミドルウェアのインストール・設定に専門知識が必要
- OSやミドルウェアのバージョンアップ、セキュリティパッチ適用などの保守作業が必要
- 利用者がいない時間帯でもサーバーを起動し続ける必要があり、コストがかかり続ける
- スケーリングのために設定変更が必要で、トラフィックの増減に柔軟に対応しづらい
- ストレージについても、容量の見積もりや増設の作業が必要

## サーバーレスの登場
こうした課題を解決するため、近年ではサーバーレスアーキテクチャが注目を集めています。主要なクラウドプロバイダーは以下のようなサーバーレス関数サービスを提供しています。

- AWS Lambda
- Google Cloud Functions
- Microsoft Azure Functions
- IBM Cloud Functions

これらのサービスでは、開発者はサーバーのプロビジョニングや管理をすることなく、コードを書くことに集中できます。関数は特定のイベントによってトリガーされ、必要な時にのみ実行されるため、コストも最適化されます。

これらを他のサーバーレスサービス(API Gateway、DynamoDBなど)と組み合わせることで、ハードウェアの調達やOSの設定、ミドルウェアの管理なしで、柔軟にスケーリングできるシステムを構築できます。

## サーバーレスで何ができる？
サーバーレスアーキテクチャを活用することで、様々なタイプのアプリケーションを構築できます。例えば:

- RESTful APIやWebサイトのバックエンド
 - API GatewayとLambdaを組み合わせることで、スケーラブルなバックエンドを構築できます。
- IoTのデータ処理パイプライン
 - IoTデバイスからのデータをKinesis StreamsやIoT Coreで収集し、Lambdaで処理してDynamoDBに保存できます。
- 画像や動画の変換処理
 - S3に画像や動画をアップロードし、それをトリガーにLambdaで変換処理を実行できます。
- 定期的なバッチ処理
 - CloudWatch Eventsをトリガーに、Lambdaで定期的なバッチ処理を実行できます。
- チャットボットやSlackの通知
 - API GatewayとLambdaを使って、チャットボットやSlackの通知機能を実装できます。

このように、サーバーレスは幅広いユースケースに対応できます。アプリケーションの要件に合わせて、適切なサービスを組み合わせることが重要です。

## サーバーレスのメリット
サーバーレスアーキテクチャには以下のようなメリットがあります。

- ハードウェア調達やOSのセットアップが不要で、すぐに開発を始められる
- OSやミドルウェアの管理が不要なので、アプリケーションのロジックに集中できる
- リクエストがあった時だけ実行されるので、コストを最小限に抑えられる
- 自動でスケーリングされるため、トラフィックの増減に柔軟に対応できる
- ストレージの容量を気にする必要がなく、必要に応じて自動で拡張される

## 費用の比較
月間1万PVの小規模なブログシステムをホストする場合で比較してみましょう

オンプレミスのサーバーを使う場合:
```
サーバー調達費用: 約20万円(3年リース換算で約5,600円/月)
ストレージ(500GB): 約5,000円
電力代: 約3,000円/月
管理者人件費: 約5万円/月
合計: 約6万円/月
※サーバールームのコストは除外
```

EC2(t2.micro)とRDS(db.t2.micro)を使う場合:
```
EC2インスタンス料金: 約800円
RDSインスタンス料金: 約1,000円
ストレージ料金(EBS 30GB): 約300円
合計: 約2,100円/月
```

サーバーレス(API Gateway + Lambda + DynamoDB)の場合:
```
API Gateway: 1万リクエスト分で約120円
Lambda: 128MBメモリ, 1秒の実行時間として約18円
DynamoDB: 1GBまで無料、それ以降は1GBあたり約25円
合計: 約140円/月
```

小規模なシステムであれば、サーバーレスが最もコストを抑えられる選択肢と言えます。

## 注意点
ただし、サーバーレスにも注意点があります。

- 実行時間に上限がある(Lambdaの場合は最大15分)
- コールドスタート(初回起動の遅延)が発生する可能性がある
- 大規模なシステムではEC2などの従来の方式の方が安くなるケースがある
- 全ての処理をサーバーレスで実装するのは難しい場合がある

ステートフルな処理やリアルタイム性が求められる処理など、一部の処理は従来の方式で実装した方が良いケースもあります。システムのアーキテクチャ設計では、サーバーレスと従来の方式を適切に組み合わせることが重要です。

## まとめ
サーバーレスアーキテクチャは、ハードウェア調達やOSセットアップ、ミドルウェアの管理の手間を大幅に減らせ、小規模なシステムではコストも抑えられる優れた選択肢です。AWS Lambda、Google Cloud Functions、Azure Functionsなどのサービスを活用することで、開発者はインフラではなくアプリケーションに集中できます。

また、Lambda@EdgeやCloudflare Workersなどのエッジコンピューティングサービスと組み合わせることで、レイテンシーを低減し、ユーザーにより近い場所で処理を実行できます。これによりコールドスタートの改善が期待できます。

一方で、全てのユースケースに適しているわけではありません。システムの要件をよく見極め、オンプレミス、EC2などの仮想サーバー、サーバーレス、エッジコンピューティングを適切に組み合わせることが重要です。それぞれの特性を理解し、自分のシステムに合ったアーキテクチャを設計することが、モダンなアプリケーション開発において欠かせないスキルと言えるでしょう。