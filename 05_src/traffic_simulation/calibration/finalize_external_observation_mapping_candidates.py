"""Classify the ten external Road Census observation mapping references."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pyproj import CRS, Transformer
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

from traffic_simulation.calibration import road_census_sumo_pipeline as pipeline
from traffic_simulation.paths import REPOSITORY_ROOT


DEFAULT_DATA_DIR = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
)
DEFAULT_REPORT = REPOSITORY_ROOT / "05_src/traffic_simulation/external_observation_mapping_candidate_review.md"
STATUS_ORDER = ("AUTO_ACCEPT", "REVIEW_REQUIRED", "NETWORK_EXTENSION_REQUIRED", "UNRESOLVED")


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _edge_orig_ids(net_path: Path, selected: set[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for _, edge in ET.iterparse(net_path, events=("end",)):
        if edge.tag != "edge":
            continue
        edge_id = edge.get("id", "")
        if edge_id in selected:
            result[edge_id] = sorted({
                source
                for lane in edge.findall("lane")
                for param in lane.findall("param")
                if param.get("key") == "origId"
                for source in param.get("value", "").split()
                if source
            })
        edge.clear()
    missing = selected - set(result)
    if missing:
        raise ValueError(f"selected SUMO edges missing from network: {sorted(missing)}")
    return result


def _way_and_relation_evidence(
    osm_path: Path, relation_path: Path, way_ids: set[str]
) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    tags: dict[str, dict[str, str]] = {}
    for _, element in ET.iterparse(osm_path, events=("end",)):
        if element.tag == "way" and element.get("id", "") in way_ids:
            tags[element.get("id", "")] = {
                tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")
            }
        if element.tag in {"node", "way", "relation"}:
            element.clear()
    memberships: dict[str, list[dict[str, str]]] = defaultdict(list)
    for _, element in ET.iterparse(relation_path, events=("end",)):
        if element.tag == "relation":
            relation_tags = {tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")}
            if relation_tags.get("type") == "route" and relation_tags.get("route") == "road":
                record = {
                    "relation_id": element.get("id", ""),
                    "network": relation_tags.get("network", ""),
                    "ref": relation_tags.get("ref", ""),
                    "operator": relation_tags.get("operator", ""),
                    "name": relation_tags.get("name", ""),
                }
                for member in element.findall("member"):
                    way_id = member.get("ref", "")
                    if member.get("type") == "way" and way_id in way_ids:
                        memberships[way_id].append(record)
        if element.tag in {"node", "way", "relation"}:
            element.clear()
    return tags, memberships


def _connection_violations(edge_ids: list[str], edge_by_id: dict[str, dict[str, Any]]) -> int:
    return sum(
        right not in edge_by_id[left]["_successor_edge_ids"]
        or edge_by_id[left]["to_node"] != edge_by_id[right]["from_node"]
        for left, right in zip(edge_ids, edge_ids[1:])
    )


def _bbox(geometry: Any) -> dict[str, float]:
    west, south, east, north = geometry.bounds
    return {
        "west": round(west, 9), "south": round(south, 9),
        "east": round(east, 9), "north": round(north, 9),
    }


def _minimum_extension(
    geometry: Any,
    candidates: list[dict[str, Any]],
    buffer_m: float,
    net_root: ET.Element,
    offset_x: float,
    offset_y: float,
) -> dict[str, Any]:
    covered = unary_union([row["edge"]["geometry"] for row in candidates]).buffer(buffer_m)
    uncovered = geometry.difference(covered)
    search_extent = uncovered.buffer(buffer_m)
    location = net_root.find("location")
    if location is None:
        raise ValueError("SUMO network location metadata is missing")
    inverse = Transformer.from_crs(CRS.from_proj4(location.get("projParameter")), 4326, always_xy=True)

    def to_wgs84(value: Any) -> Any:
        return transform(lambda x, y, z=None: inverse.transform(x - offset_x, y - offset_y), value)

    return {
        "official_geometry_length_m": round(geometry.length, 3),
        "covered_length_m": round(geometry.length - uncovered.length, 3),
        "uncovered_length_m": round(uncovered.length, 3),
        "uncovered_ratio": round(uncovered.length / geometry.length, 6),
        "uncovered_geometry_bbox_wgs84": _bbox(to_wgs84(uncovered)),
        "minimum_25m_search_bbox_wgs84": _bbox(to_wgs84(search_extent)),
        "scope_note": (
            "Minimum spatial search extent around the uncovered official geometry. "
            "The network build must additionally include connecting nodes and applicable restriction relations."
        ),
    }


def build_review(data_dir: Path = DEFAULT_DATA_DIR) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    config = pipeline.load_config()
    inputs = config["inputs"]
    census_dir = REPOSITORY_ROOT / inputs["road_census_dir"]
    audit_path = data_dir / "traffic_comparison_data_availability_review.csv"
    audit = read_csv(audit_path)
    references = [row for row in audit if row["primary_availability_cause"] == "PROCESSING_OMISSION"]
    if len(references) != 10:
        raise ValueError(f"expected 10 processing omissions, got {len(references)}")
    targets_by_observation: dict[str, list[str]] = defaultdict(list)
    for row in references:
        targets_by_observation[row["r3_observation_section_id"]].append(row["section_id"])
    if len(targets_by_observation) != 6:
        raise ValueError(f"expected 6 unique observation sections, got {len(targets_by_observation)}")

    raw_sections = pipeline.read_csv_cp932(census_dir / inputs["sections_csv"])
    raw_by_id = {row["交通調査基本区間番号"]: row for row in raw_sections}
    sections = pipeline.normalize_sections([
        raw_by_id[section_id] for section_id in sorted(targets_by_observation)
    ])
    section_by_id = {row["census_section_id"]: row for row in sections}

    net_path = REPOSITORY_ROOT / inputs["sumo_net_xml"]
    osm_path = REPOSITORY_ROOT / inputs["source_osm_xml"]
    net_root = ET.parse(net_path).getroot()
    transformer, offset_x, offset_y = pipeline.parse_sumo_location(net_root)
    osm_tags = pipeline.load_osm_way_tags(osm_path)
    edges = pipeline.load_sumo_edges(net_path, osm_tags)
    edge_by_id = {row["sumo_edge_id"]: row for row in edges}
    geometries = pipeline.load_census_geometries(
        census_dir / inputs["section_geometry_dir"],
        set(targets_by_observation), transformer, offset_x, offset_y,
    )
    if set(geometries) != set(targets_by_observation):
        raise ValueError("one or more external observation geometries are missing")
    thresholds = pipeline.thresholds_from_config(config)
    _, missing, corridors, _, _ = pipeline.match_sections_to_corridors(
        sections, geometries, edges, thresholds
    )
    if missing:
        raise ValueError("external observation geometry unexpectedly unresolved")
    selected = {row["section_id"]: row for row in corridors if row["selected"]}

    edge_tree = STRtree([row["geometry"] for row in edges])
    geometry_id_to_index = {id(row["geometry"]): index for index, row in enumerate(edges)}
    candidates: dict[str, list[dict[str, Any]]] = {}
    spatial_coverage: dict[str, float] = {}
    for section_id, section in section_by_id.items():
        items = pipeline._candidate_edge_features(
            section, geometries[section_id], edges, edge_tree, geometry_id_to_index, thresholds
        )
        candidates[section_id] = items
        union = unary_union([item["edge"]["geometry"] for item in items])
        spatial_coverage[section_id] = (
            geometries[section_id].intersection(union.buffer(thresholds.candidate_buffer_m)).length
            / geometries[section_id].length
        )

    # The automatic candidate for 13200100070 is an untagged motorway_link.
    # Canonical name and route-relation evidence identify both Route 1 mainline
    # carriageways; keep both until official up/down assignment is reviewed.
    haneda_corridors = []
    for row in corridors:
        if row["section_id"] != "13200100070" or row["corridor_coverage_ratio"] < 0.95:
            continue
        ids = row["corridor_edge_ids"].split(";")
        if {edge_by_id[edge_id]["name"] for edge_id in ids} == {"首都高速1号羽田線"}:
            haneda_corridors.append(row)
    maximal_haneda: dict[str, dict[str, Any]] = {}
    for row in haneda_corridors:
        first = row["corridor_edge_ids"].split(";")[0].split("#")[0]
        if first not in maximal_haneda or row["edge_count"] > maximal_haneda[first]["edge_count"]:
            maximal_haneda[first] = row
    if len(maximal_haneda) != 2:
        raise ValueError(f"expected two Haneda mainline carriageway candidates, got {len(maximal_haneda)}")
    haneda_pair = sorted(maximal_haneda.values(), key=lambda row: -row["corridor_coverage_ratio"])

    evidence_edge_ids = {
        edge_id
        for row in selected.values()
        for edge_id in row["corridor_edge_ids"].split(";")
    }
    evidence_edge_ids.update(
        edge_id for row in haneda_pair for edge_id in row["corridor_edge_ids"].split(";")
    )
    orig_ids = _edge_orig_ids(net_path, evidence_edge_ids)
    way_ids = {way_id for values in orig_ids.values() for way_id in values}
    relation_path = (
        REPOSITORY_ROOT
        / "03_data/processed/traffic_simulation/road_network/sumo/common/kanto_260716_road_route_relations.osm.xml"
    )
    way_tags, memberships = _way_and_relation_evidence(osm_path, relation_path, way_ids)

    edge_evidence: list[dict[str, Any]] = []
    for edge_id in sorted(evidence_edge_ids):
        for way_id in orig_ids[edge_id] or [""]:
            tags = way_tags.get(way_id, {})
            edge_evidence.append({
                "edge_id": edge_id,
                "osm_way_id": way_id,
                "sumo_from": edge_by_id[edge_id]["from_node"],
                "sumo_to": edge_by_id[edge_id]["to_node"],
                "osm_highway": tags.get("highway", ""),
                "osm_ref": tags.get("ref", ""),
                "osm_name": tags.get("name", "") or tags.get("name:ja", ""),
                "route_relations_json": json_text(memberships.get(way_id, [])),
            })

    physical: dict[str, dict[str, Any]] = {}
    for section_id in sorted(targets_by_observation):
        section = section_by_id[section_id]
        automatic = selected[section_id]
        automatic_ids = automatic["corridor_edge_ids"].split(";")
        chosen_ids = automatic_ids
        alternative_corridors: list[dict[str, Any]] = []
        extension: dict[str, Any] = {}
        route_identity = "CONFIRMED_WAY_REF"
        rationale = "Configured high-confidence rule passed; route/ref, coverage and directed topology are consistent."
        status = "AUTO_ACCEPT"
        coverage = float(automatic["corridor_coverage_ratio"])

        if section_id == "13200100070":
            status = "REVIEW_REQUIRED"
            chosen_ids = haneda_pair[0]["corridor_edge_ids"].split(";")
            coverage = float(haneda_pair[0]["corridor_coverage_ratio"])
            route_identity = "CONFIRMED_CANONICAL_NAME_AND_ROUTE_RELATION"
            alternative_corridors = [{
                "edge_ids": row["corridor_edge_ids"].split(";"),
                "coverage_ratio": round(float(row["corridor_coverage_ratio"]), 6),
                "connection_violation_count": _connection_violations(
                    row["corridor_edge_ids"].split(";"), edge_by_id
                ),
            } for row in haneda_pair]
            rationale = (
                "Official name 高速1号羽田線 matches OSM/route-relation name 首都高速1号羽田線. "
                "Both mainline carriageways have ref=1 and relation 4256244 (network=首都高速道路, ref=1); "
                "operator is blank in the relation. The automatic motorway_link candidate is rejected. "
                "Manual review is still required to assign the two connected mainline corridors to official up/down."
            )
        elif section_id == "13403160320":
            route_identity = "CONFIRMED_ROUTE_RELATION"
            rationale = (
                "All seven selected edges are connected and derive from OSM ways with ref=316/name=海岸通り. "
                "Relation 11699637 supplies network=JP:prefectural:tokyo, ref=316 and name=日本橋芝浦大森線; "
                "operator is blank. Coverage passes the unchanged medium threshold."
            )
        elif section_id == "13300010260":
            status = "NETWORK_EXTENSION_REQUIRED"
            route_identity = "CONFIRMED_PARTIAL_WAY_REF"
            extension = _minimum_extension(
                geometries[section_id], candidates[section_id], thresholds.candidate_buffer_m,
                net_root, offset_x, offset_y,
            )
            rationale = (
                "Only 24.5% of the official National Route 1 geometry is within 25 m of the current network. "
                "Threshold adjustment is prohibited; extend the source/network search extent around the uncovered geometry."
            )

        physical[section_id] = {
            "status": status,
            "official_route_number": section["route_number"],
            "official_route_name": section["route_name"],
            "automatic_confidence": automatic["confidence"],
            "network_spatial_coverage_ratio": round(spatial_coverage[section_id], 6),
            "candidate_corridor_coverage_ratio": round(coverage, 6),
            "candidate_edge_ids": chosen_ids,
            "automatic_edge_ids": automatic_ids,
            "alternative_corridors": alternative_corridors,
            "route_identity_status": route_identity,
            "connection_violation_count": _connection_violations(chosen_ids, edge_by_id),
            "full_corridor_connection_status": (
                "NOT_TESTABLE_UNTIL_EXTENSION" if status == "NETWORK_EXTENSION_REQUIRED" else "CONNECTED"
            ),
            "extension": extension,
            "evidence_summary": rationale,
        }

    reference_rows: list[dict[str, Any]] = []
    for source in references:
        section_id = source["r3_observation_section_id"]
        item = physical[section_id]
        reference_rows.append({
            "target_section_id": source["section_id"],
            "observation_section_id": section_id,
            "observation_municipality_code": source["r3_observation_section_municipality_code"],
            "classification": item["status"],
            "automatic_confidence": item["automatic_confidence"],
            "network_spatial_coverage_ratio": item["network_spatial_coverage_ratio"],
            "candidate_corridor_coverage_ratio": item["candidate_corridor_coverage_ratio"],
            "route_identity_status": item["route_identity_status"],
            "connection_violation_count": item["connection_violation_count"],
            "full_corridor_connection_status": item["full_corridor_connection_status"],
            "candidate_edge_ids": ";".join(item["candidate_edge_ids"]),
            "candidate_directed_corridors_json": json_text(item["alternative_corridors"]),
            "minimum_extension_bbox_wgs84_json": json_text(
                item["extension"].get("minimum_25m_search_bbox_wgs84", {})
            ),
            "evidence_summary": item["evidence_summary"],
            "mapping_threshold_changed": False,
            "existing_mapping_changed": False,
            "rule_id": "EXTERNAL_OBSERVATION_MAPPING_CANDIDATE_REVIEW_V1",
        })
    reference_rows.sort(key=lambda row: row["target_section_id"])

    counts = Counter(row["classification"] for row in reference_rows)
    summary = {
        "schema_version": 1,
        "review_id": "external_observation_mapping_candidate_review_20260827",
        "scope": {
            "target_reference_count": len(reference_rows),
            "unique_observation_section_count": len(physical),
            "candidate_buffer_m": thresholds.candidate_buffer_m,
        },
        "classification_counts": {status: counts[status] for status in STATUS_ORDER},
        "existing_network_formally_adoptable_count": counts["AUTO_ACCEPT"],
        "manual_review_count": counts["REVIEW_REQUIRED"],
        "limited_network_extension_required_count": counts["NETWORK_EXTENSION_REQUIRED"],
        "unresolved_count": counts["UNRESOLVED"],
        "physical_observation_sections": physical,
        "network_extension": physical["13300010260"]["extension"],
        "guardrails": {
            "existing_mapping_changed": False,
            "matching_threshold_changed": False,
            "representative_edge_inferred": False,
            "direction_assignment_finalized": False,
        },
        "source_manifest": [
            {"path": str(path.relative_to(REPOSITORY_ROOT)), "sha256": sha256_file(path)}
            for path in (audit_path, census_dir / inputs["sections_csv"], net_path, osm_path, relation_path)
        ],
    }
    expected = {"AUTO_ACCEPT": 8, "REVIEW_REQUIRED": 1, "NETWORK_EXTENSION_REQUIRED": 1, "UNRESOLVED": 0}
    if summary["classification_counts"] != expected:
        raise ValueError(f"unexpected review summary: {summary['classification_counts']}")
    return reference_rows, edge_evidence, summary


def render_report(summary: dict[str, Any]) -> str:
    rows = []
    for section_id, item in summary["physical_observation_sections"].items():
        targets = {
            "13200100070": "13200100080", "13300010260": "13300010290",
            "13400020040": "13400020050", "13400110130": "13400110100 / 13400110110 / 13400110120",
            "13403160320": "13403160330 / 13403160340 / 13403160350", "13604210030": "13604210040",
        }[section_id]
        rows.append(
            f"| `{section_id}` | {targets} | {item['status']} | "
            f"{item['network_spatial_coverage_ratio']:.1%} | {item['candidate_corridor_coverage_ratio']:.1%} | "
            f"{item['route_identity_status']} | {item['connection_violation_count']} |"
        )
    extension = summary["network_extension"]
    bbox = extension["minimum_25m_search_bbox_wgs84"]
    counts = summary["classification_counts"]
    return f"""# 外部観測参照10件 正式mapping候補レビュー

