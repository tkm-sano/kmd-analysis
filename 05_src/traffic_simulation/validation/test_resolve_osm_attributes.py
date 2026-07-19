from __future__ import annotations

import csv
from dataclasses import replace
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

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


def test_load_policy_matches_v12_and_fixture_paths() -> None:
    policy = resolver.load_policy("structural")

    assert policy.config_id == "ota_ward_sumo_network_v12"
    assert policy.config_version == 12
    assert policy.profile == "structural"
    assert policy.lane_imputation_minimum_sample_size == 30
    assert policy.lane_imputation_minimum_mode_share == 0.5
    assert policy.speed_imputation_minimum_sample_size == 30
    assert policy.speed_imputation_minimum_mode_share == 0.5
    assert {"residential", "motorway", "busway"} <= policy.retained_highway_types
    assert policy.typemap_permissions["highway.residential"] == policy.governed_vclasses
    assert POSITIVE_FIXTURE.is_file()
    assert NEGATIVE_FIXTURE.is_file()


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
    assert rows["oneway"].value_state == "derived_osm_rule"
    assert rows["lanes"].value_state == "missing"
    assert rows["maxspeed"].value_state == "missing"
    assert len(result.blockers) == 2
    assert "lanes" in result.blockers[0]
    assert "maxspeed" in result.blockers[1]


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


def test_even_bidirectional_lane_total_is_split_for_permission_expectations() -> None:
    result = resolver.resolve_tree(
        make_tree(
            [way_xml(1, tags={"lanes": "4", "maxspeed": "40", "oneway": "no"})]
        ),
        resolver.load_policy("formal"),
    )

    assert result.blockers == ()
    assert len(result.permission_expectations["1"]["forward"]) == 2
    assert len(result.permission_expectations["1"]["backward"]) == 2


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
    with audit_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["attribute"] for row in rows} == {"oneway", "lanes", "maxspeed"}


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
    assert json.loads(permissions_path.read_text())["complete"] is True
    summary = json.loads(summary_path.read_text())
    assert summary["sample_unit"] == "osm_way_count"
    assert summary["input_osm_sha256"] == resolver.sha256_file(input_path)


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
