# External traffic observation final inventory specification

## Status axes

`direction_evidence_status`、`opposite_mapping_status`、`traffic_assignment_status`、
`calibration_usability_status`を独立して管理する。

direction解決は、反対車道mappingの正式採択、traffic assignment利用可能性、
calibration利用可能性を自動的には意味しない。

各statusは以下の異なる判断を表す。

- `direction_evidence_status`
  - official observation sectionのUP / DOWN方向を正式に決定できているか
- `opposite_mapping_status`
  - 反対方向carriagewayをSUMO network上で正式に対応付けできているか
- `traffic_assignment_status`
  - 観測交通量をSUMO上の対応方向へ正式に割り当て可能か
- `calibration_usability_status`
  - 当該観測値をcurrent calibrationに使用可能か

これらを混同せず、各段階の未解決理由を独立して保持する。

---

## Nine-target final inventory

| target | direction | opposite mapping | assignment | calibration |
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

## Recomputed counts

9 targetの最終集計結果は以下である。

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

assignment可能targetが6件である一方、current calibration usableが5件である差は、
国道1号がhistorical observationであり、current calibrationには使用しないためである。

---

## 国道1号 `13300010290`

国道1号はdirection、mapping、双方向traffic assignmentとも正式利用可能である。

反対方向carriagewayのmappingにはpartial-edge方式を使用する。

- official observation section: `13300010260`
- target: `13300010290`
- selected direction: `RESOLVED_DOWN`
- selected role: `DOWN_ORIGIN_TO_TERMINUS`
- opposite role: `UP_TERMINUS_TO_ORIGIN`
- opposite mapping status: `ACCEPTED_AS_PARTIAL_EDGE_MAPPING`
- traffic assignment status: `BIDIRECTIONAL_ASSIGNMENT_AVAILABLE`

UP側edge sequenceは14 edgeのまま保持する。

末尾edge `542890137#0`のみ、

- coverage role: `PARTIAL_END_EDGE`
- start position: `0 m`
- end position: `14.073 m`

として部分使用する。

`14.073 m`は公式Road Census境界値ではない。

方向解決済みDOWN corridor始点を反対方向SUMO edgeへ投影した、
再現可能なderived valueである。

partial-edge情報は、

`external_observation_partial_edge_mapping_v1.csv`

へのreferenceとして保持し、新しいSUMO edgeは生成しない。

国道1号の正式partial-edge review結果は以下である。

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

一方、公式raw traffic seriesの観測日は2019-11-20である。

したがって、

- observation type: `HISTORICAL_EXTERNAL_VALIDATION`
- calibration weight: `0`
- calibration usability: `VALIDATION_ONLY`

として保持する。

2021 current observationへsilent substitutionしない。

---

## 都道316号 `13403160330 / 13403160340 / 13403160350`

都道316号3 targetはすべてdirectionを正式解決済みである。

- direction evidence status: `RESOLVED_UP`
- selected role: `UP_TERMINUS_TO_ORIGIN`
- opposite candidate role: `DOWN_ORIGIN_TO_TERMINUS`

したがって、これらを今後 `direction unresolved` と扱わない。

残っている問題は反対方向carriagewayのspatial correspondenceである。

route identity、relation membership、topology、direction、contamination、
oneway structure、target boundary consistencyはいずれもPASSしている。

一方、既存のspatial adoption criteriaを満たさない。

正式review結果：

- alternate official geometry coverage: `0.503218`
- selected / alternate mutual coverage: `0.000000 / 0.000000`
- opposite endpoint distance: `33.774 m / 55.979 m`
- corridor minimum separation: `27.159 m`

既存基準：

- coverage `>= 0.60`
- endpoint / projection distance `<= 25 m`

を変更せず適用した結果、3 targetとも、

- opposite mapping status: `REVIEW_REQUIRED`
- traffic assignment status: `REVIEW_REQUIRED`
- calibration usability status: `REVIEW_REQUIRED`

とする。

正式reasonは、

`SPATIAL_CORRESPONDENCE_BELOW_EXISTING_ADOPTION_CRITERIA`

である。

これはdirection evidence不足、route identity conflict、topology conflict、
contaminationによる未解決ではない。

また、両端不一致と横方向分離を伴うため、端部切詰めのみを扱う既存partial-edge仕様では解決しない。

---

## final_traffic_observations.csv

`final_traffic_observations.csv` は、公式raw `zkntrf13.csv`から
対象観測地点の公開時間値を読み、9 targetへ展開したmachine-readable observation inventoryである。

最終行数は `240` 行である。

