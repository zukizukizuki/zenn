---
title: "TerraformとCDKのリソース削除動作の違い"
emoji: "🔷"
type: "tech"
topics: ["cloud", "terraform","terraform cdk" , "IaC" , "SRE"]
published: true
---

## はじめに

普段Terraformを愛用している筆者が、AWS CDKプロジェクトでリソース削除を行った際に遭遇した「予想外の動作」について記録する。

**Terraformの経験から期待していたこと:**
- 設定ファイルからリソース定義を削除
- `terraform apply`を実行
- 実際のAWSリソースが削除される

しかし、CDKでは全く異なる動作をすることを学んだ。Infrastructure as Code (IaC) ツールといっても、ツールによってリソース管理の思想が大きく異なることを痛感した体験を共有したい。

## 問題の発生

STG環境の不要なALB（Application Load Balancer）を削除するため、CDKコードで以下の修正を行った：

```typescript
// 修正前：すべての環境でALBを作成
const albStack = new AlbStack(app, `${stackPrefix}AlbV2`, {
  version: 2,
  internetFacing: true,
  env,
  // その他のプロパティ...
})

// 修正後：STG環境のみALB作成を無効化
let albStack: AlbStack | undefined

if (envName !== "stg") {  // STG環境では作成しない
  albStack = new AlbStack(app, `${stackPrefix}AlbV2`, {
    version: 2,
    internetFacing: true,
    env,
    // その他のプロパティ...
  })
}
```

**Terraformユーザーとして期待した動作**: `cdk deploy`で既存の`{envName}{AppName}AlbV2` CloudFormationスタックが削除される

**実際の動作**: 既存スタックは残存したまま、参照のみが削除された

**筆者の心境**: 「あれ？なんでスタックが残ってるの？コードから削除したのに...」

Terraformであれば確実に削除されるはずの操作が、CDKでは全く異なる結果となり、最初は「バグなのでは？」と疑ってしまった。

## Terraform vs CDK の削除動作の違い

### 🟢 Terraform の場合

```hcl
# リソース定義を削除またはコメントアウト
# resource "aws_lb" "example" {
#   name               = "test-lb"
#   load_balancer_type = "application"
#   subnets           = [aws_subnet.public1.id, aws_subnet.public2.id]
# }
```

```bash
terraform plan   # 削除予定として表示される
terraform apply  # 実際にリソースが削除される
```

**結果**: 設定ファイルから削除 → `terraform apply` → 実際のAWSリソースも削除

### 🔴 CDK の場合

```typescript
// スタック作成コードを削除または条件分岐で無効化
// if (envName !== "stg") {
//   new AlbStack(...)
// }
```

```bash
cdk diff    # 既存スタックの削除は表示されない
cdk deploy  # 既存CloudFormationスタックは残存
```

**結果**: コードから削除しても既存CloudFormationスタックは残存

## なぜこの違いが生まれるのか

### Terraform の仕組み

1. **State File による状態管理**
   - `terraform.tfstate`でリソース状態を追跡
   - 設定ファイルとState Fileを比較して差分を検出
   - 設定削除 = State File削除 = 実リソース削除

2. **宣言的な状態管理**
   ```
   設定ファイルの状態 = 実環境の状態
   ```

### CDK の仕組み

1. **CloudFormation ベースの動作**
   - CDKはCloudFormationテンプレートを生成するツール
   - CDK App ≠ CloudFormationスタック
   - スタックのライフサイクルは独立管理

2. **安全性重視の設計**
   ```
   CDKコード = テンプレート生成器
   CloudFormationスタック = 実際のリソース管理
   ```

## AWS公式ドキュメントの記載

### CDK公式ドキュメント
> **CDK does not delete stacks that are no longer defined in your CDK app.** You must delete them manually using the AWS CLI or AWS Management Console.

