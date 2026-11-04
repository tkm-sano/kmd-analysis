# 再現性と環境
Pythonは既存.conda/bin/python3.11を-B付きで使用した。研究コード・既存環境を変更せず、全スクリプトをtrial/scriptsに保存した。新たな大規模実験は行っていない。
再実行は別の一意な新規trialへscriptsをコピーし、開始時にSTART/Git状態/追跡SHA台帳を作ってから、inventory.py → literature_audit.py → finalize_literature.py → review_claims.py → write_content.py → figures_step4.py → build_thesis.py → render_thesis.py → write_audits.py → add_verifications.py → final_audit.pyの順で行う。現行の元原稿・旧trialを上書きしない。
3.6の古典主対照には、run_cpu_matched_classical_swaps.pyで確認した隣接降下・乱数摂動・soft CPU cap・incumbent保持の説明を加え、write_content.pyにも最終文面を反映した。最終drafts/が実際の文章版であり、本文生成の入力として使用する。DOCXの生成はこの最終drafts/を入力にする。源文章版のhashは出力台帳に記録する。
図の再生成はdata/PATH2_SENSITIVITY_SUMMARY.csvとCROSS_PATH_CONDITION_MATRIX.csvをStep3からコピーし、三つのFIGURES出力ディレクトリを作った上でfigures_step4.pyを実行する。編集済みの章番号を画像内へ反映した。図データは元CSVを変更していない。
表示は既存LibreOffice24.2.7.2バイナリを読み取り専用で使用し、profile/cacheはtrial内に作った。DOCXからPDFへ二回変換し、章ページを照合して固定目次を更新する。全ページPNG/contact sheetはrenderに保存する。Word実機の表示は未確認である。
源の一部は外部保全領域にあり、このtrialだけで原地理データから実験全体を再生成できるとはしない。書誌照合のHTTP失敗・確認範囲は原ログを参照する。Step5では採否、文献の全文確認範囲、保存付録の提出形態を別途判断する。
