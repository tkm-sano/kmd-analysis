# Network Build Architecture

## Component Responsibility

| Component | Sole decision responsibility | Inputs | Outputs |
|---|---|---|---|
| Relation Closure | Governed relation scope, recursive member completion and analysis/support roles | registered BBOX PBF, regional source PBF, N03 boundary, closure config | relation-closed PBF/XML, element roles, closure manifest |
| Resolver | OSM attribute interpretation and expected permissions | governed OSM XML, typemap, config, evidence tables | normalized OSM, permission expectations, audit, summary |
| Provisional Build | SUMO topology creation and exact source lineage | normalized OSM, typemap, reviewed node joins | plain XML, edge provenance, provisional logs |
| Permission Materializer | Lane/connection permission projection and zero-permission removal | expectations, provenance, provisional edge/connection XML | permission edge/connection XML, audit, summary/failure |
| TLS Review | Signal selection and connection-to-link assignment | final permission connection set, provisional TLS evidence | reviewed connection XML, reviewed TLS XML, review manifest |
| Final Build | Deterministic execution of approved conversion inputs | reviewed node/edge/connection/TLS inputs, manifest | formal `net.xml`, logs, build summary |
| Post-build Audit | Detection and readiness decision without repair | expectations, lineage, reviewed inputs, `net.xml`, logs | audit report and acceptance state |

No downstream component MAY independently reinterpret OSM access tags or invent a missing governed attribute.

## Data Flow

```text
registered OSM + evidence + config
  -> Relation Closure
  -> relation-closed OSM + element roles + closure manifest
  -> Resolver
  -> normalized OSM + permission_expectations.json
  -> Provisional Build
  -> plain XML + edge_provenance.json
  -> Permission Materializer
  -> governed_permissions.edg.xml + governed_permissions.con.xml
  -> TLS Review
  -> governed_reviewed.con.xml + governed_reviewed.tll.xml
  -> Final Build
  -> formal.net.xml
  -> Post-build Audit
  -> accepted formal network
  -> demand/calibration/comparison
```

## Readiness Gates

| Gate | Evaluated | May depend on |
|---|---|---|
| `formal_build_input_ready` | Immediately before final `netconvert` | Resolver, provisional build, materializer, junction/TLS review, validators, manifest |
| `formal_network_acceptance` | After final build | input gate plus build, load, warning, lineage, permission and structural audits |
| `downstream_experiment_ready` | Before formal demand/calibration/optimization | accepted network plus candidate-subgraph, observation, calibration and comparison registrations |

## Normative Requirements

| ID | Requirement | Failure | Test |
|---|---|---|---|
| ARC-REQ-001 | Every artifact MUST declare `artifact_type`, `schema_version`, `config_id` and `config_version`. | BLD001 | ARC-TST-001 |
| ARC-REQ-002 | An artifact MUST NOT cross a component boundary unless its schema and recorded input hashes validate. | BLD002 | ARC-TST-002 |
| ARC-REQ-003 | Readiness gates MUST form the declared acyclic order and partition their requirement matrix. | BLD003 | ARC-TST-003 |
| ARC-REQ-004 | Generated `net.xml` MUST be audit-only and MUST NOT be patched. | PA001 | ARC-TST-004 |
| ARC-REQ-005 | A changed upstream artifact hash MUST invalidate all dependent review and acceptance states. | BLD004 | ARC-TST-005 |
| ARC-REQ-006 | Structural and formal outputs MUST use separate directories, manifests and identifiers. | BLD005 | ARC-TST-006 |

## State Propagation

`failed`, `invalidated`, `rejected`, `pending` and `conditional` never evaluate as eligible. Only `eligible=true` and `state=eligible` satisfy a requirement. A component failure preserves its governed audit/failure report but cannot publish a success output.
