# 経路1：指標仕様

根拠：P/run_b.pyのFraction計算、S各SOURCE_SNAPSHOTのinteger_travel/validateおよびmeasure。目的は最小化。i=input SHAで識別する問題、a=アルゴリズム設定、r=0..9の測定反復。JCは指定古典近似ごとに保持する。初期解との差には必ずinitialと付記する。

|指標|式・単位|分母・集計|欠測・適用範囲|
|---|---|---|---|
|主ΔJ|JC,i−JQ,iar [s]|同一入力・制約での対応差。input内10rep平均→規模内等重み|JCまたはJQ欠測/非可行は差NULL、理由・対象数を併記。B全460が対象、現行予算統制は別HOLD|
|相対改善率|100(JC−JQ)/JC [%]|各入力のJCが分母、個別比の平均を主。比の総和とは別|JC≤0はNULL。JC不在時Jinitialで代用しない|
|補助初期差|ΔJinitial=Jinitial−JQ [s]|同一入力・rep|既存delta_objective_vs_initial_sはJQ−Jinitialなので符号反転。主ΔJへの改名は禁止|
|改善解取得率|sum_r I(acquired & feasible & ΔJ>0)/Nscheduled|設定ごと入力内10rep、その平均 [%]。初期差ならinitialを明示|未取得/非可行は成功0、実行記録自体欠測は未知として上下限[成功/N,(成功+未知)/N]と既知数。QC差NULLを失敗と決めない|
|可行計画取得率|sum I(acquired & feasible)/Nscheduled [%]|保存計画単位（B各設定4,600rep）→入力平均|全保存best36,800可行を確認。全shotsの可行率とは異なる。欠測実行は未知上下限|
|raw-shot可行率|1−invalid/8192 [%]|測定repの全raw shots|invalid count未保存はNULL。selected-bestの可行率100%で埋めない。保存されたactive等のみ|
|最適性gap|100(J−J*)/J* [%]|JQとJCの両方に共通参照J*。各入力内平均→厳密取得入力内平均|J*未証明53件はNULL。J*≤0はNULL。407分母と各規模内分母を明示、全460への外挿禁止|
|最適解一致率|sum I(J=J*)/Nexact-valid [%]|目的値一致。経路文字列一致とは別|参照あり407。未取得は失敗、実行未知は区間、参照なしは対象外。多重最適解を許容|
|試行間ばらつき|sample SD=sqrt(sum(Jr−mean J)^2/(m−1)) [s]、median、IQR=Q.75−Q.25 [s]|同一input×設定×fitの測定repのみ。quantile線形補間。m≥2でSD|m<2はSD NULL。fit間・学習seed間・入力間のばらつきと区別。各nを保存|

数値判定は保存小数をDecimal→共通整数scaleまたはFractionで読み、厳密に再計算する。元NPZはfloat64だがDecimal(str(x))の保存十進数を目的関数の定義値とする実装であり、そこでの比較許容幅εJ=0秒とする。ΔJ>0改善、=0同等、<0悪化。既存CSV float表示だけで一致判定しない。元分数・経路がないJCは同じ入力から厳密再構成できるまで一致判定HOLD。既存古典目的分数は利用可、経路再検証可能性は別記する。

float64の整合性検査に使う絶対1e−7秒（元run_b.py）やsample候補抽出1e−8秒（各measure）、MPSエネルギー差1e−7秒は、目的値が同等とする科学的閾値ではない。精度検査と効果境界を混同しない。近接値はexact deltaも併記し、必要なら表示精度感度として別表にするが、任意の1秒改善を成功定義にしない。

独立性：36,800行は独立観測ではない。10repは同一fit、8設定は同一入力、入力は26親・25需要groupに依存。CへこのID/分母を転用しない。Bは省電力最適化でも定時率実験でもない。
