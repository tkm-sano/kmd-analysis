# README更新準備計画（2026-11-13）

判定は **HOLD**。今回、README本文は執筆・変更しない。[事実監査](README_FACT_AUDIT.md)の120項目と[実在ファイル索引](FILE_LINK_INDEX.md)を材料とする。最新ユーザー方針を既存コードに実装済みと書くことを避け、[未解決事項](OPEN_DECISIONS.md)の優先ゲートを解消してから本文へ反映する。

## 1. 研究概要

掲載可能：京浜トラックターミナルを起点とする大田区ToC配送、仮想単一拠点、一般配送車両、複数車両・最大2便、D・W・Tの比較。実運行再現ではなく公開地理情報と研究仮定による配送計画比較である。

本実験未実施を冒頭に置く。旧S1限定実行、人工検証、OD整備、並列実装完了を区別する。現行コードがローカル未追跡である状態と、GitHub公開済みの旧内容の差も明示する。

## 2. 研究課題（RQ）・単一仮説・評価式

以下の文言だけを採用し、旧H1〜H3を追加しない。

RQ：京浜トラックターミナルを起点とする大田区内のToC配送において、量子計算は、配送実績を想定するベースライン、従来的な手法、古典最適化計算と比較して、全車両の総走行距離、積込待機時間、配送計画の計算時間という三目的について、どのような性能差とトレードオフを示すか。

研究仮説：量子計算は、古典計算と比較して、積込待機時間と全車両の総走行距離のバランスをより良好に調整できる。

ここに `J_m=0.5D_m/D_A+0.5W_m/W_A`、重み0.5固定、D対BとD対Cの両対応J差について95%CI上限<0という判定方針を置く。Tは別報告。現在のJ実装・統計プロトコルは不一致であり「設計方針、実装統合待ち」と区別する。未適格のD_A/W_Aに数値を補わない。

主規模・主ε/τ・失敗を含む推論対象、両比較と他セルの同時保証の範囲は、実験前のプロトコル更新事項として残す。今回の監査で主規模や仮説を変更しない。

## 3. 共通実験条件

比較条件より前に、S1〜S3の地点/台/バース、60単位/便、最大2便、積込1800秒、作業120秒、準備0秒、8〜20時、初便readyの式、顧客時間窓なし、未使用車両可を表にする。

運行正本はcommon_conditions_v1_1.jsonとcommon/config.pyのpin。道路生成方式は後続Route v2のメタデータが採用状態で、設定中のsame_table_response等は未統合と明記する。全設定を矛盾なく最新と表示するには新しい正本版が必要。

地点数は人物数ではない。凍結需要の元39956/eligible34912/182町丁目、元地点比・最大剰余・SHA256順位・S1⊂S2⊂S3を説明する。人口メッシュによる再配分や旧固定車両割当は現行に含めない。

道路は関東OSM/OSRM5.27.1、静的car profile、有向Route距離/時間、位置情報EPSG:4326。対象区境界と計算graph範囲を分ける。拠点出入口は構内図/OSM上の採用モデルで現地測量ではない。未確認の対象面積・道路総延長は数値を掲載しない。

## 4. 比較条件A〜D

|手法|記載できること|統合待ち・注意|
|---|---|---|
|A|Web調査による実績参照水準。複数資料なら合成参照|旧A2生成器を現行Aとしない。適格D_A/W_A、全体Tは未取得|
|B|VeRyPyのsavings生成を使う有向CW拡張＋共通完成器|標準対称版VeRyPy全体をそのまま実行したとはしない|
|C|OR-Tools Routing＋共通CP-SAT完成器|Routing内制約と物理車両/積込/バース制約を分離、全VRP最適性保証なし|
|D|Huangらを参考にした限定AOA・有限車両日列＋共通完成器|tensor訓練/Qiskit StatevectorのCPUシミュレーション。新量子経路の最終採用0という旧観測を量子改善にしない|

B〜Dの通常実行は各手法内4CPU・4プロセス、各native thread=1。共通完成器、入力、制約、予算、検証を揃える。内部4枝は一つの外側試行。手法間を同時実行してTを測らない。今回の並列実検証は人工6/20地点まで。

## 5. 評価指標と目的関数

Dは全活動便の有向距離mを合計して/1000、WはΣ(load_start−ready)/60、T_programは親入力読込直前から全枝回収・選択・採用計画の二重検証終了まで。負待機は違反、積込作業時間はWへ入れない。T_humanは外部工程参照/推計であり、T_programへ代入しない。

経路探索は既存のε制約と予算制御、評価は最新の2指標JとTの併記、補助分析は観測D/W/T非支配集合、と役割を説明する。Tを経路目的関数に事後定数として加えることを3目的最適化と呼ばない。

旧3指標J、4重み、時間参照60秒は過去限定分析の定義であり、今回の主評価と混ぜない。D_A/W_Aを使える根拠が揃うまではJの実験数値を載せない。

## 6. 実験設計

独立需要family数n、同一需要の外側反復r、内部4枝、量子shotsを分ける。各規模の既存凍結需要は一つである。本番n/r・精度h・最小効果δ・主セル・本番shotsは未確定。

