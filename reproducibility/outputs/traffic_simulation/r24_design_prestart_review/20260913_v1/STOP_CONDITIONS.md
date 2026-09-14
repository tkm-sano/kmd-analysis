# Stop conditions

Execution stops on any of: `STOP_CAPACITY_TRIVIAL`, `STOP_DEMAND_AUTHORITY_INSUFFICIENT`, `STOP_CAPACITY_AUTHORITY_INSUFFICIENT`, `STOP_CLASSICAL_FORMULATION_AMBIGUOUS`, `STOP_EXACT_REFERENCE_UNAVAILABLE`, `STOP_QUBO_ENCODING_UNVERIFIED`, `STOP_PENALTY_UNJUSTIFIED`, `STOP_QUBIT_RESOURCE_EXCEEDED`, or `STOP_RESEARCHER_ARBITRARINESS_HIGH_UNRESOLVED`.

Current unresolved stops are demand authority, vehicle capacity authority, and penalty justification. Qubit resource is resolved for design: n=2 is feasible, n=3 small-scale only, n>=4 not recommended for exact statevector. Capacity-trivial, classical-ambiguity, and exact-reference-availability stops are resolved for the proposed design.

