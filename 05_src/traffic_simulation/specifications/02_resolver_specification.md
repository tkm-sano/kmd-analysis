# Resolver Specification

## Scope

The Resolver is the only component that interprets OSM `oneway`, lane count, speed and access semantics. Detailed evidence precedence remains governed by `network_attribute_governance.md`; this document defines its executable boundary and artifacts.

## Inputs and Outputs

Inputs MUST be repository-relative, hash-registered OSM XML, v14 config, governed typemap and optional versioned criticality/evidence tables. Successful output consists of:

- `normalized.osm.xml`
- `permission_expectations.json` conforming to `permission_expectations.schema.json`
- road-attribute audit CSV
- imputation summary JSON
- `failure_report.json` conforming to `failure_report.schema.json` when the CLI stops

An ordinary governed blocker retains the audit, imputation summary, incomplete permission artifact and failure report but removes `normalized.osm.xml`. An input, configuration, schema or publication failure that occurs before a coherent result set is available publishes only the failure report. The CLI returns zero on success, two on a classified Resolver failure and three if even the failure report cannot be published.

## Normative Requirements

| ID | Requirement | Failure | Test |
|---|---|---|---|
| RS-REQ-001 | The OSM root MUST be `osm`; retained ways MUST have unique nonempty IDs and unique tag keys. | RS001 | RS-TST-001 |
| RS-REQ-002 | Only the explicit typemap whitelist MAY be retained; every excluded highway way MUST be counted. | RS002 | RS-TST-002 |
| RS-REQ-003 | Every retained way MUST resolve `oneway`, directional lane counts, `maxspeed` and permissions before successful output. | RS003 | RS-TST-003 |
| RS-REQ-004 | Missing, unsupported, conditional, asymmetric, conflicting and invalid values MUST remain distinct states. | RS004 | RS-TST-004 |
| RS-REQ-005 | Structural imputation MAY apply only to true missing lane/speed values on explicitly noncritical ways under the preregistered unique-mode rule. | RS005 | RS-TST-005 |
| RS-REQ-006 | Formal output MUST contain no structural placeholder or unresolved stopping state. | RS006 | RS-TST-006 |
| RS-REQ-007 | `oneway=-1` MUST stop until a complete direction-dependent transformation is implemented; no partial reversal is permitted. | RS007 | RS-TST-007 |
| RS-REQ-008 | Lane access values MUST be read left-to-right as viewed in their respective travel direction for both forward and backward tags. | RS008 | RS-TST-008 |
| RS-REQ-009 | Resolver lane position zero MUST mean the leftmost lane in that travel direction. | RS008 | RS-TST-009 |
| RS-REQ-010 | Unsupported access keys/values, unsuffixed bidirectional lane access and lane-value count mismatch MUST stop. | RS009 | RS-TST-010 |
| RS-REQ-011 | Expected permissions MUST equal the resolved OSM permission intersected with the selected typemap baseline and governed vClasses. | RS010 | RS-TST-011 |
| RS-REQ-012 | The expectation artifact MUST contain complete type, direction, lane-position, rule and hash provenance; the v13 map-only shape is not a valid v14 input. | RS011 | RS-TST-012 |
| RS-REQ-013 | Output writes MUST be atomic, distinct from inputs and non-overwriting unless an explicit governed development override is supplied. | RS012 | RS-TST-013 |

## Directional Lane Allocation

`formal` requires explicit, consistent `lanes:forward` and `lanes:backward` for every bidirectional road. It never infers an equal split from `lanes`. `structural` may split an even total equally only as `approved_assumption`, with audit and sensitivity required. A single/odd total without explicit allocation and every `lanes:both_ways` case stop with `RS008`.

## Imputation Donors

A structural donor MUST have resolvable direction, consistent explicit lane and canonical numeric speed values, no conditional tag, no `oneway=-1`, and resolvable permissions under the structural profile. A way that later stops is not a donor. Decimal-equivalent speeds such as `40` and `40.0` share the canonical value `40`.

## Permission Trace

Each way-direction-lane record contains only the rules applied to that lane. The ordered trace records typemap baseline, research-scope intersection and applicable general, class, directional or lane-specific OSM transitions, including source tag/value, lane-local value, and before/after vClass sets. A tag applying to another direction or lane MUST NOT appear in that lane's trace.

## Publication and Input Integrity

All artifacts are generated in one staging directory and validated before publication. Replacement uses backups and rollback so an exception cannot mix artifacts from different runs. `.part` files are removed in `finally` cleanup. `--overwrite` is a development override only; formal orchestration uses new run identities and paths.

OSM tags require nonempty `k` and present nonempty `v`; retained ways require valid node references. Relations referencing an intentionally excluded highway way are removed with that way, while an unknown way reference stops. A supplied criticality map requires a source file and exact retained-way coverage. The v14 typemap contract is `allow`-only; any retained type with `disallow` stops policy loading.

## Lane Order Authority

OSM lane lists are interpreted left-to-right in the respective direction of travel. Therefore a backward list is not reversed inside the Resolver merely because it travels opposite the OSM way. The Materializer later reverses lane positions when mapping to SUMO right-to-left indices.

## Success Condition

`complete=true` requires zero blockers, one expectation record per retained way, exact agreement between direction lane counts and lane records, and matching config/input/typemap hashes. A successful artifact with an empty governed vClass universe is prohibited.

For a successful artifact, `normalized_osm` records the repository-relative path and SHA-256 of the exact normalized XML emitted by the same run. Failed artifacts omit this reference because normalized XML is not published. Fixture validation of this format does not establish eligibility on the registered Ota Ward extract.
