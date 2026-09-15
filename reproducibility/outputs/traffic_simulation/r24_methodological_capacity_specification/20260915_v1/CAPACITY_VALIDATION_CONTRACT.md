# Capacity validation contract

Every future instance-regime pair must pass or record the following checks before optimization claims.

| Check | Rule | Failure/status action |
|---|---|---|
| demand integrity | integer `q_i` equals frozen building value | reject as `DEMAND_LINEAGE_MISMATCH` |
| positive instance | `n>=1` and `D>0` | reject as `EMPTY_OR_ZERO_INSTANCE` |
| individual feasibility | `max_i q_i <= Q=14` | reject as `INDIVIDUAL_DEMAND_EXCEEDS_CAPACITY` |
| fleet domain | `m>=1` and integer | reject as `INVALID_FLEET_PARAMETER` |
| aggregate capacity | `mQ>=D` | reject as `AGGREGATE_CAPACITY_INFEASIBLE` |
| exact packing | all customers partitionable into at most `m` bins of capacity `Q` | exclude regime as `INFEASIBLE_REGIME` |
| pressure record | save target and exact actual rho | reject metadata as `PRESSURE_NOT_REPRODUCIBLE` |
| same-m degeneracy | compare `m` across targets | flag `DEGENERATE_REGIME_SAME_M`; exclude affected capacity-effect comparison |
| redundancy | `D<=Q` or exact formulation proves capacity never restricts solutions | flag `CAPACITY_REDUNDANT`; retain only outside capacity-effect claims |
| routing feasibility | accepted directed depot/customer paths and route feasibility | reject/exclude under routing contract |

Passing `mQ>=D` alone is not proof of feasibility because indivisible customer demands create a bin-packing condition. This distinction must be preserved in tables and prose.

## Instance-size independence

`n` is a computational benchmark parameter and `n != Q`. Changing `n` never changes `Q`. Very small instances may legitimately produce redundant capacity or identical `m` across regimes. They are flagged under the rules above; customers are not selected or redrawn after seeing optimization quality or binding behavior.

## QUBO compatibility

`q_i`, `Q`, and `m` are integers and can support later exact capacity encodings. A direct binary slack `s_k in [0,Q]` requires conceptually `ceil(log2(Q+1))=4` bits per vehicle before any formulation-specific auxiliaries or validity penalties. This is an estimate, not a frozen QUBO design. No QUBO was constructed here.
