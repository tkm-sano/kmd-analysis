# Analysis APIと凍結済み結果

## 1. 対象と正式な実装

`src/kmd_quantitative/analysis/` は保存結果の読込み専用APIです。既存の分析ソース・表・freezeは原位置で保持します。物理移動、科学的集計の再実装、新規実験、欠損補完は行いません。

- [method_battery.py](../../src/kmd_quantitative/analysis/method_battery.py)：最終共通Protocol R0/R1。
- [scale_analysis.py](../../src/kmd_quantitative/analysis/scale_analysis.py)：古典6規模の保存表と診断。
- [result_io.py](../../src/kmd_quantitative/analysis/result_io.py)：13の保存ファイルについてSHA256・サイズ・列/キー・行数を検査。返却値は新しいdict/DataFrameです。

統合分析ソース（Hayate保存参照: `01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/analyze_frozen_results.py`、公開ツリー非同梱）と古典Scale×Battery分析ソース（Hayate保存参照: `05_src/literature_analysis/analyze_classical_scale_battery.py`、公開ツリー非同梱）にはトップレベルの検証・集計・書込みがあります。APIはこれらをimportしません。数式をAPIに複製せず、生成済み結果を読みます。

## 2. Method×Batteryの比較構造

正式R0は3顧客、R1は4顧客。各78実験条件で最終標本からR0は78経路、R1は64経路を取得しました。R1の14未取得は配送不可能を意味しません。歴史的R0の40/78取得結果とは別です。

`parent_id, replicate_id` で対応する計画78ブロックから、両側に経路がある64を使用します。26 parent・25 groupに属し、3 subset replicateは独立した量子反復や独立地理標本ではありません。R0/R1で同じ顧客課題でもありません。未取得14の値をゼロにせず、`population()`は除外理由と空欄を残します。

`contrasts()`は64×2 Crr×2比較＝256行。`energies()`は64×2 Crr×3 Battery＝384行。全R0で同一経路、R1で59同一・5異経路。4条件それぞれTゼロ59・非ゼロ5（正1・負4）で、4条件を256独立標本にまとめません。

## 3. 古典6規模の比較構造

n=3,4,5,25,99,125。各78論理インスタンス、合計468論理に対して460実体です。R5は78論理が70実体を参照し、他の規模は各78実体。重複対応を独立サンプルとして数えません。

n≤5はEXHAUSTIVE_PERMUTATIONS / PROVED_OPTIMAL。n≥25はDETERMINISTIC_HEURISTIC_3_SWEEPS_PLUS_HIGHS_ASSIGNMENT_LP / BOUNDED_GAP_NOT_GLOBAL_OPTIMUM。顧客構成、地理、時間窓、解法が異なるため、顧客数単独の因果効果ではありません。大規模側の量子計算結果はありません。

`conditions()`はデポDEP_006、容量216 parcel-equivalent（kgではない）、静的departure=0 s、return deadline=32400 s、TW幅7200 s、顧客service=102 s等の保存条件を返します。実業務の条件を実測したことは意味しません。

## 4. 評価指標

正式freezeの定義：

- Battery saving (%) = `100*(E_B0-E_Bk)/E_B0`。分母は各scale・method・経路・Crr条件のB0 DC Wh。
- D = Classical saving − Quantum saving。
- T = D_R1 − D_R0。主表示単位はpercentage points（pp）。元の正式仮説のkWh応答差と同一ではありません。
- `_Wh`のsaving contrastも保存されていますが、ppと混ぜません。
- 直接の電力量差はQuantum − Classical。saving Dと符号の定義が異なります。

`summary()`は最終freezeの4条件の保存集計です。母数64、中央値0、標準偏差はddof=1。`mean_decimal`は元のDecimal文字列を保持します。T=0は計算性能の同等性、量子優位性、統計的有意差を示しません。

## 5. 古典側の集計単位

`battery_summary()`は24行、各scale×Crr×B1/B2について78論理の削減率分布（percent）。Scale×Battery interactionの集計そのものではありません。

`interaction_summary()`は既存112行を返します。40行のEQUAL_PARENT_MEAN_CONTRASTはブロック内の規模差→parent内3replicate平均→26parent等重みの集計（pp）です。他の72行はREPLICATE_LOGICAL_REDUCTION、UNIQUE_PHYSICAL_REDUCTION、EQUAL_PARENT_REDUCTION（percent）。`summary_type`, `unit`, `count`, `planned_count`, `algorithm_stratum` を保ち、異なる推定対象を混ぜません。B2が元分析の主対象、B1は副対象です。

## 6. 入力ファイル

`result_io.artifacts()`がパス・SHA256・サイズ・schema・保存行数の一覧を返します。ファイルは既存パスで配布する必要があります。主な所在：

| API | 保存入力 |
|---|---|
| freeze / summary | `final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json`, `FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv` |
| population / contrasts / energies | `matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv`, `SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv`, `DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv` |
| routes / battery_summary / interaction_summary | `01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv`, `MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv`, `CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv` |
| methods / conditions / service_diagnostics | `quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv`, `SCALE_INSTANCE_COMPARISON.csv`, `LOGISTICS_SERVICE_SCOPE.csv` |
| battery_conditions / trajectory_validation | `01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json`, `MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json` |

