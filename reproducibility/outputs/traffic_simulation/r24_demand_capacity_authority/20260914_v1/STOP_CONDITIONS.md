# Stop conditions

| Stop | Status | Evidence / release condition |
|---|---|---|
| `STOP_DEMAND_PROXY_NOT_TRACEABLE` | RESOLVED | customer expected parcel proxy reconstructed from expected household demand + scoped building assignment; 39,956 rows reproduced |
| `STOP_PARCEL_WEIGHT_AUTHORITY_INSUFFICIENT` | REMAINS | no parcel-level or matching-universe representative weight authority; do not populate kg |
| `STOP_CAPACITY_AUTHORITY_INSUFFICIENT` | RESOLVED_FOR_Q_ONLY | `Q=2,000 kg` inherited from fixed research profile; it is not observed payload evidence |
| `STOP_REPRESENTATIVENESS_UNVERIFIED` | REMAINS | R24 customer/OD representative all-pairs diagnostics and frozen strata are not present in this authority artifact |
| `STOP_CAPACITY_NON_BINDING_AT_QUANTUM_SCALE` | CONDITIONAL / NOT ASSESSED | requires authorized kg demand and candidate `(n,m,Q)` instances; no artificial rescaling is allowed |
| `STOP_QUBO_RESOURCE_EXCEEDED` | NOT ASSESSED | no QUBO or quantum execution permitted |

Overall physical-unit demand/capacity gate is blocked by the parcel-weight stop. No QUBO penalty or production CVRP work is authorized.
