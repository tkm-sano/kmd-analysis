#!/usr/bin/env python3
"""Build a byte-level inventory for the Mac-to-Hayate research migration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


EPHEMERAL_NAMES = {
    ".DS_Store",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def category(relative: Path) -> str:
    parts = relative.parts
    if parts and parts[0] == ".git":
        return "git_repository_metadata"
    if parts[:2] == ("03_data", "raw"):
        return "raw_source_data"
    if parts[:2] == ("03_data", "processed"):
        return "processed_research_data"
    if parts[:2] == ("reproducibility", "outputs"):
        return "reproducibility_and_simulation_output"
    if parts and parts[0] in {"06_outputs", "07_presentations", "08_documents"}:
        return "research_output"
    if parts and parts[0] in {"tmp", "output"}:
        return "temporary_review_required"
    return "repository_source_and_metadata"


def git_text(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    )
    return completed.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output.resolve()
    if not (root / ".git").exists():
        raise SystemExit(f"not a Git working tree: {root}")
    if output != root and root not in output.parents:
        raise SystemExit("output must be inside root so its exclusion is auditable")
    output.mkdir(parents=True, exist_ok=True)
    output_relative = output.relative_to(root)
    excluded_names = {
        "migration_inventory.json",
        "migration_inventory.csv",
        "migration_inventory.json.sha256",
        "git_status_porcelain.txt",
        "git_working_tree.patch",
    }

    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in EPHEMERAL_NAMES for part in relative.parts):
            continue
        if relative.parent == output_relative and relative.name in excluded_names:
            continue
        if path.is_symlink():
            target = os.readlink(path)
            records.append(
                {
                    "path": relative.as_posix(),
                    "type": "symlink",
                    "size_bytes": len(target.encode()),
                    "sha256": hashlib.sha256(target.encode()).hexdigest(),
                    "symlink_target": target,
                    "category": category(relative),
                }
            )
        elif path.is_file():
            records.append(
                {
                    "path": relative.as_posix(),
                    "type": "file",
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "symlink_target": "",
                    "category": category(relative),
                }
            )

    category_counts = Counter(str(record["category"]) for record in records)
    category_bytes = Counter()
    for record in records:
        category_bytes[str(record["category"])] += int(record["size_bytes"])

    status = git_text(root, "status", "--porcelain=v1", "--untracked-files=all")
    diff = git_text(root, "diff", "--binary", "HEAD")
    payload = {
        "schema_version": "1.0.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root_recorded_as": ".",
        "intended_destination_root": "/home/takuma/research_canonical/repo/research",
        "excluded_ephemeral_names": sorted(EPHEMERAL_NAMES),
        "file_count": len(records),
        "total_bytes": sum(int(record["size_bytes"]) for record in records),
        "category_counts": dict(sorted(category_counts.items())),
        "category_bytes": dict(sorted(category_bytes.items())),
        "git": {
            "head": git_text(root, "rev-parse", "HEAD").strip(),
            "status_sha256": hashlib.sha256(status.encode()).hexdigest(),
            "status_line_count": len(status.splitlines()),
            "working_tree_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
            "working_tree_is_clean": not bool(status),
        },
        "records": records,
    }

    (output / "migration_inventory.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "migration_inventory.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["path", "type", "size_bytes", "sha256", "symlink_target", "category"],
        )
        writer.writeheader()
        writer.writerows(records)
    (output / "git_status_porcelain.txt").write_text(status, encoding="utf-8")
    (output / "git_working_tree.patch").write_text(diff, encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("file_count", "total_bytes", "category_counts", "category_bytes", "git")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
