import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "calibration" / "fix_ota_sumo_measurement_locations.py"
SPEC = importlib.util.spec_from_file_location("fix_ota_sumo_measurement_locations", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_external_incoming_edges_excludes_internal_cluster_links_and_outgoing_edges():
    edges = {
        "enter_a": {"from": "outside_a", "to": "inside_1", "motorized": True},
        "enter_b": {"from": "outside_b", "to": "inside_2", "motorized": True},
        "cluster_link": {"from": "inside_1", "to": "inside_2", "motorized": True},
        "leave": {"from": "inside_2", "to": "outside_c", "motorized": True},
        "foot_only": {"from": "outside_d", "to": "inside_1", "motorized": False},
    }
    assert MODULE.external_incoming_edges(edges, {"inside_1", "inside_2"}) == ["enter_a", "enter_b"]


def test_short_boundary_split_is_absorbed_before_incoming_edges_are_fixed():
    edges = {
        "real_approach": {"from": "outside", "to": "split", "motorized": True, "length": 40.0},
        "tiny_split": {"from": "split", "to": "inside", "motorized": True, "length": 0.2},
    }
    cluster = MODULE.absorb_short_incoming_links(edges, {"inside"}, minimum_detector_length=5.1)
    assert cluster == {"inside", "split"}
    assert MODULE.external_incoming_edges(edges, cluster) == ["real_approach"]


def test_detector_registry_reuses_same_physical_lane_position_across_years():
    registry = MODULE.DetectorRegistry()
    first = registry.register("site_2023", "edge_0", "edge_0_0", 20.004)
    second = registry.register("site_2024", "edge_0", "edge_0_0", 20.0044)
    assert first == second
    assert len(registry.records) == 1
    assert registry.records[0]["observation_groups"] == ["site_2023", "site_2024"]


def test_split_policy_never_uses_2024_for_calibration():
    assert MODULE.use_split(2023) == "calibration"
    assert MODULE.use_split(2024) == "independent_validation"


def test_detector_position_requires_a_real_lane_interior():
    assert MODULE.safe_lane_position(100.0, 50.0) == 50.0
    assert MODULE.safe_lane_position(100.0, 0.0) == 0.1
    assert MODULE.safe_lane_position(100.0, 100.0) == 99.9
