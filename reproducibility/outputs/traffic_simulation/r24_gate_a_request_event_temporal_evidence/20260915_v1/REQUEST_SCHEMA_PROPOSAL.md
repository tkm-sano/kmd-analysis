# Minimum request/demand schema proposal — not implemented
Primary type: SYNTHETIC_HOUSEHOLD_DAY_DEMAND_RECORD, a count-bearing explicit synthetic demand record, not individual shipment microdata. Never expand counts to invented parcel IDs. Individual Delivery Request identity is NOT_AVAILABLE.

| Proposed field | Existing source / derivation | Null policy / meaning |
|---|---|---|
| request_id | daily_requests.request_id, retain verbatim | unique non-null household-day record identity |
| source_record_id | same existing request_id, no new ID | source identity |
| source_snapshot_sha256 | saved source byte hash | required metadata, deterministic |
| destination_building_id | request_building_mapping.building_id or scoped household join | nullable for 347 unmapped positive rows, reason required |
| household_id | daily_requests.household_id | synthetic household identity |
| realized_count | daily_requests.parcel_equivalent | integer content count, unit parcel_equivalent; not count of shipment IDs |
| content_basis | source is realized count | MODEL_BASED_SYNTHETIC lineage, not physical load |
| synthetic_date | evaluation_date | ISO date, no added timestamp |
| access_id | none | null: NOT_AVAILABLE; no fabricated entrance |
| road_node_id | R03 edge_from_node/edge_to_node relation | do not choose one endpoint arbitrarily; use separate routing reference relation |
| provenance_class | raw provenance_type retained plus authority interpretation | original model_assumed; synthetic with calibrated mean, Poisson family assumed |
| observation_status | source authority | SYNTHETIC, never observed |
| record_type / unit_definition | this dictionary proposal | household-day aggregated demand record |
| transformation_version | future deterministic join contract | not implemented |

Road relation should retain routing_proxy_id=existing stop_id, network_sha256, mapping_rule, mapped_edge_id, edge_from_node, edge_to_node, geometry/CRS and mapping status. No one road node or access identity is selected. Old accepted fixture may supply edge_offset_m only for its existing endpoints; that does not populate all records.

Building-level alternative type: AGGREGATED_DELIVERY_DEMAND_RECORD. Retain source_record_id=stop_id, destination_building_id, child request_ids, request_count (number of household-day rows), realized_count (sum of parcel-equivalents), synthetic_date, geographic point and source hash. Do not set its ID equal to individual request or service-event identity. Expected rate belongs in a separate expectation table with parcel_equivalent/day unit.

Proposed invariants: source IDs stable/unique; one household and day per request row; no split/added child identity; join at most one saved building per household; explicitly preserve unmapped rows; within selected horizon no omission/double membership; request_count and realized_count conserved separately. Event assignment and horizon fields stay OPEN. No q_i/Q/m fields are populated.
