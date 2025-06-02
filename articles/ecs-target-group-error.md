# ECSサービスのターゲットグループ設定ミス調査・修正手順

## 概要

ECSサービスでRegisterTargetsイベントが発生しているにも関わらず、Application Load Balancerでターゲットが登録されない問題の調査・解決記録です。

**結論：ECSサービスが意図しないターゲットグループを参照していることが原因でした。**

## 問題の症状

- ECSサービスは正常に`RUNNING`状態
- RegisterTargetsイベントは発生している
- ALBのターゲットグループにターゲットが登録されない
- ヘルスチェックが`UNKNOWN`状態

## 調査手順

### 1. 基本的な状態確認

```bash
# ECSサービスの状態確認
aws ecs describe-services \
  --cluster ltd-cluster-dev \
  --services ltd-web-v2-dev-service ltd-front-employee-ecs-service-dev-App-fargate \
  --region ap-northeast-1 \
  --query 'services[*].[serviceName,status,desiredCount,runningCount]' \
  --output table

# 実行中のタスク確認
aws ecs list-tasks \
  --cluster ltd-cluster-dev \
  --service-name ltd-web-v2-dev-service \
  --region ap-northeast-1 \
  --query 'taskArns[0]' \
  --output text
```

### 2. ターゲットグループの状態確認

```bash
# ターゲットグループのヘルス状態確認
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN> \
  --region ap-northeast-1 \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
  --output table
```

### 3. ECSサービスのロードバランサー設定確認

**重要：ここで問題を発見**

```bash
# ECSサービスに設定されているロードバランサー情報を確認
aws ecs describe-services \
  --cluster ltd-cluster-dev \
  --service ltd-web-v2-dev-service \
  --region ap-northeast-1 \
  --query 'services[0].loadBalancers' \
  --output json
```

**発見した問題：**
- ECSサービスが意図しないターゲットグループを参照していた
- AWSコンソールのECS画面では、この設定ミスが視覚的にわかりやすく表示される

### 4. IAM実行ロールの権限確認

```bash
# タスク定義から実行ロールARNを取得
aws ecs describe-task-definition \
  --task-definition ltd-web-v2-dev:1496 \
  --region ap-northeast-1 \
  --query 'taskDefinition.executionRoleArn' \
  --output text

# 実行ロールにアタッチされたポリシー確認
aws iam list-attached-role-policies \
  --role-name <EXECUTION_ROLE_NAME> \
  --region ap-northeast-1
```

## 解決方法

### TerraformやGUIでは変更できない理由

ECSサービスのロードバランサー設定は、サービス作成後は以下の方法では変更できません：
- ❌ Terraform（force new deploymentでも変更不可）
- ❌ AWS Management Console（GUIには変更オプションなし）

### CLIによる修正手順

**唯一の解決方法：AWS CLI の `update-service` コマンド**

```bash
# 手順1: 現在の設定確認
aws ecs describe-services \
  --cluster ltd-cluster-dev \
  --service ltd-web-v2-dev-service \
  --region ap-northeast-1 \
  --query 'services[0].loadBalancers' \
  --output json

# 手順2: コンテナ名とポート確認
aws ecs describe-task-definition \
  --task-definition ltd-web-v2-dev:1496 \
  --region ap-northeast-1 \
  --query 'taskDefinition.containerDefinitions[*].[name,portMappings[0].containerPort]' \
  --output table

# 手順3: 正しいターゲットグループに修正
aws ecs update-service \
  --cluster ltd-cluster-dev \
  --service ltd-web-v2-dev-service \
  --load-balancers '[
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:ap-northeast-1:960293440626:targetgroup/ltd-dev-tg-backend/9c68336fe7c338fb",
      "containerName": "nginx",
      "containerPort": 80
    }
  ]' \
  --region ap-northeast-1

# 手順4: デプロイメント完了を待機
aws ecs wait services-stable \
  --cluster ltd-cluster-dev \
  --services ltd-web-v2-dev-service \
  --region ap-northeast-1

# 手順5: 修正結果確認
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:960293440626:targetgroup/ltd-dev-tg-backend/9c68336fe7c338fb \
  --region ap-northeast-1 \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
  --output table
```

## 調査で分かった重要なポイント

### 1. 問題特定のキーポイント

- **RegisterTargetsイベントの発生** ≠ **正しいターゲットグループへの登録**
- ECSコンソールの「ロードバランサーの状態」セクションで設定ミスが視覚的に確認可能
- CLIでの`describe-services`による詳細確認が必須

### 2. よくある落とし穴

- Terraformでサービスを再作成しても、間違った設定のまま再作成される可能性
- GUIでは修正不可能（update-serviceのオプションが存在しない）
- タスク定義の変更だけでは解決しない

### 3. 権限問題との複合

今回は以下の複数問題が同時発生：
- **設定ミス：** 間違ったターゲットグループの参照
- **権限不足：** 実行ロールに必要なポリシーが未アタッチ

権限問題の解決：
```bash
# 必要なポリシーをアタッチ
aws iam attach-role-policy \
  --role-name <EXECUTION_ROLE_NAME> \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy \
  --role-name <EXECUTION_ROLE_NAME> \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

## 予防策

### 1. 作成時の注意点

```bash
# サービス作成時にターゲットグループARNを正確に指定
aws ecs create-service \
  --cluster <CLUSTER_NAME> \
  --service-name <SERVICE_NAME> \
  --task-definition <TASK_DEFINITION> \
  --load-balancers targetGroupArn=<CORRECT_TARGET_GROUP_ARN>,containerName=<CONTAINER_NAME>,containerPort=<PORT> \
  --desired-count 2
```

### 2. 定期的な設定確認

```bash
# 定期的にECSサービスの設定を確認するスクリプト
#!/bin/bash
CLUSTER="ltd-cluster-dev"
SERVICES=("ltd-web-v2-dev-service" "ltd-front-employee-ecs-service-dev-App-fargate")

for service in "${SERVICES[@]}"; do
  echo "=== $service ==="
  aws ecs describe-services \
    --cluster $CLUSTER \
    --service $service \
    --query 'services[0].loadBalancers[0].targetGroupArn' \
    --output text
done
```

### 3. Terraformでの注意点

```hcl
# Terraformでの正確な設定例
resource "aws_ecs_service" "app" {
  name            = "my-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn  # 正確なARNを指定
    container_name   = "app"
    container_port   = 80
  }
}
```

## まとめ

**RegisterTargetsイベントが発生してもターゲットが登録されない場合：**

1. **ECSコンソールで視覚的に確認**（最も効率的）
2. **CLIで`describe-services`を実行してロードバランサー設定を確認**
3. **間違ったターゲットグループが設定されている場合は、CLIの`update-service`で修正**
4. **TerraformやGUIでは修正不可能なので注意**

この問題は設定ミスが原因でありがちですが、修正方法が限られているため、CLIでの対応方法を覚えておくことが重要です。