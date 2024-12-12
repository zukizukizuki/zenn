---
title: "【AWS】CloudFrontをterraformで作るためus-east-01で管理する"
emoji: "🏓"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , CloudFront, terraform , ACM]
published: true
---

CloudFrontは`us-east-1`リージョンにリソースを作成する必要があります。そのため、別リージョンで作成したリソースをCloudFrontで利用する場合、以下のようにプロバイダとモジュールを設定します。

以下のコードでは、CloudFrontのリソースは`us-east-1`で作成し、S3バケットなどのリソースは`ap-northeast-1`で作成する例を示しています。

```
# プロバイダ設定
provider "aws" {
  region = "ap-northeast-1"
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# S3バケット (ap-northeast-1 リージョン)
resource "aws_s3_bucket" "example_bucket" {
  bucket = "example-bucket-ap-northeast-1"
  acl    = "private"
}

# CloudFront設定 (us-east-1 リージョン)
resource "aws_cloudfront_distribution" "example_distribution" {
  provider = aws.us_east_1

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket.example_bucket.bucket_domain_name
    origin_id   = "example-origin"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.example.iam_arn
    }
  }

  default_cache_behavior {
    target_origin_id       = "example-origin"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.us_east_1_cert.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Environment = "example"
  }
}

# Origin Access Identity (us-east-1)
resource "aws_cloudfront_origin_access_identity" "example" {
  provider    = aws.us_east_1
  comment     = "Example OAI for CloudFront"
}

# ACM証明書 (us-east-1)
resource "aws_acm_certificate" "us_east_1_cert" {
  provider          = aws.us_east_1
  domain_name       = "*.example.com"
  validation_method = "DNS"

  tags = {
    Environment = "example"
  }
}
```

## ポイント
1. **プロバイダの指定**
   - `aws.us_east_1`をCloudFrontやACM証明書など`us-east-1`で作成する必要があるリソースに使用。
   - デフォルトの`aws`プロバイダは`ap-northeast-1`で使用。

2. **リソース間の連携**
   - S3バケットなど`ap-northeast-1`で作成したリソースの情報をCloudFrontに渡す。
   - 例: `aws_s3_bucket.example_bucket.bucket_domain_name`。

