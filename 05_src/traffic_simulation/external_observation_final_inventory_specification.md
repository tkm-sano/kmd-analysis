<a id="external-traffic-observation-final-inventory-specification"></a>

# 外部交通観測最終一覧仕様

<a id="status-axes"></a>

## 状態軸

`direction_evidence_status`、`opposite_mapping_status`、`traffic_assignment_status`、
`calibration_usability_status`を独立して管理する。

方向解決は、反対車道対応付けの正式採択、交通 割当利用可能性、
較正利用可能性を自動的には意味しない。

各状況は以下の異なる判断を表す。

- `direction_evidence_status`
  - official observation sectionのUP / DOWN方向を正式に決定できているか
- `opposite_mapping_status`
  - 反対方向carriagewayを交通シミュレーターの道路網上で正式に対応付けできているか
- `traffic_assignment_status`
  - 観測交通量をスーモ上の対応方向へ正式に割り当て可能か
- `calibration_usability_status`
  - 当該観測値を現行 較正に使用可能か

これらを混同せず、各段階の未解決理由を独立して保持する。

---

<a id="nine-target-final-inventory"></a>

## 九つの-対象最終一覧

| 対象 | 方向 | opposite mapping | 割当 | 較正 |
| --- | --- | --- | --- | --- |
| `13300010290` | `RESOLVED_DOWN` | `ACCEPTED_AS_PARTIAL_EDGE_MAPPING` | `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE` | `VALIDATION_ONLY` |
| `13400020050` | `RESOLVED_DOWN` | `ACCEPTED_AS_OPPOSITE_CARRIAGEWAY` | `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE` | `CALIBRATION_USABLE` |
| `13400110100` | `RESOLVED_UP` | `DIRECT_REVERSE_AVAILABLE` | `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE` | `CALIBRATION_USABLE` |
| `13400110110` | `RESOLVED_UP` | `DIRECT_REVERSE_AVAILABLE` | `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE` | `CALIBRATION_USABLE` |
| `13400110120` | `RESOLVED_UP` | `DIRECT_REVERSE_AVAILABLE` | `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE` | `CALIBRATION_USABLE` |
| `13403160330` | `RESOLVED_UP` | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |
| `13403160340` | `RESOLVED_UP` | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |
| `13403160350` | `RESOLVED_UP` | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |
| `13604210040` | `RESOLVED_DOWN` | `ACCEPTED_AS_OPPOSITE_CARRIAGEWAY` | `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE` | `CALIBRATION_USABLE` |

---

<a id="recomputed-counts"></a>

## 再計算済み件数

9 対象の最終集計結果は以下である。

- target total: `9`
- direction resolved: `9`
- direction unresolved: `0`
- bidirectional assignment available: `6`
- current calibration usable: `5`
- validation only: `1`
- review required: `3`
- direct reverse available: `3`
- opposite carriageway adopted: `2`
- partial-edge mapping: `1`
- route identity failure: `0`
- topology failure: `0`
- contamination failure: `0`
- data conflict: `0`

割当可能対象が6件である一方、現行 較正 利用可能なが5件である差は、
国道1号が過去の記録 observationであり、現行 較正には使用しないためである。

---

## 国道1号 `13300010290`

国道1号は方向、対応付け、双方向交通 割当とも正式利用可能である。

反対方向carriagewayの対応付けには部分的-道路区間方式を使用する。

- official observation section: `13300010260`
- target: `13300010290`
- selected direction: `RESOLVED_DOWN`
- selected role: `DOWN_ORIGIN_TO_TERMINUS`
- opposite role: `UP_TERMINUS_TO_ORIGIN`
- opposite mapping status: `ACCEPTED_AS_PARTIAL_EDGE_MAPPING`
- traffic assignment status: `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE`

UP側道路区間 sequenceは14 道路区間のまま保持する。

末尾道路区間 `542890137#0`のみ、

- coverage role: `PARTIAL_END_EDGE`
- start position: `0 m`
- end position: `14.073 m`

として部分使用する。

`14.073 m`は公式Road Census境界値ではない。

