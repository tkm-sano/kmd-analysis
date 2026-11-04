# C：材料・質量・固定速度DCの全件結果

算術PASS、科学解釈CONDITIONAL。T08全4,464行（CLASSICAL2,760、R0補助936、R1補助768）、T09全183行、bridge全25,760行を保持。元MATERIAL_ENERGYの744 dataset/method軌跡参照は465固有速度に集約できた。主感度の旧古典460軌跡と、Bの現行460入力を同一視しない。新しいSUMO・材料値・車両条件は追加していない。

## T08

凍結参照qはLP171.875、S200195.959596 Ah/kg（保持率からの逆算参照を丸めた既存値）、利用率1、平均電圧3.5V、gross20,000Wh、usable18,000Wh、負極360Ah/kg、正活物質率0.75、負0.98、N/P1.1。100cell×0.19kg、pack他15kgを含む簡略会計。比容量を量子計算で得た値とはしない。

LP mass96.145654799kg、S200 90.697357384kg、差 **5.448297415kg**。保存速度・共通非pack massでDCを再計算し、下表が個別元行から再現された。初期stock18kWh、補機境界外、回生なし、平坦、61kg回転等価mass、合計後正値化を変更していない。

|Crr|質量削減kg|DC削減総和Wh（460）|総量加重削減%|個別率平均%|
|---|---:|---:|---:|---:|
|CRR_LOWER_BOUND|5.448297415077|5941.555975382|0.412579010061|0.409329419377|
|CRR_UPPER_BOUND|5.448297415077|6102.033288992|0.413590411697|0.410435042400|

同一LP controlの差は全行0。機械成分はW1転がり／W2空気／W3並進／W4回転のsigned値を保存し、成分別正値化へ変更しない。末端未観測区間はunknownで0Wh補完していない。旧N0の地域妥当性FAILを保持し、実EV・実配送での0.412579%削減とは呼ばない。

## T09とunknown mass

183行すべて完成pack massはNULL（HOLD）、全面対向1行はFAILを保持。既知部材は正負塗工材、Al/Cu、separator、liquid。全183行の各成分を独立Fraction式で照合した。case/tabs/foil margin/pack structure等は未実測で、残差で埋めない。T08の固定部材をT09へ再加算しない。

代表pair B015固定担持の既知LP−S差 **9.722608121kg**、B051固定面積の差 **5.977891152kg**。完成pack同士の差ではなく、全設計で一定の普遍的差でもない。設計全条件と部材差はC_T09_COMPONENTS_183、C_COMPONENT_MASS_BRIDGEに保存した。

b=既知LP−S、δ=未知S−LPとして、正味削減はb−δ。δ<bで軽量、δ=bで相殺、δ>bで逆転。未測定のδを0と確定していない。既存equal_unknownsは感度条件の一つである。

## bridge・走行条件

既存reference走行massは1,200／1,400kgのprobeで、T09完成pack massやB共通massではない。旧460速度×2設計×7δprobe×2Crr×2mass=25,760行を再計算。既存条件範囲ではmass/DC符号が一致し、saving11,040、相殺3,680、逆転11,040行。これらは独立試料数ではない。

|設計（δ=0感度）|Crr|参照走行kg|既知削減kg|総量加重DC削減%|
|---|---|---:|---:|---:|
|fixed_loading|CRR_LOWER_BOUND|1200.0|9.722608121|0.704603292|
|fixed_loading|CRR_LOWER_BOUND|1400.0|9.722608121|0.615743639|
|fixed_loading|CRR_UPPER_BOUND|1200.0|9.722608121|0.706063388|
|fixed_loading|CRR_UPPER_BOUND|1400.0|9.722608121|0.616969693|
|fixed_area_LP|CRR_LOWER_BOUND|1200.0|5.977891152|0.433240559|
|fixed_area_LP|CRR_LOWER_BOUND|1400.0|5.977891152|0.378589365|
|fixed_area_LP|CRR_UPPER_BOUND|1200.0|5.977891152|0.434121763|
|fixed_area_LP|CRR_UPPER_BOUND|1400.0|5.977891152|0.379340934|

これはunknownが等しい場合の条件付き値で、T08より完成pack性能が高いという比較ではない。Crr・参照mass・scale別336strataの保存距離／再発進とDC差の記述を `C_DRIVING_CONDITION_SENSITIVITY.csv` に保存。相関を独立した走行条件の因果効果や回帰による校正とは呼ばない。

凍結kernelで20,260固有(trajectory,mass,Crr)を評価。独立のmass線形式との最大差は **2.73e-12Wh**。質量の単純比例はbranch切替があるため一般化せず、既存probeで検証した条件付き関係として報告する。

量子材料解析→材料改善は未実証。文献のVASP/DFTと量子計算機を区別する。完成pack・実車・寿命／安全・対象車校正の接続はHOLDのままである。
