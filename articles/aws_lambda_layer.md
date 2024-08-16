---
title: "【AWS】Lambdaレイヤーの作成とアップロード手順(python)"
emoji: "✂️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , lambda, Lambdaレイヤー , cloud9 . python]
published: true
---

AWS Lambdaで`pymysql`コマンドを使用するために、Lambdaレイヤーを作成し、ローカルのWindows端末にダウンロードしてからAWSコンソールでアップロードする手順を解説します。

## Cloud9の立ち上げ

- AWSコンソールでCloud9を選択し、新しい環境を作成します。
- 作成が完了したら環境を開きます。

## Pyenvのインストール

次のコマンドでpyenvをインストールします。
```bash
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
```

## Pyenvのパス設定

~/.bashrcにpyenvのパスを追加し、シェルに反映させます。
```bash
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
```
## Pythonのインストール

必要なPythonのバージョン（例では3.11.0）をインストールし、グローバルに設定します。
```bash
pyenv install 3.11.0
pyenv global 3.11.0
```

## Pythonのバージョン確認

正しくインストールされていることを確認します。
```bash
python3 --version
```

## 必要ライブラリのインストール

pymysqlなどの必要なライブラリをインストールし、そのディレクトリを作成します。
```bash
mkdir python && cd $_
pip install pymysql -t .
```

## Lambdaレイヤー用のZIPファイル作成

インストールしたライブラリを含めたディレクトリをZIPファイルに圧縮します。
ZIPファイルをローカルにダウンロードします。

## Lambdaコンソールからレイヤーのアップロード
- AWS Lambdaコンソールに移動し、新しいレイヤーを作成します。
- ダウンロードしたZIPファイルをアップロードし、レイヤーを完成させます。

これでpymysqlがlambdaで使えるようになります。