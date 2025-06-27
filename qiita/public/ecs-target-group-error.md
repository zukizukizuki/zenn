---
title: ECSサービスのターゲットグループ設定ミスでハマった話
private: false
tags:
  - ubuntu
  - linux
  - rc.local
  - bash
updated_at: '2025-06-02T12:52:37.284Z'
id: null
organization_url_name: null
slide: false
---

## 概要

ECSサービスでRegisterTargetsイベントが発生しているにも関わらず、Application Load Balancerでターゲットが登録されない問題の調査・解決記録です。

**結論：ECSサービスが意図しないターゲットグループを参照していることが原因でした。**

> **注意：** 本記事のコマンド例では、実際のリソース名やARNは仮名に置き換えています。実際の運用では、適切なリソース名に読み替えてください。

## 背景・経緯

この問題は、以下のTerraform運用過程で発生しました：

1. **STG環境で正常に動作していたリソース**をベースに**Terraformモジュール化**を実施
2. 作成したモジュールを**DEV環境に適用**
3. Terraform applyは成功したが、**ECSサービスがALBに正しく登録されない**問題が発生

**重要なポイント：**
- Terraformでは**ECSサービス作成後のロードバランサー設定変更ができない**
- この制限により、Terraformで管理しているつもりでも**実際は設定が反映されない**状況が発生
- モジュール化の過程で**ターゲットグループの参照が正しく設定されていなかった**

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
  --cluster my-cluster \
  --services my-web-service my-api-service \
  --region ap-northeast-1 \
  --query 'services[*].[serviceName,status,desiredCount,runningCount]' \
  --output table

# 実行中のタスク確認
aws ecs list-tasks \
  --cluster my-cluster \
  --service-name my-web-service \
  --region ap-northeast-1 \
  --query 'taskArns[0]' \
  --output text
```

### 2. ターゲットグループの状態確認

```bash
# ターゲットグループのヘルス状態確認
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:123456789012:targetgroup/my-target-group/1234567890abcdef \
  --region ap-northeast-1 \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
  --output table
```

### 3. ECSサービスのロードバランサー設定確認

**重要：ここで問題を発見**

```bash
# ECSサービスに設定されているロードバランサー情報を確認
aws ecs describe-services \
  --cluster my-cluster \
  --service my-web-service \
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
  --task-definition my-app:123 \
  --region ap-northeast-1 \
  --query 'taskDefinition.executionRoleArn' \
  --output text

# 実行ロールにアタッチされたポリシー確認
aws iam list-attached-role-policies \
  --role-name MyECSTaskExecutionRole \
  --region ap-northeast-1
```

## 解決方法

### TerraformやGUIでは変更できない理由

ECSサービスのロードバランサー設定は、**サービス作成後は以下の方法では変更できません：**
- ❌ **Terraform**（force new deploymentでも変更不可）
- ❌ **AWS Management Console**（GUIには変更オプションなし）

**この制限が今回の問題の根本原因：**
1. STG環境のリソースをモジュール化する際、ターゲットグループの参照が間違って設定された
2. Terraformでサービスを作成時に間違った設定が適用された
3. **作成後はTerraformでは修正できない**ため、設定ミスが残り続けた
4. Terraform state上は正常に見えるが、実際のAWSリソースは間違った設定のまま

**Terraformの落とし穴：**
```hcl
# このようにTerraformで定義しても...
resource "aws_ecs_service" "app" {
  name = "my-service"
  
  load_balancer {
    target_group_arn = aws_lb_target_group.correct.arn  # 正しい値に修正
    container_name   = "app"
    container_port   = 80
  }
}

# サービス作成後にこの設定を変更してapplyしても、
# 実際のECSサービスには反映されない！
```

### CLIによる修正手順

**唯一の解決方法：AWS CLI の `update-service` コマンド**

```bash
# 手順1: 現在の設定確認
aws ecs describe-services \
  --cluster my-cluster \
  --service my-web-service \
  --region ap-northeast-1 \
  --query 'services[0].loadBalancers' \
  --output json

# 手順2: コンテナ名とポート確認
aws ecs describe-task-definition \
  --task-definition my-app:123 \
  --region ap-northeast-1 \
  --query 'taskDefinition.containerDefinitions[*].[name,portMappings[0].containerPort]' \
  --output table

# 手順3: 正しいターゲットグループに修正
aws ecs update-service \
  --cluster my-cluster \
  --service my-web-service \
  --load-balancers '[
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:ap-northeast-1:123456789012:targetgroup/my-backend-tg/abcdef1234567890",
      "containerName": "nginx",
      "containerPort": 80
    }
  ]' \
  --region ap-northeast-1

