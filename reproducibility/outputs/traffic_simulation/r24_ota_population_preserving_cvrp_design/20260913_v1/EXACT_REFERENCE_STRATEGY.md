# Exact reference strategy

The primary exact reference is independent vehicle-assignment plus partition-and-permutation enumeration: assign customers to at most m labelled vehicles, enumerate each vehicle's customer permutation, reject capacity and unreachable routes, canonicalize unused-vehicle symmetry, and select minimum total directed travel cost.

An independently implemented exact MILP with the same frozen matrix and constraints is the cross-check for the smallest representative instances. Agreement must cover objective, served set, capacity loads, and route validity. If enumeration is unavailable for a selected instance, execution stops with `STOP_EXACT_REFERENCE_UNAVAILABLE`; a solver-reported optimum alone is insufficient.

For n customers and m vehicles, the raw labelled route count before capacity filtering is `(m+n-1)!/(m-1)!` when empty routes are allowed, equivalent to distributing an ordered customer permutation among m route separators. Exact burden grows factorially; n is determined by the selected representative cluster and resource gate.

