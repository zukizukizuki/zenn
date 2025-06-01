---
title: Windows端末でDistrolessイメージを使用してDockerを起動する方法
private: false
tags:
  - docker
  - distroless
  - セキュリティ
  - コンテナ
updated_at: '2025-06-01T01:52:54.637Z'
id: null
organization_url_name: null
slide: false
---

## 前提条件

1. Windows 10 Pro、Enterprise、または Education（64ビット版）
2. Docker Desktop for Windowsがインストールされていること

## 基本的な手順

1. Docker Desktopを起動する
   - タスクバーのDocker Desktop アイコンをクリックする、または
   - スタートメニューからDocker Desktopを検索して起動する

2. PowerShellを管理者権限で開く
   - スタートメニューを右クリック
   - 「Windows PowerShell (管理者)」を選択

3. Chainguard社が提供する Wolfi イメージをプルする

```powershell
docker pull cgr.dev/chainguard/wolfi-base:latest
```

4. Wolfiイメージを使用してコンテナを起動する

```powershell
docker run -it --rm cgr.dev/chainguard/wolfi-base:latest
```

5. コンテナ内でコマンドを実行する

6. コンテナを終了する

Ctrl + D を押すか、exit コマンドを実行する


## 補足

Chainguard社が提供するstaticイメージで同様の事を実施します。

```powershell
docker pull cgr.dev/chainguard/static:latest
```

Chainguardの static イメージを単純に実行しようとすると、以下のようなエラーが発生します

```
docker: Error response from daemon: No command specified.
See 'docker run --help'.
```

これは、static イメージが実行するデフォルトのコマンドを持たないために発生します。
このイメージは主に他のイメージのベースとして、または静的ファイルの配布用に設計されているためです。
対話的な使用には、chainguard社が提供する wolfi イメージなど、より多くのツールを含むイメージを使用できます。

## 結論

- Chainguard Distrolessイメージ（特に static イメージ）は極めて最小限の構成のため、ほとんどの一般的なLinuxコマンドやツールは含まれていません。
- これらのイメージは主にアプリケーションの実行環境として設計されており、対話的な使用には適していません。
- 実際の使用では、このイメージをベースにしてアプリケーションを含むカスタムイメージを作成することが一般的です。
- Chainguardは複数のDistrolessイメージを提供しています。
- 特定のアプリケーションやランタイムに適したイメージを選択することができます。
