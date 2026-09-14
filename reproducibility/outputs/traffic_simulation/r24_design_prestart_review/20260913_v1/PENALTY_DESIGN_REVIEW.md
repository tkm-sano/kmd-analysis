# Penalty design review

Capacity uses the exact equality `sum_i q_i y[i,k] + u[k] = Q z[k]`; binary slack represents `0..Q` with `s=ceil(log2(Q+1))` bits, with an out-of-range code rejected by an explicit bound term or fail-closed decoder. Unary slack is exact but costs Q bits; one-hot load costs Q+1 states per position.

Penalty coefficients will not be tuned after observing results. For each frozen instance, derive a sufficient lexicographic bound: each violated hard constraint must cost more than the maximum possible improvement in the normalized travel objective over all feasible route changes. If coefficient scaling or weighted equality produces a smaller independent bound, the run stops with `PENALTY_BOUND_NOT_YET_JUSTIFIED`. This review does not claim a numeric universal lambda because `Q`, demand units, cost normalization, and the exact penalty decomposition are not yet authoritative.

