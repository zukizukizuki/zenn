---
title: Terraform Cloudでstateを管理してgithub actionsでAWSを管理するCI/CDを組む
tags:
  - GitHub
  - AWS
  - IAM
  - OIDC
  - GitHubActions
private: false
updated_at: '2024-06-11T20:53:37+09:00'
id: 43dadccaff29528d04bc
organization_url_name: null
slide: false
ignorePublish: false
---
## 概要
従来はstateファイルをAWS S3 やGCP GCSで管理していたがTerraform Cloudで管理するメリットが大きい

## 従来のバケットでのstate管理
![terraformS3.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/1e89354d-f59d-7057-0f9f-bbe724df1cd8.png)

AWSにあるリソースを管理するためにAWS S3を使う釈然としない感じになってる

## Terraform Cloudでのstate管理
![terraform.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/5eef60d9-37c1-d722-9eca-8c2fd7addb3c.png)


S3で管理していたところがTerraform Cloudになるだけだが

メリットとしては
- Stateファイル管理用のリソースを用意する必要がない
- Stateファイルの変更履歴をGUIで簡単に確認できる
- Stateファイルの細かいアクセス制御をシンプルに実現できる
- plan や apply時に自動でstateロックしてくれる
- デフォルトでバージョン管理機能がついてる
- Freeプランで500 Resourcesまで無料

これだけメリットがあるから使わない手はない

## 実装手順

### Terraform Cloudの設定

#### Terraform Cloudにアクセスして Organization を作る

https://app.terraform.io/app/organizations



**Create organization** から作成
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/1051de53-5788-2a9a-f04a-0eded3fbdb62.png)


必要事項を入力して作成
![image-2.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/b7c19d40-6c12-cb39-9e82-8df827460b54.png)


#### organization 内に Workspace を作成

作成した organization にアクセスしてWorkspace を作成
![image-3.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/3646eb07-e131-7a34-610d-053deb9123a3.png)


**API-Driven Workflow**を選択し、
![image-4.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/82629334-dc0a-b2e6-26df-177e6f378b29.png)


必要事項を入力し作成
![image-5.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/f4265bb1-5482-1418-09c1-04d63c15cdeb.png)


settings → General にある Execution Mode を **Local** にして Save settings
![image-6.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/55174165-8f2b-25d0-80ed-c8cdd3b706e8.png)
![image-7.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/85fd083e-41c9-3c26-60d9-0a7a5e5473b7.png)


#### Terraform Cloud の認証TOKENを取得してgithubに登録

対象のOrganizationをクリック
![image-9.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/000fb521-1f77-931d-924b-3922a4d41478.png)


settings → teams の**Create team token**をクリック
![image-10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/294db693-a214-9325-8886-7c4e09e5da4c.png)
![image-12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/d0c0f5cb-1617-dfd2-0352-1a441acbf7ef.png)


作成したtokenをgithubに登録するのでgithubの対象リポジトリにアクセス
![image-13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/4d689750-52cb-86c3-2c90-0afa84e9937e.png)


settings → Secrets and variables → actions をクリック
![image-14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/97b850b4-03f3-7217-03b6-8e1cc87f08b4.png)


Environment Secretは本番環境や検証環境などで区別して利用できます。
Repository Secretはリポジトリ内で同一の値を利用できます。
お好みでsecretを作ってください。
今回は **TERRAFORM_CLOUD_TOKEN** というトークン名にしてます。

![image-15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/81503789-31e6-89dc-d792-b3a43a4d5803.png)


### AWS での設定

#### OIDCプロバイダを作成

AWS → IAM → ID プロバイダ → プロバイダを追加 の順にクリックし画像の通り

```
プロバイダ : token.actions.githubusercontent.com
OpenID Connect
```
のプロバイダを作成

![image-16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/f4233011-53d3-e7e3-b809-9fdb14e2c42a.png)


#### ロールの作成

