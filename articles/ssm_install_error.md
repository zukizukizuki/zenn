---
title: "Get-Content : パス 'SSM\\InstanceData\\registration' が存在しないため検出できません。"
emoji: "⭕"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [windows , windows_server, AWS , SSM]
published: true
---

## 概要
windows server 2022にRDPするためにSSM agentを[公式の方法](https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/sysman-install-managed-win.html)でインストールしようと以下のコマンドを実行したところ・・・

```
$code = "activation-code"
$id = "activation-id"
$region = "region"
$dir = $env:TEMP + "\ssm"
New-Item -ItemType directory -Path $dir -Force
cd $dir
(New-Object System.Net.WebClient).DownloadFile("https://amazon-ssm-$region.s3.$region.amazonaws.com/latest/windows_amd64/AmazonSSMAgentSetup.exe", $dir + "\AmazonSSMAgentSetup.exe")
Start-Process .\AmazonSSMAgentSetup.exe -ArgumentList @("/q", "/log", "install.log", "CODE=$code", "ID=$id", "REGION=$region") -Wait
Get-Content ($env:ProgramData + "\Amazon\SSM\InstanceData\registration")
Get-Service -Name "AmazonSSMAgent"
```

以下のエラーが出てしまった。
```
PS C:\Users\root\AppData\Local\Temp\ssm> Get-Content ($env:ProgramData + "\Amazon\SSM\InstanceData\registration")

Get-Content : パス 'C:\ProgramData\Amazon\SSM\InstanceData\registration' が存在しないため検出できません。

発生場所 行:1 文字:12

+ Get-Content <<<<  ($env:ProgramData + "\Amazon\SSM\InstanceData\registration")

    + CategoryInfo          : ObjectNotFound: (C:\ProgramData\...ta\registration:String) [Get-Content]、ItemNotFoundException

    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
```

## 調査内容
`Start-Process .\AmazonSSMAgentSetup.exe -ArgumentList @("/q", "/log", "install.log", "CODE=$code", "ID=$id", "REGION=$region") -Wait`

でログを出してるみたいなので$env:TEMPで指定してたtempフォルダ内のログを見てみると

`2023-11-01 12:16:59 ERROR Registration failed due to error registering the instance with AWS SSM. ActivationExpired:`

の記述を確認

どうやらアクティベーションの期限切れの様なので作り直してコマンドを再実行したらいけた

## 結論
ログを見よう