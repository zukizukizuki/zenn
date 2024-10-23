---
title: "PrivateサブネットにあるECSからVPCエンドポイントを利用してECRイメージをプルする方法"
emoji: "📎"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [terraform , aws , ECS , ECR , セキュリティグループ ]
published: true
---

プライベートサブネット内でECSタスクがAmazon ECRからイメージをプルするには、VPCエンドポイントを使用する必要があります。以下の手順では、ECSタスクがNAT Gatewayを使わずにVPCエンドポイントを介してECRにアクセスし、イメージをプルする方法を説明します。

## VPCエンドポイントの作成

ECSタスクがプライベートサブネット内からECRにアクセスするためには、以下の3つのVPCエンドポイントを作成する必要があります。

### **ECR APIエンドポイント**
- Amazon ECRのAPIにアクセスするために必要です。

$$$
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type = "Interface"
  subnet_ids        = var.private_subnet_ids
  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.environment}-ecr-api-endpoint"
  }
}
$$$

### **ECR Dockerエンドポイント**
- ECRからDockerイメージをプルするために必要です。

$$$
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type = "Interface"
  subnet_ids        = var.private_subnet_ids
  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.environment}-ecr-dkr-endpoint"
  }
}
$$$

### **S3エンドポイント**
- Amazon ECRがS3をバックエンドとして使用するため、S3エンドポイントが必要です。

$$$
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.private_route_table_ids

  tags = {
    Name = "${var.environment}-s3-endpoint"
  }
}
$$$

## セキュリティグループの設定

VPCエンドポイントに関連付けるセキュリティグループで、ECSタスクからのHTTPS通信（ポート443）が許可されている必要があります。

### **VPCエンドポイント用セキュリティグループ**

$$$
resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "${var.environment}-vpc-endpoint-sg"
  description = "Security group for VPC Endpoints"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # VPCのCIDR範囲
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]  # 必要なアウトバウンド通信を許可
  }

  tags = {
    Name = "${var.environment}-vpc-endpoint-sg"
  }
}
$$$

## ECSタスクのセキュリティグループ設定

ECSタスクに関連付けるセキュリティグループでも、HTTPS通信（ポート443）を許可する必要があります。

### **ECSタスク用セキュリティグループ**

$$$
resource "aws_security_group" "ecs_task_sg" {
  name        = "${var.environment}-ecs-task-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # 全ての宛先に対するHTTPS通信を許可
  }

  tags = {
    Name = "${var.environment}-ecs-task-sg"
  }
}
$$$

## 4. IAMロールの設定

ECSタスクがECRからイメージをプルするためには、**タスク実行ロール**に適切なIAMポリシーがアタッチされている必要があります。

### **タスク実行ロールにアタッチするポリシー**

1. `AmazonECSTaskExecutionRolePolicy`
2. `AmazonEC2ContainerRegistryReadOnly`

$$$
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecs_ecr_readonly_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}
$$$

## 5. ECSタスク定義の作成

ECSタスク定義で、適切なロールとセキュリティグループを設定します。

$$$
resource "aws_ecs_task_definition" "ecs_task" {
  family                   = "my-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  container_definitions    = file("${path.module}/container_definitions.json")
  cpu                      = "256"
  memory                   = "512"
}
$$$

## 6. ECSサービスの設定

最後に、ECSサービスでFargateタスクを起動します。ここでプライベートサブネットとセキュリティグループを設定します。

$$$
resource "aws_ecs_service" "ecs_service" {
  name            = "${var.environment}-ecs-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.ecs_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_task_sg.id]
    assign_public_ip = false
  }
}
$$$

## 7. タスク実行の確認

ECSサービスを起動した後、タスクがプライベートサブネット内で正しくECRからイメージをプルできているかを確認します。タスクの実行状況やログを確認し、問題がないかチェックしてください。
