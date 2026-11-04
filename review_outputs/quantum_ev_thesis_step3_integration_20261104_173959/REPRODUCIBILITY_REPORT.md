# 再現性報告

この改訂は新しい科学実験を実施していない。scripts/audit_evidence.pyは元入力・保存測定・保存証明を読み、461450検査項目を照合した。実行時間は22.30秒、seedを伴う新計算は既存group再標本化の独立再現（PCG64 seed20261102、10000回）である。solver・量子学習・SUMO・実機実験は実行していない。検査項目数は科学的標本数ではない。

主要手順はaudit_evidence.py（検算）、build_tables_figures.py（既存統計から図表）、build_docx.py（原DOCX XML＋改稿本文）、render_docx.sh（PDF）、inspect_render.py（全ページ画像）、audit_document.py（文書監査）である。.conda/bin/python -Bで実行し、追加Python cacheを元研究へ書かない。図表はPNGに加え作成可能なPDF/SVG、表はCSVと編集可能なWord表を保存した。

文献のOpenAlex JSONと一次資料はsources/literatureへ取得日時付きで保存した。台帳は実際の巻年を用い、原著の確認範囲を示す。最初の取得失敗・誤取得を隠さず保存し、成功したretryと正しい一次資料だけを根拠にした。fetch系スクリプトは取得作業の記録であり、将来のネットワーク応答・被引用数は同一とは保証しない。凍結したCSV/JSONが今回の版を定める。

文書生成は原stylesと選択した原XMLを使う。表示検証には既存保全LibreOffice runtimeとPyMuPDFを読み取り利用し、profile/cache/PDF/画像は今回ディレクトリ内へ保存した。Microsoft Wordのネイティブ表示は未確認である。原ファイル同一性はSOURCE_PRESERVATION_REPORT.json、追跡ファイルはTRACKED_PRESERVATION_REPORT.jsonを参照する。

保存結果の算術再現と、原資料からの再生成・現実妥当性を分ける。ローカル外部保全領域へ依存する入力を含み、公開cloneだけで研究全体を再現できるとは主張しない。原地域網・需要の再生成と実車校正はHOLDを維持する。
