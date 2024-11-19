---
title: "ElasticCache で SSL: WRONG_VERSION_NUMBER が出た時の対処方法"
emoji: "🌰"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [ElasticCache , redis, aws, SSL, terraform]
published: true
---

## 背景
AWS Lambda 関数から ElastiCache (Redis) に接続した際、以下のエラーが発生しました。

```
[ERROR] ConnectionError: Error 1 connecting to <Redisエンドポイント>:6379. [SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:1000).
```

このエラーは、Redis への接続時に TLS (SSL) が無効になっている場合に発生することが判明しました。本記事では、この問題を解決するために TLS を有効化した手順を記録します。

---

## 発生していた問題
1. **ElastiCache の TLS が無効**
   - `TransitEncryptionEnabled` が `false` の状態であったため、Lambda 環境変数で `rediss://` プロトコルを使用して接続を試みた際に失敗していました。

2. **エラー詳細**
   - `SSL: WRONG_VERSION_NUMBER` エラーは、TLS が無効なクラスターに対して `rediss://` を使用して接続した場合に発生します。

---

## 解決手順

### 1. ElastiCache の TLS サポート状況を確認
ElastiCache クラスターが TLS をサポートしているかを確認しました。

```
aws elasticache describe-replication-groups --replication-group-id prd-redis
```

**確認結果**:
```
"TransitEncryptionEnabled": false
```
TLS が無効であることを確認しました。

---

### 2. ElastiCache の TLS を有効化
TLS を有効にするために、Terraform の ElastiCache 設定を修正しました。

**修正前のコード:**
```
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.environment}-redis"
  engine                     = "redis"
  engine_version             = "6.x"
  node_type                  = "cache.t3.micro"
  automatic_failover_enabled = false
  security_group_ids         = var.ElastiCache_security_group_ids
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  description                = "redis"
  tags = {
    environment = var.environment
  }
}
```

**修正後のコード:**
```
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.environment}-redis"
  engine                     = "redis"
  engine_version             = "6.x"
  node_type                  = "cache.t3.micro"
  automatic_failover_enabled = false
  security_group_ids         = var.ElastiCache_security_group_ids
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  description                = "redis"
  transit_encryption_enabled = true  # TLS を有効化
  tags = {
    environment = var.environment
  }
}
```

---

### 3. Lambda の接続設定の確認
Lambda の環境変数で設定している Redis URL に問題がないかを確認しました。

**環境変数の値:**
```
REDIS_URL = "rediss://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0"
```

**生成された実際の URL:**
```
rediss://<Redisエンドポイント>:6379/0
```

問題なく正しい形式で生成されていることを確認しました。

---

### 4. 動作確認
修正後、再デプロイを実施して動作確認を行いました。

```
terraform apply
```

その後、Lambda 関数をトリガーした結果、Redis に正しく接続できることを確認しました。

---

## まとめ
本記事では、AWS Lambda から ElastiCache (Redis) への接続で発生した TLS 関連のエラーを解消するための手順を説明しました。

主なポイントは以下の通りです：
1. **ElastiCache の TLS を有効化する**: `transit_encryption_enabled = true` を設定。
2. **Lambda の接続設定を確認する**: 環境変数で `rediss://` プロトコルを正しく使用。

これにより、Redis 接続が安全に行えるようになりました。
