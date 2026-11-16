# 最終学術監査

総合判定は **CONDITIONAL COMPLETE** である。保存証拠によるStep5再分析・改訂稿作成・監査は完了したが、全HOLD解消、Microsoft Word実機確認、大学提出版の完成を意味しない。同一エージェントの分離工程であり第三者査読ではない。

## 15項目の監査

| 項目 | 対象 | 判定 | 証拠 | 位置 |
| --- | --- | --- | --- | --- |
| 1 | 目的と結論 | PASS_WITH_LIMITS | RQ0/RQ1/RQ2/RQIを明記し、未回答の実定時率/実材料を区別 | 1.4/7章 |
| 2 | 方法と結果 | PASS | 同一入力分数比較、全階層統計、モデル時刻/凍結DCが対応 | 3/4/5章 |
| 3 | 元データと数値 | PASS | 全件数値検査37724、科学検算1386、最終機械検査28がPASS | 各CHECKS.csv |
| 4 | 差の符号・単位 | PASS | 候補−greedy、正で悪化。旧定義は保存付録の履歴 | 3.8/4.2 |
| 5 | 標本単位・独立性 | PASS | 36,800反復出力/460入力/25group/26親を区別。固定cohort記述 | 3.8/4.2 |
| 6 | 結果と考察 | PASS | 4章に数値、6章に機構候補・変換条件・意味を配置 | 4/6章 |
| 7 | Step4採用判断 | PASS | 科学台帳をbyte同一コピーして維持 | STEP4_EVIDENCE_DECISIONS |
| 8 | HOLD保持 | PASS_WITH_OPEN_HOLD | 46/41、H_plan/QPU、Chen/full-cell/BOM、道路/実車、引用、Wordを保持 | 6.7/各報告 |
| 9 | 量子因果帰属 | PASS_WITH_LIMITS | CPU模擬と古典対照を分離、予算不一致、経路2上流未実行を明記 | 4.1/6.5 |
| 10 | 実証範囲と限界 | PASS_WITH_LIMITS | 静的OD/共通上限と契約定時率、モデルと実車を区別 | 4.5/6.7 |
| 11 | 先行研究比較 | CONDITIONAL | 既存20項目＋関連一次資料の限定確認。網羅的精読ではない | 2章/LITERATURE_COMPARISON.csv |
| 12 | 新規性 | PASS_WITH_LIMITS | 指定cohort/支持/証拠対応の追加に限定。「初めて」の主張なし | 6.6/貢献報告 |
| 13 | 引用・参考文献 | CONDITIONAL | 比較文献7項目の書誌/確認範囲対応、旧原意図/未精読HOLD | 文献台帳/ISSUE H04 |
| 14 | DOCX/PDF一致 | CONDITIONAL | 現行本文183段落と表451セルの正規化抽出一致、86OMML保持。Word実機はHOLD | DOCX_PDF_* /RENDER_RUN |
| 15 | 図表と本文参照 | PASS_DISPLAY_SCOPE | 新4図＋設定/入力/運用表、全118頁接触シート、代表頁拡大。大学体裁はHOLD | NEW_FIGURE_REGISTER/visual log |

## 主張と根拠

`evidence/CLAIM_EVIDENCE_MAP.csv` に11主要主張、計算式、元パス、Step5根拠、論文章を対応付けた。入力の正本は `ANALYSIS_INPUT_SHA256.csv` と `SCIENCE_INPUT_SHA256.csv`、全新規出力は `OUTPUT_SHA256_MANIFEST.csv` で固定する。表中の秒と百分率はCSVから作成し、高桁数値を測定精度とは扱わない。

## 問題・原因・修正・再検証

