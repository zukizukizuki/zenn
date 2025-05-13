@echo off
echo Zenn articles to Obsidian copy process started...

REM コピー元フォルダ
set "SOURCE_DIR=C:\Users\asaka\Documents\git\zenn\articles"

REM コピー先フォルダ
set "DEST_DIR=C:\Users\asaka\Documents\git\Obsidian\01_IT"

REM コピー先フォルダが存在しない場合は作成
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
    echo Created destination directory: %DEST_DIR%
)

REM robocopyコマンドでコピーを実行
REM /E : 空のディレクトリも含め、サブディレクトリをすべてコピーします。
REM /PURGE または /MIR : コピー元に存在しないファイル/フォルダをコピー先から削除します。(注意して使用)
REM /XO : 新しいファイルのみをコピーします（既に存在する同じタイムスタンプのファイルは上書きしません）。変更されたファイルは上書きされます。
REM /R:n : リトライ回数をn回に設定します。
REM /W:n : リトライ間の待機時間をn秒に設定します。
REM /LOG:filepath : ログファイルを指定したパスに出力します。
REM /NFL : ファイルリストを表示しません。
REM /NDL : ディレクトリリストを表示しません。

echo Copying files from %SOURCE_DIR% to %DEST_DIR%...
robocopy "%SOURCE_DIR%" "%DEST_DIR%" /E /XO /R:1 /W:1 /NFL /NDL

REM /MIR オプションを使う場合 (コピー元と完全に同期させ、コピー先に余分なファイルがあれば削除する)
REM 注意: /MIR を使うと、DEST_DIR にあって SOURCE_DIR にないファイルは削除されます。
REM もし意図しないファイル削除を防ぎたい場合は、/E /XO の方が安全です。
REM robocopy "%SOURCE_DIR%" "%DEST_DIR%" /MIR /R:1 /W:1 /NFL /NDL

echo Copy process finished.
REM pause