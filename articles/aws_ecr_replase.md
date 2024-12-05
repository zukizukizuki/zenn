

title: "【AWS】ECRにimageを異なるアカウントにあるECRにpushする"
emoji: "🐛"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws, ECR, docker, image]
published: true


## 目的
この手順の目的は、あるAWSアカウントのECR（Elastic Container Registry）に格納されているDockerイメージを、別のAWSアカウントのECRに移動することです。これにより、異なるアカウント間でイメージの共有やデプロイが可能になります。

## 手順

### 1. AWS CLIプロファイルの設定
別アカウント用のプロファイルをAWS CLIに設定します。このプロファイルを使用してターゲットアカウントにログインします。

```
aws configure --profile <プロファイル名>
```

入力例:
- **AWS Access Key ID**: `<IAMユーザーのアクセスキー>`
- **AWS Secret Access Key**: `<IAMユーザーのシークレットキー>`
- **Default region name**: `ap-northeast-1`
- **Default output format**: `json`

### 2. ECRにログイン
ターゲットアカウントのECRにログインします。プロファイル名を指定して認証を行います。

```
aws ecr get-login-password --region <リージョン> --profile <プロファイル名> | docker login --username AWS --password-stdin <ターゲットECRアカウント>.dkr.ecr.<リージョン>.amazonaws.com
```



### 3. Dockerイメージをタグ付け
Push先のECRリポジトリに合わせて、既存のDockerイメージをタグ付けします。

```
docker tag <元ECRアカウント>.dkr.ecr.<リージョン>.amazonaws.com/<リポジトリ名>:<タグ> <ターゲットECRアカウント>.dkr.ecr.<リージョン>.amazonaws.com/<リポジトリ名>:<タグ>
```

例:
```
docker tag <元ECRアカウント>.dkr.ecr.ap-northeast-1.amazonaws.com/my-repo:latest <ターゲットECRアカウント>.dkr.ecr.ap-northeast-1.amazonaws.com/my-repo:latest
```



### 4. DockerイメージをPush
タグ付けしたイメージをターゲットアカウントのECRにPushします。

```
docker push <ターゲットECRアカウント>.dkr.ecr.<リージョン>.amazonaws.com/<リポジトリ名>:<タグ>
```

例:
```
docker push <ターゲットECRアカウント>.dkr.ecr.ap-northeast-1.amazonaws.com/my-repo:latest
```



## 注意点
1. **IAMポリシー**:
   - ターゲットアカウントのIAMユーザーにECRへのアクセス権限を付与する必要があります。
   - 最低限必要なアクション:
     - `ecr:GetAuthorizationToken`
     - `ecr:BatchCheckLayerAvailability`
     - `ecr:InitiateLayerUpload`
     - `ecr:UploadLayerPart`
     - `ecr:CompleteLayerUpload`
     - `ecr:PutImage`

2. **ECRリポジトリの存在確認**:
   - ターゲットアカウントでプッシュ先のリポジトリが事前に作成されていることを確認してください。

3. **プロファイル名とリージョン**:
   - 適切なプロファイル名とリージョンを指定してください。



これで、別のアカウントのECRにDockerイメージをプッシュできます！