# 手順4: デプロイメント完了を待機
aws ecs wait services-stable \
  --cluster my-cluster \
  --services my-web-service \
  --region ap-northeast-1

# 手順5: 修正結果確認
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:123456789012:targetgroup/my-backend-tg/abcdef1234567890 \
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
  --role-name MyECSTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy \
  --role-name MyECSTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

## 予防策

### 1. モジュール化時の注意点

**STG環境からのモジュール化で特に注意すべき点：**

```hcl
# モジュール側（modules/ecs-service/main.tf）
resource "aws_ecs_service" "main" {
  name            = var.service_name
  cluster         = var.cluster_id
  task_definition = var.task_definition_arn
  desired_count   = var.desired_count

  load_balancer {
    target_group_arn = var.target_group_arn  # ← この変数が正しく渡されているか要確認
    container_name   = var.container_name
    container_port   = var.container_port
  }
}

# 呼び出し側（environments/dev/main.tf）
module "ecs_service" {
  source = "../../modules/ecs-service"
  
  service_name        = "my-web-service"
  cluster_id          = aws_ecs_cluster.main.id
  task_definition_arn = aws_ecs_task_definition.app.arn
  target_group_arn    = aws_lb_target_group.backend.arn  # ← 正しいターゲットグループを指定
  container_name      = "nginx"
  container_port      = 80
}
```

**チェックポイント：**
- ✅ ターゲットグループのARNが環境ごとに正しく設定されているか
- ✅ コンテナ名とポート番号が正確か
- ✅ 依存関係（target_group → ecs_service）が正しく設定されているか

### 2. デプロイ前の検証手順

**Terraformモジュール適用前に必ず実行：**

```bash
# 1. Terraform planで作成されるリソースを確認
terraform plan

# 2. 特にECSサービスのload_balancer設定を詳しく確認
terraform show -json terraform.tfplan | jq '.planned_values.root_module.resources[] | select(.type == "aws_ecs_service") | .values.load_balancer'

# 3. 作成予定のターゲットグループARNを確認
terraform show -json terraform.tfplan | jq '.planned_values.root_module.resources[] | select(.type == "aws_lb_target_group") | {name: .values.name, arn: .values.arn}'
```

### 3. 定期的な設定確認

```bash
# 定期的にECSサービスの設定を確認するスクリプト
#!/bin/bash
CLUSTER="my-cluster"
SERVICES=("my-web-service" "my-api-service")

for service in "${SERVICES[@]}"; do
  echo "=== $service ==="
  aws ecs describe-services \
    --cluster $CLUSTER \
    --service $service \
    --query 'services[0].loadBalancers[0].targetGroupArn' \
    --output text
done
```

### 4. Terraformでの注意点（改訂版）

**モジュール化での失敗を防ぐ設定例：**

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
  
  # 依存関係を明示的に指定して、作成順序を制御
  depends_on = [
    aws_lb_target_group.app,
    aws_lb_listener.app
  ]
}

# 作成後の検証も含める
resource "null_resource" "ecs_service_validation" {
  depends_on = [aws_ecs_service.app]
  
  provisioner "local-exec" {
    command = <<EOF
      aws ecs describe-services \
        --cluster ${aws_ecs_cluster.main.name} \
        --service ${aws_ecs_service.app.name} \
        --query 'services[0].loadBalancers[0].targetGroupArn' \
        --output text
    EOF
  }
}
```

## まとめ

**RegisterTargetsイベントが発生してもターゲットが登録されない場合：**

1. **ECSコンソールで視覚的に確認**（最も効率的）
2. **CLIで`describe-services`を実行してロードバランサー設定を確認**
3. **間違ったターゲットグループが設定されている場合は、CLIの`update-service`で修正**
4. **TerraformやGUIでは修正不可能なので注意**

**Terraformモジュール化での教訓：**
- **ECSサービスのロードバランサー設定は作成後変更不可**という制限を理解する
- **モジュール化時はターゲットグループの参照を慎重に設定**する
- **デプロイ前にterraform planで設定値を必ず確認**する
- **作成後はCLIでの設定確認を習慣化**する

この問題は設定ミスが原因でありがちですが、Terraformの制限により修正方法が限られているため、**事前の慎重な設計と検証**、および**CLIでの対応方法**を覚えておくことが重要です。

特に**STG環境からのモジュール化**では、環境固有の設定が混入しやすいため、より一層の注意が必要です。
