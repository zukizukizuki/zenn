---
title: AWS WAFで403 Forbiddenで酷い目にあった話
private: false
tags:
  - AWS
  - WAF
  - 403
  - 障害対応
updated_at: '2025-05-28T12:31:13.629Z'
id: null
organization_url_name: null
slide: false
---

## 1. 発生した問題

- CloudFrontのWAFで403 Forbiddenエラーが発生
- 結論から言うとIPアドレス許可リストに追加しようとした際、異なる2つのIPアドレスが検出された
  - `curl -s ifconfig.me`: `[IP_ADDRESS_1]`
  - cman.jp: `[IP_ADDRESS_2]`

## 2. 調査プロセス

### 2.1 初期確認
- CloudFrontからの403エラー応答を確認
- WAFのルール設定を確認
- IPアドレスの許可リスト（`ltd_ip_set_allow`）の設定を確認

### 2.2 IPアドレスの検証
複数のサービスでIPアドレスを確認：
```bash
# 異なるサービスでのIP確認結果
ifconfig.me: [IP_ADDRESS_1]
ipinfo.io: [IP_ADDRESS_1]
checkip.amazonaws.com: [IP_ADDRESS_1]
cman.jp: [IP_ADDRESS_2]
```

## 3. 原因分析

異なるIPアドレスが表示される主な要因：

1. **プロバイダーのNAT設定**
   - 国内/海外向けで異なるNATゲートウェイを使用している可能性
   - アクセス先によって異なる経路を使用

2. **プロバイダーのプロキシ設定**
   - 国内向けトラフィックと海外向けトラフィックで異なる経路を使用
   - 特定のサービスへのアクセスで異なるプロキシを経由

3. **DNSとCDNの影響**
   - サービスのCDN設定による経路の違い
   - 地理的な位置による経路の違い

## 4. 解決策

### 4.1 短期的な対応
1. WAFのIPセットに両方のIPアドレスを追加
   - `[IP_ADDRESS_1]`
   - `[IP_ADDRESS_2]`

### 4.2 長期的な対応
1. **IPアドレスの定期的な確認**
   - 複数のサービスでIPアドレスを定期的に確認
   - 新しいIPアドレスが検出された場合、WAFの設定を更新

2. **WAFルールの監視**
   - WAFのログを定期的に確認
   - ブロックされたアクセスのパターンを分析

3. **ドキュメント化**
   - IPアドレスの変更履歴を記録
   - WAF設定の変更履歴を記録

## 5. 今後の同様の事象への対応手順

1. **IPアドレスの包括的な確認**
   ```bash
   # 複数のサービスでIPを確認
   curl -s ifconfig.me
   curl -s ipinfo.io/ip
   curl -s checkip.amazonaws.com
   # cman.jpでも確認
   ```

2. **WAFの設定確認**
   - AWS ConsoleでWAFのIPセットを確認
   - 検出された全てのIPアドレスが許可リストに含まれているか確認

3. **アクセステスト**
   ```bash
   # 各IPアドレスでのテスト
   curl -v -H "X-Forwarded-For: [検出されたIP]" https://[対象ドメイン]/
   ```

4. **ログ確認**
   - CloudFrontのログ
   - WAFのログ
   - アクセス元IPアドレスの確認

## 6. 教訓

1. IPアドレスの確認は複数のサービスで行う
2. プロバイダーのNAT設定により複数のIPアドレスが存在する可能性を考慮
3. WAFの設定更新時は、全ての可能性のあるIPアドレスを考慮する
4. 定期的なIPアドレスの確認と監視の重要性

この対応を通じて、WAFの設定とIPアドレスの管理において、複数の確認手段と包括的な対応の重要性が明確になりました。