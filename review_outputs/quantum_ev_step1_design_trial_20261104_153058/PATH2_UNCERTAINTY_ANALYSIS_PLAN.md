# Step 2：経路2の感度・不確実性

主対象は決定論的条件付き伝達。T08主、T09構造補完、Controlled-DC固定軌跡。モデル内で入力を動かした49点は49独立実験ではない。未知部材に確率分布を与えず、境界δ=bとその両側を決定論的に評価する。

|区別|推定/表示対象|Step2仕様|
|---|---|---|
|軌跡間分布|固定パラメータ下の460軌跡におけるΔE、個別率|trajectory SHA単位でLP/Sと2Crrを対応保持。規模別mean/median/SD/IQR/min/max、Σ差/Σ基準と平均個別率を併記。R0/R1 method参照は別表|
|パラメータ感度|q、u、V、loading、porosity等による決定論的曲面|保存範囲内の連続感度と零境界。既存q49点とu49点、各固定条件を再利用。二変数u×V等は新計算候補、外挿をしない|
|未知部材境界|ΔM=b−δの成立/消失/逆転|T08 additionalとT09未知部材差の内訳を固定。δ=b−1kg,b,b+1kg等は境界を可視化するdiagnostic（成功率目標ではない）。B015/B051を混ぜない|
|構造的不確実性|T08固定部材とT09面積連動部材の違い|共通Egross/V/u/q/NP/qneg/fractions等を一致させ、会計境界の揃う成分差だけ比較。完成パック差や実証validationとしない|
|統計的推定不確実性|同様の需要群へ一般化する仮想感度、あるいは実測入力の誤差|主解析は有限cohort記述。希望する場合のみ25group bootstrap、全軌跡のLP/S/Crr/parameter gridを一緒に再標本化。実測誤差分布の証拠がないq/u/δにはCIを付けない|

既存実施：P/C_T08_PAIRED_DIFFERENCES.csv、C_CONDITIONAL_MASS_DC_SUMMARY.csv、CLUSTER_SENSITIVITY_INTERVALS.csv、T/PATH2_SENSITIVITY_RESULTS.csv・SUMMARY.csv、UTILIZATION_CONTINUOUS.csv、BOUNDARY_RESULTS.csv、OPERATION_INTERACTIONS.csvが存在する。Tのq感度は460×2Crr×49=45,080行。これらの行数は独立標本数ではなく評価格子×対応入力の数。

Step2ではhash/PKとpair key(trajectory SHA,Crr,scenario)を検証し、端点・identical controlのΔ=0を確認。質量差→DC符号の成立は保存mass区間内の正値化branchを含む感度で評価する。ΔM=0なら同一軌跡・同一全条件でΔE=0、ΔM>0だけから全ての運行条件で厳密ΔE>0とは外挿しない。既存正傾き確認は保存区間・Crr条件内の結果。

走行条件別は距離/停止再発進/速度/加速指標を保存速度から算出し、規模/parent/groupと併記。共通軌跡の条件差として分布を記述し、単相関から運転条件の因果効果を断定しない。Crr2値を同じtrajectoryの反復測定として独立化しない。未観測tail、回生/補機/勾配、未知BOM、密度transfer、材料の実現性、道路受入を別々のHOLDとして残す。

任意0.25%等は既存例示の出典としてのみ保存し、新しい成功基準・必要性能へ置き換えない。統計的有意差を経路2成立の要件にしない。