方向解決済みDOWN corridor始点を反対方向スーモ 道路区間へ投影した、
再現可能な導出済み 値である。

部分的-道路区間情報は、

`external_observation_partial_edge_mapping_v1.csv`

への参照として保持し、新しいスーモ 道路区間は生成しない。

国道1号の正式部分的-道路区間 確認結果は以下である。

- coverage ratio: `0.840896`
- endpoint difference: `17.968 m`
- projection error: `17.968 m`
- connection violation: `0`
- route identity: `PASS`
- topology: `PASS`
- contamination: `PASS`

既存採択基準である、

- coverage `>= 0.60`
- endpoint / projection distance `<= 25 m`

は変更していない。

一方、公式未加工 交通 seriesの観測日は2019-11-20である。

したがって、

- observation type: `HISTORICAL_EXTERNAL_VALIDATION`
- calibration weight: `0`
- calibration usability: `VALIDATION_ONLY`

として保持する。

2021 現行 observationへsilent substitutionしない。

---

## 都道316号 `13403160330 / 13403160340 / 13403160350`

都道316号3 対象はすべて方向を正式解決済みである。

- direction evidence status: `RESOLVED_UP`
- selected role: `UP_TERMINUS_TO_ORIGIN`
- opposite candidate role: `DOWN_ORIGIN_TO_TERMINUS`

したがって、これらを今後 `direction unresolved` と扱わない。

残っている問題は反対方向carriagewayの空間的な correspondenceである。

route identity、relation membership、topology、direction、contamination、
一方通行 structure、対象 境界 consistencyはいずれも合格している。

一方、既存の空間的な adoption criteriaを満たさない。

正式確認結果：

- alternate official geometry coverage: `0.503218`
- selected / alternate mutual coverage: `0.000000 / 0.000000`
- opposite endpoint distance: `33.774 m / 55.979 m`
- corridor minimum separation: `27.159 m`

既存基準：

- coverage `>= 0.60`
- endpoint / projection distance `<= 25 m`

を変更せず適用した結果、3 対象とも、

- opposite mapping status: `REVIEW_REQUIRED`
- traffic assignment status: `REVIEW_REQUIRED`
- calibration usability status: `REVIEW_REQUIRED`

とする。

正式理由は、

`SPATIAL_CORRESPONDENCE_BELOW_EXISTING_ADOPTION_CRITERIA`

である。

これは方向 根拠不足、経路 同一性 矛盾、接続構造 矛盾、
混入による未解決ではない。

また、両端不一致と横方向分離を伴うため、端部切詰めのみを扱う既存部分的-道路区間仕様では解決しない。

---

## final_traffic_observations.csv

`final_traffic_observations.csv` は、公式未加工 `zkntrf13.csv`から
対象観測地点の公開時間値を読み、9 対象へ展開したmachine-readable observation 一覧である。

最終行数は `240` 行である。

国道1号は24時間観測、他の現行 observation地点は公式12時間観測
（7時から18時）である。

未公開夜間値は補完しない。

small / large 車種は公式cross-section単位で合計し、
`raw_observed_value`と`normalized_observed_value`は同値として保持する。

観測値に対して以下を行わない。

- mapped 道路区間数による除算
- one-to-many 対象への按分
- 過去の記録値による現行値の置換
- DATA_NOT_AVAILABLEへの推定補完

one-to-many 対象については、同一cross-section observation seriesを
各対象へそのまま反復する。

この方針は、

`REPEAT_OBSERVATION_SERIES_WITHOUT_DIVISION`

として扱う。

---

<a id="partial-edge-handling"></a>

## 部分的-道路区間取扱い

部分的-道路区間 対応付けは交通シミュレーターの道路網を物理的に変更する仕組みではない。

部分的-道路区間は主として以下に使用する。

- observation sectionとの空間対応
- 網羅率計算
- 境界判定
- endpoint correspondence
- 空間集計
- mapping QA

交通 割当、simulation、道路区間-based 交通 件数では、
車両は元のスーモ 道路区間上に存在する。

したがって、

`partial edge = new SUMO edge`

とは解釈しない。

道路区間 sequenceと道路区間 segment 仕様を分離して保持する。

