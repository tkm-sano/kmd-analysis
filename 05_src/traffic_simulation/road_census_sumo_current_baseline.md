# 大田区 Road Census→SUMO 現状ベースライン

基準日: **2026-08-27**  
baseline ID: `road_census_sumo_ota_20260827`  
機械可読正本: `reproducibility/config/traffic_simulation/road_census_sumo_baseline_20260827.json`

## 判定

本資料は既存成果物を再実行・変更せず、section ID単位で段階的レビュー結果を重ねて再集計したスナップショットである。部分工程の件数を66区間全体の件数として扱わない。

## 現状値

| 項目 | 66区間全体の現状 |
|---|---:|
| final mapping一意 | 66/66 |
| 後段利用可能mapping | 65/66 |
| 後段利用不可mapping | 1/66（`13200510020`） |
| Road Census属性正規化 | RESOLVED 65 / UNRESOLVED 1 |
| final mapping対象edge | 1482 unique edge |
| lane | NO_ASSUMPTION_NEEDED 40 / MODEL_ASSUMPTION_REQUIRED 19 / DATA_CONFLICT 2 / UNRESOLVED 5 |
| speed | NO_ASSUMPTION_NEEDED 55 / DATA_CONFLICT 10 / UNRESOLVED 1 |
| traffic comparison | NO_ASSUMPTION_NEEDED 34 / MODEL_ASSUMPTION_REQUIRED 1 / DATA_NOT_AVAILABLE 11 / UNRESOLVED 20 |
| 外部観測mapping処理漏れ | 10/10を正式status化済み（品川区7 / 世田谷区3）。mapping RESOLVED 10、direction RESOLVED 1 / MODEL_ASSUMPTION_REQUIRED 9、traffic assignment USABLE 1 / PENDING 9 |
| final inventory | 330セル未生成 |

## 旧計画値からの訂正

- 後段利用可能mappingは64/66ではなく、現行summaryに基づき **65/66** とする。
- laneの38/17/4は59区間だけを対象としたrefinement中間値である。66区間へ初期inventoryとfinal reviewを統合した現状値は **40/19/2/5** である。
- speedの31/0/10は41区間だけを対象としたrefinement値である。66区間全体では **55 NO_ASSUMPTION_NEEDED / 10 DATA_CONFLICT / 1 UNRESOLVED** である。
- trafficの11 DATA_NOT_AVAILABLE / 15 UNRESOLVEDは追加調査26区間だけの値である。66区間全体の現行分類は上表のとおりであり、最終traffic taxonomyではない。

## 未完了ゲート

- canonical route identityの全66区間・対象edgeへの確定
- Census上下方向とSUMO directed edge列の正式対応
- 外部観測10件のmapping層は完了。残る9件の上下方向は`MODEL_ASSUMPTION_REQUIRED`であり、方向別traffic assignmentには公式証拠または明示的研究仮定が必要
- traffic 66区間の目的別最終taxonomy
- lane、speed、route、direction、trafficの330セルinventory
- 3正式CSVのschema、export runner、QA、再生成manifest

既存の`census_section_final_mapping.csv`は中間mappingとして存在するが、計画が要求するraw・normalized・adopted・provenanceを備えた正式契約は未完成である。`final_sumo_road_attributes.csv`と`final_traffic_observations.csv`は未生成である。

## 集計規則

1. `assumption_inventory.csv`の66区間を初期母集団とする。
2. laneは59区間refinement、続いて21区間final reviewをsection IDで上書きする。
3. speedは41区間refinementを上書きし、`SOURCE_CONFLICT`を`DATA_CONFLICT`として表示する。
4. trafficは32区間final review、続いて26区間availability auditを上書きする。
5. 入力値、mapping閾値、欠測値は変更しない。

入力ファイルとSHA-256は機械可読正本の`source_manifest`に記録する。

## 外部観測mapping正式化（2026-08-27）

- 既存`AUTO_ACCEPT` 8/8を、edge列とcoverageを変更せず正式mappingへ昇格した。
- `13200100070`は上りを`45554540#0;45554540#1`、下りを`4854104#1;4854104#2`として確定した。
- `13300010260`は指定bboxだけを使う版付き別networkで再評価し、coverage 83.5796%、未被覆169.045m、connection violation 0で`RESOLVED`とした。
- `13403160320`系3件のcoverageは58.0542%のまま保持し、未被覆336.185mを記録した。
- 既存66区間はedge ID、edge分割/topology、lane、speed、route identityの変更0、後段利用可能mappingは65/66のままである。
- 作業後回帰は既存57件と新規11件の計68件が成功した。

正式成果物の正本は`external_observation_final_mapping_manifest.json`である。
