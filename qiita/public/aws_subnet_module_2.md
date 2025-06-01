---
title: 【AWS】Terraformの公式AWS VPCモジュールを使用してサブネットを管理
private: false
tags:
  - AWS
  - EC2
  - terraform
  - Cloud
updated_at: '2025-06-01T01:52:49.030Z'
id: null
organization_url_name: null
slide: false
---

## はじめに

[この記事](https://zukkie.link/%e3%80%90aws%e3%80%91terraform%e3%81%a7subnet%e3%82%92%e3%83%a2%e3%82%b8%e3%83%a5%e3%83%bc%e3%83%ab%e5%8c%96%e3%81%99%e3%82%8b/#google_vignette)でsubnetをモジュール化していたが公式のモジュールがあるのでそれを使ってみる


## 手順

1. モジュールの宣言:
  main.tfファイルに以下のコードを追加します。

```
module "vpc" {
 source  = "terraform-aws-modules/vpc/aws"
 version = "~> 5.0"

 name = "${var.environment}-vpc"
 cidr = var.vpc_cidr

 azs             = var.availability_zones
 private_subnets = [for i in range(3) : cidrsubnet(var.vpc_cidr, 8, i)]
 public_subnets  = [cidrsubnet(var.vpc_cidr, 8, 3)]

 enable_nat_gateway = true
 single_nat_gateway = true

 enable_dns_hostnames = true
 enable_dns_support   = true

 tags = {
   Environment = var.environment
 }
}
```

このコードでは以下の設定を行っています：

- `source`: Terraform Registryから公式VPCモジュールを参照します。
- `version`: モジュールのバージョンを指定します（ここでは5.x系の最新版）。
- `name`: VPCの名前を環境変数を用いて動的に設定します。
- `cidr`: VPCのCIDRブロックを指定します。
- `azs`: 使用するアベイラビリティーゾーンのリストを指定します。
- `private_subnets`: プライベートサブネットのCIDRブロックを動的に生成します。`cidrsubnet`関数を使用して、VPCのCIDRブロックから自動的にサブネットを作成します。
- `public_subnets`: パブリックサブネットのCIDRブロックを同様に生成します。
- `enable_nat_gateway`: NATゲートウェイを有効にします。
- `single_nat_gateway`: コスト最適化のため、単一のNATゲートウェイを使用します。
- `enable_dns_hostnames`と`enable_dns_support`: VPC内のDNS設定を有効にします。
- `tags`: リソースにタグを付与します。

2. 変数の定義:
  variables.tfファイルに必要な変数を定義します。

```
variable "environment" {
 description = "The environment (e.g., dev, staging, prod)"
 type        = string
}

variable "vpc_cidr" {
 description = "The CIDR block for the VPC"
 type        = string
}

variable "availability_zones" {
 description = "List of availability zones"
 type        = list(string)
}
```

これらの変数定義により：

- `environment`: デプロイ環境を指定できます（例：dev, staging, prod）。
- `vpc_cidr`: VPCのCIDRブロックを柔軟に設定できます。
- `availability_zones`: 使用するアベイラビリティーゾーンをリストで指定できます。

3. サブネットの参照:
  他のリソースからサブネットを参照する際は、以下のように記述します。

```
resource "aws_instance" "example" {
 subnet_id = module.vpc.public_subnets[0]
 # その他の設定...
}
```

このコードでは：

- `module.vpc.public_subnets[0]`: VPCモジュールが作成したパブリックサブネットの最初の要素（インデックス0）を参照しています。これにより、EC2インスタンスを特定のサブネットにデプロイできます。

## 公式モジュールを使用する場合のメリット

1. **簡潔性**: 複雑なVPCとサブネット構成を数行のコードで実現できます。
2. **ベストプラクティス**: AWSのベストプラクティスに基づいた設定が自動的に適用されます。
3. **保守性**: モジュールのバージョンアップにより、最新の機能や修正を容易に取り入れられます。
4. **一貫性**: 異なる環境間で一貫したネットワーク構成を維持しやすくなります。
5. **柔軟性**: モジュールのパラメータを調整することで、様々な要件に対応できます。

## 公式モジュールを使用する場合のデメリット

1. **カスタマイズの制限**: 非常に特殊な要件がある場合、モジュールでは対応できないことがあります。
2. **ブラックボックス化**: 内部の動作が見えにくくなり、トラブルシューティングが難しくなる可能性があります。
3. **バージョン管理**: モジュールのバージョン更新に伴う互換性の問題に注意が必要です。

## 結論

Terraformの公式AWS VPCモジュールは、多くの場合において、VPCとサブネットの管理を大幅に簡素化し、開発効率を向上させます。自動的なサブネット計算やベストプラクティスの適用により、安全で効率的なネットワーク設計が可能になります。