# v17 Attribute Resolution Traceability Matrix

## Control

- Policy: `ota_ward_attribute_resolution_policy_v17`
- Configuration: `ota_ward_sumo_network_v17`
- Specification: `10_approved_attribute_resolution_policy_v17_complete.md`
- Specification version: approved repository baseline, 2026-08-03
- Phase 1 authority validator: `traffic_simulation.network.validate_v17_phase1_authority`

`authority_status` records whether Phase 1 has a consistent normative and
machine-readable destination. `implementation_phase` records when runtime
behavior must be integrated. Therefore `aligned` does not claim that a Phase
3–14 production behavior has already run.

| requirement_id | specification_section | requirement_summary | configuration_location | schema_location | registry_location | semantic_invariant | implementation_phase | authority_status |
|---|---:|---|---|---|---|---|---:|---|
| AR-STATE-001 | 7.1 | Use the five canonical resolution states. | `resolution_contract.resolution_status` | resolution record | state/origin | `AR-STATE-001` | 3 | aligned |
| AR-STATE-002 | 7.2 | Use the six canonical value origins and formal eligibility. | `resolution_contract.value_origin` | resolution record | state/origin | `AR-STATE-002` | 3 | aligned |
| AR-STATE-003 | 7.3 | Resolved and non-resolved fields obey null/value invariants. | profiles/contract | resolution record | stop codes | `AR-STATE-001`,`002` | 3 | aligned |
| AR-STATE-004 | 7.3 | Formal output prohibits model assumptions. | `profiles.formal` | resolution record | assumptions | `AR-STATE-003` | 3 | aligned |
| AR-STATE-005 | 7.4 | `value_state` is read-only compatibility. | resolution contract | resolution record | legacy mappings | `AR-STATE-004` | 3 | aligned |
| AR-STATE-006 | 7.3 | Conflict records preserve candidates and provenance. | resolution contract | resolution record | stop codes | `AR-STATE-005` | 3 | aligned |
| AR-ID-001 | 6.2 | Resolver tuple dimensions remain explicit and nullable only when inapplicable. | resolution contract | resolution record | — | `AR-ID-001` | 3 | aligned |
| AR-ID-002 | 6.3 | Record IDs use SHA-256 over RFC 8785 canonical identity JSON. | semantic invariants | resolution record | — | `AR-ID-001` | 3 | aligned |
| AR-ID-003 | 6.3 | Classification identity is not overwritten by resolution. | acceptance | resolution record | — | `AR-ID-003` | 14 | aligned |
| AR-DIR-001 | 9.1 | Directed Segment ID uses canonical source interval and direction. | direction model | directed segment | — | `AR-DIR-001` | 4 | aligned |
| AR-DIR-002 | 9.2 | Direction follows immutable source node lineage. | direction model | directed segment | — | `AR-DIR-002` | 4 | aligned |
| AR-DIR-003 | 9.3 | Normalize registered explicit oneway values only. | direction model | resolution record | oneway rules | `AR-DIR-003` | 4 | aligned |
| AR-DIR-004 | 9.4 | `yes`, `no`, and `-1` generate the specified direction sets. | direction model | directed segment | oneway rules | `AR-DIR-003` | 4 | aligned |
| AR-DIR-005 | 9.5 | Missing ordinary-road oneway derives `no` through a rule. | direction model | resolution record | oneway rules | `AR-DIR-003` | 4 | aligned |
| AR-DIR-006 | 9.6 | Class-specific direction affects permissions without mutating base direction. | permissions | access rule | vehicle ontology | `AR-DIR-002` | 4 | aligned |
| AR-DIR-007 | 9.7 | Relation mappings uniquely resolve or stop. | direction model | directed segment | stop codes | `AR-DIR-004` | 4 | aligned |
| AR-DIR-008 | 9.2 | SUMO edge sign and nearest coordinate are prohibited direction evidence. | direction model | directed segment | — | `AR-DIR-005` | 4 | aligned |
| AR-LANE-001 | 10.1 | Governed moving lanes exclude parking and shoulders absent a rule. | lane resolution | resolution record | — | `AR-LANE-001` | 5 | aligned |
| AR-LANE-002 | 10.2 | One-way lane counts attach to the active direction. | lane resolution | resolution record | oneway rules | `AR-LANE-001` | 5 | aligned |
| AR-LANE-003 | 10.3 | Formal bidirectional allocation requires explicit or approved evidence. | profiles/lane resolution | resolution record | evidence methods | `AR-LANE-003` | 5 | aligned |
| AR-LANE-004 | 10.3 | Total equals directional plus both-ways counts. | semantic invariants | resolution record | stop codes | `AR-LANE-001` | 5 | aligned |
| AR-LANE-005 | 10.4 | Even split is structural-only and predicate-bound. | lane resolution | resolution record | assumptions | `AR-LANE-003` | 5 | aligned |
| AR-LANE-006 | 10.5 | Lane vector length equals directional count. | semantic invariants | resolution record | stop codes | `AR-LANE-002` | 5 | aligned |
| AR-LANE-007 | 10.6 | Resolver-to-SUMO lane index is `n-1-p`. | lane resolution | directed segment | — | `AR-LANE-004` | 5 | aligned |
| AR-SPEED-001 | 11.1 | Canonical speed uses km/h and materializes by division by 3.6. | lane/speed policy | resolution record | speed rules | `AR-SPEED-001` | 9 | aligned |
| AR-SPEED-002 | 11.2 | Apply deterministic speed source priority. | registries | resolution record | speed rules | `AR-SPEED-002` | 9 | aligned |
| AR-SPEED-003 | 11.3 | Symbolic or absent speed requires a registered Japan rule. | registries | resolution record | speed rules | `AR-SPEED-002` | 9 | aligned |
| AR-SPEED-004 | 11.4 | Preserve directional asymmetry. | semantic invariants | resolution record | speed rules | `AR-SPEED-002` | 9 | aligned |
| AR-SPEED-005 | 11.5 | Missing context and within-interval changes stop. | scenario context | resolution record | conditional grammar | `AR-SPEED-003` | 9 | aligned |
| AR-ACCESS-001 | 12.1 | Normalize each statement into an AccessRule. | access resolution | access rule | access values | `AR-ACCESS-001` | 6 | aligned |
| AR-ACCESS-002 | 12.2 | Direction/lane target scope is separate from specificity axes. | access resolution | access rule | — | `AR-ACCESS-001` | 6 | aligned |
| AR-ACCESS-003 | 12.3 | Specificity axes are spatial, vehicle, temporal, and purpose sets. | access resolution | access rule | vehicle ontology | `AR-ACCESS-002` | 6 | aligned |
| AR-ACCESS-004 | 12.4 | Dominance uses scope plus set inclusion and at least one strict subset. | access resolution | access rule | — | `AR-ACCESS-003` | 8 | aligned |
| AR-ACCESS-005 | 12.5 | Equal maxima preserve provenance; different maxima stop. | access resolution | resolution record | stop codes | `AR-ACCESS-003`,`004` | 8 | aligned |
| AR-ACCESS-006 | 13.1 | Formal permissions cover every governed tuple. | permissions/acceptance | acceptance | vehicle ontology | `AR-ACCESS-005` | 8 | aligned |
| AR-ACCESS-007 | 13.2 | Access values use registered context semantics. | scenario context | access rule | access values | `AR-ACCESS-002` | 6 | aligned |
| AR-ACCESS-008 | 13.3 | Resolver expectation, not typemap, is formal authority. | permissions | acceptance | — | `AR-ACCESS-005` | 8 | aligned |
| AR-ACCESS-009 | 13.4 / `DEC-P13-HORSE-ONTOLOGY-001` | A registered non-governed vehicle-class tag has an empty intersection with governed permissions; approved scalar `horse=yes/no` preserves provenance and cannot change delivery permission or authorize exclusion. | access resolution | access rule | `vehicle_ontology.domains.horse`, `vehicle_ontology.non_governed_domain_decisions.horse` | `AR-ACCESS-009` | 13 | implemented |
| AR-ACCESS-010 | 13.5 / `DEC-P13-PSV-ONTOLOGY-001` | The approved psv domain is exactly `bus` and `taxi`; coach and managed delivery remain excluded; explicit child rules override psv without changing tourist_bus or coach constraints; unknown and unsupported syntax remain fail-closed. | access resolution | access rule | `vehicle_ontology.domains.psv` | `AR-ACCESS-010` | 13 | implemented |
| AR-COND-001 | 14.1 | Last-match is limited to clauses in one conditional tag. | access resolution | access rule | conditional grammar | `AR-COND-003` | 7 | aligned |
| AR-COND-002 | 14.2 | Only versioned registered grammar categories are supported. | scenario context | access rule | conditional grammar | `AR-COND-002` | 7 | aligned |
| AR-COND-003 | 14.3 | Required scenario context is explicit; missing is not false. | scenario context | resolution record | conditional grammar | `AR-COND-001` | 7 | aligned |
| AR-COND-004 | 14.4 | Interval changes split through an approved transform or stop. | scenario context | resolution record | conditional grammar | `AR-COND-004` | 7 | aligned |
| AR-COND-005 | 14.5 | Unsupported syntax stops without falling back to static access. | scenario context | resolution record | conditional grammar | `AR-COND-002` | 7 | aligned |
| AR-EVID-001 | 15.1 | No generic formal imputation fallback exists. | profiles | resolution record | evidence methods | `AR-EVID-001` | 10 | aligned |
| AR-EVID-002 | 15.2 | Evidence/model origins require an approved method record. | registries | resolution record | evidence methods | `AR-EVID-001` | 10 | aligned |
| AR-EVID-003 | 15.3 | Formal donors satisfy eligibility and contain no assumptions. | semantic invariants | resolution record | evidence methods | `AR-EVID-002` | 10 | aligned |
| AR-EVID-004 | 15.4 | Manual evidence is separate and outputs are regenerated. | registries | environment manifest | evidence methods | `AR-EVID-003` | 10 | aligned |
| AR-EXCL-001 | 16.1 | Exclusion is not a resolution status. | resolution contract | exclusion manifest | exclusion rules | `AR-EXCL-002` | 12 | aligned |
| AR-EXCL-002 | 16.2 | Exclusions use approved registered entries. | registries | exclusion manifest | exclusion rules | `AR-EXCL-002` | 12 | aligned |
| AR-EXCL-003 | 16.3 | Input equals governed plus excluded population. | acceptance | exclusion manifest | — | `AR-EXCL-001` | 12 | aligned |
| AR-EXCL-004 | 16.4 | Materialization omission is separate and retained in denominators. | outputs | omission schema | — | `AR-EXCL-003` | 12 | aligned |
| AR-BLOCK-001 | Blocker policy 5 | Every blocker receives exactly one strategy. | blocker policy | blocker inventory | strategy registry | `AR-BLOCK-001` | 11 | aligned |
| AR-BLOCK-002 | Blocker policy 3, 10, 18 | Missing data, unsupported code, volume and schedule pressure cannot authorize exclusion. | blocker policy | blocker inventory | exclusion rules | `AR-BLOCK-002` | 11 | aligned |
| AR-BLOCK-003 | Blocker policy 14 | Permission blockers identify upstream causal records and are regenerated. | blocker policy | blocker inventory | — | `AR-BLOCK-003` | 11 | aligned |
| AR-BLOCK-004 | Blocker policy 2, 16 | Excluded records are not resolved or governed and population sets do not overlap. | blocker policy | exclusion manifest | exclusion rules | `AR-BLOCK-004` | 12 | aligned |
| AR-PROV-001 | 17.1 | Every value identifies source/rule/evidence/model/assumption and activity. | acceptance | resolution record | — | `AR-PROV-002` | 11 | aligned |
| AR-PROV-002 | 17.2 | Identity and acceptance JSON use RFC 8785 and reject duplicate keys. | semantic invariants | all JSON schemas | — | `AR-PROV-001` | 11 | aligned |
| AR-PROV-003 | 17.3 | Run manifest records environment, command, hashes, logs, and seeds. | schemas | environment manifest | — | `AR-PROV-002` | 12 | aligned |
| AR-PROV-004 | 17.4 | Two clean identical runs have identical canonical hashes. | acceptance | acceptance | — | `AR-PROV-003` | 14 | aligned |
| AR-PROV-005 | 22 | v16 artifacts remain immutable and v17 outputs are separate. | history/outputs | configuration | — | `AR-PROV-004` | 12 | aligned |
| AR-ACC-001 | 18.1 | Validation layers remain distinct. | acceptance | acceptance | — | `AR-ACC-002` | 14 | aligned |
| AR-ACC-002 | 18.2 | Attribute acceptance covers only the formal Resolver artifact. | acceptance | acceptance | — | `AR-ACC-001` | 14 | aligned |
| AR-ACC-003 | 18.3 | Acceptance requires complete and zero blocker/review/stop/assumed counts. | acceptance | acceptance | stop codes | `AR-ACC-001` | 14 | aligned |
| AR-ACC-004 | 18.4 | Complete means every governed record exists once and is formally resolved. | acceptance | acceptance | — | `AR-ACC-001` | 14 | aligned |
| AR-ACC-005 | 18.5 | Gate result is passed, failed, or not_run; missing evidence never passes. | acceptance | acceptance | — | `AR-ACC-003` | 14 | aligned |
| AR-ACC-006 | 18.6 | Acceptance artifact contains all required identities, hashes, counts, and results. | acceptance | acceptance | — | `AR-ACC-002` | 14 | aligned |
| AR-ACC-007 | 19 | Fixtures and oracles are independent and cover required families. | acceptance | acceptance | stop codes | `AR-ACC-002` | 2 | aligned |
| AR-TRANS-001 | 21 | Implementation follows the normative Phase 0–14 dependency order. | phase1 description | — | — | — | 14 | aligned |
| AR-TRANS-002 | 22 | v17 writer supersedes legacy state and v16 permission authority without rewriting history. | history/contract | resolution record | legacy mappings | `AR-STATE-004` | 3 | aligned |

