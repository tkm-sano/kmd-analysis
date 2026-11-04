# 統計・研究解釈の監査

|項目|判定|確認内容|
|---|---|---|
|主比較/分母|PASS|JC greedy、random別、initial補助、J*共通。全460とexact414を分離|
|階層|PASS|25group/26parent/input460/config8/fit1/measurement10。36,800独立学習としない|
|欠測/非可行|PASS|全保存best可行を再計算、exact46はNULL、invalid raw未保存はNULL|
|不確実性|CONDITIONAL|group交換可能性・測定stream独立は仮定。有限cohort/条件付き測定/仮想母集団感度を分離|
|ゼロ改善区間|CONDITIONAL|bootstrap[0,0]は観測分布の退化。Wilson/条件付きゼロevent上限を併記、学習へ外挿しない|
|新規学習反復|PASS|97optimizer-start/cellと10measurement/fitを分離。rep0 Wilson、fit bootstrap|
|要因統制|CONDITIONAL|小規模同入力/支持/初期/mixer/p/評価/測定予算。support間ではgraphも変わる。旧staged8の全条件統制とは別|
|時間比較|CONDITIONAL|scope内のCPU分布。Q10出力/greedy1出力と共通初期生成除外を明示。H_plan未設定|
|モデル範囲|CONDITIONAL|T08主/T09補完、既知部材とunknownを分離。凍結物理/同軌跡/観測窓のみ|
|49点/Crr|PASS|独立実験数にしない。軌跡内対応と決定論的格子を保持|
|多重比較/検定|PASS|検定0。全cell/設定を表示、主要greedyと探索的機構診断を区別|
|未実証接続|HOLD|実道路改善・実材料の量子由来改善・実機優位は未実証|

scipy未導入のshell Pythonを統計には使わず、既存科学環境Python3.11へ切替えた。exact監査のFraction演算/CLIはshell Python3.13、科学計算/図は既存.condaの版を記録。入力は変更していない。解析コードの不備を修正した場合もtrial内だけで、NUMERICAL_VERIFICATIONとlogに最終検算を残した。

補助表のCSV再読ではNULL混在列を明示的に数値/Booleanへ変換した。raw目的分数や欠測の定義は変えず、evidence class別の373参照感度を追加した。目的分数が同一の77fitでfloat標準偏差の丸め残差だけをpublic summaryで0へ正規化し、raw実験CSVを保持した。
