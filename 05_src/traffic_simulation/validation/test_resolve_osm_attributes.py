from __future__ import annotations

import csv
from dataclasses import replace
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest
import yaml

from traffic_simulation.network import resolve_osm_attributes as resolver


POSITIVE_FIXTURE = (
    resolver.REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/"
    "osm_attribute_resolution_positive.osm.xml"
)
NEGATIVE_FIXTURE = (
    resolver.REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/"
    "osm_attribute_resolution_negative.osm.xml"
)
BIDIRECTIONAL_FIXTURE = (
    resolver.REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/"
    "osm_attribute_resolution_bidirectional.osm.xml"
)
V15_ORACLE = (
    resolver.REPOSITORY_ROOT
    / "05_src/traffic_simulation/validation/fixtures/"
    "permission_expectations_v15.oracle.json"
)


def make_tree(ways: list[str]) -> ElementTree.ElementTree:
    nodes = "".join(
        f'<node id="{index}" lat="35.{index:04d}" lon="139.0000"/>'
        for index in range(1, len(ways) * 2 + 1)
    )
    return ElementTree.ElementTree(
        ElementTree.fromstring(
            f'<osm version="0.6">{nodes}{"".join(ways)}</osm>'
        )
    )


def way_xml(
    way_id: int,
    *,
    highway: str = "residential",
    tags: dict[str, str] | None = None,
) -> str:
    values = {"highway": highway, **(tags or {})}
    encoded = "".join(f'<tag k="{key}" v="{value}"/>' for key, value in values.items())
    first = way_id * 2 - 1
    second = way_id * 2
    return (
        f'<way id="{way_id}"><nd ref="{first}"/><nd ref="{second}"/>'
        f"{encoded}</way>"
    )


def tags_for(tree: ElementTree.ElementTree, way_id: str) -> dict[str, str]:
    way = next(way for way in tree.getroot().findall("way") if way.attrib["id"] == way_id)
    return {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}


def artifact_permissions(payload: dict[str, object]) -> dict[str, object]:
    return {
        way["osm_way_id"]: {
            direction["direction"]: [
                lane["expected_vclasses"] for lane in direction["lanes"]
            ]
            for direction in way["directions"]
        }
        for way in payload["ways"]
    }


def test_load_policy_matches_v15_and_fixture_paths() -> None:
    policy = resolver.load_policy("structural")

    assert policy.config_id == "ota_ward_sumo_network_v15"
    assert policy.config_version == 15
    assert policy.profile == "structural"
    assert policy.typemap_path == (
        "reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml"
    )
    assert policy.typemap_policy_id == "tokyo_motorized_v2"
    assert policy.lane_imputation_minimum_sample_size == 30
    assert policy.lane_imputation_minimum_mode_share == 0.5
    assert policy.speed_imputation_minimum_sample_size == 30
    assert policy.speed_imputation_minimum_mode_share == 0.5
    assert {"residential", "motorway", "busway"} <= policy.retained_highway_types
    assert policy.typemap_permissions["highway.residential"] == policy.governed_vclasses
    assert "moped" not in policy.governed_vclasses
    assert "moped" not in resolver.ACCESS_BASE_KEYS
    assert "moped" not in resolver.ACCESS_CLASS_MAP
    assert POSITIVE_FIXTURE.is_file()
    assert NEGATIVE_FIXTURE.is_file()
    assert BIDIRECTIONAL_FIXTURE.is_file()
    assert V15_ORACLE.is_file()


@pytest.mark.parametrize(
    ("values", "minimum_size", "minimum_share", "expected", "decision"),
    [
        (["2"] * 20, 30, 0.5, None, "insufficient_sample"),
        (["1"] * 15 + ["2"] * 15, 30, 0.5, None, "tied_mode"),
        (["1"] * 12 + ["2"] * 10 + ["3"] * 8, 30, 0.5, None, "insufficient_mode_share"),
        (["2"] * 18 + ["1"] * 12, 30, 0.5, "2", "selected"),
    ],
)
def test_unique_mode_applies_preregistered_rule(
    values: list[str],
    minimum_size: int,
    minimum_share: float,
    expected: str | None,
    decision: str,
) -> None:
    result = resolver.unique_mode(values, minimum_size, minimum_share)

    assert result.value == expected
    assert result.decision == decision


def test_positive_fixture_resolves_expected_permissions_and_preserves_access_tags() -> None:
    policy = resolver.load_policy("structural")
    result = resolver.resolve_tree(ElementTree.parse(POSITIVE_FIXTURE), policy)
    governed = tuple(sorted(policy.governed_vclasses))

    assert result.blockers == ()
    assert result.retained_way_count == 5
    assert result.permission_expectations["100"] == {"forward": (("bus",),)}
    assert result.permission_expectations["200"] == {"forward": (("delivery",),)}
    assert result.permission_expectations["300"] == {
        "forward": ((), governed)
    }
    assert result.permission_expectations["400"] == {
        "forward": ((), governed)
    }
    assert result.permission_expectations["500"] == {
        "forward": (governed,)
    }
    assert tags_for(result.tree, "100")["access"] == "no"
    assert tags_for(result.tree, "100")["bus"] == "yes"


