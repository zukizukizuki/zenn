---
title: LPIC304チートシート
tags:
  - Linux
  - lpic
  - 仮想化
  - linuc
  - LPIC3
private: false
updated_at: '2021-04-30T22:27:00+09:00'
id: 99ce97d8cb0a4bdb7bdc
organization_url_name: null
slide: false
ignorePublish: false
---
xlコマンド
---
vcpu-list…cpu情報
vcpu-set…cpu設定

xen
---
vif…IP,MAC設定

dom0_mem は grub.cfg に設定

ハイパーバイザ…独立とリソースマッピング保証

qemu-kvmコマンド
---
-name…VMの名前指定
-boot…ブートデバイス指定
-cdrom…ISOをVMに
-monitor stdio…QEMU標準出力
-net user…userモード
-net tap…TUN/TAP使用し、接続
-net nic…VLAN接続用NIC作成

qemu-imgコマンド
---
info…イメージ情報

QEMUモニタ
---
change…disk入替
info cpus…cpu情報
info network…net情報
info snapshots…SN一覧

高可用
---
DSR…LB経由せず直接レスポンス

パワーフェンシング…障害ノード電源OFF
スイッチフェンシング…通信を遮断

RPO…どの時点まで復旧？
RTO…いつまでに復旧？

LB
---
nanny…リアルサーバを監視

LVSアルゴリズム
---
rr…均等に
wrr…処理能力に応じて均等に
lc…少ない所に多く
wlc…デフォルト、最小に多く、処理能力の重みづけを付加
ldlc…IP参照、少ない所に多く
ldlcr…
dh…宛先ハッシュ
sh…送信元ハッシュ
sed…最小遅延
nq…処理してないとこに→最小遅延

ipvsadmコマンド
---
--start-deamon…デーモン開始
--stop-deamon…デーモン停止
-g,--gatewaying…ダイレクトルーティング
-s,-scheduler…スケジューリング指定

keepalived…リアルサーバを監視、LB冗長化
---
virtual_server…仮想サーバ、LB
delay_loop…監視感覚
lb_algo…アルゴリズム
lb_kind…フォワーディング方式

VRRP…keepalivedで使われるLB冗長化

ldirectord…LVS設定を簡単に
---
autoreload…設定ファイルが変わったら自動読み込み
checkinterval…接続テスト間隔
checktimeout…応答がない時異常判定時間
checktype…チェック方法
fallback…全て停止した時の転送先
logfile…ログ保存先
quiescent…no=以上はリストから削除。yes=重みづけ0だけど削除しない
real…リアルサーバとサービスの指定

HAproxy
---
roundrobin…順番。重みづけ変更可
static-rr…順番。重みづけは静的
leastconn…コネクト少ない優先
source…送信元ハッシュ
uri…uri全体をハッシュ化
url_param…URLパラメータによって振り分け
hdr()…HTTPヘッダによって振り分け
rdp-cookie…RDPクッキーにより振り分け

/etc/haproxy/haproxy.cfgには最後にオプションを指定

pacemaker
---
CIB…クラスタの設定、リソース状態
CRMd…クラスタ全体を管理
PEngine…CIBに基づいて最適化
LRMd…ローカルリソース管理
STONITHd…フェンシング

cib.xml…CIBの内容、起動時自動作成される、クラスタと同期

RA…リソースエージェント
---
LSB…内部構造標準仕様
OCF…LSB拡張、クラスタ標準
System Service…Systemd,Upstart,LSBの組み合わせ

pacemaker関連コマンド
---
crm_attribute…クラスタオプション管理
crm_mon…状態監視
crm_node…ノード情報一覧
crm_resouce…リソースタスク実行
crm_shadow…クラスタの前にサンドボックスで実行
crm_simulate…応答シミュ
crm_stanby…crm_attributeのラッパー
crm_verify…構文エラーチェック

cibadminコマンド
---
-C,--create…作成
-D,--delete…削除
-d,--delete-all…全て削除
-E,--erace…全てのコンテンツ削除
-M,--modify…変更
-o,--scope…操作の対象を限定
-Q,--query…検索
-R,--replace…置換
-u,--upgrade…設定を最新更新

-A,--xpath…XpathとしてXML指定
-l,--local…対象をローカルに
-X,--xml-text…文字列としてXML指定
-x,--xml-file…XMLファイル指定

crmコマンド、crmshシェル
---
cib…CIBの管理
cluster…クラスター管理
configure…CIB設定の管理
node…ノード管理
ra…リソースエージェント管理
resource…リソース管理
status…クラスタの状態表示

pcsコマンド
---
acl…ACL設定
cluster…クラスタ、ノード設定
config…表示管理
constraint…リソース制約
property…プロパティ
resource…リソース管理
status…状態表示
stonith…フェンスデバイス

corosyncコマンド
---
corosync-cfgtool…管理
corosync-cmapctl…DBアクセス
corosync-keygen…認証キー生成
corosync-quorumtool…クオーラム設定、表示

DRBD…ミラーリング,drbd,/proc/drbd
---
レプリーケーション
A…非同期、障害に弱いけど早い
B…メモリ同期、普通
C…同期、障害に強いけど遅い

/etc/drbd.conf
allow-two-primaries…デュアルプライマリで負荷分散

drbdadmコマンド
---
-c,--config-file…設定ファイル指定
-s,--drbdsetup…drbdsetupの絶対パス
-m,--drbdmeta…drbdmetaの絶対パス

primary…プライマリに切り替え
role…ロール表示、プライマリセカンダリ表示
syncer…再同期パラ読み込み
verify…オンライン照合

cLVM…クラスタ内で論理Volumeを作る,clvmd
---
vgsコマンド…一覧表示
---

vgchangeコマンド
---
-a,--activate…アクティブ切替
-c,--cluster…VG共有するか？
-l,--logicalvolume…LV最大
-p,--maxphysicalvolumes…PV最大
-s,--physicalextentsize…PVエクステントサイズ変更

GFSコマンド
---
mkfs.gfs2…FS作成
mount.gfs2…FSマウント
fsck.gfs2…check,修復
gfs2.grow…拡張
gfs2.edit…表示,出力,編集
gfs2.jadd…ジャーナル追加

OCFS2コマンド…/etc/ocfs2/cluster.conf
---
mkfs.ocfs2…FS作成
mount.ocfs2…FSマウント
fsck.ocfs2…check,修復
tunefs.ocfs2…プロパティ変更
mounted.ocfs2…OCFS2を表示
o2info…FS情報
o2image…metaコピー復元

O2CBコンポーネント…/etc/sysconfig/o2cb
---
o2nm…ノードマネージャ
o2hb…heartbeat
o2net…ネットワーク
o2dlm…ロック
dlmfs…インメモリFS

