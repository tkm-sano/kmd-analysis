# Runtime optimization implementation

`optimized_metrics_v4.py` uses indexed feasible basis generation, direct mass aggregation, explicit invalid mass, and finite/range/unit-norm guards. The inspected arithmetic is mathematically equivalent to the route metrics for valid inputs; caching is limited to feasible indices and does not use the optimum to alter the objective. It is a candidate post-processing optimization, not a formal end-to-end benchmark. Result: `SAFE_EQUIVALENT` for the helper arithmetic with validation limitations; no scientific rerun was authorized.
