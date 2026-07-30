"""Validate the governed Tokyo motorized OSM typemap."""

from __future__ import annotations

import hashlib
from pathlib import Path
from xml.etree import ElementTree

import yaml

from traffic_simulation.network import validate_sumo_network_config as config_validator


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "reproducibility/config/traffic_simulation/sumo_network.yml"
TYPEMAP_PATH = (
    ROOT / "reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml"
)
RUNTIME_FIXTURE_PATH = (
    ROOT
    / "05_src/traffic_simulation/validation/fixtures/osm_typemap_governance.osm.xml"
)
GOVERNED_VCLASSES = {
    "passenger",
    "taxi",
    "bus",
    "coach",
    "delivery",
    "truck",
    "motorcycle",
}
GOVERNED_ATTRIBUTES = {"numLanes", "speed", "oneway"}
FORBIDDEN_VCLASSES = {"ignoring", "custom1", "custom2", "evehicle"}


def load_config() -> dict[str, object]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def load_types() -> dict[str, dict[str, str]]:
    root = ElementTree.parse(TYPEMAP_PATH).getroot()
    assert root.tag == "types"
    types = [element.attrib for element in root.findall("type")]
    ids = [attributes["id"] for attributes in types]
    assert len(ids) == len(set(ids))
    return {attributes["id"]: attributes for attributes in types}


def test_typemap_path_and_vclasses_match_governed_config() -> None:
    config = load_config()
    policy = config["typemap_policy"]
    vehicle_scope = config["vehicle_scope"]

    assert policy["path"] == str(TYPEMAP_PATH.relative_to(ROOT))
    assert policy["sha256"] == hashlib.sha256(TYPEMAP_PATH.read_bytes()).hexdigest()
    assert (ROOT / policy["design_record"]).is_file()
    assert policy["inclusion_policy"] == "explicit_whitelist"
    assert policy["enforcement_status"] == "pending_build_pipeline"
    assert (
        policy["unknown_type_policy"]
        == "reject_unmatched_and_report_explicit_discard"
    )
    assert policy["absence_of_type_defaults_is_validation"] is False
    assert set(vehicle_scope["keep_vclasses"]) == GOVERNED_VCLASSES
    assert vehicle_scope["scope_duration"] == "entire_research"
    assert vehicle_scope["multimodal_expansion_outside_research_scope"] is True
    assert set(vehicle_scope["excluded_dedicated_modes"]) == {
        "pedestrian",
        "bicycle",
        "rail",
        "ship",
    }


def test_retained_types_are_an_explicit_configured_whitelist() -> None:
    config = load_config()
    policy = config["typemap_policy"]
    types = load_types()
    expected = {
        *(f"highway.{value}" for value in policy["retained_shared_highway_types"]),
        *policy["retained_compound_type_ids"],
        *policy["retained_dedicated_motorized_type_ids"],
    }
    retained = {
        type_id
        for type_id, attributes in types.items()
        if attributes.get("discard") != "true"
    }

    assert retained == expected
    assert all("allow" in types[type_id] for type_id in retained)
    assert all(
        set(types[type_id]["allow"].split()) <= GOVERNED_VCLASSES
        for type_id in retained
    )
    assert {
        vclass
        for type_id in retained
        for vclass in types[type_id]["allow"].split()
    } == GOVERNED_VCLASSES
    assert len(types["highway.residential"]["allow"].split()) == 7
    assert len(types["highway.motorway"]["allow"].split()) == 7
    assert all(
        "moped" not in attributes.get("allow", "").split()
        for attributes in types.values()
    )
    assert len(types["highway.service|bus"]["allow"].split()) == 2
    assert types["highway.busway"]["allow"] == "bus"
    assert types["highway.bus_guideway"]["allow"] == "bus"


def test_vehicle_inputs_cannot_bypass_typemap_permissions() -> None:
    config = load_config()
    policy = config["vehicle_input_policy"]

    assert set(policy["allowed_vclasses"]) == GOVERNED_VCLASSES
    assert set(policy["forbidden_vclasses"]) == FORBIDDEN_VCLASSES
    assert GOVERNED_VCLASSES.isdisjoint(FORBIDDEN_VCLASSES)
    assert set(policy["inspect_elements"]) == {"vType", "vehicle", "flow", "trip"}
    assert policy["reject_ungoverned_vclass"] is True
    assert policy["validate_referenced_vtype"] is True
    ev_policy = policy["ev_delivery_representation"]
    assert ev_policy["road_vclass"] == "delivery"
    assert ev_policy["powertrain_model"] == "sumo_battery_device"
    assert ev_policy["evehicle_vclass_allowed"] is False


