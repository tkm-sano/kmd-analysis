#!/usr/bin/env python3
"""Create immutable provenance and capability records for Phase 13 X1 sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--catalog-output", required=True, type=Path)
    args = parser.parse_args()
    for output in (args.manifest_output, args.catalog_output):
        if output.exists():
            raise FileExistsError(f"immutable output already exists: {output}")

    files = []
    for path in sorted(item for item in args.raw_dir.rglob("*") if item.is_file()):
        files.append(
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    status_path = args.raw_dir / "mlit_r3_webmap_tiles/http_status.csv"
    statuses = []
    with status_path.open(encoding="utf-8") as stream:
        for row in csv.reader(stream):
            statuses.append({"url": row[0], "http_status": int(row[1])})
    tile_base = "https://www.mlit.go.jp/road/ir/ir-data/census_visualizationR3"
    for path in sorted((args.raw_dir / "mlit_r3_webmap_tiles").glob("*.geojson")):
        layer, zoom, x_value, y_value = path.stem.rsplit("_", 3)
        statuses.append(
            {
                "url": f"{tile_base}/{layer}/{zoom}/{x_value}/{y_value}.geojson",
                "http_status": 200,
                "local_file": path.name,
                "sha256": sha256(path),
            }
        )
    statuses.sort(key=lambda item: item["url"])

    plateau_zip = args.raw_dir / "13111_ota-ku_pref_2025_citygml_1_op.zip"
    with ZipFile(plateau_zip) as archive:
        tran_names = [
            name for name in archive.namelist()
            if name.startswith("udx/tran/") and name.endswith(".gml")
        ]
        plateau_road_count = 0
        plateau_lane_attribute_count = 0
        for name in tran_names:
            data = archive.read(name)
            plateau_road_count += data.count(b"<tran:Road ")
            plateau_lane_attribute_count += data.count(b"numberOfLanes")

    manifest = {
        "schema_version": 1,
        "investigation_id": "phase13_x1_official_evidence_20260821",
        "retrieved_at": "2026-08-21",
        "raw_artifact_count": len(files),
        "raw_artifacts": files,
        "mlit_web_map_tile_request_count": len(statuses),
        "mlit_web_map_http_status_counts": {
            str(code): sum(item["http_status"] == code for item in statuses)
            for code in sorted({item["http_status"] for item in statuses})
        },
        "mlit_web_map_requests": statuses,
    }
    catalog = {
        "schema_version": 1,
        "investigation_id": manifest["investigation_id"],
        "sources": [
            {
                "source_id": "MLIT_R3_ROAD_TRAFFIC_CENSUS_LOCATION_SURVEY",
                "authority": "国土交通省 道路局",
                "official_index": "https://www.mlit.go.jp/road/census/r3/index.html",
                "coverage": "major surveyed roads; Tokyo and Kanagawa records used",
                "lane_count_capability": "numeric lane count at road-condition survey unit",
                "direction_semantics": "both-directions total except official one-way sections",
                "temporal_reference": "2021 autumn",
                "machine_readable": True,
                "identifier_capability": "traffic survey basic section ID, route number and name",
                "geometry_capability": "official visualization GeoJSON keyed by census ID",
                "license": "MLIT website policy / PDL 1.0; attribution and modification notice required",
                "formal_status": "candidate_method_not_approved",
            },
            {
                "source_id": "PLATEAU_OTA_2025_CITYGML",
                "authority": "国土交通省 都市局 / 大田区",
                "official_dataset": "https://www.geospatial.jp/ckan/dataset/plateau-13111-ota-ku-2025",
                "coverage": "Ota Ward",
                "temporal_reference": "2025 edition; road thematic sources include 2021/2025 maps",
                "machine_readable": True,
                "road_gml_file_count": len(tran_names),
                "road_feature_count": plateau_road_count,
                "number_of_lanes_occurrence_count": plateau_lane_attribute_count,
                "lane_count_capability": "none in this delivered transportation dataset",
                "formal_status": "not_applicable_to_X1_lane_count",
            },
            {
                "source_id": "TOKYO_AND_OTA_ROAD_LEDGER_MAPS",
                "authority": "東京都建設局 / 大田区",
                "official_pages": [
                    "https://www.kensetsu.metro.tokyo.lg.jp/road/information/todoukensaku",
                    "https://www.city.ota.tokyo.jp/seikatsu/sumaimachinami/douro_kouen_kasen/douro/dourodaicho.html",
                ],
                "coverage": "administrator-specific roads",
                "lane_count_capability": "no bulk lane-count field established; plans emphasize road geometry/current width",
                "machine_readable": False,
                "temporal_reference": "map-specific/update-list dependent",
                "formal_status": "manual corroboration candidate only",
            },
            {
                "source_id": "GSI_AERIAL_PHOTO_ARCHIVE",
                "authority": "国土地理院",
                "official_page": "https://service.gsi.go.jp/map-photos/app/help",
                "coverage": "photo-dependent",
                "lane_count_capability": "visual observation only; GSI does not interpret photographed objects",
                "temporal_reference": "capture date available per photograph",
                "machine_readable": False,
                "formal_status": "independent visual corroboration candidate, not sole bulk donor",
            },
            {
                "source_id": "N13_NATIONAL_LAND_NUMERICAL_INFORMATION",
                "authority": "国土交通省",
                "lane_count_capability": "no exact directional lane-count donor field used by v17",
                "formal_status": "geometry/auxiliary evidence only under existing project policy",
            },
            {
                "source_id": "DRM_DATABASE",
                "authority": "一般財団法人日本デジタル道路地図協会",
                "lane_count_capability": "potentially available in licensed product",
                "formal_status": "prohibited by existing project external-source policy",
            },
        ],
        "conclusion": {
            "current_official_bulk_source_with_lane_count": "MLIT R3 Road Traffic Census",
            "immediately_formalizable_way_count": 0,
            "reason": "no approved v17 method; R3 is temporally older, and most matched counts are both-direction totals",
        },
    }

    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.catalog_output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"manifest": manifest["mlit_web_map_http_status_counts"], "catalog": catalog["conclusion"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
