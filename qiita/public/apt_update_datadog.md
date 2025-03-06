---
title: 【Ubuntu 20.04】apt updateしたらDatadog GPG キーエラーが出る件
tags:
  - Ubuntu
  - apt
  - gpg
  - Datadog
private: false
updated_at: '2025-03-06T18:15:28+09:00'
id: f6e77ad017ad9c784fdb
organization_url_name: null
slide: false
ignorePublish: false
---

Ubuntu システムで Datadog エージェントをインストールまたはアップデートしようとした際に、`apt update` で以下のようなエラーが発生することがあります。

```
Err:6 https://apt.datadoghq.com stable Release.gpg
  The following signatures couldn't be verified because the public key is not available: NO_PUBKEY E6266D4AC0962C7D
W: An error occurred during the signature verification. The repository is not updated and the previous index files will be used. GPG error: https://apt.datadoghq.com stable Release: The following signatures couldn't be verified because the public key is not available: NO_PUBKEY E6266D4AC0962C7D
W: Failed to fetch https://apt.datadoghq.com/dists/stable/Release.gpg  The following signatures couldn't be verified because the public key is not available: NO_PUBKEY E6266D4AC0962C7D
W: Some index files failed to download. They have been ignored, or old ones used instead.
```

このエラーは、Datadog リポジトリの署名を検証するための公開鍵がシステムに存在しない、または古い/破損している場合に発生します。

## 対処法: Datadog リポジトリの公開鍵を設定

1.  **公開鍵のインポート:**
    Datadog の公式ドキュメントに記載されている公開鍵をインポートします。多くの場合、以下のコマンドでインポートできます。

    ```bash
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys E6266D4AC0962C7D
    ```

    *   **重要:** 必ず Datadog の公式ドキュメントを参照し、最新の正しい公開鍵と手順を確認してください。バージョンやディストリビューションによって異なる場合があります。
    * 公開鍵サーバーが利用できないなどの理由で上記コマンドが失敗する場合は、`curl`などでDatadogの公開鍵ファイルをダウンロードし、`apt-key add`で追加する方法を試します（詳細はDatadog公式ドキュメント参照）。

2.  **`apt update` の再実行:**

    ```bash
    sudo apt update
    ```

    エラーが解消され、Datadog リポジトリが正常に更新されることを確認します。

## `apt` によるパッケージのアップグレード

`apt update` でパッケージリストを更新した後、`apt upgrade`  でパッケージをアップグレードできます。

### パッケージが保留 (kept back) される場合

`apt upgrade` を実行しても、一部のパッケージがアップグレードされず、「保留 (kept back)」されることがあります。

```
The following packages have been kept back:
  ...
0 upgraded, 0 newly installed, 0 to remove and X not upgraded.
```

これは、以下の理由が考えられます。

1.  **依存関係の問題:**
    アップグレードによって、他のパッケージとの依存関係が壊れる可能性がある場合など。

2.  **Phased Updates (段階的アップデート):**
    Ubuntu では、安定性のため、一部のアップデートを段階的にリリースすることがあります。

3. **意図的な保留**
    `apt-mark hold`コマンドで意図的に保留状態にしている。

**対処法:**

*   **`apt full-upgrade` を試す:**
    多くの場合、`sudo apt full-upgrade` を実行することで、依存関係の問題が解決され、保留されていたパッケージがアップグレードされます。ただし、システムの安定性に影響を与える可能性もあるため、実行前に変更内容をよく確認してください。

*   **`apt-cache policy <package_name>` で Phased Updates を確認:**
  Phased Updates が原因であれば、通常は待つのが最善です。

* `apt-mark showhold`で意図しない保留がないか確認し、あれば`sudo apt-mark unhold <package_name>`で解除。

*   **個別のパッケージのインストールを試す:**
    `sudo apt-get install <package_name>` で個別にインストールを試み、詳細なエラーメッセージを確認します。

### `apt upgrade` と `apt full-upgrade` の違い

*   **`apt upgrade`:**
    インストール済みのパッケージを新しいバージョンにアップグレードします。ただし、新しいパッケージのインストールや、不要になったパッケージの削除は行いません。

*   **`apt full-upgrade` (または `apt-get dist-upgrade`):**
    `apt upgrade` の機能に加えて、依存関係を解決するために、必要に応じて新しいパッケージのインストールや、不要になったパッケージの削除を行います。より包括的なアップグレード方法です。

### 推奨されるアップグレード手順

1.  **パッケージリストの更新:**
    ```bash
    sudo apt update
    ```

2.  **アップグレードの実行:**
    ```bash
    sudo apt full-upgrade
    ```

## まとめ

Datadog エージェントのインストール/アップデート時の `NO_PUBKEY` エラーは、正しい公開鍵をインポートすることで解決できます。また、`apt` によるパッケージのアップグレードでは、`apt full-upgrade` を使用することで、依存関係の問題や保留されたパッケージに対処できる可能性が高まります。
問題が解決しない場合は、Datadogの公式ドキュメントを参照するか、Ubuntuのコミュニティで質問すると良いでしょう。
