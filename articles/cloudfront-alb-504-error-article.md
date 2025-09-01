---
title: "【AWS】CloudFront→ALBで504エラー！原因はまさかの〇〇だった件"
emoji: "💐"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["terraform" , "aws" , "cloudfront" , "elb" , "ecs"]
published: true
---

## 発生した問題

### 初期状況
ALBには2つのセキュリティグループがアタッチされていました：

```
Before: 
  ALB → SG1: 0.0.0.0/0からの80/443を許可
     → SG2: CloudFrontプレフィックスからの443を許可
  結果: ✅正常動作

After:
  ALB → SG1: 削除（セキュリティ強化のため）
     → SG2: CloudFrontプレフィックスからの443を許可（これのみ残す）
  結果: ❌504エラー大量発生
```

セキュリティを強化するため、`0.0.0.0/0`を許可していたSGを削除し、CloudFrontからのアクセスのみを許可するSGだけを残したところ、504 Gateway Timeoutが発生。

## Terraformでの管理における落とし穴

### 構成管理の状況
```hcl
# 削除対象のSG1（dataブロックで管理）
data "aws_security_group" "alb_allow_all" {
  id = "sg-old-allow-all"  # 0.0.0.0/0を許可していたSG
}

# 残すSG2（resourceブロックで管理）
resource "aws_security_group" "alb_cloudfront_only" {
  name = "alb-cloudfront-only"
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    prefix_list_ids = ["pl-58a04531"] # CloudFront
  }
}

# ALBの設定
resource "aws_lb" "main" {
  security_groups = [
    data.aws_security_group.alb_allow_all.id,        # SG1: 削除予定
    aws_security_group.alb_cloudfront_only.id        # SG2: 残す
  ]
}
```

**反省点：dataブロックで管理していたSG1を削除する際、インバウンドルールの変更に気を取られ、このSGがECSのインバウンドルールで参照されていることの確認が疎かになった**

## トラブルシューティングの迷走記

### 第1の仮説：CloudFrontのIPを個別に許可すればいい？

CloudFrontのアクセスログを確認：
```
2025-08-28 5:49:25 NRT20-P2 54.249.34.116 GET /company/30 504 OriginError
2025-08-28 5:49:34 SEA19-C2 157.55.39.7 GET /job/557 504 OriginError
```

「これらのIPをセキュリティグループに追加すれば...」

**→ 大きな勘違い！これらはエンドユーザーのIPで、CloudFrontのエッジサーバーのIPではない**

### 第2の仮説：ALBのインバウンドルールに80ポートが必要？

ターゲットグループのヘルスチェックを確認：
```yaml
ヘルスチェック:
  プロトコル: HTTP
  ポート: 80
```

「CloudFrontは443で通信、でもヘルスチェックは80...だからALBの80ポートを開ける必要がある！」

**→ これも違った！ヘルスチェックはALB→ECS間の通信で、ALBのインバウンドは無関係**

### 第3の仮説：ヘルスチェックをHTTPSに変更？

「じゃあヘルスチェックもHTTPS:443にすれば統一できて...」

**→ でも検証環境では80のままで動いているぞ？**

## 衝撃の展開：検証環境での再現

同じ構成を検証環境で再現：
- ALBのSG：CloudFrontから443のみ許可
- ヘルスチェック：HTTP:80
- 結果：**正常に動作している！**

「なぜ検証環境では動くのに、問題の環境では504エラー？」

## 根本原因の特定

### Terraformで見落としていた依存関係

```hcl
# ALBのセキュリティグループ（削除したSG1）
data "aws_security_group" "alb_allow_all" {
  id = "sg-old-allow-all"  # 0.0.0.0/0を許可
}

# ECSのセキュリティグループ（dataブロックで管理）
data "aws_security_group" "ecs" {
  id = "sg-ecs-existing"
}

# ECSのセキュリティグループルール（別のtfファイルで管理）
resource "aws_security_group_rule" "ecs_from_alb" {
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = data.aws_security_group.alb_allow_all.id  # 削除したSG1を参照！
  security_group_id        = data.aws_security_group.ecs.id
}
```

