---
title: windows11 ベースの端末にwindows server 2022を入れた時の備忘録
private: false
tags:
  - windows
  - windows_server
  - BIOS
  - backup
updated_at: '2025-06-01T01:53:18.484Z'
id: null
organization_url_name: null
slide: false
---

## はじめに
windows11が入ってる端末に windows server 2022を構築しようとした。
物理マシンにwindows server を構築する機会がなかなかなく今度同じような事を
したいときの備忘録をここに残す。

## 前提
- 使用端末：HP Elite SFF 600 G9 Desktop
- 外付けHDD：BUFFALO HD-PCFS1.0U3-BBA
- USBメモリ：USB FLASH 1000GB
- CPU：HP Elite SFF 600 G9 Desktop PC
- BIOS：U01 Ver.02.11.00 07/25/2023

## ダメだった案1
1. ISOをダウンロード後 右クリックで「マウント」を実行しEドライブにマウント
2. BIOSを開くため再起動
https://pc-karuma.net/enter-uefi-bios-on-windows-11-pc/
→再起動するとマウント外れるためダメ

## ダメだった案2
1. ISOをHDDに書き込む(3時間くらいかかったのでUSBメモリ推奨)
https://techlive.tokyo/archives/10783

2. BIOSを開くため再起動
https://pc-karuma.net/enter-uefi-bios-on-windows-11-pc/

3. BIOS 動いたら以下の順で選択
Boot Menu → ISOを書き込んだ機器名 → Continue Boot
・BIOSから起動順をいじってHDDを一番先にしてもダメ
・容量が使用されてないので本当に書き込まれているのか微妙
・手でISOファイルを入れるもダメ

いろんな記事を見たけどみんなUSBメモリでやってるのでUSBメモリ使ってリベンジ

## ダメだった案3
1. ISOをUSBメモリに書き込む
https://techlive.tokyo/archives/10783

2. USB内の setup を起動し以下の設定を選択する
・パッケージ：windows server 2022 standard (デスクトップエクスペリエンス)
・引継ぎ項目：何もしない

3. インストールが完了すると再起動される

ドライバーのエラーでインストール出来ない
エラーコード：0xC1900101 - 0x20017
https://support.microsoft.com/ja-jp/windows/windows-%E3%81%AE%E3%82%A2%E3%83%83%E3%83%9[…]%98%E3%83%AB%E3%83%97-ea144c24-513d-a60e-40df-31ff78b3158a

ブート順を元に戻して再度試してみる → ダメ
再起動後のエラー内容が  Unmountable Boot Volume
https://www.partitionwizard.jp/clone-disk/unmountable-boot-volume.html

windows11は消していいので回復から初期化して再インストール→ダメ
desktopエクスペリエンスを選択しないといけないっぽい？→ダメ
https://ameblo.jp/mizuhokuzuhara/entry-12536887629.html

システム ファイルを復元および修復を実施→ダメ
クリーンブート→ダメ

※exeを実行したり起動順を変えるのではなく以下のようにbootオプションでUSBメモリを選択するのが正解

## ダメだった案4
1. ISOをUSBメモリに書き込む
https://techlive.tokyo/archives/10783

2. 以下の方法でBIOSを開く
https://pc-karuma.net/enter-uefi-bios-on-windows-11-pc/

3. F9 bootオプションで1で作成したUSBを選択

windows server2022をインストールするドライブが見つからないのでVMD用ストレージコントローラーの構成を無効化してみる→ダメ
https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q14261094919
https://sunrise-gifu.com/intel_vmd/
→BIOSで見当たらない。rstドライバインストールしても無理。
→Intel optenaからも認識されていない

windowsバックアップからいけるかも
https://www.truesystems.jp/blog/use-windows-server-2022-backup
→結局diskが見つからないのでドライブを認識させないとダメ

BIOS 1~10まで確認したけどVMDの設定は VMD用ストレージコントローラーの構成を無効化 以外見当たらない

RAID無効化して再起動
→BIOS からVMD用ストレージコントローラーの構成を無効化
→inaccessible boot deviceエラー
https://manumaruscript.com/inaccessible-boot-error/
→セーフモードで起動し再起動→inaccessible boot deviceエラーが出なくなった🎉

4. 外付けHDDにwindows server2022のバックアップを取得

5. USBと外付けHDDを繋いで以下のリストア方法を実施
https://www.truesystems.jp/blog/use-windows-server-2022-backup
※復元の時にwindows11 しか選択出来なかったので要確認
→ドライブにアクセス出来ずダメだった
→Bitlockerの暗号化が原因っぽいので無効化してリベンジ
→リストアの実施
→エラー：「windows バックアップで回復したオペレーティングシステムのオペレーティングシステムローダーエントリをブートメニューにインポート出来ませんでした。(0x8078008C)」
https://answers.microsoft.com/en-us/windows/forum/all/system-image-restore-failed-0x8078008c/4eee1405-ba9d-460f-ad0e-9d2cbc9987da
→windows server 2022のインストールはいけた🎉
→リストアの実施
→エラー：「windows バックアップで回復したオペレーティングシステムのオペレーティングシステムローダーエントリをブートメニューにインポート出来ませんでした。(0x8078008C)」

上記のエラーの情報が少ないため1からインストール

## 成功案
1. ISOをUSBメモリに書き込む
https://techlive.tokyo/archives/10783

2. 以下の方法でBIOSを開く
https://pc-karuma.net/enter-uefi-bios-on-windows-11-pc/

3. F9 bootオプションで1で作成したUSBを選択

windows server2022をインストールするドライブが見つからないのでVMD用ストレージコントローラーの構成を無効化してみる→ダメ
https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q14261094919
https://sunrise-gifu.com/intel_vmd/
→BIOSで見当たらない。rstドライバインストールしても無理。
→Intel optane からも認識されていない
→Intel optane からRAID無効化して再起動
→VMD用ストレージコントローラーの構成を無効化
→inaccessible boot deviceエラー
https://manumaruscript.com/inaccessible-boot-error/
→セーフモードで起動し再起動→inaccessible boot deviceエラーが出なくなった🎉

4. windows server 2022 (デスクトップエクスペリエンス)をインストール
うまくいった