def test_negative_fixture_reports_all_required_attributes_and_does_not_impute_unclassified() -> None:
    policy = resolver.load_policy("structural")
    result = resolver.resolve_tree(ElementTree.parse(NEGATIVE_FIXTURE), policy)
    rows = {row.attribute: row for row in result.audit_rows}

    assert tags_for(result.tree, "600")["oneway"] == "no"
    assert rows["oneway"].source_value == ""
    assert rows["oneway"].adopted_value == "no"
    assert rows["oneway"].value_state == "derived_osm_rule"
    assert (
        rows["oneway"].derivation_method
        == "ordinary_road_derived_bidirectional_osm_rule"
    )
    assert rows["lanes"].value_state == "missing"
    assert rows["maxspeed"].value_state == "missing"
    assert rows["lanes"].stop_category == "structural_confirmation_rule"
    assert rows["maxspeed"].stop_category == "structural_confirmation_rule"
    assert rows["permissions"].decision == "blocked_by_prerequisite"
    assert rows["permissions"].stop_category == ""
    assert len(result.blockers) == 2
    assert "lanes" in result.blockers[0]
    assert "maxspeed" in result.blockers[1]


def test_stop_categories_are_exclusive_and_non_stops_have_none() -> None:
    policy = resolver.load_policy("formal")
    tags = {"highway": "residential"}
    rows = [
        resolver._audit(
            way_id="1",
            tags=tags,
            attribute="lanes",
            source_value="",
            adopted_value="",
            value_state="missing",
            policy=policy,
            derivation_method="no_admissible_lane_value",
            criticality="unclassified",
            decision="stop",
        ),
        resolver._audit(
            way_id="2",
            tags=tags,
            attribute="lanes",
            source_value="bad",
            adopted_value="",
            value_state="invalid",
            policy=policy,
            derivation_method="invalid_explicit_lane_value",
            criticality="unclassified",
            decision="stop",
        ),
        resolver._audit(
            way_id="3",
            tags=tags,
            attribute="lanes",
            source_value="",
            adopted_value="",
            value_state="governed_precondition_not_met",
            policy=policy,
            derivation_method="normal_precondition_gate",
            criticality="unclassified",
            decision="stop",
        ),
        resolver._audit(
            way_id="4",
            tags=tags,
            attribute="lanes",
            source_value="2",
            adopted_value="2",
            value_state="explicit_osm",
            policy=policy,
            derivation_method="explicit_osm_lanes",
            criticality="unclassified",
            decision="adopted",
        ),
    ]
    assert [row.stop_category for row in rows] == [
        "additional_evidence_requirement",
        "exception_rule",
        "normal_rule",
        "",
    ]
    assert all(row.stop_category_rule_id for row in rows[:3])
    assert rows[3].stop_category_rule_id == ""


def test_reverse_oneway_stops_without_mutating_direction_dependent_semantics() -> None:
    tree = make_tree(
        [
            way_xml(
                1,
                tags={
                    "lanes": "1",
                    "maxspeed": "30",
                    "oneway": "-1",
                    "access:forward": "no",
                    "access:backward": "yes",
                },
            )
        ]
    )
    policy = resolver.load_policy("structural")
    way = tree.getroot().find("way")
    assert way is not None
    original_nodes = [node.attrib["ref"] for node in way.findall("nd")]

    result = resolver.resolve_tree(tree, policy)
    normalized_way = result.tree.getroot().find("way")
    assert normalized_way is not None

    assert result.blockers == ("way 1 oneway: valid_but_unsupported",)
    assert [node.attrib["ref"] for node in normalized_way.findall("nd")] == original_nodes
    normalized_tags = tags_for(result.tree, "1")
    assert normalized_tags["oneway"] == "-1"
    assert normalized_tags["access:forward"] == "no"
    assert normalized_tags["access:backward"] == "yes"
    reverse_row = next(
        row for row in result.audit_rows if row.attribute == "oneway"
    )
    assert reverse_row.source_value == "-1"
    assert reverse_row.adopted_value == ""
    assert reverse_row.value_state == "valid_but_unsupported"
    assert reverse_row.decision == "stop"
    assert result.permission_expectations == {}


