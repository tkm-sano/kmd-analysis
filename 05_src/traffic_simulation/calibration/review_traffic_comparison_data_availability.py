#!/usr/bin/env python3
"""Audit unresolved traffic comparison sections across R3, H27 and H22.

The script only inventories official evidence and existing mapping artifacts.
It does not infer a point, select an edge, impute traffic, or alter mappings.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
DEFAULT_R3_DIR = REPOSITORY_ROOT / "03_data/raw/traffic_simulation/road_census/mlit_r3_tokyo_20260823"
DEFAULT_H27_KASYO = Path("/tmp/kmd_h27_kasyo13.csv")
DEFAULT_H27_TRAFFIC = Path("/tmp/kmd_h27_zkntrf13.csv")
DEFAULT_H22_KASYO = Path("/tmp/kmd_h22_kasyo13.csv")
DEFAULT_H22_TRAFFIC = Path("/tmp/kmd_h22_zkntrf13.csv")

CAUSE_CODES = (
    "FOUND_IN_OTHER_SOURCE", "KEY_MISMATCH", "YEAR_MISMATCH",
    "PROCESSING_OMISSION", "TRULY_NOT_AVAILABLE", "OTHER",
)
FINAL_STATUSES = ("NO_ASSUMPTION_NEEDED", "DATA_NOT_AVAILABLE", "UNRESOLVED")
URLS = {
    "h27_kasyo": "https://www.mlit.go.jp/road/census/h27/data/csv/kasyo13.csv",
    "h27_traffic": "https://www.mlit.go.jp/road/census/h27/data/csv/zkntrf13.csv",
    "h22_kasyo": "https://www.mlit.go.jp/road/census/h22-1/data/csv/kasyo13.csv",
    "h22_traffic": "https://www.mlit.go.jp/road/census/h22-1/data/csv/zkntrf13.csv",
}


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def split(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def traffic_series_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    output: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        output[(row["都道府県指定市コード"], row["交通量調査単位区間番号"])].append(row)
    return output


def series_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "direction_codes": sorted({row.get("上り・下りの別", "") for row in rows if row.get("上り・下りの別", "")}),
        "vehicle_class_codes": sorted({row.get("車種区分", "") for row in rows if row.get("車種区分", "")}),
        "observation_flags": sorted({
            row.get("令和３年度調査交通量観測・非観測の別", row.get("平成２７年度調査交通量観測・非観測の別", row.get("交通量観測・非観測の別", "")))
            for row in rows
        } - {""}),
    }


def classify_availability(
    previous_cause: str, r3_observation_id: str,
    current_mapping_present: bool, current_mapping_usable: bool,
    h27_observed_location: bool, h27_series_complete: bool,
) -> tuple[str, str, list[str], str]:
    if previous_cause == "LOCATION_MAPPING_MISSING":
        if r3_observation_id and not current_mapping_present:
            return (
                "UNRESOLVED", "PROCESSING_OMISSION", ["PROCESSING_OMISSION"],
                "official R3 observation section and series exist, but that referenced section was outside the 66-section final-mapping population",
            )
        if current_mapping_usable:
            return (
                "NO_ASSUMPTION_NEEDED", "FOUND_IN_OTHER_SOURCE", ["FOUND_IN_OTHER_SOURCE"],
                "official R3 evidence and a traffic-usable observation-section mapping are both available",
            )
        return (
            "UNRESOLVED", "OTHER", ["OTHER"],
            "official R3 evidence and a final corridor exist, but the approved mapping is explicitly not usable for traffic assignment",
        )
    if h27_observed_location and h27_series_complete:
        return (
            "UNRESOLVED", "YEAR_MISMATCH", ["FOUND_IN_OTHER_SOURCE", "YEAR_MISMATCH"],
            "R3 has no observation location, but official H27 (and corroborating H22 lineage) contains an observed location and directional series; it is not current-year evidence",
        )
    return (
        "DATA_NOT_AVAILABLE", "TRULY_NOT_AVAILABLE", ["TRULY_NOT_AVAILABLE"],
        "no observed location is published for the linked R3, H27 or H22 record; non-observed estimated series are not a physical comparison cross-section",
    )


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classification_summary = {}
    for status in FINAL_STATUSES:
        selected = [row for row in rows if row["final_status"] == status]
        classification_summary[status] = {
            "section_count": len(selected),
            "target_final_unique_edge_count": len({edge for row in selected for edge in split(row["target_final_edge_ids"])}),
            "target_final_section_edge_pair_count": sum(row["target_final_edge_count"] for row in selected),
            "available_observation_mapping_unique_edge_count": len({edge for row in selected for edge in split(row["available_observation_mapping_edge_ids"])}),
        }
    cause_summary = []
    for cause in CAUSE_CODES:
        selected = [row for row in rows if cause in row["cause_codes"].split(";")]
        cause_summary.append({
            "cause_code": cause,
            "section_count": len(selected),
            "target_final_unique_edge_count": len({edge for row in selected for edge in split(row["target_final_edge_ids"])}),
            "available_observation_mapping_unique_edge_count": len({edge for row in selected for edge in split(row["available_observation_mapping_edge_ids"])}),
        })
    return {"classification_summary": classification_summary, "cause_summary": cause_summary}


def run(
    data_dir: Path = DEFAULT_DATA_DIR, r3_dir: Path = DEFAULT_R3_DIR,
    h27_kasyo_path: Path = DEFAULT_H27_KASYO, h27_traffic_path: Path = DEFAULT_H27_TRAFFIC,
    h22_kasyo_path: Path = DEFAULT_H22_KASYO, h22_traffic_path: Path = DEFAULT_H22_TRAFFIC,
) -> dict[str, Any]:
    for path in (h27_kasyo_path, h27_traffic_path, h22_kasyo_path, h22_traffic_path):
        if not path.exists():
            raise FileNotFoundError(f"download the registered official source first: {path}")
    prior = [
        row for row in read_csv(data_dir / "traffic_comparison_cross_section_refinement.csv")
        if row["primary_cause_code"] in {"OFFICIAL_LOCATION_MISSING", "LOCATION_MAPPING_MISSING"}
    ]
    if Counter(row["primary_cause_code"] for row in prior) != Counter({"OFFICIAL_LOCATION_MISSING": 15, "LOCATION_MAPPING_MISSING": 11}):
        raise ValueError("expected fixed scope of 15 official-location and 11 mapping deficits")

    r3_rows = read_csv(r3_dir / "kasyo13.csv", "cp932")
    r3_by_id = {row["交通調査基本区間番号"]: row for row in r3_rows}
    r3_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in r3_rows:
        r3_groups[(row["交通量／都道府県指定市コード"], row["交通量／調査単位区間番号"])].append(row)
    h27_by_id = {row["交通調査基本区間番号"]: row for row in read_csv(h27_kasyo_path)}
    h22_by_id = {row["交通調査基本区間番号"]: row for row in read_csv(h22_kasyo_path, "cp932")}
    h27_series = traffic_series_index(read_csv(h27_traffic_path, "cp932"))
    h22_series = traffic_series_index(read_csv(h22_traffic_path, "cp932"))
    finals = {row["section_id"]: row for row in read_csv(data_dir / "census_section_final_mapping.csv")}
    geometry_ids: set[str] = set()
    for path in (r3_dir / "webmap_tiles").glob("*.geojson"):
        document = json.loads(path.read_text(encoding="utf-8"))
        geometry_ids.update(
            str(feature.get("properties", {}).get("census", ""))
            for feature in document.get("features", [])
            if feature.get("properties", {}).get("census")
        )

    output: list[dict[str, Any]] = []
    for old in prior:
        sid = old["section_id"]
        r3 = r3_by_id[sid]
        r3_obs_ids = sorted({
            value for value in (
                r3["上り／観測地点交通調査基本区間番号"],
                r3["下り／観測地点交通調査基本区間番号"],
            ) if value
        })
        r3_obs_id = r3_obs_ids[0] if len(r3_obs_ids) == 1 else ""
        current_mapping = finals.get(r3_obs_id)
        current_mapping_present = current_mapping is not None
        current_mapping_usable = bool(current_mapping and current_mapping["usable_for_traffic_assignment"].lower() == "true")
        r3_observation_raw = r3_by_id.get(r3_obs_id, {})
        r3_key = (r3["交通量／都道府県指定市コード"], r3["交通量／調査単位区間番号"])
        alternate_same_key_locations = sorted({
            value
            for candidate in r3_groups[r3_key]
            for value in (
                candidate["上り／観測地点交通調査基本区間番号"],
                candidate["下り／観測地点交通調査基本区間番号"],
            ) if value
        })

        h27_id = r3["平成２７年度／交通調査基本区間番号"]
        h27 = h27_by_id.get(h27_id, {})
        h27_key = (
            h27.get("交通量調査単位区間番号／都道府県指定市コード", ""),
            h27.get("交通量調査単位区間番号／調査単位区間番号", ""),
        )
        h27_series_summary = series_summary(h27_series.get(h27_key, []))
        h27_observed_location = bool(
            h27.get("観測地点交通調査基本区間番号", "")
            and h27.get("交通量観測地点地名／市郡区町村丁字目", "")
            and h27.get("平成２７年度調査交通量観測・非観測の別", "") == "1"
        )
        h27_series_complete = (
            set(h27_series_summary["direction_codes"]) == {"1", "2"}
            and set(h27_series_summary["vehicle_class_codes"]) == {"1", "2"}
        )
        h22_id = h27.get("平成２２年度／交通調査基本区間番号", "")
        h22 = h22_by_id.get(h22_id, {})
        h22_key = (
            h22.get("交通量／都道府県指定市コード", ""),
            h22.get("交通量／調査単位区間番号", ""),
        )
        h22_series_summary = series_summary(h22_series.get(h22_key, []))

        final_status, primary, causes, reason = classify_availability(
            old["primary_cause_code"], r3_obs_id, current_mapping_present,
            current_mapping_usable, h27_observed_location, h27_series_complete,
        )
        available_obs_mapping = current_mapping
        if available_obs_mapping is None and h27_observed_location:
            available_obs_mapping = finals.get(h27.get("観測地点交通調査基本区間番号", ""))
        target = finals[sid]
        output.append({
            "section_id": sid,
            "previous_cause_code": old["primary_cause_code"],
            "final_status": final_status,
            "primary_availability_cause": primary,
            "cause_codes": ";".join(causes),
            "r3_traffic_key": "|".join(r3_key),
            "r3_observation_section_id": r3_obs_id,
            "r3_up_location_name": r3["上り／交通量観測地点地名"],
            "r3_down_location_name": r3["下り／交通量観測地点地名"],
            "r3_observation_flags": ";".join(sorted({r3["上り／令和３年度調査交通量観測・非観測の別"], r3["下り／令和３年度調査交通量観測・非観測の別"]} - {""})),
            "same_r3_key_alternate_observation_ids": ";".join(alternate_same_key_locations),
            "r3_observation_section_municipality_code": r3_observation_raw.get("市区町村コード", ""),
            "r3_observation_geometry_available": r3_obs_id in geometry_ids,
            "r3_observation_section_in_ota66_mapping_population": r3_obs_id in finals,
            "h27_section_id": h27_id,
            "h27_traffic_key": "|".join(h27_key),
            "h27_observation_section_id": h27.get("観測地点交通調査基本区間番号", ""),
            "h27_location_name": h27.get("交通量観測地点地名／市郡区町村丁字目", ""),
            "h27_observation_flag": h27.get("平成２７年度調査交通量観測・非観測の別", ""),
            "h27_observation_date": h27.get("交通量観測年月日", ""),
            "h27_series_summary_json": json.dumps(h27_series_summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "h22_section_id": h22_id,
            "h22_traffic_key": "|".join(h22_key),
            "h22_observation_section_id": h22.get("観測地点交通調査基本区間番号", ""),
            "h22_location_name": h22.get("交通量観測地点地名", ""),
            "h22_observation_flag": h22.get("交通量観測・非観測の別", ""),
            "h22_series_summary_json": json.dumps(h22_series_summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "current_observation_mapping_present": current_mapping_present,
            "current_observation_mapping_usable": current_mapping_usable,
            "available_observation_mapping_section_id": available_obs_mapping["section_id"] if available_obs_mapping else "",
            "available_observation_mapping_edge_ids": available_obs_mapping["final_edge_ids"] if available_obs_mapping else "",
            "target_final_edge_ids": target["final_edge_ids"],
            "target_final_edge_count": len(split(target["final_edge_ids"])),
            "reference_sources": "MLIT_R3_kasyo13;MLIT_R3_zkntrf13;MLIT_H27_kasyo13;MLIT_H27_zkntrf13;MLIT_H22_kasyo13;MLIT_H22_zkntrf13;existing_final_mapping",
            "evidence_summary": reason,
            "representative_edge_selected": False,
            "position_inferred": False,
            "traffic_imputed": False,
            "mapping_or_threshold_changed": False,
            "classification_rule_id": "TRAFFIC_COMPARISON_DATA_AVAILABILITY_AUDIT_V1",
        })

    parts = summarize(output)
    summary = {
        "schema_version": 1,
        "scope": {
            "section_count": len(output),
            "previous_official_location_missing": 15,
            "previous_location_mapping_missing": 11,
            "target_final_unique_edge_count": len({edge for row in output for edge in split(row["target_final_edge_ids"])}),
            "target_final_section_edge_pair_count": sum(row["target_final_edge_count"] for row in output),
        },
        **parts,
        "findings": {
            "r3_missing_location_recovered_in_h27": sum("FOUND_IN_OTHER_SOURCE" in row["cause_codes"] for row in output),
            "truly_no_observed_location_across_r3_h27_h22": sum(row["final_status"] == "DATA_NOT_AVAILABLE" for row in output),
            "referenced_observation_sections_omitted_from_66_mapping_scope": sum(row["primary_availability_cause"] == "PROCESSING_OMISSION" for row in output),
            "existing_but_traffic_unusable_mapping": sum(row["primary_availability_cause"] == "OTHER" for row in output),
            "key_mismatch": sum(row["primary_availability_cause"] == "KEY_MISMATCH" for row in output),
        },
        "source_provenance": {
            "r3_kasyo": {"path": str(r3_dir / "kasyo13.csv"), "sha256": sha256(r3_dir / "kasyo13.csv")},
            "r3_traffic": {"path": str(r3_dir / "zkntrf13.csv"), "sha256": sha256(r3_dir / "zkntrf13.csv")},
            "h27_kasyo": {"url": URLS["h27_kasyo"], "sha256": sha256(h27_kasyo_path)},
            "h27_traffic": {"url": URLS["h27_traffic"], "sha256": sha256(h27_traffic_path)},
            "h22_kasyo": {"url": URLS["h22_kasyo"], "sha256": sha256(h22_kasyo_path)},
            "h22_traffic": {"url": URLS["h22_traffic"], "sha256": sha256(h22_traffic_path)},
        },
        "reproduction": {
            "download": [
                f"curl -fsSL {URLS['h27_kasyo']} -o {DEFAULT_H27_KASYO}",
                f"curl -fsSL {URLS['h27_traffic']} -o {DEFAULT_H27_TRAFFIC}",
                f"curl -fsSL {URLS['h22_kasyo']} -o {DEFAULT_H22_KASYO}",
                f"curl -fsSL {URLS['h22_traffic']} -o {DEFAULT_H22_TRAFFIC}",
            ],
            "run": "PYTHONPATH=05_src .conda/bin/python 05_src/traffic_simulation/calibration/review_traffic_comparison_data_availability.py",
            "join_sequence": [
                "R3 section -> R3 up/down observation-section ID and prefecture/city+traffic-unit key",
                "R3 previous-year section ID -> H27 section; H27 traffic key -> H27 directional series",
                "H27 previous-year section ID -> H22 section; H22 traffic key -> H22 directional series",
                "official observation-section ID -> existing census_section_final_mapping.csv",
            ],
        },
        "guardrails": {
            "representative_edge_selection": False,
            "position_inference": False,
            "traffic_imputation": False,
            "mapping_or_threshold_change": False,
        },
    }
    write_csv(data_dir / "traffic_comparison_data_availability_review.csv", output)
    write_csv(data_dir / "traffic_comparison_data_availability_review_summary.csv", [
        {"final_status": key, **value} for key, value in parts["classification_summary"].items()
    ])
    write_csv(data_dir / "traffic_comparison_data_availability_review_cause_summary.csv", parts["cause_summary"])
    (data_dir / "traffic_comparison_data_availability_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--r3-dir", type=Path, default=DEFAULT_R3_DIR)
    parser.add_argument("--h27-kasyo", type=Path, default=DEFAULT_H27_KASYO)
    parser.add_argument("--h27-traffic", type=Path, default=DEFAULT_H27_TRAFFIC)
    parser.add_argument("--h22-kasyo", type=Path, default=DEFAULT_H22_KASYO)
    parser.add_argument("--h22-traffic", type=Path, default=DEFAULT_H22_TRAFFIC)
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.r3_dir, args.h27_kasyo, args.h27_traffic, args.h22_kasyo, args.h22_traffic), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
