"""Reusable validation for final external-observation calibration artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from traffic_simulation.calibration import formalize_external_observation_inventory as subject


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, object]:
    errors: list[str] = []
    inventory = read_csv(subject.INVENTORY_CSV)
    observations = read_csv(subject.OBSERVATIONS_CSV)
    summary = json.loads(subject.SUMMARY_JSON.read_text(encoding="utf-8"))
    if len(inventory) != 9 or len({row["target_id"] for row in inventory}) != 9:
        errors.append("inventory does not contain nine unique targets")
    if len(observations) != 240:
        errors.append("final observation row count is not 240")
    if summary["counts"].get("direction_resolved") != 9:
        errors.append("direction resolved count is not nine")
    if summary["counts"].get("bidirectional_assignment_available") != 6:
        errors.append("bidirectional assignment count is not six")
    if summary["counts"].get("calibration_usable") != 5:
        errors.append("current calibration usable count is not five")
    route316 = [row for row in inventory if row["official_observation_section_id"] == "13403160320"]
    if len(route316) != 3:
        errors.append("Route 316 target count is not three")
    if any(row["direction_evidence_status"] != "RESOLVED_UP" for row in route316):
        errors.append("Route 316 direction is not RESOLVED_UP")
    if any(row["traffic_assignment_status"] != "REVIEW_REQUIRED"
           or row["calibration_usability_status"] != "REVIEW_REQUIRED" for row in route316):
        errors.append("Route 316 was made assignable or calibration usable")
    if any(float(row["normalized_observed_value"]) != float(row["raw_observed_value"])
           for row in observations):
        errors.append("observed values were apportioned or transformed")
    historical = [row for row in observations if row["observation_type"] == "HISTORICAL_EXTERNAL_VALIDATION"]
    if len(historical) != 48 or any(float(row["calibration_weight"]) != 0 for row in historical):
        errors.append("historical observation policy failed")
    schema_errors = subject.validate_schema(observations)
    errors.extend(f"schema: {error}" for error in schema_errors)
    manifest = json.loads(subject.MANIFEST_JSON.read_text(encoding="utf-8"))
    for group in ("input_hashes", "output_hashes"):
        for relative, expected in manifest[group].items():
            path = subject.REPOSITORY_ROOT / relative
            if not path.is_file() or sha256_file(path) != expected:
                errors.append(f"{group} mismatch: {relative}")
    if any(manifest["non_mutation_contract"].values()):
        errors.append("non-mutation contract failed")
    return {
        "status": "PASSED" if not errors else "FAILED",
        "error_count": len(errors), "errors": errors,
        "target_count": len(inventory), "observation_row_count": len(observations),
    }


def main() -> None:
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "PASSED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
