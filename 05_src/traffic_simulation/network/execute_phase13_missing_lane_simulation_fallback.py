"""Execute the approved Phase 13 simulation-only missing-lane fallback."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping, Sequence

from traffic_simulation.network.directional_lanes_v17 import (
    build_lane_production_artifact,
)
from traffic_simulation.network.simulation_lane_fallback_v17 import (
    DECISION_ID,
    DECISION_VERSION,
    SCENARIOS,
    build_simulation_collection,
    load_policy,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_json_gzip(path: Path, value: Mapping[str, Any]) -> None:
    canonical = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
            stream.write(canonical)


def _source_tags(input_path: Path, way_ids: set[int]) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for _event, element in ET.iterparse(input_path, events=("end",)):
        if element.tag == "way":
            way_id = int(element.attrib["id"])
            if way_id in way_ids:
                result[way_id] = {
                    item.attrib["k"]: item.attrib["v"]
                    for item in element.findall("tag")
                }
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    if set(result) != way_ids:
        raise RuntimeError(
            f"source Way mismatch: missing={sorted(way_ids - set(result))[:20]}"
        )
    return result


def execute(input_path: Path, output_directory: Path) -> dict[str, Any]:
    if output_directory.exists():
        raise FileExistsError(f"refusing to overwrite output: {output_directory}")
    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{output_directory.name}.", dir=output_directory.parent
        )
    )
    try:
        policy = load_policy()
        source_hash = _sha256(input_path)
        if source_hash != policy["fixed_binding"]["source_osm"]["sha256"]:
            raise RuntimeError("fixed source OSM hash mismatch")

        formal = build_lane_production_artifact(input_path, profile="formal")
        _write_json(temporary / "formal_directional_lane_after.json", formal)
        way_ids = {
            int(item["source_way_id"]) for item in formal["resolutions"]
        } | {int(item["source_way_id"]) for item in formal["blockers"]}
        tags = _source_tags(input_path, way_ids)
        ways = [
            {"source_way_id": way_id, "tags": tags[way_id]}
            for way_id in sorted(way_ids)
        ]

        manifests = {}
        collections = {}
        for scenario in sorted(SCENARIOS):
            collection = build_simulation_collection(
                ways,
                source_osm_hash=source_hash,
                scenario=scenario,
                policy=policy,
            )
            collections[scenario] = collection
            manifests[scenario] = collection["manifest"]
            _write_json_gzip(
                temporary / f"simulation_{scenario}.json.gz", collection
            )
            _write_json(
                temporary / f"manifest_{scenario}.json", collection["manifest"]
            )

        coverage = {
            "schema_version": 1,
            "decision_id": DECISION_ID,
            "decision_version": DECISION_VERSION,
            "source_way_count": len(way_ids),
            "by_scenario": {
                scenario: {
                    "eligible": manifest["assumed_way_count"],
                    "assigned": manifest["assumed_way_count"],
                    "simulation_unresolved": 0,
                    "class_calibrated": manifest["by_fallback_level"].get(
                        "class_directionality_calibrated_default", 0
                    ),
                    "global_fallback": manifest["by_fallback_level"].get(
                        "global_directionality_fallback", 0
                    ),
                    "formal_blockers_preserved": manifest[
                        "formal_blockers_preserved"
                    ],
                    "formal_source_usage": manifest["formal_source_usage_count"],
                    "conflicts_excluded": manifest["conflicts_excluded"],
                    "shared_unsupported_excluded": manifest[
                        "shared_unsupported_excluded"
                    ],
                    "out_of_scope_excluded": manifest["out_of_scope_excluded"],
                }
                for scenario, manifest in sorted(manifests.items())
            },
        }
        _write_json(temporary / "coverage.json", coverage)

        scenario_comparison = {
            "schema_version": 1,
            "delivery_simulation_executed": False,
            "network_input_assumptions": {
                scenario: {
                    "semantic_sha256": collections[scenario]["semantic_sha256"],
                    "assumed_way_count": manifests[scenario]["assumed_way_count"],
                    "assumed_lane_totals": manifests[scenario][
                        "assumed_lane_totals"
                    ],
                    "by_cluster": manifests[scenario]["by_cluster"],
                    "by_highway": manifests[scenario]["by_highway"],
                    "by_fallback_level": manifests[scenario][
                        "by_fallback_level"
                    ],
                }
                for scenario in sorted(SCENARIOS)
            },
        }
        _write_json(temporary / "scenario_comparison.json", scenario_comparison)
        _write_json(
            temporary / "approved_decision_reference.json",
            {
                "decision_id": DECISION_ID,
                "decision_version": DECISION_VERSION,
                "policy_id": policy["policy_id"],
                "policy_version": policy["policy_version"],
                "source_osm_sha256": source_hash,
                "calibration_population_sha256": policy["fixed_binding"][
                    "calibration"
                ]["semantic_sha256"],
            },
        )
        os.replace(temporary, output_directory)
    except Exception:
        for child in temporary.iterdir():
            child.unlink()
        temporary.rmdir()
        raise
    return coverage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = execute(args.input, args.output_directory)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
