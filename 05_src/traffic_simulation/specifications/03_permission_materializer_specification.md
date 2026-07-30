# Permission Materializer Specification

> Version note: v17 uses Resolver expected permissions as the formal authority.
> Any v16 clause that intersects the final set with a typemap baseline is
> superseded by `10_approved_attribute_resolution_policy.md`.

## Scope and Authority

The Materializer projects already-decided permissions onto SUMO 1.24.0 plain XML. It MUST NOT interpret source access tags, choose a typemap type, guess topology, create a turn or finalize TLS logic.

## Preconditions

The following MUST validate before any success output is written:

- `permission_expectations.json` v2 with `complete=true` and zero blockers.
- `edge_provenance.json` v1.
- provisional `.edg.xml` against pinned `edges_file.xsd`.
- provisional `.con.xml` against pinned `connections_file.xsd`.
- exact `config_id`, config version and all recorded hashes.
- formal use requires profile `formal`.

## Exact Edge Mapping

Formal mapping uses `edge_provenance.json`; coordinate-nearest matching is prohibited. Each external provisional edge MUST have one governed OSM way ID, one SUMO type, a nonempty ordered source-node subsequence and source start/end indices.

```text
start_index < end_index => forward
start_index > end_index => backward
start_index = end_index => PM006
```

All source nodes MUST occur in the normalized OSM way in the recorded order. Reviewed node joins MUST supply explicit source-node lineage. An OSM way MAY map to multiple ordered edge records. SUMO edge-ID sign is never direction evidence.

## Lane Mapping

Resolver position `p` is left-to-right in the relevant travel direction. SUMO index 0 is the rightmost lane. For direction lane count `n`:

```text
sumo_lane_index = n - 1 - p
```

This formula applies to forward and backward records. SUMO lane children MUST have unique contiguous indices `0..n-1`, and edge `numLanes`, provenance lane count and expectation lane count MUST agree.

## Permission Normalization

The universe is the seven governed vClasses in `sumo_network.yml`. Tokens are ASCII, case-sensitive and deduplicated before comparison.

| Plain XML state | Effective provisional set |
|---|---|
| neither `allow` nor `disallow` | all governed vClasses |
| `allow="all"` | all governed vClasses |
| `disallow="all"` | empty set |
| explicit `allow` | listed governed classes |
| explicit `disallow` | governed universe minus listed classes |

Empty strings, unknown/unmanaged tokens and simultaneous `allow` plus `disallow` are rejected. The final lane set is expectation intersected with typemap baseline, governed universe and effective provisional restriction. A nonempty set is written as a lexicographically sorted `allow` with `disallow` removed.

## Empty Lane and Edge Rules

- If at least one lane on the directed edge remains usable, an empty lane is retained with `disallow="all"` and no `allow`.
- If every lane on a directed edge is empty, the entire edge and every incident candidate connection are removed and recorded as `zero_permission_edge`.
- Edge removal MUST preserve an explicit OSM-way/edge/action audit and MUST occur before TLS review.

## Connection Rules

Only explicit lane-to-lane `<connection>` elements with nonempty `from`, `to`, `fromLane` and `toLane` are supported. Their unique identity is `(from, to, fromLane, toLane)`. Duplicates stop.

```text
connection_allow = from_lane_allow
                   intersect to_lane_allow
                   intersect effective_provisional_connection_allow
```

Nonempty sets are written as sorted `allow`; empty connections are removed. Missing candidate turns are never synthesized. `prohibition` and `delete` elements are preserved only when all referenced edges remain and are recorded; unresolved references stop. `crossing` and `walkingArea` are prohibited in the governed motorized materializer input. Other elements stop as unsupported.

TLS assignments are not stored in the 1.24.0 connection type. The Materializer does not modify or emit final `.tll.xml`; provisional TLS output is evidence only and the TLS Review creates the reviewed file after permissions are fixed.

## Deterministic Output

Outputs MUST use UTF-8, XML declarations, LF endings, no generator timestamp comment, source element order for retained objects, numeric lane order, lexicographically ordered vClasses and deterministic attribute order defined by the serializer. Writes are atomic, partial success files are removed and existing outputs are not overwritten.

## Normative Requirements

| ID | Requirement | Failure | Test |
|---|---|---|---|
| PM-REQ-001 | All preconditions and hashes MUST validate before transformation. | PM001-PM005 | PM-TST-001 |
| PM-REQ-002 | Edge direction MUST come only from exact lineage indices. | PM006-PM009 | PM-TST-002 |
| PM-REQ-003 | Every external lane MUST map exactly once by the fixed lane formula. | PM010-PM013 | PM-TST-003 |
| PM-REQ-004 | Permission tokens MUST follow the closed normalization table. | PM014-PM016 | PM-TST-004 |
| PM-REQ-005 | Materialized lane permissions MUST equal the governed intersection exactly. | PM017 | PM-TST-005 |
| PM-REQ-006 | Partial and complete empty-edge cases MUST follow the fixed removal rules. | PM018 | PM-TST-006 |
| PM-REQ-007 | Connection identity, intersection and removal MUST follow this specification without guessing. | PM019-PM022 | PM-TST-007 |
| PM-REQ-008 | Supported nonconnection elements MUST be preserved and unsupported elements MUST stop. | PM023 | PM-TST-008 |
| PM-REQ-009 | TLS logic MUST remain outside Materializer output responsibility. | PM024 | PM-TST-009 |
| PM-REQ-010 | Success output and audit MUST be deterministic, atomic and non-overwriting. | PM025-PM027 | PM-TST-010 |
| PM-REQ-011 | The audit and summary MUST conform to their schemas and account for every input edge, lane and connection. | PM028 | PM-TST-011 |
