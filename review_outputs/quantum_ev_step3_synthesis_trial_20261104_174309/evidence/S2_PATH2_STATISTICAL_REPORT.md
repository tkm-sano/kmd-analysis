# 経路2：感度・境界・走行条件

 C旧古典460軌跡×2Crrを対応保持し、144パラメータcase、132,480行を計算した。q49点、u9×V9=81点、共通固定部材3点、追加部材相殺3点、T09既知差のmass probe8点。全て決定論的モデル出力であり独立実験数ではない。T09共通入力構造感度は別162行。

 デフォルトT08端点：

 |rolling_case|trajectories|delta_mass_kg|delta_sum_Wh|total_weighted_saving_percent|mean_individual_saving_percent|sd_individual_saving_percent|min_individual_saving_percent|max_individual_saving_percent|mean_transfer_K_EM|mean_transfer_K_Eq|
|---|---|---|---|---|---|---|---|---|---|---|
|CRR_LOWER_BOUND|460|5.448297|5941.556|0.412579|0.4093294|0.01217239|0.3672604|0.4307705|0.8565055140823102|0.029210991936681502|
|CRR_UPPER_BOUND|460|5.448297|6102.033|0.4135904|0.410435|0.01201783|0.3676733|0.4314989|0.8588189862421535|0.02928989255727975|

 削減率のSDは軌跡間のpercentage points。総和比と個別率平均は別推定対象。25group感度区間は：

 |rolling_case|groups|point|lower95|upper95|resamples|
|---|---|---|---|---|---|
|CRR_LOWER_BOUND|25|0.412579|0.4097784|0.4152567|10000|
|CRR_UPPER_BOUND|25|0.4135904|0.4107746|0.4162839|10000|

 この区間は仮想需要group再標本化の感度で、材料・モデル誤差・未知BOMの確率分布ではない。

 元mass式からb=5.448297415076934kg、u*=0.8770940719841043、V*=3.193155683779789Vを再現した。旧float順序値との差約1e-14kgは検算許容内。delta=bでは920対応caseのDC差も0、b±1kgでは符号反転。1000〜1250kg内で各軌跡のDC(m)はstrictly increasing、全920の最小導関数は0.827572647958Wh/kg。質量差とDCゼロ境界の一致はこの範囲・固定物理条件に限定する。

 改善伝達率K_EM=(DeltaE/E_LP)/(DeltaM/m_LP)とqのみのK_Eq=(DeltaE/E_LP)/((q*u−qLP)/qLP)を無次元比として定義。ゼロ分母はNULL、u/Vを同時に変えたcaseへ単一材料因果効果として適用しない。端点ではK_EMの軌跡平均約0.857/0.859、K_Eq約0.0292。実材料の実現性能を推定したものではない。

 T09は固定loadingとLP固定areaで既知差bが9.722608121107783kg/5.977891152148871kgへ変わる。共通E/V/u/q/NP/fractionsで部材差を算出したが、完成packはNULLのまま。T08との絶対質量比較・実証validationには用いない。

 走行条件は距離、再発進、moving平均速度、正dv2和でquartile分布を保存。PATH2_OPERATION_CONDITION_ANALYSIS.csv/STRATA.csvを参照。W1/W3と正値化branch補正を含み、Crrはtrajectory内対応。規模/parent/需要groupの交絡を残すため、相関を運転介入の因果効果としない。旧C460を新B460へ結び付けない。
