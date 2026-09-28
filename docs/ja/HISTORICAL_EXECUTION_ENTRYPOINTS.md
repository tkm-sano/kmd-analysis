# 過去段階・再現用コードの入口

通常の入口は [CURRENT_EXECUTION.md](../../CURRENT_EXECUTION.md) です。以下は旧段階や検証目的のコードであり、現在の計算方式 Phase 1を起動する一覧ではありません。ファイルを移動せず、案内上で分離しています。

| 用途・段階 | 既存コードの場所 | 現在の扱い |
|---|---|---|
| VRPTW Uniform QAOA | [r24_vrptw_qaoa_worker](../../05_src/traffic_simulation/r24_vrptw_qaoa_worker/) | 過去科学実行の再現用。新電気自動車配送経路問題固定パラメーター 実行処理の代用不可 |
| VRPTW Structured QAOA | [r24_vrptw_structured_worker](../../05_src/traffic_simulation/r24_vrptw_structured_worker/) | 過去S01/S02/S03等の再現用。現在の起動入口から除外 |
| 旧QAOA/Aer実装 | [r23_qaoa_aer](../../05_src/traffic_simulation/r23_qaoa_aer/) | 旧実験・依存コードとして保持 |
| 旧n5 規模拡大 | [run_n5_scaling.py](../../05_src/traffic_simulation/r23_n5_scaling/run_n5_scaling.py) | 過去規模検証用。現行ladderの実行入口ではない |
| 一時量子計算診断 | [run_diagnostic.py](../../05_src/traffic_simulation/temporary_quantum_diagnostic/run_diagnostic.py) | 過去診断用。現行計算方式の確認として再実行しない |
| Minimal EVRP classical regression | [run_regression.py](../../05_src/traffic_simulation/r24_minimal_evrp/run_regression.py) | モデル検証用。読取り専用 手順検証や本実験の第0段階実行とは別 |
| Controlled charging validation | [run_charging_validation.py](../../05_src/traffic_simulation/r24_minimal_evrp/run_charging_validation.py) | 制御条件でのモデル検証用。第0段階充電条件と混同しない |
| 旧古典参照解 | [run_r24_classical_validation.py](../../05_src/traffic_simulation/r24_classical_reference/run_r24_classical_validation.py) | 過去参照検証用。調査Aの起動入口ではない |
| 旧OR-Tools実行 | [run_ortools_execution.py](../../05_src/traffic_simulation/evrp_r18_execution/run_ortools_execution.py) | 旧段階の再現用 |
| 旧経路-順序 検証 | [r20_route_ordering](../../05_src/traffic_simulation/r20_route_ordering/) | 検証・依存として保持 |
| 旧QUBO/Ising構築 | [r21_qubo_validation](../../05_src/traffic_simulation/r21_qubo_validation/)、[r22_ising_conversion](../../05_src/traffic_simulation/r22_ising_conversion/) | ライブラリ・検証コードを含む。不要判定はしていない |
| R23監査ツール | [reproducibility/tools](../../reproducibility/tools/) | 過去監査・再現用 |
| 過去成果物内の生成・監査スクリプト | [traffic_simulation outputs](../../reproducibility/outputs/traffic_simulation/) | 当時のauthority/manifestとともに保持。build/finalize/verifyを一括起動しない |
| 既存の物理アーカイブ | [R23 archive manifest](../../reproducibility/archive/traffic_simulation/r23/ARCHIVE_MANIFEST.md) | 既に移動済みの記録。今回追加移動なし |

2026-09-27の棚卸しでは、`05_src/traffic_simulation` のPython/shell/notebook 405ファイルと `reproducibility/tools` の13ファイルは、直近計算方式 手順の保護記録に全件含まれていました。出力内の同種ファイル202件中165件も保護記録に含まれています。残る37件を不要と判断したわけではありません。この数は入口数ではなく拡張子によるファイル数で、ライブラリ・試験も含みます。

本整理は文書による入口分離のみです。削除0、移動0、既存実行コード変更0。凍結ハッシュ値を壊すchmod変更、実行wrapperの追加、過去コマンド操作の付け替えも行っていません。
