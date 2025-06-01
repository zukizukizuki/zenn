---
title: '[postgres]docker内のDBをバックアップ・リストアする'
private: false
tags:
  - docker
  - postgres
  - DB
  - コンテナ
updated_at: '2025-06-01T01:52:55.662Z'
id: null
organization_url_name: null
slide: false
---

## 全DBをbackup

```
sudo docker compose exec ${dockerのホスト名} pg_dumpall --clean --username ${user名} > /tmp/${ファイル名}.sql
```

## 特定のDBのみbackup

```
sudo docker compose exec ${dockerのホスト名} pg_dump ${DB名} --username ${user名} > /tmp/${ファイル名}.sql
```

## restore
```
sudo cat /tmp/${ファイル名}.sql | docker-compose exec -T ${dockerのホスト名} psql --username ${user名}
```