review ID: `{summary['review_id']}`

既存mappingおよびmatching閾値は変更していない。10 target参照は6 unique公式観測区間を参照する。

## 判定結果

| 公式観測区間 | target区間 | 分類 | network被覆 | candidate coverage | route identity | connection violation |
|---|---|---|---:|---:|---|---:|
{chr(10).join(rows)}

## `13200100070`

自動選択された`5219302`は無名・refなし・route relationなしの`motorway_link`であるため、正式候補から除外した。公式名「高速1号羽田線」に対し、次の二つの本線corridorを確認した。

- `4854104#1;4854104#2`：coverage 99.8%、接続違反0
- `45554540#0;45554540#1`：coverage 99.4%、接続違反0

両方ともOSM `ref=1`、名称「首都高速1号羽田線」、route relation `4256244`、network=`首都高速道路`、relation ref=`1`である。relationのoperatorは空欄である。路線同一性は確認できるが、Census上り・下りへの割当が未確定のため`REVIEW_REQUIRED`とした。

## `13403160320`

7 edgeのselected corridorは接続違反0、coverage 58.1%で、変更していないmedium基準30%を満たす。OSM Wayの`ref=316`、別名「海岸通り」に加え、route relation `11699637`がnetwork=`JP:prefectural:tokyo`、ref=`316`、名称「日本橋芝浦大森線」を与える。正式路線identityと一致するため3 target参照を`AUTO_ACCEPT`とした。

