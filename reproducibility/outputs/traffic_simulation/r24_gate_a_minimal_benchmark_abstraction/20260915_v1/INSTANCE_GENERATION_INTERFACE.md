# Instance Generation interface

This is the common input contract for future Repeated Random, Controlled and Fixed Anchor generators. It does not itself select or generate an instance.

| field | type | requirement / meaning |
|---|---|---|
| `benchmark_customer_id` | string | required, unique; `R24-20260101-BUILDING::<source_building_id>` |
| `source_building_id` | string | required, immutable saved building ID |
| `source_horizon_id` | string | required; `R24-SOURCE-DAY-2026-01-01-v1` |
| `source_horizon_member` | boolean | required and true for eligibility |
| `realized_demand_ref` | string | required pointer to building aggregate/source hash; no copied expected rate |
| `realized_parcel_equivalent` | integer | required, positive exact building sum |
| `routing_proxy_id` | string | required for eligibility; version-qualified edge/node/offset identity |
| `routing_edge_id` | string | required for eligibility |
| `routing_from_node_id` / `routing_to_node_id` | string | directed topology identifiers |
| `source_longitude` / `source_latitude` | float | required finite WGS84 building representative point; not an entrance |
| `routing_proxy_longitude` / `routing_proxy_latitude` | float/null | accepted routing endpoint coordinates; nullable in candidate frame only |
| `routing_edge_offset_m` | float/null | accepted endpoint offset; nullable in candidate frame only |
| `mapping_method` | string | required |
| `mapping_network_hash` | sha256 | required |
| `mapping_source_hash` | sha256 | required |
| `mapping_status` | enum | `ACCEPTED`, `INCOMPATIBLE`, `MISSING`, `INVALID`, `NOT_EVALUATED` |
| `depot_outbound_reachable` | boolean/null | `DEP_006 -> customer`; true required for eligibility |
| `depot_inbound_reachable` | boolean/null | `customer -> DEP_006`; true required for eligibility |
| `reachability_network_hash` | sha256/null | must equal accepted Routing Baseline hash |
| `duplicate_proxy_flag` | boolean | true for shared accepted proxy identity/location |
| `duplicate_proxy_group_id` | string/null | deterministic group identity; does not merge customers |
| `eligibility_status` | enum | `ELIGIBLE`, `EXCLUDED`, `PENDING_VALIDATION` |
| `exception_codes` | list/string | explicit reason codes; empty only after validation |

All three generator families must filter on `eligibility_status=ELIGIBLE`, preserve customer identity and provenance, and perform complete directed pair reachability plus zero-cost/duplicate-location validation for the selected instance. They must not interpret one row as an observed stop or service event.

