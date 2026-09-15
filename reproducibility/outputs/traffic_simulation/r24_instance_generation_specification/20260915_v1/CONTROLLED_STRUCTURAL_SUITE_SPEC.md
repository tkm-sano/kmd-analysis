# Controlled Structural Suite Specification

## Frozen size

- structures: `CLUSTERED`, `DISPERSED`, `MIXED`;
- n: `{4,10,20}`;
- repetitions: `3` for every `(structure,n)`;
- total: 27 deterministic base subsets.

These are controlled spatial stress tests, not random or representative samples. Manual customer or anchor selection is prohibited.

## Common geometry and tie rules

Use each eligible customer's stored `source_longitude` and `source_latitude`, transformed from EPSG:4326 to **EPSG:6677 (JGD2011 / Japan Plane Rectangular CS IX)** with `always_xy=true`. The metric is projected straight-line Euclidean distance in metres, not routing-network distance. Reject the base under `STRUCTURAL_COORDINATE_INVALID` if transformation is non-finite or missing; do not replace a customer or anchor.

Use the structural seed and `selection_score` from `SEED_POLICY.md`. All maximization/minimization ties are resolved by `(selection_score, benchmark_customer_id)` ascending. Customer IDs are unique; a subset contains no customer twice.

## CLUSTERED

Let anchor `a` be the eligible customer with smallest `(selection_score, customer_id)`. Select `a` plus the `n-1` customers with smallest `(EuclideanDistance(a,c), selection_score(c), customer_id)`. This minimizes local radius around a mechanically chosen anchor without outcome inspection.

## DISPERSED

Initialize `S={a}` using the same anchor rule. Until `|S|=n`, choose the unselected customer maximizing

\[
\delta(c,S)=\min_{s\in S}d(c,s).
\]

For equal `delta`, choose the smallest `(selection_score, customer_id)`. This deterministic farthest-point traversal increases pairwise separation without an outcome-based threshold.

## MIXED

Choose `a1` by the anchor rule and `a2` as the farthest customer from `a1`, using the common tie rule. Define quotas `k1=ceil(n/2)` and `k2=floor(n/2)`. Start group 1 with `a1` and group 2 with `a2`. Alternating group 1 then group 2, append to a group the globally unselected customer nearest its anchor by `(distance, selection_score, customer_id)` until that group's quota is full; skip a full group. The base subset is the union. This creates two separated spatial groups by a fully mechanical rule.

Overlap across repetitions, structures, or primary instances is allowed and recorded. It never triggers redraw.
