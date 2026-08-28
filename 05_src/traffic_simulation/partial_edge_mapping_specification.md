# Road Census–SUMO partial-edge mapping specification v1.0.0

## 1. Purpose and authority

This specification adds an edge-segment layer to the existing ordered SUMO edge
mapping. It does not replace `final_sumo_edge_sequence`, split a SUMO edge, modify a
`.net.xml`, or apportion an observed traffic count by mapped length. The ordered edge
sequence remains the edge-level mapping; the segment table states which interval of
each selected edge represents the observation section spatially.

Evidence is separated into the following classes.

- **Official fact**: an identifier, geometry, direction, or boundary explicitly present
  in an authoritative source.
- **Rule-derived fact**: a reproducible result with `boundary_position_source`,
  `boundary_anchor`, `derivation_rule_id`, source hashes, and an error metric.
- **Model assumption**: an interpretation needed by a downstream model. It cannot be
  presented as an official fact.
- **Unresolved**: evidence is absent, contradictory, or below an unchanged criterion.

Map imagery and visual inspection may be logged as supporting context but cannot set
`adoption_status`. GeoJSON coordinate order and a bare numeric OSM `ref` are not
direction or route-identity proof.

## 2. Storage model and key

The canonical v1 representation is a separate CSV/JSON-schema pair. Its row key is:

`(official_observation_section_id, direction, sequence_order)`

`edge_id` and ordering must equal the corresponding existing edge sequence. Consumers
that are not segment-aware continue to read the edge sequence. Segment-aware consumers
join the separate table on section, direction, and edge identity. This arrangement
minimizes changes to existing readers and makes provenance and validation explicit.

Required fields are defined by
`reproducibility/config/traffic_simulation/partial_edge_mapping.schema.json`.
Positions are metres along the SUMO edge in its directed geometry, from its `from` node
towards its `to` node. Every row must satisfy, within the declared numeric tolerance:

`0 <= start_position_m <= end_position_m <= edge_length_m`

and:

`used_length_m = end_position_m - start_position_m`.

## 3. Coverage roles

| Role | Start/end meaning in edge direction | Used interval | Permitted conditions | Invalid conditions |
|---|---|---|---|---|
| `FULL_EDGE` | Start is edge origin; end is edge terminus | `[0, edge_length_m]` | Whole edge is inside coverage; no boundary derivation is needed | Non-zero start, end different from edge length, or a partial interval |
| `PARTIAL_START_EDGE` | Observation coverage enters within this first edge and continues to its terminus | `[start_position_m, edge_length_m]` | First row of a multi-edge sequence; `0 < start < length`; boundary evidence is reproducible | Not first, end not equal to length, missing boundary provenance, or zero/full-length interval |
| `PARTIAL_END_EDGE` | Coverage enters at edge origin and leaves within this final edge | `[0, end_position_m]` | Last row of a multi-edge sequence; `0 < end < length`; boundary evidence is reproducible | Not last, non-zero start, missing boundary provenance, or zero/full-length interval |
| `PARTIAL_SINGLE_EDGE` | Both observation boundaries fall inside the same edge | `[start_position_m, end_position_m]` | Only row; `0 <= start < end <= length`; both boundary derivations are represented by the evidence record | More than one row, zero-length interval, or missing provenance for either derived boundary |

At most the first and last rows may be partial. An interior row must be `FULL_EDGE`.
`PARTIAL_SINGLE_EDGE` cannot coexist with another row for the same section/direction.
The v1 CSV has one provenance tuple per row; a single-edge case with two independently
derived anchors must reference a compound evidence record that contains both anchors.

## 4. Boundary provenance and derivation rule

`DERIVED_BY_GEOMETRIC_PROJECTION` means the position is a computed fact, not the
official Road Census boundary. For rule
`PROJECT_OPPOSITE_DIRECTION_BOUNDARY_TO_EDGE_V1`:

1. use the already direction-resolved opposite carriageway sequence as the boundary
   anchor source;
2. take the specified endpoint (`DOWN_CORRIDOR_START` or `DOWN_CORRIDOR_END`);
3. project that point orthogonally to the directed candidate SUMO edge;
4. store the along-edge distance as the appropriate start/end position; and
5. store point-to-projection distance as `projection_error_m`.

The source direction decision, SUMO network, selected sequence, and rule inputs must be
hash-addressed in the manifest. A derived boundary is valid only when its projection is
on the edge, route identity and topology pass, contamination passes, the unchanged
spatial criteria pass, and the derivation reproduces within 0.001 m. Projection error
is evaluated against the existing `candidate_buffer_m`; no new threshold is introduced.

## 5. Formal adoption rule v1

`ACCEPTED_AS_PARTIAL_EDGE_MAPPING` requires all of the following:

- schema, position, used-length, and role consistency pass;
- the ordered edge sequence is unchanged and topologically connected;
- route identity is supported by canonical route evidence, not numeric `ref` alone;
- no internal, link, ramp/frontage, cross-route, or other-carriageway contamination;
- each derived position reproduces within 0.001 m;
- official-geometry coverage and both directional-axis coverage ratios meet the existing
  `high_section_coverage_ratio` (0.60 in the locked configuration);
- endpoint difference and projection error are no greater than the existing
  `candidate_buffer_m` (25 m in the locked configuration); and
- official direction is resolved.

Failure is classified without forced adoption as `ROUTE_IDENTITY_CONFLICT`,
`TOPOLOGY_CONFLICT`, `CARRIAGEWAY_IDENTIFICATION_FAILURE`,
`OFFICIAL_DIRECTION_UNRESOLVED`, `GENUINE_GEOMETRY_MISMATCH`, or
`INSUFFICIENT_EVIDENCE`. Candidate extraction is not automatic adoption.

## 6. Downstream meaning

| Consumer | Level read | Meaning of a partial edge |
|---|---|---|
| Traffic assignment and simulation | edge-level | Vehicles remain on the original SUMO edge |
| Calibration and edge traffic counts | edge-level | The full observed series is repeated on selected edges; no length apportionment |
| Road Census/observation spatial join | edge-segment-level | Use only the declared interval for spatial correspondence |
| Coverage, boundary, endpoint and mapping QA | edge-segment-level | Recompute geometry and endpoint metrics from declared intervals |
| Spatial aggregation | edge-segment-level where supported | Clip spatial support, but do not invent a new SUMO edge or traffic count |

An application must not interpret a partial interval as a new edge ID.

## 7. Network-wide screening

The reusable validator inventories all 66 base Road Census mappings and the nine current
external-observation direction targets. It screens existing review, low-coverage,
boundary-mismatch, and endpoint-mismatch evidence. It emits a classification and the
next evidence required. Only a direction-resolved candidate with an official or formally
derived boundary anchor can become `PARTIAL_EDGE_REVIEW_CANDIDATE`; all other cases stay
in one of the conflict/unresolved classes above until evidence exists.

