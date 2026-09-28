# kmd-analysis

量子技術の進展がEV配送の運用電力量に与える影響：東京都大田区のラストマイル配送をケースとして

東京都大田区の道路データと配送ベンチマークを用い、経路計算とバッテリー性能の変化がEV配送の運用電力量に与える影響を研究します。配送需要・時間窓には合成条件を含み、実配送会社の運用再現や地域全体の統計的代表性は主張しません。

## Research Question

量子技術の進展は、EV配送の経路計算とバッテリー性能の変化を通じて、ラストマイル配送の運用電力量にどのような影響を与えるか。

## Hypothesis

同一の充電を考慮したEV配送問題において、古典計算を用いた場合と比較して、量子計算を用いた場合の方が、バッテリー性能の違いによるEV配送の運用電力量の差が大きくなる。

仮説は今後の検証対象であり、確認済みの結果ではありません。

## Start Here

| 内容 | 最初に読むファイル |
|---|---|
| 現在地・実行状況・次の限定task | [CURRENT_EXECUTION.md](CURRENT_EXECUTION.md) |
| 計算基盤の概要・4点の図・検証履歴 | [COMPUTATION_PLATFORM_SUMMARY.md](reproducibility/COMPUTATION_PLATFORM_SUMMARY.md) |
| 正式な研究タイトル | [RESEARCH_TITLE_AUTHORITY.md](RESEARCH_TITLE_AUTHORITY.md) |
| 問い・仮説の正本文言 | [RESEARCH_QUESTION_AND_HYPOTHESIS.md](RESEARCH_QUESTION_AND_HYPOTHESIS.md) |
| 最新の計算基盤検証の総合判定 | [N002/M2/TW-MODERATE 総合判定](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/MEANINGFUL_MULTI_VEHICLE_OVERALL_DECISION.json) |
| 今後の研究段階・条件の関係 | [RESEARCH_STAGE_ROADMAP.md](01_research_design/RESEARCH_STAGE_ROADMAP.md) |
| 環境・CLI・再現コード・詳細資料への案内 | [REPOSITORY_NAVIGATION.md](docs/REPOSITORY_NAVIGATION.md) |

段階文書に残る過去時点の「次task」より、直近の実行状況はCURRENT_EXECUTIONを優先してください。出力成果物の一部はGit管理対象外のため、GitHubや新規cloneでは別途取得が必要です。ローカル保存先の実在とGitHub公開済みは区別します。

## Current Status

2026-09-28時点。対象は **N002/M2/TW-MODERATE** です。

| 項目 | 状態 |
|---|---|
| 計算基盤検証 | PASS / COMPLETE（当該instanceの範囲） |
| Dense/MPS state-level validation | PASS |
| finite-shot smoke | PASS |
| METHOD_COMPARISON_SCALE | NOT_FROZEN（未固定） |
| Main S0 | NOT_AUTHORIZED（未許可） |

## Computation Platform

道路網・配送条件から、交通経路計算、VRPTW/EVRP、QUBO、Dense/MPSシミュレーション、sampling、復号・独立物理検証へ接続する基盤です。DenseとMPSは、ともに量子回路を古典計算機上でシミュレーションする方式です。

構成図・実道路経路図・時間軸・数値詳細は[計算基盤のまとめ](reproducibility/COMPUTATION_PLATFORM_SUMMARY.md)を参照してください。

## Key Results

- 実際に2台必要な対象で、Dense/MPSのstate-level整合性を確認しました。
- Dense64 shots・MPS64 shotsのsamplingからdecoder・独立validator・会計までの処理経路がPASSしました。
- 両者を合わせた計算基盤検証が完了しました。数値・監査の出典は上記summaryから辿れます。

[finite-shot最終判定](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/FINITE_SHOT_DECISION.json)。この結果は量子優位性、省エネ効果、高い解品質、大規模問題や実QPUでの成立を示しません。

## Next Step

**METHOD_COMPARISON_SCALEの選定・固定に向けた証拠整理と判断**：古典計算と量子計算の本比較に使用する配送問題の規模・条件を決定する段階です。まだ固定済みではなく、このREADMEは追加科学実行やMain S0の許可を与えません。

## Repository Guide

| Directory | 内容 |
|---|---|
| `00_project_management/` | 研究管理・環境・構造規則 |
| `01_research_design/` | 研究設計・段階ロードマップ・比較計画 |
| `02_literature/` / `03_data/` | 文献、入力データ、metadata |
| `05_src/` | 実装・仕様・検証コード |
| `06_outputs/` | 主要出力の案内 |
| `reproducibility/` | summary・設定・環境・manifest・再現性資料 |
| `reproducibility/outputs/traffic_simulation/` | routing・VRPTW・QUBO・backend検証のauthorityと成果物 |
| `docs/` | 利用ガイド・詳細資料への索引 |
| `reproducibility/archive/` / `legacy/` | 履歴・過去資産（現行指示と区別） |

README → summary／CURRENT／正本 → 詳細報告 → raw artifactsの順に参照します。個別の実行条件・判定は凍結済みauthorityと成果物を優先します。