## Phase 1 conclusion

Every normative family has a configuration, Schema, Registry, or semantic
invariant destination. Runtime implementation remains explicitly assigned to
Phases 2–14 and is not represented as completed by this matrix.

## Phase 13 horse ontology implementation trace

- Decision: `reproducibility/config/traffic_simulation/v17_phase13_horse_vehicle_ontology_decision.yml`
- Registry rule: `NON_GOVERNED_HORSE_RIDER_DOMAIN_EMPTY_INTERSECTION_V1`
- Invariant: `AR-ACCESS-009`
- Fixture: `05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/phase13_horse_vehicle_domain_fixture.yml`
- Oracle: `05_src/traffic_simulation/validation/fixtures/v17_attribute_resolution/phase13_horse_vehicle_domain_oracle.yml`
- Runtime enforcement: `05_src/traffic_simulation/network/static_access_v17.py`
- Tests: `05_src/traffic_simulation/validation/test_static_access_v17.py` and `test_phase13_horse_vehicle_ontology_decision_v17.py`
- Full-population probe record: `reproducibility/config/traffic_simulation/v17_phase13_horse_full_population_probe.yml`
- Stable-ID and permission comparator: `05_src/traffic_simulation/network/compare_phase13_horse_probe.py`
- Probe result: horse hierarchy blocker 0 and permission change 0, but strict acceptance failed because two `private_authorization` successor blocker IDs were newly exposed.

