import csv
from pathlib import Path

import pytest

from traffic_simulation.calibration.diagnose_marouter_route_generation import (
    audit_demand_coverage,
    audit_route_support,
    experiment_case_command,
    semantic_xml_sha256,
    summarize_fixed_routes,
)


def test_summarize_fixed_routes_identifies_target(tmp_path: Path) -> None:
    routes = tmp_path / "routes.xml"
    routes.write_text(
        """<routes><vehicle id="v"><routeDistribution>
        <route cost="10" probability="0.7" edges="a b c"/>
        <route cost="12" probability="0.3" edges="a target c"/>
        </routeDistribution></vehicle></routes>""",
        encoding="utf-8",
    )
    result = summarize_fixed_routes(routes, "target")
    assert result["route_count"] == 2
    assert result["target_route_count"] == 1
    assert result["best_target_cost_seconds"] == 12
    assert result["target_probability"] == pytest.approx(0.3)


def test_semantic_xml_hash_ignores_comment_whitespace_and_attribute_order(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    first.write_text(
        '<!-- generated now --><routes><route id="r" edges="a b"/></routes>',
        encoding="utf-8",
    )
    second.write_text(
        '<!-- generated later -->\n<routes>\n <route edges="a b" id="r"/>\n</routes>',
        encoding="utf-8",
    )
    assert semantic_xml_sha256(first) == semantic_xml_sha256(second)


def test_audit_route_support_reports_all_six_and_opposite_cooccurrence(
    tmp_path: Path,
) -> None:
    locations = tmp_path / "locations.csv"
    with locations.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "official_observation_section_id",
                "direction",
                "representative_edge_id",
            ],
        )
        writer.writeheader()
        for section, up, down in (
            ("s1", "u1", "d1"),
            ("s2", "u2", "d2"),
            ("s3", "u3", "d3"),
        ):
            writer.writerow(
                {
                    "official_observation_section_id": section,
                    "direction": "UP",
                    "representative_edge_id": up,
                }
            )
            writer.writerow(
                {
                    "official_observation_section_id": section,
                    "direction": "DOWN",
                    "representative_edge_id": down,
                }
            )
    routes = tmp_path / "routes.xml"
    routes.write_text(
        """<routes>
        <flow id="f" fromTaz="o" toTaz="d" number="10">
          <routeDistribution>
            <route cost="10" probability="6" edges="u1 x -x d1"/>
            <route cost="20" probability="4" edges="u2 x d3"/>
          </routeDistribution>
        </flow></routes>""",
        encoding="utf-8",
    )
    rows = audit_route_support(routes, locations)
    keyed = {(row["official_observation_section_id"], row["direction"]): row for row in rows}
    assert len(rows) == 6
    assert keyed[("s1", "UP")]["assigned_route_weight"] == pytest.approx(6)
    assert keyed[("s1", "UP")]["best_target_detour_factor"] == pytest.approx(1)
    assert keyed[("s1", "UP")]["routes_with_opposite_edge"] == 1
    assert keyed[("s1", "UP")]["routes_with_immediate_reversal"] == 1
    assert keyed[("s1", "UP")][
        "immediate_reversal_assigned_weight_fraction"
    ] == pytest.approx(1)
    assert keyed[("s1", "UP")]["route_support_status"] == "PATHOLOGICAL_ONLY"
    assert keyed[("s2", "UP")]["route_support_status"] == "PRESENT_CLEAN"
    assert keyed[("s2", "DOWN")]["route_support_status"] == "ABSENT"


def test_experiment_case_command_supports_case_overrides() -> None:
    config = {
        "sumo_version": "1.24.0",
        "seed": 17,
        "inputs": {
            "network": "net.xml",
            "taz": "taz.xml",
            "assignment_relations": "od.xml",
            "canonical_count_locations": "locations.csv",
        },
        "common": {
            "assignment_method": "SUE",
            "route_choice_method": "logit",
            "paths_penalty": 1.0,
            "max_iterations": 20,
            "max_inner_iterations": 1000,
            "routing_algorithm": "dijkstra",
            "routing_threads": 8,
            "with_taz": True,
        },
    }
    case = {
        "output": "out",
        "paths": 50,
        "paths_penalty": 0.5,
        "max_alternatives": 70,
        "max_iterations": 7,
        "weights_turnaround_penalty": 3600,
    }
    command, _, _ = experiment_case_command(config, case)
    assert command[command.index("--paths.penalty") + 1] == "0.5"
    assert command[command.index("--max-iterations") + 1] == "7"
    assert command[
        command.index("--weights.turnaround-penalty") + 1
    ] == "3600"


def test_audit_demand_coverage_detects_missing_relation(tmp_path: Path) -> None:
    relations = tmp_path / "relations.xml"
    relations.write_text(
        """<data><interval begin="0" end="10">
        <tazRelation from="a" to="b" count="3"/>
        <tazRelation from="c" to="d" count="2"/>
        </interval></data>""",
        encoding="utf-8",
    )
    routes = tmp_path / "routes.xml"
    routes.write_text(
        """<routes><flow fromTaz="a" toTaz="b" number="3">
        <routeDistribution>
        <route probability="1" edges="x y"/>
        <route probability="2" edges="x z"/>
        </routeDistribution></flow></routes>""",
        encoding="utf-8",
    )
    result = audit_demand_coverage(relations, routes)
    assert result["input_od_relation_count"] == 2
    assert result["output_od_flow_count"] == 1
    assert result["missing_od_pairs"] == [["c", "d"]]
    assert result["all_od_relations_routed"] is False
    assert result["flow_demand_matches_input"] is False
    assert result["route_weight_matches_output_flow"] is True