def test_typemap_does_not_supply_governed_road_attribute_defaults() -> None:
    config = load_config()
    policy = config["typemap_policy"]
    types = load_types()

    assert set(policy["typemap_must_not_default"]) == {
        "lanes",
        "maxspeed",
        "oneway",
    }
    for attributes in types.values():
        assert GOVERNED_ATTRIBUTES.isdisjoint(attributes)

    materialization_gate = config["attribute_resolution"][
        "missing_attribute_policy"
    ]["pre_netconvert_materialization_gate"]
    assert set(materialization_gate["required_for_every_retained_way"]) == {
        "lanes",
        "maxspeed",
        "oneway",
    }
    assert set(materialization_gate["reject_states"]) == {
        "unresolved",
        "conflict",
        "invalid",
        "missing",
        "valid_but_unsupported",
        "conditional",
        "directionally_asymmetric",
    }
    assert materialization_gate["list_structural_placeholders_separately"] is True
    assert config["failure_policy"][
        "abort_on_unmaterialized_governed_attribute"
    ] is True


def test_access_and_netconvert_audits_are_pinned() -> None:
    config = load_config()
    access_resolution = config["access_resolution"]
    lane_access = access_resolution["lane_specific_access"]
    options = config["netconvert"]["common_options"]
    failure_policy = config["failure_policy"]
    log_audit = failure_policy["netconvert_log_audit"]

    assert lane_access["enabled"] is True
    assert lane_access["runtime_fixture_validation_required"] is True
    assert access_resolution[
        "exact_precedence_requires_pinned_runtime_fixture_validation"
    ] is True
    assert {"motorcar", "hgv", "bus", "delivery"} == set(
        access_resolution["class_specific_tags_to_validate"]
    )
    assert {"access:lanes", "vehicle:lanes"} == set(
        access_resolution["lane_specific_tags_to_validate"]
    )
    assert {"access", "motor_vehicle", "access:lanes", "vehicle:lanes"} <= set(
        lane_access["fixture_tags"]
    )
    assert options["osm.lane-access"] is True
    assert options["osm.annotate-defaults"] is True
    runtime_fixture = access_resolution["runtime_fixture"]
    assert runtime_fixture["path"] == str(RUNTIME_FIXTURE_PATH.relative_to(ROOT))
    assert runtime_fixture["status"] == "failed"
    assert set(runtime_fixture["observed_failures"]) == {
        "unknown_bus_compound_type",
        "generated_bicycle_permission_exceeds_typemap_baseline",
        "motor_vehicle_no_delivery_yes_did_not_restrict_as_expected",
        "vehicle_lanes_introduced_private_permission",
        "missing_attributes_accepted_with_global_defaults",
        "missing_oneway_accepted_as_one_direction_edge",
        "osm_defaults_annotation_did_not_report_missing_oneway",
    }
    assert failure_policy["abort_on_generated_permission_exceeding_typemap"] is True
    assert failure_policy["abort_on_unapproved_default_derived_value"] is True
    assert {
        "Unknown type",
        "Unknown compound type",
        "Discarding unknown compound",
        "Could not add edge",
    } <= set(log_audit["fatal_patterns"])
    assert "Discarding edge" in log_audit["reconcile_or_fail_patterns"]
    assert log_audit["fail_on_unreconciled_exclusion"] is True


