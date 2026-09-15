# Fleet-size derivation

For an instance customer set `C`, define:

\[
D=\sum_{i\in C}q_i,
\quad Q=14,
\quad m_{min}=\left\lceil\frac{D}{Q}\right\rceil.
\]

For each frozen capacity target:

\[
m(\rho^*)=\left\lceil\frac{D}{\rho^*Q}\right\rceil.
\]

This `m` is the **methodological available fleet size**. It is neither observed fleet size nor an estimate of kei vans operated in Ota or by any carrier.

## Required properties

For positive-demand instances and `0<rho_target<=1`:

- `m >= 1`;
- `m >= m_min`;
- `mQ >= D`;
- `rho_actual=D/(mQ) <= rho_target`.

The total-capacity inequality is necessary, not sufficient. Customer demands must be packable into `m` bins of size `Q`, and the routing formulation must admit valid routes. R24 therefore does not call `m_min` or target-derived `m` a feasible or observed fleet until exact instance-level checks pass.

## No post-hoc adjustment

The primary rule fixes `Q` and derives `m`. If exact bin-packing or routing is infeasible, mark the regime `INFEASIBLE_REGIME`; do not increase/decrease `m`, alter `Q`, rescale demand or redraw based on solver performance. A separately versioned sensitivity could define another rule, but it would not be a primary R24 regime.

Actual `m` values are materialized only after instance customers are fixed. Thus the derivation rule is frozen now while instance rows remain absent.
