---
title: "git pull「Need to specify how to reconcile divergent branches」エラーが発生"
emoji: "🔧"
type: "tech"
topics: [git, github , rebase , pull , error]
published: true
---

## 背景
- 作業ブランチ: `feature/app-refactor`
- リモート: `origin/feature/app-refactor`
- 作業内容: アプリ向け Terraform リポジトリでの修正を push しようとした
- 直前に別チームの PR が `main`へマージされており、リモート側で取り込みを実施して履歴が先行していた

## 発生した事象
- `git pull --tags origin feature/app-refactor` を実行すると、以下のエラーで処理が停止した
  - `fatal: Need to specify how to reconcile divergent branches.`
- その結果ローカルにリモート更新が取り込まれず、push も拒否された（non-fast-forward）

## 原因
- 別 PR が `main` へマージされたことでリモートの `feature/app-refactor` が進み、ローカルの同名ブランチと履歴が分岐していた
- Git 2.27 以降では、分岐状態で `git pull` を行う際に「マージ」「リベース」「ff-only」のいずれかを明示しないと処理が進まないため、エラーメッセージが表示された

## 対応手順
1. pull 時のデフォルト挙動をマージへ設定
   - `git config --global pull.rebase false`
2. 再度 pull を実行し、リモート更新を取り込む
   - `git pull --tags origin feature/app-refactor`
3. コンフリクトがないことを確認したうえで push を実施
   - `git push origin feature/app-refactor`

## `pull.rebase` 設定の違いについて

`git pull` の挙動は、`pull.rebase` の設定値によって「マージ」か「リベース」かが決まります。

### `pull.rebase false` (マージ方式)

- `git pull` を実行すると、内部で `git fetch` + `git merge` が行われます。
- リモートとローカルの変更を統合するための**マージコミットが新たに作られます**。
- **特徴**: 誰がいつ変更を統合したかという履歴が正確に残りますが、コミットログが分岐して複雑になりがちです。

### `pull.rebase true` (リベース方式)

- `git pull` を実行すると、内部で `git fetch` + `git rebase` が行われます。
- ローカルのコミットを一旦取り消し、リモートの最新コミットの直後に移動（再適用）します。
- **特徴**: マージコミットが作られず、**コミット履歴が一直線になり、非常にクリーン**に保たれます。

今回の対応では、Gitのデフォルト挙動であり、変更履歴が明示的に残るマージ方式 (`false`) を選択しました。プロジェクトによっては、履歴を綺麗に保つためにリベース方式 (`true`) を推奨する場合もあります。

## 補足
- VS Code(Cursor) の GUI で同等操作を行う場合は、リポジトリのコンテキストメニューから「プル」を選択するとマージ方式での pull になる
- リベース方式で履歴を直列化したい場合は `git pull --rebase ...` または GUI の「プル（リベース）」を使用する
- 今回はグローバル設定を変更したが、プロジェクト単位で切り替える場合は `git config pull.rebase <true|false>` を使用する