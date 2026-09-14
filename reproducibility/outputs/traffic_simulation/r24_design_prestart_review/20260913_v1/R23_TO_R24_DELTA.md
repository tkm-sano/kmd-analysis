# R23 to R24 delta

R23 remains closed and its scientific facts are unchanged. R24 inherits reduced routing methodology, exact-reference-first, independent QUBO verification, full-state probability definitions, provenance controls, and the audit lessons.

R23: one vehicle, one closed tour, each customer exactly once, customer-only position encoding `n^2`. R24 adds exactly one structural degree of freedom: at most two depot-to-depot trips by the same vehicle, with a capacity constraint per trip. It does not add time windows, SOC, charging, dynamic traffic, stochastic demand, or fleet optimization.

The R24 change is accepted as a design proposal only. No implementation or execution is started by this review.

