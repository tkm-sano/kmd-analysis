# Stop conditions

Execution stops on `STOP_POPULATION_DEFINITION_UNCLEAR`, `STOP_REDUCTION_RULE_ARBITRARY`, `STOP_REPRESENTATIVENESS_UNVERIFIED`, `STOP_DEMAND_AUTHORITY_INSUFFICIENT`, `STOP_CAPACITY_AUTHORITY_INSUFFICIENT`, `STOP_EXACT_REFERENCE_UNAVAILABLE`, or `STOP_QUBO_RESOURCE_EXCEEDED`.

Currently open: demand authority, capacity authority, representative all-pairs reachability/representativeness verification, and the resource gate if selected sub-instances exceed it. Population definition and proposed reduction rule are clear enough for design approval. Exact-reference availability is feasible in principle only after the representative instance and matrix are frozen.

