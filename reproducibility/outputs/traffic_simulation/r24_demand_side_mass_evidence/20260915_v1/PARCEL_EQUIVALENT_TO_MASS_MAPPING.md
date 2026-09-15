# Parcel-equivalent to mass mapping boundary

## Existing semantic authority

`parcel_equivalent` is a **calibrated synthetic realized abstract content count**. It is neither an observed parcel identity nor a measured physical parcel count. No statement of `1 parcel-equivalent = 1 actual observed parcel` is permitted.

## Conditional mapping if authority is later accepted

Let `N_i` be the frozen parcel-equivalent count for benchmark customer `i`. If and only if a target-compatible parcel-level gross-mass distribution `F_W` is accepted:

\[
W_{ij} \sim F_W, \qquad
q_i = \sum_{j=1}^{N_i} W_{ij}.
\]

Required implementation metadata would include source ID/version, gross/net mass definition, kg conversion, sampling algorithm and seed, truncation/tail rule, dependence assumptions, and uncertainty scenario. The generated values must be labeled **synthetic parcel mass realization**.

This review does not authorize independence, identical distribution across customers, or a specific random-number generator; those are later modeling choices.

## Mean-only alternative

\[
q_i = N_i\bar W
\]

is deterministic and removes parcel-level variance and tail behavior. It also makes every building with the same `N_i` identical in mass. A mean-only source could support a coarse deterministic sensitivity case only if its population validity and uncertainty were exceptionally well established. The reviewed sources do not meet that threshold.

## Current status

- `F_W = NOT_AUTHORIZED`
- kg conversion = `PROHIBITED_PENDING_AUTHORITY`
- mass realization performed = `NONE`
- frozen demand counts mutated = `NO`
