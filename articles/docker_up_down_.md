---
title: "dockerを起動/停止する際にシェルを組んだ時の備忘録"
emoji: "🐱"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [docker , コンテナ, linux , shell]
published: true
---

## はじめに

仕事で手動で複数のdockerの起動/停止をしていたが
自動で複数のdockerの起動/停止するシェルスクリプトを作った際の備忘録を書きます。

## 実際のコード

```
#!/bin/bash

# 第1引数に up , down , first_set のいずれかを指定します。
# up…必要なdockerを起動します。
# down…upで起動したdockerを停止します。
# first_set…初回必要な設定を実施します。

# 第2引数にIPアドレスを指定します。
# 指定しない場合は停止します。

# 変数指定
ServerIP=$2 #←スペースが入ると期待した結果にならない

# 第2引数がない場合終了
if [ -n "$ServerIP" ] ; then #←""を使わないと期待した結果にならない
    echo -e "\e[31m$1 を実施します。"
else
    echo -e "\e[31m第2引数にIPアドレスを設定してください。"
    exit
fi

###############
# 初回設定手順
###############
if [ $1 = "first_set" ] ; then

    # hosts設定、DNSの代わり(初回のみ)
    echo "127.0.0.1 XYZ.co.jp" >> /etc/hosts

    # 環境変数設定(初回のみ)
    echo "HTTP_PROXY = \"\"" >> .env
    # フォルダ作成とコピー(初回のみ)
    cd setup
    sudo mkdir /usr/local/share/nginx
    sudo cp -p ./nginx/nginx.conf /usr/local/share/nginx/
    sudo cp -rpT ./nginx/ssl /usr/local/share/nginx/ssl
    sudo mkdir /usr/local/share/coredns
    sudo cp -rpT ./coredns  /usr/local/share/coredns/
    cd ..

    echo -e "\e[31m初回設定完了"

####################
# 起動手順
####################
elif [ $1 = "up" ] ; then
    # ソース配置
    cd
    tar xvfJ application-packages-20230929160000.tar.xz
    cd application-packages

    # DB起動＆初期構築処理
    sudo docker compose up db -d
    cd backend/db-create/
    sudo docker image build --no-cache --build-arg ARG_WORKDIR=$PWD --build-arg ARG_PROXY=""  -t db-create:0.1.0 .

    # コンテナ内に入らず起動だけする
    sudo docker run --tty --detach --name db-create_0.1.0 --net network --volume .:$PWD ibsen/db-create:0.1.0 /bin/ash #←detachはバックグラウンドで実行、ttyを入れないとExit(0)になる
    sudo docker exec db-create_0.1.0 npm install #←dockerに入らずホストOSから実行
    sudo docker exec db-create_0.1.0 npm run db:migrate:latest
    sudo docker exec -it db-create_0.1.0 npm run db:seed:run:test

    cd ../..

    # Dockerコンテナをビルドする。
    sudo docker compose build api-server --no-cache
    sudo docker compose build monitor-receiver --no-cache
    sudo docker compose build video-receiver --no-cache
    sudo docker compose build monitor-analyzer --no-cache
    sudo docker compose build video-analyzer --no-cache
    sudo docker compose build video-linker --no-cache
    sudo docker compose build webrtc --no-cache

    # Docker起動
    sudo docker compose up video-analyzer -d
    sudo docker compose up video-linker -d
    sudo docker compose up webrtc -d
    sudo docker compose up monitor-receiver -d
    sudo docker compose up video-receiver -d
    sudo docker compose up api-server -d
    sudo docker compose up nginx -d

    echo -e "\e[31m起動完了"

###############
# 停止手順
###############
elif [ $1 = "down" ] ; then

    cd
    cd application-packages

    # コンテナ→イメージの順で強制削除
    sudo docker rm -f $(docker ps -aq)
    sudo docker rmi -f $(docker images -q)

    #オブジェクトの削除
    sudo docker system prune -a

    #確認
    sudo docker images
    docker ps -a

    # DIR削除
    sudo rm -r /home/ubuntu/application-packages

    echo -e "\e[31m停止完了"
else
  echo "up か down か first_set を第1引数に指定してください。"
fi
```