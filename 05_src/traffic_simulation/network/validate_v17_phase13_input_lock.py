"""Validate the immutable Phase 12 publication consumed by Phase 13."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


DEFAULT_LOCK = REPOSITORY_ROOT / (
    "reproducibility/config/traffic_simulation/v17_phase13_input_lock.yml"
)


class Phase13InputLockError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_input_lock(path: Path = DEFAULT_LOCK) -> dict[str, Any]:
    lock = yaml.safe_load(path.read_text(encoding="utf-8"))
    if lock.get("status") != "fixed":
        raise Phase13InputLockError("Phase 13 input lock is not fixed")
    completion = REPOSITORY_ROOT / lock["phase12_completion"]["path"]
    if _sha256(completion) != lock["phase12_completion"]["sha256"]:
        raise Phase13InputLockError("Phase 12 completion hash mismatch")
    report = REPOSITORY_ROOT / lock["determinism_report"]["path"]
    if _sha256(report) != lock["determinism_report"]["sha256"]:
        raise Phase13InputLockError("determinism report hash mismatch")
    publication = lock["publication"]
    if publication.get("source_run") != "run_1" or publication.get("locked") is not True:
        raise Phase13InputLockError("publication source is not locked to run_1")
    root = REPOSITORY_ROOT / publication["root"]
    artifacts = publication["artifacts"]
    actual_paths = sorted(
        item.relative_to(root).as_posix() for item in root.rglob("*") if item.is_file()
    )
    expected_paths = sorted(item["path"] for item in artifacts)
    if actual_paths != expected_paths:
        raise Phase13InputLockError("published artifact set mismatch")
    for item in artifacts:
        artifact = root / item["path"]
        if _sha256(artifact) != item["byte_sha256"]:
            raise Phase13InputLockError(f"published artifact hash mismatch: {item['path']}")
        if "semantic_sha256" in item:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            if payload.get("semantic_sha256") != item["semantic_sha256"]:
                raise Phase13InputLockError(
                    f"semantic hash field mismatch: {item['path']}"
                )
    return {
        "phase13_input_lock": "passed",
        "source_run": publication["source_run"],
        "artifact_count": len(artifacts),
        "complete_blocker_inventory": "fixed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_input_lock(args.input_lock), sort_keys=True))
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        print(json.dumps({"phase13_input_lock": "failed", "error": str(error)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