def test_implied_oneway_rules_distinguish_motorway_and_motorway_link() -> None:
    tree = make_tree(
        [
            way_xml(1, highway="motorway", tags={"lanes": "2", "maxspeed": "80"}),
            way_xml(2, highway="motorway_link", tags={"lanes": "1", "maxspeed": "40"}),
            way_xml(3, tags={"lanes": "2", "maxspeed": "30"}),
        ]
    )
    result = resolver.resolve_tree(tree, resolver.load_policy("formal"))
    oneway_rows = {
        row.osm_way_id: row
        for row in result.audit_rows
        if row.attribute == "oneway"
    }

    assert tags_for(result.tree, "1")["oneway"] == "yes"
    assert oneway_rows["1"].derivation_method == "implied_motorway_oneway"
    assert oneway_rows["2"].value_state == "unresolved"
    assert "oneway" not in tags_for(result.tree, "2")
    assert tags_for(result.tree, "3")["oneway"] == "no"
    assert any("way 2 oneway" in blocker for blocker in result.blockers)


def test_structural_imputation_uses_local_mode_only_for_explicit_noncritical_way() -> None:
    observed = [
        way_xml(
            index,
            tags={"lanes": "2", "maxspeed": "30", "oneway": "no"},
        )
        for index in range(1, 31)
    ]
    observed.append(way_xml(31, tags={"oneway": "no"}))
    tree = make_tree(observed)
    criticality = {str(index): "noncritical" for index in range(1, 32)}

    result = resolver.resolve_tree(
        tree,
        resolver.load_policy("structural"),
        criticality_by_way=criticality,
    )
    imputed_rows = {
        row.attribute: row
        for row in result.audit_rows
        if row.osm_way_id == "31" and row.attribute in {"lanes", "maxspeed"}
    }

    assert result.blockers == ()
    assert tags_for(result.tree, "31")["lanes"] == "2"
    assert tags_for(result.tree, "31")["maxspeed"] == "30"
    assert imputed_rows["lanes"].value_state == "structural_placeholder"
    assert imputed_rows["maxspeed"].value_state == "structural_placeholder"
    assert "n=30" in imputed_rows["lanes"].derivation_method


def test_formal_profile_never_uses_structural_imputation() -> None:
    observed = [
        way_xml(
            index,
            tags={"lanes": "2", "maxspeed": "30", "oneway": "no"},
        )
        for index in range(1, 31)
    ]
    observed.append(way_xml(31, tags={"oneway": "no"}))

    result = resolver.resolve_tree(
        make_tree(observed),
        resolver.load_policy("formal"),
        criticality_by_way={"31": "noncritical"},
    )

    assert any("way 31 lanes" in blocker for blocker in result.blockers)
    assert any("way 31 maxspeed" in blocker for blocker in result.blockers)


@pytest.mark.parametrize(
    "tags",
    [
        {"lanes": "1", "maxspeed": "30", "oneway": "yes", "access": "destination"},
        {"lanes": "1", "maxspeed": "30", "oneway": "yes", "access": "private"},
        {"lanes": "1", "maxspeed": "30", "oneway": "yes", "psv": "yes"},
        {"lanes": "2", "maxspeed": "30", "oneway": "no", "access:lanes": "no|yes"},
        {"lanes": "2", "maxspeed": "30", "oneway": "yes", "access:lanes": "yes"},
    ],
)
def test_unsupported_or_ambiguous_access_is_unresolved(tags: dict[str, str]) -> None:
    result = resolver.resolve_tree(
        make_tree([way_xml(1, tags=tags)]), resolver.load_policy("formal")
    )

    permission_rows = [
        row for row in result.audit_rows if row.attribute == "permissions"
    ]
    assert len(permission_rows) == 1
    assert permission_rows[0].value_state == "unresolved"
    assert any("permissions" in blocker for blocker in result.blockers)


def test_directional_lane_total_conflict_and_conditional_speed_stop() -> None:
    result = resolver.resolve_tree(
        make_tree(
            [
                way_xml(
                    1,
                    tags={
                        "lanes": "3",
                        "lanes:forward": "1",
                        "lanes:backward": "1",
                        "maxspeed": "30",
                        "maxspeed:conditional": "20 @ (school_hours)",
                        "oneway": "no",
                    },
                )
            ]
        ),
        resolver.load_policy("formal"),
    )
    rows = {row.attribute: row for row in result.audit_rows}

    assert rows["lanes"].value_state == "conflict"
    assert rows["maxspeed"].value_state == "conditional"
    assert len(result.blockers) == 2


@pytest.mark.parametrize(
    "way",
    [
        '<way><nd ref="1"/><nd ref="2"/><tag k="highway" v="residential"/></way>',
        (
            '<way id="1"><nd ref="1"/><nd ref="2"/>'
            '<tag k="highway" v="residential"/>'
            '<tag k="lanes" v="1"/><tag k="lanes" v="2"/></way>'
        ),
    ],
)
def test_invalid_way_identity_or_duplicate_tags_are_rejected(way: str) -> None:
    tree = make_tree([way])

    with pytest.raises(resolver.ResolutionError):
        resolver.resolve_tree(tree, resolver.load_policy("formal"))


