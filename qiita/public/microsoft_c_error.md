---
title: 【解決方法】Microsoft Visual C++ で "Assertion failed!" エラーが発生した場合
private: false
tags:
  - Microsoft
  - C++
  - Adobe
updated_at: '2025-06-01T01:53:04.918Z'
id: null
organization_url_name: null
slide: false
---

最近、PC上で **"Assertion failed!"** エラーが発生して困っていました。このエラーの原因が **Microsoft Visual C++** や **Adobe Creative Cloud Experience** に関連していることが判明し、以下の手順で解決しました。
同じエラーで悩んでいる方の参考になれば幸いです。

## 前提

- **OS:** Windows 11 (バージョン: 23H2)
- **CPU:** Intel Core i7-12700 (12コア20スレッド)
- **GPU:** NVIDIA GeForce RTX 3060
- **メモリ:** 48GB (増設済)

## 発生したエラーの詳細

以下のエラーが表示されました。

- **エラーメッセージ:**
  `Assertion failed!`
  **Program:**
  C:\node-vulcanjs\build\Release\VulcanMessageLib.node
  **File:**
  C:\bld\workspace\CCX-Process#release...\vulcanadapter.cc
  **Line:** 390

このエラーは **Microsoft Visual C++** や **node-vulcanjs** に関連していることが示唆されており、原因究明を進めました。

## 解決の糸口: 問題のファイルを特定した方法

エラーに関連するファイルの位置を突き止めるため、以下のコマンドを実行しました。

```
Get-ChildItem -Path C:\ -Recurse -ErrorAction SilentlyContinue -Filter "node-vulcanjs"
```

このコマンドにより、関連ファイルが以下のディレクトリに存在していることを特定しました。

```
ディレクトリ: C:\Program Files\Adobe\Adobe Creative Cloud Experience\js\node_modules
```

この結果、問題が **Adobe Creative Cloud Experience** に関連している可能性が高いことが判明しました。

## 試したけれど効果がなかった方法

以下の手順を試しましたが、今回のケースでは解決に至りませんでした。

1. **Vulkan ライブラリの再インストール**
   - Vulkan SDK を公式サイトから再インストールしましたが、エラーは解消されませんでした。

2. **グラフィックドライバの更新**
   - NVIDIA の公式サイトから最新ドライバをダウンロードして更新しましたが、同様に効果なし。

3. **Microsoft Visual C++ 再頒布可能パッケージの再インストール**
   - x86 と x64 の両方を再インストールしましたが、エラーが継続。

4. **環境変数の確認**
   - Vulkan SDK に関連する環境変数が正しいことを確認しましたが、問題ありませんでした。

5. **関連アプリケーションのアップデート**
   - Node.js プロジェクトなど、関連アプリを確認しようとしましたが、最終的に **Adobe Creative Cloud Experience** に起因していることが判明。

## 問題解決の手順

以下の手順を実施した結果、エラーが解消されました。

### **手順 1: Adobe Creative Cloud Experience のアンインストール**

1. **コントロールパネルを開く**
   - Windowsの検索バーで「**コントロールパネル**」と入力し、開きます。

2. **プログラムのアンインストール**
   - 「**プログラムのアンインストール**」をクリックします。

3. **Adobe Creative Cloud を探す**
   - プログラム一覧から「**Adobe Creative Cloud**」または「Adobe Creative Cloud Experience」を選択し、「**アンインストール**」をクリックします。

4. **画面の指示に従ってアンインストール**
   - 指示に従い、アンインストールを完了させます。

### **手順 2: 残存ファイルの削除 (必要に応じて)**

1. **以下のディレクトリを確認し、残存ファイルを削除します:**
   - **C:\Program Files\Adobe\**
   - **C:\Program Files (x86)\Adobe\**
   - **C:\Users\<ユーザー名>\AppData\Local\Adobe**
   - **C:\Users\<ユーザー名>\AppData\Roaming\Adobe**

2. **レジストリのクリーンアップ (必要に応じて)**
   - レジストリエディタ (regedit) を開き、以下のキーを確認して削除:
     - `HKEY_CURRENT_USER\Software\Adobe`
     - `HKEY_LOCAL_MACHINE\Software\Adobe`

### **手順 3: 再起動**

- アンインストールとファイルの削除後に PC を再起動しました。

## 結果

上記の手順を実施した後、問題の **"Microsoft Visual C++ Assertion failed!"** エラーが発生しなくなりました。

## 注意点

もしこの手順で解決しない場合は、以下を試すことをおすすめします。

1. **Adobe Creative Cloud Cleaner Tool を使用**
   - [Adobe公式のクリーンアップツール](https://helpx.adobe.com/creative-cloud/kb/cc-cleaner-tool-installation-problems.html) を使用して不要なコンポーネントを削除します。

2. **関連するソフトウェアやドライバの再確認**
   - 他の関連アプリやドライバに問題がないか確認します。

## まとめ

**"Microsoft Visual C++ Assertion failed!"** エラーの解消には、**Adobe Creative Cloud Experience** のアンインストールが有効でした。
また Adobeのコミュニティで[同様の事象について議論されていました](https://community.adobe.com/t5/creative-cloud%E3%81%AE%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89%E3%81%A8%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB-discussions/%E6%95%B0%E6%97%A5%E5%89%8D%E3%81%8B%E3%82%89%E5%87%BA%E3%81%A6%E3%81%8F%E3%82%8B%E6%A7%98%E3%81%AB%E3%81%AA%E3%82%8A%E3%81%BE%E3%81%97%E3%81%9F/td-p/11879193?profile.language=ja)。

同じエラーで悩んでいる方の参考になれば幸いです。
