"""Validate the governed Tokyo motorized OSM typemap."""

from __future__ import annotations

import hashlib
from pathlib import Path
from xml.etree import ElementTree

import yaml


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
    "moped",
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
    assert len(types["highway.residential"]["allow"].split()) == 8
    assert len(types["highway.motorway"]["allow"].split()) == 7
    assert "moped" not in types["highway.motorway"]["allow"].split()
    assert len(types["highway.service|bus"]["allow"].split()) == 2
    assert types["highway.busway"]["allow"] == "bus"


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
    assert imputation["applicable_criticality"] == "noncritical_only"
    assert imputation["formal_use_allowed"] is False
    assert imputation["lanes"]["grouping"] == ["highway", "oneway_status"]
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


def test_access_precedence_and_permission_enforcement_only_reduce_scope() -> None:
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
    assert enforcement["patch_operation"] == (
        "evidence_backed_exact_expected_permissions"
    )
    assert enforcement["evidence_required_for_restriction_or_specific_exception"] is True
    assert enforcement["prohibit_unsourced_automatic_expansion"] is True
    assert enforcement["patch_may_expand_importer_output_only_with_evidence"] is True
    assert enforcement["patch_must_not_expand_typemap_baseline"] is True
    assert enforcement["require_exact_expected_permission_match_after_patch"] is True
    assert enforcement["revalidate_connections_after_patch"] is True


def test_formal_network_precedes_demand_calibration_and_validation() -> None:
    config = load_config()
    order = config["network_stage_order"]

    assert order["required_sequence"] == [
        "structural_network",
        "structural_debug",
        "governed_attributes_and_permissions",
        "formal_baseline_network",
        "demand_and_signal_inputs",
        "calibration",
        "independent_validation",
        "delivery_classical_qaoa_evaluation",
    ]
    assert order["calibration_requires_formal_network"] is True
    assert order["demand_simulation_requires_formal_network"] is True
    assert order["structural_placeholders_must_be_zero_before_calibration"] is True
    assert order["changing_formal_network_invalidates_downstream_calibration"] is True


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
    assert "moped" not in profiles["background_traffic"]["vclasses"]


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
