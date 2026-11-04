# 最終品質レビュー

判定は**条件付き採用可**である。方法・結果・考察・結論のMarkdown、図10点のPNG/SVG/PDF、図表の元データ対応、26主張の審査、32箇所のDOCX反映対応を作成した。数値確認を工学的実証とみなさず、下記HOLD/FAILを保持している。DOCXへの実編集は実施していない。

## 独立照合と実行資源

|工程|今回の確認数|不一致|wall秒|最大RSS bytes|
|---|---:|---:|---:|---:|
|元行集計・経路・待機会計|32269|0|4.651891|588251136|
|図表・代表部材・保存hashの別照合|2912|0|4.360882|274792448|

上記合計35,181は照合項目数であり、独立標本数ではない。前回全件分析の独立検証・bootstrap検証の件数と区別した。Cの全速度の再積分、bootstrap再計算、科学runnerは今回実行していない。図表生成の実測資源はFIGURES_SUMMARY.json、描画の再実行ログはFIGURES_REPLAY.log、Python等はREVIEW_ENVIRONMENT.jsonに保存した。各工程のRSSは当該processのピークであり、総和や研究全体の最大メモリとして解釈しない。

保存図の全30形式ファイルは描画再実行でbyte一致した。PNG10点を実際に閲覧した。文字欠落・凡例重なり等の新規図表の不適合は修正し、差分・修正前hash・再確認をrevisions/へ保存した。数値結果や元データを修正していない。最終描画stderrは空である。Wordへの配置、印刷幅・ページまたぎ・目次と相互参照の更新はHOLDである。

## 品質基準の審査

|確認対象|判定|根拠と制限|
|---|---|---|
|数値・単位・分母|PASS|REVIEW_NUMERICAL_CHECKS.csv、PACKAGE_VALIDATION_CHECKS.csv不一致0|
|主張の証拠対応|PASS|26行にfile/row/hash/式/実装/図/限界。一般同等性・量子一般優劣等は使用不可|
|Aの100%と完了時刻差の区別|PASS|待機吸収9,216行、帰庫会計2,304組、余裕78問題を保存|
|Aの実世界解釈|CONDITIONAL|固定OD・102秒・期限余裕。実配送同等性ではない|
|Bの6設定同値の理由|PASS|初期値＝mirror支持最小2,300fit、active zero460。経路リストも別照合|
|Bの規模・方式・計算予算|CONDITIONAL|全8設定・6規模、支持・FIT/最終検証/RESULT分離。同予算一般比較は不可|
|Bの407/53分母と未実施DC|PASS|53入力を補完せず、走行DCはUNTESTEDのまま|
|Bの実機回路資源|HOLD|hardware qubits/compiled gates/depth、統一当時環境の保存不足|
|Cの既知と完成パック|PASS記載／HOLD完成品|全183完成pack NULL、既知差を完成品差としない|
|T09全面対向|FAIL保持|T09_ROW_183、元CSV source_row184。除外・修正なし|
|量子材料解析→材料改善|UNTESTED|参照文献は古典DFT・電極実験、量子機による改善実証なし|
|統計区間|CONDITIONAL|25群内依存を保持した補助感度1,176区間、検定0、モデル誤差未包含|
|図表の元CSV対応・再生成|PASS|10図×3形式、全36/8設定の表、生成コードとplot-data保存|
|用語・結果／考察分離|PASS|である調、モデル完了、OD秒、工程CPU、固定軌跡DCを区別|
|方法の再実行情報|CONDITIONAL|式・単位・設定・seed・protocol・sourcehashを記載。外部保全rawを含む公開資料不足|
|本文引用と末尾参考文献|HOLD|背景8引用の対応、Faraji-Niri DOI、引用様式の整理。LITERATURE_VERIFICATION.csv|
|論文DOCX・既存成果物の保全|PASS|2,532資料hash一致、DOCX SHA一致、tracked diff不変|

既存道路網N0幾何FAIL、N1動的FAILは継続し、地域代表試行は開始していない。Aの正の遅延native、B走行DC、T09完成パックを実証済みとしていない。実世界の交通・材料・実車妥当性について研究全体の再現性を確保したとは記さない。

## 再現手順

作業ディレクトリは `/home/takuma/kmd-analysis` である。元科学runnerを実行せず、以下のレビュー専用入口を使う。材料原著・元会計のhashを再照合する補助入口はpin_material_provenance.pyである。主要参考文献の転記案はPRIMARY_REFERENCES_FOR_INSERTION.md、元材料モデルはMATERIAL_PRIMARY_SOURCES.csv、アルゴリズム全設定はALGORITHM_PROTOCOL_APPENDIX.mdを参照する。出力先は各スクリプトの親review directoryとして決定するため、第三者はscripts/を新しいrunへコピーして再生成できる。参照元F/D等の実パスはevidence.pyに明示し、再配置時はsha一致を要求する。

```bash
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/source_and_docx.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/make_figures.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/write_review.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/write_drafts.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/docx_map_and_protocols.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/verify_package.py
```

finish_review.pyは検算と描画再実行の成功後に台帳を作る最終入口である。VISUAL_REVIEW.csvの手動確認欄は今回実際に閲覧した画像hashの証明であり、異なる画像を再生成した第三者は改めて目視確認する。自動実行だけで新たな目視受入を主張しない。RENDER_REPLAY_EXPECTED.jsonと同じ30出力hashを確認してからfinish_review.pyを使う。

入力・コード・出力のhashはSOURCE_INVENTORY_SHA256.csvとSHA256_MANIFEST.csv。hash台帳自体は自己参照を避けてその台帳から除外し、SHA256_MANIFEST.sha256で別管理する。環境用matplotlib cacheは研究成果物台帳から除外する。外部保全資料を持たない環境で全ソースを再取得できることはHOLDである。

## DOCX編集前の残作業と停止

1. 08の32対応に沿って、主系列と旧補助系列の配置・章番号を確定する。特に3.8、欠落5.2、旧548/99配送先・native3099秒の履歴を整理する。
2. 背景引用8件・DOI・参考文献様式を照合し、未確認の出典を推測で追加しない。
3. 本文の主要図・付録図、全条件表、補助区間を決め、Wordへ反映した際の数式・フォント・図幅・目次・相互参照を確認する。
4. 因果経路の到達範囲と限界を維持する。実機・実交通・完成パックに関するHOLDは追加工学証拠なしで解消しない。

限定された研究主張の転記素材は準備済みである。無修正で提出できる完成DOCXの受入ではない。新規SUMO、道路修復、再学習、全件科学実験、既存docsやDOCXの編集を行わず、このレビューの保存で停止した。
