---
title: "【初心者向け】terraformでAWSリソースを爆速構築"
emoji: "🦔"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["terraform" , "aws" , "lambda" , "sns" , "sqs"]
published: true
---

## 初めに

CI/CDを組む記事を書こうとしたがまずはIaC(※)でインフラリソースを管理するところから始めた方がいいと思いterraformでAWSのリソースを管理したいと思います。
本項目を実施したい場合は 以下を実施してください。

1. [terraform](https://developer.hashicorp.com/terraform/downloads) のインストール
2. [AWS](https://aws.amazon.com/jp/)のアカウント登録
3. [AWS CLI](https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/getting-started-install.html)のインストール
4. [Github](https://github.com/)のアカウント登録

※**Infrastructure as Code**の略。インフラをコードで管理する。

## tfstateファイルについて

terraformが管理しているリソースの現在の状態を表すファイル。
terraformを介して追加したリソースはtfstateファイルに追加され、
terraformを介して削除したリソースはtfstateファイルから削除される。

tfstateファイルと実行したtfファイルを比較してリソースを作ったり消したりする。
デフォルトではローカルに生成されますが、S3 , GCS のようなstorageに生成して管理する方がチームで開発・運用しやすいです。

### tfstateファイルをS3で管理する

aws cliのconfig設定(※やってない人のみ)

AWS CLI インストール後以下のコマンドを実施し、configが設定されているか確認。

```
> aws configure list
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key                <not set>             None    None
secret_key                <not set>             None    None
    region                <not set>             None    None
> 
```

上記の様にValueが<not set>の場合は設定されていないので以下のコマンドで設定

`aws configure`

AWS Access Key ID 
→ AWSコンソール右上のユーザ名→セキュリティ認証情報→アクセスキーIDを入力

AWS Secret Access Key 
→アクセスキーのSecretを入力(アクセスキーを作った時にcsvをダウンロードするのがオススメ)

Default region name
→ほとんどの人は ap-northeast-1になる

Default output format
→jsonでもなんでも好きなものを

### S3バケットを手動作成する

1. AWSコンソールにアクセス
2. S3に移動
3. "バケットを作成" でバケットを作る

### 空のgitリポジトリを作成し、それをローカルに持ってくる

1. [Github](https://github.com/)にアクセス
2. 新しいリポジトリを作成
3. 以下のコマンドでローカルに持ってくる(${hoge*}は自分のリポジトリのものを記載)

`git clone https://github.com/${hoge1}/${hoge2}.git`

### S3 のtfstateファイル参照するように backend.tf を作る

```
terraform {
    required_version = "1.4.6"
  backend "s3" {
    bucket = "1で作ったバケット名"
    key    = "terraform.state"
    region = "ap-northeast-1"
  }
}

provider "aws" {
  region = "ap-northeast-1"
}
```

### terraform initの実施

`terraform init`

## terraformでリソースを管理する

今回は安いSNSとSQSをつくります。

### SNS作成例

```
resource "aws_sns_topic" "terraform_test" {
  name = "terraform-test"
}
```
	
### SQS作成例

```
resource "aws_sqs_queue" "terraform_queue" {
  name                      = "terraform-test"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  tags = {
    description = "test"
  }
}
```

### テストの実施


```
#構文チェック
terraform validate

#dry-run
terraform plan
```

### デプロイの実施

`terraform apply`

## resource、data、moduleについて

### resource

インフラ上へ作成するリソースを定義します。

### data

既存のリソースを読み込みます。例えば

```
data "aws_s3_bucket" "zukkie_terraform_state" {
  bucket = "zukkie-terraform-state"
}

resource "aws_sns_topic" "terraform_test2" {
  name = "terraform-test2"
  tags = data.aws_s3_bucket.zukkie_terraform_state
}
```

と定義すれば tags にzukkie-terraform-stateバケットの情報を定義することが出来ます。
(普通↑のような使い方はしません。)
[Route53のオリジンにS3を設定する時](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/s3_bucket)etc...役立つ状況は様々です。

### module

terraformコードを分割する事が出来ます。例えば先ほどのsqsリソースを分割すると

**module.tf**

```
module "sqs" {
  source  = "./module/sqs"
  name = "terraform-test-sqs"
}
```

**./module/sqs/main.tf**

```
resource "aws_sqs_queue" "terraform_queue" {
  name                      = var.name
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  tags = {
    description = "test"
  }
}
```

**./module/sqs/variables.tf**

```
variable "name" {
  type = string
}
```

と定義することで先ほどと同様のリソースが作成出来ます。
またvariableブロックを使う事で変数を渡すことも可能です。
開発環境と本番環境で設定値が違うリソースを作りたい時など、resourceを1つだけ書いて異なる設定値を変数で渡すだけで済むので視認性がよくなります。

## tfstateファイル に対して使えるコマンド

### terraform import

tfstateファイルにリソースを追加したい場合は terraform import コマンドを使います。

手動で作ったリソースをterraformで管理したい場合などに使います。
試しに 手動で作ったtfstateファイルを保存しているS3をimportします。

```
#これを定義しないと失敗する
resource "aws_s3_bucket" "bucket" {
  name = "zukkie-terraform-state"
}
```

`terraform import aws_s3_bucket.bucket zukkie-terraform-state`

※terraform v1.5.0で[importブロック](https://zukkie.link/terraform-v1-5-0%e3%81%a7%e8%bf%bd%e5%8a%a0%e3%81%95%e3%82%8c%e3%81%9fimport%e3%83%96%e3%83%ad%e3%83%83%e3%82%af%e3%82%92%e4%bd%bf%e3%81%a3%e3%81%a6%e3%81%bf%e3%82%8b/)なるものが実装される神アプデがあったのでコード内で完結するようになりました。

### terraform state list

terraform state listコマンドで実際にimportされたか確認します。

```
> terraform state list
data.aws_s3_bucket.zukkie_terraform_state
aws_s3_bucket.bucket
aws_sns_topic.terraform_test
aws_sns_topic.terraform_test2
module.sqs.aws_sqs_queue.terraform_queue
> 
```

### terraform state rm

importの逆でstateファイルから削除したい場合はterraform state rmコマンドを使います。
terraformから切り離したい場合などに使います。
さっきimportしたS3をstateから削除します。

```
#dry-run(テスト)
terraform state rm -dry-run 'aws_s3_bucket.bucket' 

#実際に消す
terraform state rm 'aws_s3_bucket.bucket' 
```

## 小技

terraform destroyコマンドというリソースを削除するコマンドがありますが
削除したいリソースがある時は対象のリソースをコメントアウトしてterraform applyをすればOK

理由は terraform は tfstateファイルとtfファイルを比較してtfファイルの方に合わせる様にリソースを作成・削除するためです。

## 最後に

今回の内容を[Githubリポジトリ](https://github.com/zukizukizuki/aws-terraform/tree/f7363cf9c1bd162972c0f08f2465f44906b1485c)で公開しているのでいちいち書くのが面倒な人は
git cloneするなり利用してください。