## Phase 13 PSV ontology decision trace

- Decision: `reproducibility/config/traffic_simulation/v17_phase13_psv_vehicle_ontology_decision.yml`
- Decision rule: `OSM_PSV_TO_GOVERNED_BUS_TAXI_V1`
- Fixed OSM authority: `Key:psv` revision 2960634 and `Key:access` revision 3054035
- Fixed SUMO authority: official source tag `v1_24_0`, commit `b72eb3fabc806681f8c9048999a33dd8d64092b1`
- Governed intersection: `bus=true`, `taxi=true`, `coach=false`
- Managed delivery effect: none
- Registry domain: `psv: [bus, taxi]`
- Invariant: `AR-ACCESS-010`
- Validation: `05_src/traffic_simulation/validation/test_phase13_psv_vehicle_ontology_decision_v17.py` and static access regression fixtures
- Implementation status: Registry, invariant, fixture/oracle, traceability, and static-access fail-closed syntax handling are synchronized; governed vehicle-domain resolution remains Registry-driven.

## Phase 13 private authorization context resolution trace

- Resolution: `RES-P13-PRIVATE-AUTH-CONTEXT-001`
- Resolution record: `reproducibility/config/traffic_simulation/v17_phase13_private_authorization_context_resolution.yml`
- Root cause: the fixed governed runtime context already established `authorization_ids: []` and therefore `private_authorization=false`, but the static-access default context did not expose that governed authorization fact.
- Runtime remediation: `05_src/traffic_simulation/network/static_access_v17.py`
- Regression test: `05_src/traffic_simulation/validation/test_phase13_private_authorization_context_resolution_v17.py`
- Revealed successor Ways: `992482251`, `992488487`
- Result: both successor Ways resolve as `denied`; neither remains an `ACCESS_CONTEXT_MISSING` blocker.
- Full-population `ACCESS_CONTEXT_MISSING`: `45 -> 0`
- Full-population static-access blockers: `248 -> 187`
- Horse stable-ID reacceptance: `passed`
- New horse stable blocker IDs after remediation: `0`
- Revealed private-context successor blockers after remediation: `0`
- Unexpected managed-delivery permission changes: `0`
- Known unresolved motorcar transitions preserved: `2`
- Final focused validation: `63 passed`
- Focused validation log SHA-256: `60201825a75c4103d66bfeb3e6bccb09c623fb3690627a63b8d59681343513b6`
- Historical boundary: `v17_phase13_horse_full_population_probe.yml` remains the immutable record of the earlier strict failure; this resolution is a later successor-remediation record.
