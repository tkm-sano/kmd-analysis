# 外部観測参照10区間 正式Road Census→SUMO mapping

run ID: `external_observation_formal_mapping_20260827_v1`  
generator version: `1.0.0`

## 一番重要な結論

10/10参照について層別の最終statusを確定した。既存`AUTO_ACCEPT` 8/8は正式mappingへ昇格し、`13200100070`は既存corridorを変えず上下方向を解決した。`13300010260`は指定bboxだけを使った別版ネットワークで再評価し、statusを`RESOLVED`とした。

## 10区間の最終分類

| target区間 | 公式観測区間 | mapping | direction | traffic assignment | final acceptance |
|---|---|---|---|---|---|
| `13200100080` | `13200100070` | RESOLVED | RESOLVED | USABLE | ACCEPTED_FOR_TRAFFIC_ASSIGNMENT |
| `13300010290` | `13300010260` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13400020050` | `13400020040` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13400110100` | `13400110130` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13400110110` | `13400110130` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13400110120` | `13400110130` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13403160330` | `13403160320` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13403160340` | `13403160320` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13403160350` | `13403160320` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |
| `13604210040` | `13604210030` | RESOLVED | MODEL_ASSUMPTION_REQUIRED | PENDING_DIRECTION_ASSIGNMENT | ACCEPTED_MAPPING_ONLY |

集計は `{"ACCEPTED_FOR_TRAFFIC_ASSIGNMENT":1,"ACCEPTED_MAPPING_ONLY":9}` である。

## 8区間の正式昇格

8/8を既存edge列・route identity・実測coverageのまま昇格した。`13403160320`系3件はrelation `11699637`、`JP:prefectural:tokyo`、ref `316`、名称「日本橋芝浦大森線」、7 edge、connection violation 0を保持した。coverageは **58.1%**、被覆長465.3m、未被覆長336.2mであり、100%相当にはしていない。

## `13200100070`の方向

国交省定義の上り=`TERMINUS_TO_ORIGIN`、下り=`ORIGIN_TO_TERMINUS`、原表の起点・終点、relation `4256244`のmember role、SUMO from/to topologyが一致した。正式割当は次のとおりである。

- 上り: `45554540#0;45554540#1`
- 下り: `4854104#1;4854104#2`

GeoJSON座標順、道路名だけ、単独bearingは決定根拠にしていない。

## `13300010260`の限定拡張

固定bboxは `{"east":139.720295799,"north":35.62182519,"south":35.617146755,"west":139.717263428}` である。選択したgoverned wayは108件、restriction relationは11件であり、範囲は自動拡張していない。拡張後coverageは83.6%、被覆長860.4m、未被覆長169.0m、connection violationは0件である。

## 既存66区間への影響

既存66区間は66/66 unchanged、意図しない変更0件である。後段利用可能mappingは前後とも65件である。比較対象にはedge ID、edge分割/topology、lane、speed、route identityを含む。

## connection violation

正式mapping 10/10と各directional corridorのconnection violationは0件である。

## 回帰テスト

作業前57件は57 passed（38.19秒）、作業後は既存57件と新規11件を合わせて68 passed（38.37秒）である。

## 生成・更新した成果物

- `external_observation_final_mapping.csv`: 正式mapping 10件
- `external_observation_mapping_final_edge_evidence.csv`: edge evidence
- `external_observation_final_inventory.csv`: 層別inventory
- `external_observation_network_extension_before_after.csv`: `13300010260`の拡張前後差分
- `ota66_network_extension_regression.csv`: 既存66区間の回帰差分
- `external_observation_final_mapping_qa_summary.json`: QA集計
- `external_observation_final_mapping_manifest.json`: 入出力・設定・ツール・成果物hash
- `reproducibility/outputs/traffic_simulation/road_census_external_extension_20260827_v1`: 版付き限定extract、結合OSM、SUMO network、netconvert実行記録
- `05_src/traffic_simulation/calibration/finalize_external_observation_mapping.py`: 再生成スクリプト
- `05_src/traffic_simulation/validation/test_finalize_external_observation_mapping.py`: 新規テスト11件

## QA要約

- 外部参照: 10/10
- connection violation: 0
- matching threshold変更: false
- 任意の代表edge選択: false
- raw/normalizedをmodel assumptionで上書き: false
- 生成時QA: `PASSED`

## 未解決・利用制約

本依頼で方向確定を求められた`13200100070`以外は、既存候補が方向別正式割当を証明していないため、mappingを採択しても`MODEL_ASSUMPTION_REQUIRED`を維持した。これらの観測系列をSUMO方向別edgeへ流す処理は、方向証拠が追加されるまで保留である。欠測値を0で補完していない。

## 次のtraffic全66区間分類へ進めるか

進められる。既存66 mappingは不変で、外部参照10件のmapping層は確定した。ただし、方向別traffic assignmentへ進められる外部参照は現時点で`13200100070`を参照する1件だけであり、残る9件には方向証拠または明示的な研究仮定が必要である。

## ユーザー側で必要な作業

正式mapping成果物の再生成・検証には追加作業は不要である。残る9件を方向別traffic assignmentへ使用する場合だけ、公式方向証拠の提示またはmodel assumption採否の判断が必要である。

## 要するに

10/10の状態は確定し、8/8候補は正式化、Haneda方向は解決、固定bbox拡張は83.6% coverageで採択条件を満たした。既存66区間・閾値・原典は変わらず、connection violationは0、全68テストは成功である。