def test_runtime_fixture_covers_access_and_missing_attribute_cases() -> None:
    root = ElementTree.parse(RUNTIME_FIXTURE_PATH).getroot()
    ways = {way.attrib["id"]: way for way in root.findall("way")}
    tags = {
        way_id: {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
        for way_id, way in ways.items()
    }

    assert tags["100"] | {"access": "no", "bus": "yes"} == tags["100"]
    assert tags["200"] | {"motor_vehicle": "no", "delivery": "yes"} == tags["200"]
    assert "access:lanes" in tags["300"]
    assert "vehicle:lanes" in tags["400"]
    assert {"lanes", "maxspeed", "oneway"}.isdisjoint(tags["600"])


def test_left_hand_traffic_and_oneway_materialization_are_mandatory() -> None:
    config = load_config()
    traffic_side = config["traffic_side"]
    options = config["netconvert"]["common_options"]
    oneway = config["attribute_rules"]["oneway"]

    assert traffic_side["lefthand"] is True
    assert traffic_side["reverse_osm_oneway_direction"] is False
    assert options["lefthand"] is True
    assert oneway["ordinary_road_without_oneway_tag"] == (
        "derived_bidirectional_osm_rule"
    )
    assert oneway["motorway_without_explicit_value"] == "derived_yes_osm_rule"
    assert oneway["motorway_link_without_explicit_value"] == "unresolved"
    assert oneway["explicit_reverse"] == (
        "valid_but_unsupported_stop_until_directional_tag_safe_transform"
    )
    assert oneway["statistical_placeholder_allowed"] is False
    assert oneway["materialize_derived_bidirectional_as"] == "no"
    assert oneway["absent_typemap_value_may_fallback_to"] == "oneway_true"
    assert oneway["require_materialized_value_before_netconvert"] is True


def test_structural_imputation_is_rule_based_and_formal_use_is_forbidden() -> None:
    config = load_config()
    imputation = config["structural_imputation"]

    assert set(imputation["allowed_attributes"]) == {"lanes", "maxspeed"}
    assert set(imputation["prohibited_attributes"]) == {"oneway", "access"}
    assert imputation["applicable_profile"] == "structural"
    assert imputation["applicable_criticality"] == {
        "lanes": "L1",
        "maxspeed": "S1",
    }
    assert imputation["formal_use_allowed"] is False
    assert imputation["lanes"]["grouping"] == ["highway", "oneway_status"]
    lane_donors = imputation["lanes"]["donor_eligibility"]
    speed_donors = imputation["maxspeed_kmh"]["donor_eligibility"]
    assert lane_donors["require_consistent_explicit_lanes"] is True
    assert "require_consistent_explicit_maxspeed" not in lane_donors
    assert speed_donors["require_canonical_numeric_explicit_maxspeed"] is True
    assert "require_consistent_explicit_lanes" not in speed_donors
    for rule in (imputation["lanes"], imputation["maxspeed_kmh"]):
        assert rule["statistic"] == "unique_mode"
        assert rule["minimum_sample_size"] == 30
        assert rule["minimum_mode_share"] == 0.5
        assert rule["tie_policy"] == "unresolved"
        assert rule["insufficient_evidence_policy"] == "unresolved"
        assert rule["prohibit_automatic_fallback_to_adjacent_highway_class"] is True

    formal = config["attribute_resolution"]["missing_attribute_policy"]["profiles"][
        "formal"
    ]
    assert formal["allow_structural_placeholder"] is False
    assert formal["allow_derived_validated_model"] is True
    assert formal["require_validation_record_for_derived_model"] is True


def test_attribute_classification_basic_design_is_machine_registered() -> None:
    policy = load_config()["road_criticality"]

    assert policy["population_source"] == "accepted_relation_closure_candidate_ways"
    assert policy["population_hash_binding"] == "relation_closed_osm_sha256"
    assert policy["subgraph_role_enum"] == [
        "final",
        "topology_support",
        "excluded",
    ]
    assert policy["one_profile_per_artifact"] is True
    assert policy["record_id_format"] == "acr:<osm_way_id>:<attribute>:<profile>"
    assert policy["record_order"] == [
        "numeric_osm_way_id_ascending",
        "lanes_before_maxspeed",
        "structural_before_formal",
        "record_revision_ascending",
    ]
    assert policy["classification_rule_priority"]["lanes"] == [
        f"LANE-CRIT-{number:03d}" for number in range(1, 8)
    ]
    assert policy["classification_rule_priority"]["maxspeed"] == [
        f"SPEED-CRIT-{number:03d}" for number in range(1, 7)
    ]
    assert policy["review_status_enum"] == [
        "machine_classified",
        "review_required",
        "reviewed",
        "stopped",
    ]
    assert policy["record_sha256_canonicalization"]["standard"] == (
        "RFC_8785_JSON_Canonicalization_Scheme"
    )
    assert (
        policy["semantic_validator"]
        == "05_src/traffic_simulation/network/validate_attribute_classification.py"
    )
    assert set(policy["implemented_schemas"]) == {
        "classification_predicates.schema.json",
        "predicate_source_registry.schema.json",
        "attribute_classification.schema.json",
        "attribute_classification_fixture.schema.json",
    }
    fixtures = policy["fixture_collection"]
    assert fixtures["schema_version"] == 2
    assert fixtures["case_count"] == 19
    assert fixtures["required_negative_case_count"] == 10
    assert fixtures["oracle_generated_by_production_code"] is False
    assert fixtures["independent_human_review_required"] is False
    assert fixtures["independent_human_acceptance_complete"] is False
    assert fixtures["independent_human_review_waived"] is True
    assert fixtures["independent_human_review_waiver_date"] == "2026-07-30"
    assert (
        fixtures["review_mode"]
        == "automated_validation_without_independent_human_review"
    )
    assert fixtures["input_contract"] == "complete_execution_input"
    assert fixtures["coverage_contract"] == (
        "coverage_id_to_oracle_assertion_ids"
    )
    assert fixtures["acceptance_allowed_is_derived"] is True
    assert (ROOT / fixtures["builder"]).is_file()
    for field in ("manifest", "inputs", "oracles", "review"):
        assert (ROOT / fixtures[field]).is_file()
    predicates = policy["predicate_artifact"]
    assert predicates["one_record_per_population_way"] is True
    assert predicates["evidence_required_for_false_and_true"] is True
    assert "is_accepted_delivery_route" in predicates["required_predicates"]
    assert "topology_support_without_reason" in predicates["forbidden_combinations"]
    generator = policy["predicate_generator"]
    assert (ROOT / generator["implementation"]).is_file()
    assert (ROOT / generator["source_registry_schema"]).is_file()
    assert generator["requires_accepted_population"] is True
    assert generator["real_data_requires_acceptance_artifact"] is True
    assert generator["minimum_real_data_config_version"] == 16
    assert set(generator["externally_governed_predicates"]) == {
        "is_calibration_segment",
        "is_validation_segment",
        "is_major_junction_approach",
        "is_accepted_delivery_route",
        "is_sensitivity_elevated",
    }
    assert len(generator["osm_derived_predicates"]) == 14


def test_permissions_are_materialized_before_final_conversion_and_only_audited_after() -> None:
    config = load_config()
    resolution = config["access_resolution"]
    enforcement = resolution["enforcement"]

    assert resolution["osm_override_application_order"] == [
        "access",
        "vehicle",
        "motor_vehicle",
        "class_specific",
        "direction_specific",
        "lane_specific",
    ]
    assert resolution["resolve_osm_overrides_before_research_scope_intersection"] is True
    assert (
        resolution["final_permission_composition"]
        == "intersection_of_research_scope_and_resolved_osm_permissions"
    )
    assert resolution["unknown_or_unsupported_rule"] == "unresolved"
    assert enforcement["compute_expected_permissions_before_netconvert"] is True
    assert enforcement["compare_expected_with_generated_permissions"] is True
    assert enforcement["materialize_expected_permissions_before_final_netconvert"] is True
    assert enforcement["materialization_target"] == "explicit_final_netconvert_input"
    assert enforcement["final_netconvert_must_build_connections_from_materialized_permissions"] is True
    assert enforcement["patch_generated_net_xml"] is False
    assert enforcement["post_netconvert_operation"] == "audit_only"
    assert enforcement["prohibit_unsourced_automatic_expansion"] is True
    assert enforcement["materialized_permissions_must_not_expand_typemap_baseline"] is True
    assert enforcement["require_exact_expected_permission_match_after_conversion"] is True
    assert enforcement["mismatch_policy"] == "stop_fix_input_and_rerun_final_netconvert"
    assert enforcement["validate_lane_and_connection_permissions"] is True


def test_formal_network_precedes_demand_calibration_and_validation() -> None:
    config = load_config()
    order = config["network_stage_order"]

    assert order["required_sequence"] == [
        "structural_network",
        "structural_debug",
        "governed_attributes_and_lane_permissions",
        "provisional_connections",
        "connection_permissions_and_final_connection_set",
        "signal_junction_and_tls_link_review",
        "formal_baseline_network",
        "demand_inputs",
        "signal_timing_calibration",
        "calibration",
        "independent_validation",
        "delivery_classical_qaoa_evaluation",
    ]
    assert order["calibration_requires_formal_network"] is True
    assert order["demand_simulation_requires_formal_network"] is True
    assert order["structural_placeholders_must_be_zero_before_calibration"] is True
    assert order["changing_formal_network_invalidates_downstream_calibration"] is True
    assert order["changing_signal_junction_or_link_structure_is_formal_network_change"] is True


def test_structural_gate_uses_preregistered_measurable_metrics() -> None:
    gate = load_config()["structural_quality_gate"]

    assert gate["threshold_status"] == "pending_preregistration_with_rationale"
    assert gate["result_blind_threshold_selection_required"] is True
    assert set(gate["metrics"]) == {
        "retained_osm_way_rate",
        "major_road_reachability_rate",
        "largest_component_drivable_length_share",
        "direction_mismatch_count",
        "representative_od_route_success_rate",
        "sumo_load_status",
        "warning_counts",
    }
    assert gate["metrics"]["warning_counts"]["unclassified_warning_policy"] == "stop"
    assert gate["formal_promotion_requires_all_thresholds_registered"] is True


def test_runtime_manifest_and_one_to_many_provenance_are_required() -> None:
    config = load_config()
    fields = set(config["execution_environment"]["required_build_manifest_fingerprint"])
    provenance = config["geometry_and_connectivity"]["provenance_relation"]

    assert {
        "sumo_container_image_digest",
        "proj_version",
        "analysis_container_image_digest",
        "python_dependency_lock_sha256",
        "locale",
        "output_precision_options",
        "typemap_sha256",
        "osm_input_sha256",
        "network_config_sha256",
        "exact_command",
    } <= fields
    assert provenance["cardinality"] == (
        "osm_way_to_many_sumo_edges_to_many_sumo_lanes"
    )
    assert provenance["require_every_lane_traceable_to_osm_or_explicit_generation_rule"] is True
    assert provenance["unmapped_lane_policy"] == "stop"


def test_observation_and_calibration_governance_are_fail_closed() -> None:
    config = load_config()
    observations = config["traffic_observation_policy"]
    calibration = config["calibration_policy"]

    assert observations["acquisition_runs_in_parallel_with_network_pipeline"] is True
    assert observations["periodic_snapshot_automation_status"] == "pending"
    assert observations["temporal_alignment"]["same_date_and_time_window_preferred"] is True
    assert observations["temporal_alignment"][
        "mixed_time_observations_require_adjustment_and_uncertainty_record"
    ] is True
    assert calibration["prerequisite_network_profile"] == "formal"
    assert calibration["simultaneous_free_calibration_of_all_parameter_groups"] is False
    assert calibration["metric_threshold_status"] == (
        "pending_preregistration_with_rationale"
    )
    stochastic = calibration["stochastic_evaluation"]
    assert stochastic["multiple_seeds_required"] is True
    assert stochastic["warmup_period_required"] is True
    assert stochastic["common_random_numbers_for_comparisons"] is True


def test_formal_review_covers_the_selectable_candidate_subgraph() -> None:
    scope = load_config()["formal_candidate_subgraph"]

    assert scope["review_scope"] == "all_edges_selectable_by_any_compared_algorithm"
    assert set(scope["terminals"]) == {"depots", "all_customers", "charging_facilities"}
    assert scope["include_all_reachable_edges_between_terminals"] is True
    assert scope["final_selected_routes_only_is_prohibited"] is True


def test_requirement_matrix_does_not_conflate_policy_with_validation() -> None:
    status = load_config()["status"]
    matrix = status["requirement_matrix"]

    assert status["formal_build_input_ready"] is False
    assert status["formal_network_accepted"] is False
    assert status["downstream_experiment_ready"] is False
    assert status["specification"]["state"] == "current_governed_draft"
    assert status["specification"]["formal_execution_authorized"] is False
    assert matrix["typemap_xml"]["xsd_validation"] == "passed"
    assert matrix["typemap_xml"]["runtime_validation"] == (
        "failed_importer_governance_fixture"
    )
    assert matrix["attribute_resolver"]["runtime_validation"] == (
        "positive_negative_bidirectional_and_failure_contract_fixtures_passed"
    )
    assert matrix["permission_expectation_artifact"]["implementation"] == (
        "implemented_v15_schema_shape"
    )
    assert matrix["permission_expectation_artifact"]["real_data_validation"] == (
        "incomplete_schema_valid_artifact_emitted_from_registered_input"
    )
    assert matrix["permission_expectation_artifact"]["eligibility"]["eligible"] is False
    assert matrix["attribute_resolver"]["real_data_validation"] == (
        "structural_dry_run_completed_with_governed_blockers"
    )
    assert matrix["permission_materializer"]["implementation"] == "not_implemented"
    assert matrix["permission_materializer"]["runtime_validation"] == "not_run"
    assert matrix["formal_network"]["implementation"] == "not_built"
    assert matrix["formal_network"]["eligibility"]["eligible"] is False


def test_permission_materializer_format_and_mapping_rules_are_fixed() -> None:
    contract = load_config()["permission_materialization"]

    assert contract["contract_version"] == "sumo_plain_xml_permissions_v3"
    assert contract["implementation_status"] == "not_implemented"
    assert contract["fixture_status"] == "not_run"
    assert contract["target_sumo_version"] == "1.24.0"
    assert contract["materialized_output"]["mutate_provisional_files_in_place"] is False
    assert contract["materialized_output"]["final_net_xml_is_audit_only"] is True
    empty_lane = contract["materialized_output"]["empty_lane_permission_policy"]
    assert empty_lane["serialization"] == "disallow_all"
    assert empty_lane["attribute"] == "disallow"
    assert empty_lane["value"] == "all"
    assert empty_lane["pinned_runtime_fixture_required"] is True
    assert contract["provenance_mapping"]["lane_orig_id_source"] == (
        "lane_param_key_origId"
    )
    assert contract["provenance_mapping"]["prohibit_edge_id_sign_as_direction_evidence"] is True
    lane_rule = contract["lane_expectation_rule"]
    assert lane_rule["mapping_formula"] == (
        "sumo_lane_index_equals_lane_count_minus_one_minus_resolver_lane_position"
    )
    assert lane_rule["expected_set_must_be_subset_of_typemap_baseline"] is True
    assert lane_rule["fixture_must_confirm_order_under_lefthand_true"] is True
    connection_rule = contract["connection_expectation_rule"]
    assert connection_rule["candidate_source"] == "provisional_connections_only"
    assert connection_rule["synthesize_missing_or_turn_restricted_connections"] is False
    assert connection_rule["empty_expected_set"] == "remove_connection_and_record_reason"
    handoff = contract["signal_structure_handoff"]
    assert handoff["prohibit_provisional_tll_as_final_input"] is True
    assert contract["materialized_output"]["tls_artifact_action"] == (
        "do_not_copy_provisional_tll_to_final_inputs"
    )
    assert handoff["review_occurs_after_final_connection_set"] is True
    assert handoff["tls_connection_assignment_location"] == (
        "tllogic_file_connection_elements"
    )
    assert contract["edge_provenance_artifact"][
        "coordinate_matching_in_formal_profile"
    ] == "prohibited"
    assert contract["lane_expectation_rule"][
        "backward_values_are_not_reversed_by_resolver"
    ] is True
    assert contract["materialized_output"]["all_lanes_empty_edge_policy"][
        "action"
    ] == "remove_directed_edge_and_incident_connections"
    assert contract["final_conversion"]["inputs"] == {
        "node-files": "governed_provisional.nod.xml",
        "edge-files": "governed_permissions.edg.xml",
        "connection-files": "governed_reviewed.con.xml",
        "tllogic-files": "governed_reviewed.tll.xml",
    }


def test_requirement_matrix_covers_every_current_formal_blocker() -> None:
    matrix = load_config()["status"]["requirement_matrix"]
    required = {
        "registered_source_and_extract",
        "typemap_xml",
        "attribute_resolver",
        "permission_expectation_artifact",
        "permission_materializer",
        "permission_post_conversion_audit",
        "reverse_oneway_handler",
        "formal_attribute_evidence",
        "junction_join_review",
        "signal_structure",
        "vehicle_input_validator",
        "build_prepare_and_validate_pipeline",
        "environment_and_manifest_fingerprint",
        "warning_and_exclusion_audit",
        "structural_quality_gate",
        "formal_candidate_subgraph_review",
        "reproducibility_artifact_publication",
        "formal_network",
        "demand_and_observation_inputs",
        "calibration_design",
        "optimization_comparison_design",
    }

    assert set(matrix) == required
    state_fields = {
        "policy",
        "gate",
        "implementation",
        "unit_validation",
        "xsd_validation",
        "runtime_validation",
        "real_data_validation",
        "eligibility",
    }
    assert all(set(state) == state_fields for state in matrix.values())
    assert all(
        isinstance(state["eligibility"]["eligible"], bool)
        for state in matrix.values()
    )
    assert all(state["eligibility"]["eligible"] is False for state in matrix.values())


def test_readiness_gates_are_acyclic_and_partition_requirements() -> None:
    status = load_config()["status"]
    gates = status["readiness_gates"]
    assert list(gates) == [
        "formal_build_input_ready",
        "formal_network_acceptance",
        "downstream_experiment_ready",
    ]
    assert gates["formal_network_acceptance"]["requires_gate"] == (
        "formal_build_input_ready"
    )
    assert gates["downstream_experiment_ready"]["requires_gate"] == (
        "formal_network_acceptance"
    )
    assigned = [name for gate in gates.values() for name in gate["requires"]]
    assert len(assigned) == len(set(assigned))
    assert set(assigned) == set(status["requirement_matrix"])
    assert "formal_network" not in gates["formal_build_input_ready"]["requires"]
    assert "formal_candidate_subgraph_review" in gates[
        "downstream_experiment_ready"
    ]["requires"]


def test_governed_config_validator_and_schema_pass() -> None:
    config = config_validator.load_config(CONFIG_PATH)
    config_validator.validate_config(config)
    assert (ROOT / config["config_schema"]).is_file()
    assert (ROOT / config["config_validator"]).is_file()


def test_signal_structure_is_part_of_formal_network_but_timing_is_calibrated() -> None:
    policy = load_config()["traffic_lights"]

    assert policy["structure"]["must_be_fixed_before_formal_network"] is True
    assert policy["structure"]["includes_connection_to_tls_link_mapping"] is True
    assert policy["structure"]["change_invalidates_calibration_and_validation"] is True
    assert policy["timing"]["calibrated_after_demand_input"] is True


def test_connectivity_gate_is_vclass_directional_and_reports_length() -> None:
    gate = load_config()["structural_quality_gate"]
    evaluation = gate["vclass_directional_evaluation"]

    assert set(gate["metrics"]["retained_osm_way_rate"]["report_units"]) == {
        "way_count",
        "way_length_m",
    }
    assert evaluation["directed_reachability_required"] is True
    assert evaluation["depot_to_all_customers_and_chargers_required"] is True
    assert evaluation["all_customers_and_chargers_to_depot_return_required"] is True
    assert set(evaluation["vclasses"]) == GOVERNED_VCLASSES


def test_seeds_are_separated_by_role() -> None:
    registry = load_config()["calibration_policy"]["seed_registry"]

    assert set(registry["shared_environment_seeds"]) == {
        "instance_seed",
        "demand_generation_seed",
        "traffic_simulation_seed",
    }
    assert set(registry["algorithm_specific_seed_sets"]) == {
        "classical_solver_seed",
        "qaoa_parameter_seed",
        "qaoa_sampling_seed",
    }
    assert registry["same_integer_across_algorithm_specific_seeds_has_no_equivalence_claim"] is True


def test_small_reproducibility_artifacts_and_test_evidence_are_versioned() -> None:
    config = load_config()
    artifacts = config["artifact_retention"]
    evidence = config["test_execution_evidence"]

    assert artifacts["large_generated_artifacts"]["git_tracked"] is False
    assert artifacts["small_reproducibility_artifacts"]["immutable_versioning_required"] is True
    assert set(artifacts["small_reproducibility_artifacts"]["required"]) == {
        "netccfg",
        "build_manifest_json",
        "build_summary_json",
        "warning_classification_json",
        "artifact_checksums_txt",
    }
    assert set(evidence["required_fields"]) == {
        "git_commit",
        "container_digest",
        "exact_command",
        "test_collection_hash",
        "exit_code",
        "log_sha256",
        "started_at",
        "finished_at",
    }


def test_surface_and_vehicle_class_policies_are_explicit() -> None:
    config = load_config()
    typemap = config["typemap_policy"]
    delivery = config["vehicle_scope"]["use_profiles"]["delivery_routing"]

    assert typemap["road_function_and_surface_are_separate_axes"] is True
    assert typemap["surface_assessment"]["primary_tag"] == "surface"
    assert typemap["surface_assessment"]["retained_highway_may_still_be_unpaved"] is True
    assert delivery["vehicle_to_vclass_mapping"] == {
        "small_delivery_van": "delivery",
        "heavy_freight_vehicle": "truck",
    }
    assert delivery["vehicle_vclass_is_immutable_within_problem_instance"] is True


def test_access_provenance_and_geometry_policies_are_consistent() -> None:
    config = load_config()

    assert config["access_resolution"]["allow_permission_placeholder"] is False
    assert config["access_resolution"][
        "allow_unresolved_record_in_structural_audit"
    ] is True
    assert config["netconvert"]["common_options"]["geometry.remove"] is False
    assert config["netconvert"]["formal_conversion_options"]["geometry.remove"] is False
    assert set(config["provenance"]["distinguish_value_classes"]) == set(
        config["attribute_resolution"]["value_states"]
    )


def test_external_source_uses_and_runtime_stop_counts_are_governed() -> None:
    config = load_config()
    census = config["external_sources"]["supplements"]["road_traffic_census"]
    regulations = config["external_sources"]["supplements"][
        "jartic_traffic_regulations"
    ]

    assert set(census["verified_uses"]) == {
        "lanes",
        "road_width",
        "traffic_volume",
        "travel_speed",
    }
    assert set(census["candidate_uses_pending_field_definition_verification"]) == {
        "designated_maxspeed",
        "oneway",
    }
    assert set(regulations["required_record_fields"]) == {
        "regulation_type",
        "effective_from",
        "effective_until",
        "recurrence",
        "vehicle_scope",
        "legal_or_administrative_source",
        "snapshot_date",
    }
    assert {
        "unmapped_lanes",
        "unmapped_connections",
        "unexpected_connections",
        "missing_expected_connections",
        "tls_link_mapping_mismatches",
        "tls_phase_state_length_mismatches",
        "unclassified_warnings",
        "unreconciled_removed_edges",
    } <= set(config["failure_policy"]["post_netconvert_zero_counts"])


def test_configuration_dates_and_policy_documents_are_unambiguous() -> None:
    config = load_config()

    assert config["schema_version"] == 2
    assert config["config_id"] == "ota_ward_sumo_network_v15"
    assert config["config_version"] == 15
    assert config["created_at"] == "2026-07-18"
    assert config["last_updated_at"] == "2026-07-25"
    assert config["configuration_lineage_date"] == "2026-07-16"
    assert config["decision_date"] == "2026-07-23"
    documents = config["policy_documents"]
    assert set(documents) == {
        "attribute_governance",
        "current_specification",
        "change_log",
        "network_build_protocol",
        "traffic_calibration_protocol",
        "optimization_protocol",
        "attribute_criticality_and_evidence",
        "resolver_exception_decision_table",
        "requirements_traceability",
    }
    for path in documents.values():
        assert (ROOT / path).is_file()


def test_network_scope_and_use_specific_vclass_profiles_are_distinct() -> None:
    config = load_config()
    scope = config["vehicle_scope"]
    profiles = scope["use_profiles"]

    assert set(scope["keep_vclasses"]) == GOVERNED_VCLASSES
    assert set(profiles["delivery_routing"]["vclasses"]) == {"delivery", "truck"}
    assert set(profiles["background_traffic"]["vclasses"]) == {
        "passenger",
        "taxi",
        "bus",
        "coach",
        "delivery",
        "truck",
        "motorcycle",
    }
    assert scope["excluded_motorized_vclasses"] == {
        "moped": "outside_delivery_research_scope"
    }


def test_later_stage_context_inputs_are_not_core_comparison_inputs() -> None:
    policy = load_config()["later_stage_context_inputs"]

    assert policy["core_comparison_input"] is False
    assert policy["introduction_requires_separate_stage_and_recorded_rationale"] is True
    retained = policy["retained_for_later_use"]
    assert set(retained) == {
        "overseas_driving_behavior",
        "weather",
        "incidents",
        "pedestrian_related_driving_behavior_fields",
    }
    assert (
        retained["pedestrian_related_driving_behavior_fields"][
            "pedestrian_agents_or_pedestrian_network_mode"
        ]
        is False
    )


def test_moped_access_tags_are_explicitly_outside_resolution_scope() -> None:
    config = load_config()

    assert config["access_resolution"]["out_of_scope_class_tags_ignored"] == [
        "moped"
    ]


def test_missing_oneway_tag_is_distinct_from_unresolved_direction() -> None:
    policy = load_config()["attribute_rules"]["oneway"]

    assert policy["ordinary_road_without_oneway_tag"] == (
        "derived_bidirectional_osm_rule"
    )
    assert policy["materialize_derived_bidirectional_as"] == "no"
    assert policy["missing_source_tag_is_not_unresolved_by_itself"] is True
    assert policy["preserve_source_absence_and_derivation_in_audit"] is True
    assert policy["statistical_placeholder_allowed"] is False


def test_only_turn_restriction_relations_are_retained() -> None:
    policy = load_config()["relation_resolution"]

    assert policy["retained_types"] == ["restriction"]
    assert policy["discard_other_types_before_member_reference_validation"] is True
    assert policy["retained_relation_missing_way_reference_policy"] == "stop"
    assert policy["excluded_relation_count_required"] is True
    assert policy["input_closure"] == {
        "base_elements": "all_nodes_and_ways_from_registered_bbox_extract",
        "retained_relations": "restriction_relations_present_in_bbox_extract",
        "referenced_element_authority": "registered_regional_raw_pbf",
        "recursively_add_referenced_elements": True,
        "record_intermediate_pbf_and_xml_sha256": True,
    }


def test_design_decisions_and_sensitivity_metrics_are_separated() -> None:
    config = load_config()
    assessment = config["design_decision_assessment"]
    items = assessment["items"]
    sensitivity = config["design_sensitivity"]
    factors = sensitivity["factors"]
    routing = config["routing"]

    assert assessment["impact_ranking_before_sensitivity"] == "prohibited"
    assert items["priority"]["category"] == (
        "design_choice_with_regional_validity_limit"
    )
    assert items["priority"]["regional_validity"] == (
        "not_empirically_calibrated_for_tokyo"
    )
    assert items["typemap_attribute_omission"]["category"] == (
        "evidence_governance_design_choice"
    )
    validator_risk = items["incomplete_pre_and_post_validators"]
    assert validator_risk["category"] == (
        "implementation_and_quality_assurance_risk"
    )
    assert validator_risk["severity"] == "high"
    assert validator_risk["blocks_formal_build"] is True
    assert items["governance_fixture_values"]["representative_of_tokyo"] is False
    assert items["governance_fixture_values"]["isolated_from_formal_experiments"] is True

    assert routing["common_options"]["weights.priority-factor"] == 0.0
    assert routing["priority_policy"][
        "direct_priority_penalty_in_static_route_choice"
    ] is False
    assert sensitivity["prohibit_post_hoc_condition_selection"] is True
    assert sensitivity["thresholds"]["status"] == (
        "pending_preregistration_with_rationale"
    )
    assert set(factors["priority"]["primary_metrics"]) == {
        "junction_waiting_time",
        "stop_count",
        "travel_time",
        "delay",
    }
    assert set(factors["service_permissions"]["primary_metrics"]) >= {
        "delivery_reachable_edge_count",
        "reachable_customer_count",
    }
    priority_alternatives = {
        alternative["id"]: alternative
        for alternative in factors["priority"]["alternatives"]
    }
    assert priority_alternatives["uniform_priority_1"][
        "value_for_all_retained_types"
    ] == 1
    simplified = priority_alternatives["simplified_three_level_hierarchy"][
        "values"
    ]
    assert set(simplified) == {"1", "2", "3"}
    simplified_type_ids = {
        type_id for type_ids in simplified.values() for type_id in type_ids
    }
    policy = config["typemap_policy"]
    retained_type_ids = {
        *(f"highway.{value}" for value in policy["retained_shared_highway_types"]),
        *policy["retained_compound_type_ids"],
        *policy["retained_dedicated_motorized_type_ids"],
    }
    assert simplified_type_ids == retained_type_ids


def test_out_of_scope_types_are_explicitly_discarded() -> None:
    types = load_types()
    discarded = {
        type_id
        for type_id, attributes in types.items()
        if attributes.get("discard") == "true"
    }

    assert "highway.footway" in discarded
    assert "highway.cycleway" in discarded
    assert "highway.track" in discarded
    assert "highway.construction" in discarded
    assert "railway.rail" in discarded
    assert "railway.construction" in discarded
