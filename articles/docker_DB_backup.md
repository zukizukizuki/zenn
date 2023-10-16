---
title: "[postgres]docker内のDBをバックアップ・リストアする"
emoji: "🦍"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [docker , postgres, DB , コンテナ]
published: true
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