---

<a id="observation-value-policy"></a>

## 観測値方針

観測値について以下を正式方針とする。

- cross-section 値を保持する
- mapped 道路区間数で除算しない
- one-to-many 対象では同じobservation seriesを反復する
- 過去の記録 observationは較正 重み `0`
- 過去の記録 observationを現行 observationへsilent substitutionしない
- DATA_NOT_AVAILABLEは推定値で補完しない

現行 observation、過去の記録 検証、data not availableを
共通データ構造で扱う。

`HISTORICAL_EXTERNAL_VALIDATION`は現行 較正には使用せず、
外部検証用途に限定する。

---

<a id="canonical-output-location"></a>

## 正本出力位置

正本 最終 外部-observation 成果物は以下に生成する。

`03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826/external_observation_finalization_20260827/`

正本 成果物は以下である。

- `external_observation_final_inventory.csv`
- `final_traffic_observations.csv`
- `final_traffic_observation_status_summary.json`
- `external_observation_final_inventory_validation.json`
- `external_observation_final_inventory_manifest.json`

データ構造は以下を使用する。

`reproducibility/config/traffic_simulation/final_traffic_observations.schema.json`

生成器は以下である。

`05_src/traffic_simulation/calibration/formalize_external_observation_inventory.py`

reusable 検証器は以下である。

`05_src/traffic_simulation/validation/validate_external_observation_final_inventory.py`

---

<a id="legacy--superseded-artifacts"></a>

## 旧版 / 後続版に置換済み成果物

`road_census_sumo_mapping_20260826/`直下に存在する、

- `external_observation_final_inventory.csv`
- `final_traffic_observations.csv`
- `final_traffic_observation_status_summary.json`
- `external_observation_final_inventory_manifest.json`

等の同名または類似成果物は、
finalization以前のworkflow段階で生成された旧版 / 後続版に置換済み 成果物である。

これらは追跡可能性のため削除せず保持する。

ただし、downstream 較正、検証、正式集計では使用しない。

downstream処理は必ず、

`external_observation_finalization_20260827/`

配下の正本 成果物を参照する。

正本 / 旧版の区別によって、旧状況と最新状況を混在させない。

---

<a id="provenance-and-non-mutation-policy"></a>

## 出典・来歴 ・ 変更を行わない方針

最終一覧は既存のmachine-readable 根拠から再構成する。

主要入力には以下を含む。

- direction final classification
- direction cluster evidence
- Route316 direction diagnosis
- opposite-carriageway adoption review
- Route316 opposite-carriageway adoption review
- partial-edge formal review
- partial-edge segment specification
- post-partial-edge inventory
- official raw Road Census section data
- official raw traffic series

成果物一覧には入力 / 出力 ハッシュ値を保持する。

既存の、

- 交通シミュレーターの道路網
- formal mapping
- 方向成果物
- adoption 確認成果物
- 設定
- thresholds

は本finalization処理によって変更しない。

結果に合わせてしきい値を変更しない。

---

<a id="validation"></a>

## 検証

正本 最終 一覧に対する検証結果は以下である。

- automated tests: `14 passed`
- reusable validator: `PASSED`
- validation error count: `0`
- target count: `9`
- final traffic observation rows: `240`

reusable 検証器では少なくとも以下を検証している。

- 9 unique targets
- 240 observation rows
- direction resolved count = `9`
- bidirectional assignment available count = `6`
- current calibration usable count = `5`
- Route316 target count = `3`
- Route316 direction = `RESOLVED_UP`
- Route316 traffic assignment = `REVIEW_REQUIRED`
- Route316 calibration usability = `REVIEW_REQUIRED`
- 未加工 observed 値とnormalized observed 値が同値
- historical observation rows = `48`
- historical calibration weight = `0`
- schema validation
- manifest input hash consistency
- manifest output hash consistency
- non-mutation contract

最終検証器実行結果：

- status: `PASSED`
- error count: `0`
- target count: `9`
- observation row count: `240`

以上をもって、
`external_observation_finalization_20260827/`配下の成果物を
外部 交通 observation 最終 一覧の正本 出力とする。
