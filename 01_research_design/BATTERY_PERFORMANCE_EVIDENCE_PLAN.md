<a id="battery性能根拠調査と凍結authorityへの索引"></a>

# 電池性能根拠調査と凍結正本への索引

更新2026-09-26。現在・劣化・技術容量の根拠調査COMPLETED、容量/健全度/技術換算/感度設計固定済みである。想定条件実行は未着手である。旧計画のbefore 保存時点の記録は新正本のplanning_beforeに保存した。

<a id="採用したauthority"></a>

## 採用した正本

- [電池 想定条件 正本](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SCENARIO_AUTHORITY.md)：車種、式、仮定、第0段階引渡し、主張 boundaries。
- [全条件と根拠 chain](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SCENARIOS.json)：CURRENT20、DEGRADATION_1=15、DEGRADATION_2=13、TECHNOLOGY_CAPACITY=80/3 kWh。
- [出典 確認](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SOURCE_REVIEW.md)と[追加登録簿](../reproducibility/config/traffic_simulation/evidence/battery_scenario_sources_20260926_v1.yml)：採否、版、適用範囲、URL、snapshot/hash。
- [感度設計](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SENSITIVITY_DESIGN.md)：10点、0.1比率刻み＋代表基準。
- [未決事項](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/OPEN_DECISIONS.md)：実車充電出力、第0段階全体、後続次元。

## 採用方針と限界

基準は凍結済み三菱ミニキャブ電気自動車 CD20.0kWh・2座・急速充電option・ZAB-U69V/HLDDIの2026年9月catalogue仕様である。メーカー総量20kWhをモデル容量とする仮定と、AC WLTC127Wh/kmを距離比例電力量係数へ用いる代理指標を分離した。usable20や実配送定数とはしない。

公的劣化条件はMLIT2024の小型貨物SOCE75%/65%をモデル健全度へ移用する。平均実車劣化・選択車両への現行法適用とはしない。技術容量はNEDO2020方針の2025/2030全固体pack密度目標比4/3を規格化して移用する。原表は容量一定・軽量化の例であり、当研究の質量一定・容量増加は別仮定である。NEDOの将来Minicab予測ではない。

全量の出典 出典・来歴、モデル 役割、仮定、換算、限界を別欄で記録する。B_max/SOH/P_charge/rを単一得点へまとめず、effective容量へ健全度を二重適用しない。初期100%、最低10%は各effective容量に対する研究仮定である。

## 次の工程

[研究段階](RESEARCH_STAGE_ROADMAP.md)に従い、次は完全な第0段階 正本の定義である。第0段階 電池=現行。検証用10kWは転用しない。実車実効PはUNRESOLVED_DEFERREDであり、凍結q0経路だけから全探索空間のP不要を断定しない。経済価格は今回調査していない。

第0段階定義→同一条件C/Q→第0段階評価/固定→劣化C/Q→技術C/Q→条件差と手法差の分離→感度分析である。[想定条件比較](BATTERY_SCENARIO_COMPARISON_PLAN.md)、[C/Q比較](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)、[二系統接続](BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)を維持する。量子化学は将来の別trackであり、電池 kWhへの直接換算をしない。新しい科学実行0、停止。
