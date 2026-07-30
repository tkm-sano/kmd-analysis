from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from shapely.geometry import box

from traffic_simulation.network import build_sumo_network as build


FIXTURE = (
    Path(__file__).parent / "fixtures/relation_closure/bbox.opl"
)
CLOSED_FIXTURE = (
    Path(__file__).parent / "fixtures/relation_closure/closed.opl"
)


def fixture_lines(_path: Path):
    yield from FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)


def closed_fixture_lines(_path: Path):
    yield from CLOSED_FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)


def configured(tmp_path: Path) -> dict:
    config = build.load_config()
    config["relation_policy"]["known_required_relation_ids"] = [101]
    return config


def test_bbox_scope_keeps_ordinary_and_bus_restrictions_separately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(build, "iter_osmium_opl", fixture_lines)
    result = build.scan_bbox(tmp_path / "bbox.pbf", tmp_path / "ids", configured(tmp_path))

    assert result["retained_by_type"] == {
        "restriction": 1,
        "restriction:bus": 1,
    }
    assert result["retained_by_category"] == {
        "bus_turn_restriction": 1,
        "ordinary_turn_restriction": 1,
    }
    assert result["discarded_by_type"] == {"route": 1}
    assert (tmp_path / "ids").read_text().splitlines()[-2:] == ["r100", "r101"]


def test_closed_scan_separates_final_and_topology_support_ways(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(build, "iter_osmium_opl", fixture_lines)
    monkeypatch.setattr(
        build,
        "load_study_area",
        lambda _region: SimpleNamespace(
            api_boundary=box(139.695, 35.545, 139.715, 35.555)
        ),
    )
    config = configured(tmp_path)
    bbox = build.scan_bbox(tmp_path / "bbox.pbf", tmp_path / "ids", config)
    monkeypatch.setattr(build, "iter_osmium_opl", closed_fixture_lines)
    result = build.scan_closed(tmp_path / "closed.pbf", bbox, config)

    assert result["candidate_ids"] == {10, 11}
    assert result["final_ids"] == {10}
    assert result["topology_support_ids"] == {11}
    assert result["final_node_ids"] == {1, 2}
    assert result["topology_support_node_ids"] == {3, 4}
    assert result["reference_validation"] == {
        "missing_node_references": 0,
        "missing_way_members": 0,
        "missing_relation_members": 0,
        "relation_cycles": 0,
        "duplicate_identifiers": 0,
    }


def test_bbox_scan_stops_on_unclassified_vehicle_restriction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines = list(fixture_lines(tmp_path))
    lines[-1] = (
        "r102 v1 dV c0 t2026-07-16T00:00:00Z i1 u "
        "Ttype=restriction:hgv Mw10@from,n2@via,w11@to\n"
    )
    monkeypatch.setattr(build, "iter_osmium_opl", lambda _path: iter(lines))

    with pytest.raises(build.PrepareError, match="unclassified vehicle-specific"):
        build.scan_bbox(tmp_path / "bbox.pbf", tmp_path / "ids", configured(tmp_path))


def test_closed_scan_stops_on_missing_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = configured(tmp_path)
    monkeypatch.setattr(build, "iter_osmium_opl", fixture_lines)
    bbox = build.scan_bbox(tmp_path / "bbox.pbf", tmp_path / "ids", config)
    lines = list(closed_fixture_lines(tmp_path))
    lines[4] = lines[4].replace("n1,n2", "n1,n999")
    monkeypatch.setattr(build, "iter_osmium_opl", lambda _path: iter(lines))

    with pytest.raises(build.PrepareError, match="missing_nodes=1"):
        build.scan_closed(tmp_path / "closed.pbf", bbox, config)


def test_relation_cycle_detection_is_fail_closed() -> None:
    assert build.relation_cycles({100: {101}, 101: {100}}) == [[100, 101, 100]]


def test_duplicate_identifiers_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines = list(fixture_lines(tmp_path))
    lines.insert(1, lines[0])
    monkeypatch.setattr(build, "iter_osmium_opl", lambda _path: iter(lines))

    with pytest.raises(build.PrepareError, match="duplicate identifiers"):
        build.scan_bbox(tmp_path / "bbox.pbf", tmp_path / "ids", configured(tmp_path))


def test_fixed_acceptance_values_fail_closed_on_population_drift(
    tmp_path: Path,
) -> None:
    config = configured(tmp_path)
    bbox = {
        "counts": config["acceptance"]["element_counts"]["bbox"],
        "retained_by_type": config["acceptance"]["retained_relation_counts"],
    }
    closed = {
        "counts": config["acceptance"]["element_counts"]["closed"],
        "supplemented": {
            "n": list(range(config["acceptance"]["element_counts"]["supplemented"]["nodes"])),
            "w": list(range(config["acceptance"]["element_counts"]["supplemented"]["ways"])),
            "r": [],
        },
        "candidate_ids": set(
            range(config["acceptance"]["road_population"]["governed_candidate_ways"] + 1)
        ),
        "final_ids": set(
            range(config["acceptance"]["road_population"]["final_analysis_target_ways"])
        ),
        "topology_support_ids": set(
            range(config["acceptance"]["road_population"]["topology_support_ways"])
        ),
        "excluded_ids": set(
            range(config["acceptance"]["road_population"]["excluded_ways"])
        ),
    }

    with pytest.raises(build.PrepareError, match="road population differs"):
        build.verify_acceptance(
            config,
            bbox,
            closed,
            config["acceptance"]["output_sha256"],
        )
