# Phase 12 Full-Population Output Contract v17

Status: approved

## 1. Purpose

Phase 12 SHALL execute the structural and formal v17 Resolver profiles against the fixed
population and SHALL persist the complete, immutable evidence needed to reproduce every
count, blocker, exclusion decision, and profile difference. Phase 12 is an inventory and
accounting phase. It does not claim that formal resolution or Attribute Resolution
Acceptance is complete.

## 2. Authority and fixed inputs

The machine-readable authority is
`reproducibility/config/traffic_simulation/v17_phase12_output_contract.yml`. The source OSM,
Configuration, Registry bundle, Semantic Invariants, Scenario Context, blocker policy, and
the source Git commit SHALL be hash-bound in each run manifest. A dirty worktree is
prohibited.

## 3. Required executions

Two independent executions, `run_1` and `run_2`, SHALL be performed in fresh output
directories with identical inputs, container digest, library versions, effective arguments,
and random seeds. Each environment manifest SHALL retain its exact argument vector. For the
cross-run environment comparison only, the value following the single required `--run-id`
option SHALL equal that run's ID and SHALL be normalized to the literal `<run_id>`. No other
option or value may be ignored or normalized. Neither execution may read files produced by the other. A `published`
directory may be created from `run_1` only after every determinism-required semantic hash
matches `run_2`.

Phase 12 attribute resolution does not invoke a SUMO executable. Its environment manifest
SHALL record `sumo_version: not_invoked_phase12` rather than claiming an unexecuted runtime
version. The later SUMO Network Integration gate SHALL independently pin and execute its
required SUMO runtime.

## 4. Required artifacts

Each run SHALL contain:

1. `structural/full_population.json`
2. `formal/full_population.json`
3. `formal/blocker_inventory.json`
4. `formal/exclusion_manifest.json`, including an empty manifest when no exclusion exists
5. `population_accounting.json`
6. `environment_build_manifest.json`
7. `run_manifest.json`

`run_manifest.json` SHALL list and hash the other six run artifacts. It SHALL NOT list
itself, because a file cannot contain its own final byte hash without a circular value.

The execution root SHALL also contain `determinism_report.json`. Missing, empty-by-omission,
or manually edited generated outputs are forbidden.

The profile artifacts SHALL embed the complete outputs of Directed Segment, directional
lanes, static access, conditional access, final permission, and speed stages. Projection-
only or summary-only files do not satisfy the full-population artifact requirement.

## 5. Blocker identity and causality

Every blocker SHALL have one canonical `blocker_id`, one canonical `record_id`, a registered
`root_cause_category`, and exactly one strategy. Permission blockers SHALL contain non-empty
`root_cause_record_ids`. Upstream blockers that suppress downstream candidate creation SHALL
be recorded as `candidate_suppressed`; absence of a downstream permission record must not be
reported as zero impact. Upstream and permission blocker counts SHALL NOT be added unless a
deduplicated identity calculation is also supplied.

For `ACCESS_PERMISSION_UNRESOLVED` caused by an empty applicable rule set, Phase 12 SHALL
create one `no_applicable_access_rule` root-cause record per source Way, vehicle class, and
Scenario Context. Every affected permission tuple SHALL link to that record. The root-cause
record SHALL retain the observed access-tag keys, candidate rule IDs, and affected permission
count. The link is diagnostic evidence and SHALL NOT change the permission status to resolved.

## 6. Population accounting

Accounting SHALL be performed separately for each declared population unit. For every unit:

`input = governed + excluded`

`governed = resolved + unresolved + conflict + invalid + valid_but_unsupported`

The artifact SHALL also record blocker causality, the formal/structural population
difference by registered assumption ID, exclusion ratios, and exclusion network impact.
Empty production exclusions SHALL still report zero counts and identical before/after
network metrics.

## 7. Serialization and hashes

Semantic JSON SHALL use UTF-8, lexicographically sorted object keys, compact separators,
Unicode characters without ASCII escaping, and exactly one trailing newline in the file.
`semantic_sha256` is calculated from the canonical object after omitting only its own
`semantic_sha256` field. `byte_sha256` in a manifest is calculated over the complete stored
file bytes. Arrays that are sets SHALL be sorted by their canonical record identifiers.

Timestamps, temporary directory names, host paths, and run IDs SHALL NOT enter semantic
artifacts. They may appear only in environment or run manifests, which are excluded from
semantic determinism comparison.

Each independently executed run validator SHALL be invoked through its recorded argument
vector. The run manifest SHALL retain the validator ID, exact command vector, exit code,
captured stdout and stderr as one canonical log object, and the SHA-256 of the exact stored
log bytes. A successful run manifest requires exit code zero for every required validator;
an unrecorded, malformed, or non-zero validator execution SHALL fail the run.
Each validator SHALL report required, completed, and failed check counts. Per-category
validation results and the whole-run result SHALL be derived from those reported results;
they SHALL NOT be populated with unconditional success literals.

## 8. Atomic publication and immutability

Every artifact SHALL first be written to a file in the destination directory, flushed and
closed, validated, and then atomically renamed to its final name. Existing final files SHALL
not be overwritten. A failed run SHALL retain no `published` artifact and SHALL never be
promoted by copying only the successful subset.

## 9. Phase 12 completion gate

Phase 12 may be recorded as passed only when all required files exist, all schemas and
semantic invariants pass, all hashes and accounting equations match, no record identity is
duplicated, run manifests bind a clean identical source revision, and the determinism report
passes. `formal_build_ready` SHALL remain false while any governed blocker remains, and
`attribute_resolution_acceptance` SHALL remain `not_run` until Phase 14.

Before writing the determinism report or creating `published`, finalization SHALL revalidate
both run manifests, every validator execution and log hash, every referenced artifact byte
hash and semantic hash, and the derived whole-run result. Any missing artifact, changed value,
duplicate identity, invalid population equation, failed run, existing determinism report, or
existing publication target SHALL prohibit publication and SHALL NOT be overwritten.
