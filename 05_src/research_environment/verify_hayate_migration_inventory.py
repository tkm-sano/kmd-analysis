#!/usr/bin/env python3
"""Verify a transferred research tree against its Mac-side migration inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    payload = json.loads(args.inventory.read_text(encoding="utf-8"))
    failures: list[dict[str, str]] = []
    checked = 0
    for record in payload["records"]:
        path = root / record["path"]
        expected_type = record["type"]
        if expected_type == "symlink":
            if not path.is_symlink():
                failures.append({"path": record["path"], "reason": "missing_or_not_symlink"})
                continue
            actual = hashlib.sha256(os.readlink(path).encode()).hexdigest()
        else:
            if not path.is_file():
                failures.append({"path": record["path"], "reason": "missing_or_not_file"})
                continue
            actual = sha256_file(path)
        checked += 1
        if actual != record["sha256"]:
            failures.append({"path": record["path"], "reason": "sha256_mismatch"})
    result = {"checked": checked, "expected": len(payload["records"]), "failures": failures}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures or checked != len(payload["records"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