## `13300010260`の限定拡張

公式geometry {extension['official_geometry_length_m']:.1f}mのうち、既存ネットワーク被覆は{extension['covered_length_m']:.1f}m、未被覆は{extension['uncovered_length_m']:.1f}m（{extension['uncovered_ratio']:.1%}）である。閾値調整ではなく、未被覆geometryの25m bufferを最小探索範囲とする。

```json
{json.dumps(bbox, ensure_ascii=False, indent=2)}
```

これは最小の空間探索bboxである。実際のネットワーク生成では、bbox内の必要wayだけでなく、既存ネットワークへの接続nodeと該当restriction relationのclosureを含める。

## Summary

- 既存ネットワークで正式採用可能：**{counts['AUTO_ACCEPT']}/10**
- 手動確認：**{counts['REVIEW_REQUIRED']}/10**
- 限定ネットワーク拡張が必要：**{counts['NETWORK_EXTENSION_REQUIRED']}/10**
- 未解決：**{counts['UNRESOLVED']}/10**

方向別traffic系列への最終割当は本レビューの範囲外であり、`direction_assignment_finalized=false`を維持する。
"""


def run(data_dir: Path, report_path: Path) -> dict[str, Any]:
    references, evidence, summary = build_review(data_dir)
    write_csv(data_dir / "external_observation_mapping_candidates.csv", references)
    write_csv(data_dir / "external_observation_mapping_candidate_edge_evidence.csv", evidence)
    (data_dir / "external_observation_mapping_candidate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    summary = run(args.data_dir.resolve(), args.report.resolve())
    print(json.dumps({
        "review_id": summary["review_id"],
        "classification_counts": summary["classification_counts"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
