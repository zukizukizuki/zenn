---
title: "【2024年最新】EC2にSSM agentをinstallしてAWSコンソールからアクセス"
emoji: "🎢"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [AWS , EC2, terraform , Cloud]
published: true
---

## 概要
[公式の手順](https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/agent-install-al2.html)で SSM agentをinstallしてもフリートマネージャーから認識されないのでひと手間加える必要がある

## 前提
- OSはAmazon linux
- セキュリティグループは
  - インバウンド: SSHアクセスするIPからSSH許可
  - アウトバウンド: 全て許可

## 手順

1. EC2 に SSH 接続
```
ssh -i ${秘密鍵のパス} ec2-user@${public IP}
```

2. [公式の手順](https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/agent-install-al2.html)で SSM agent install

### x86_64

```
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
```
### ARM64

```
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_arm64/amazon-ssm-agent.rpm
```

3. EC2 に 割り当てるIAMロールを作成するIAMコンソールで以下のロールを作成する

| **項目** | **値** |
| ---- | ---- |
| 信頼されたエンティティタイプ | AWS のサービス |
| ユースケース | EC2 Role for AWS Systems Manager |
| 許可ポリシー | AmazonSSMManagedInstanceCore |
| ロール名 | ${任意のロール名} |


4. EC2 に作成したロールを割り当てる

```
1. EC2サービスに移動します。
2. 左側のメニューから「インスタンス」を選択します。
3. 確認したいEC2インスタンスを選択します。
4. 下部のペインで「セキュリティ」タブを選択します。
5. 「IAMロール」の項目を確認します。ここに割り当てられているロールの名前が表示されます。
```

5. SSM フリートマネージャーからアクセス出来る事を確認する

## 参考
公式の別のところに書いてあった
https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/setup-instance-permissions.html