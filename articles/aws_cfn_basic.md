---
title: "【AWS】CDKで特定Cloud Formationスタックの作成・削除手順まとめ"
emoji: "🍖"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , CloudFormation, CDK , stack , template]
published: true
---

## 1. やったこと（概要）

- CDKプロジェクトで複数のスタック（CloudFormation Stack）を管理している。
- 特定のスタックのみをCloudFormationテンプレートとして出力（`synth`）したり、AWS上から削除（`destroy`）したりしたい場合、**スタック名を指定してコマンドを実行**する。
- スタック名は `bin/levtech.ts` などで `new XxxStack(app, "<StackName>", ...)` の形で定義されている。

---

## 2. スタック名の確認

```sh
npx cdk ls
```
または
```sh
npm run ls:stg
```
などで、現在のSTAGEで有効なスタック名一覧を確認できる。

---

## 3. スタックの作成（テンプレート出力）

### コマンド例

```sh
npx cdk synth <StackName>
```

例:
`<StackName>` というスタックのみテンプレート出力したい場合

```sh
npx cdk synth <StackName>
```

npm scriptを使う場合（`package.json`より）:

```sh
npm run synth:dev <StackName>
```

---

## 4. スタックのデプロイ（実際にAWSへ反映）

> **補足:**
> スタックは `cdk synth` でテンプレートを生成しただけではAWS上に作成・変更されません。
> 実際にAWSへリソースを作成・更新するには `cdk deploy` を実行する必要があります。

### コマンド例

```sh
npx cdk deploy <StackName>
```

npm scriptを使う場合（`package.json`より）:

```sh
npm run deploy:dev <StackName>
```

---

## 5. スタックの削除

### コマンド例

```sh
npx cdk destroy <StackName>
```

例:
`<StackName>` というスタックのみ削除したい場合

```sh
npx cdk destroy <StackName>
```

npm scriptを使う場合（`package.json`より）:

```sh
npm run destroy:dev <StackName>
```

- 削除時は確認プロンプトが出る。`-f` オプションで強制削除も可能。

---

## 6. よく使うnpm script（`package.json`より）

- `npm run synth:dev <StackName>` ... Dev環境でテンプレート出力
- `npm run deploy:dev <StackName>` ... Dev環境でデプロイ（AWSへ反映）
- `npm run destroy:dev <StackName>` ... Dev環境でスタック削除
- `npm run synth:stg <StackName>` ... Stg環境でテンプレート出力
- `npm run deploy:stg <StackName>` ... Stg環境でデプロイ
- `npm run destroy:stg <StackName>` ... Stg環境でスタック削除
- `npm run synth:prd <StackName>` ... Prd環境でテンプレート出力
- `npm run deploy:prd <StackName>` ... Prd環境でデプロイ
- `npm run destroy:prd <StackName>` ... Prd環境でスタック削除

---

## 7. まとめ

- **スタック名を指定して `cdk synth` でテンプレート出力、`cdk deploy` でAWSへ反映、`cdk destroy` で削除ができる。**
- `cdk synth` だけではAWS上にリソースは作成されない。**実際に反映するには `cdk deploy` が必要。**
- npm scriptを活用すると環境変数（STAGE）も自動でセットされるので便利。
- スタック名は `cdk ls` で確認できる。