def test_empty_governed_scope_is_rejected() -> None:
    tree = make_tree([way_xml(1, highway="footway")])

    with pytest.raises(resolver.ResolutionError, match="no governed motorized ways"):
        resolver.resolve_tree(tree, resolver.load_policy("formal"))


def test_even_bidirectional_lane_total_is_split_only_for_structural_profile() -> None:
    formal = resolver.resolve_tree(
        make_tree(
            [way_xml(1, tags={"lanes": "4", "maxspeed": "40", "oneway": "no"})]
        ),
        resolver.load_policy("formal"),
    )
    structural = resolver.resolve_tree(
        make_tree(
            [way_xml(1, tags={"lanes": "4", "maxspeed": "40", "oneway": "no"})]
        ),
        resolver.load_policy("structural"),
    )

    assert formal.permission_expectations == {}
    assert formal.blockers == (
        "way 1 permissions: bidirectional lane allocation is unresolved",
    )
    assert structural.blockers == ()
    assert len(structural.permission_expectations["1"]["forward"]) == 2
    assert len(structural.permission_expectations["1"]["backward"]) == 2


def test_formal_implicit_bidirectional_split_writes_rs008_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = resolver.load_policy("formal")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    input_path = tmp_path / "input.osm.xml"
    input_path.write_text(
        ElementTree.tostring(
            make_tree(
                [
                    way_xml(
                        1,
                        tags={"lanes": "4", "maxspeed": "40", "oneway": "no"},
                    )
                ]
            ).getroot(),
            encoding="unicode",
        ),
        encoding="utf-8",
    )
    permissions_path = tmp_path / "permissions.json"

    with pytest.raises(resolver.ResolutionError, match="materialization gate failed"):
        resolver.resolve_file(
            input_path,
            tmp_path / "normalized.xml",
            tmp_path / "audit.csv",
            permissions_path,
            tmp_path / "imputation.json",
            policy,
        )

    payload = json.loads(permissions_path.read_text(encoding="utf-8"))
    assert payload["complete"] is False
    assert [blocker["code"] for blocker in payload["blockers"]] == ["RS008"]


def test_resolve_file_writes_audit_but_not_xml_when_gate_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = resolver.load_policy("formal")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    input_path = tmp_path / "input.osm.xml"
    output_path = tmp_path / "normalized.osm.xml"
    audit_path = tmp_path / "audit.csv"
    permissions_path = tmp_path / "permissions.json"
    summary_path = tmp_path / "imputation.json"
    input_path.write_bytes(NEGATIVE_FIXTURE.read_bytes())
    output_path.write_text("stale successful output", encoding="utf-8")

    with pytest.raises(resolver.ResolutionError, match="materialization gate failed"):
        resolver.resolve_file(
            input_path,
            output_path,
            audit_path,
            permissions_path,
            summary_path,
            policy,
            overwrite=True,
        )

    assert audit_path.is_file()
    assert permissions_path.is_file()
    assert summary_path.is_file()
    assert not output_path.exists()
    permissions = json.loads(permissions_path.read_text())
    oracle = json.loads(V15_ORACLE.read_text())
    resolver.validate_permission_expectations_payload(permissions)
    assert permissions["artifact_type"] == "permission_expectations"
    assert permissions["schema_version"] == 2
    assert permissions["complete"] is oracle["negative"]["complete"]
    assert [item["code"] for item in permissions["blockers"]] == oracle["negative"][
        "blocker_codes"
    ]
    assert len(permissions["ways"]) == oracle["negative"]["way_count"]
    assert "normalized_osm" not in permissions
    with audit_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["attribute"] for row in rows} == {
        "oneway",
        "lanes",
        "maxspeed",
        "permissions",
    }
    stopping_rows = [row for row in rows if row["decision"] == "stop"]
    assert {row["stop_category"] for row in stopping_rows} == {
        "additional_evidence_requirement"
    }
    assert all(row["stop_category_rule_id"] for row in stopping_rows)


