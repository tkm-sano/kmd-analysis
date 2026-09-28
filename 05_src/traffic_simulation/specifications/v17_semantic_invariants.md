# v17 属性解決意味上の Invariants

## 文書管理

- Invariant set: `ota_ward_attribute_resolution_semantic_invariants_v17`
- Version: `1.8.0`
- Policy: `ota_ward_attribute_resolution_policy_v17`
- Machine-readable authority: `reproducibility/config/traffic_simulation/v17_semantic_invariants.yml`
- Schema: `reproducibility/config/traffic_simulation/schemas/semantic_invariants_v17.schema.json`

This document separates constraints that JSON Schema can enforce locally from
cross-record, set, population, provenance, and determinism constraints. The
machine-readable file fixes each invariant's ID, assertion, failure state,
stop code, severity, and implementation phase.

<a id="invariant-families"></a>

## 不変条件の分類

| Family | IDs | Responsibility |
|---|---|---|
| State contract | `AR-STATE-001`–`005` | resolved/non-resolved fields, formal eligibility, legacy output, conflict evidence |
| Identity | `AR-ID-001`–`003` | RFC 8785 record identity, uniqueness, classification projection invariance |
| 方向付き区間 | `AR-DIR-001`–`005` | canonical interval, lineage, `oneway=-1`, relation mapping, prohibited direction evidence |
| Directional lanes | `AR-LANE-001`–`004`, `008`–`010` | count equation, vector length, profile boundary, approved Phase 13 formal rules, source/materialization separation, SUMO index mapping |
| 速度 | `AR-SPEED-001`–`003` | unit conversion, priority/asymmetry, interval changes |
| Access | `AR-ACCESS-001`–`012` | scope separation, ontology sets, dominance, order invariance, permission authority, non-governed domain intersection, key-scoped access-value semantics and source specificity |
| Conditional | `AR-COND-001`–`004` | context, syntax boundary, last-match boundary, interval changes |
| 根拠 | `AR-EVID-001`–`003` | method approval, donor eligibility, immutable manual evidence |
| Population | `AR-EXCL-001`–`003` | population equation, registered exclusions, omission accounting |
| 出典・来歴 | `AR-PROV-001`–`004` | canonicalization, manifests, determinism, profile-separated outputs |
| Acceptance | `AR-ACC-001`–`003` | zero-blocker gate, validation layers, missing-evidence result |

<a id="validation-boundary"></a>

## 検証 境界

JSON Schema validates required fields, types, enums, local nullability, the
formal prohibition on `model_assumed`, and manifest shapes. The Phase 1
authority validator validates configuration/Schema/Registry synchronization,
registered references, hashes, uniqueness, and invariant coverage. Runtime
semantic evaluation of Resolver output is implemented in the target phase
recorded for each invariant; Phase 1 completion does not claim those later
runtime checks have executed.

An invariant failure is fail-closed. A missing implementation or missing
runtime artifact is not evidence that an invariant passed.

<a id="ar-lane-009-one-way-count-from-approved-road-lane-vectors"></a>

### `AR-LANE-009`: 一方通行件数からの承認済み road-車線ベクトル

Under `DEC-P13-LANE-COUNT-FROM-ROAD-LANE-VECTOR-001`, a formal canonical
one-way road with no explicit total or active-direction lane count may derive
the missing count only from equal positive pipe-field counts on exact
`turn:lanes`, `destination:lanes`, or `destination:ref:lanes` tags. The value
is `rule_derived`, formal eligible, and retains the complete source vectors.
No other `*:lanes` family is lane-count authority. Conflicting approved vectors
remain unresolved, while explicit counts retain precedence and are still
checked against every vector with `LANE_VECTOR_LENGTH_MISMATCH` on mismatch.

<a id="ar-access-009-non-governed-vehicle-domain"></a>

### `AR-ACCESS-009`: non-管理対象の車両領域

A vehicle-specific access key may have an empty intersection with the governed
motorized vehicle universe only when a versioned decision is registered. For
`DEC-P13-HORSE-ONTOLOGY-001`, scalar `horse=yes` and `horse=no` normalize to an
empty vehicle domain. They preserve the source key, source value, Way identity,
and provenance, but neither allow nor deny the managed `delivery` vehicle and
never authorize exclusion. Parent and motorized-specific rules remain effective.
Other `horse` values and conditional, directional, or lane-scoped syntax remain
fail-closed until separately approved.

<a id="ar-access-011-key-scoped-use_sidepath-semantics"></a>

### `AR-ACCESS-011`: キー-scoped `use_sidepath` 意味

Under `DEC-P13-USE-SIDEPATH-SEMANTICS-001` version 1.1.0, scalar
`bicycle=use_sidepath` and `foot=use_sidepath` preserve the OSM meaning
`parallel_way_required`; neither is rewritten to `no`. Both registered governed
vehicle domains are exactly empty. Source key, value, Way identity, decision
provenance, and deferred `foot:conditional` provenance remain traceable, but
these statements never change a governed static maximum. The same value on
`access`, `vehicle`, or `motor_vehicle`, as well as typos and unknown values,
remains fail-closed.

<a id="ar-access-012-source-hierarchy-after-governed-domain-projection"></a>

### `AR-ACCESS-012`: 出典階層後の管理対象の-領域射影

The registered OSM access-key ancestry remains part of vehicle specificity
after projection into the governed vClass universe. If a child and parent
project to equal sets, the child is still strictly more specific for their
shared tuples. This preserves, for example, `motor_vehicle` precedence over
`vehicle`. The relation is read from the registry, not inferred from key names
or equal sets; unrelated keys do not override one another, and record order is
never a tiebreak.
