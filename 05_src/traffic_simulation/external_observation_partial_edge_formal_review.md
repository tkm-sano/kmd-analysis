# 国道1号 partial-edge mapping 正式再レビュー

## 結論

国道1号 `13300010260` のUP側14-edge列を
`ACCEPTED_AS_PARTIAL_EDGE_MAPPING` と判定する。edge列は変更せず、末尾
`542890137#0` の使用範囲だけを `PARTIAL_END_EDGE` の `0–14.073 m` とする。

14.073 mは公式Road Census境界値ではない。方向解決済みDOWN corridorの始点
`DOWN_CORRIDOR_START` をSUMO edgeへ
`PROJECT_OPPOSITE_DIRECTION_BOUNDARY_TO_EDGE_V1` で投影した導出値である。

## 固定基準による判定

- partial-edge coverage: 0.840896（既存閾値 0.600000）
- candidate/fixed axis coverage: 0.728822 / 0.736383
- endpoint difference / projection error: 17.968 m / 17.968 m（既存閾値 25.000 m）
- connection violation: 0
- route identity / topology / contamination: PASS / PASS / PASS

旧判定 `BOUNDARY_GEOMETRY_MISMATCH` / `REVIEW_REQUIRED` は
`03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826/external_observation_route1_boundary_review.csv` に変更せず保持した。新判定は別reviewとして追加した。
Google Maps等の目視情報は正式判定に使用していない。

## 9 target inventory

実成果物を再集計した結果、双方向割当可能は 6 件
（国道1号1、都道2号1、都道11号3、都道421号1）、方向未解決は
3 件（都道316号3）である。したがって次の主要な
未解決対象は都道316号である。

## 下流接続

edge-level consumerは既存edge列を読み続ける。空間対応、coverage、boundary、endpoint、
空間集計、mapping QAだけが `03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826/external_observation_partial_edge_mapping_v1.csv` をjoinする。partial edgeを新しい
SUMO edgeとして扱わず、観測交通量をedge数または使用長で按分しない。