def test_resolve_file_writes_normalized_xml_and_complete_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = resolver.load_policy("structural")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    input_path = tmp_path / "input.osm.xml"
    output_path = tmp_path / "normalized.osm.xml"
    audit_path = tmp_path / "audit.csv"
    permissions_path = tmp_path / "permissions.json"
    summary_path = tmp_path / "imputation.json"
    input_path.write_bytes(POSITIVE_FIXTURE.read_bytes())

    result = resolver.resolve_file(
        input_path,
        output_path,
        audit_path,
        permissions_path,
        summary_path,
        policy,
    )

    assert result.blockers == ()
    assert output_path.is_file()
    assert audit_path.is_file()
    assert permissions_path.is_file()
    assert summary_path.is_file()
    normalized = ElementTree.parse(output_path)
    assert tags_for(normalized, "100")["access"] == "no"
    permissions = json.loads(permissions_path.read_text())
    oracle = json.loads(V15_ORACLE.read_text())
    resolver.validate_permission_expectations_payload(permissions)
    assert permissions["complete"] is True
    assert permissions["blockers"] == []
    assert permissions["config_id"] == oracle["config_id"]
    assert permissions["config_version"] == oracle["config_version"]
    assert permissions["artifact_type"] == oracle["artifact_type"]
    assert permissions["schema_version"] == oracle["schema_version"]
    assert permissions["typemap"] == oracle["typemap"]
    assert permissions["governed_vclasses"] == oracle["governed_vclasses"]
    assert permissions["input_osm"]["sha256"] == oracle["positive_input_sha256"]
    assert permissions["normalized_osm"]["sha256"] == resolver.sha256_file(output_path)
    assert artifact_permissions(permissions) == oracle["positive_permissions"]
    for way in permissions["ways"]:
        actual_source_tags = sorted(
            trace["source_tag"]
            for trace in way["directions"][0]["lanes"][0]["rule_trace"]
            if "source_tag" in trace
        )
        assert actual_source_tags == oracle["source_access_tags"][
            way["osm_way_id"]
        ]
    assert "permission_expectations" not in permissions
    summary = json.loads(summary_path.read_text())
    assert summary["sample_unit"] == "osm_way_count"
    assert summary["input_osm_sha256"] == resolver.sha256_file(input_path)


def test_v15_artifact_preserves_forward_and_backward_osm_lane_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = resolver.load_policy("formal")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    input_path = tmp_path / "bidirectional.osm.xml"
    output_path = tmp_path / "normalized.osm.xml"
    audit_path = tmp_path / "audit.csv"
    permissions_path = tmp_path / "permissions.json"
    summary_path = tmp_path / "imputation.json"
    input_path.write_bytes(BIDIRECTIONAL_FIXTURE.read_bytes())

    resolver.resolve_file(
        input_path,
        output_path,
        audit_path,
        permissions_path,
        summary_path,
        policy,
    )

    permissions = json.loads(permissions_path.read_text())
    oracle = json.loads(V15_ORACLE.read_text())
    assert artifact_permissions(permissions) == oracle["bidirectional_permissions"]
    way = permissions["ways"][0]
    assert [direction["direction"] for direction in way["directions"]] == [
        "forward",
        "backward",
    ]
    assert [
        lane["osm_lane_position"]
        for direction in way["directions"]
        for lane in direction["lanes"]
    ] == [0, 1, 0, 1]
    forward_tags = {
        trace["source_tag"]
        for lane in way["directions"][0]["lanes"]
        for trace in lane["rule_trace"]
        if "source_tag" in trace
    }
    backward_tags = {
        trace["source_tag"]
        for lane in way["directions"][1]["lanes"]
        for trace in lane["rule_trace"]
        if "source_tag" in trace
    }
    assert forward_tags == {"access:lanes:forward"}
    assert backward_tags == {"access:lanes:backward"}
    assert [
        lane["rule_trace"][-1]["lane_value"]
        for lane in way["directions"][0]["lanes"]
    ] == ["yes", "no"]
    assert [
        lane["rule_trace"][-1]["lane_value"]
        for lane in way["directions"][1]["lanes"]
    ] == ["no", "yes"]


def test_v13_map_only_permission_artifact_is_rejected_by_v15_schema() -> None:
    with pytest.raises(resolver.ResolutionError, match="schema validation failed"):
        resolver.validate_permission_expectations_payload(
            {
                "config_id": "ota_ward_sumo_network_v15",
                "complete": True,
                "permission_expectations": {"1": {"forward": [["delivery"]]}},
            }
        )


def test_v15_artifact_failure_rolls_back_the_whole_previous_output_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = resolver.load_policy("structural")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    input_path = tmp_path / "input.osm.xml"
    output_path = tmp_path / "normalized.osm.xml"
    audit_path = tmp_path / "audit.csv"
    permissions_path = tmp_path / "permissions.json"
    summary_path = tmp_path / "imputation.json"
    input_path.write_bytes(POSITIVE_FIXTURE.read_bytes())
    for path in (output_path, audit_path, permissions_path, summary_path):
        path.write_text(f"old:{path.name}", encoding="utf-8")

    def fail_artifact(*args: object, **kwargs: object) -> dict[str, object]:
        raise resolver.ResolutionError("forced v15 artifact failure")

    monkeypatch.setattr(resolver, "build_permission_expectations_payload", fail_artifact)

    with pytest.raises(resolver.ResolutionError, match="forced v15 artifact failure"):
        resolver.resolve_file(
            input_path,
            output_path,
            audit_path,
            permissions_path,
            summary_path,
            policy,
            overwrite=True,
        )

    for path in (output_path, audit_path, permissions_path, summary_path):
        assert path.read_text(encoding="utf-8") == f"old:{path.name}"


