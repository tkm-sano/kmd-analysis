# Instance Manifest Schema

Generation must emit UTF-8, LF, deterministically ordered machine-readable JSON plus tabular CSV indexes. JSON object keys are lexicographically sorted; customer and OD arrays use the orders below. SHA-256 hashes are lowercase hexadecimal. Null is explicit and never an empty string in JSON.

## Base instance record

Required fields:

| Field | Type / rule |
|---|---|
| `protocol_id`, `protocol_version` | string; fixed specification identity |
| `instance_id` | string; convention contract |
| `suite` | enum `RND`,`STR`,`ANCHOR` |
| `structure` | null or enum |
| `n`, `repetition` | integer; anchor repetition is null |
| `seed_material`, `seed_digest_sha256`, `seed_uint64` | primary/structural required; anchor inherited/reference |
| `sampling_method` | enum `HASH_RANKED_SRSWOR`,`CLUSTERED`,`DISPERSED`,`MIXED`,`ANCHOR_ALIAS` |
| `customer_ids` | array, bytewise customer-ID order |
| `anchor_source_base_instance_id` | required only for anchor |
| `depot_id` | exactly `DEP_006` |
| `graph_id`, `graph_sha256` | run_3 identity |
| `source_c_eligible_path`, `source_c_eligible_sha256` | frozen source identity |
| `source_customer_count`, `source_total_demand` | 39,930 and 81,793 |
| `capacity_unit` | `METHODOLOGICAL_PARCEL_EQUIVALENT` |
| `total_demand_D` | positive integer |
| `q_i_by_customer` | ordered array of `{customer_id,q_i}` |
| `q_i_vector_sha256` | canonical JSON array hash |
| `duplicate_proxy_customer_count` | integer |
| `duplicate_proxy_group_count` | integer |
| `duplicate_proxy_groups` | group IDs and sorted members |
| `zero_distance_ordered_arc_count`, `zero_travel_time_ordered_arc_count` | integer |
| `od_record_count` | must equal `(n+1)n` |
| `od_matrix_sha256`, `od_validation_sha256` | hashes |
| `selection_validation_status`, `routing_validation_status`, `base_status` | enums |
| `hard_rejection_reasons` | sorted enum array, empty only for accepted |
| `created_at_utc` | RFC 3339 execution timestamp; not used in selection |
| `generator_code_sha`, `git_commit_sha`, `output_sha256` | provenance |

## OD record

Required fields are `origin_id`, `destination_id`, `reachable`, `distance_m`, `travel_time_s`, `origin_edge_id`, `origin_offset_m`, `destination_edge_id`, `destination_offset_m`, `edge_sequence`, `edge_sequence_sha256`, `connection_validation_status`, `duplicate_proxy_arc_flag`, `zero_distance_flag`, and `zero_travel_time_flag`. Sort by `(origin_id,destination_id)` bytewise. Self pairs are absent.

## Capacity-condition record

Required fields are `condition_id`, `base_instance_id`, `regime_label`, `target_rho` (decimal string with two digits), `Q`, `capacity_unit`, `m`, `actual_rho` (full-precision decimal string), `total_demand_D`, `necessary_capacity_check`, `packing_preflight_algorithm`, `packing_feasibility`, `packing_certificate_sha256`, `packing_states_examined`, `degenerate_regime_flag`, `degenerate_regime_group_id`, `condition_status`, `hard_condition_reasons`, `base_output_sha256`, `generator_code_sha`, and `output_sha256`.

## Suite-level manifest

The suite index records every planned base and condition ID, including rejected and infeasible records; counts by suite/n/status; source/protocol/graph/code hashes; generation environment; output file hashes; and the explicit facts `scientific_experiment=NONE`, `optimization=NONE` for generation. An output cannot be accepted if the suite index omits a planned ID.
