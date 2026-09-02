# Phase 12 Validated Successor Blocker Reduction Plan v1

This plan is anchored to `phase12_validated_successor_baseline_20260902_v1_2`.
It decomposes the current Formal blocker inventory without resolving any
blocker, adopting a new research decision, relaxing Formal policy, or
building a SUMO network.

## Baseline scope

The canonical baseline is run_4 at source commit
`0cbdb1ec392115468f14e9665e46af67e74ef43d`, configuration
`ota_ward_sumo_network_v17` v17, Decision A v1.1.0, Phase 12 contract v1.2.0,
and population accounting schema v17.2.0. The current Formal blocker count is
115,935 for population `ota_ward_relation_closure_v16`. The run_5 rerun is a
determinism witness; its temporary run-id manifest-enum workaround is recorded
as a pipeline governance gap, not as a baseline rule.

## Decomposition by attribute and evidence class

Counts below are blocker records from the run_4 inventory. A source Way may
occur in multiple downstream attributes; those occurrences are retained as
manifestations, not summed as independent root causes.

| Attribute | Total | genuine_rule_conflict | missing_evidence | missing_registered_rule | unsupported_source_syntax | Affected source Ways |
|---|---:|---:|---:|---:|---:|---:|
| speed | 78,616 | 0 | 78,601 | 0 | 15 | 23,135 |
| directional_lanes | 22,934 | 25 | 22,729 | 0 | 180 | 22,934 |
| final_permission | 14,302 | 0 | 0 | 14,302 | 0 | 2,473 |
| conditional_access | 35 | 0 | 1 | 0 | 34 | 35 |
| directed_segments | 48 | 0 | 48 | 0 | 0 | 1 |
| **Total** | **115,935** | **25** | **101,379** | **14,302** | **229** | **25,789 unique across inventory** |

The inventory has no separate evidence-class field; the four evidence classes
above are the inventory `root_cause_category` values. Attribute totals and
root-cause totals reconcile exactly to the inventory total.

## Root-cause hierarchy

1. `missing_evidence` (101,379) is the dominant upstream evidence deficit.
   It manifests mainly in speed (78,601), directional lanes (22,729), plus
   directed segments (48) and conditional access (1). The same source relation
   or Way can therefore create several downstream records.
2. `missing_registered_rule` (14,302) is concentrated in final permission.
   These records are downstream permission manifestations and must not be
   treated as permission-only evidence that can authorize Formal output.
3. `unsupported_source_syntax` (229) affects directional lanes (180),
   conditional access (34), and speed (15). It requires a registered remedy;
   parser fallback is not authorized by this plan.
4. `genuine_rule_conflict` (25) is confined to directional lanes and remains
   a decision-sensitive group until its conflict semantics are reviewed.

## Priority blocker groups

### P0 — Freeze and repair blocker lineage/projection

- Count: 115,935 records; root-cause groups remain as above.
- Affected population: all five attributes, 25,789 unique source Ways in the
  inventory.
- Action: preserve the run_4 inventory as the immutable baseline; add a
  root-cause-to-downstream projection keyed by source Way/relation and stage.
- Research decision: no.
- Expected impact: prevents double-counting and makes later reductions
  auditable; resolves no Formal blocker by itself.
- Implementation location: Phase 12 accounting/reporting and blocker lineage
  tooling.
- Validation: inventory total reconciliation, unique source identity checks,
  blocker/root-cause relationship checks, and repeat semantic hashing.

### P1 — Directional-lane upstream evidence and syntax decomposition

- Count: 22,934 (`missing_evidence` 22,729, `genuine_rule_conflict` 25,
  `unsupported_source_syntax` 180).
- Affected source Ways: 22,934.
- Root cause: evidence gap, syntax gap, and a small decision-sensitive conflict
  group.
- Action: separate source-evidence acquisition, parser coverage, and conflict
  review; map downstream speed/permission impacts before implementation.
- Research decision: required only for the 25 conflicts; not for mechanical
  inventory/provenance work.
- Expected downstream impact: directional-lane remediation can reduce related
  speed and permission manifestations, but must be measured by lineage rather
  than added counts.
- Implementation location: directional lane resolver, evidence registry,
  blocker relationship projection.
