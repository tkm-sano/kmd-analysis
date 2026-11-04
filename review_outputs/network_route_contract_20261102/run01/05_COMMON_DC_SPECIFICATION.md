# Bの共通Controlled-DC仕様

凍結 `CONTROLLED_MASS_TO_DC_V1`を保持。入力契約・算術kernelはPASS、**現行Bの主比較質量はHOLD**。材料改善・回生・補機・SOC制御を主評価へ追加していない。

## 入力と積分

timestamp_s、speed_m_sは同長の1次元有限配列、2標本以上、速度非負、隣接差厳密1秒。native時刻順を保持し、並替え・補間・padding・重複時刻・欠測を拒否。時刻は当該車両の観測標本であり、出発待機を合成して付けない。軌跡SHA、run入力SHA、mass条件、freezeSHA、pressure条件で結果を識別する。

区間t−1→tについてv=v_t m/s、u=v_(t−1)、ds=v×1秒。加速度を使うなら(v−u)/1だが慣性仕事は隣接運動エネルギー差で厳密に計算する。

|項目|式・値|単位・出典|
|---|---|---|
|Crr|0.005+(0.01+0.0095×(3.6v/100)^2)/p|p=4.5または2.6barの2境界、freeze。中間値なし|
|W1|m×9.80665×Crr×ds|転がり仕事J|
|W2|0.5×1.2041×1.175×v²×ds|空気抵抗仕事J|
|W3|0.5×m×(v²−u²)|並進慣性J|
|W4|0.5×61×(v²−u²)|回転慣性J、61kgを質量条件で変更しない|
|区間DC|max(W1+W2+W3+W4,0)/(0.90×3600)|Wh、4成分の合計後に正値化|
|距離|Σv_t×1|m、右端速度離散化|

W1…4はsigned値をJまたはWhと明記して保存。成分別maxを加算したものやsigned仕事総和はDC総量ではない。平坦、grade0、accepted regen0、turnとauxは境界外null。CdA1.175m²・rho1.2041kg/m³・g9.80665m/s²・η0.90は凍結共通値で、対象車の実測校正ではない。パラメータ原資料・cacheSHAはFREEZEのsource_refs／input_hashesを保持する。

FCD速度積分距離とtripinfo.routeLengthは計量境界が異なるため、両方を保存し差を診断する。終端は最後の観測時刻までで止め、arrivalとの差をterminal_gap_s、未観測電力量をnullで保存。端の欠測を停止0Whで埋めない。主表はOBSERVED_WINDOW_CONTROLLED_DCで、完全帰庫DCと主張する場合は終端が観測された証拠が必要。未確定tailを含む全行程の厳密比較はHOLD。

stock18,000Whは研究上usable仮定の累積会計。negativeならFAIL flag、clampや速度変更なし。gross20,000Whと区別する。経路へのSOC制約や電池枯渇による運行可否を実証したモデルではない。

## B質量と比較可能性

凍結mass会計には旧B0車両1,100kg（pack111.111111kgを含む）＋driver55kg＝**1,155kg**、共通非pack988.888889kg、cargo0がある。これは由来のある候補だが、現行no-window Bの主質量として採用された記録は確認できない。したがって今回のB_main_mass_kgはnull。

候補B1=1,134.797980kg、B2=1,123.888889kgは旧比エネルギー感度であり、Bの主比較へ自動採用しない。T08の条件付きmassは別の材料比較、T09完成massは183行未確定。単体試験1,200kgはfixtureに限る。

216PEは配送需要・積載能力の単位で、kg対応なし。PE→kg換算0件、配達による荷重変化も凍結空荷controlでは未実装。積載を主分析に入れるなら原荷物kg・荷卸し規則・別版が必要。

次段階で現行Bの共通車両・pack含有・driver・cargo0等を正式に採用し、全方式へ同じmassを適用する必要がある。速度生成はlegacy配送vTypeで、材料massは走行動特性を変えず外部DCへだけ入力する条件付き比較である。背景交通なし、seed、道路・stop・出発はrun契約どおり。実EVの積載走行消費と同一視しない。

## 独立検算と主比較

`validate_measurements.py` は別スカラー式と凍結kernelを比較。定速・加速・減速・停止・再発進、同一入力再現、massのみ変更、欠測・NaN・重複・終端未観測を検査。Decimal手計算の10m/s×2秒例も保存。`DC_INDEPENDENT_FIXTURES.csv`、`MEASUREMENT_TEST_CASES.csv` に期待・実測・差を保存。35fixtureは35PASS／0FAILで、地域走行やmass実証ではない。

比較は固定全需要が両方式で完了、両方式が帰庫、観測境界同等、共通mass等が成立した場合のみ効率主比較を受入。未配達や経路不達で低Whになったrunは未完了として保持し、効率改善へ数えない。C−Q Whと個別率平均、Σ(C−Q)/ΣCの加重率を区別する。新しい回生・補機・SOCモデルは独立拡張感度とし主評価を置換しない。

CのT08/T09/bridgeは同一保存速度・共通非pack質量による条件付き感度を継承する。未知部材差δに対し既知削減b−δ、δ=bで質量相殺、δ>bで逆転。完成packの工学的妥当性と量子解析→材料改善は未実証で、A/Bの走行結果へ合算しない。固定軌跡算術には新SUMO不要、材料・pack・積載の実証には別の工学データが必要。
