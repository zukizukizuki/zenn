---
title: "GCPとGitHub ActionsでOIDC認証しgithub actionsでterraform planを実施する"
emoji: "🫏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [gcp , github actions , oidc , terraform , CI/CD]
published: true
---

## はじめに

Google Cloud Platform (GCP) とGitHub Actionsを連携させる際、OIDCを使用することで、より安全で効率的な認証が可能になります。この記事では、GCPでWorkload Identity Federationを設定し、GitHub Actionsと連携させる手順を解説します。

## 前提条件

- GCPのプロジェクトが作成済みであること
- gcloudコマンドラインツールがインストールされていること
- 必要な権限を持つGCPアカウントでログインしていること

## 手順

### Workload Identity Poolの作成

まず、Workload Identity Poolを作成します。

```bash
gcloud iam workload-identity-pools create "github-pool" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

※コンソールでやる場合、以下の部分
![](https://storage.googleapis.com/zenn-user-upload/cb62d81ceed2-20240813.png)

### Workload Identity Providerの作成

次に、Workload Identity Providerを作成します。
```
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

※コンソールでやる場合、以下の部分
![](https://storage.googleapis.com/zenn-user-upload/8c57bdc833df-20240813.png)
![](https://storage.googleapis.com/zenn-user-upload/fb19a23b1ebc-20240813.png)

### サービスアカウントの作成

GitHubから利用するためのサービスアカウントを作成します。
```bash
gcloud iam service-accounts create "terraform" \
  --project="YOUR_PROJECT_ID" \
  --display-name="Terraform Service Account"
```

※コンソールでやる場合、以下の部分
![](https://storage.googleapis.com/zenn-user-upload/2636b7773657-20240813.png)

### サービスアカウントに権限を付与
作成したサービスアカウントに必要な権限を付与します。
```bash
gcloud projects add-iam-policy-binding "YOUR_PROJECT_ID" \
  --member="serviceAccount:terraform@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/editor"
```

※コンソールでやる場合、以下の部分
![](https://storage.googleapis.com/zenn-user-upload/0d0757646ea4-20240813.png)

注意：セキュリティのベストプラクティスとして、roles/editorの代わりに必要最小限の権限を持つカスタムロールを使用することをお勧めします。

### Workload Identity Poolの完全な名前（フルパス）を取得
以下のコマンドで取得

```bash
gcloud iam workload-identity-pools describe "github-pool" --project="YOUR_PROJECT_ID" --location="global" --format="value(name)"
```

### Workload Identity Poolとサービスアカウントの関連付け
最後に、Workload Identity Poolとサービスアカウントを関連付けます。
```
gcloud iam service-accounts add-iam-policy-binding "terraform@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --project="YOUR_PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${Workload Identity Poolの完全な名前}/attribute.repository/${YOUR_GITHUB_ORG}/${YOUR_GITHUB_REPO}"
```

### GitHub Actionsの設定
GCP側の設定が完了したら、GitHub Actionsのワークフローファイルに以下のような設定を追加します。
```yaml
jobs:
  deploy:
    permissions:
      contents: 'read'
      id-token: 'write'

    steps:
    - id: 'auth'
      name: 'Authenticate to GCP'
      uses: 'google-github-actions/auth@v1'
      with:
        workload_identity_provider: 'projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
        service_account: 'terraform@YOUR_PROJECT_ID.iam.gserviceaccount.com'

    - name: 'Set up Terraform'
      uses: 'hashicorp/setup-terraform@v2'
      with:
        terraform_version: 1.5.2  # Terraformのバージョンを指定

    - name: 'Checkout repository'
      uses: 'actions/checkout@v3'

    - name: 'Terraform Init'
      run: terraform init

    - name: 'Terraform Plan'
      run: terraform plan
```

## まとめ
以上の手順で、GCPとGitHub ActionsをOIDC認証で連携させることができます。この方法を使用することで、長期的な認証情報を保存する必要がなくなり、よりセキュアな運用が可能になります。