**dataブロックの落とし穴：**
- ALBのSG1もECSのSGもdataブロックで管理
- 既存リソースへの参照のため、依存関係が見えにくい
- `terraform plan`では「SGを削除すると、ECSのインバウンドルールが無効になる」という警告が出ない

### 削除したセキュリティグループの呪い

```yaml
削除したSG1 (sg-old-allow-all):
  用途: 0.0.0.0/0からの80/443を許可
  状態: 削除済み
  
残したSG2 (sg-cloudfront-only):
  用途: CloudFrontプレフィックスからの443のみ許可
  状態: 運用中
  
でも実は...
  
ECSのセキュリティグループ:
  インバウンドルール:
    - ソース: sg-old-allow-all（削除済み！） ← 幽霊参照
    - ポート: 80
    
  本来必要だったのは:
    - ソース: sg-cloudfront-only（残したSG）
    - ポート: 80
```

## 真の原因と解決方法

### 根本原因：ALBとECSのセキュリティグループの紐付けが切れた

#### 通信経路とSGの関係
```
正常時の通信フロー:
CloudFront → ALB (SG1 + SG2) → ECS
              ↓                  ↑
         アウトバウンド      インバウンド
         (デフォルト全許可)   (SG1からの80を許可)

SG1削除後:
CloudFront → ALB (SG2のみ) → × → ECS
              ↓                    ↑
         アウトバウンド        インバウンド
         (デフォルト全許可)     (存在しないSG1を待機)
```

#### 具体的な問題
1. **ALBのアウトバウンド**: デフォルトで全許可なので問題なし
2. **ECSのインバウンド**: 削除したSG1からの通信のみ許可 → **ここが問題！**
3. ALB（SG2）からのトラフィックがECSに到達できない

### 解決策
```hcl
# ECSのSGルールを修正
resource "aws_security_group_rule" "ecs_from_alb" {
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb_cloudfront_only.id  # 残したSG2に更新！
  security_group_id        = data.aws_security_group.ecs.id
}
```

つまり、**ECSのインバウンドルールが、削除したSG1からの通信を待っていたが、実際にはSG2から通信が来ていた**ため、通信がブロックされていました。

## 学んだ教訓

### 1. Terraformでdataブロックを使う際の注意点
```bash
# SGを削除する前に必ず実行
# dataブロックで管理しているSGの参照先を確認
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.group-id,Values=[削除予定のSG-ID]" \
  --query 'SecurityGroups[*].[GroupId,GroupName]'
```

### 2. インバウンドだけでなくアウトバウンドの影響も確認
実際には、今回の問題は「ALBのアウトバウンド」ではなく「ECSのインバウンドで参照しているSG」の問題でした：

```bash
# SGを削除する前に、そのSGがどこで参照されているか確認
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.group-id,Values=[削除予定のSG-ID]" \
  --query 'SecurityGroups[*].[GroupId,GroupName,IpPermissions[?UserIdGroupPairs[?GroupId==`削除予定のSG-ID`]]]'
```

### 3. 504エラーの切り分け方
- CloudFrontログで`OriginError`＋10秒タイムアウト = ALB→ターゲット間の問題
- まずターゲットヘルスを確認
- 次にターゲット側のSG設定を確認

### 4. 正しいSG設計パターン
```yaml
ALB-SG:
  インバウンド: CloudFrontプレフィックスリストから443
  
ECS-SG:
  インバウンド: ALB-SGのIDを指定して80を許可（IPではなくSG-IDで）
```

## まとめ

トラブルシューティングで遠回りしましたが、その過程で以下を学んだ：

1. **ALBのインバウンド80は不要**（ヘルスチェックとは無関係）
2. **SGの参照は削除後も残る**（幽霊参照に注意）
3. **Terraformのdataブロックは依存関係が見えにくい**

最終的な原因は「削除したSGの幽霊参照」という落とし穴でした。特にTerraformでdataブロックを使っている場合、インバウンドルールだけでなく、そのSGがどこで参照されているかも必ず確認しましょう！

## 参考リンク
- [AWS セキュリティグループのルール](https://docs.aws.amazon.com/ja_jp/vpc/latest/userguide/VPC_SecurityGroups.html)
- [ELB のトラブルシューティング](https://docs.aws.amazon.com/ja_jp/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html)
- [Terraform AWS Provider - Security Group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group)