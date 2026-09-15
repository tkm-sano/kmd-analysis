# Capacity regime definition

## Frozen controlled parameters

\[
\rho^*\in\{0.50,0.70,0.90\}.
\]

| ID | Target | Intended benchmark condition |
|---|---:|---|
| `LOOSE` | 0.50 | weak nominal capacity pressure |
| `MODERATE` | 0.70 | intermediate nominal capacity pressure |
| `TIGHT` | 0.90 | strong nominal capacity pressure |

All three are `CONTROLLED_BENCHMARK_PARAMETER`. They are not estimates of physical load factor, vehicle utilization, carrier practice or Ota fleet operation.

For each frozen instance, store:

- `capacity_regime_id`
- `rho_target`
- `total_demand_D`
- `Q=14`
- derived `m`
- `rho_actual=D/(mQ)`
- validation status and degeneracy flags

## Integer-rounding behavior

Because `m=ceil(D/(rho_target Q))`, actual pressure never exceeds its target but may be materially lower. No tolerance-based adjustment of `Q` or `m` is permitted.

Two target regimes may yield the same integer `m`. When this occurs, label each affected cross-regime comparison `DEGENERATE_REGIME_SAME_M`. Preserve the calculation, but exclude that comparison from claims about a capacity-pressure effect. Do not redraw customers solely to obtain separation.

If `D<=Q`, the capacity inequality is redundant for the instance irrespective of route assignment. Label it `CAPACITY_REDUNDANT`; it may remain a routing/algorithm case but is excluded from capacity-effect claims.

Capacity non-binding in an otherwise valid instance is an allowed result. Binding behavior was not used to select `Q` or the regime targets.
