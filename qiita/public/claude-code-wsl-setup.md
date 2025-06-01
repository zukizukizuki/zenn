---
title: Windows環境でWSLを使ってClaude Codeを快適に動かす方法
private: false
tags:
  - wsl
  - claude
  - ai
  - windows
  - setup
updated_at: '2025-06-01T01:52:51.560Z'
id: null
organization_url_name: null
slide: false
---

## はじめに

Windows環境でAI開発ツールのClaude Codeを使用する際、WSL（Windows Subsystem for Linux）を活用することで、より快適で安定した開発環境を構築できます。この記事では、WSLの導入からClaude Codeの設定まで、具体的な手順を解説します。

## WSLとは

WSL（Windows Subsystem for Linux）は、Windows上でLinux環境を実行できる機能です。Claude CodeはLinux環境での動作が最適化されているため、WindowsでWSLを使用することで以下のメリットが得られます：

- **安定したLinux環境での実行**
- **豊富なLinuxツールの活用**
- **パフォーマンスの向上**
- **開発ワークフローの統一**

## 必要な環境

- Windows 10 version 2004以降、またはWindows 11
- 管理者権限でのコマンド実行が可能
- インターネット接続

## Step 1: WSLの有効化とインストール

### 1.1 WSLの有効化

PowerShellを管理者権限で実行し、以下のコマンドを実行します：

```powershell
wsl --install
```

このコマンドにより、WSL機能が有効化され、デフォルトでUbuntuがインストールされます。

### 1.2 再起動

インストール完了後、システムを再起動します。

### 1.3 Ubuntuの初期設定

再起動後、Ubuntuが自動で起動するので、以下の設定を行います：

```bash
# ユーザー名とパスワードの設定
# プロンプトに従って入力

# システムの更新
sudo apt update && sudo apt upgrade -y
```

## Step 2: Node.jsの環境構築

Claude CodeはNode.js環境で動作するため、NVMを使用してNode.jsをインストールします。

### 2.1 NVMのインストール

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
```

### 2.2 シェルの再読み込み

```bash
source ~/.bashrc
```

### 2.3 Node.jsのインストール

```bash
# LTS版のNode.jsをインストール
nvm install --lts
nvm use --lts

# バージョン確認
node --version
npm --version
```

## Step 3: Claude Codeのインストールと設定

### 3.1 Claude Codeのインストール

```bash
npm install -g @anthropic-ai/claude-code
```

### 3.2 初回起動と設定

```bash
# Claude Codeの起動
claude

# 初回起動時に表示される設定ダイアログに従って設定を完了
```

## Step 4: Windowsとの連携設定

### 4.1 ファイルシステムの理解

WSL内からWindowsのファイルシステムにアクセスする方法：

```bash
# Cドライブへのアクセス
cd /mnt/c/

# ユーザーのDocumentsフォルダへのアクセス
cd /mnt/c/Users/[ユーザー名]/Documents/
```

### 4.2 プロジェクトディレクトリの推奨配置

パフォーマンスを考慮した推奨配置：

```bash
# WSLのホームディレクトリ内（推奨）
~/projects/

# Windowsとの共有が必要な場合
/mnt/c/Users/[ユーザー名]/Documents/projects/
```

## Step 5: 開発環境の最適化

### 5.1 Git設定

```bash
# Gitの基本設定
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Windows Credential Managerとの連携
git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"
```

### 5.2 VS Codeとの連携

VS CodeでWSLを使用する場合：

```bash
# WSL拡張機能のインストール（VS Code側で実行）
# Remote - WSL拡張機能をインストール

# WSLからVS Codeを起動
code .
```

### 5.3 便利なエイリアスの設定

```bash
# .bashrcに追加
echo 'alias ll="ls -alF"' >> ~/.bashrc
echo 'alias la="ls -A"' >> ~/.bashrc
echo 'alias l="ls -CF"' >> ~/.bashrc
echo 'alias cc="claude"' >> ~/.bashrc
source ~/.bashrc
```

## トラブルシューティング

### WSLが起動しない場合

```powershell
# WSLのバージョン確認
wsl --list --verbose

# WSLの再起動
wsl --shutdown
wsl
```

### Claude Codeが正常に動作しない場合

```bash
# Node.jsのバージョン確認
node --version

# Claude Codeの再インストール
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code
```

### パフォーマンスが悪い場合

- プロジェクトファイルをWSL内（`~/`以下）に配置
- Windows Defenderの除外設定でWSLディレクトリを指定
- WSL2を使用していることを確認

## まとめ

WSLを使用することで、Windows環境でもLinux特有の安定性とパフォーマンスを享受しながらClaude Codeを実行できます。特に以下のポイントが重要です：

1. **WSL2の使用を推奨**
2. **プロジェクトファイルはWSL内に配置**
3. **適切なNode.js環境の構築**
4. **WindowsツールとのスムーズなThursday**

この設定により、Windows環境でも快適なAI開発体験が得られるでしょう。

## 参考資料

- [WSL公式ドキュメント](https://docs.microsoft.com/ja-jp/windows/wsl/)
- [Claude Code公式ドキュメント](https://docs.anthropic.com/claude/docs/claude-code)
- [NVM公式リポジトリ](https://github.com/nvm-sh/nvm)