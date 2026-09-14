# Representative instance schema (design only)

No instance was generated or solved in this task. A future nested instance record MUST preserve the following fields:

| Field | Type/unit | Rule |
|---|---|---|
| `instance_id` | string | deterministic versioned ID |
| `parent_stratum_id` | string | frozen hierarchical stratum |
| `customer_ids` | ordered list[string] | IDs from the frozen 39,956 population |
| `q_i` | float, kg/customer/day | only after parcel-weight authority passes |
| `q_i_source` | string | expected parcel proxy + weight authority IDs |
| `Q` | float, kg | 2,000 from fixed profile |
| `m_min_capacity` | integer | `ceil(sum(q_i)/Q)`; lower bound only |
| `depot_id` | string | `DEP_006` |
| `depot_role` | enum | public logistics-facility proxy, not observed operational depot |
| `od_source_artifact` | string | frozen R24-compatible directed matrix |
| `reachability_status` | enum | each ordered pair explicit; unreachable not imputed |
| `representativeness_metadata` | object | parent size/share, density/time/road diagnostics |
| `sampling_seed` | integer/null | required only when PPS realization is used |
| `source_sha256` | object | all input/source hashes |

Nested hierarchy remains `C_all -> C_s -> C_{s,r}`. Population scale, classical evaluation scale, and quantum evaluation scale are separate. No customer or demand rescaling is permitted merely to make a quantum instance feasible.
