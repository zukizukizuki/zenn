---
title: "【AWS】Lambdaレイヤーの作成とアップロード手順"
emoji: "✂️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , lambda, Lambdaレイヤー , EC2]
published: true
---

AWS Lambdaで`mysqldump`コマンドを使用するために、Lambdaレイヤーを作成し、ローカルのWindows端末にダウンロードしてからAWSコンソールでアップロードする手順を解説します。

## EC2インスタンスでのLambdaレイヤーの作成

まず、必要なライブラリを含むLambdaレイヤーをEC2インスタンス上で作成します。

### 必要なディレクトリの作成

```bash
mkdir -p lambda-layer/lib
```
### 依存ファイルの調査
mysqldumpコマンドが依存しているライブラリを調べるためには、lddコマンドを使用します。以下のように実行します。

```bash
ldd /usr/bin/mysqldump
```

実行結果には、mysqldumpが依存しているライブラリが一覧表示されます。例えば、以下のような出力が得られます。

```bash
linux-vdso.so.1 (0x00007ffe347fb000)
libssl.so.3 => /lib64/libssl.so.3 (0x00007f025a2b1000)
libcrypto.so.3 => /lib64/libcrypto.so.3 (0x00007f0259e00000)
libresolv.so.2 => /lib64/libresolv.so.2 (0x00007f025a29d000)
libm.so.6 => /lib64/libm.so.6 (0x00007f0259d25000)
libstdc++.so.6 => /lib64/libstdc++.so.6 (0x00007f0259a00000)
libgcc_s.so.1 => /lib64/libgcc_s.so.1 (0x00007f025a283000)
libc.so.6 => /lib64/libc.so.6 (0x00007f0259600000)
libz.so.1 => /lib64/libz.so.1 (0x00007f025a267000)
```

### 依存ライブラリのコピー
調べた依存ライブラリをlambda-layer/lib/ディレクトリにコピーします。以下のコマンドを実行します。

```bash
cp /lib64/libssl.so.3 lambda-layer/lib/
cp /lib64/libcrypto.so.3 lambda-layer/lib/
cp /lib64/libresolv.so.2 lambda-layer/lib/
cp /lib64/libm.so.6 lambda-layer/lib/
cp /lib64/libstdc++.so.6 lambda-layer/lib/
cp /lib64/libgcc_s.so.1 lambda-layer/lib/
cp /lib64/libc.so.6 lambda-layer/lib/
cp /lib64/libz.so.1 lambda-layer/lib/
cp /lib64/ld-linux-x86-64.so.2 lambda-layer/lib/
```

### LambdaレイヤーのZIPファイルを作成
依存ファイルを含むディレクトリの準備ができたら、以下のコマンドでZIPファイルを作成します。

```bash
cd lambda-layer
zip -r ../mysqldump-layer.zip .
```

## Lambdaレイヤーのダウンロード
次に、作成したZIPファイルをローカルのWindows端末にダウンロードします。以下のscpコマンドを使用します。
※windows端末です

```
scp -i C:\\Users\\user\\Documents\\aws\\XXX.pem ec2-user@xxx.xxx.xxx.xxx:/home/ec2-user/mysqldump-layer.zip C:\\Users\\user\\Documents\\aws
```

コマンドの各部分の説明：

- -i オプションは、SSH接続に使用する秘密鍵のファイルパスを指定します。
- ec2-user@xxx.xxx.xxx.xxx は、EC2インスタンスのユーザー名とIPアドレスです。
- /home/ec2-user/mysqldump-layer.zip は、EC2インスタンス上のファイルのパスです。
- C:\\Users\\user\\Documents\\aws は、ローカル端末上のダウンロード先のパスです。

## AWSコンソールでのレイヤーのアップロード
ダウンロードしたZIPファイルをAWSコンソールにアップロードしてLambdaレイヤーとして使用します。

### アップロード手順
1. AWS Management Consoleにログインします。
2. 「Lambda」サービスに移動します。
3. 左側のメニューから「レイヤー」を選択し、「レイヤーを作成」をクリックします。
4. 「名前」フィールドにレイヤー名を入力し、「アップロード」オプションを選択して、ダウンロードしたZIPファイルを選択します。
5. 「作成」をクリックしてレイヤーを作成します。

## 結論
これで、Lambda関数でmysqldumpを使用できるようになります。
