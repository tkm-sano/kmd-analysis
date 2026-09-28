<a id="大田区-road-censussumo-現状ベースライン"></a>

# 大田区道路交通センサス→スーモ現状ベースライン

基準日: **2026-08-27**  
baseline ID: `road_census_sumo_ota_20260827`  
機械可読正本: `reproducibility/config/traffic_simulation/road_census_sumo_baseline_20260827.json`

## 判定

本資料は既存成果物を再実行・変更せず、section 識別子単位で段階的レビュー結果を重ねて再集計したスナップショットである。部分工程の件数を66区間全体の件数として扱わない。

## 現状値

| 項目 | 66区間全体の現状 |
|---|---:|
| 最終 対応付け一意 | 66/66 |
| 後段利用可能対応付け | 65/66 |
| 後段利用不可対応付け | 1/66（`13200510020`） |
| Road Census属性正規化 | RESOLVED 65 / UNRESOLVED 1 |
| 最終 対応付け対象道路区間 | 1482 unique edge |
| 車線 | NO_ASSUMPTION_NEEDED 40 / MODEL_ASSUMPTION_REQUIRED 19 / DATA_CONFLICT 2 / UNRESOLVED 5 |
| 速度 | NO_ASSUMPTION_NEEDED 55 / DATA_CONFLICT 10 / UNRESOLVED 1 |
| traffic comparison | NO_ASSUMPTION_NEEDED 34 / MODEL_ASSUMPTION_REQUIRED 1 / DATA_NOT_AVAILABLE 11 / UNRESOLVED 20 |
| 外部観測対応付け処理漏れ | 10/10を正式状況化済み（品川区7 / 世田谷区3）。対応付け RESOLVED 10、方向 RESOLVED 1 / MODEL_ASSUMPTION_REQUIRED 9、交通 割当 USABLE 1 / PENDING 9 |
| final inventory | 330セル未生成 |

## 旧計画値からの訂正

- 後段利用可能対応付けは64/66ではなく、現行まとめに基づき **65/66** とする。
- 車線の38/17/4は59区間だけを対象としたrefinement中間値である。66区間へ初期一覧と最終 確認を統合した現状値は **40/19/2/5** である。
- 速度の31/0/10は41区間だけを対象としたrefinement値である。66区間全体では **55 NO_ASSUMPTION_NEEDED / 10 DATA_CONFLICT / 1 未解決** である。
- 交通の11 DATA_NOT_AVAILABLE / 15 未解決は追加調査26区間だけの値である。66区間全体の現行分類は上表のとおりであり、最終交通 taxonomyではない。

## 未完了ゲート

- 正本 経路 同一性の全66区間・対象道路区間への確定
- Census上下方向とスーモ directed 道路区間列の正式対応
- 外部観測10件の対応付け層は完了。残る9件の上下方向は`MODEL_ASSUMPTION_REQUIRED`であり、方向別交通 割当には公式証拠または明示的研究仮定が必要
- 交通 66区間の目的別最終taxonomy
- 車線、速度、経路、方向、交通の330セル一覧
- 3正式コンマ区切り形式のデータ構造、出力 実行器、QA、再生成成果物一覧

既存の`census_section_final_mapping.csv`は中間対応付けとして存在するが、計画が要求する未加工・normalized・採用済み・出典・来歴を備えた正式契約は未完成である。`final_sumo_road_attributes.csv`と`final_traffic_observations.csv`は未生成である。

## 集計規則

1. `assumption_inventory.csv`の66区間を初期母集団とする。
2. 車線は59区間refinement、続いて21区間最終 確認をsection 識別子で上書きする。
3. 速度は41区間refinementを上書きし、`SOURCE_CONFLICT`を`DATA_CONFLICT`として表示する。
4. 交通は32区間最終 確認、続いて26区間availability 監査を上書きする。
5. 入力値、対応付け閾値、欠測値は変更しない。

入力ファイルとSHA-256は機械可読正本の`source_manifest`に記録する。

<a id="外部観測mapping正式化2026-08-27"></a>

## 外部観測対応付け正式化（2026-08-27）

- 既存`AUTO_ACCEPT` 8/8を、道路区間列と網羅率を変更せず正式対応付けへ昇格した。
- `13200100070`は上りを`45554540#0;45554540#1`、下りを`4854104#1;4854104#2`として確定した。
- `13300010260`は指定bboxだけを使う版付き別道路網で再評価し、網羅率 83.5796%、未被覆169.045m、接続 violation 0で`RESOLVED`とした。
- `13403160320`系3件の網羅率は58.0542%のまま保持し、未被覆336.185mを記録した。
- 既存66区間は道路区間 識別子、道路区間分割/接続構造、車線、速度、経路 同一性の変更0、後段利用可能対応付けは65/66のままである。
- 作業後回帰は既存57件と新規11件の計68件が成功した。

正式成果物の正本は`external_observation_final_mapping_manifest.json`である。
