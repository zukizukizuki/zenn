---
title: "【AWS】terraform で EC2を作成しようとしたところ InvalidGroup.NotFound が出る"
emoji: "☘️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws, error, ec2, cloud]
published: true
---

## 概要

以下のterraformでEC2を作ろうとしたところSGグループが見つからない旨のエラーが出現

## tfファイル
```
resource "aws_instance" "dev_test_01" {
  ami                  = "ami-"
  availability_zone    = "ap-northeast-1a"
  iam_instance_profile = "SSM_access_for_EC2"
  instance_type        = "t2.micro"
  key_name             = "dev-test-01"
  private_ip           = "192.168.10.1"
  subnet_id            = "subnet-"
  security_groups = ["ec2-1", "ec2-2"]
  tags = {
    Name = "dev-test-01"
  }
  vpc_security_group_ids = ["sg-1", "sg-2", "sg-3"]

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
  }
}
```

## エラーメッセージ
```
Error: creating EC2 Instance: operation error EC2: RunInstances, https response error StatusCode: 400, RequestID: , api error InvalidGroup.NotFound: The security group 'ec2-1' does not exist in VPC 'vpc-'
```

### 解決方法

`security_groups`を削除する

### 解決方法の理由

`security_groups`属性はEC2-Classicネットワークで使用されるもので、VPC内のインスタンスには適していません。一方、`vpc_security_group_ids`はVPC内のセキュリティグループを直接指定するために使用されます。VPC環境では、セキュリティグループはVPCに紐づいているため、`vpc_security_group_ids`を使用することで、正しいVPC内のセキュリティグループを確実に指定できます。
