#!/usr/bin/env python3
"""Read-only verification of research specification v1 against a fixed trust anchor.

Changing v1 requires explicit user authorization and a new version, never a new
digest calculated from whatever happens to be present. This is a local integrity
check, not protection against someone changing this program and the CI together.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = "297be6f6be2be000e627480af189bad1533a385bf269b25fc22dc4922b3de9be"
SPEC_PATH = "docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md"
MANIFEST_PATH = "docs/frozen/FREEZE_MANIFEST.json"
ROOT = Path(__file__).resolve().parents[1]


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def verify(root=ROOT):
    root = Path(root)
    errors = []
    raw = None
    actual = None
    try:
        raw = (root / SPEC_PATH).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != EXPECTED_SHA256:
            errors.append({"file": SPEC_PATH, "reason": "SHA256_MISMATCH",
                           "expected": EXPECTED_SHA256, "actual": actual})
    except OSError as error:
        errors.append({"file": SPEC_PATH, "reason": "SPEC_UNREADABLE", "detail": str(error)})
    try:
        manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"),
                              object_pairs_hook=_unique)
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        expected = {"schema_version": 1, "specification_version": "v1",
                    "file_path": SPEC_PATH, "sha256": EXPECTED_SHA256,
                    "freeze_date": "2026-11-20", "verification_result": "PASS"}
        for key, value in expected.items():
            if manifest.get(key) != value:
                errors.append({"file": MANIFEST_PATH, "reason": "MANIFEST_FIELD_MISMATCH", "field": key})
        content = manifest.get("content_utf8")
        if not isinstance(content, str) or hashlib.sha256(content.encode("utf-8")).hexdigest() != EXPECTED_SHA256:
            errors.append({"file": MANIFEST_PATH, "reason": "MANIFEST_CONTENT_MISMATCH"})
        elif raw is not None and content.encode("utf-8") != raw:
            errors.append({"file": MANIFEST_PATH, "reason": "MANIFEST_SPEC_BYTES_DIFFER"})
        if raw is not None and manifest.get("byte_count") != len(raw):
            errors.append({"file": MANIFEST_PATH, "reason": "MANIFEST_SIZE_MISMATCH"})
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        errors.append({"file": MANIFEST_PATH, "reason": "MANIFEST_UNREADABLE", "detail": str(error)})
    return {"status": "FAIL" if errors else "PASS", "specification_version": "v1",
            "expected_sha256": EXPECTED_SHA256, "actual_sha256": actual,
            "files_requiring_attention": sorted({e["file"] for e in errors}), "errors": errors,
            "scope": "frozen specification integrity only; not implementation conformance"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = verify(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
