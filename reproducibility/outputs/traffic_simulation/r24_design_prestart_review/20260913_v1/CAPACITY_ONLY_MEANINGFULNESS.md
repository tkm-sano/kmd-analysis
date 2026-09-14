# Capacity-only meaningfulness

`R23 + sum_i q_i <= Q` is `CAPACITY_ONLY_TRIVIAL`. The left side is independent of route order: if total demand is at most `Q`, every R23 permutation is feasible; otherwise none is feasible. It therefore changes feasibility globally, not the solution structure.

Capacity becomes meaningful only when customers can be partitioned among trips or vehicles. Candidate A fails this test. Candidate B passes with two trips. Candidate C passes with two vehicles. Candidate D (time windows) also passes in principle but requires arrival-time variables, sequencing constraints, and substantially less transparent penalties; it is deferred.

