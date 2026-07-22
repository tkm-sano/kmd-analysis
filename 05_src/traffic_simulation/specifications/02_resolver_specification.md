# Resolver Specification

## Scope

The Resolver is the only component that interprets OSM `oneway`, lane count, speed and access semantics. Detailed evidence precedence remains governed by `network_attribute_governance.md`; this document defines its executable boundary and artifacts.

## Inputs and Outputs

Inputs MUST be repository-relative, hash-registered OSM XML, v14 config, governed typemap and optional versioned criticality/evidence tables. Successful output consists of:

- `normalized.osm.xml`
- `permission_expectations.json` conforming to `permission_expectations.schema.json`
- road-attribute audit CSV
- imputation summary JSON

Failure retains audit and failure artifacts but removes `normalized.osm.xml` and sets `complete=false`.

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

## Lane Order Authority

OSM lane lists are interpreted left-to-right in the respective direction of travel. Therefore a backward list is not reversed inside the Resolver merely because it travels opposite the OSM way. The Materializer later reverses lane positions when mapping to SUMO right-to-left indices.

## Success Condition

`complete=true` requires zero blockers, one expectation record per retained way, exact agreement between direction lane counts and lane records, and matching config/input/typemap hashes. A successful artifact with an empty governed vClass universe is prohibited.