def test_policy_threshold_change_can_be_injected_without_changing_resolution_code() -> None:
    policy = replace(
        resolver.load_policy("structural"),
        lane_imputation_minimum_sample_size=2,
        lane_imputation_minimum_mode_share=0.5,
        speed_imputation_minimum_sample_size=2,
        speed_imputation_minimum_mode_share=0.5,
    )
    tree = make_tree(
        [
            way_xml(1, tags={"lanes": "1", "maxspeed": "20", "oneway": "yes"}),
            way_xml(2, tags={"lanes": "1", "maxspeed": "20", "oneway": "yes"}),
            way_xml(3, tags={"oneway": "yes"}),
        ]
    )

    result = resolver.resolve_tree(
        tree, policy, criticality_by_way={"3": "noncritical"}
    )

    assert result.blockers == ()
    assert tags_for(result.tree, "3")["lanes"] == "1"
    assert tags_for(result.tree, "3")["maxspeed"] == "20"


def test_excluded_highway_ways_are_physically_removed_from_output_tree() -> None:
    result = resolver.resolve_tree(
        make_tree(
            [
                way_xml(1, tags={"lanes": "1", "maxspeed": "30", "oneway": "yes"}),
                way_xml(2, highway="footway"),
            ]
        ),
        resolver.load_policy("formal"),
    )

    output_highways = {
        tags_for(result.tree, way.attrib["id"])["highway"]
        for way in result.tree.getroot().findall("way")
        if "highway" in tags_for(result.tree, way.attrib["id"])
    }
    assert output_highways == {"residential"}
    assert result.excluded_way_count == 1


@pytest.mark.parametrize(
    ("attribute_tags", "attribute", "state"),
    [
        ({"lanes": "1.5"}, "lanes", "invalid"),
        ({"maxspeed": "50 mph"}, "maxspeed", "valid_but_unsupported"),
        (
            {"maxspeed:forward": "30", "maxspeed:backward": "40"},
            "maxspeed",
            "directionally_asymmetric",
        ),
    ],
)
def test_explicit_unsupported_values_are_never_structurally_imputed(
    attribute_tags: dict[str, str], attribute: str, state: str
) -> None:
    observed = [
        way_xml(
            index,
            tags={"lanes": "2", "maxspeed": "30", "oneway": "no"},
        )
        for index in range(1, 31)
    ]
    observed.append(
        way_xml(
            31,
            tags={
                "lanes": "2",
                "maxspeed": "30",
                "oneway": "no",
                **attribute_tags,
            },
        )
    )
    result = resolver.resolve_tree(
        make_tree(observed),
        resolver.load_policy("structural"),
        criticality_by_way={"31": "noncritical"},
    )
    row = next(
        row
        for row in result.audit_rows
        if row.osm_way_id == "31" and row.attribute == attribute
    )

    assert row.value_state == state
    assert row.decision == "stop"


def test_bidirectional_single_lane_is_not_duplicated_by_direction() -> None:
    result = resolver.resolve_tree(
        make_tree(
            [way_xml(1, tags={"lanes": "1", "maxspeed": "30", "oneway": "no"})]
        ),
        resolver.load_policy("formal"),
    )

    assert result.permission_expectations == {}
    assert any("bidirectional lane allocation is unresolved" in blocker for blocker in result.blockers)


def test_access_designated_is_validated_with_its_key() -> None:
    general = resolver.resolve_tree(
        make_tree(
            [way_xml(1, tags={"lanes": "1", "maxspeed": "30", "oneway": "yes", "access": "designated"})]
        ),
        resolver.load_policy("formal"),
    )
    bus = resolver.resolve_tree(
        make_tree(
            [way_xml(1, tags={"lanes": "1", "maxspeed": "30", "oneway": "yes", "access": "no", "bus": "designated"})]
        ),
        resolver.load_policy("formal"),
    )

    assert any("unsupported access value access=designated" in blocker for blocker in general.blockers)
    assert bus.permission_expectations["1"] == {"forward": (("bus",),)}


def test_imputation_donors_exclude_reverse_oneway_and_conflicting_speed() -> None:
    policy = replace(
        resolver.load_policy("structural"),
        lane_imputation_minimum_sample_size=1,
        speed_imputation_minimum_sample_size=1,
    )
    result = resolver.resolve_tree(
        make_tree(
            [
                way_xml(
                    1,
                    tags={"lanes": "2", "maxspeed": "30", "oneway": "-1"},
                ),
                way_xml(
                    2,
                    tags={
                        "lanes": "2",
                        "maxspeed": "40",
                        "maxspeed:forward": "30",
                        "maxspeed:backward": "50",
                        "oneway": "no",
                    },
                ),
                way_xml(3, tags={"oneway": "yes"}),
            ]
        ),
        policy,
        criticality_by_way={"3": "noncritical"},
    )

    assert result.imputation_summary["lanes"] == {}
    assert result.imputation_summary["maxspeed"] == {}
    assert any("way 3 lanes" in blocker for blocker in result.blockers)
    assert any("way 3 maxspeed" in blocker for blocker in result.blockers)


