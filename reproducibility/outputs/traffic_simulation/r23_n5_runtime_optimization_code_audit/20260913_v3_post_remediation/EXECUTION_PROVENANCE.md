# Execution provenance

| run | classification | evidence |
|---|---|---|
| rank01 | `VERIFIED` for recorded conditions; `STRONGLY_INFERRED` for complete source execution | result/terminal/resource records contain p=1, COBYLA, fixed_0.1, lambda 4, seed 17, cap 300; source commit is historical and no full trace/final parameters are retained |
| rank02 | `STRONGLY_INFERRED` | compact record and v4 helper SHA exist, but execution used dirty/uncommitted source and resource/provenance limitations remain |
| rank03 | `STRONGLY_INFERRED` | same limitation as rank02 |

Authority environment and input identity are pinned; rank02/03 cannot be promoted to formal acceptance without a fresh contract-compliant run.
