# Final Build Specification

## Boundary

Final Build is a deterministic executor. It MUST NOT resolve attributes, alter permissions, guess missing connections, join unreviewed nodes or repair TLS mappings.

## Required Inputs

- reviewed `.nod.xml`
- `governed_permissions.edg.xml`
- `governed_reviewed.con.xml`
- `governed_reviewed.tll.xml` or an eligible `not_required` TLS manifest
- typemap, config and all JSON manifests/audits
- pinned SUMO 1.24.0 container digest

## Normative Requirements

| ID | Requirement | Failure | Test |
|---|---|---|---|
| BLD-REQ-001 | `formal_build_input_ready` MUST be true before invocation. | BLD001 | BLD-TST-001 |
| BLD-REQ-002 | All config IDs, versions, input hashes and schema versions MUST agree. | BLD002 | BLD-TST-002 |
| BLD-REQ-003 | The exact container digest, SUMO/netconvert/PROJ versions, platform, locale and dependency-lock hash MUST be recorded. | BLD006 | BLD-TST-003 |
| BLD-REQ-004 | The exact ordered argument vector and working directory MUST be recorded; shell-expanded command strings are not authoritative. | BLD007 | BLD-TST-004 |
| BLD-REQ-005 | Formal options MUST disable geometry removal, automatic junction joining, TLS guessing and error ignoring. | BLD008 | BLD-TST-005 |
| BLD-REQ-006 | Every input MUST validate against its pinned schema before `netconvert`. | BLD009 | BLD-TST-006 |
| BLD-REQ-007 | `netconvert` exit code MUST be zero and its output MUST be written atomically to a new path. | BLD010 | BLD-TST-007 |
| BLD-REQ-008 | Existing formal outputs MUST NOT be overwritten; a new config/run ID is required. | BLD011 | BLD-TST-008 |
| BLD-REQ-009 | Repeated builds from identical semantic inputs MUST produce identical governed edge/lane/connection/permission/TLS content. | BLD012 | BLD-TST-009 |
| BLD-REQ-010 | Byte-identical `net.xml` is not required when pinned SUMO emits nonsemantic metadata; semantic digest and raw SHA-256 MUST both be recorded. | BLD013 | BLD-TST-010 |
| BLD-REQ-011 | A failed build MUST publish only its failure report and immutable logs, never a success manifest or accepted network. | BLD014 | BLD-TST-011 |

## Canonical Semantic Digest

The semantic digest covers sorted external edge IDs, lane indices, numeric attributes at configured precision, effective permissions, connection identities, TLS IDs/link indices and phase states. It excludes generation timestamps, comments and absolute container paths. The canonicalization implementation itself is versioned and recorded.
