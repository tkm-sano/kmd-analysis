# Capacity Condition Contract

For every base subset, compute once:

\[
D=\sum_i q_i,\qquad Q=14.
\]

For each target `rho` in the fixed ordered set `{0.50,0.70,0.90}` (`LOOSE`, `MODERATE`, `TIGHT`), derive:

\[
m=\left\lceil\frac{D}{\rho^*Q}\right\rceil,
\qquad
\rho_{actual}=\frac{D}{mQ}.
\]

The customer subset and OD matrix are identical across the three conditions. No regime-specific sampling is allowed.

## CAPACITY_PACKING_PREFLIGHT

Before route optimization, decide exactly whether indivisible demands can be partitioned into at most m bins of capacity Q. Use this deterministic complete decision procedure:

1. fail input validation if any q is not a positive integer or exceeds Q;
2. sort demands by `(q descending, customer_id ascending)`;
3. initialize m residual capacities of Q, represented as a non-increasing tuple;
4. recursively place the next demand into each distinct residual-capacity value that fits, iterating values high-to-low;
5. after placement, sort residuals non-increasing and memoize `(next_index,residual_tuple)`;
6. return `FEASIBLE` on the first complete placement and persist its lexicographically first deterministic assignment; return `PACKING_INFEASIBLE` only after exhaustive state exhaustion.

This symmetry-reduced memoized backtracking is exact and deterministic; it is not route optimization. The execution manifest must record implementation/code SHA, node/state count, result, and certificate/assignment hash.

If packing is infeasible, retain the base and condition, set `condition_status=PACKING_INFEASIBLE`, set hard condition reason `CAPACITY_PACKING_INFEASIBLE`, and prohibit CVRP optimization for that condition. Do not redraw or replace the sample. The necessary check `mQ>=D` is recorded but never treated as sufficient.

## Degeneracy

For any two targets on the same base producing the same m, set `degenerate_regime_flag=true` and `degenerate_regime_group_id` to the sorted shared-m group. Preserve all records and outputs. Such conditions remain valid if packing is feasible but are excluded from capacity-effect comparisons under `DEGENERATE_REGIME_SAME_M`; the instance is never discarded.
