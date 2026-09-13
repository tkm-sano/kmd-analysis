# Reduced Problem 正式仕様（現行）

Document ID: `R23-REDUCED-PROBLEM-CANONICAL`
Lifecycle: `現行`
Updated: 2026-09-11

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
- B2: fixed_0.1の6 paired conditionsでCOBYLA/Nelder-MeadのP_feasible、P_optimal、runtime、nfev、termination差を確認。両者ともexact best routeは6/6。
- status: `R23_REDUCED_PROBLEM_BASELINE_ACCEPTED_WITH_LIMITATIONS`。

## Limitations

`n=2,3,4`のみ、small deterministic instance set、exact statevector、finite shotsなし、noiseなし、CPU Aer、limited optimizers/initializations、Full EVRP constraintsなし。QPU performance、quantum advantage、QAOA convergence、n>4、Full EVRP generalizationを示さない。

## Next

更新後の状態: n=5の既存scientific recordsは`R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`として保持する。route recovery=3/3、relative gap=0（3/3）に対しoptimizer reported success=2/3。rank01はsuccess=false、300 evaluation cap reached。rank02/03はexecution lineage/resource provenance制約付きで未再承認である。standing auditは`CODE_AUDIT_FAIL`、`CODE_AUDIT_RESULT_NOT_REPRODUCED`。I03 validation gate修正が完了し、現在`REMEDIATION_COMPLETED_PENDING_INDEPENDENT_REAUDIT`。新gateが検出したB2旧terminal-index SHA不整合6件は未修復・独立review待ち。修正後は別taskの独立再監査を行い、この修正ではCODE_AUDIT_PASSを宣言しない。R24は`NOT_AUTHORIZED_PENDING_R23_REMEDIATION`。

n=5だけのλ authorityはλ=4.0、strict sufficient condition λ>(5+1)/2=3。λ−bound=1、2λ−(n+1)=2が正しいmarginである。旧authorityの0.5/1.0表記はerratumで訂正し、元artifactとλは変更しない。n=2,3,4のλ=3.0を変更しない。

n=5は全rankでP_feasible<1%、P_optimal約5.45e-5〜6.64e-5。rank01は42.62h、absolute peak RSS 201.58GiB。runtime benchmarkはPRELIMINARY_ONLY、異なるRSS metricsからmemory reduction factorを算出しない。n≥6は36 logical qubits・raw約1TiBで現methodology非推奨。[remediation contract](R23_RUNTIME_REMEDIATION_CONTRACT.md)を参照する。
