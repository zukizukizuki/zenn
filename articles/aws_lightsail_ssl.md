---
title: "【AWS】LightSailのSSL証明書の自動更新"
emoji: "🍖"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [aws , LightSail, WordPress , SSL , Bitnami]
published: true
---

Bitnamiが提供するWordPressイメージでSSL証明書を自動更新する手順を説明します。

1. SSHでLightSailインスタンスに接続します。

2. まず、Let's Encrypt アカウントを作成し、認証を行います：

```
sudo /opt/bitnami/letsencrypt/lego --path /opt/bitnami/letsencrypt --email="your_email@example.com" --http --http-timeout 30 --http.webroot /opt/bitnami/apps/letsencrypt --domains=your_domain.com --user-agent bitnami-bncert/1.1.1 run
```

your_email@example.comとyour_domain.comを適切な値に置き換えてください。このコマンドを実行すると、Let's Encryptの利用規約に同意するよう求められます。同意して進めてください。

3. 認証が完了したら、証明書が生成されます。次に、証明書の更新をテストします：

```
sudo /opt/bitnami/letsencrypt/lego --path /opt/bitnami/letsencrypt --email="your_email@example.com" --http --http-timeout 30 --http.webroot /opt/bitnami/apps/letsencrypt --domains=your_domain.com --user-agent bitnami-bncert/1.1.1 renew
```

4. 証明書が正常に更新されたら、Apacheを再起動します：

```
sudo /opt/bitnami/ctlscript.sh restart apache
```

5. 自動更新のためのcronジョブを設定します。rootのcrontabを編集するには以下のコマンドを使用します：

```
sudo crontab -e
```

6. 以下の行を追加します：

```
0 0 1 * * /opt/bitnami/letsencrypt/lego --path /opt/bitnami/letsencrypt --email="your_email@example.com" --http --http-timeout 30 --http.webroot /opt/bitnami/apps/letsencrypt --domains=your_domain.com --user-agent bitnami-bncert/1.1.1 renew && sleep 30 && /opt/bitnami/ctlscript.sh restart apache >> /var/log/letsencrypt-renewal.log 2>&1
```

この設定により、毎月1日の午前0時に証明書の更新チェックが行われ、必要に応じて更新とApacheの再起動が実行されます。

7. crontabの内容を確認します：

```
sudo crontab -l
```

8. 最後に、証明書が正しく適用されているか確認します：

```
openssl x509 -in /opt/bitnami/letsencrypt/certificates/your_domain.com.crt -noout -dates
```

これで、SSL証明書の自動更新が設定されました。/var/log/letsencrypt-renewal.logファイルを定期的にチェックして、更新プロセスが正常に実行されていることを確認してください。

注意：この方法はBitnamiが提供するWordPressイメージに特化しています。他の環境では手順が異なる場合があります。