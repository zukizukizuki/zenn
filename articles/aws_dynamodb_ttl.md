---
title: "【AWS】DynamoDBでTTLに達したデータをS3 Glacierへアーカイブする構成"
emoji: "🍷"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , DynamoDB, terraform , Python, lambda]
published: true
---

## 概要

この構成は、IoTデバイスから送信されたデータをDynamoDBに格納し、設定したTTL（Time To Live）に基づいて自動的に削除されたデータを、低コストなS3 Glacierストレージにアーカイブするものです。

## 目的

*   **データ保持要件の遵守:** 一定期間経過したデータを削除する必要があるものの、監査や分析のために長期的な保管が必要な場合に、コスト効率よくデータを保持します。
*   **コスト最適化:** アクティブに使用するデータは高速なDynamoDBに、アクセス頻度の低い過去データは低コストなS3 Glacierに保管することで、全体的なストレージコストを削減します。
*   **運用負荷の軽減:** TTLによる自動削除と、削除されたデータの自動アーカイブにより、手動でのデータ管理作業を削減します。

## 構成要素

1.  **IoT Core (SQS):** IoTデバイスからのデータは、まずSQS (またはIoT Coreルールエンジン) を経由してLambda関数に渡されます。

2.  **Lambda (SQS -> DynamoDB):** SQSに格納されたJSONデータを取得し、DynamoDBに書き込むLambda関数です。このLambda関数は、データにTTLを設定するための`expiredAt`属性を追加します。

3.  **DynamoDB:** 取得したデータを格納するNoSQLデータベースです。`expiredAt`属性をTTL属性として設定することで、指定された期間が経過したデータを自動的に削除します。

4.  **DynamoDB Streams:** DynamoDBテーブルの変更履歴を記録する機能です。データの作成、更新、削除などのイベントが発生すると、その内容がストリームに記録されます。

5.  **Lambda (DynamoDB Streams -> S3 Glacier):** DynamoDB Streamsからのイベントを受け取り、TTLによって削除されたデータをJSON形式でS3 GlacierにアーカイブするLambda関数です。

6.  **S3 Glacier:** 長期的なデータ保管に適した、低コストなストレージサービスです。アーカイブされたデータは、必要な場合に取得して分析などに利用できます。

## 構成図

