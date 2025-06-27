---
title: "【AWS】最もオーソドックスな分析基盤の構築手順 - 完全版ガイド"
emoji: "📊"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS, analytics, S3, Glue, Athena, QuickSight, 分析基盤]
published: true
---

## 1. はじめに

企業が持つデータを効果的に活用するために、データ分析基盤の構築は欠かせません。AWSでは複数のマネージドサービスを組み合わせることで、スケーラブルで費用対効果の高い分析基盤を構築できます。

本記事では、AWSの分析サービスを使った最もオーソドックスな構成での分析基盤構築手順を詳しく解説します。

---

## 2. 分析基盤のアーキテクチャ概要

### 基本構成図

```
[データソース] → [S3] → [AWS Glue] → [Amazon Athena] → [Amazon QuickSight]
     ↓             ↓         ↓             ↓               ↓
   RDS/DynamoDB  データレイク  ETL処理     SQLクエリ     可視化・ダッシュボード
   ログファイル
   外部API
```

### 各コンポーネントの役割

- **Amazon S3**: データレイクとして大量データを安価に保存
- **AWS Glue**: データカタログ管理とETL処理
- **Amazon Athena**: S3上のデータをSQLで分析
- **Amazon QuickSight**: ビジネスインテリジェンス・可視化ツール

---

## 3. 前提条件

- AWSアカウントの準備
- IAM権限の設定（各サービスへのアクセス権限）
- 分析対象となるデータの準備

---

## 4. 手順1: Amazon S3でデータレイクを構築

### S3バケットの作成

```bash
# AWS CLI使用例
aws s3 mb s3://your-analytics-datalake-bucket --region ap-northeast-1
```

### フォルダ構造の設計

```
your-analytics-datalake-bucket/
├── raw-data/           # 生データ
│   ├── sales/
│   ├── customers/
│   └── products/
├── processed-data/     # 加工後データ
│   ├── sales/
│   └── customers/
└── query-results/      # Athenaクエリ結果
```

### データのアップロード

```bash
# CSVファイルのアップロード例
aws s3 cp sales_data.csv s3://your-analytics-datalake-bucket/raw-data/sales/
```

---

## 5. 手順2: AWS Glueでデータカタログとクローラーの設定

### Glueデータベースの作成

1. AWS Glueコンソールにアクセス
2. 「データベース」から「データベースの追加」をクリック
3. データベース名: `analytics_database` を入力

### クローラーの作成

```bash
# AWS CLI例：クローラーの作成
aws glue create-crawler \
    --name sales-data-crawler \
    --role AWSGlueServiceRole-analytics \
    --database-name analytics_database \
    --targets '{"S3Targets":[{"Path":"s3://your-analytics-datalake-bucket/raw-data/sales/"}]}'
```

### クローラーの実行

```bash
# クローラーの実行
aws glue start-crawler --name sales-data-crawler
```

---

## 6. 手順3: ETL処理の作成

### Glue ETLジョブの作成

```python
# Glue ETLジョブのサンプルコード
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# データソースの読み込み
datasource0 = glueContext.create_dynamic_frame.from_catalog(
    database = "analytics_database",
    table_name = "raw_data_sales"
)

# データ変換処理
applymapping1 = ApplyMapping.apply(
    frame = datasource0,
    mappings = [
        ("sale_id", "string", "sale_id", "string"),
        ("customer_id", "string", "customer_id", "string"),
        ("amount", "double", "amount", "double"),
        ("sale_date", "string", "sale_date", "timestamp")
    ]
)

# 結果をS3に保存
datasink2 = glueContext.write_dynamic_frame.from_options(
    frame = applymapping1,
    connection_type = "s3",
    connection_options = {
        "path": "s3://your-analytics-datalake-bucket/processed-data/sales/"
    },
    format = "parquet"
)

job.commit()
```

---

## 7. 手順4: 加工後データのカタログ登録

### 加工後データ用クローラーの作成

ETL処理で生成されたParquetファイルをAthenaでクエリするため、加工後データ用のクローラーを作成します。

```bash
# 加工後データ用のクローラーを作成
aws glue create-crawler \
    --name processed-data-crawler \
    --role AWSGlueServiceRole-analytics \
    --database-name analytics_database \
    --targets '{"S3Targets":[{"Path":"s3://your-analytics-datalake-bucket/processed-data/sales/"}]}'
```

### 加工後データクローラーの実行

```bash
# クローラーの実行
aws glue start-crawler --name processed-data-crawler

# クローラー実行状況の確認
aws glue get-crawler --name processed-data-crawler
```

---

## 8. 手順5: Amazon Athenaでクエリ環境の構築

### Athenaの初期設定

1. Athenaコンソールにアクセス
2. クエリ結果の保存場所を設定: `s3://your-analytics-datalake-bucket/query-results/`

