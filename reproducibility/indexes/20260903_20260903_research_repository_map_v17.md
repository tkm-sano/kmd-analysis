# 研究リポジトリマップ v17

文書識別子: `DOC-RESEARCH-REPOSITORY-MAP-V17`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `reproducibility/indexes/research_repository_index_v17.yml`

研究の問い、段階 1～11の全計画、マイルストーン、ゲート、現在地は、最初に[研究概要・ロードマップ v17](../../00_project_management/history/20260903_20260903_RESEARCH_OVERVIEW.md)を読む。各stageのinput/output、コマンド、正本、検証、受入、引継ぎは[現行 研究工程の参照資料](../../docs/RESEARCH_PIPELINE_REFERENCE.md)を参照する。統合された実行・検証入口には[`./research`](../../docs/20260903_20260903_research_cli.md)を使用し、`./research commands`をコマンド 索引とする。

本書はnavigation文書であり、第二の正本ではない。道路網の正本参照先は[current_network_completion_authority_v17.yml](../config/traffic_simulation/current_network_completion_authority_v17.yml)、道路網完成処理工程の正本は[network_completion_pipeline_v17.yml](../config/traffic_simulation/network_completion_pipeline_v17.yml)である。

```text
概念モデル
  └─ Decision
      └─ 仕様
          └─ Registry／Schema
              └─ 実装
                  └─ 検証
                      └─ 基準／Run
                          └─ SUMO道路網
                              └─ Mapping
                                  └─ 受入
                                      └─ Portal
                                          └─ 研究概要
                                              └─ 経路基準（次段階）
                                                  └─ 共通instance／最適化／評価／解釈（将来段階）
```

現在の追跡可能性:

| 役割 | 現行参照先 |
|---|---|
| 研究概要／段階計画 | `00_project_management/history/20260903_20260903_RESEARCH_OVERVIEW.md`、stable entry: `01_research_design/RESEARCH_OVERVIEW.md` |
| 研究実行コマンド操作 | `research`、reference: `docs/20260903_20260903_research_cli.md` |
| Pipeline運用参照 | `docs/RESEARCH_PIPELINE_REFERENCE.md` |
| 決定記録 | `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001` |
| 規範仕様 | `05_src/traffic_simulation/specifications/20260903_20260903_formal_completion_three_tier_policy_v17.md` |
| Pipeline仕様 | `05_src/traffic_simulation/specifications/20260903_20260903_network_completion_pipeline_v17.md` |
| Registry／schema | `reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml`および`schemas/formal_completion_*three_tier*` |
| 受入済み実行 | `.../phase13_20260903_three_tier_completion/run_2` |
| 受入済み道路網 | `three_tier.net.xml`、SHA `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| 受入成果物 | `run_2/network_acceptance.json` |
| ポータル | `reproducibility/config/research_portal/three_tier_network_run2_status.yml` |

規範文書には方針と契約だけを置く。調査、診断、報告、生成出力は非規範のままとし、索引または成果物一覧から参照する。履歴・後続版に置換済み成果物は保持し、filenameだけを根拠に現行へ昇格させない。