必要数の式、分散の需要間/内分解、需要を共有する対応比較、seedの役割分離・全失敗保持を説明する。予備12×3は暫定設計で未実行。旧S1単発結果を正式予備分散にしない。今後の分散/計算費用は4CPU条件で校正する。

両J差に基づく新仮説判定へ統計設計を更新するまで、旧S2距離D対Cを新しい確認的主比較として記載しない。

## 7. データ・実行コード

READMEには次の小さな対応表を置き、詳細はFILE_LINK_INDEXへ委ねる。

|資産|実在する入口|
|---|---|
|研究計画と差分|research_plan_toc_three_objectives_faceted_20261108.docx、TOC_DELIVERY_SPEC、共通条件文書|
|凍結需要|03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/|
|採用道路/入力|output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S1〜S3/|
|現在の実行設定/CLI|configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json、scripts/run_dwt.py|
|共通完成/検証|src/kmd_toc/pipeline/completion.py、common/validation.py、baseline_a/independent.py|
|評価/集計|src/kmd_toc/dwt/evaluation.py、analysis.py（最新J/CIは統合待ち）|
|標準出力|src/kmd_toc/dwt/standard.py、各保存trialの7製品|
|旧限定結果|Route v2比較CSVとDWT revision_1_3_1（本実験ではない）|
|道路/計画可視化|output/toc_delivery/visualization_20261113_v1/|
|並列検証|output/toc_delivery/cpu_parallel_20261113_v1/|

上表は実在確認済みの資産名・フォルダ表記である。GitHubへ公開済みのリンクとローカル相対リンクは区別する。OSM/PBF/巨大raw/索引の配布条件と容量、外部VeRyPy固定commit、output内の必須コードを説明する。

## 8. 予期される結果

本実験未実施なので「結果」「量子が優れる」という断定を置かない。図1総合、図2 D、図3 W、図4 T、図5〜7 S1〜S3の3目的という指定構成を維持し、すべて「作成予定」と表示する。

各図の軸・単位・色・観測数・CI対象・Aの外部参照表示をDWT_7_FIGURES_SPECと監査§8から記す。Aの文献/仮定範囲は非CIの別記号、T_humanは別枠。単発の旧front画像、OD図、ガントを主実験の7図として並べない。性能差やトレードオフが観測されない可能性も残す。

## 9. 再現方法

実行環境の保存版はPython3.12.11、NumPy2.3.1、SciPy1.16.0、OR-Tools9.14.6206、Qiskit2.1.1、Linux/AMD EPYC9684X。VeRyPy固定commitとOSRM5.27.1/profile/graph/PBFの来歴が別途必要。旧requirements-quickstartだけで現行VRP全体が入るとは記載しない。

以下は**実在CLIから確認した構文で、今回未実行、ゲート解除後の例**。現在のA/J/統計条件で本実験を開始する推奨ではない。出力rootは新規の設定版で指定し、既存出力/登録を上書きしない。

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B scripts/run_dwt.py register --phase pilot --config configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B scripts/run_dwt.py run --phase pilot --config configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B scripts/run_dwt.py analyze --config configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json
```

登録の各method=B/C/Dが対応する実行を選ぶ。旧逐次登録は明示flagが必要。run_dwt_bundle.pyは小規模既定で、限定S1にはinclude-limitedが必要だが、今回起動しない。analysisも既存集計を更新するので今回実行しない。

道路生成口はbuild_route_pair_od.pyであり、build_common_road_od.pyのTable方式は旧診断入口。経路出力はstandard.Geometryがvisualization/data_access.pyとraw経路/ノード索引へ依存する。検証はcommon/validation、第二再計算、dwt/audit、標準形状監査と保存済み検証JSONを対応づける。render_dwt.pyは旧3図の入口で、未完成の7統計図生成コマンドを創作しない。

GitHub公開コード・データ・環境の整備と、登録時source hashが実行時にも一致する手順を確認するまで「一コマンド完全再現」としない。今回の監査ではコマンド、テスト、ブラウザ、実験コードの起動は0。

## 10. 研究の限界と今後の課題

優先順は、Aの適格分母→新J/二比較の統計設計→正本統合→独立需要と試行数→4CPU道路適格性/資源/再現→shotsと量子帰属→主実験→7統計図。

静的道路、現地未測量の入口/建物アクセス、ToC研究仮定、有限候補D、最適性未証明、量子実機未使用、外部参照Aの対象差、T_human未校正、公開cloneの不足を明記する。

## 旧READMEと旧研究の保全案

旧READMEの履歴保存先案は `docs/history/README_before_toc_revision_20261113.md`。これは予定パスで、今回は作成・コピー・移動していない。更新時には現物hashと当時HEADを添え、既存履歴を上書きしない。

旧単一車両TSP・EV/電池・面接研究は専用履歴節から元資料へ案内し、現行の方法/仮説/図/結果から外す。元コード・凍結結果・研究記録の削除は提案しない。

## 更新着手のゲート

P0項目の採用判断、最新A/J/仮説と計画・設定・実装の関係が明文化され、READMEへ「実装済み」「未実装」「未実行」を矛盾なく書ける状態になってから本文を作成する。統計実験が未実施でもそのことを正確に説明するREADMEは可能だが、不適格分母を確定値として載せる更新はしない。今回の結論はHOLDであり、本文の上書き許可も得ていない。