![](https://storage.googleapis.com/zenn-user-upload/017dba26ed62-20250218.png)

## コード

### SQS(IoT Core)からJSONを吸い上げてDynamoDBに入れるLambdaのterraform設定
```
################
# lambdaのソースのzip
################
data "archive_file" "function_archive" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_putSensorData/"
  output_path = "${path.module}/lambda_putSensorData/output/functions.zip"
}

############################
# IotデータをlambdaにキューするためのSQS
############################
resource "aws_sqs_queue" "ba_sqs" {
  name                       = "${var.environment}_ba_sqs"
  visibility_timeout_seconds = 900
  tags                       = { environment = "${var.environment}" }

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::<ACCOUNT_ID>:role/<IOT_ROLE_NAME>" # 秘匿情報: AWSアカウントIDとIAMロール名を隠蔽
        }
        Action   = "sqs:SendMessage"
        Resource = "arn:aws:sqs:ap-northeast-1:<AWS_ACCOUNT_ID>:${var.environment}_ba_sqs" # 秘匿情報: AWSアカウントIDを隠蔽
      }
    ]
  })
}

######################
# S3に配置するlambdaソースのzip
######################
resource "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.lambda_bucket.bucket
  key    = "cross-account-${filemd5(data.archive_file.function_archive.output_path)}.zip"
  source = data.archive_file.function_archive.output_path
  etag   = filemd5(data.archive_file.function_archive.output_path)
  tags   = { environment = "${var.environment}" }
}


########################
# データを処理するためのlambda関数
########################
resource "aws_lambda_function" "sensor_data_ingest_lambda" {
  architectures    = ["arm64"]
  function_name    = "${var.environment}-sensor-data-ingest"
  handler          = "lambda_function.lambda_handler"
  memory_size      = 128
  package_type     = "Zip"
  role             = data.aws_iam_role.admin_for_lambda.arn # 適切なIAMロールのARNを設定
  runtime          = "python3.12"
  s3_bucket        = aws_s3_bucket.lambda_bucket.bucket
  s3_key           = aws_s3_object.lambda_zip.key
  source_code_hash = data.archive_file.function_archive.output_base64sha256
  tags = {
    "lambda:createdBy" = "SAM",
    environment        = "${var.environment}"
  }
  tags_all = {
    "lambda:createdBy" = "SAM"
  }
  timeout = 900
  environment {
    variables = merge(var.lambda_environment_variables, {
      DEVICE_DATA = "${var.environment}_DeviceData"
    })
  }
  logging_config {
    log_format = "Text"
    log_group  = "/aws/lambda/${var.environment}-sensor-data-ingest" # ロググループ名も変更
  }
  tracing_config {
    mode = "PassThrough"
  }
}

####################
# lambdaのトリガー対象を指定
####################
resource "aws_lambda_event_source_mapping" "sqs_source_mapping" {
  event_source_arn                   = aws_sqs_queue.ba_sqs.arn
  function_name                      = aws_lambda_function.sensor_data_ingest_lambda.arn
  batch_size                         = 20
  maximum_batching_window_in_seconds = 60
  bisect_batch_on_function_error     = false
  enabled                            = true
  tags                               = { environment = "${var.environment}" }
  lifecycle {
    ignore_changes = [enabled]
  }
}
```

### SQS(IoT Core)からJSONを吸い上げてexpiredAt(TTL)を追加した上でDynamoDBに入れるLambda

```python
import boto3
import os
import json
import base64
from decimal import Decimal
import logging
import time

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.WARNING)  # WARNINGレベル以上のログ出力

dynamoDB = boto3.resource('dynamodb')

# 1年分の秒数
ONE_YEAR_IN_SECONDS = 31536000

def lambda_handler(event, context):
    table = dynamoDB.Table(os.environ['DEVICE_DATA'])

    with table.batch_writer(overwrite_by_pkeys=['deviceID', 'createdAt']) as batch:
        for record in event['Records']:
            message_body = record['body']

            # Base64 エンコードされている場合の処理
            try:
                decoded_bytes = base64.b64decode(message_body)
                decoded_str = decoded_bytes.decode('utf-8')
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                logger.error(f'Error decoding or parsing message body: {e}')
                continue

            try:
                data = json.loads(decoded_str, parse_float=Decimal)
            except json.JSONDecodeError as e:
                logger.error(f'Error parsing JSON: {e}')
                continue
            
            if "things_name" in data:
              client_id = data.get('things_name', '')
              data['topic'] = client_id + "/SENSOR/DAT"  #topicを追加
              data['client_id'] = client_id #client_idを追加

            logger.info(f'Received data: {data}')  # デバッグ用ログ

            if is_except_data(data.get('client_id', '')):
                data = {k.lower(): v for k, v in data.items()}
                data = convert_floats_to_decimals(data)
                try:
                    put_device_data(data, batch) #expiredAtを渡す必要はありません
                except KeyError as e:
                    logger.error(f'KeyError: {e}. Data: {data}')
                    continue

    return {
        'statusCode': 200
    }

def is_except_data(things_name):
    if os.environ.get('APP_ENV', '') == "Staging":
        return 'stg' in things_name
    else:
        return 'stg' not in things_name

def put_device_data(data, batch):
    
    # データ内にdataキーが存在するか確認する
    data_value = data.get('data', None)
    
    if data_value:  # dataキーが存在する場合
        if isinstance(data_value, dict): # dataが辞書型の場合
           
            # 'createdAt' キーが存在しない場合は 'timestamp' の値を使用
            createdAt = data_value.get('createdAt', data.get('timestamp'))
            if createdAt is None:
                createdAt = data.get('timestamp')
                if createdAt is None:
                  logger.error(f'KeyError: createdAt and timestamp are both None. Data: {data}')
                  return

            if len(str(createdAt)) == 10:
                createdAt *= 1000
            # expiredAt を計算
            expiredAt = int(createdAt / 1000) + ONE_YEAR_IN_SECONDS  # ミリ秒単位から秒単位に変換してから1年を足す
            data_value['expiredAt'] = expiredAt #data_value に expiredAt を追加

            data_value.update({
                'createdAt': createdAt,
                'deviceID': data.get('topic', '').split('/')[0],
                'sensorID': data.get('topic', '').split('/')[0] + "-sen",
            })

            logger.info(f'Putting item into DynamoDB: {data_value}') # INFOレベルなので出力されます
            try:
                batch.put_item(Item=data_value)
            except Exception as e:
                logger.error(f'Error putting item into DynamoDB: {e}. Item: {data_value}')


        elif isinstance(data_value, list): # dataがリスト型の場合
            for item in data_value:
                if item is None:
                    logger.error(f'Item is None. Data: {data}')
                    continue
                
                # item が辞書型かどうかをチェック
                if isinstance(item, dict):
                    # 'createdAt' キーが存在しない場合は 'timestamp' の値を使用
                    createdAt = item.get('createdAt', data.get('timestamp'))
                    if createdAt is None:
                        logger.error(f'KeyError: createdAt and timestamp are both None. Data: {data}')
                        continue  # または raise KeyError('createdAt and timestamp') でエラーを投げる

                    if len(str(createdAt)) == 10:
                        createdAt *= 1000

                    # expiredAt を計算
                    expiredAt = int(createdAt / 1000) + ONE_YEAR_IN_SECONDS  # ミリ秒単位から秒単位に変換してから1年を足す
                    item['expiredAt'] = expiredAt #item に expiredAt を追加

                    item.update({
                        'createdAt': createdAt,
                        'deviceID': data.get('topic', '').split('/')[0],
                        'sensorID': data.get('topic', '').split('/')[0] + "-sen",
                    })

                    logger.info(f'Putting item into DynamoDB: {item}') # INFOレベルなので出力されます
                    try:
                        batch.put_item(Item=item)
                    except Exception as e:
                        logger.error(f'Error putting item into DynamoDB: {e}. Item: {item}')
                else:
                   logger.error(f'Item is not a dict. Item: {item}. Data: {data}')
        else: # data が辞書でもリストでもない場合
            logger.error(f'Data is not a dict or a list. Data: {data}')
    else: # dataキーが存在しない場合、dataを単一アイテムとして処理する
        # 'createdAt' キーが存在しない場合は 'timestamp' の値を使用
        createdAt = data.get('createdat', data.get('timestamp'))
        if createdAt is None:
            logger.error(f'KeyError: createdAt and timestamp are both None. Data: {data}')
            return  # または raise KeyError('createdAt and timestamp') でエラーを投げる

        if len(str(createdAt)) == 10:
            createdAt *= 1000
        
        if "things_name" in data:
          client_id = data.get('things_name', '')
        else:
          client_id = data.get('topic', '').split('/')[0]

        # expiredAt を計算
        expiredAt = int(createdAt / 1000) + ONE_YEAR_IN_SECONDS  # ミリ秒単位から秒単位に変換してから1年を足す
        data['expiredAt'] = expiredAt #dataにexpiredAtを追加
        data.update({
            'createdAt': createdAt,
            'deviceID': client_id,
            'sensorID': client_id + "-sen",
        })
        logger.info(f'Putting item into DynamoDB: {data}') # INFOレベルなので出力されます

        try:
            batch.put_item(Item=data)
        except Exception as e:
            logger.error(f'Error putting item into DynamoDB: {e}. Item: {data}')

def convert_floats_to_decimals(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = convert_floats_to_decimals(value)
    elif isinstance(obj, list):
        obj = [convert_floats_to_decimals(item) for item in obj]
    return obj
```

### DynamoDBのTerraform設定

```terraform
resource "aws_dynamodb_table" "DeviceData" {
  billing_mode                = "PROVISIONED"
  deletion_protection_enabled = false
  hash_key                    = "deviceID"
  name                        = "${var.environment}_DeviceData"
  range_key                   = "createdAt"
  table_class                 = "STANDARD"
  stream_enabled              = true
  stream_view_type            = "OLD_IMAGE"
  tags                        = { environment = "${var.environment}" }

  attribute {
    name = "createdAt"
    type = "N"
  }
  attribute {
    name = "deviceID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  read_capacity  = 38 # hazaviewの推奨読み込みキャパシティ
  write_capacity = 22 # hazaviewの推奨書き込みキャパシティ

  ttl {
    attribute_name = "expiredAt"
    enabled        = true
  }
}
```

### TTLを迎えたデータをS3 GlacierにアーカイブするLambda

```python
import boto3
import json
import os
import logging

# S3クライアントを初期化
s3 = boto3.client('s3')

# 環境変数からS3バケット名を取得
S3_BUCKET = os.environ.get('S3_BUCKET')

# ロガーを初期化
logger = logging.getLogger()
logger.setLevel(logging.WARNING)  # ログレベルをWARNINGに設定 (INFOから変更)

def lambda_handler(event, context):
    """
    Lambda関数のハンドラ

    DynamoDBストリームイベントを処理し、TTLを迎えて削除されたデータをS3 Glacierにアーカイブする。
    REMOVEイベントに関するログのみを出力するように変更。

    Args:
        event (dict): Lambdaイベントデータ (DynamoDBストリームイベント)
        context (LambdaContext): Lambdaコンテキストオブジェクト

    Returns:
        dict: 処理結果のステータスコードとメッセージ
    """

    # S3_BUCKET環境変数が設定されているかチェック
    if not S3_BUCKET:
        logger.error("S3_BUCKET environment variable is not set.")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'S3_BUCKET environment variable is not set.'})
        }

    logger.info("Received event: %s", json.dumps(event)) # イベント全体のログはINFOレベルで出力 (デバッグ用として残す)

    for record in event['Records']:
        if record['eventName'] == 'REMOVE': # REMOVEイベント (TTL削除) の場合のみ処理
            logger.info("Processing REMOVE record: %s", json.dumps(record)) # REMOVEイベントの処理開始ログをINFOレベルで出力
            if 'dynamodb' in record and 'OldImage' in record['dynamodb']: # OldImageが存在するかチェック
                dynamodb_data = record['dynamodb']['OldImage']
                try:
                    # データ型を指定して値を取得
                    device_id = dynamodb_data['deviceID']['S']
                    created_at = dynamodb_data['createdAt']['N']
                    #expired_at = dynamodb_data['expiredAt']['N']  # 追加: expiredAt の値を取得

                    # S3に保存するファイル名 (アーカイブ/deviceID/createdAt.json)
                    s3_key = f"archive/{device_id}/{created_at}.json"

                    # DynamoDBのデータをJSON文字列に変換 (日付型を文字列に変換するためのdefault指定)
                    json_data = json.dumps(dynamodb_data, default=str)

                    # S3 Glacier にデータを保存
                    s3.put_object(
                        Bucket=S3_BUCKET,
                        Key=s3_key,
                        Body=json_data,
                        StorageClass='GLACIER'
                    )
                    logger.info(f"Archived data to s3://{S3_BUCKET}/{s3_key} with storage class GLACIER")

                except KeyError as e:
                    logger.exception(f"KeyError processing record: {e}.  Check if 'deviceID' and 'createdAt' exist and have the correct type (S and N).") # エラー詳細ログ (スタックトレースを含む) をERRORレベルで出力
                    return {
                        'statusCode': 500,
                        'body': json.dumps({'message': f'Error archiving data to S3: {e}'})
                    }

                except Exception as e:
                    logger.exception(f"Error processing record: {e}") # エラー詳細ログ (スタックトレースを含む) をERRORレベルで出力
                    return {
                        'statusCode': 500,
                        'body': json.dumps({'message': f'Error archiving data to S3: {e}'})
                    }
            else:
                logger.warning("OldImage not found in REMOVE event. Skipping archive for this record.") # 警告ログをWARNINGレベルで出力 (OldImageがない場合)
        # REMOVEイベント以外の場合はログ出力しない (INFOレベル以上のログレベル設定のため)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Successfully processed DynamoDB records.'})
    }
```

### S3バケットとLambda関数の設定

```terraform
resource "aws_s3_bucket" "archive_bucket" {
  bucket = "${var.environment}-dynamodb-archive-bucket"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_DynamoDB_archive/"
  output_path = "${path.module}/lambda_DynamoDB_archive/output/functions.zip"
}

resource "aws_lambda_function" "archive_lambda" {
  function_name = "${var.environment}-dynamodb-archive"
  description   = "Lambda function to archive DynamoDB TTL deleted items to S3 Glacier"
  role          = data.aws_iam_role.for_lambda.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128
  filename      = data.archive_file.lambda_zip.output_path

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.archive_bucket.bucket
    }
  }
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}

# DynamoDB ストリームトリガーの作成 (Lambda 関数をトリガー)
resource "aws_lambda_event_source_mapping" "dynamodb_trigger" {
  event_source_arn  = aws_dynamodb_table.DeviceData.stream_arn
  function_name     = aws_lambda_function.archive_lambda.arn
  starting_position = "LATEST"
  batch_size        = 100
}
```

## 補足
*   `${var.environment}`は環境変数に合わせて変更してください。
*   `data.aws_iam_role.for_lambda.arn`は、適切なIAMロールのARNに置き換えてください。
*   上記は例であり、必要に応じて設定を調整してください。
