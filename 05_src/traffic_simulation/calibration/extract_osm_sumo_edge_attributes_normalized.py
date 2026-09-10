#!/usr/bin/env python3
"""Extract final-mapping OSM/SUMO edge attributes without imputation.

The source OSM tags, route-relation tags, model-assumption materialization,
and netconvert output are deliberately kept as different evidence layers.
Missing OSM values are never reconstructed from the SUMO network.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MAPPING = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826/census_section_final_mapping.csv"
DEFAULT_OSM = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/road_network/sumo/common/ota_ward_20260716_relation_closure_v16.osm.xml"
DEFAULT_ROUTE_RELATIONS = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/road_network/sumo/common/kanto_260716_road_route_relations.osm.xml"
DEFAULT_ROUTE_RELATION_PARENT = REPOSITORY_ROOT / "03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf"
DEFAULT_ROUTE_RELATION_MANIFEST = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/road_network/sumo/common/kanto_260716_road_route_relations_manifest.json"
DEFAULT_NET = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/ota_ward_explicit_v17_oneway.net.xml"
DEFAULT_ONEWAY_MANIFEST = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260823_v17_oneway_materialization_tdd/oneway_materialization_manifest.json"
DEFAULT_LANE_ASSUMPTIONS = REPOSITORY_ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260822_missing_lane_simulation_fallback_tdd/simulation_baseline.json.gz"
DEFAULT_TYPEMAP = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation/osm_tokyo_motorized.typ.xml"
DEFAULT_OUTPUT_DIR = DEFAULT_MAPPING.parent

OSM_FIELDS = (
    "lanes", "lanes:forward", "lanes:backward", "lanes:both_ways",
    "oneway", "ref", "name", "highway", "maxspeed", "access",
)
RELATION_FIELDS = ("network", "ref", "operator")
ACCESS_PREFIXES = ("access", "vehicle", "motor_vehicle", "motorcar", "hgv", "bus", "psv")
INTEGER_FIELDS = {"lanes", "lanes:forward", "lanes:backward", "lanes:both_ways"}
RULES = {
    "osm": "OSM_WAY_TAG_PRESERVE_NFKC_V1",
    "route_relation": "OSM_ROAD_ROUTE_RELATION_MEMBERSHIP_V1",
    "sumo": "SUMO_NET_EDGE_LANE_EXTRACT_V1",
    "reverse": "SUMO_EXACT_NODE_SWAP_SAME_OSM_WAY_V1",
    "missing": "NO_CROSS_SOURCE_IMPUTATION_V1",
}


def clean(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").strip()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_final_edges(path: Path) -> tuple[set[str], dict[str, list[str]]]:
    sections: dict[str, list[str]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            for edge_id in filter(None, (clean(item) for item in row.get("final_edge_ids", "").split(";"))):
                sections[edge_id].append(clean(row["section_id"]))
    return set(sections), sections


def _params(element: ET.Element) -> dict[str, str]:
    return {child.get("key", ""): child.get("value", "") for child in element.findall("param")}


def load_net(
    path: Path, selected: set[str]
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], list[str]], dict[str, list[str]]]:
    records: dict[str, dict[str, Any]] = {}
    endpoint_index: dict[tuple[str, str], list[str]] = defaultdict(list)
    all_orig_ids: dict[str, list[str]] = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag != "edge":
            continue
        edge_id = element.get("id", "")
        if edge_id.startswith(":") or not element.get("from") or not element.get("to"):
            element.clear()
            continue
        lanes = element.findall("lane")
        params = _params(element)
        # netconvert may encode more than one source way in a whitespace-separated
        # origId value.  Keep the source IDs from the network instead of inferring
        # them from the (occasionally synthetic) SUMO edge ID.
        orig_ids = sorted({
            source_id
            for lane in lanes
            for key, value in _params(lane).items()
            if key == "origId"
            for source_id in value.split()
            if source_id
        })
        endpoint_index[(element.get("from", ""), element.get("to", ""))].append(edge_id)
        all_orig_ids[edge_id] = orig_ids
        if edge_id in selected:
            records[edge_id] = {
                "edge_id": edge_id,
                "from": element.get("from", ""),
                "to": element.get("to", ""),
                "type": element.get("type", ""),
                "name": element.get("name", ""),
                "orig_ids": orig_ids,
                "osm_defaults": sorted(filter(None, params.get("osmDefaults", "").split())),
                "edge_params": params,
                "lanes": [{
                    "id": lane.get("id", ""),
                    "speed": lane.get("speed", ""),
                    "allow": lane.get("allow", ""),
                    "disallow": lane.get("disallow", ""),
                    "width": lane.get("width", ""),
                } for lane in lanes],
            }
        element.clear()
    missing = selected - set(records)
    if missing:
        raise ValueError(f"{len(missing)} final-mapping edges absent from SUMO net; examples: {sorted(missing)[:5]}")
    return records, endpoint_index, all_orig_ids


def load_osm(path: Path, selected_way_ids: set[str]) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    ways: dict[str, dict[str, str]] = {}
    relation_membership: dict[str, list[dict[str, str]]] = defaultdict(list)
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "way":
            way_id = element.get("id", "")
            if way_id in selected_way_ids:
                ways[way_id] = {tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")}
        elif element.tag == "relation":
            tags = {tag.get("k", ""): tag.get("v", "") for tag in element.findall("tag")}
            if tags.get("type") == "route" and tags.get("route") == "road":
                record = {"relation_id": element.get("id", ""), **{key: tags.get(key, "") for key in RELATION_FIELDS}}
                for member in element.findall("member"):
                    if member.get("type") == "way" and member.get("ref") in selected_way_ids:
                        relation_membership[member.get("ref", "")].append(record)
        # Clear complete container elements only.  Clearing every end event would
        # erase tag/member attributes before their enclosing way/relation is read.
        if element.tag in {"way", "relation", "node"}:
            element.clear()
    return ways, relation_membership


def load_lane_assumptions(path: Path, selected_way_ids: set[str]) -> dict[str, dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        document = json.load(handle)
    return {
        str(record["source_way_id"]): record
        for record in document.get("assumption_records", [])
        if str(record["source_way_id"]) in selected_way_ids
    }


def load_oneway_manifest(path: Path, selected_way_ids: set[str]) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    return {
        str(record["source_way_id"]): record
        for record in document.get("records", [])
        if str(record["source_way_id"]) in selected_way_ids
    }


def normalize_value(field: str, value: str) -> tuple[str, str]:
    text = clean(value)
    if not text:
        return "", "MISSING"
    if field in INTEGER_FIELDS:
        if re.fullmatch(r"[1-9][0-9]*", text):
            return str(int(text)), "PRESENT"
        return "", "INVALID"
    if field == "oneway":
        mapping = {"yes": "yes", "1": "yes", "true": "yes", "no": "no", "0": "no", "false": "no", "-1": "-1"}
        return (mapping[text.lower()], "PRESENT") if text.lower() in mapping else ("", "INVALID")
    if field == "maxspeed":
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*(?:km/?h|kph)?", text, flags=re.I)
        if match:
            return format(float(match.group(1)), "g"), "PRESENT"
        return "", "UNSUPPORTED_FORMAT"
    return text, "PRESENT"


def aggregate_way_tag(field: str, way_ids: list[str], ways: dict[str, dict[str, str]]) -> dict[str, Any]:
    raw_map = {way_id: ways.get(way_id, {}).get(field, "") for way_id in way_ids}
    normalized_by_way = {way_id: normalize_value(field, value) for way_id, value in raw_map.items()}
    present = {value for value, status in normalized_by_way.values() if status == "PRESENT"}
    invalid = sorted({status for _, status in normalized_by_way.values() if status not in {"PRESENT", "MISSING"}})
    if invalid:
        normalized, status = "", invalid[0] if len(invalid) == 1 else "INVALID"
    elif len(present) > 1:
        normalized, status = "", "CONFLICT"
    elif len(present) == 1:
        normalized, status = next(iter(present)), "PRESENT"
    else:
        normalized, status = "", "MISSING"
    return {"raw_map": raw_map, "normalized": normalized, "status": status}


def aggregate_relation_field(field: str, way_ids: list[str], memberships: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    records = [record for way_id in way_ids for record in memberships.get(way_id, [])]
    values = sorted({clean(record.get(field)) for record in records if clean(record.get(field))})
    status = "PRESENT" if len(values) == 1 else "CONFLICT" if len(values) > 1 else "MISSING"
    return {"raw": values, "normalized": values[0] if len(values) == 1 else "", "status": status, "records": records}


def lane_source(record: dict[str, Any], osm: dict[str, Any], assumptions: list[dict[str, Any]]) -> tuple[str, str, str]:
    if "numLanes" in record["osm_defaults"]:
        return "SUMO_TYPE_DEFAULT", record["type"], "NETCONVERT_OSM_DEFAULT_ANNOTATION_V1"
    if osm["lanes"]["status"] == "PRESENT" or any(osm[field]["status"] == "PRESENT" for field in ("lanes:forward", "lanes:backward", "lanes:both_ways")):
        return "OSM_EXPLICIT_TRANSFORMED", ";".join(record["orig_ids"]), "NETCONVERT_OSM_LANE_TRANSFORMATION_V1"
    if assumptions:
        ids = sorted({item.get("assumption_id", "") for item in assumptions})
        return "MODEL_ASSUMPTION_MATERIALIZED", ";".join(ids), "MISSING_SOURCE_LANE_SIMULATION_FALLBACK_V1"
    return "UNRESOLVED_TRANSFORMATION_PROVENANCE", ";".join(record["orig_ids"]), RULES["missing"]


def speed_source(record: dict[str, Any], osm: dict[str, Any]) -> tuple[str, str, str]:
    if "speed" in record["osm_defaults"]:
        return "SUMO_TYPE_DEFAULT", record["type"], "NETCONVERT_OSM_DEFAULT_ANNOTATION_V1"
    if osm["maxspeed"]["status"] == "PRESENT":
        return "OSM_EXPLICIT_TRANSFORMED", ";".join(record["orig_ids"]), "NETCONVERT_OSM_MAXSPEED_TRANSFORMATION_V1"
    return "UNRESOLVED_TRANSFORMATION_PROVENANCE", ";".join(record["orig_ids"]), RULES["missing"]


def permission_source(record: dict[str, Any], ways: dict[str, dict[str, str]]) -> tuple[str, str, str]:
    related = {
        key for way_id in record["orig_ids"] for key in ways.get(way_id, {})
        if any(key == prefix or key.startswith(prefix + ":") for prefix in ACCESS_PREFIXES)
    }
    if related:
        return "OSM_EXPLICIT_PLUS_TYPEMAP_TRANSFORMED", ";".join(record["orig_ids"]), "NETCONVERT_OSM_ACCESS_TRANSFORMATION_V1"
    return "SUMO_TYPE_DEFAULT", record["type"], "CUSTOM_TYPEMAP_PERMISSION_DEFAULT_V1"


def build_rows(
    records: dict[str, dict[str, Any]], endpoint_index: dict[tuple[str, str], list[str]],
    all_orig_ids: dict[str, list[str]],
    ways: dict[str, dict[str, str]], memberships: dict[str, list[dict[str, str]]],
    lane_assumptions: dict[str, dict[str, Any]], oneway_manifest: dict[str, dict[str, Any]],
    sections: dict[str, list[str]], paths: dict[str, Path],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for edge_id in sorted(records):
        net = records[edge_id]
        way_ids = net["orig_ids"]
        osm = {field: aggregate_way_tag(field, way_ids, ways) for field in OSM_FIELDS}
        rel = {field: aggregate_relation_field(field, way_ids, memberships) for field in RELATION_FIELDS}
        rel_records = [item for field in rel.values() for item in field["records"]]
        relation_ids = sorted({item["relation_id"] for item in rel_records})
        assumptions = [lane_assumptions[way_id] for way_id in way_ids if way_id in lane_assumptions]
        oneway_records = [oneway_manifest[way_id] for way_id in way_ids if way_id in oneway_manifest]
        same_way_candidates = []
        topology_candidates = sorted(endpoint_index.get((net["to"], net["from"]), []))
        for candidate in topology_candidates:
            if set(all_orig_ids.get(candidate, ())) & set(way_ids):
                same_way_candidates.append(candidate)
        same_way_candidates = sorted(same_way_candidates)
        if len(same_way_candidates) == 1:
            reverse_id, reverse_status = same_way_candidates[0], "RESOLVED_EXACT_SAME_WAY"
        elif len(same_way_candidates) > 1:
            reverse_id, reverse_status = "", "AMBIGUOUS_EXACT_SAME_WAY"
        else:
            canonical = {record.get("canonical_oneway") for record in oneway_records}
            reverse_id = ""
            reverse_status = "NOT_AVAILABLE_ONEWAY" if canonical and canonical <= {"yes", "-1"} else "UNRESOLVED"

        lane_type, lane_source_id, lane_rule = lane_source(net, osm, assumptions)
        speed_type, speed_source_id, speed_rule = speed_source(net, osm)
        permission_type, permission_source_id, permission_rule = permission_source(net, ways)
        provenance: dict[str, Any] = {}
        provenance["osm_way_id"] = {
            "source_type": "SUMO_NET_ORIGID",
            "source_id": edge_id,
            "source_file": relative(paths["net"]),
            "extraction_rule_id": "SUMO_LANE_ORIGID_TO_OSM_WAY_V1",
            "missing_status": "PRESENT" if way_ids else "MISSING",
        }
        for field in OSM_FIELDS:
            provenance[f"osm_{field.replace(':', '_')}"] = {
                "source_type": "OSM_WAY_EXPLICIT" if osm[field]["status"] == "PRESENT" else "OSM_WAY_MISSING_OR_INVALID",
                "source_id": way_ids,
                "source_file": relative(paths["osm"]),
                "extraction_rule_id": RULES["osm"],
                "missing_status": osm[field]["status"],
            }
        for field in RELATION_FIELDS:
            provenance[f"route_relation_{field}"] = {
                "source_type": "OSM_ROUTE_RELATION_EXPLICIT" if rel[field]["status"] == "PRESENT" else "OSM_ROUTE_RELATION_MISSING_OR_CONFLICT",
                "source_id": relation_ids,
                "source_file": relative(paths["route_relations"]),
                "extraction_rule_id": RULES["route_relation"],
                "missing_status": rel[field]["status"],
            }
        provenance.update({
            "sumo_lane_count": {"source_type": lane_type, "source_id": lane_source_id, "source_file": relative(paths["net"]), "extraction_rule_id": lane_rule, "missing_status": "PRESENT"},
            "sumo_speed": {"source_type": speed_type, "source_id": speed_source_id, "source_file": relative(paths["net"]), "extraction_rule_id": speed_rule, "missing_status": "PRESENT"},
            "sumo_allow_disallow": {"source_type": permission_type, "source_id": permission_source_id, "source_file": relative(paths["net"]), "extraction_rule_id": permission_rule, "missing_status": "PRESENT"},
            "sumo_from_to": {"source_type": "SUMO_NETCONVERT_OUTPUT", "source_id": edge_id, "source_file": relative(paths["net"]), "extraction_rule_id": RULES["sumo"], "missing_status": "PRESENT"},
            "reverse_edge": {"source_type": "SUMO_TOPOLOGY_EXACT_REVERSE" if reverse_id else "SUMO_TOPOLOGY_UNRESOLVED_OR_UNAVAILABLE", "source_id": reverse_id, "source_file": relative(paths["net"]), "extraction_rule_id": RULES["reverse"], "missing_status": reverse_status},
        })
        unresolved_count = sum(
            item["missing_status"] != "PRESENT"
            for key, item in provenance.items()
            if key.startswith("osm_") or key.startswith("route_relation_")
        )
        access_related = {
            way_id: {
                key: value
                for key, value in ways.get(way_id, {}).items()
                if any(key == prefix or key.startswith(prefix + ":") for prefix in ACCESS_PREFIXES)
            }
            for way_id in way_ids
        }
        row: dict[str, Any] = {
            "edge_id": edge_id,
            "final_mapping_section_ids": ";".join(sorted(set(sections[edge_id]))),
            "osm_way_ids_raw": ";".join(way_ids),
            "osm_way_id": way_ids[0] if len(way_ids) == 1 else "",
            "osm_way_id_status": "RESOLVED" if len(way_ids) == 1 else "MISSING" if not way_ids else "MULTIPLE",
            "sumo_from_raw": net["from"], "sumo_from_normalized": net["from"],
            "sumo_to_raw": net["to"], "sumo_to_normalized": net["to"],
            "sumo_type_raw": net["type"], "sumo_name_raw": net["name"],
            "sumo_lane_count_raw": str(len(net["lanes"])), "sumo_lane_count_normalized": str(len(net["lanes"])),
            "sumo_lane_ids_raw_json": json_text([lane["id"] for lane in net["lanes"]]),
            "sumo_speed_mps_raw_json": json_text([lane["speed"] for lane in net["lanes"]]),
            "sumo_speed_mps_normalized": ";".join(sorted({clean(lane["speed"]) for lane in net["lanes"] if clean(lane["speed"])})),
            "sumo_allow_raw_json": json_text({lane["id"]: lane["allow"] for lane in net["lanes"]}),
            "sumo_allow_normalized_json": json_text(sorted({clean(lane["allow"]) for lane in net["lanes"]})),
            "sumo_disallow_raw_json": json_text({lane["id"]: lane["disallow"] for lane in net["lanes"]}),
            "sumo_disallow_normalized_json": json_text(sorted({clean(lane["disallow"]) for lane in net["lanes"]})),
            "sumo_osm_defaults_raw": ";".join(net["osm_defaults"]),
            "sumo_lane_count_source_type": lane_type, "sumo_lane_count_source_id": lane_source_id,
            "sumo_lane_count_source_file": relative(paths["net"]), "sumo_lane_count_extraction_rule_id": lane_rule,
            "sumo_speed_source_type": speed_type, "sumo_speed_source_id": speed_source_id,
            "sumo_speed_source_file": relative(paths["net"]), "sumo_speed_extraction_rule_id": speed_rule,
            "sumo_permission_source_type": permission_type, "sumo_permission_source_id": permission_source_id,
            "sumo_permission_source_file": relative(paths["net"]), "sumo_permission_extraction_rule_id": permission_rule,
            "osm_access_related_tags_raw_json": json_text(access_related),
            "route_relation_ids": ";".join(relation_ids),
            "route_relation_status": "AVAILABLE" if relation_ids else "MISSING",
            "lane_assumption_records_raw_json": json_text(assumptions),
            "lane_assumption_status": "MODEL_ASSUMPTION_MATERIALIZED" if assumptions else "NOT_APPLICABLE",
            "lane_assumption_source_file": relative(paths["lane_assumptions"]) if assumptions else "",
            "materialized_oneway_records_raw_json": json_text(oneway_records),
            "materialized_oneway_status": "AVAILABLE" if oneway_records else "MISSING",
            "materialized_oneway_source_file": relative(paths["oneway_manifest"]) if oneway_records else "",
            "reverse_edge_candidates_raw": ";".join(topology_candidates),
            "reverse_same_osm_way_candidates_raw": ";".join(same_way_candidates),
            "reverse_edge_id_normalized": reverse_id,
            "reverse_edge_status": reverse_status,
            "unresolved_attribute_count": str(unresolved_count),
            "attribute_provenance_json": json_text(provenance),
        }
        for field in OSM_FIELDS:
            column = field.replace(":", "_")
            row[f"osm_{column}_raw_json"] = json_text(osm[field]["raw_map"])
            row[f"osm_{column}_normalized"] = osm[field]["normalized"]
            row[f"osm_{column}_missing_status"] = osm[field]["status"]
        for field in RELATION_FIELDS:
            row[f"route_relation_{field}_raw_json"] = json_text(rel[field]["raw"])
            row[f"route_relation_{field}_normalized"] = rel[field]["normalized"]
            row[f"route_relation_{field}_missing_status"] = rel[field]["status"]
        rows.append(row)
    return rows


def qa_summary(rows: list[dict[str, Any]], paths: dict[str, Path]) -> dict[str, Any]:
    osm_by_attribute = {}
    for field in OSM_FIELDS:
        key = f"osm_{field.replace(':', '_')}_missing_status"
        osm_by_attribute[field] = dict(sorted(Counter(row[key] for row in rows).items()))
    relation_by_attribute = {
        field: dict(sorted(Counter(row[f"route_relation_{field}_missing_status"] for row in rows).items()))
        for field in RELATION_FIELDS
    }
    default_by_attribute = {
        "sumo_lane_count": sum(row["sumo_lane_count_source_type"] == "SUMO_TYPE_DEFAULT" for row in rows),
        "sumo_speed": sum(row["sumo_speed_source_type"] == "SUMO_TYPE_DEFAULT" for row in rows),
        "sumo_allow_disallow": sum(row["sumo_permission_source_type"] == "SUMO_TYPE_DEFAULT" for row in rows),
    }
    assumption_by_attribute = {
        "sumo_lane_count": sum(row["sumo_lane_count_source_type"] == "MODEL_ASSUMPTION_MATERIALIZED" for row in rows),
    }
    return {
        "schema_version": 1,
        "artifact": "osm_sumo_edge_attributes_normalized.csv",
        "scope": {"unique_final_mapping_edges": len(rows)},
        "source_files": {key: relative(value) for key, value in paths.items()},
        "normalization_policy": {
            "osm_missing_from_sumo_imputation": False,
            "cross_source_overwrite": False,
            "route_relation_requires_type_route_and_route_road": True,
            "reverse_resolution_requires_exact_from_to_swap_and_same_osm_way": True,
        },
        "osm_explicit_by_attribute": osm_by_attribute,
        "osm_explicit_value_instances_present": sum(
            counts.get("PRESENT", 0) for counts in osm_by_attribute.values()
        ),
        "osm_value_instances_missing_or_invalid": sum(
            count
            for counts in osm_by_attribute.values()
            for status, count in counts.items()
            if status != "PRESENT"
        ),
        "osm_edges_with_any_explicit_requested_value": sum(any(row[f"osm_{field.replace(':', '_')}_missing_status"] == "PRESENT" for field in OSM_FIELDS) for row in rows),
        "osm_edges_with_no_explicit_requested_value": sum(all(row[f"osm_{field.replace(':', '_')}_missing_status"] != "PRESENT" for field in OSM_FIELDS) for row in rows),
        "sumo_default_derived_edge_counts": default_by_attribute,
        "model_assumption_materialized_edge_counts": assumption_by_attribute,
        "sumo_value_provenance": {
            "lane_count": dict(sorted(Counter(row["sumo_lane_count_source_type"] for row in rows).items())),
            "speed": dict(sorted(Counter(row["sumo_speed_source_type"] for row in rows).items())),
            "allow_disallow": dict(sorted(Counter(row["sumo_permission_source_type"] for row in rows).items())),
        },
        "route_relation_availability": dict(sorted(Counter(row["route_relation_status"] for row in rows).items())),
        "route_relation_by_attribute": relation_by_attribute,
        "reverse_edge_resolution": dict(sorted(Counter(row["reverse_edge_status"] for row in rows).items())),
        "unresolved_attributes": {
            "total_edge_attribute_instances": sum(int(row["unresolved_attribute_count"]) for row in rows),
            "edges_with_one_or_more": sum(int(row["unresolved_attribute_count"]) > 0 for row in rows),
            "definition": "OSM way and road-route relation attributes with MISSING, INVALID, UNSUPPORTED_FORMAT, or CONFLICT status; SUMO values are not used to fill them.",
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("no rows to write")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--osm", type=Path, default=DEFAULT_OSM)
    parser.add_argument("--route-relations", type=Path, default=DEFAULT_ROUTE_RELATIONS)
    parser.add_argument("--net", type=Path, default=DEFAULT_NET)
    parser.add_argument("--oneway-manifest", type=Path, default=DEFAULT_ONEWAY_MANIFEST)
    parser.add_argument("--lane-assumptions", type=Path, default=DEFAULT_LANE_ASSUMPTIONS)
    parser.add_argument("--typemap", type=Path, default=DEFAULT_TYPEMAP)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    paths = {
        "mapping": args.mapping,
        "osm": args.osm,
        "route_relations": args.route_relations,
        "route_relation_parent_pbf": DEFAULT_ROUTE_RELATION_PARENT,
        "route_relation_manifest": DEFAULT_ROUTE_RELATION_MANIFEST,
        "net": args.net,
        "oneway_manifest": args.oneway_manifest,
        "lane_assumptions": args.lane_assumptions,
        "typemap": args.typemap,
    }
    final_edges, sections = load_final_edges(args.mapping)
    net_records, endpoint_index, all_orig_ids = load_net(args.net, final_edges)
    way_ids = {way_id for record in net_records.values() for way_id in record["orig_ids"]}
    ways, _ = load_osm(args.osm, way_ids)
    _, memberships = load_osm(args.route_relations, way_ids)
    lane_assumptions = load_lane_assumptions(args.lane_assumptions, way_ids)
    oneway_manifest = load_oneway_manifest(args.oneway_manifest, way_ids)
    rows = build_rows(net_records, endpoint_index, all_orig_ids, ways, memberships, lane_assumptions, oneway_manifest, sections, paths)
    output_csv = args.output_dir / "osm_sumo_edge_attributes_normalized.csv"
    output_qa = args.output_dir / "osm_sumo_edge_attributes_normalized_qa_summary.json"
    write_csv(output_csv, rows)
    output_qa.write_text(json.dumps(qa_summary(rows, paths), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "csv": str(output_csv), "qa": str(output_qa)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