@pytest.mark.parametrize("service", ["bus", "psv"])
def test_compound_service_types_are_retained_by_exact_sumo_type(service: str) -> None:
    result = resolver.resolve_tree(
        make_tree(
            [
                way_xml(
                    1,
                    highway="service",
                    tags={
                        "service": service,
                        "lanes": "1",
                        "maxspeed": "30",
                        "oneway": "yes",
                    },
                )
            ]
        ),
        resolver.load_policy("formal"),
    )

    assert result.blockers == ()
    assert result.retained_way_count == 1
    assert result.excluded_way_count == 0
    assert result.permission_expectations["1"]["forward"] == (
        ("bus", "delivery"),
    )


@pytest.mark.parametrize(
    "malformed_way",
    [
        '<way id="1"><nd ref="1"/><nd ref="2"/><tag v="residential"/></way>',
        '<way id="1"><nd ref="1"/><nd ref="2"/><tag k="highway"/></way>',
        '<way id="1"><nd ref="1"/><nd ref="2"/><tag k="" v="residential"/></way>',
        '<way id="1"><nd ref="1"/><nd ref="999"/><tag k="highway" v="residential"/></way>',
    ],
)
def test_malformed_tags_and_node_references_are_rejected(
    malformed_way: str,
) -> None:
    with pytest.raises(resolver.ResolutionError):
        resolver.resolve_tree(
            make_tree([malformed_way]), resolver.load_policy("formal")
        )


def test_relation_referencing_an_excluded_way_is_removed() -> None:
    tree = make_tree(
        [
            way_xml(1, tags={"lanes": "1", "maxspeed": "30", "oneway": "yes"}),
            way_xml(2, highway="footway"),
        ]
    )
    tree.getroot().append(
        ElementTree.fromstring(
            '<relation id="10"><member type="way" ref="1" role="from"/>'
            '<member type="way" ref="2" role="to"/>'
            '<tag k="type" v="restriction"/></relation>'
        )
    )

    result = resolver.resolve_tree(tree, resolver.load_policy("formal"))

    assert result.tree.getroot().find("relation") is None


def test_non_road_relation_is_removed_before_missing_reference_validation() -> None:
    tree = make_tree(
        [way_xml(1, tags={"lanes": "1", "maxspeed": "30", "oneway": "yes"})]
    )
    tree.getroot().append(
        ElementTree.fromstring(
            '<relation id="10"><member type="way" ref="999" role="outer"/>'
            '<tag k="type" v="multipolygon"/>'
            '<tag k="natural" v="water"/></relation>'
        )
    )

    result = resolver.resolve_tree(tree, resolver.load_policy("formal"))

    assert result.excluded_relation_count == 1
    assert result.tree.getroot().find("relation") is None


def test_turn_restriction_with_missing_way_reference_stops() -> None:
    tree = make_tree(
        [way_xml(1, tags={"lanes": "1", "maxspeed": "30", "oneway": "yes"})]
    )
    tree.getroot().append(
        ElementTree.fromstring(
            '<relation id="10"><member type="way" ref="1" role="from"/>'
            '<member type="way" ref="999" role="to"/>'
            '<tag k="type" v="restriction"/></relation>'
        )
    )

    with pytest.raises(
        resolver.ResolutionError,
        match="relation 10 has an unresolved way reference",
    ):
        resolver.resolve_tree(tree, resolver.load_policy("formal"))


