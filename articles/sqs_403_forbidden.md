---
title: "【AWS】SQS 403 Forbiddenエラーの解決方法"
emoji: "🦝"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , sqs, error]
published: true
---


## 問題の概要
ECSタスクからSQSキューへのアクセス時に403 Forbiddenエラーが発生しました。

### エラーログ
```
LogGroup: scout-admin-dev
LogStream: laravel-server
LogMessage: [2025-06-12 18:01:41] develop.ERROR: Error executing "SendMessage" on "https://sqs.ap-northeast-1.amazonaws.com"; AWS HTTP error: Client error: `POST https://sqs.ap-northeast-1.amazonaws.com` resulted in a `403 Forbidden` response
```
## 原因分析
SQSアクセスには**双方向の権限設定**が必要ですが、IAMロール側の権限が不足していました：
1. ✅ **SQSリソースポリシー**: 設定済み（特定のIAMロールからのアクセスを許可）
2. ❌ **IAMロール権限**: 未設定（ECSタスクロールにSQSアクセス権限なし）

## 解決手順

### 1. 現状確認

ECSタスクロールの既存ポリシーを確認：

```bash
aws iam list-role-policies --role-name <ECS_TASK_ROLE_NAME> --region <REGION>
```

**結果：** SQSアクセス権限なし
- CloudWatch Logs権限のみ
- S3バケットアクセス権限のみ

### 2. SQSアクセス権限の追加
ECSタスクロールにSQSアクセス権限を追加：

```bash
aws iam put-role-policy \
  --role-name <ECS_TASK_ROLE_NAME> \
  --policy-name SQSAccessPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ],
        "Resource": "arn:aws:sqs:<REGION>:<ACCOUNT_ID>:<QUEUE_NAME>"
      }
    ]
  }' \
  --region <REGION>
```

### 3. 権限追加の確認

```bash
aws iam list-role-policies --role-name <ECS_TASK_ROLE_NAME> --region <REGION>
```

**期待結果：**

```json
{
    "PolicyNames": [
        "DefaultPolicy",
        "s3",
        "SQSAccessPolicy"
    ]
}
```

### 4. ECSサービスの再起動

新しい権限を適用するためECSサービスを再起動：

```bash
aws ecs update-service \
  --cluster <ECS_CLUSTER_NAME> \
  --service <ECS_SERVICE_NAME> \
  --force-new-deployment \
  --region <REGION>
```

### 5. 動作確認

ログを確認してエラーが解消されたことを確認：

```bash
aws logs filter-log-events \
  --log-group-name <LOG_GROUP_NAME> \
  --log-stream-names <LOG_STREAM_NAME> \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --region <REGION> \
  --query 'events[].message'
```

## 設定済み権限の詳細

### SQSリソースポリシー（既に設定済み）

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowECSTaskAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<ACCOUNT_ID>:role/<ECS_TASK_ROLE_NAME>"
      },
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl"
      ],
      "Resource": "arn:aws:sqs:<REGION>:<ACCOUNT_ID>:<QUEUE_NAME>",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "<ACCOUNT_ID>"
        }
      }
    }
  ]
}
```

### IAMロールポリシー（今回追加）

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl"
      ],
      "Resource": "arn:aws:sqs:<REGION>:<ACCOUNT_ID>:<QUEUE_NAME>"
    }
  ]
}
```

## 重要なポイント

### 双方向権限の必要性

SQSアクセスには以下の**両方**が必要：
1. **SQS側（リソースポリシー）**: 「誰がアクセスできるか」を定義
2. **IAM側（ロールポリシー）**: 「何にアクセスできるか」を定義

### セキュリティ考慮事項

- **最小権限の原則**: 必要最小限のアクションのみ許可
- **リソース制限**: 特定のSQSキューのみ対象
- **アカウント制限**: 同一AWSアカウント内のみアクセス許可
## 結果

✅ 403 Forbiddenエラーが解消され、ECSタスクからSQSへの正常なアクセスが可能になりました。

## トラブルシューティングのポイント

### よくある間違い

1. **SQSポリシーのみ設定**: IAMロール権限も必要
2. **IAMロール権限のみ設定**: SQSリソースポリシーも必要
3. **権限適用の遅延**: ECSサービス再起動が必要

### 確認方法

1. **IAMロール権限**: `aws iam list-role-policies`
2. **SQSリソースポリシー**: `aws sqs get-queue-attributes --attribute-names Policy`
3. **ECSタスクステータス**: `aws ecs describe-services`
4. **ログ確認**: CloudWatch Logsでエラーメッセージを確認
