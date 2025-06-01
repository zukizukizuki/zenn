---
title: Terraform Cloudでstateを管理してgithub actionsでAWSを管理するCI/CDを組む
private: false
tags:
  - AWS
  - GitHub Actions
  - Github
  - OIDC
updated_at: '2025-06-01T01:53:14.980Z'
id: null
organization_url_name: null
slide: false
---

## 概要
従来はstateファイルをAWS S3 やGCP GCSで管理していたがTerraform Cloudで管理するメリットが大きい

## 従来のバケットでのstate管理
![alt text](/images/terraformS3.drawio.png)

AWSにあるリソースを管理するためにAWS S3を使う釈然としない感じになってる

## Terraform Cloudでのstate管理
![alt text](/images/terraform.png)

S3で管理していたところがTerraform Cloudになるだけだが

メリットとしては
- Stateファイル管理用のリソースを用意する必要がない
- Stateファイルの変更履歴をGUIで簡単に確認できる
- Stateファイルの細かいアクセス制御をシンプルに実現できる
- plan や apply時に自動でstateロックしてくれる
- デフォルトでバージョン管理機能がついてる
- Freeプランで500 Resourcesまで無料

これだけメリットがあるから使わない手はない

## 今回やる事

- CI は dev , stg , prd配下を編集してPRを作るとterraform planをする
- CD は dev , stg , prd配下を編集したPRがマージされるとterraform applyする
- あくまでCI/CDがメインなのでリソースはテキトーなsqsを作ってCI/CDが動くか確認

## 実装手順

### Terraform Cloudの設定

#### Terraform Cloudにアクセスして Organization を作る

https://app.terraform.io/app/organizations



**Create organization** から作成
![alt text](/images/image.png)

必要事項を入力して作成
![alt text](/images/image-2.png)


#### organization 内に Workspace を作成

作成した organization にアクセスしてWorkspace を作成
![alt text](/images/image-3.png)

**API-Driven Workflow**を選択し、
![alt text](/images/image-4.png)

必要事項を入力し作成
![alt text](/images/image-5.png)

settings → General にある Execution Mode を **Local** にして Save settings
![alt text](/images/image-6.png)
![alt text](/images/image-7.png)

#### Terraform Cloud の認証TOKENを取得してgithubに登録

対象のOrganizationをクリック
![alt text](/images/image-9.png)

settings → teams の**Create team token**をクリック
![alt text](/images/image-10.png)
![alt text](/images/image-12.png)

作成したtokenをgithubに登録するのでgithubの対象リポジトリにアクセス
![alt text](/images/image-13.png)

settings → Secrets and variables → actions をクリック
![alt text](/images/image-14.png)

Environment Secretは本番環境や検証環境などで区別して利用できます。
Repository Secretはリポジトリ内で同一の値を利用できます。
お好みでsecretを作ってください。
今回は **TERRAFORM_CLOUD_TOKEN** というトークン名にしてます。

![alt text](/images/image-15.png)

### AWS での設定

#### OIDCプロバイダを作成

AWS → IAM → ID プロバイダ → プロバイダを追加 の順にクリックし画像の通り

```
プロバイダ : token.actions.githubusercontent.com
OpenID Connect
```
のプロバイダを作成

![alt text](/images/image-16.png)

#### ロールの作成

AWS → IAM → ロール → ロールの作成をクリック

![alt text](/images/image-17.png)

**カスタム信頼ポリシー**を選択し、ステートメントに以下を追加
![alt text](/images/image-18.png)
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
![alt text](/images/image-19.png)

※作成したロール名はgithub actionsで使うので控えててください

#### AWSアカウントのIDをgithubのsecretに登録

AWSの12桁のIDをgithub のsecretに入れる
githubのリポジトリにアクセスしてsettings → Secrets and variables → actions をクリック
![alt text](/images/image-14.png)

Environment Secretは本番環境や検証環境などで区別して利用できます。
Repository Secretはリポジトリ内で同一の値を利用できます。
お好みでsecretを作ってください。
今回は **AWS_ACCOUNT_ID** というトークン名にしてます。

![alt text](/images/image-15.png)

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

![alt text](/images/image-20.png)
