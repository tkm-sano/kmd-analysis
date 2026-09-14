# Feasibility definition

A bitstring is feasible only if all customers occur exactly once, every active trip has a valid depot-to-depot route, every selected arc is reachable, and every trip load satisfies `sum_i q_i y[i,k] <= Q`. Invalid bitstrings are discarded, with the full-state denominator retained; no repair and no renormalization are permitted. A decoded route is optimal only when it matches an independently enumerated exact optimum (allowing declared route symmetries).

