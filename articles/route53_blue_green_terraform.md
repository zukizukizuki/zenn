---
title: "TerraformでRoute 53の加重ルーティングをシンプルに変更しようとしたら`InvalidChangeBatch`エラーが出た話"
emoji: "🦓"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [terraform , Route53, aws, 加重ルーティング, エラー]
published: true
---

## はじめに
先日、Terraformで管理しているRoute 53の構成を見直す機会がありました。具体的には、Blue/Greenデプロイメントが無事完了したため、トラフィックを100%新環境に向け、加重ルーティング（Weighted Routing）から通常のシンプルルーティングへ切り戻す、という作業です。
コード上は`weighted_routing_policy`ブロックを削除するだけの単純な変更に見えたのですが、いざCI/CDで`terraform apply`を実行するとエラーが...。

```
Error: updating Route 53 resource record sets: InvalidChangeBatch: [RRSet with DNS name your-domain.com., type A cannot be created as other RRSets exist with the same name and type.]
```

「既に同じレコードが存在する」...？ 単純な更新のはずがなぜ？

今回は、この`InvalidChangeBatch`エラーに直面した私が、原因を調査し、実際に解決に至った手順を記録として残します。同じ問題に遭遇した方の助けになれば幸いです。


## エラーが発生した状況

### 変更前のTerraformコード

当初、Blue/Green構成のために、CloudFront（Green）とALB（Blue）を向く2つの加重レコードを定義していました。
**Green: CloudFront (Weight: 100)**

```terraform
# route53.tf
resource "aws_route53_record" "main_cf_record" {
  # ... (詳細は省略) ...
  set_identifier = "green"
  weighted_routing_policy {
    weight = 100
  }
}
```

**Blue: ALB (Weight: 0)**
```terraform
# route53.tf
resource "aws_route53_record" "fallback_alb_record" {
  # ... (詳細は省略) ...
  set_identifier = "blue"
  weighted_routing_policy {
    weight = 0
  }
}
```

### 変更後のTerraformコード
トラフィックを完全にCloudFrontへ移行し、ALB（Blue）のレコードを削除、CloudFront（Green）のレコードをシンプルルーティングに変更しようとしました。

-   `fallback_alb_record`リソースをコードから削除。
-   `main_cf_record`リソースから`set_identifier`と`weighted_routing_policy`を削除。

```terraform
# route53.tf
resource "aws_route53_record" "main_cf_record" {
  zone_id = data.aws_route53_zone.primary.id
  name    = "your-domain.com"
  type    = "A"
  
  alias {
    name                   = module.app_cloudfront_waf.cloudfront_domain_name
    zone_id                = module.app_cloudfront_waf.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}
```

### CIで確認したTerraform Plan

CI/CD上で実行された`terraform plan`の結果は以下の通りでした。Weight 0の`fallback_alb_record`が`destroy`され、Weight 100の`main_cf_record`が`update in-place`（インプレース更新）になると表示されています。

```
Terraform will perform the following actions:
  # aws_route53_record.fallback_alb_record will be destroyed
  - resource "aws_route53_record" "fallback_alb_record" { ... }
  # aws_route53_record.main_cf_record will be updated in-place
  ~ resource "aws_route53_record" "main_cf_record" {
        id             = "Z0123456789ABCDEFGHIJ_your-domain.com_A_green"
        name           = "your-domain.com"
      - set_identifier = "green" -> null
      - weighted_routing_policy {
          - weight = 100 -> null
        }
      ...
    }
Plan: 0 to add, 1 to change, 1 to destroy.
```

この`plan`結果を見て、「問題なく更新されるだろう」と判断し、`apply`を進めた結果、前述のエラーに遭遇しました。

## エラーの原因分析

エラーの根本原因は、**Terraform（およびAWS API）が「加重レコード」から「シンプルレコード」への変更をアトミックな「更新(Update)」として扱えない**点にあります。

-   **Terraform Planの表示**: `plan`では`update in-place`と表示されるため、単純な属性変更のように見えます。
-   **実際のAPI動作**: しかし、内部的にはRoute 53のAPIに対して「既存の加重レコードセットを削除し、新しいシンプルレコードセットを作成する」という操作（Change Batch）を発行しようとします。
-   **Route 53の制約**: Route 53では、同じ名前とタイプのレコードセットが（たとえトランザクション内であっても）同時に存在することを許可しません。加重レコードセットがまだ存在する状態でシンプルレコードセットを作成しようとするため、「既に同じレコードが存在する」というエラーが返されます。

