#!/usr/bin/env python3
"""
Zennの記事を他のプラットフォーム用にエクスポートするツール
使用方法: python export_articles.py --format [qiita|wordpress|hatena] --output <output_dir>
"""

import os
import re
import argparse
import yaml
import markdown
from pathlib import Path
from glob import glob

def parse_args():
    parser = argparse.ArgumentParser(description='Zennの記事を他のプラットフォーム用にエクスポート')
    parser.add_argument('--format', choices=['qiita', 'wordpress', 'hatena'], default='qiita',
                        help='エクスポート形式 (デフォルト: qiita)')
    parser.add_argument('--output', default='./exported',
                        help='出力ディレクトリ (デフォルト: ./exported)')
    parser.add_argument('--articles', default='./articles',
                        help='記事のディレクトリ (デフォルト: ./articles)')
    return parser.parse_args()

def parse_markdown(file_path):
    """マークダウンファイルを解析してフロントマターとコンテンツを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # フロントマターを抽出
    frontmatter_match = re.match(r'---\n(.*?)\n---\n', content, re.DOTALL)
    if not frontmatter_match:
        print(f"警告: {file_path} にフロントマターが見つかりません。スキップします。")
        return None, None
    
    frontmatter_yaml = frontmatter_match.group(1)
    frontmatter = yaml.safe_load(frontmatter_yaml)
    
    # 本文を抽出
    body = content[frontmatter_match.end():]
    
    return frontmatter, body

def convert_to_qiita(frontmatter, body, output_path):
    """QiitaのMarkdown形式に変換"""
    # タグを準備
    tags = frontmatter.get("topics", [])
    tags_str = ", ".join([f'"{tag}"' for tag in tags])
    
    # Qiita形式のフロントマター
    qiita_frontmatter = f"""---
title: "{frontmatter['title']}"
tags: [{tags_str}]
---
"""
    
    # 出力ファイルに書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(qiita_frontmatter + body)
    
    return output_path

def convert_to_wordpress(frontmatter, body, output_path):
    """WordPress用のHTML形式に変換"""
    # マークダウンをHTMLに変換
    html_content = markdown.markdown(body)
    
    # WordPressのメタデータ
    wp_header = f"""<!--
Title: {frontmatter['title']}
-->

"""
    
    # 出力ファイルに書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(wp_header + html_content)
    
    return output_path

def convert_to_hatena(frontmatter, body, output_path):
    """はてなブログ形式に変換"""
    # タグを準備
    tags = frontmatter.get("topics", [])
    tags_str = " ".join([f'[{tag}]' for tag in tags])
    
    # はてなブログ形式のヘッダー
    hatena_header = f"""---
title: {frontmatter['title']}
date: {frontmatter.get('date', '')}
categories:
{tags_str}
---
"""
    
    # 出力ファイルに書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(hatena_header + body)
    
    return output_path

def main():
    args = parse_args()
    
    # 出力ディレクトリを作成
    os.makedirs(args.output, exist_ok=True)
    
    # 記事ファイルを取得
    article_files = glob(os.path.join(args.articles, '*.md'))
    
    # 変換関数を選択
    if args.format == 'qiita':
        convert_func = convert_to_qiita
        ext = '.md'
    elif args.format == 'wordpress':
        convert_func = convert_to_wordpress
        ext = '.html'
    elif args.format == 'hatena':
        convert_func = convert_to_hatena
        ext = '.md'
    
    # 各記事を変換
    for file_path in article_files:
        print(f"処理中: {file_path}")
        
        # マークダウンを解析
        frontmatter, body = parse_markdown(file_path)
        if not frontmatter:
            continue
        
        # ファイル名を取得
        filename = os.path.basename(file_path)
        output_filename = os.path.splitext(filename)[0] + ext
        output_path = os.path.join(args.output, output_filename)
        
        # 変換して保存
        converted_path = convert_func(frontmatter, body, output_path)
        print(f"変換完了: {converted_path}")
    
    print(f"\n{args.format}形式への変換が完了しました。")
    print(f"出力ディレクトリ: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()