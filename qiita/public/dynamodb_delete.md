---
title: DynamoDBデータ削除における問題解決パターン (Lambda + Scan + FilterExpression + Delete)
private: false
tags:
  - aws
  - DynamoDB
  - NoSQL
  - lambda
  - python
updated_at: '2025-06-01T01:52:57.163Z'
id: null
organization_url_name: null
slide: false
---

今後、DynamoDBの特定の条件に合致するデータを削除する際に役立つ、Markdown形式の手順書です。このドキュメントでは、**Lambda関数**と `Scan + FilterExpression + Delete` パターンを組み合わせることで、効率的かつ安全にデータを削除する方法について解説します。

**シナリオ:**

DynamoDBテーブルから、特定のunix_time以前の古いデータを定期的に削除したい。

**解決策:**

Lambda関数と `Scan + FilterExpression + Delete` パターンを組み合わせます。Lambda関数を使用することで、自動化されたスケジュールされた方法で削除プロセスを実行できます。

1.  **Lambda関数の作成:** AWS Lambda コンソールで、Python ランタイムを使用して新しい関数を作成します。
2.  **権限設定:**  Lambda関数に、DynamoDBテーブルに対する `dynamodb:Scan` および `dynamodb:DeleteItem` 権限を持つIAM Roleを付与します。
3.  **コード実装:** Lambda関数内に、テーブルをスキャンし、条件に合致するアイテムを特定して削除するコードを実装します。 (下記参照)
4.  **トリガー設定:** CloudWatch Events (EventBridge) を使用して、Lambda関数を定期的に実行するようにスケジュールします。

**手順:**

### 1. 準備

*   **IAM Role の設定:**
    このLambda関数を実行するためのIAM Roleを作成または選択し、以下の権限を付与します。

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:Scan",
                    "dynamodb:DeleteItem"
                ],
                "Resource": "arn:aws:dynamodb:YOUR_REGION:YOUR_ACCOUNT_ID:table/YourTableName"
            }
        ]
    }
    ```

    *   `YOUR_REGION` と `YOUR_ACCOUNT_ID` を適切な値に置き換えます。
    *   `YourTableName` は、実際のテーブル名に置き換えます。

*   **テーブル情報の確認:**
    削除対象の DynamoDB テーブルのテーブル名、パーティションキー名、およびソートキー名を確認します。

### 2. Lambda関数のコード

```python
import boto3
import os
from datetime import datetime, timezone

def lambda_handler(event, context):
    """
    DynamoDBテーブルからcreatedAtが指定された閾値以下のすべてのアイテムを削除するLambda関数。
    """
    TABLE_NAME = os.environ['TABLE_NAME']  # 環境変数からテーブル名を取得
    CUTOFF_TIMESTAMP_MS = int(os.environ['CUTOFF_TIMESTAMP_MS'])  # 環境変数から閾値を取得

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)

    scan_kwargs = {
        'FilterExpression': boto3.dynamodb.conditions.Attr('createdAt').lt(CUTOFF_TIMESTAMP_MS)
    }

    try:
        item_count = 0
        while True:
            response = table.scan(**scan_kwargs)
            for item in response['Items']:
                try:
                    # プライマリキーの構成に合わせて修正
                    table.delete_item(Key={'partitionKeyName': item['partitionKeyName'], 'sortKeyName': item['sortKeyName']})
                    item_count += 1
                    print(f"Deleted item: partitionKeyName={item['partitionKeyName']}, sortKeyName={item['sortKeyName']}")
                except Exception as e:
                    print(f"Error deleting item: {e}")

            if 'LastEvaluatedKey' not in response:
                break
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

        print(f"Total items deleted: {item_count}")
        return {
            'statusCode': 200,
            'body': f"Successfully deleted {item_count} items."
        }

    except Exception as e:
        print(f"Scan operation failed: {e}")
        return {
            'statusCode': 500,
            'body': f"Error: {e}"
        }
```

### 3. Lambda関数の設定

*   **環境変数:**
    Lambda関数の設定で、以下の環境変数を設定します。

    *   `TABLE_NAME`: DynamoDBテーブル名
    *   `CUTOFF_TIMESTAMP_MS`: 削除したい `createdAt` の閾値（ミリ秒単位のUnixタイムスタンプ）

*   **タイムアウト:**
    Lambda関数のタイムアウト値を、削除処理が完了するのに十分な時間に設定します。 テーブルのサイズによっては、タイムアウト値を大きくする必要があるかもしれません。 (デフォルトは3秒ですが、テーブルサイズに応じて増やしてください。最大15分まで設定可能です。)

*   **メモリ:**
    Lambda関数のメモリ割り当てを、削除処理に必要な量に設定します。

### 4. 実行と監視

*   **Lambda関数の実行:**
    **テスト**からLambda関数を実行します。
*   **CloudWatch Logs の監視:**
    Lambda関数の実行ログは、CloudWatch Logs に記録されます。 ログを監視することで、関数の実行状況やエラーを確認できます。

### 5. スクリプトの修正 (必要に応じて)

必要に応じて、Lambda関数内のコードを修正します。特に、以下の点に注意してください。

*   **テーブル名の修正:**
    `TABLE_NAME` 環境変数が、削除対象の実際のテーブル名に設定されていることを確認します。

*   **削除条件の修正:**
    `CUTOFF_TIMESTAMP_MS` 環境変数が、削除したいデータに合致する値であることを確認してください。

*   **プライマリキーの修正:**
    `table.delete_item(Key={'partitionKeyName': item['partitionKeyName'], 'sortKeyName': item['sortKeyName']})` の部分を、テーブルの実際のプライマリキー構成に合わせて修正します。
    複合キーの場合は、パーティションキーとソートキーの両方を指定する必要があります。

### 重要な注意点:

*   **バックアップ:** 削除操作の前に、必ずテーブルのバックアップを作成してください。
*   **スロットリング:** DynamoDBのスロットリング制限に注意してください。
*   **コスト:** スキャン操作はテーブル全体を読み込むため、テーブルが大きい場合はコストがかかる可能性があります。
*   **環境変数:** コード内にハードコードされた値を使用せず、環境変数を使用することを推奨します。