def test_typemap_disallow_is_rejected_in_allow_only_v15_contract(
    tmp_path: Path,
) -> None:
    typemap = tmp_path / "typemap.xml"
    typemap.write_text(
        '<types><type id="highway.residential" disallow="truck"/></types>',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported disallow"):
        resolver._load_typemap_permissions(
            typemap, frozenset({"passenger", "truck"})
        )


@pytest.mark.parametrize(
    ("source", "expected"),
    [("40", "40"), ("40.0", "40"), ("40.50", "40.5")],
)
def test_maxspeed_numeric_strings_are_canonicalized(
    source: str, expected: str
) -> None:
    assert resolver._simple_maxspeed(source) == expected


def test_criticality_map_requires_source_and_exact_retained_way_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = resolver.load_policy("formal")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    input_path = tmp_path / "input.osm.xml"
    input_path.write_bytes(POSITIVE_FIXTURE.read_bytes())
    artifacts = [tmp_path / name for name in ("out.xml", "audit.csv", "p.json", "i.json")]

    with pytest.raises(ValueError, match="hashable source"):
        resolver.resolve_file(
            input_path,
            *artifacts,
            policy,
            criticality_by_way={"100": "critical"},
        )

    criticality_path = tmp_path / "criticality.csv"
    criticality_path.write_text(
        "osm_way_id,criticality\n100,critical\n999,noncritical\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="coverage differs"):
        resolver.resolve_file(
            input_path,
            *artifacts,
            policy,
            criticality_by_way={"100": "critical", "999": "noncritical"},
            criticality_source_path=criticality_path,
        )


def test_json_writer_removes_part_file_after_serialization_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_dump(*args: object, **kwargs: object) -> None:
        raise TypeError("forced serialization failure")

    monkeypatch.setattr(resolver.json, "dump", fail_dump)
    output = tmp_path / "artifact.json"
    with pytest.raises(TypeError, match="forced serialization failure"):
        resolver._write_json({"value": "x"}, output)

    assert not output.exists()
    assert list(tmp_path.glob("*.part")) == []


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("minimum_sample_size", 0, "at least 1"),
        ("minimum_mode_share", 0, "must be in"),
        ("minimum_mode_share", 1.1, "must be in"),
    ],
)
def test_policy_rejects_invalid_imputation_thresholds(
    tmp_path: Path, field: str, value: float, message: str
) -> None:
    config = yaml.safe_load(resolver.CONFIG_PATH.read_text(encoding="utf-8"))
    config["structural_imputation"]["lanes"][field] = value
    path = tmp_path / "sumo_network.yml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        resolver.load_policy("structural", path)


def test_publication_failure_restores_every_previous_artifact(tmp_path: Path) -> None:
    destination_a = tmp_path / "a.txt"
    destination_b = tmp_path / "b.txt"
    destination_a.write_text("old-a", encoding="utf-8")
    destination_b.write_text("old-b", encoding="utf-8")
    staging = tmp_path / "stage"
    staging.mkdir()
    staged_a = staging / "new-a.txt"
    staged_a.write_text("new-a", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        resolver._publish_artifact_set(
            {
                destination_a: staged_a,
                destination_b: staging / "missing.txt",
            },
            (),
            overwrite=True,
            transaction_directory=staging,
        )

    assert destination_a.read_text(encoding="utf-8") == "old-a"
    assert destination_b.read_text(encoding="utf-8") == "old-b"


def test_cli_writes_schema_valid_failure_report_with_stable_blockers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    policy = resolver.load_policy("structural")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(resolver, "load_policy", lambda profile: policy)
    input_path = tmp_path / "input.osm.xml"
    input_path.write_bytes(NEGATIVE_FIXTURE.read_bytes())
    output_path = tmp_path / "normalized.osm.xml"
    audit_path = tmp_path / "audit.csv"
    permissions_path = tmp_path / "permissions.json"
    summary_path = tmp_path / "imputation.json"
    failure_path = tmp_path / "failure.json"

    exit_code = resolver.main(
        [
            "--profile",
            "structural",
            "--input-osm",
            str(input_path),
            "--output-osm",
            str(output_path),
            "--audit-csv",
            str(audit_path),
            "--permission-expectations-json",
            str(permissions_path),
            "--imputation-summary-json",
            str(summary_path),
            "--failure-report-json",
            str(failure_path),
        ]
    )

    report = json.loads(failure_path.read_text(encoding="utf-8"))
    resolver._validate_failure_report(report)
    assert exit_code == 2
    assert [failure["code"] for failure in report["failures"]] == [
        "RS003",
        "RS003",
    ]
    assert report["partial_outputs_published"] is False
    assert len(report["retained_artifacts"]) == 3
    assert "RS003" in capsys.readouterr().err


def test_cli_classifies_malformed_xml_as_rs001(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = resolver.load_policy("formal")
    monkeypatch.setattr(resolver, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(resolver, "load_policy", lambda profile: policy)
    input_path = tmp_path / "malformed.osm.xml"
    input_path.write_text("<osm><way>", encoding="utf-8")
    failure_path = tmp_path / "failure.json"

    exit_code = resolver.main(
        [
            "--profile",
            "formal",
            "--input-osm",
            str(input_path),
            "--output-osm",
            str(tmp_path / "normalized.osm.xml"),
            "--audit-csv",
            str(tmp_path / "audit.csv"),
            "--permission-expectations-json",
            str(tmp_path / "permissions.json"),
            "--imputation-summary-json",
            str(tmp_path / "imputation.json"),
            "--failure-report-json",
            str(failure_path),
        ]
    )

    report = json.loads(failure_path.read_text(encoding="utf-8"))
    assert exit_code == 2
    assert report["failures"][0]["code"] == "RS001"