## 感想：Terraform Planの表示と実際の挙動のギャップ

ここで感じたのは、**Terraformの`plan`が示す内容と、実際の`apply`の挙動にギャップがある**という点です。
`plan`の出力では、明確に`updated in-place`と表示されていました。この表示は通常、リソースの再作成（destroy & create）を伴わない安全な変更を示唆します。しかし、今回のケースでは、この表示とは裏腹に、内部的にはリソースの種別自体を変更する破壊的な操作が行われようとしており、結果としてAWS APIの制約に引っかかりました。

これは正直、Terraformの少しイケてない部分だと感じました。`plan`の段階で、この変更が単純な更新ではなく、再作成に近い操作、あるいは失敗する可能性のある操作であることを警告してくれれば、もっと早く問題に気づけたはずです。

今回の件で、`terraform plan`の結果を100%信頼するのではなく、**変更対象リソースの特性（今回はRoute 53のルーティングポリシー）を理解した上で、`plan`の結果を解釈する必要がある**という教訓を得ました。

## 解決策

### 方法1: `terraform state`コマンドと手動操作によるリカバリー（今回採用した方法）

CI/CDが失敗し、Stateと実環境が不整合に陥ってしまった状況で、かつ**サービスへの影響（ダウンタイム）を最小限に抑える必要があった**ため、今回はこの方法でリカバリーを行いました。

1.  **Terraform管理下からレコードを外す**

    ローカル環境で`terraform state rm`コマンドを実行し、Terraform Stateファイルから対象レコードの情報を削除します。

    ```bash
    terraform state rm 'aws_route53_record.main_cf_record'
    ```

2.  **AWSコンソールで手動修正**

    AWSマネジメントコンソールにログインし、Route 53のホストゾーンから対象のレコードを手動でシンプルルーティングに変更します。この手動操作の間もレコードは存在し続けるため、ダウンタイムは発生しません。

3.  **再びTerraform管理下に置く**

    手動で修正したリソースを、`terraform import`コマンドで再びTerraformの管理下に置きます。

    ```bash
    terraform import 'aws_route53_record.main_cf_record' Z0123456789ABCDEFGHIJ_your-domain.com_A
    ```

4.  **差分がないことを確認**

    最後に`terraform plan`を実行し、差分がないことを確認して完了です。

### 方法2: Terraformのみで完結させる計画的な変更（ダウンタイムが許容できる場合）

エラー発生前の計画的な変更であれば、IaCの原則に沿った以下の方法もあります。

1.  **ステップ1: レコードの削除**

    Terraformコード内の`aws_route53_record.main_cf_record`リソースブロック全体をコメントアウトし、`terraform apply`を実行してリソースを削除します。

2.  **ステップ2: レコードの再作成**

    次に、コメントアウトを解除し、シンプルルーティングの定義に戻して再度`terraform apply`を実行します。これにより、新しいシンプルレコードがクリーンな状態で作成されます。

この方法は、Terraformのコードだけで完結するため非常にクリーンで再現性が高いです。しかし、レコードを一度削除してから再作成するため、**DNSレコードが存在しないごくわずかなダウンタイムが発生する可能性**があります。本番環境の重要なエンドポイントでダウンタイムが許容できない場合、この方法は選択しにくいでしょう。**実際、今回私がこのアプローチを取らなかったのは、このダウンタイムのリスクを避けたかったためです。**

## まとめ

TerraformでRoute 53の加重ルーティングをシンプルルーティングに変更する際の`InvalidChangeBatch`エラーは、`plan`の表示とは裏腹に、内部的な操作がAWS APIの制約に抵触することが原因でした。

-   **エラーの原因**: `update in-place`と表示されても、実際は「削除＋作成」に近い操作が行われ、同じ名前・タイプのレコードが共存できないRoute 53の仕様に引っかかる。
-   **教訓**: `plan`の結果はあくまでTerraformの意図を示すものであり、最終的な挙動はクラウドプロバイダのAPI仕様に依存する。リソースの特性を理解することが重要。
-   **解決策**: ダウンタイムを避けたい場合は`state`操作と手動でのリカバリーを、ダウンタイムが許容できるなら「削除してから作成する」という2段階の`apply`を行う。