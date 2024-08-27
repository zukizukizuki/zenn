---
title: "【AWS】TerraformでSubnetをモジュール化する"
emoji: "🍰"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , VPC, ネットワーク , サブネット , subnet]
published: true
---

Terraformでは、コードの再利用性を高めるために、モジュールを活用することが推奨されています。
ここでは、Subnetをモジュール化する方法について説明します。

## モジュールの作成

まず、```00_modules/subnets```ディレクトリを作成し、その中に以下のファイルを作成します。

- ```main.tf```
- ```variables.tf```
- ```outputs.tf```

### main.tf

```main.tf```では、Subnetのリソースを定義します。

```hcl
resource "aws_subnet" "rds_private_subnet_1" {
 count             = var.create_rds_private_subnets ? 1 : 0
 availability_zone = "${var.region}a"
 cidr_block        = cidrsubnet(var.vpc_cidr, 8, 0)
 vpc_id            = var.vpc_id
 tags = {
   Name = "${var.environment}-rds-private-subnet-1"
 }
}

resource "aws_subnet" "rds_private_subnet_2" {
 count             = var.create_rds_private_subnets ? 1 : 0
 availability_zone = "${var.region}c"
 cidr_block        = cidrsubnet(var.vpc_cidr, 8, 1)
 vpc_id            = var.vpc_id
 tags = {
   Name = "${var.environment}-rds-private-subnet-2"
 }
}

resource "aws_subnet" "rds_private_subnet_3" {
 count             = var.create_rds_private_subnets ? 1 : 0
 availability_zone = "${var.region}d"
 cidr_block        = cidrsubnet(var.vpc_cidr, 8, 2)
 vpc_id            = var.vpc_id
 tags = {
   Name = "${var.environment}-rds-private-subnet-3"
 }
}

resource "aws_subnet" "public_subnet_1" {
 availability_zone       = "${var.region}a"
 cidr_block              = cidrsubnet(var.vpc_cidr, 8, 3)
 vpc_id                  = var.vpc_id
 map_public_ip_on_launch = true
 tags = {
   Name = "${var.environment}-public-subnet-1"
 }
}
```

ここで注目すべきは、以下の2点です。

1. ```count```を使用した条件分岐
2. ```cidrsubnet```関数の使用

#### countを使用した条件分岐

```count```は、リソースを複数作成する際に使用します。ここでは、```var.create_rds_private_subnets```の値によって、RDS用のプライベートサブネットを作成するかどうかを制御しています。

```hcl
count = var.create_rds_private_subnets ? 1 : 0
```

```var.create_rds_private_subnets```がtrueの場合、```count```は1となり、サブネットが1つ作成されます。falseの場合、```count```は0となり、サブネットは作成されません。

#### cidrsubnet関数の使用

```cidrsubnet```関数は、VPCのCIDRブロックを分割して、サブネットのCIDRブロックを計算するために使用します。

```hcl
cidr_block = cidrsubnet(var.vpc_cidr, 8, 1)
```

この例では、```var.vpc_cidr```で指定されたVPCのCIDRブロックを、8ビットのサブネットマスクで分割し、1番目のサブネットのCIDRブロックを計算しています。

例えば、```var.vpc_cidr```が"10.0.0.0/16"の場合、以下のようなサブネットのCIDRブロックが計算されます。

- rds_private_subnet_1: "10.0.0.0/24" (8ビット分割, 0番目)
- rds_private_subnet_2: "10.0.1.0/24" (8ビット分割, 1番目)
- rds_private_subnet_3: "10.0.2.0/24" (8ビット分割, 2番目)
- public_subnet_1: "10.0.3.0/24" (8ビット分割, 3番目)

このように、```cidrsubnet```関数を使用することで、VPCのCIDRブロックを柔軟に分割し、サブネットのCIDRブロックを自動的に計算することができます。

### variables.tf

```variables.tf```では、モジュールで使用する変数を定義します。

```hcl
variable "environment" {
 description = "環境名 (dev, stg, prd)"
 type        = string
}

variable "vpc_id" {
 description = "VPC ID"
 type        = string
}

variable "region" {
 description = "AWSリージョン"
 type        = string
 default     = "ap-northeast-1"
}

variable "vpc_cidr" {
 description = "VPCのCIDRブロック"
 type        = string
 default     = "172.31.0.0/16"
}

variable "create_rds_private_subnets" {
 description = "RDS用のプライベートサブネットを作成するかどうか"
 type        = bool
 default     = true
}
```

### outputs.tf

```outputs.tf```では、モジュールの出力値を定義します。

```hcl
output "rds_subnet_ids" {
 value = [
   aws_subnet.rds_private_subnet_1[0].id,
   aws_subnet.rds_private_subnet_2[0].id,
   aws_subnet.rds_private_subnet_3[0].id
 ]
}

output "public_subnet_1_id" {
 value = aws_subnet.public_subnet_1.id
}
```

## モジュールの使用

作成したSubnetモジュールを使用するには、```main.tf```で以下のように記述します。

```hcl
module "subnets" {
 source      = "./00_modules/subnets"
 environment = var.environment
 vpc_id      = module.vpc.vpc_id
}
```

これにより、各環境に応じたSubnetを柔軟に作成することができます。

## まとめ

Subnetをモジュール化することで、コードの再利用性が高まり、管理がしやすくなります。
環境ごとに異なる設定を適用する場合でも、モジュールを活用することで、コードの重複を避けることができます。

また、```count```を使用した条件分岐や```cidrsubnet```関数の使用により、より柔軟かつ自動化されたサブネットの作成が可能になります。

ぜひ、Terraformでインフラを管理する際には、モジュールを活用してみてください。