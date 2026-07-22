# Post-build Audit Specification

## Boundary

Post-build Audit detects discrepancies and decides acceptance. It MUST NOT edit `net.xml`, regenerate inputs, classify an unknown warning automatically or waive a threshold.

## Normative Requirements

| ID | Requirement | Failure | Test |
|---|---|---|---|
| PA-REQ-001 | Final `net.xml` MUST validate against the pinned network XSD and load in pinned SUMO with exit code zero. | PA001-PA002 | PA-TST-001 |
| PA-REQ-002 | Every expected external edge and lane MUST be traceable through edge provenance or an explicit generation rule. | PA003 | PA-TST-002 |
| PA-REQ-003 | Missing, unexpected and unmapped lanes/connections MUST each be zero. | PA004-PA006 | PA-TST-003 |
| PA-REQ-004 | Effective lane and connection permissions MUST exactly equal materialized expectations. | PA007 | PA-TST-004 |
| PA-REQ-005 | Unmanaged vClasses and unexpected directed edges MUST be zero. | PA008-PA009 | PA-TST-005 |
| PA-REQ-006 | TLS IDs, link indices, controlled connections and phase-state lengths MUST equal the reviewed TLS manifest. | PA010 | PA-TST-006 |
| PA-REQ-007 | Warnings MUST be classified as `BLOCKING`, `ACKNOWLEDGED` or `INFORMATIONAL` by a versioned registry; unclassified warnings MUST be zero. | PA011 | PA-TST-007 |
| PA-REQ-008 | Removed/excluded edges MUST reconcile to an approved input action; unreconciled removals MUST be zero. | PA012 | PA-TST-008 |
| PA-REQ-009 | Structural gate metrics MUST be calculated by vClass and direction; unregistered thresholds MUST block acceptance. | PA013 | PA-TST-009 |
| PA-REQ-010 | The audit report MUST conform to schema and set acceptance true only when every blocking count is zero and every threshold passes. | PA014 | PA-TST-010 |
| PA-REQ-011 | Audit reruns MUST be deterministic for identical inputs and auditor version. | PA015 | PA-TST-011 |

## Warning Classes

- `BLOCKING`: conversion uncertainty, discarded governed content, unknown type/option or structural mismatch.
- `ACKNOWLEDGED`: versioned approval with pattern, scope, rationale, reviewer and expiration/review rule.
- `INFORMATIONAL`: known message demonstrated not to alter governed semantics.

Pattern-only suppression without a registry record is prohibited.

## Acceptance

`formal_network_acceptance` becomes satisfied only after schema/XSD/load success, exact permissions/TLS correspondence, zero unexplained elements and warnings, structural thresholds passed, and immutable reproducibility artifacts published.
