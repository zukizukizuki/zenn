---
title: "【AWS】WAFをterraform importしようとしたらThe scope is not valid(400エラー) が出る"
emoji: "🌪️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , CloudFront, terraform , WAF]
published: true
---

## 事象
terraform import ブロックやterraform importコマンドでCloudFrontに割り当てたAWS WAFをimportしようとすると以下のエラー

```
Error: reading WAFv2 WebACL : operation error WAFV2: GetWebACL, https response error StatusCode: 400, RequestID: 77e90616-f220-46e7-a5f5-328eafeea190, WAFInvalidParameterException: Error reason: The scope is not valid., field: SCOPE_VALUE, parameter: CLOUDFRONT
```

## 結論
CloudFront を対象としたWAFをimportする場合は us-east-1(バージニア北部)を指定する
なのでap-northeast-01などで管理している場合はstateファイルを分割する必要がある

## 参考
https://registry.terraform.io/providers/babylonhealth/aws-babylon/latest/docs/resources/wafv2_web_acl#scope