上表のディレクトリ短縮名は `01_research_design/scenario_evaluation/` 配下です。既存結果をコピー・加工した新しいfreezeは作成しません。

## 7. 出力と検査

JSONはdict、CSVは既存Notebookと同じ `pandas.read_csv` のDataFrameを返します。CSVで `raw=True` を指定すると文字列dictのリストになり、Decimalの原文・空欄・行順を保持します。DataFrame表示では空欄がNaNへ変換されますが、ゼロ補完・行除外・再集計はしません。APIはファイル出力を行いません。

欠損はFileNotFoundError、改変はValueError、未登録artifact keyはKeyError。hash確認とschema確認はバイト整合性検査で、モデルの科学的妥当性を新たに証明するものではありません。証拠内の絶対パスや外部ファイル参照は来歴文字列で、自動追跡しません。`root=`は同じ相対配置を復元したディレクトリに指定でき、hashを回避する機能ではありません。

## 8. 利用例

既存Notebook環境を使用し、repository rootで：

```bash
PYTHONPATH=src python -B -c 'from kmd_quantitative.analysis import method_battery as m; print(m.summary())'
python -B tests/test_analysis_api.py
python -B notebooks/test_notebooks.py
```

```python
from kmd_quantitative.analysis import method_battery as mb, scale_analysis as scale

print(mb.freeze()['definitions'])
print(mb.summary()[['rolling_case', 'comparison', 'n', 'units', 'mean', 'zero_count']])
print(scale.routes()[['n', 'planned_logical_instances', 'distinct_physical_instances']])
print(scale.service_diagnostics())
# 保存値のDecimal原文が必要な場合。計算結果の再生成ではない。
saved_contrasts = mb.contrasts(raw=True)
```

この小規模読込みにはSUMO・Qiskit・道路network・全軌跡は不要です。DataFrameにはpandasが必要で、raw/JSONのみなら標準ライブラリです。Notebook全体の環境は [notebooks/README](../../notebooks/README.md)を参照してください。

## 9. Notebookとの対応

[04](../../notebooks/04_quantitative_results.ipynb)はMethod×Battery/R0/R1、[05](../../notebooks/05_scale_analysis.ipynb)は古典6規模の保存結果を新API経由で表示します。既存の表示対象選択・表・アサーションは維持しました。01〜05の実行出力は変更前後で完全一致。00は依存一覧の増加だけを別扱いにしています。教材用QAOAのNOT_ACQUIREDは正式実験結果ではありません。

## 10. Authority・処理区分

FROZEN_RESULTは元の保存値、NOTEBOOK_PRESENTATIONはその表示、SMOKE_TESTはAPI接続検査です。今回はDETERMINISTIC_REAGGREGATIONを公開APIに追加していません。テスト内のDecimal恒等式・件数照合は保存値の整合性確認に限定し、新しい結果や検定を保存しません。

release manifest（Hayate保存参照: `reproducibility/release/RELEASE_MANIFEST.json`、公開ツリー非同梱）と正式source/freezeは変更しません。Phase6の入力hash catalogは再利用の契約であり、過去のauthorityを置換しません。古典側はroute execution、Battery validation、後続Scale×Battery分析の保存記録を区別します。先行validationのNOT_YET_EXECUTEDを後続分析未実施と誤読しません。

## 11. 配送充足の境界

静的可行性、SUMO走行完了、SUMO観測時刻の診断、現実の全需要充足を区別します。古典matched460はL2 COMPLETEでも、L3遅延はR4が73停止/61経路、R5が63停止/55経路、合計136停止/116経路。帰還期限超過はR4=1、R5=3の計4経路です。全域465経路の別診断と混同しません。

APIはこれらを除外しません。native VRPTW全条件再検証はFalse、実業務充足は未検証。電力量を計算できることと配送条件を満たすことは別です。未配送による低消費を省エネルギー達成としません。

## 12. エネルギー境界

20 kWh容量固定、180/220/250 Wh/kgによるパック・車両質量条件、同一軌跡内の比較です。18 kWhは既存残量会計条件。2 Crr境界は圧力変更実験・信頼区間ではありません。DC Whは保存観測区間のみ、平坦・回生なし・補機対象外・エネルギー側積載0 kg・効率一定。充電・計算・通信・設備・製造を含む社会全体のエネルギーではありません。

## 13. 再利用範囲と残課題

Linuxの独立一時配置で、元repositoryへのfileアクセスなし・旧互換リンクなし・SUMOなしで読込みと全6Notebookを検証しました。新規pip構築、Windows、Colab、全量実験の復元は未検証です。全量再計算には未配布のOD・network・専用router/native fork・軌跡・元実験設定等が必要です。

技術候補一覧は PHASE6_GITHUB_FILELIST.csv（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/PHASE6_GITHUB_FILELIST.csv`、公開ツリー非同梱）。これは公開許諾一覧ではなく、権利・配布条件は未確定です。git add/commit/pushは実施していません。
