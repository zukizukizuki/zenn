---
title: 【AWS】terraformでSQSのメッセージをlambdaで処理してDynamoDBに保存する
private: false
tags:
  - AWS
  - lambda
  - SQS
  - DynamoDB
  - serverless
updated_at: '2025-06-01T01:52:47.532Z'
id: null
organization_url_name: null
slide: false
---

## 概要
terraformでSQSのメッセージをlambdaで加工してDynamoDBに保存する
例として'deviceID' と 'createdAt'というカラムがあるデータの処理を実施する

## ポイント
- SQSのメッセージはエンコードされているので受け取るlambda側でデコードが必要
- lambdaのソースコードはS3に入れて管理する

## 構成
```
.
│  backend.tf
│  data_transfer.tf
│  variables.tf
│
└─lambda_function
    │  lambda_function.py
    │
    └─output
            functions.zip
```


## ファイルの中身

`backend.tf`
```
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  cloud {
    organization = "${terraform cloudの組織名}"

    workspaces {
      name = "${terraform cloudのワークスペース名}"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}
```

`data_transfer.tf`

```
# lambdaのソースのzip
data "archive_file" "function_archive" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_function/"
  output_path = "${path.module}/lambda_function/output/functions.zip"
}

# lambda用のロール
data "aws_iam_role" "admin_for_lambda" {
  name = "Admin_for_lambda"
}

# IotデータをlambdaにキューするためのSQS
resource "aws_sqs_queue" "sqs" {
  name                       = "sqs"
  visibility_timeout_seconds = 900
}

# Lambdaのソースを入れるS3
resource "aws_s3_bucket" "lambda_bucket" {
  bucket = "ambda-source-bucket" #一意である必要がある
}

# S3に配置するlambdaソースのzip
resource "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.lambda_bucket.bucket
  key    = "lambda_function.zip"
  source = data.archive_file.function_archive.output_path
}

# lambdaで処理されたデータを格納するDynamoDB
resource "aws_dynamodb_table" "DeviceData" {
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = false
  hash_key                    = "deviceID"
  name                        = "DeviceData"
  range_key                   = "createdAt"
  read_capacity               = 0
  restore_date_time           = null
  restore_source_name         = null
  restore_to_latest_time      = null
  stream_enabled              = false
  stream_view_type            = null
  table_class                 = "STANDARD"
  tags                        = {}
  tags_all                    = {}
  write_capacity              = 0
  attribute {
    name = "createdAt"
    type = "N"
  }
  attribute {
    name = "deviceID"
    type = "S"
  }
  attribute {
    name = "sensorID"
    type = "S"
  }
  global_secondary_index {
    hash_key           = "sensorID"
    name               = "sensorID-createdAt-index"
    non_key_attributes = []
    projection_type    = "ALL"
    range_key          = "createdAt"
    read_capacity      = 0
    write_capacity     = 0
  }
  point_in_time_recovery {
    enabled = false
  }
  ttl {
    attribute_name = null
    enabled        = false
  }
}

# データを処理するためのlambda関数
resource "aws_lambda_function" "lambda_putData" {
  architectures                      = ["arm64"]
  code_signing_config_arn            = null
  function_name                      = "lambda_putData"
  handler                            = "lambda_function.lambda_handler"
  image_uri                          = null
  kms_key_arn                        = null
  layers                             = []
  memory_size                        = 128
  package_type                       = "Zip"
  publish                            = null
  replace_security_groups_on_destroy = null
  replacement_security_group_ids     = null
  reserved_concurrent_executions     = -1
  role                               = data.aws_iam_role.admin_for_lambda.arn
  runtime                            = "python3.12"
  s3_bucket                          = aws_s3_bucket.lambda_bucket.bucket
  s3_key                             = aws_s3_object.lambda_zip.id
  s3_object_version                  = null
  skip_destroy                       = false
  source_code_hash                   = filebase64sha256(data.archive_file.function_archive.output_path)
  tags = {
    "lambda:createdBy" = "SAM"
  }
  tags_all = {
    "lambda:createdBy" = "SAM"
  }
  timeout = 900
  environment {
    variables = {
      DEVICE_DATA = "DeviceData"
    }
  }
  ephemeral_storage {
    size = 512
  }
  logging_config {
    application_log_level = null
    log_format            = "Text"
    log_group             = "${ロググループ名}"
    system_log_level      = null
  }
  tracing_config {
    mode = "PassThrough"
  }
}

```

`variables.tf`
```
variable "AWS_ACCOUNT_ID" {}
```

`lambda_function.py`
```
import boto3
import os
import json
from decimal import Decimal
import base64

dynamoDB = boto3.resource('dynamodb')

def lambda_handler(event, context):
    # print("Received event:", json.dumps(event, indent=2))
    with table.batch_writer(overwrite_by_pkeys=['deviceID', 'createdAt']) as batch:
        for record in event['Records']:
            message_body = record['body']

            try:
                # ↓でデコードする
                decoded_bytes = base64.b64decode(message_body)
                decoded_str = decoded_bytes.decode('utf-8')

                data = json.loads(decoded_str, parse_float=Decimal)
                print(f'{data=}')
            except (base64.binascii.Error, json.JSONDecodeError) as e:
                print(f'Error decoding or parsing message body: {e}')
                continue

            if is_except_data(data['client_id']):
                data = {k.lower(): v for k, v in data.items()}
                data = convert_floats_to_decimals(data)
                try:
                    put_device_data(data, batch)
                except KeyError as e:
                    print(f'KeyError: {e}. Data: {data}')
                    continue

    return {
        'statusCode': 200
    }

def is_except_data(things_name):
    if os.environ.get('APP_ENV', '') == "Staging":
        if 'stg' in things_name:
            return True
        return False
    else:
        if 'stg' in things_name:
            return False
        return True

def put_device_data(data, batch):
    for item in data['data']:
        if 'unix_time' in item:
            createdAt = item['unix_time']
        else:
            raise KeyError('unix_time')

        if len(str(createdAt)) == 10:
            createdAt *= 1000
        data['createdAt'] = createdAt

        data['deviceID'] = data['topic'].split('/')[0]
        data['sensorID'] = data['topic'].split('/')[0] + "-sen"

        item.update({
            'createdAt': createdAt,
            'deviceID': data['deviceID'],
            'sensorID': data['sensorID'],
        })

        print(f'Putting item into DynamoDB: {item}')
        batch.put_item(Item=item)

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

## 実際に配置してみる

1. `aws configure`でAWSを触れるようにする
2. `terraform init` で初期化
3. `terraform plan` でtest
4. `terraform apply` で配置