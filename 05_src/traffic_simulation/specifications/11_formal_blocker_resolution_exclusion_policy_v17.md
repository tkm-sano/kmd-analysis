# Formal Blocker Resolution and Exclusion Policy v17

Status: approved  
Approved by: repository owner directive  
Approval date: 2026-08-04

## Purpose

Every formal blocker shall receive exactly one strategy:

- `preserve_and_resolve`: retain it in the governed population and remediate its root cause;
- `formal_exclusion`: remove it only after outside-scope status is proven by an approved, versioned exclusion rule;
- `remain_blocked`: retain fail-closed state when scope or value cannot currently be proven.

The default is `preserve_and_resolve`. Exclusion is not attribute resolution and shall never add `out_of_scope` to `resolution_status`.

## Mandatory identification and root cause

Every inventory entry shall contain `record_id`, `source_way_id`, `directed_segment_id`, `lane_position`, `vehicle_class`, `attribute_name`, and `stop_code`. Inapplicable fields shall be explicit `null` values.

The single most-upstream cause shall be selected from:

`implementation_defect`, `missing_registered_rule`, `unsupported_source_syntax`, `missing_scenario_context`, `missing_vehicle_ontology`, `missing_evidence`, `genuine_rule_conflict`, `outside_research_scope`, or `undetermined`.

Downstream effects belong in `secondary_causes`. `ACCESS_PERMISSION_UNRESOLVED` shall not be treated as the root cause when an upstream attribute record caused it. Permission blockers shall retain their causal upstream record IDs and shall be regenerated after upstream remediation.

## Scope decision

The decision order is mandatory:

1. identify the record and attribute tuple;
2. identify the most-upstream root cause;
3. determine whether the tuple is governed by the current Configuration;
4. determine whether a registered rule, implementation, Scenario Context, ontology, or evidence could resolve it;
5. consider exclusion only when outside-scope status is independently proven;
6. otherwise retain a blocker.

Missing OSM attributes, unsupported syntax, incomplete implementation, high blocker volume, schedule pressure, and a desire to pass acceptance are never exclusion evidence.

## Strategy rules

- Governed records with an implementable or registrable remedy use `preserve_and_resolve`.
- Proven outside-scope records use `formal_exclusion` only when all exclusion requirements pass.
- Missing evidence, unresolved formal conflicts, undetermined scope, or partially satisfied exclusion conditions use `remain_blocked`.
- A record shall never carry more than one strategy.

General-road direction, Directed Segment mapping, directional lanes, lane vectors, access rules, conditional grammar, Scenario Context, vehicle ontology, speed rules, production defects, and registry/schema/configuration inconsistencies are remediation work, not exclusion reasons.

## Resolution change order

Every new resolving rule shall be introduced in this order:

1. Decision Record;
2. Registry or Decision Table;
3. JSON Schema;
4. Semantic Invariant;
5. small fixture;
6. production-independent oracle;
7. production code;
8. phase test;
9. regression test;
10. full-population run.

Source OSM, generated JSON, and generated `.net.xml` shall not be manually patched.

## Formal exclusion

All of the following are mandatory:

1. the target is outside the current research purpose;
2. Configuration, road function, source evidence, or an approved Decision Record proves that fact;
3. a versioned exclusion rule is registered;
4. reason, evidence, approver, and approval date are recorded;
5. the population equation remains valid.

Every excluded entry shall be written to the Exclusion Manifest with all fields required by `exclusion_manifest_v17.schema.json`. Unregistered rules stop with `EXCLUSION_RULE_UNREGISTERED`. `private` alone is not an exclusion rule.

## Population accounting

Every population dimension shall satisfy:

`input = governed + excluded`

Every governed attribute collection shall satisfy:

`governed = resolved + unresolved + conflict + invalid + valid_but_unsupported`

An ID shall not occur in both governed and excluded sets. Exclusions shall not be counted as resolved records. Materialization omission remains separate from exclusion.

## Phase sequencing and acceptance

Phase 9 through Phase 12 may continue with explicit blockers. Phase 13 remediation priority is implementation defects, Directed Segment/relation mapping, directional lanes, Scenario Context, vehicle ontology, static access, conditional access, speed, evidence resolution, then formal exclusion.

Phase 14 may permit a formal build only when blockers, review-required records, unresolved stops, and model assumptions are all zero; all governed records are resolved; permission coverage and population equations are complete; and schema, semantic, oracle, and two-run determinism checks pass.

This policy does not itself approve an exclusion, resolve a blocker, or declare Attribute Resolution Acceptance.
