# Reduced Problem 正式仕様（現行）

Document ID: `R23-REDUCED-PROBLEM-CANONICAL`
Lifecycle: `現行`
Updated: 2026-09-14（status/authority linksのみ）

Formal A、Experiment B1、Experiment B2を経て受入されたReduced Problem baselineのcanonical specificationである。

## Problem

Single-Vehicle Route Ordering Problem。depot=`0`、customers=`1...n`。depotから出発し、各customerを1回訪問してdepotへ戻る。routeは`(0, π_1, ..., π_n, 0)`。

## Encoding

customer-only position encoding `x[i,t] = 1` iff customer `i` is assigned to visit position `t`。logical variablesは`n²`、depotは変数にしない。

## Hard constraints

各customerをちょうど1回割り当て、各visit positionにちょうど1 customerを割り当てる。これはroute-ordering feasibilityでありFull EVRP feasibilityではない。

## Objective and QUBO

closed routeのdirected travel-time costを最小化する。

```text
H_QUBO = H_travel + λ(P_customer + P_position)
```

`H_travel`はdepot→first、連続customer間、last→depotのdirected travel term、penaltyはexact-one制約の二乗である。formal scopeは`n=2,3,4`、`λ=3.0`。λをn≥5へ一般化しない。詳細な係数・theorem linkageは[R20 supporting specification](R20_QAOA_SUBPROBLEM_SPEC.md)とFormal A evidenceを参照する。

## Exact reference

permutation enumerationでexact referenceを作成し、best decoded feasible routeと比較する。invalid bitstringsはdiscardし、repairしない。

## Probability and decoding

- `P_feasible`: full-state denominatorで配送ルールを守ったstateの確率質量。
- `P_optimal`: full-state denominatorでexact optimal stateの確率質量。
- probabilityはrenormalizeしない。
- `exact_optimum_found`はroute一致を示すだけで、P_optimal=1、100% sampling success、convergenceを意味しない。

## Current evidence

- Formal A: n=2,3,4のproblem-size、p、probability、CPU Aer burdenを確認。
- B1: COBYLAでinitialization sensitivity、instance heterogeneity、exact best-route recovery、termination uncertaintyを確認。
- B2: fixed_0.1の6 paired conditionsでCOBYLA/Nelder-MeadのP_feasible、P_optimal、runtime、nfev、termination差を確認。比較baseline COBYLAとB2 Nelder-Meadはそれぞれexact best route recovery 6/6。B2 scientific integrityは6/6 VERIFIEDだが、terminal-index SHA不整合6件によりartifact integrityはFAILED、独立評価待ち。
- status: `R23_REDUCED_PROBLEM_BASELINE_ACCEPTED_WITH_LIMITATIONS`。

## Limitations

`n=2,3,4`のみ、small deterministic instance set、exact statevector、finite shotsなし、noiseなし、CPU Aer、limited optimizers/initializations、Full EVRP constraintsなし。QPU performance、quantum advantage、QAOA convergence、n>4、Full EVRP generalizationを示さない。

## Current authority and next step

n=5 scientific evidenceは`R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`。optimal route recovery = 3/3、relative gap = 0、optimizer reported success = 2/3。rank01は300 evaluation cap reached。rank02/03はexecution lineage/resource provenance制約付きで未再承認。

standing auditは`CODE_AUDIT_FAIL_PENDING_POST_REMEDIATION_REAUDIT`、original resultは`CODE_AUDIT_RESULT_NOT_REPRODUCED`。remediationは`COMPLETED_PENDING_INDEPENDENT_REAUDIT`、I03は`RESOLVED`。B2の6件は`B2_TERMINAL_INDEX_SHA_INCONSISTENCY`として独立に未解決。historical indexは修復しない。

n=5のλ authorityはλ=4.0、strict condition λ>(5+1)/2=3。λ−bound=1、2λ−(n+1)=2。旧authorityのmargin表記のみerratumが訂正し、元artifactとλは不変。n=2,3,4のλ=3.0は不変。

全n=5 rankでP_feasible<1%。runtime benchmarkはPRELIMINARY_ONLY、n≥6は現行exact CPU Aer statevector方法では非推奨。R23 phaseはOPEN。R24は`R24_NOT_STARTED_BLOCKED_PENDING_R23_POST_REMEDIATION_REAUDIT`。

[Authority map](../../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/final_authority_map.json) · [Scientific facts](../../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/scientific_fact_table.json) · [Remediation/finding map](../../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/current_finding_map.json)。次taskは `R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN`。