国道1号は24時間観測、他のcurrent observation地点は公式12時間観測
（7時から18時）である。

未公開夜間値は補完しない。

small / large vehicle classは公式cross-section単位で合計し、
`raw_observed_value`と`normalized_observed_value`は同値として保持する。

観測値に対して以下を行わない。

- mapped edge数による除算
- one-to-many targetへの按分
- historical値によるcurrent値の置換
- DATA_NOT_AVAILABLEへの推定補完

one-to-many targetについては、同一cross-section observation seriesを
各targetへそのまま反復する。

この方針は、

`REPEAT_OBSERVATION_SERIES_WITHOUT_DIVISION`

として扱う。

---

## Partial-edge handling

partial-edge mappingはSUMO networkを物理的に変更する仕組みではない。

partial-edgeは主として以下に使用する。

- observation sectionとの空間対応
- coverage計算
- boundary判定
- endpoint correspondence
- 空間集計
- mapping QA

traffic assignment、simulation、edge-based traffic countでは、
車両は元のSUMO edge上に存在する。

したがって、

`partial edge = new SUMO edge`

とは解釈しない。

edge sequenceとedge segment specificationを分離して保持する。

---

## Observation value policy

観測値について以下を正式方針とする。

- cross-section valueを保持する
- mapped edge数で除算しない
- one-to-many targetでは同じobservation seriesを反復する
- historical observationはcalibration weight `0`
- historical observationをcurrent observationへsilent substitutionしない
- DATA_NOT_AVAILABLEは推定値で補完しない

current observation、historical validation、data not availableを
共通schemaで扱う。

`HISTORICAL_EXTERNAL_VALIDATION`はcurrent calibrationには使用せず、
外部validation用途に限定する。

---

## Canonical output location

canonical final external-observation artifactsは以下に生成する。

`03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826/external_observation_finalization_20260827/`

canonical artifactsは以下である。

- `external_observation_final_inventory.csv`
- `final_traffic_observations.csv`
- `final_traffic_observation_status_summary.json`
- `external_observation_final_inventory_validation.json`
- `external_observation_final_inventory_manifest.json`

schemaは以下を使用する。

`reproducibility/config/traffic_simulation/final_traffic_observations.schema.json`

generatorは以下である。

`05_src/traffic_simulation/calibration/formalize_external_observation_inventory.py`

reusable validatorは以下である。

`05_src/traffic_simulation/validation/validate_external_observation_final_inventory.py`

---

## Legacy / superseded artifacts

`road_census_sumo_mapping_20260826/`直下に存在する、

- `external_observation_final_inventory.csv`
- `final_traffic_observations.csv`
- `final_traffic_observation_status_summary.json`
- `external_observation_final_inventory_manifest.json`

等の同名または類似成果物は、
finalization以前のworkflow段階で生成されたlegacy / superseded artifactsである。

これらはtraceabilityのため削除せず保持する。

ただし、downstream calibration、validation、正式集計では使用しない。

downstream処理は必ず、

`external_observation_finalization_20260827/`

配下のcanonical artifactsを参照する。

canonical / legacyの区別によって、旧statusと最新statusを混在させない。

---

## Provenance and non-mutation policy

最終inventoryは既存のmachine-readable evidenceから再構成する。

主要inputには以下を含む。

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

manifestにはinput / output hashを保持する。

既存の、

- SUMO network
- formal mapping
- direction成果物
- adoption review成果物
- config
- thresholds

は本finalization処理によって変更しない。

結果に合わせてthresholdを変更しない。

---

## Validation

canonical final inventoryに対する検証結果は以下である。

- automated tests: `14 passed`
- reusable validator: `PASSED`
- validation error count: `0`
- target count: `9`
- final traffic observation rows: `240`

reusable validatorでは少なくとも以下を検証している。

- 9 unique targets
- 240 observation rows
- direction resolved count = `9`
- bidirectional assignment available count = `6`
- current calibration usable count = `5`
- Route316 target count = `3`
- Route316 direction = `RESOLVED_UP`
- Route316 traffic assignment = `REVIEW_REQUIRED`
- Route316 calibration usability = `REVIEW_REQUIRED`
- raw observed valueとnormalized observed valueが同値
- historical observation rows = `48`
- historical calibration weight = `0`
- schema validation
- manifest input hash consistency
- manifest output hash consistency
- non-mutation contract

最終validator実行結果：

- status: `PASSED`
- error count: `0`
- target count: `9`
- observation row count: `240`

以上をもって、
`external_observation_finalization_20260827/`配下の成果物を
external traffic observation final inventoryのcanonical outputとする。