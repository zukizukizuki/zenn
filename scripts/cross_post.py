#!/usr/bin/env python3
"""
Zennの記事を他のプラットフォーム（Qiita、WordPress）に自動投稿するスクリプト
使用方法: python cross_post.py <markdown_file_path>
"""

import os
import sys
import re
import json
import requests
import yaml
import markdown
from pathlib import Path

# 設定ファイルのパス
CONFIG_PATH = Path.home() / ".cross_post_config.json"

def load_config():
    """設定ファイルを読み込む"""
    if not CONFIG_PATH.exists():
        # 設定ファイルがない場合は作成
        config = {
            "qiita": {
                "access_token": "",
                "enabled": False
            },
            "wordpress": {
                "url": "",
                "username": "",
                "password": "",
                "enabled": False
            }
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"設定ファイルを作成しました: {CONFIG_PATH}")
        print("APIキーなどの情報を設定ファイルに追加してください。")
        sys.exit(1)
    
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def parse_markdown(file_path):
    """マークダウンファイルを解析してフロントマターとコンテンツを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # フロントマターを抽出
    frontmatter_match = re.match(r'---\n(.*?)\n---\n', content, re.DOTALL)
    if not frontmatter_match:
        print("フロントマターが見つかりません。")
        sys.exit(1)
    
    frontmatter_yaml = frontmatter_match.group(1)
    frontmatter = yaml.safe_load(frontmatter_yaml)
    
    # 本文を抽出
    body = content[frontmatter_match.end():]
    
    return frontmatter, body

def post_to_qiita(frontmatter, body, config):
    """Qiitaに投稿"""
    if not config["qiita"]["enabled"]:
        print("Qiitaへの投稿は無効になっています。")
        return
    
    access_token = config["qiita"]["access_token"]
    if not access_token:
        print("Qiita APIトークンが設定されていません。")
        return
    
    # Qiita APIのエンドポイント
    url = "https://qiita.com/api/v2/items"
    
    # タグを準備
    tags = [{"name": tag} for tag in frontmatter.get("topics", [])]
    
    # 投稿データを準備
    data = {
        "title": frontmatter["title"],
        "body": body,
        "private": False,
        "tags": tags
    }
    
    # ヘッダーを準備
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 投稿リクエスト
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 201:
        print(f"Qiitaへの投稿が成功しました: {response.json()['url']}")
    else:
        print(f"Qiitaへの投稿が失敗しました: {response.status_code}")
        print(response.text)

def post_to_wordpress(frontmatter, body, config):
    """WordPressに投稿"""
    if not config["wordpress"]["enabled"]:
        print("WordPressへの投稿は無効になっています。")
        return
    
    wp_url = config["wordpress"]["url"]
    username = config["wordpress"]["username"]
    password = config["wordpress"]["password"]
    
    if not all([wp_url, username, password]):
        print("WordPress設定が不完全です。")
        return
    
    # WordPressのREST APIエンドポイント
    api_url = f"{wp_url}/wp-json/wp/v2/posts"
    
    # マークダウンをHTMLに変換
    html_content = markdown.markdown(body)
    
    # 投稿データを準備
    data = {
        "title": frontmatter["title"],
        "content": html_content,
        "status": "publish"
    }
    
    # 認証情報
    auth = (username, password)
    
    # 投稿リクエスト
    response = requests.post(api_url, auth=auth, json=data)
    
    if response.status_code in [200, 201]:
        print(f"WordPressへの投稿が成功しました: {response.json()['link']}")
    else:
        print(f"WordPressへの投稿が失敗しました: {response.status_code}")
        print(response.text)

def main():
    if len(sys.argv) < 2:
        print("使用方法: python cross_post.py <markdown_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        sys.exit(1)
    
    # 設定を読み込む
    config = load_config()
    
    # マークダウンを解析
    frontmatter, body = parse_markdown(file_path)
    
    # 各プラットフォームに投稿
    post_to_qiita(frontmatter, body, config)
    post_to_wordpress(frontmatter, body, config)

if __name__ == "__main__":
    main()