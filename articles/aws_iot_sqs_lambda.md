---
title: "【AWS】Iot Coreで吸い上げたデータを別アカウントのSQSにルーティングする"
emoji: "🗽"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , Iot, SQS , IAM , AWS IoT Core]
published: true
---

## はじめに

Iot Coreで吸い上げたデータをルールエンジンを使用して別アカウントのSQSにルーティングする方法を説明します。

### アーキテクチャ

1. **AWS IoT Core**: デバイスからのメッセージを受信し、ルールエンジンで処理。送信元アカウントになる。
2. **Amazon SQS**: メッセージをキューイングし、異なるアカウントに配信。送信先アカウントになる。

![](https://storage.googleapis.com/zenn-user-upload/3ad723012f2e-20240625.png)

## 実装手順

### 前提条件

- AWS アカウントがある (送信元と送信先)
- AWS CLI の設定が済んでる
- AWS Iot Coreに対応したIoT デバイスがある

### SQS キューの作成

送信先アカウントに Amazon SQS キューを作成します。

```bash
aws sqs create-queue --queue-name MyQueue
```
※SQSのURLを後ほど使うので記録します。

### 送信元アカウントで Amazon SQS キューリソースにアクセスできるようにする

```
aws sqs add-permission \
     --queue-url https://sqs.<送信先アカウントのリージョン>.amazonaws.com/<送信先アカウントID>/MyQueue \
     --label IoTSendMessage \
     --aws-account-ids <送信元アカウントID> \
     --actions SendMessage
```

### クロスアカウント用の IAMロールとIAMポリシーを作成する

1. `iot_policy.json`という以下のファイルを作成する。

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
			"Effect": "Allow",
			"Principal": {
				"Service": "iot.amazonaws.com"
			},
			"Action": "sts:AssumeRole"
		}
	]
}
```

2. 送信元アカウントで以下のコマンドを実行して`iot-cross-sqs-allow`というIAMロールを作る

```
aws iam create-role \
     --role-name iot-cross-sqs-allow \
     --assume-role-policy-document file://iot_policy.json
```

3. 以下の様なログが出力されればOK

```
{
    "Role": {
        "Path": "/",
        "RoleName": "iot-cross-sqs-allow",
        "RoleId": "XXXXXXXXXXXXXXXXXXXXX",
        "Arn": "arn:aws:iam::XXXXXXXXXXXX:role/iot-cross-sqs-allow",
        "CreateDate": "2022-09-07T05:05:58+00:00",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
				{
					"Effect": "Allow",
					"Principal": {
						"Service": "iot.amazonaws.com"
					},
					"Action": "sts:AssumeRole"
				}
			]
		}
    }
}
```

4. `allow_send_cross_sqs.json` という名前のファイルを作成

```
{
    "Version": "2012-10-17",
    "Statement": [
		{
			"Effect": "Allow",
			"Action": "sqs:SendMessage",
			"Resource": "arn:aws:sqs:<送信先アカウントのリージョン>:<送信先アカウントID>:iot-data"
		}
	]
}
```

5. 2で作ったロールにポリシーをアタッチする

```
aws iam put-role-policy \
     --role-name iot-cross-sqs-allow \
     --policy-name new-iot-cross-sqs-policy \
     --policy-document file://allow_send_cross_sqs.json
```

### エラーの再送信を許可する AWS IAM ロールとポリシーを作成

1. 送信元に`iot-republish` という新しいロールを作成
※iot_policy.jsonを再利用します。

```
aws iam create-role \
     --role-name iot-republish \
     --assume-role-policy-document file://iot_policy.json
```

2. 以下の様なログが出力されればOK

```
{
    "Role": {
        "Path": "/",
        "RoleName": "iot-cross-sqs-allow",
        "RoleId": "XXXXXXXXXXXXXXXXXXXXX",
        "Arn": "arn:aws:iam::XXXXXXXXXXXX:role/iot-cross-sqs-allow",
        "CreateDate": "2022-09-07T05:05:58+00:00",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
				{
					"Effect": "Allow",
					"Principal": {
						"Service": "iot.amazonaws.com"
					},
					"Action": "sts:AssumeRole"
				}
			]
		}
    }
}
```

3. `allow_republish.json` という名前のファイルを作成

```
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "iot:Publish",
        "Resource": "arn:aws:iot:<取り込み用アカウントのリージョン>:<取り込み用アカウントID>:errors/*"
    }
}
```

4. ポリシーを `iot-republish` ロールに追加

```
aws iam put-role-policy \
     --role-name iot-republish \
     --policy-name iot-republish \
     --policy-document file://allow_republish.json
```

### 送信元アカウントでメッセージを評価し、エラーを再送信するIoT ルールを作成

1. `ingestion_rule.json`を作成

```
{
"sql": "SELECT * FROM 'data/private'" ,
"description": "Cross-account publishing of messages to SQS.",
"ruleDisabled": false,
"awsIotSqlVersion": "2016-03-23",
"actions": [{
	"sqs": {
		"roleArn": "<iot-cross-sqs-allow ロールのARN>",
		"queueUrl": "https://sqs.<データ用アカウントのリージョン>.amazonaws.com/<データ用アカウントID>/iot-data",
		"useBase64": true
	}
}],
"errorAction": {
    "republish": {
      "roleArn": "<iot-republish ロールのARN>",
      "topic": "error/rules",
      "qos": 0
    }
  }
}
```

2. 送信元アカウントに送信先アカウントの SQS にメッセージを送信するための IoT ルールを作成

```
aws iot create-topic-rule \
     --rule-name "cross_account_sqs_publish" \
     --topic-rule-payload file://ingestion_rule.json
```

## 参考
https://aws.amazon.com/jp/blogs/news/route-messages-across-multiple-accounts-with-aws-iot-core-and-amazon-sqs/