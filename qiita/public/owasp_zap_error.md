---
title: AWS環境のOWASP ZAPで「The provided browser was not found.」が出たので解決した話
private: false
tags:
  - AWS
  - OWASP_ZAP
  - 脆弱性診断
  - ペネトレーションテスト
updated_at: '2025-06-01T01:53:08.983Z'
id: null
organization_url_name: null
slide: false
---

## はじめに
penetration testing tool として広く知られる OWASP ZAP (Zed Attack Proxy)。Webアプリケーションの弱性診断に非常に役立つツールですが、GUIからブラウザを起動して操作する際に「ブラウザが見つかりません」いうエラーに遭遇することがあります。
今回、私がAWS環境でOWASP ZAPを操作していた際に、まさにこのエラーに遭遇しました。同じように困っているの助けになればと思い、発生した事象、試したこと、そして最終的な解決策をまとめました。

## 環境
AMI : [Debian 12 Web Desktop : Ultimate Sysadmin Toolset + Security Features](https://aws.mazon.com/marketplace/pp/prodview-r2juwnhaqmp5i?applicationId=AWS-Marketplace-Console&ef_=beagle&sr=0-1)
インスタンスタイプ : t3.large

## 発生した事象：「ブラウザが見つかりません」エラー
ZAPを起動し、メニューバーから「クイックスタート」を選択。「手動で探査」をクリックし、Firefoxを選択しところ、以下のエラーメッセージが表示されました。
```
The provided browser was not found.
see https://www.zaproxy.org/faq/no-browser/
```
## 試したこと（初期段階）：公式FAQを参考に
まず最初に試したのは、ZAPの公式サイトにあるFAQ「How can I fix 'browser was not found'?」に記載されいる内容です。

**ZAPのアップデート確認:** メニューバーから「ヘルプ」>「最新情報を確認」を選択しましたが、以下のエーが表示され、自動アップデートはできませんでした。
```
Error encountered. Please check manually for new updates.
```

**ローカルブラウザのアップデート確認:**  FAQには「ローカルブラウザのアップデート」とありますが、私環境はAWSのZAP AMIです。直接的な解決には繋がらないと考えました。

## 試したこと（詳細な調査）：原因特定への道のり
公式FAQだけでは解決できなかったため、より深く原因を特定するために以下のことを試しました。

**ZAPのOutputタブの確認:** エラーメッセージに「The Output tab may contain further details.」とったので確認しましたが、特にエラーに関する詳細な情報は出力されていませんでした。

**ネットワーク接続の確認:**  ZAPが外部に接続できていない可能性を考え、`ping` コマンドで `rawgithubusercontent.com` への接続を確認しました。

  ```bash
  admin@decyphertek:~$ ping raw.githubusercontent.com
  PING raw.githubusercontent.com (185.199.111.133) 56(84) bytes of data.
  64 bytes from cdn-185-199-111-133.github.com (185.199.111.133): icmp_seq=1 ttl=55 time=2.27 ms
  ...
  ```
  `ping` は成功しており、ネットワーク接続自体は問題なさそうでした。
**telnetとncコマンドでのポート接続確認:**  HTTPS (443番ポート) での接続も確認しました。
  ```bash
  admin@decyphertek:~$ nc -zv raw.githubusercontent.com 443
  Connection to raw.githubusercontent.com (185.199.108.133) 443 port [tcp/https] succeeded!
  ```
  こちらも問題ありませんでした。
**ZAPのログファイル(zap.log)の確認:**  ログファイルを確認しましたが、ブラウザが見つからないエラー関する明確な記述は見当たりませんでした。

## プロキシ設定の混乱：複数の設定項目
色々と試す中で、ZAPのプロキシ設定に複数の項目があることに気づき、混乱しました。

**オプション > ネットワーク > HTTP プロキシ**
![](https://storage.googleapis.com/zenn-user-upload/bbfb956c5c1a-20250115.png)

**オプション > ネットワーク > Local Servers/Proxies**
![](https://storage.googleapis.com/zenn-user-upload/582ff47fbd80-20250115.png)

どちらを設定すれば良いのか分からず、両方設定してみたり、ポート番号を色々変えてみたりしましたが、状況はわりませんでした。

## 解決：プロキシ設定の肝は「Local Servers/Proxies」
最終的に、ZAPのプロキシ設定で重要なのは **「オプション」>「ネットワーク」>「Local Servers/Proxies** であることに気づきました。
ここで設定したポート番号と、ブラウザのプロキシ設定のポート番号が一致していなかったことが原因だったのす。

**解決手順:**
1. **ZAPの設定確認:** ZAPの「オプション」>「ネットワーク」>「Local Servers/Proxies」を開き、「ポト」に設定されている番号を確認します。（私の場合は `8081` でした）

2. **ブラウザのプロキシ設定:** Firefoxの設定を開き、「ネットワーク設定」で「手動でプロキシを設定するを選択。**「HTTPプロキシ」と「HTTPSプロキシ」のポートを、ZAPの「Local Servers/Proxies」で確認したート番号と同じに設定します。**
私の場合は、Firefoxのプロキシ設定のポートが `8080` になっていたため、ZAPの `8081` に合わせて修正しました。

この設定変更を行ったところ、無事にZAPからブラウザを起動することができ、インターネットにも接続できるようになりました！

## まとめ
今回の件で、以下の教訓を得ました。
**エラーメッセージを鵜呑みにしない:** 「ブラウザが見つかりません」というエラーメッセージに囚われすて、プロキシ設定という根本的な原因に気づくのが遅れてしまった。
**ZAPのプロキシ設定は「Local Servers/Proxies」が重要:** ブラウザ連携においては、「HTTP プロキシではなく「Local Servers/Proxies」の設定が鍵となる。
**設定項目の意味を理解する:** 複数の設定項目がある場合は、それぞれの役割を理解することが重要。
**基本に立ち返る:**  うまくいかない時は、ネットワークの基本的な設定（プロキシなど）を見直すことが切。
今後、同様の事象が発生した場合は、まずZAPの「Local Servers/Proxies」の設定とブラウザのプロキシ設定が致しているかを確認するようにします。
