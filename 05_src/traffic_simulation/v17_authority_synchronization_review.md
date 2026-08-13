# v17 Authority Synchronization Review

## Review control

- Review ID: `ota_ward_v17_phase1_authority_review_20260803`
- Policy: `ota_ward_attribute_resolution_policy_v17`
- Configuration: `ota_ward_sumo_network_v17`
- Baseline date: 2026-08-03
- Reviewer role: repository implementation agent
- Approval authority: repository owner directive
- Review result: Phase 1 authority aligned
- Runtime Resolver acceptance: not run
- Formal network status: not ready

## Scope

The review compared the complete v17 specification with the pre-existing
policy YAML, Schemas, configuration, utilities, fixtures, validators, and v16
state. Phase 1 findings concern authority synchronization only. Production
integration findings assigned to Phases 2–14 remain planned work and do not
represent Phase 1 authority conflicts.

## Phase 1 findings

| finding_id | category | initial condition | required condition | severity | resolution | status |
|---|---|---|---|---|---|---|
| V17-P1-001 | `enum_conflict` | Existing policy used `not_applicable` and `unsupported`. | Five canonical `resolution_status` values, including `valid_but_unsupported`. | critical | Configuration, record Schema, Registry, and validator now use one enum. | resolved |
| V17-P1-002 | `semantic_conflict` | Existing Directed Segment IDs used `way/.../direction/F|B`. | Canonical interval ID `ds:way:start:end:direction`. | critical | v17 Configuration and dedicated Schema use the canonical interval form. | resolved |
| V17-P1-003 | `semantic_conflict` | Direction and lane were included in access specificity. | Direction/lane are target scope; four set axes are separate. | critical | Configuration and AccessRule Schema separate the concepts. | resolved |
| V17-P1-004 | `missing_artifact` | No separate v17 network-state Configuration existed. | v16 history preserved and v17 state independently selected. | major | Added `sumo_network_v17.yml`; existing `sumo_network.yml` is unchanged. | resolved |
| V17-P1-005 | `missing_artifact` | Required v17 artifact Schemas were incomplete. | Record, segment, access, exclusion, omission, environment, acceptance, and configuration Schemas exist. | major | Added all required dedicated v17 Schemas and Schema validation. | resolved |
| V17-P1-006 | `missing_artifact` | Finite states, origins, rules, ontology, assumptions, and stop codes were spread across files/code. | One versioned, hash-bound Registry authority exists. | major | Added the v17 Registry bundle with 30 registered stop codes. | resolved |
| V17-P1-007 | `validator_gap` | No Phase 1 cross-artifact synchronization validator existed. | References, versions, hashes, enums, IDs, and coverage fail closed. | major | Added `validate_v17_phase1_authority` and focused tests. | resolved |
| V17-P1-008 | `documentation_only` | The complete specification remained a draft with unchecked approval items. | Repository approval and Phase 2 fixture/oracle boundary are explicit. | major | Recorded repository-owner approval and fixed the Phase 2 boundary. | resolved |
| V17-P1-009 | `authority_conflict` | Existing links pointed to a shorter policy summary. | One complete normative v17 baseline has precedence. | major | The legacy summary now carries a compatibility notice and precedence link. | resolved |

## Deferred implementation findings

These are required by the normative implementation order but are not Phase 1
authority defects.

| finding_id | category | current behavior | required behavior | severity | target_phase | status |
|---|---|---|---|---|---:|---|
| V17-IMP-001 | `fixture_gap` | Existing fixtures primarily exercise v16/isolated utilities. | Freeze independent v17 fixtures and production-independent oracles. | major | 2 | planned |
| V17-IMP-002 | `obsolete_v16_behavior` | Production output still uses legacy state shapes in places. | v17 writers emit only `resolution_status`/`value_origin`. | major | 3 | planned |
| V17-IMP-003 | `semantic_conflict` | Existing Directed Segment utility uses the legacy segment-index ID. | Integrate canonical interval IDs with exact lineage. | critical | 4 | planned |
| V17-IMP-004 | `validator_gap` | Runtime lane/access/conditional/speed invariants are not integrated end-to-end. | Implement the invariant targets in dependency order. | critical | 5–11 | planned |
| V17-IMP-005 | `missing_artifact` | No v17 full-population runner or run manifest exists. | Separate structural/formal runs and population accounting. | critical | 12 | planned |
| V17-IMP-006 | `evidence_gap` | Attribute Resolution Acceptance has not run. | Execute all Section 18 checks with two-run determinism. | critical | 14 | planned |

Deferred critical items prohibit formal execution and acceptance. They do not
permit defaults, direct source/output edits, or a claim that v17 runtime is
ready.

## Phase 1 exit assessment

- Unresolved Phase 1 critical findings: 0
- Unresolved Phase 1 major findings: 0
- Configuration/Schema/Registry enum conflicts: 0
- Unregistered Phase 1 stop codes: 0
- v16 state configuration modifications: 0
- Structural/formal output path overlap: 0
- Runtime acceptance result: `not_run`
- Formal build ready: `false`

The Phase 1 authority is complete. Work resumes at Phase 2; no full-population
v17 execution is authorized by this result alone.
