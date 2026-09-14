# R24 Ota CVRP design decision

Problem family: `Small Capacitated Vehicle Routing Problem` with multiple vehicles, one fixed depot, customer demand, capacity, exact customer service, depot departure/return, flow continuity, reachability, and total travel-time minimization.

Decision: `R24_OTA_HIERARCHICAL_CVRP_RECOMMENDED`; final verdict `R24_OTA_HIERARCHICAL_CVRP_APPROVED_WITH_REVISIONS`.

The complete Ota candidate population is retained as `C_all`. Data-derived depot travel-time bands and demand-density strata define service areas; deterministic feature-medoid selection and seeded PPS sampling define representative subproblems. This preserves the distinction between the Ota delivery system and a solver evaluation unit. Execution is gated until demand/capacity units and representative reachability are authoritative. R24 remains `R24_NOT_STARTED`.

