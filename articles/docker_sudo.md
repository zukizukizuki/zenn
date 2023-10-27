---
title: "dockerコマンドのsudoを省略する"
emoji: "🐷"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [docker , コンテナ, linux , shell , sudo]
published: true
---

## 概要
dockerコマンドでいちいちsudoするのがだるいので省略する

## 手順

1. sudo 特権のあるユーザでログインします。

2. docker グループを作成し、ユーザを追加します。
$ sudo usermod -aG docker ubuntu

3. PCを再起動するとsudoを使わなくてもdockerコマンドが使える。

## 参考
https://docs.docker.jp/v1.12/engine/installation/linux/centos.html#:~:text=docker%20%E3%82%B0%E3%83%AB%E3%83%BC%E3%83%97%E3%81%AE%E4%BD%9C%E6%88%90,-docker%20%E3%83%87%E3%83%BC%E3%83%A2%E3%83%B3%E3%81%AF&text=docker%20%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89%E5%88%A9%E7%94%A8%E6%99%82%E3%81%AB%20sudo,%E3%81%8C%E5%8F%AF%E8%83%BD%E3%81%AB%E3%81%AA%E3%82%8A%E3%81%BE%E3%81%99%E3%80%82