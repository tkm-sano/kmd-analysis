# Tokyo traffic simulation extension

This directory is an additive research layer. It must not overwrite the
existing synthetic EVRP analysis or its frozen inputs and outputs.

The data-governance, minimum-area validation, classical-versus-Qiskit-Aer-QAOA
route comparison, CI, and server-migration tasks are recorded in
[`implementation_plan.md`](implementation_plan.md).

The assumptions, interpretation, commands, and operating rules for staged
map review are recorded in [`visualization/README.md`](visualization/README.md).

The Japanese implementation and verification procedure for applying
vehicle-class permissions to the Ota Ward SUMO road network is documented in
[`東京交通・EV配送研究の全工程と大田区道路網の通行権限実装手順`](learning/permission_materializer_reproducible_implementation_guide.md).

The learning-oriented Japanese translation of the attribute-criticality,
evidence, classification, and resolution contract is available in
[`属性別重要度と証拠に関する仕様書`](learning/attribute_criticality_and_evidence_specification_ja.md).
The English specification and machine-readable configuration remain
authoritative.

The model-development lifecycle, Verification, calibration, independent
Validation, evidence requirements, and formal-use gates are organized in
[`simulation_model_development_and_vv.md`](simulation_model_development_and_vv.md).

The current blockers, their evidence, downstream effects, resolution work, and
acceptance criteria are documented in
[`current_issues_and_blockers.md`](current_issues_and_blockers.md).
The approved v17 road-attribute policy, whose implementation and runtime
validation remain incomplete, is specified in
[`10_approved_attribute_resolution_policy.md`](specifications/10_approved_attribute_resolution_policy.md)
and
[`approved_attribute_resolution_policy_v17.yml`](../../reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml).
The ordered Japanese procedure from the current v16 attribute-resolution state
through rule approval, implementation, full-data rerun, and formal acceptance
is documented in
[`版16道路属性の正式解決に向けた実行手順`](attribute_resolution_execution_procedure.md).
Accepted v16 road-population and relation-closure facts are kept separately in
[`confirmed_network_population_and_relation_closure.md`](confirmed_network_population_and_relation_closure.md).
Other implemented and verified facts are separated from open blockers in
[`confirmed_implementation_and_verification.md`](confirmed_implementation_and_verification.md).

The Japan/Tokyo interpretation policy and the implemented one-to-one
classification rules for the 307 governed Resolver exception rows are recorded
in
[`japan_tokyo_osm_exception_classification_rules.md`](specifications/japan_tokyo_osm_exception_classification_rules.md).
The fixed-input execution record, one-to-one row counts and the historical
331/335-test verification results are recorded in
[`20260730_ota_ward_v15_exception_rule_validation.md`](../../03_data/metadata/acquisition/20260730_ota_ward_v15_exception_rule_validation.md).
The current traffic-simulation validation suite passes 355 tests after the
v16 attribute-resolution execution.

The authoritative rules for road attributes, external-data matching,
structural placeholders, human review, and formal-network quality gates are
recorded in
[`network_attribute_governance.md`](network_attribute_governance.md).

The open-statistics calculation and the non-optimizing baseline comparator are
specified in
[`demand/baseline_demand_and_comparator.md`](demand/baseline_demand_and_comparator.md).
The implemented population and parcel-equivalent demand preparation uses
[`../../reproducibility/config/traffic_simulation/baseline_demand.yml`](../../reproducibility/config/traffic_simulation/baseline_demand.yml)
and [`demand/prepare_baseline_demand.py`](demand/prepare_baseline_demand.py).

## Source-code boundaries

- `network/`: OSM acquisition adapters, clipping, map matching, and SUMO
  network generation.
- `demand/`: time-of-day traffic and freight-demand construction.
- `calibration/`: JARTIC/road-census calibration and validation.
- `simulation/`: SUMO configurations, runners, and result extraction.
- `validation/`: structural and empirical checks for the new layer.

All new modules must import canonical locations from `traffic_simulation.paths`.
They must not infer the repository root from a fixed `Path.parents[...]` index
or contain a host-specific absolute path.

## Data boundaries

- Raw inputs: `03_data/raw/traffic_simulation/`, separated into the
  source-specific directories documented in that directory's `README.md`.
- Processed road networks: `03_data/processed/traffic_simulation/road_network/`
- Processed traffic profiles:
  `03_data/processed/traffic_simulation/traffic_profiles/`
- Generated SUMO inputs: `03_data/processed/traffic_simulation/sumo_inputs/`
- Processed calibration data: `03_data/processed/traffic_simulation/calibration/`
- Processed demand data: `03_data/processed/traffic_simulation/demand/`
- Processed driver-behavior parameters:
  `03_data/processed/traffic_simulation/driver_behavior/`
- Processed validation data: `03_data/processed/traffic_simulation/validation/`
- Source registry: `03_data/metadata/traffic_simulation_sources.csv`
- Reproducible run products:
  `reproducibility/outputs/traffic_simulation/`
- Curated final artifacts: `06_outputs/traffic_simulation/`

All paths stored in metadata must be relative to the repository root. Runtime
code uses `traffic_simulation.paths` to discover that root independently of
the process working directory.
