# Routing proxy policy

## Adopted policy

The routing proxy is the versioned road-network attachment used to compute benchmark travel, while the building remains the customer identity. The saved R03 relation supplies historical edge and endpoint-node identifiers for all 39,956 candidate buildings. It is `ROUTING_PROXY`, not `PHYSICAL_STOP`.

- Preserve `source_building_id` and unique `benchmark_customer_id`.
- Record mapping method, network hash, source hash, edge ID, endpoint-node IDs and mapping distance.
- Do not merge buildings merely because they share an edge, node or coordinate.
- Flag duplicate proxy locations/nodes and validate zero-cost or duplicate-location effects at instance level.
- Do not infer service-event aggregation from co-location.
- Preserve directed Routing Baseline semantics; do not symmetrize reachability or cost.

## Current mapping boundary

The historical R03 mapping uses run_2 network hash `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` and rule `nearest_delivery_permitted_edge_midpoint`. Its CSV stores building longitude/latitude, mapped edge, from/to nodes and mapping distance; it does not store an observed entrance or a canonical accepted run_3 endpoint coordinate/offset for the full population.

Accordingly:

- `routing_proxy_id` may be populated for the candidate frame as `R03-RUN2-EDGE::<sumo_edge_id>`;
- source building coordinates are labeled `source_longitude/source_latitude`, never proxy or entrance coordinates;
- current Routing Baseline endpoint ID/coordinate/offset and compatibility remain nullable until remapping/validation;
- a record becomes routing-eligible only after its mapping network/version and access profile match the accepted Routing Baseline.

Historical duplication audit: 21,684 unique edges for 39,956 buildings; 28,294 buildings occur on shared edges. There are 21,673 unique directed `(from_node,to_node)` pairs, with 28,299 buildings in shared-pair groups. These are retained and flagged, not consolidated.

