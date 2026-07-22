# TLS Review Specification

## Scope

TLS Review starts only after the permission edge and connection set is fixed. It owns signalized-junction selection and connection-to-link assignment. It does not change lane/connection permissions or calibrate observed timing.

## States

| State | Meaning |
|---|---|
| `not_required` | No signalized junction is in scope |
| `review_required` | A governed connection set exists but has no accepted mapping |
| `reviewed` | Mapping and evidence are accepted for the recorded connection hash |
| `invalidated` | An upstream connection/node hash changed after review |
| `rejected` | Reviewer found an unresolved structural problem |

Only `not_required` and `reviewed` can satisfy the TLS input gate.

## Normative Requirements

| ID | Requirement | Failure | Test |
|---|---|---|---|
| TLS-REQ-001 | Review MUST use the SHA-256 of canonical permission connections and reviewed nodes as its identity. | TLS001 | TLS-TST-001 |
| TLS-REQ-002 | Provisional `.tll.xml` MAY be evidence but MUST NOT be final input. | TLS002 | TLS-TST-002 |
| TLS-REQ-003 | Every controlled lane-to-lane connection MUST have one TLS ID and valid `linkIndex`; `linkIndex2` MUST be absent unless its governed use is documented. | TLS003 | TLS-TST-003 |
| TLS-REQ-004 | Link indices for each TLS MUST be contiguous from zero with no duplicate controlled connection identity. | TLS004 | TLS-TST-004 |
| TLS-REQ-005 | Every phase state string MUST have exactly the controlled-link count for its TLS program. | TLS005 | TLS-TST-005 |
| TLS-REQ-006 | Reviewed `.con.xml` MUST preserve permission-materialized connection identities and permissions exactly. | TLS006 | TLS-TST-006 |
| TLS-REQ-007 | Any node, edge, connection or permission hash change MUST set the review to `invalidated`. | TLS007 | TLS-TST-007 |
| TLS-REQ-008 | A review MUST record reviewer, UTC review time, evidence references, decisions and rejected items. | TLS008 | TLS-TST-008 |
| TLS-REQ-009 | Reviewed connection, TLS XML and manifest MUST validate against pinned XSD/schema before eligibility. | TLS009 | TLS-TST-009 |
| TLS-REQ-010 | Signal cycle, duration, split and offset values without observed evidence MUST be marked initialized, not observed. | TLS010 | TLS-TST-010 |

## Outputs

- `governed_reviewed.con.xml`
- `governed_reviewed.tll.xml`
- `tls_review_manifest.json`

The reviewed connection file is the permission connection file plus reviewed structural TLS association where supported by the pinned plain-XML interfaces. TLS connection-to-link records reside in the `.tll.xml` artifact. Timing calibration may later update timing values under a new manifest without changing controlled connection identities.