[AWS CDK Developer Guide - Working with stacks](https://docs.aws.amazon.com/cdk/v2/guide/stacks.html)

### 設計思想
- **安全性**: 意図しないデータ消失を防ぐ
- **明示的操作**: 削除は開発者が明示的に指示する必要がある
- **責任の分離**: コード管理とインフラ管理を分離

## CDKでのリソース削除方法

### 1. 手動でCloudFormationスタックを削除
```bash
# AWS CLI
aws cloudformation delete-stack --stack-name {StackName}

# CDK CLI
cdk destroy {StackName}
```

### 2. コードで削除ポリシーを指定
```typescript
const albStack = new AlbStack(app, `${stackPrefix}AlbV2`, {
  // ...
})

// 削除ポリシーを追加
albStack.node.addMetadata('aws:cdk:deletion-policy', 'delete')
```

### 3. 条件付きスタック作成 + 手動削除の組み合わせ
```typescript
// 新規作成は無効化（今回の対応）
if (envName !== "stg") {
  albStack = new AlbStack(...)
}

// 既存スタックは別途手動削除
```

## 他のIaCツールとの比較

| ツール             | 削除動作                           | 特徴                         |
| ------------------ | ---------------------------------- | ---------------------------- |
| **Terraform**      | 設定削除 → apply で削除            | State File による直接管理    |
| **CDK**            | 手動削除が必要                     | CloudFormation経由の間接管理 |
| **CloudFormation** | テンプレート削除してもスタック残存 | CDKと同じ動作                |
| **Pulumi**         | 設定削除 → up で削除               | Terraformに近い動作          |

## 実際のプロジェクトでの対応

今回のALB削除では以下の手順で対応：

1. **CDKコード修正**: STG環境でのスタック作成を無効化
2. **cdk diff確認**: 参照削除のみ表示されることを確認
3. **手動スタック削除**: AWS ConsoleまたはCLIで該当スタックを削除

## Terraformユーザーが感じる戸惑い

### 最初の印象
「CDKって使いにくいな...」「Terraformの方が直感的じゃん」

これは筆者が最初に感じた率直な感想だった。しかし、調べてみるとこれは**CDKの仕様であり、設計思想の違い**であることがわかった。

### Terraformに慣れ親しんだ脳内での期待値

```bash
# いつものTerraform作業フロー
1. .tfファイルからリソース定義を削除
2. terraform plan で削除予定を確認  ← 「- aws_lb.example will be destroyed」
3. terraform apply で実行
4. ✅ リソース削除完了

# CDKでも同じだと思い込んでいた
1. CDKコードからスタック定義を削除  ← ここまで同じ
2. cdk diff で差分確認           ← あれ？スタック削除が表示されない...？
3. cdk deploy で実行            ← 参照だけ削除される
4. ❌ スタックが残ってる...やっぱりバグ？ ← さらに混乱
```

### `cdk diff`の結果に困惑

Terraformであれば`terraform plan`で以下のような削除予定が表示される：

```bash
# Terraform plan の出力例
- # aws_lb.example will be destroyed
  - resource "aws_lb" "example" {
      - name               = "test-lb"
      - load_balancer_type = "application"
      # 削除されるリソースが明確に表示
    }
```

しかし、CDKで`cdk diff`を実行すると：

```bash
# CDK diff の実際の出力
Stack stgLtdWebEcsStackV2
[-] AWS::EC2::SecurityGroupIngress FargateSecurityGroupfromALB...
[-] AWS::EC2::SecurityGroupEgress FargateSecurityGrouptoALB...
[~] AWS::ECS::Service Fargate/Service FargateService (requires replacement)

# ALBスタック自体の削除は表示されない！
```

### 「なぜTerraformではできるのに...」という疑問

Terraformユーザーにとって、設定ファイルから削除→plan/diffで削除予定確認→apply での自動削除は**当たり前の動作**。だからこそCDKで同じ操作をしても削除が表示されず、実際にも削除されないことに強い違和感を覚えた。

## まとめ

### Terraform ユーザーが CDK で注意すべき点

- **リソース削除は自動で行われない**（これが一番の衝撃）
- **既存スタックの削除は別途手動操作が必要**
- **cdk diffで削除が表示されなくても正常**
- **「バグかも？」と思ったら、まず公式ドキュメントを確認**

### 慣れてしまえば、それぞれに利点がある

**Terraform**
- 直感的な削除動作
- 設定ファイル = 実環境の状態
- Terraformユーザーには「期待通り」の動作

**CDK**
- 意図しない削除事故を防げる（安全性重視）
- プログラミング言語の表現力を活用可能
- CloudFormationベースの堅牢なリソース管理

### 筆者の正直な感想

**個人的にはTerraformの設計思想の方がやりやすい**と感じている。

**理由：**
- 設定ファイル = 実環境の状態という分かりやすさ
- `plan`で削除予定が明確に見える安心感
- 設定削除→apply での直感的な削除フロー
- State Fileによる一元的なリソース管理の明確性
- 削除し忘れなどが未然に防げる

CDKの安全性重視の設計も理解できるが、日常的な運用では「やりたいことをストレートに実現できる」Terraformの方が開発効率が良いと感じる。

## 参考資料

- [AWS CDK Developer Guide - Working with stacks](https://docs.aws.amazon.com/cdk/v2/guide/stacks.html)
- [AWS CDK Best Practices](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)
- [AWS CDK Workshop](https://cdkworkshop.com/)
- [Terraform vs CDK Comparison](https://aws.amazon.com/compare/the-difference-between-terraform-and-cdk/)
