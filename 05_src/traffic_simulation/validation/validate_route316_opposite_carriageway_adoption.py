"""Validate generated Route 316 opposite-carriageway review artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from traffic_simulation.calibration import review_route316_opposite_carriageway_adoption as subject


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate() -> dict[str, object]:
    errors: list[str] = []
    review = read_csv(subject.REVIEW_CSV)
    edges = read_csv(subject.EDGE_CSV)
    targets = read_csv(subject.TARGET_CSV)
    if len(review) != 3:
        errors.append("review target count is not 3")
    if len(edges) != 4:
        errors.append("alternate edge count is not 4")
    if len(targets) != 3:
        errors.append("target summary count is not 3")
    if any(int(row["selected_edge_count"]) != 7 for row in review):
        errors.append("selected edge count is not 7")
    if any(row["adoption_status"] != "REVIEW_REQUIRED" for row in review + targets):
        errors.append("adoption status is inconsistent")
    if any(row["traffic_assignment_status"] != "REVIEW_REQUIRED" for row in review + targets):
        errors.append("traffic assignment was made available")
    if any(row["route_identity_status"] != "PASS" for row in review + edges):
        errors.append("route identity failed")
    if any(row["topology_status"] != "PASS" for row in review):
        errors.append("topology failed")
    if any(row["contamination_status"] != "PASS" for row in review + edges):
        errors.append("contamination failed")
    manifest = json.loads(subject.MANIFEST_JSON.read_text(encoding="utf-8"))
    for group in ("input_hashes", "output_hashes"):
        for relative, expected in manifest[group].items():
            path = subject.REPOSITORY_ROOT / relative
            if not path.is_file() or sha256_file(path) != expected:
                errors.append(f"{group} mismatch: {relative}")
    if any(manifest["non_mutation_contract"][key] for key in (
        "formal_mapping_changed", "direction_artifacts_changed", "network_changed",
        "threshold_changed", "traffic_counts_apportioned",
    )):
        errors.append("non-mutation contract failed")
    return {
        "status": "PASSED" if not errors else "FAILED",
        "error_count": len(errors), "errors": errors,
        "target_count": len(targets), "alternate_edge_count": len(edges),
    }


def main() -> None:
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "PASSED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
