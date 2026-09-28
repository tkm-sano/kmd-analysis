# 交通シミュレーション・配送最適化コード

このディレクトリは、既存の合成電気自動車配送経路問題分析を上書きせずに、大田区の道路・交通・配送・最適化研究を追加する実装層です。

現在の研究設計は[CURRENT_RESEARCH_DESIGN.md](CURRENT_RESEARCH_DESIGN.md)、意思決定履歴は[RESEARCH_PROGRESS_AND_DECISION_RECORD.md](RESEARCH_PROGRESS_AND_DECISION_RECORD.md)を正本とします。日本語での案内は[R24現行研究設計ガイド](../../docs/ja/R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)を参照してください。

## 現在のR24状態

| 項目 | 状態 |
|---|---|
| 判定段階A〜D | `ACCEPTED_WITH_LIMITATIONS` |
| 経路計算の互換性 | `ACCEPTED_WITH_LIMITATIONS` |
| 最終的な対象顧客母集団 | 顧客39,930件／方法論上の荷物換算量81,793単位 |
| 問題例生成仕様 | `FROZEN_WITH_LIMITATIONS` |
| 性能評価用問題例群 | `GENERATED_WITH_LIMITATIONS` |
| R24の古典計算による容量制約付き配送経路問題の求解器 | `R24_CLASSICAL_REFERENCE_VALIDATED` |
| R24の二値二次最適化・量子近似最適化 | `NOT_EXECUTED` |

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```

R24 問題例 生成のコード:

- [generate_r24_benchmark_instance_suite.py](r24_instance_generation/generate_r24_benchmark_instance_suite.py)
- [validate_r24_benchmark_instance_suite.py](r24_instance_generation/validate_r24_benchmark_instance_suite.py)

R24 古典参照解のコード:

- [r24_classical_reference](r24_classical_reference/): HiGHS 混合整数線形計画、独立厳密 列挙、復号器、独立検証器、検証 実行器
- [検証 試験](validation/test_r24_classical_reference.py): 既知の最適解、容量、非対称性、費用0の区間、破損した解等の単位 検証用データ

検証結果: 厳密解と数理最適化ソルバーの最適値が21/21件で一致、復号解・厳密解の42/42件で 検証合格、最大目的差 `9.999894245993346e-10 s`。全体 ベンチマークは未実行です。

生成済み結果:

- 無作為抽出：80/80件が有効
- 構造条件の統制：27/27件が有効
- 基準問題の別名：3/3件が有効
- 容量条件：330/330件で積載割当が可能
- 退化していない準備済み問題：135件
- 退化した問題：195件
- 経路計算・必須制約の検証失敗：0件

<a id="r20r23-reduced-quantum-pipeline"></a>

## R20–R23 縮約した 量子計算 処理工程

R20–R23は完全な電気自動車配送経路問題ではなく、`INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`に限定した単一車両 訪問順序 調査です。

| 段階 | 状態 | 実装・正本 |
|---|---|---|
| R20の定式化 | `FORMULATION_VERIFIED = PASS` | [r20_route_ordering](r20_route_ordering/) / [R20の仕様](specifications/R20_QAOA_SUBPROBLEM_SPEC.md) |
| R21の二値二次最適化の検証 | `PASS` | [r21_qubo_validation](r21_qubo_validation/) |
| R22のイジング形式への変換 | `PASS` | [r22_ising_conversion](r22_ising_conversion/) |
| R23の量子近似最適化・回路シミュレーション | `CLOSED_WITH_DOCUMENTED_LIMITATIONS` | [R23_STATUS.md](R23_STATUS.md) |

縮約モデルは顧客のみの `n × n` 位置 符号化で、静的な有向移動時間を最小化し、各顧客・各訪問位置をちょうど一度使う制約を制約なし二値二次最適化 罰則項にします。容量、時間窓、電池・充電率、充電、車両群の規模設計は含みません。回路シミュレーションはソフトウェアによる計算であり、量子実機性能や量子優位性の証拠ではありません。

<a id="source-code-boundaries"></a>

## ソースコードの配置範囲

| ディレクトリ | 役割 |
|---|---|
| `network/` | オープンストリートマップ取得、対象範囲の切出し、地図上の対応付け、交通シミュレーターの道路網生成 |
| `demand/` | 時間帯別交通需要・配送需要構築 |
| `calibration/` | 日本道路交通情報センター/道路交通センサス較正・検証 |
| `simulation/` | スーモの設定、実行器、結果抽出 |
| `validation/` | 構造・経験的検証 |
| `r20_route_ordering/` | 縮約した二値二次最適化、厳密参照解、経路計算の変換器 |
| `r21_qubo_validation/` | 縮約した二値二次最適化段階の検証 |
| `r22_ising_conversion/` | 二値二次最適化からイジング形式への変換と同等性検証 |
| `r23_qaoa_aer/` | R23の量子近似最適化・回路シミュレーション基盤 |
| `r24_instance_generation/` | 固定済み R24 検証一式 生成器と独立検証器 |
| `r24_classical_reference/` | HiGHS 容量制約付き配送経路問題 混合整数線形計画、厳密 列挙、復号器、独立した解の検証器 |

新規モジュールは可能な限り`traffic_simulation.paths`の正本の保存先検出を使用し、ホスト固有の絶対パスを埋め込みません。既存の固定実装を変更する場合は、その出典・来歴 境界を明記します。

<a id="data-boundaries"></a>

## データの保存範囲

| データ | 保存先 |
|---|---|
| 未加工入力 | `03_data/raw/traffic_simulation/` |
| 加工済み道路網 | `03_data/processed/traffic_simulation/road_network/` |
| 交通条件 | `03_data/processed/traffic_simulation/traffic_profiles/` |
| スーモの入力 | `03_data/processed/traffic_simulation/sumo_inputs/` |
| 較正データ | `03_data/processed/traffic_simulation/calibration/` |
| 需要データ | `03_data/processed/traffic_simulation/demand/` |
| 検証データ | `03_data/processed/traffic_simulation/validation/` |
| 出典登録簿 | `03_data/metadata/traffic_simulation_sources.csv` |
| 再現可能な出力 | `reproducibility/outputs/traffic_simulation/` |
| 確認済み出力 | `06_outputs/traffic_simulation/` |

付随情報に保存する保存先はリポジトリの最上位からの相対パスとします。

## 主要仕様

- [仕様索引](specifications/README.md)
- [経路計算の基準](specifications/ROUTING_BASELINE_CANONICAL.md)
- [R23の縮約問題](specifications/R23_REDUCED_PROBLEM_CANONICAL.md)
- [R24 問題例生成仕様（日本語）](../../docs/ja/R24_INSTANCE_GENERATION_SPECIFICATION_JA.md)
- [R24 検証一式結果（日本語）](../../docs/ja/R24_BENCHMARK_INSTANCE_SUITE_REPORT_JA.md)

## 運用上の注意

- 既存の固定済み 入出力を暗黙に上書きしない
- 原資料、合成処理、モデル 仮定を区別する
- 到達不能 費用を0や任意の有限 罰則項へ置換しない
- 求解器が決める顧客 訪問 順序と経路探索器が決める道路経路を分離する
- 案内文書と個別正本が矛盾する場合は、最新の現行の正本、固定済み仕様、実行 成果物一覧を優先する
