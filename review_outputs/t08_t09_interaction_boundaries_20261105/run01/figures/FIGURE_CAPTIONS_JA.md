# 図の条件とデータ由来

全図は新規の条件付き設計探索で、対象パックの測定値ではない。正の差はLP−S。画像と同名PDFを保存。

- T08_BOUNDARY_MAPS：横軸q[Ah/kg]またはu[1]、縦軸V[V]・u[1]・追加質量[kg]。色は条件付きパック差kg、黒線は解析的相殺境界。E=20kWh、LPはq171.875/u1/V3.5、Sの他条件は基準固定。源泉INTERACTION_RESULTS.csv、BOUNDARY_SURFACES.csvと同じ解析式。材料入力は逆算参照と仮定。
- T09_LOADING_POROSITY：担持量mg/cm²（活物質/片面塗工面積）と既知小計差kg。LPはL10mg/cm²・ep/en=.25固定、Sのen=.25固定でepを比較。既知材のみ、外装/タブ/構造等は未確定、完成質量HOLD。固定面積方針のL変更はS基準面積の変更で、全LでLP/S同面積を意味しない。源泉INTERACTION_RESULTS.csv。
- DRIVING_INTERACTION：距離km、再発進/km、転がり寄与Wh、DC差WhまたはWh/km、並進寄与Wh。基準5.448297415kg軽量化、460保存軌跡×2Crr、凍結DC、回生/勾配/補機等対象外。観測窓限定、依存する軌跡の記述比較。源泉data/BASELINE_OPERATION_RESPONSE.csv。
- FACTOR_IMPORTANCE：局所1%入力の平均DC差Wh（extraのみ.01kgステップ）と、宣言探索範囲の平均DC差幅Wh。CRR_LOWER_BOUND、LP固定、460軌跡平均。u=1は内側微分の接線を表示しu>1設計を採用しない。源泉FACTOR_IMPORTANCE.csv、探索範囲はEXPERIMENT_DESIGN.md。範囲幅は確率不確実性ではない。
- ANODE_AND_UNKNOWN_BOUNDARY：左はN/P[1]、条件付き完成パック差kg、負極容量Ah/kg別、fn=.98固定のSのみ再設計。源泉data/ANODE_DESIGN_COMPARISON.csv。右はT09未知部材差kgと完成パック差kgの記号式bK−δU。LP/S絶対未知量を0にしていない。L=.1kg/m²・ep/en=.25、基準既知差を使用し、絶対質量/DCはHOLD。
