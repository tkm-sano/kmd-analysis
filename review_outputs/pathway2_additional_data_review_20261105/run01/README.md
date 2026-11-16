# 因果経路2追加データレビュー

入口はFINAL_REPORT_JA.mdである。数値採用はADDITIONAL_DATA_INVENTORY.csv、出典はSOURCE_EVIDENCE_MATRIX.csv、再判定はHOLD_REASSESSMENT.csv、計算設計はRECALCULATION_PLAN.csv、順序はEXECUTION_ROADMAP.md、完了条件はCOMPLETION_CRITERIA.md、監査はFINAL_AUDIT.mdである。

sources/は取得した一次資料・補足・Source Dataである。403/404等のHTML応答も失敗証拠として保存し、文献本文の数値根拠として採用していない。web記録はevidence/web*.jsonである。xlsxは初回取得時に誤拡張子.htmlで保存された同一bytesも残しており、canonicalな.xlsxコピーとのhash一致を監査した。

再現する場合はこのrunを新しい独立先に複製し、複製先のscriptsを実行する。既存T08/T09出力と本runの保存値を上書きしない。sourcesからの読取・台帳再生成は以下である。

```bash
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/prepare_evidence.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/extract_public_data.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/build_review.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/finalize_review.py
```

実行場所は元リポジトリrootを想定し、new-runもreview_outputs/<task>/runNNの深さへ置く。旧パス依存は保全manifestに記録した。依存はPython3.11、requests、numpy、pandas、openpyxl、Pillow、およびPopplerのpdftotext/pdftoppm/pdftocairoである。acquire.pyとREQUEST_BATCH*.jsonは実際の取得要求を記録したもので、再ダウンロード時のHTTP成功は保証しない。成功物のSOURCE_SHA256.csvと取得ログが出典追跡の基準である。

公開データ派生量はevidence/PUBLIC_PROFILE_INTEGRALS.csv、元セル範囲と放電枝CSV、cycle端点はPUBLIC_CYCLING_ENDPOINTS.csv、Chen概数はCHEN_FIG5G_DIGITIZED.csvである。これらはLP/S対象パックの新しい予測値ではない。
