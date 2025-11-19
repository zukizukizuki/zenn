---
title: "【爆速】ECS Fargateタスクを踏み台にしてRDSへ安全に接続"
emoji: "🐚"
type: "tech"
topics: [aws, ecs, rds, fargate, ssm]
published: true
---

## 概要
ECS Exec機能とAWS Systems Manager (SSM) Session Managerを組み合わせることで、ECS Fargateタスクを踏み台としてRDSにポートフォワーディングし、ローカルのDBクライアントから安全に接続できます。この記事では必要な準備から接続手順をまとめます。

## 前提条件

### 必要な権限
- `ecs:DescribeTasks`
- `ecs:ListTasks`
- `ssm:StartSession`
- `ssm:TerminateSession`

### 必要なツール
- AWS CLI v2
- Session Manager plugin
- jq (JSON整形)

```bash
# Session Manager plugin (macOS)
brew install --cask session-manager-plugin

# jq
brew install jq
```

### ECS側の設定
- ECS Execが有効化されたFargateタスクが稼働していること
- タスクロールに `AmazonSSMManagedInstanceCore` がアタッチ済みであること
- SSMエージェントのバージョンが 3.1.1374.0 以上
- 対象コンテナに `DB_HOST` などRDSエンドポイントを保持する環境変数が存在すること
  - RDSエンドポイントが分かれば直接指定してもOK

### ネットワーク設定
- RDSのセキュリティグループで、ECSタスクのセキュリティグループからのアクセス (例: MySQLなら3306/TCP) を許可する

## 手順

### 1. 必要な情報を環境変数に設定
```bash
export CLUSTER_NAME="your-cluster-name"
export SERVICE_NAME="your-service-name"
export CONTAINER_NAME="your-container-name"
export DB_HOST_ENV_NAME="DB_HOST"
export LOCAL_PORT="13306"
export AWS_REGION="ap-northeast-1"

# 実行中タスクのARN
export TASK_ARN=$(aws ecs list-tasks \
  --cluster ${CLUSTER_NAME} \
  --service-name ${SERVICE_NAME} \
  --query "taskArns[0]" \
  --output text)

# 環境変数からRDSエンドポイントを抽出
export RDS_ENDPOINT=$(aws ecs describe-tasks \
  --cluster ${CLUSTER_NAME} \
  --tasks ${TASK_ARN} \
  --query "tasks[0].overrides.containerOverrides[?name=='${CONTAINER_NAME}'].environment[?name=='${DB_HOST_ENV_NAME}'].value | [0]" \
  --output text)

# タスクIDとruntimeId
export TASK_ID=$(echo ${TASK_ARN} | awk -F/ '{print $NF}')
export RUNTIME_ID=$(aws ecs describe-tasks \
  --cluster ${CLUSTER_NAME} \
  --region ${AWS_REGION} \
  --tasks ${TASK_ARN} \
  | jq -r ".tasks[0].containers[] | select(.name==\"${CONTAINER_NAME}\") | .runtimeId")
```

### 2. SSM Session Managerでポートフォワーディング
```bash
aws ssm start-session \
  --region ${AWS_REGION} \
  --target "ecs:${CLUSTER_NAME}_${TASK_ID}_${RUNTIME_ID}" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "host=${RDS_ENDPOINT},portNumber=3306,localPortNumber=${LOCAL_PORT}"
```

成功すると次のように表示されます。
```
Starting session with SessionId: xxx
Port 13306 opened for sessionId: xxx
Waiting for connections...
```

### 3. DBクライアントから接続
- Host: `127.0.0.1` または `localhost`
- Port: `13306`（LOCAL_PORTで指定した値）
- Username: RDSで設定した認証情報
- Password: RDSで設定した認証情報
- Database: 接続したいデータベース名（任意）

Sequel Ace、TablePlus、DBeaverなど任意のクライアントから通常通り接続すればOKです。

### 4. 接続終了
作業が完了したら、ポートフォワーディングを行っているターミナルで `Ctrl+C` を押し、SSMセッションを終了します。

## 参考リンク
- [ECS FargateタスクのSSMリモートポートフォワード対応](https://zenn.dev/quiver/articles/1458e453118254)
- [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [ECS Exec の使用](https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/ecs-exec.html)