- Validation: lane fixture tests, source-evidence provenance checks,
  population accounting, and no unauthorized Formal assumptions.

### P2 — Speed evidence coverage

- Count: 78,616 (`missing_evidence` 78,601, `unsupported_source_syntax` 15).
- Affected source Ways: 23,135.
- Root cause: missing source/rule evidence and a small syntax coverage gap.
- Action: inventory existing authoritative speed evidence by source Way and
  classify records that are genuinely absent versus parser-unsupported.
- Research decision: not for evidence cataloging; required before any new
  speed inference or fallback rule.
- Expected downstream impact: potentially largest materialization-readiness
  improvement, but only after evidence is registered and Formal eligibility is
  independently validated.
- Implementation location: speed resolver, Japan speed-rule registry,
  evidence/provenance records.
- Validation: speed fixtures, source evidence hashes, blocker projection,
  population equations, and determinism.

### P3 — Final-permission rule registration

- Count: 14,302 (`missing_registered_rule`).
- Affected source Ways: 2,473; vehicle class: delivery.
- Root cause: missing registered permission rule.
- Action: identify the governing source tags and candidate rule coverage;
  register only already-authorized rules or prepare a separate decision packet.
- Research decision: required for new permission semantics; not for mechanical
  coverage reporting.
- Expected downstream impact: can reduce final-permission blockers after lane
  and access provenance are valid; cannot authorize unresolved or fabricated
  records.
- Implementation location: static/final permission resolvers, rule registry,
  formal evidence registry.
- Validation: permission tuple fixtures, lane-to-permission lineage, blocker
  root-cause links, and Formal zero gates.

### P4 — Unsupported syntax remediation

- Count: 229 across directional lanes (180), conditional access (34), and
  speed (15).
- Affected source Ways: 229 by current record projection.
- Root cause: unsupported source syntax.
- Action: build minimal syntax fixtures and specify parser behavior; preserve
  blockers until a registered remedy exists.
- Research decision: required only if semantics are ambiguous; parser support
  alone is mechanical when semantics are already normative.
- Expected downstream impact: can remove syntax-specific manifestations in
  three stages and expose the remaining evidence requirement.
- Implementation location: source parsers, grammar registries, stage-specific
  validators.
- Validation: positive/negative syntax fixtures, provenance, no fallback
  adoption, and semantic determinism.

### P5 — Directed-segment relation mapping

- Count: 48 (`missing_evidence`), one affected source Way/relation projection.
- Root cause: missing directed mapping evidence.
- Action: inspect relation closure and directed-segment mapping evidence; do not
  infer missing mappings from downstream artifacts.
- Research decision: only if relation semantics are ambiguous.
- Expected downstream impact: may unblock dependent lane/speed/permission
  records for the affected relation.
- Implementation location: directed-segment builder and relation evidence
  records.
- Validation: relation identity closure, directed-segment fixtures, lineage,
  and population accounting.

## Research decisions required

No new decision is adopted by this plan. Decision packets may be required for:

- the 25 directional-lane genuine conflicts;
- any new permission semantics for the 14,302 final-permission records;
- any speed or access inference not directly supported by registered evidence;
- any interpretation of ambiguous unsupported syntax.

Formal policy relaxation, typemap fallback, and imputation remain prohibited.

## Mechanical pipeline gaps

- Add root-cause-to-downstream blocker projection without changing blocker
  semantics.
- Add attribute/stage decomposition reports with unique source identity
  counts.
- Add a canonical determinism runner accepting arbitrary valid run IDs.
- Extend the successor manifest and determinism schemas together when the
  run-ID contract is formally amended.

## Run-ID contract issue

The run_5 workaround is a `PIPELINE_GAP` / governance improvement, not a
baseline validity failure: run_5 used the same commit, inputs, semantic
artifacts, counts, provenance, and validators as run_4. It should be corrected
before future reruns so the manifest schema, CLI, executor, and determinism
report all accept the same run-ID set without temporary validation bypass.

## Explicit non-actions

This plan does not resolve blockers, adopt decisions, relax Formal policy,
adopt typemap fallback or imputation, produce Permission Materializer output,
build the final SUMO network, or advance Formal Network Acceptance.
