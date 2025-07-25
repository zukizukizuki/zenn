---
title: IAMロールを除却したらgithub actionsが使えなくなった件
private: false
tags:
  - aws
  - github actions
  - oidc
  - terraform
  - CI/CD
updated_at: '2025-06-01T01:53:02.178Z'
id: null
organization_url_name: null
slide: false
---

# GitHub ActionsとAWS連携の設定手順（OIDC利用）

GitHub ActionsでAWSと連携する際に、OIDCを使用してIAMロールを引き受ける設定を行います。本記事では、Terraformで設定したIAMロールを削除してしまった場合に、AWSコンソールから再作成する手順を説明します。

## エラーの状況

GitHub Actionsで以下のエラーが発生しました：

```
Error: Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

このエラーは、GitHub ActionsがIAMロールを引き受けるための設定が正しく行われていない場合に発生します。具体的には、OIDCプロバイダーやIAMロールの設定に問題がある可能性があります。

## 解決手順

### 1. IAMロールをAWSコンソールから作成

#### **信頼関係の設定**

1. AWSマネジメントコンソールで **IAM** にアクセスします。
2. 左メニューから「ロール」を選択し、「ロールを作成」をクリックします。
3. **信頼されたエンティティの種類** として「Web ID プロバイダー」を選択します。
4. **OIDCプロバイダー** に `token.actions.githubusercontent.com` を選択。
   - **クライアントID（aud）** は `sts.amazonaws.com` を指定。
5. **条件** を設定：
   - 条件キー: `token.actions.githubusercontent.com:sub`
   - 演算子: `StringLike`
   - 値: `repo:cynaps-inc/ba-cloud-infrastructure:*`

#### **権限の設定**

1. 必要なポリシーをIAMロールにアタッチします。今回は管理者権限を付与する例を示します：
   - **AWS 管理ポリシー** から **AdministratorAccess** を選択。
2. 設定が完了したら「次へ」をクリック。

#### **ロールの詳細設定**

1. ロール名を入力します（例: `github-actions-cicd-role`）。
2. 必要に応じて説明を追加。
3. 「ロールを作成」をクリック。



### 2. 信頼関係ポリシーの確認

作成したIAMロールの「信頼関係」タブを開き、以下の内容が設定されていることを確認します。

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWSアカウントID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:cynaps-inc/ba-cloud-infrastructure:*"
        }
      }
    }
  ]
}
```

- `<AWSアカウントID>` を自分のAWSアカウントIDに置き換えてください。



### 3. GitHub Actionsの設定

`.github/workflows/<workflow>.yml` ファイルで、`aws-actions/configure-aws-credentials` の設定を以下のように変更します。

```
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::<AWSアカウントID>:role/github-actions-cicd-role
    aws-region: <AWSリージョン>
```

### 4. GitHubリポジトリの設定

1. リポジトリの「Settings」 → 「Actions」 → 「General」を開きます。
2. 「Workflow permissions」で「Read and write permissions」を有効にします。

### 5. ワークフローの確認

GitHub Actionsで再度ワークフローを実行し、正常に動作することを確認します。

## まとめ

IAMロールの設定を削除してしまっても、AWSコンソールから簡単に再作成できます。本手順を参考に、GitHub ActionsとAWSのOIDC連携を正しく構成してください。
