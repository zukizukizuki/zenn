---
title: Ubuntu でローカルのDBをpgAdminで参照する方法
private: false
tags:
  - linux
  - ubuntu
  - postgres
  - pgAdmin
updated_at: '2025-06-01T01:53:09.983Z'
id: null
organization_url_name: null
slide: false
---

## 概要
postgres をGUIで扱えるツールであるpgAdminでローカルにあるDBを参照する方法を記載します。

## 手順

1. pgAdmin の install の為に以下のコマンドを実行

```
sudo apt install curl
sudo curl https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo apt-key add
sudo sh -c 'echo "deb https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list'
sudo apt update
sudo apt install pgadmin4
sudo /usr/pgadmin4/bin/setup-web.sh
```

2. ログイン用の `Email address` , `Password` を入力する

3. ポート80を8080に変更し443の設定を無効にする。
`sudo vi /etc/apache2/ports.conf`

```
#Listen 80
Listen 8080
#<IfModule ssl_module>
#       Listen 443
#</IfModule>
#<IfModule mod_gnutls.c>
#       Listen 443
#</IfModule
```

4. apacheの再起動
`sudo systemctl restart apache2`

5. ブラウザで以下を開く
http://127.0.0.1:8080/pgadmin4/browser/

6. 2で設定したEmailとPasswordでログイン
