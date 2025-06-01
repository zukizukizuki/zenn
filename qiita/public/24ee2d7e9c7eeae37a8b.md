---
title: 'AWS API Gateway: カスタムドメイン削除時のエラー解決とTerraform管理方法'
tags:
  - GitHub
  - AWS
  - API
  - Terraform
private: false
updated_at: '2024-12-09T18:50:11+09:00'
id: 24ee2d7e9c7eeae37a8b
organization_url_name: null
slide: false
ignorePublish: false
---
## エラー内容
terraformでAWS API Gateway のカスタムドメインを削除しようとした際に以下のエラーが発生しました。

```
Error: deleting API Gateway v2 Stage ($default): operation error ApiGatewayV2: DeleteStage, https response error StatusCode: 400, RequestID: xxxx-yyyy-zzzz, api error BadRequestException: Deleting stage $default failed. Please remove all base path mappings related to the stage in your domains: example-dashboard.example.com
```

## 原因
このエラーは、API Gateway Stage（例: `$default`）が **カスタムドメインと Base Path Mapping** に関連付けられている場合に発生します。  
Base Path Mapping が存在していると、削除する際に依存関係が原因でブロックされます。

関連付けがあるカスタムドメインを削除するには、**まず Base Path Mapping を削除**する必要があります。

## 解決策

### 1. Base Path Mapping を削除
AWS マネジメントコンソールまたは AWS CLI を使用して、カスタムドメインに設定されている Base Path Mapping を削除します。

### AWS マネジメントコンソールでの手順
1. **API Gateway コンソール**にアクセス。
2. 左メニューから「カスタムドメイン名」を選択。
3. 対象のドメイン（例: `example-dashboard.example.com`）をクリック。
4. 「Base Path Mappings」セクションで、関連付けられている Mapping を削除。

### AWS CLI を使用した削除
```
aws apigatewayv2 delete-api-mapping --domain-name "example-dashboard.example.com" --api-mapping-id <API_MAPPING_ID>
aws apigatewayv2 delete-api-mapping --domain-name "example-detection.example.com" --api-mapping-id <API_MAPPING_ID>
aws apigatewayv2 delete-api-mapping --domain-name "example-managedb.example.com" --api-mapping-id <API_MAPPING_ID>
```

`<API_MAPPING_ID>` は以下のコマンドで取得できます:
```
aws apigatewayv2 get-api-mappings --domain-name "example-dashboard.example.com"
```



### 2. カスタムドメインを削除
Base Path Mapping を削除した後、カスタムドメイン自体を削除します。

```
aws apigatewayv2 delete-domain-name --domain-name "example-dashboard.example.com"
aws apigatewayv2 delete-domain-name --domain-name "example-detection.example.com"
aws apigatewayv2 delete-domain-name --domain-name "example-managedb.example.com"
```



## Terraform でカスタムドメインを管理する方法

Terraform を使用してカスタムドメインとその関連付けを管理することで、一貫性のあるインフラ管理が可能になります。以下は、Terraform を使った具体的な例です。

### 1. カスタムドメインの作成
```
resource "aws_apigatewayv2_domain_name" "custom_domain" {
  domain_name              = "example-dashboard.example.com"
  domain_name_configuration {
    certificate_arn = aws_acm_certificate.domain_cert.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}
```

### 2. Base Path Mapping の作成
```
resource "aws_apigatewayv2_api_mapping" "custom_mapping" {
  api_id      = aws_apigatewayv2_api.example_api.id
  domain_name = aws_apigatewayv2_domain_name.custom_domain.id
  stage       = aws_apigatewayv2_stage.example_stage.name
}
```

### 3. ACM 証明書の管理
Terraform を使って ACM 証明書を作成し、DNS 検証を自動化します。

```
resource "aws_acm_certificate" "domain_cert" {
  domain_name       = "example-dashboard.example.com"
  validation_method = "DNS"
}

resource "aws_route53_record" "domain_validation" {
  zone_id = aws_route53_zone.main.id
  name    = aws_acm_certificate.domain_cert.domain_validation_options[0].resource_record_name
  type    = aws_acm_certificate.domain_cert.domain_validation_options[0].resource_record_type
  records = [aws_acm_certificate.domain_cert.domain_validation_options[0].resource_record_value]
  ttl     = 300
}
```
## まとめ
- **エラー原因**: カスタムドメインの削除時に Base Path Mapping が存在しているため。
- **解決策**: Base Path Mapping を削除してからカスタムドメインを削除する。
- **Terraform 利用**: カスタムドメイン、Base Path Mapping、ACM 証明書をコードとして管理することで、一貫性のあるインフラ管理を実現。

Terraform を使用することで、手動操作を減らし、再現性のある管理が可能になります。ぜひお試しください！
