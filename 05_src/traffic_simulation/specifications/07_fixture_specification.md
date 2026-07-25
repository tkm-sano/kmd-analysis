# Fixture Specification

## Oracle Rule

Expected artifacts MUST be authored independently from production transformation code. Production code MUST NOT update golden files. Every fixture records purpose, source hash, expected status/failure code, covered requirement IDs and pinned execution command.

Every code in `08_failure_taxonomy.md` has one mandatory negative-oracle fixture ID formed as `<failure-code>-NEG-001`. The fixture may be exercised by the requirement-level test listed below, but its input and expected failure report MUST be stored independently. A code is not considered fixture-covered merely because a production branch can emit it. Until the corresponding fixture files and pinned execution evidence exist, their implementation state remains `specified_not_implemented`.

## Fixture Catalogue

| Test ID | Class | Required case | Expected result |
|---|---|---|---|
| RS-TST-001..014 | positive/negative/repeat | Strict OSM identity/reference cases, relation-scope accounting, donor eligibility, compound types, formal/structural lane allocation, lane-local forward/backward trace, v2 artifact, transactional rollback and CLI failure report | exact artifact or RS code |
| AC-TST-001..010 | positive/negative/boundary/repeat | All lane/speed criticality levels, tuple coverage, rule selection, predicate contradictions, evidence applicability/conflict, review, placeholder gate, source hashes, state machine, topology support, profile transition, promotion and deterministic repeat | exact classification-resolution oracle or AC code |
| PM-TST-001 | negative | incomplete expectation, hash/config/schema mismatch | PM001-PM005 |
| PM-TST-002 | boundary/negative | single edge, split edge, joined-node lineage, ambiguous direction | exact direction or PM006-PM009 |
| PM-TST-003 | positive/negative | forward/backward two-lane order, gap, duplicate, count mismatch | exact index map or PM010-PM013 |
| PM-TST-004 | boundary/negative | omitted permission, `all`, explicit allow/disallow, empty, both, unknown token | exact set or PM014-PM016 |
| PM-TST-005 | positive | different per-lane permissions and typemap baseline | exact lane `allow` |
| PM-TST-006 | boundary | one empty lane and all-empty directed edge | `disallow=all` or edge removal |
| PM-TST-007 | positive/boundary | connection intersection with many, one and zero classes | retain/restrict/remove |
| PM-TST-008 | positive/negative | prohibition/delete and crossing/walkingArea/unknown element | preserve or PM023 |
| PM-TST-009 | boundary | provisional TLS evidence present | no final TLS output by materializer |
| PM-TST-010..011 | repeat/negative | deterministic rerun, existing output, forced failure, complete accounting | identical output or PM025-PM028 |
| TLS-TST-001..010 | positive/negative | no TLS, reviewed TLS, link gap/duplicate, phase length, changed connection hash | eligible state or TLS code |
| BLD-TST-001..011 | positive/negative/repeat | readiness, hash, options, schema, atomicity, semantic repeat | build output or BLD code |
| PA-TST-001..011 | positive/negative/repeat | XSD/load, lineage, permissions, TLS, warnings, thresholds | acceptance or PA code |

The ranges in this table abbreviate test families only. They do not combine failure meanings: each failure code retains its own `<failure-code>-NEG-001` catalogue identity.

The checked-in attribute-classification collection is stored under
`validation/fixtures/attribute_classification/`. Its input catalogue and
oracle catalogue are separate immutable files. Case descriptors bind both
files by SHA-256. The collection was authored from the specification before
the production predicate generator and classifier existed; production code
did not generate its oracle. Independent human acceptance remains a separate
review gate recorded in `review.json`.

`inputs.json` is the complete execution-input catalogue. It identifies every
target tuple, including failures before record emission. `oracles.json` is the
independently authored expected-result source and includes executable
assertions plus failure-stage record-emission policy. Descriptor coverage maps
coverage IDs to assertion IDs. The manifest's complete level index, canonical
level witnesses and scenario index are derived from descriptors and oracles.
The manifest hashes the input and oracle catalogues but deliberately does not
hash `review.json`. Instead, `review.json` records expected and observed
SHA-256 values for the manifest, inputs, oracles and source specification.
This one-way reference makes the review evidence complete without creating a
manifest-review hash cycle.

Derived descriptors, hashes, review hash observations and the manifest are
maintained with:

```bash
PYTHONPATH=05_src python -m \
  traffic_simulation.validation.build_attribute_classification_fixture_collection \
  --write
```

CI uses the same command with `--check`. The builder copies, but does not
author, oracle expectations; it refuses to proceed if the oracle's pinned
specification hash differs from the current specification.

## Pinned Runtime Fixture Minimum Topology

The materializer runtime fixture MUST contain:

- a left-hand one-way two-lane edge with different permissions;
- a two-way way with different forward/backward lane permissions;
- one OSM way split into multiple SUMO edges;
- an exact reviewed-node lineage case;
- a junction with retained, single-class and removed connections;
- one partially empty edge and one all-empty directed edge;
- a prohibited turn;
- a signalized junction used only by the separate TLS fixture.

## Acceptance Evidence

Each run records git commit, container digest, exact argv, fixture collection hash, start/end UTC timestamps, exit code and log SHA-256. XSD validation, netconvert and SUMO load use the pinned container. Current online documentation may explain behavior but does not replace version-pinned evidence.
