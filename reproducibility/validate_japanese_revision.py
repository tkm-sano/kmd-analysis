"""Validate that Japanese copy changes prose only."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OLD = ROOT / "quantum_transport_reproducibility_audit_revised.ipynb"
NEW = ROOT / "quantum_transport_reproducibility_audit_japanese_revised.ipynb"
OUT = ROOT / "outputs" / "tables" / "japanese_revision_validation.csv"


def sources(nb, kind):
    return ["".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == kind]


def sha(items):
    return hashlib.sha256("\n\0\n".join(items).encode()).hexdigest()


old = json.loads(OLD.read_text())
new = json.loads(NEW.read_text())
old_code, new_code = sources(old, "code"), sources(new, "code")
old_md, new_md = "\n".join(sources(old, "markdown")), "\n".join(sources(new, "markdown"))
ids = lambda nb: [c.get("metadata", {}).get("audit_cell_id") for c in nb["cells"]]
math = lambda text: re.findall(r"\$\$(.*?)\$\$|(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)", text, re.S)
status = lambda text: set(re.findall(r"`([A-Z][A-Z0-9_]+)`", text))
filenames = lambda text: set(re.findall(r"[A-Za-z0-9_()\-]+\.(?:csv|json|pptx|ipynb|txt|html)", text))
protected_numbers = ["25", "50", "100", "1.25", "81.2", "2,000", "480", "1,000", "20260711", "0.0%", "33.5185%", "64.4444%", "10.6914%", "33.2950%", "15.3021%"]

checks = [
    ("cell_count", len(old["cells"]) == len(new["cells"]), len(old["cells"]), len(new["cells"])),
    ("code_cell_count", len(old_code) == len(new_code), len(old_code), len(new_code)),
    ("code_source_sha256", sha(old_code) == sha(new_code), sha(old_code), sha(new_code)),
    ("cell_id_sequence", ids(old) == ids(new), "identical sequence", "identical sequence" if ids(old) == ids(new) else "difference detected"),
    ("math_expressions", math(old_md) == math(new_md), len(math(old_md)), len(math(new_md))),
    ("original_status_codes_retained", status(old_md).issubset(status(new_md)), sorted(status(old_md)), sorted(status(new_md))),
    ("original_filenames_retained", filenames(old_md).issubset(filenames(new_md)), sorted(filenames(old_md)), sorted(filenames(new_md))),
    ("protected_numeric_literals", all(x in new_md for x in protected_numbers), protected_numbers, [x for x in protected_numbers if x in new_md]),
    ("code_outputs_unchanged", [c.get("outputs", []) for c in old["cells"] if c.get("cell_type") == "code"] == [c.get("outputs", []) for c in new["cells"] if c.get("cell_type") == "code"], "identical", "identical"),
]
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["check_id", "status", "original", "revised"])
    writer.writeheader()
    for check_id, passed, before, after in checks:
        writer.writerow({"check_id": check_id, "status": "PASS" if passed else "FAIL", "original": str(before), "revised": str(after)})

failed = [row[0] for row in checks if not row[1]]
if failed:
    raise SystemExit("Validation failed: " + ", ".join(failed))
print(f"{len(checks)} checks passed; code SHA-256: {sha(old_code)}")
