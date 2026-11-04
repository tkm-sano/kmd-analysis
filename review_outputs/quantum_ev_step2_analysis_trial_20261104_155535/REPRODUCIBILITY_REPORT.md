# 再現方法

使用環境はevidence/ENVIRONMENT.json。元Git HEAD/remoteと開始状態はSTART/GIT_STATUS_START/GIT_DIFF_START。入力実在・保存場所・SHA256はSOURCE_PROVENANCE.csv、Step1入力hash照合はINPUT_HASH_BASELINE.csv。元B NPZ、測定JSON、古典RESULT、SCIP LP/log/solution、C trajectory、T08/T09原本が外部preservationにも必要。存在しない旧パスを推測して使わず、*_RELOCATIONS.csvの実在解決とhash一致を検査する。

科学環境は既存`.conda/bin/python`3.11.15、NumPy2.2.5、pandas2.2.3、SciPy1.15.3、Matplotlib3.11。exact前半のFraction/CSV監査はshell Python3.13.5、NumPy2.3.5/pandas2.3.3で実施。整数/分数等値は環境のfloat表示へ依存しない。CLIは同じ保存SoPlex8.0.3（SCIP10.0.3 package）。全てCPU、GPU/QPU実行false。

**既存trialへ再実行しない。** 新しい一意のreview_outputs配下へscriptsと実行前protocol文書をコピーする。common.pyのOはscript親の新trial、Rはそのrepo。scripts/evidence/logs/experiments/各FIGURESディレクトリを作り、元入力をpinしてから実行する。開始保全台帳はこのtrialのSTART作成処理と同等に別保存する。

実行順：

1. exact_audit.py（460witness・234列挙・53保存LP/log監査）。
2. prepare_exact_models.pyで148の最終LP/log/solutionを実在・hash確認して接続。exact_recheck.py --pilot と exact_separation.py --pilot（zero-tolerance/valid-bound/resource診断）。full前のgateは分数解でも有効境界を残す場合にproceedとする。
3. exact_recheck.py（148LP）→resolve_exact_status.py（弱いLPを理由に旧MIPを棄却しない）→exact_features.py。
4. path1_statistics.py → zero_success_bound.py。
5. controlled_qaoa.py --pilot → gate確認後controlled_qaoa.py（main97learning）。全cellを残す。
6. runtime_analysis.py（Qmain終了後同core）、controlled_analysis.py（shot histogram/同角度/予算感度）、path2_analysis.py（保存trajectory;別core使用可）。
7. control_sd_review.pyで目的分数が全反復同一のSDを厳密0としてpublic summaryへ正規化（元実験CSVは保持）。support_and_verification.py / dp_reference_review.py → refine_figures.py → write_reports.py → final_audit.py。

初回default toleranceのSoPlex単独diagnosticは証明ではなく参考logで、科学結果再現には-f0/-o0が必須。QAOA/measurement/bootstrap seedは各CSVとprotocol。最終angles/probabilities、shot histogramから抽出bestを再現できる。厳密LPの全モデル/dual/primal/コマンドもexperimentsに保存。

bitwiseで比較する対象は入力hashと保存原本。wall/CPU/RSSは実行環境に依存し、再実行で同じ数値を要求しない。新trial絶対パス・作成時刻でhashが変わる派生ファイルは、キーと数値列を比較する。計算コード版はCODE_SHA256.csv、成果物のhashはOUTPUT_SHA256_MANIFEST.csv。未確定external proofや物理接続を再現済みとしない。

安全な再現用にscripts/bootstrap_replay.pyとscripts/run_scientific_replay.pyを付属した。前者は新規の一意ディレクトリ以外を拒否し、後者はreplay専用markerと出力未存在を要求する。今回は別trialの科学再実行はしていない。最終監査には再現開始時点で新たに取得した保全台帳を使用し、今回の保全台帳を使い回さない。

参照強度感度はreference_strength_sensitivity.py、図一覧表示はrender_contact_sheet.py。図の重なりはrefine_figures.pyで表示だけを調整した。minplusのkernel_sha256はコンパイル済みbinaryのhash、sourceのhashはCOMPILATION.jsonで別に確認する。common.pyの空検査CSVに列schemaを付けた修正はメタデータだけで、科学計算は変更していない。
