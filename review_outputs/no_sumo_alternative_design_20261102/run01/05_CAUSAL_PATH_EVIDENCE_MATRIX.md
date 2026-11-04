# 因果経路の証拠対応

OBSERVEDは保存された計算実行／文献測定を含むが、観測対象を列で明記する。DERIVEDは入力から再計算可能、CONDITIONALはモデル仮定、UNTESTEDは未検証接続、INVALIDは既存不適合。PASS等の監査判定と別軸であり、モデル内のDERIVEDを実世界因果実証にしない。

|ID|接続|証拠分類|主張可能な範囲|未検証|
|---|---|---|---|---|
|P1-01|計算方法→取得状態・route・CPU時間|OBSERVED|CPU simulation outputs, not QPU or real fleet|Hardware acquisition performance UNTESTED|
|P1-02|route→目的値・gap・距離|DERIVED|Input-bound numerical optimization, not native trajectory|53 exact refs unavailable; full new analysis not run|
|P1-03|取得・仮想利用可能→採用・切替・出発|CONDITIONAL|Operational timing scenario, not measured quantum availability|Actual dispatch behavior unvalidated|
|P1-04|出発・訪問順→固定OD配送完了|CONDITIONAL|Ideal uninterrupted service and departure-independent costs|Signal/congestion/reachability not modeled|
|P1-05|モデル完了→固定OD定時率|CONDITIONAL|Model timing mechanism and waiting absorption|Not observed customer handover|
|P1-06|地域道路→妥当な地域速度・配送|INVALID|Network remains unaccepted|No new repair/diagnostic; no accepted regional run|
|P1-07|B計画→B速度軌跡・DC|UNTESTED|No B energy-saving claim|Route recovery alone insufficient; mass HOLD|
|P2-01|文献材料試験→保持容量・保持率|OBSERVED|Published lab conditions, not quantum-generated performance|Full-cell/pack transfer unvalidated|
|P2-02|容量・保持率→参照比容量|DERIVED|Retention back-calculated proxy|Initial practical q_ref HOLD|
|P2-03|材料・設計入力→T08mass/T09既知部材|CONDITIONAL|Distinct design models, not two completed packs|Unknown BOM and footprint FAIL retained|
|P2-04|既知mass＋未知δ→全mass差の符号|CONDITIONAL|Cancellation boundary, no invented unknown mass|Complete pack183 unknown|
|P2-05|mass＋保存速度→Controlled-DC差|CONDITIONAL|Fixed trajectory model sensitivity|Regional/vehicle calibration and tail missing|
|P2-06|量子材料解析→対象材料性能改善|UNTESTED|Potential research link only|No causal effect of quantum materials computation|

式・変数・元入力・出力・コード・判定を含む完全表は `CAUSAL_PATH_EVIDENCE_MATRIX.csv`。各source path／SHAは `SOURCE_INVENTORY.csv` と `*_SOURCES.json`、行位置は各検算CSVで対応する。

因果経路1は取得・品質の保存計算と、仮想政策・固定OD配送成果のモデル内介入を接続する。地域速度・実配送・DCへは未接続。因果経路2は文献材料参照→設計会計→未知mass境界→固定速度DCという条件付き接続。入口の量子解析→材料改善と、出口の実EV妥当性は未検証。

QAOA成功64の選択条件を無視した集団効果や、異なるA/B/Cを結合した総合量子効果量を算出しない。実験計算の観測、モデル内反事実、外的妥当性を別の結果表へ分ける。