### テーブル存在確認

ビューを作成する前に、加工後データのテーブルがData Catalogに正しく登録されているか確認します。

```sql
-- データベース内のテーブル一覧を確認
SHOW TABLES IN analytics_database;

-- 加工後データテーブルの構造確認
DESCRIBE analytics_database.processed_data_sales;

-- データの存在確認
SELECT COUNT(*) FROM analytics_database.processed_data_sales LIMIT 10;
```

**注意**: もし `processed_data_sales` テーブルが存在しない場合は、以下を確認してください：
1. ETLジョブが正常に完了しているか
2. 加工後データ用クローラー（processed-data-crawler）が実行済みか
3. S3の加工後データフォルダにParquetファイルが出力されているか

```bash
# S3の加工後データ確認
aws s3 ls s3://your-analytics-datalake-bucket/processed-data/sales/ --recursive

# クローラーの再実行（必要に応じて）
aws glue start-crawler --name processed-data-crawler
```

### サンプルクエリの実行

```sql
-- 売上データの基本分析
SELECT 
    DATE_FORMAT(sale_date, '%Y-%m') as month,
    COUNT(*) as transaction_count,
    SUM(amount) as total_sales,
    AVG(amount) as avg_sale_amount
FROM analytics_database.processed_data_sales
WHERE sale_date >= DATE('2024-01-01')
GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
ORDER BY month;
```

### ビューの作成

テーブルの存在確認完了後、分析用ビューを作成します。

```sql
-- 月次売上サマリビューの作成
CREATE VIEW monthly_sales_summary AS
SELECT 
    DATE_FORMAT(sale_date, '%Y-%m') as month,
    COUNT(*) as transaction_count,
    SUM(amount) as total_sales,
    AVG(amount) as avg_sale_amount
FROM analytics_database.processed_data_sales
GROUP BY DATE_FORMAT(sale_date, '%Y-%m');
```

---

## 9. 手順6: Amazon QuickSightでダッシュボード作成

### QuickSightの初期設定

1. QuickSightコンソールにアクセス
2. アカウントの作成（Standard Edition推奨）
3. S3およびAthenaへのアクセス権限を付与

### データセットの作成

1. 「データセット」→「新しいデータセット」
2. データソース: 「Athena」を選択
3. データベース: `analytics_database`
4. テーブル: `monthly_sales_summary`

### ダッシュボードの作成

```
推奨ビジュアル構成：
├── 月次売上推移（線グラフ）
├── 売上TOP10商品（棒グラフ）
├── 地域別売上分析（地図）
└── KPI指標（数値カード）
```

---

## 10. 運用とモニタリング

### CloudWatchでのモニタリング設定

```bash
# Glueジョブの実行状況監視
aws logs create-log-group --log-group-name /aws/glue/jobs/sales-etl-job
```

### 自動化の設定

```bash
# EventBridgeでスケジュール実行
aws events put-rule \
    --name daily-etl-schedule \
    --schedule-expression "cron(0 2 * * ? *)" \
    --state ENABLED
```

---

## 11. セキュリティとコスト最適化

### IAMロールの設定

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-analytics-datalake-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "glue:GetTable",
                "glue:GetPartitions"
            ],
            "Resource": "*"
        }
    ]
}
```

### コスト最適化のポイント

- **S3**: Intelligent Tieringの活用
- **Glue**: DPU（Data Processing Unit）の最適化
- **Athena**: パーティション分割によるスキャン量削減
- **QuickSight**: 必要最小限のユーザー数での運用

---

## 12. トラブルシューティング

### よくある問題と解決方法

#### Glueクローラーがテーブルを認識しない

```bash
# データ形式の確認
aws s3 ls s3://your-analytics-datalake-bucket/raw-data/sales/ --recursive
```

#### Athenaクエリが遅い

```sql
-- パーティション追加
ALTER TABLE analytics_database.sales_data 
ADD PARTITION (year='2024', month='01') 
LOCATION 's3://your-analytics-datalake-bucket/processed-data/sales/year=2024/month=01/';
```

---

## 13. まとめ

本記事で紹介した構成は、AWSにおける分析基盤の基本パターンです。

### 構築完了後の利点

- **スケーラビリティ**: データ量の増加に柔軟に対応
- **コスト効率**: 従量課金制でのコスト最適化
- **保守性**: マネージドサービスによる運用負荷軽減
- **拡張性**: 新しいデータソースの追加が容易

### 次のステップ

- **リアルタイム分析**: Amazon Kinesis Analyticsの導入
- **機械学習**: Amazon SageMakerとの連携
- **データガバナンス**: AWS Lake Formationの活用

このオーソドックスな構成をベースに、組織の要件に合わせてカスタマイズしていくことで、効果的なデータ分析基盤を構築できます。