| ID | 原因 | 箇所 | 修正/扱い | 状態 | 再検証 |
| --- | --- | --- | --- | --- | --- |
| F01 | 旧差の符号が依頼と逆 | 旧方法/図表/要旨/結論 | 候補−greedyへ統一し全36,800分数を旧差と逆符号照合 | RESOLVED | NUMERICAL_CHECKS/FINAL_AUTOMATED_CHECKS |
| F02 | 計画中央値と入力中央値の混同余地 | 4.2/全統計 | 0秒と7.473770秒、SD1459.379/622.305を別表示 | RESOLVED | INPUT_UNIT_STATISTICS/GAP_DESCRIPTIVE_STATISTICS |
| F03 | 平均相対率と平均J比の非同義性 | 3.8/4.2 | 22.243524%と28.471877%を分離 | RESOLVED | RELATIVE_GAP_VS_RATIO_OF_MEANS |
| F04 | 帰庫を配送完了と同一視する危険 | 4.5 | 最終帰路を除外してLを再構成。負差180件も保存 | RESOLVED | OPERATIONAL_SUMMARY/B_PLAN_GAPS |
| F05 | 共通上限遵守を契約定時率へ転用する危険 | 4.5/要旨/結論 | モデル内100%両側と契約率NULLを分離 | RESOLVED_SCOPE | S5-OP-02 |
| F06 | 存在と取得の混同 | 4.6/6.2 | mirror不存在、全支持135+条件付41、238等値、46未証明を分離 | RESOLVED_SCOPE | FULL_SUPPORT_EXISTENCE_BY_INPUT |
| F07 | Chen算術PASSを主材料採用に昇格する危険 | 5章/要旨/結論 | 主は記号感度と材料非依存DC。参考節はHOLD注記保持 | RESOLVED_SCOPE | STEP4_EVIDENCE_DECISIONS |
| F08 | 縮小後の新図の文字が小さい | 図4-1〜4 | 実寸を想定したfigsize/文字サイズへ再生成、PDF代表頁を拡大確認 | RESOLVED | scripts/refine_figures.py/render/page_017,019,020 |
| F09 | 同年Robinson Part I/IIの表記 | 2.4/参考文献 | 2008a=Part I、2008b=Part IIへ整形、内容HOLDは維持 | RESOLVED_FORMAT | FINAL_AUTOMATED_CHECKS |
| F10 | PDF抽出でminus/arrowの順序がずれる | 5.2/6.7 | DOCXの字形を維持しPDF22/27頁を拡大目視。本文一致検査は当該字形を正規化 | RESOLVED_RENDER_EXTRACTION | DOCX_PDF_PROSE_MATCH |
| F11 | Step5外の既存ポスターに開始後更新を検出 | poster_causal_structure_revision_20261105 | 13ファイルのhash差と新規Gitエントリを記録。Step5は戻さず、研究入力と区別 | EXTERNAL_CHANGE_RECORDED | EXTERNAL_BASELINE_CHANGES/EXTERNAL_GIT_STATUS_CHANGES |
| H01 | 46最適値未証明/41外部証明未了 | 4.6/6.7 | 主greedy差は460全件使用可。最適gap等の断定を限定 | HOLD_RESEARCH | Step4 P1-04/07 |
| H02 | 計画締切/全工程時間/QPU/実採用 | 3.11/4.6/6.7 | 不足数値を補作しない | HOLD_RESEARCH | Step4 P1-12/13 |
| H03 | 実材料/full-cell/未知BOM/実車 | 5/6.7 | Chen入力適格性・完成pack・実車効果を断定しない | HOLD_RESEARCH | Step4 M-03/P2 |
| H04 | 旧引用原意図と原著未確認 | 2/参考文献/保存付録 | Papachristos等を現行主結果の根拠から除外 | HOLD_SUBMISSION_SCOPE | Step4 CITATION_AUDIT/Step5 LITERATURE_COMPARISON |
| H05 | Microsoft Word実機/大学提出体裁 | 全原稿 | LibreOffice表示版と機械/目視監査まで。提出先の様式確定は別途必要 | HOLD_SUBMISSION | render/RENDER_RUN.json |

初回の報告作成で任意依存tabulateが未導入であったため標準的な文字列整形へ置換した。研究データや既存環境の変更は不要であった。図は初回の縮小可読性を確認して実寸に合わせて修正した。正しい数値を変えて見やすくしたのではなく、図中の字体/寸法のみを調整した。

## DOCX/PDFと保存内容

最終PDFは118頁で、現行本文・文献/付録Aは31頁まで、元保全付録Bは32頁以降である。目次の10章項目はPDFの章開始頁へ照合した。183現行通常段落と451表セルを正規化抽出で照合した。抽出時に独立配置のminus/arrowが文字順へ影響したため、当該字形を比較正規化し、PDF22/27頁を拡大して符号の表示を確認した。TOC頁は独立に照合し、式は元86OMMLの保持・代表頁の表示を確認した。PDFとDOCXのbyte同一性を意味するものではない。

全118頁を10枚の接触シートで確認し、代表頁3/17/19/20/22/27/29等を図/本文/数式/引用の観点から確認した。ページ外テキストblock0、置換文字0である。図表のサイズ、表の継続と見出し、参考例注記は確認したが、大学の提出規定とMicrosoft Word固有の再組版/自動参照は未確認である。

元保全付録1,594blockのテキスト/数式数/画像数signatureと元の画像byte集合を保持し、86式を保存した。本文の差し替え箇所は `THESIS_CHANGELOG.csv`、旧保全対応はStep4の `THESIS_PRESERVED_CONTENT_AUDIT.csv` を継承する。旧記述に残るΔJ符号・407/53・旧定時率・Chen参考値を、現行結論へ復帰させない。

## 保全結果

開始台帳と読取入力を統合した33,197ファイルのうち33,184ファイルのSHA256が一致した。元原稿・Step1〜4・使用研究入力の不一致は0であり、13不一致はStep5の書込み対象外の既存ポスター作業ディレクトリに限定された。HEADとtracked差分は不変であるが、Step5外に新規未追跡ファイルも増えており、リポジトリ全体不変とは判定しない。外部変更の作成主体は本監査では確定せず、上書き・巻戻しは行わない。詳細は `evidence/PRESERVATION_RESULT.json`、`PRESERVATION_END_CHECK.csv` に保存した。03_data全rawファイルの全byte検査ではなく、一覧保全と使用入力のhash確認を実施した範囲である。