AWS → IAM → ロール → ロールの作成をクリック

![image-17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/e38c9074-dbb2-2e29-ef91-e1a977e2cb65.png)


**カスタム信頼ポリシー**を選択し、ステートメントに以下を追加
![image-18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/268b5f97-4c56-f061-3434-4d9160979db8.png)

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::${AWSアカウントID}:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:${githubが所属する組織}/${githubリポジトリ}:*"
                }
            }
        }
    ]
}
```

必要な権限を追加
例では**AdministratorAccess**権限を選択
![image-19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/6c24aa15-a291-cd97-d698-08af06550430.png)


※作成したロール名はgithub actionsで使うので控えててください

#### AWSアカウントのIDをgithubのsecretに登録

AWSの12桁のIDをgithub のsecretに入れる
githubのリポジトリにアクセスしてsettings → Secrets and variables → actions をクリック
![image-14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/98b4df7c-9bb4-c9e2-d443-8c10d1c30ff1.png)


Environment Secretは本番環境や検証環境などで区別して利用できます。
Repository Secretはリポジトリ内で同一の値を利用できます。
お好みでsecretを作ってください。
今回は **AWS_ACCOUNT_ID** というトークン名にしてます。

![image-15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/ed856366-5d8a-3792-48ea-e71b6bc1de4f.png)


### github actions の設定

#### 構成

```
├─.github
│  └─workflows
│          all-dryrun.yml
│          dev-apply.yml
│          prd-apply.yml
│          stg-apply.yml
│
├─dev
│      backend.tf
│      sqs.tf
│
├─prd
│      backend.tf
│      sqs.tf
│
└─stg
        backend.tf
        sqs.tf
```

#### github
https://github.com/zukizukizuki/terraform_cloud_ci_cd_test

#### ファイル内容

```all-dryrun.yml
name: 'terraform-ci'
on:
  pull_request:
    paths:
      - 'dev/**'
      - 'stg/**'
      - 'prd/**'

env:
  AWS_REGION: "ap-northeast-1"
  AWS_ROLE_NAME: "github-actions-cicd-role"

  # Terraform
  TF_VERSION: "1.8.5"
  TF_VAR_aws_region: "ap-northeast-1"
  # 2024年6月現在、「TF_API_TOKENを利用できない」というバグが報告されているので以下の変数を指定。
  # https://zenn.dev/ficilcom/articles/cdktf-action
  TF_TOKEN_app_terraform_io: ${{ secrets.TERRAFORM_CLOUD_TOKEN }}

permissions:
  id-token: write   # This is required for requesting the JWT
  contents: read    # This is required for actions/checkout

