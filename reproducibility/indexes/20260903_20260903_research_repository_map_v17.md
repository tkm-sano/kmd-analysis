# 研究リポジトリマップ v17

文書ID: `DOC-RESEARCH-REPOSITORY-MAP-V17`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `reproducibility/indexes/research_repository_index_v17.yml`

研究の問い、Stage 1～11の全計画、マイルストーン、ゲート、現在地は、最初に[研究概要・ロードマップ v17](../../20260903_20260903_RESEARCH_OVERVIEW.md)を読む。統合された実行・検証入口には[`./research`](../../docs/20260903_20260903_research_cli.md)を使用し、`./research commands`をcommand indexとする。

本書はnavigation文書であり、第二の正本ではない。道路網の正本pointerは[current_network_completion_authority_v17.yml](../config/traffic_simulation/current_network_completion_authority_v17.yml)、道路網完成pipelineの正本は[network_completion_pipeline_v17.yml](../config/traffic_simulation/network_completion_pipeline_v17.yml)である。

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

現在のtraceability:

| 役割 | 現行pointer |
|---|---|
| 研究概要／roadmap | `20260903_20260903_RESEARCH_OVERVIEW.md`、stable entry: `RESEARCH_OVERVIEW.md` |
| 研究実行CLI | `research`、reference: `docs/20260903_20260903_research_cli.md` |
| Decision | `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001` |
| 規範仕様 | `05_src/traffic_simulation/specifications/20260903_20260903_formal_completion_three_tier_policy_v17.md` |
| Pipeline仕様 | `05_src/traffic_simulation/specifications/20260903_20260903_network_completion_pipeline_v17.md` |
| Registry／schema | `reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml`および`schemas/formal_completion_*three_tier*` |
| 受入済みrun | `.../phase13_20260903_three_tier_completion/run_2` |
| 受入済み道路網 | `three_tier.net.xml`、SHA `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| 受入成果物 | `run_2/network_acceptance.json` |
| Portal | `reproducibility/config/research_portal/three_tier_network_run2_status.yml` |

規範文書にはpolicyと契約だけを置く。調査、診断、report、生成出力は非規範のままとし、indexまたはmanifestから参照する。履歴・superseded成果物は保持し、filenameだけを根拠に現行へ昇格させない。
