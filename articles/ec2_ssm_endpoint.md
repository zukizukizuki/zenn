---
title: " 【AWS】Systems Manager (SSM) 接続エラーの対処方法"
emoji: "🎸"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [terraform , aws , ec2 , ssm ]
published: true
---

## エラー内容

1. SSMエージェントがAWSのSSMサービスに接続できない
2. EC2インスタンスがSSMに登録できない
3. SSMセッションマネージャーでインスタンスに接続できない

エラーログの例：
```
ERROR [Registrar] failed to register identity: error calling RegisterManagedInstance API: RequestError: send request failed
ERROR [CredentialRefresher] Retrieve credentials produced error: unexpected error getting instance profile role credentials or calling UpdateInstanceInformation. Skipping default host management fallback: retrieved credentials failed to report to ssm.
```

## 確認項目

1. VPCエンドポイントの設定
   - SSM、EC2Messages、SSMMessagesのエンドポイントが存在するか
   - エンドポイントの状態が「available」になっているか

2. セキュリティグループの設定
   - HTTPS（443ポート）のアウトバウンドトラフィックが許可されているか
   - VPCエンドポイントに関連付けられたセキュリティグループが適切に設定されているか

3. IAMロールの権限
   - EC2インスタンスに関連付けられたIAMロールが適切な権限（AmazonSSMManagedInstanceCore）を持っているか

4. SSMエージェントのインストールと設定
   - SSMエージェントが正しくインストールされ、実行されているか

5. DNS設定
   - VPC内でDNS解決が有効になっているか
   - プライベートDNSが有効になっているか

## 解決策

本事例では、VPCエンドポイントの追加が直接的な解決策となりました。以下に、元々追加されていたEC2リソースと、問題を解決したVPCエンドポイントの設定をTerraformコードで示します：

1. EC2リソース（既存）

```
data "aws_iam_instance_profile" "SSM_access_for_EC2" {
  name = "SSM_access_for_EC2"
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "db_jump" {
  availability_zone    = "ap-northeast-1a"
  ami                  = data.aws_ami.amazon_linux_2.id
  iam_instance_profile = data.aws_iam_instance_profile.SSM_access_for_EC2.name
  instance_type        = "t2.micro"
  key_name             = "db-jump-01"
  subnet_id            = var.ec2_subnet_id
  tags = {
    Name = "${var.environment}-db-jump-01"
  }
  vpc_security_group_ids = var.ec2_security_group_ids

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
  }
  user_data = <<-EOF
              #!/bin/bash
              sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
              systemctl enable amazon-ssm-agent
              systemctl start amazon-ssm-agent
              EOF

  user_data_replace_on_change = true
}
```

2. 追加したVPCエンドポイント（解決策）

```
resource "aws_vpc_endpoint" "ssm" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ssm"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = [var.ec2_subnet_id]
  security_group_ids = var.ec2_security_group_ids

  tags = {
    Name = "${var.environment}-ssm-endpoint"
  }
}

resource "aws_vpc_endpoint" "ec2messages" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ec2messages"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = [var.ec2_subnet_id]
  security_group_ids = var.ec2_security_group_ids

  tags = {
    Name = "${var.environment}-ec2messages-endpoint"
  }
}

resource "aws_vpc_endpoint" "ssmmessages" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ssmmessages"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = [var.ec2_subnet_id]
  security_group_ids = var.ec2_security_group_ids

  tags = {
    Name = "${var.environment}-ssmmessages-endpoint"
  }
}
```

これらのVPCエンドポイントを追加することで、EC2インスタンスがSSMサービスと通信できるようになり、問題が解決しました。

注意点：
- 各エンドポイントで `private_dns_enabled = true` を設定していることを確認してください。
- 適切なサブネットとセキュリティグループを指定していることを確認してください。
- エンドポイントの追加後、数分待ってからSSM接続を再試行してください。