jobs:
  terraform-ci:
    runs-on: ubuntu-22.04
    timeout-minutes: 100
    strategy:
      fail-fast: false
      matrix:
        environment: [dev, stg, prd]
    permissions:
      id-token: write
      contents: read
      pull-requests: write
      statuses: write
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/${{ env.AWS_ROLE_NAME }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        working-directory: ${{ matrix.environment }}
        run: terraform init -upgrade -no-color

      - name: Terraform Format Check
        working-directory: ${{ matrix.environment }}
        run: terraform fmt -check -recursive

      - name: Terraform Validate
        working-directory: ${{ matrix.environment }}
        run: terraform validate

      - name: Terraform Plan
        working-directory: ${{ matrix.environment }}
        run: terraform plan -no-color -input=false
```

```dev-apply.yml
name: 'dev-terraform-cd'
on:
  push:
    branches:
      - main
    paths:
      - 'dev/**'

env:
  AWS_REGION: "ap-northeast-1"
  AWS_ROLE_NAME: "github-actions-cicd-role"

  # Terraform
  TF_VERSION: "1.8.5"
  TF_VAR_aws_region: "ap-northeast-1"
  # 2024年6月現在、「TF_API_TOKENを利用できない」というバグが報告されているので以下の変数を指定。
  # https://zenn.dev/ficilcom/articles/cdktf-action
  TF_TOKEN_app_terraform_io: ${{ secrets.TERRAFORM_CLOUD_TOKEN }}

permissions:
  id-token: write   # This is required for requesting the JWT
  contents: read    # This is required for actions/checkout

jobs:
  dev-terraform-cd:
    runs-on: ubuntu-22.04
    timeout-minutes: 100
    permissions:
      id-token: write
      contents: read
      pull-requests: write
      statuses: write
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/${{ env.AWS_ROLE_NAME }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        working-directory: dev
        run: terraform init -upgrade -no-color

      - name: Terraform Apply
        working-directory: dev
        run: terraform apply -auto-approve -no-color
```

```stg-apply.yml
name: 'stg-terraform-cd'
on:
  push:
    branches:
      - main
    paths:
      - 'stg/**'

env:
  AWS_REGION: "ap-northeast-1"
  AWS_ROLE_NAME: "github-actions-cicd-role"

  # Terraform
  TF_VERSION: "1.8.5"
  TF_VAR_aws_region: "ap-northeast-1"
  # 2024年6月現在、「TF_API_TOKENを利用できない」というバグが報告されているので以下の変数を指定。
  # https://zenn.dev/ficilcom/articles/cdktf-action
  TF_TOKEN_app_terraform_io: ${{ secrets.TERRAFORM_CLOUD_TOKEN }}

permissions:
  id-token: write   # This is required for requesting the JWT
  contents: read    # This is required for actions/checkout

jobs:
  stg-terraform-cd:
    runs-on: ubuntu-22.04
    timeout-minutes: 100
    permissions:
      id-token: write
      contents: read
      pull-requests: write
      statuses: write
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/${{ env.AWS_ROLE_NAME }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        working-directory: stg
        run: terraform init -upgrade -no-color

      - name: Terraform Apply
        working-directory: stg
        run: terraform apply -auto-approve -no-color
```

```prd-apply.yml
name: 'prd-terraform-cd'
on:
  push:
    branches:
      - main
    paths:
      - 'prd/**'

env:
  AWS_REGION: "ap-northeast-1"
  AWS_ROLE_NAME: "github-actions-cicd-role"

  # Terraform
  TF_VERSION: "1.8.5"
  TF_VAR_aws_region: "ap-northeast-1"
  # 2024年6月現在、「TF_API_TOKENを利用できない」というバグが報告されているので以下の変数を指定。
  # https://zenn.dev/ficilcom/articles/cdktf-action
  TF_TOKEN_app_terraform_io: ${{ secrets.TERRAFORM_CLOUD_TOKEN }}

permissions:
  id-token: write   # This is required for requesting the JWT
  contents: read    # This is required for actions/checkout

jobs:
  prd-terraform-cd:
    runs-on: ubuntu-22.04
    timeout-minutes: 100
    permissions:
      id-token: write
      contents: read
      pull-requests: write
      statuses: write
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/${{ env.AWS_ROLE_NAME }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        working-directory: prd
        run: terraform init -upgrade -no-color

      - name: Terraform Apply
        working-directory: prd
        run: terraform apply -auto-approve -no-color
```

※devフォルダの中身
```backend.tf
terraform {
  required_version = "~> 1.8.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  cloud {
    organization = "zu"

    workspaces {
      name = "dev"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}
```

```sqs.tf
resource "aws_sqs_queue" "sqs-dev" {
  name = "sqs-dev"
}
```

### 自動テストの実施
dev , stg , prdフォルダ配下のファイルを編集してPRを作るとterraformの自動テストが行われます

### 自動デプロイの実施
PRをmainブランチにマージすると自動デプロイが行われます

### Terraform Cloudにstateが出来てる事の確認
リソースを作成すると以下の様にstateが出来ている
対象workspace移動してstateにあります

![image-20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/924512/d82196c8-36dc-b18b-dd89-8f815368a30d.png)

