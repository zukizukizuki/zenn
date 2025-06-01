---
title: "【AWS】CloudFront作成時に `CNAMEAlreadyExists` エラーが発生した場合の対応手順"
emoji: "🍅"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , CloudFront, terraform , ACM]
published: true
---

CloudFrontの `CNAMEAlreadyExists` エラーは、 **DNSのCNAMEレコードが既に別のCloudFrontディストリビューションを指している場合** に発生します。

## **エラー内容**

```
Error: creating CloudFront Distribution: operation error CloudFront: CreateDistributionWithTags,
https response error StatusCode: 409, RequestID: ..., CNAMEAlreadyExists:
One or more aliases specified for the distribution includes an incorrectly configured DNS record
that points to another CloudFront distribution. You must update the DNS record to correct the problem.
```

## **エラーの原因**
1. **DNSプロバイダ**（例: Cloudflare）に登録されているCNAMEレコードが既に **別のCloudFrontディストリビューション** に設定されている。
2. 同じ **CNAME（ドメイン名）** を複数のCloudFrontディストリビューションで設定しようとした。

## **対応手順**

### **1. 競合しているCloudFrontディストリビューションを特定する**

#### **AWS CLIを使用して競合を確認**
```
aws cloudfront list-conflicting-aliases \
  --distribution-id <対象のディストリビューションID> \
  --alias <該当のCNAME>
```

- `<対象のディストリビューションID>`: エラーが発生しているCloudFrontのID。
- `<該当のCNAME>`: 設定しようとしているCNAME（例: `example.com`）。

**出力例**:
```
{
  "ConflictingAliasesList": {
    "ConflictingAliases": [
      {
        "Alias": "***********.com",
        "DistributionId": "E3XXXXXXXXXXXXXX"
      }
    ]
  }
}
```

- **`DistributionId`**: 競合しているCloudFrontディストリビューションIDが確認できます。

### **2. DNSレコードの設定を確認**

#### **DNSプロバイダでCNAMEを確認**
1. **Cloudflare**、**Route53** などのDNSプロバイダにログインします。
2. 競合しているCNAMEレコードが **どのCloudFrontディストリビューション** を指しているか確認します。

#### **CNAMEを削除または修正**
- 既存のCNAMEが別のCloudFrontディストリビューションを指している場合、該当のCNAMEレコードを削除します。
- 新しいCloudFrontディストリビューションを指すようにCNAMEレコードを更新します。

**例: Cloudflareでの設定**
| タイプ   | 名前               | コンテンツ                  | ステータス |
|----------|--------------------|-----------------------------|------------|
| CNAME    | `example.com`      | `dXXXXXX.cloudfront.net`    | DNSのみ    |

### **3. CloudFrontのCNAME設定を更新**

新しいCloudFrontディストリビューションの `aliases` に該当のCNAMEを追加し、エラーが解消されたことを確認します。

### **4. 再確認**

#### **CNAMEが新しいCloudFrontに正しく向いているか確認**

**CLIでDNSの確認**:
```
nslookup example.com
```

**期待する結果**:
- 出力結果が新しいCloudFrontのドメイン名（例: `dXXXXXX.cloudfront.net`）を返す。

## **再発防止策**

1. **CNAMEの管理ルールを明確化**:
   - 各CloudFrontディストリビューションのCNAME設定を事前にドキュメント化。
2. **TerraformやInfrastructure as Code (IaC) の使用**:
   - 既存リソースの状態管理をTerraformで行い、競合を防止。
3. **DNSプロバイダとCloudFront設定の整合性確認**:
   - DNS設定を更新する際には、CloudFront側のCNAME設定も必ず確認。

### **まとめ**

`CNAMEAlreadyExists` エラーの解消手順:
1. AWS CLIで **競合するCNAME** を特定。
2. DNSプロバイダで **CNAMEレコードを修正**。
3. CloudFrontディストリビューションの **aliases設定を更新**。
4. CNAMEが新しいCloudFrontを指していることを確認。

これにより、CNAMEの競合を解消し、正常にCloudFrontを設定できます。
