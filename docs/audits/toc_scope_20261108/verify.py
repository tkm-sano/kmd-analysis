"""Read-only preservation/scope audit, writing only VALIDATION.json.

No historical runner, demand generator, optimizer or plotting code is executed.
"""

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from kmd_toc import HoldError, load_study, require_ready


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    baseline = json.loads((HERE / "BASELINE.json").read_text())
    plan = "research_plan_toc_three_objectives_faceted_20261108.docx"
    allowed = {"README.md", plan}
    failures = []
    changed = []
    for name, old in baseline["files"].items():
        path = ROOT / name
        if not path.is_file():
            failures.append("Removed pre-existing file: " + name)
        elif sha(path) != old["sha256"]:
            changed.append(name)
            if name not in allowed:
                failures.append("Unexpected pre-existing file change: " + name)
    if sha(HERE / "source_plan_original.docx") != baseline["files"][plan]["sha256"]:
        failures.append("Original plan backup mismatch")
    readme = (ROOT / "README.md").read_bytes()
    marker = "# 量子技術がEV配送の定時配達率".encode()
    old_readme = readme[readme.index(marker):]
    readme_preserved = hashlib.sha256(old_readme).hexdigest() == baseline["files"]["README.md"]["sha256"]
    if not readme_preserved:
        failures.append("Historical README body was modified")

    study = load_study(ROOT / "configs/toc_delivery/study.json")
    try:
        require_ready(study)
    except HoldError:
        pass
    else:
        failures.append("Unresolved execution was enabled")

    forbidden = re.compile(r"\b(?:EV|SOC|battery|charging|energy|Controlled.DC)\b|電池|充電|航続|電力量|エネルギー", re.I)
    if forbidden.search(readme[:readme.index(marker)].decode()):
        failures.append("Excluded premise in the active README introduction")
    for path in (ROOT / "src/kmd_toc").glob("*.py"):
        source = path.read_text()
        if forbidden.search(source):
            failures.append("Excluded term in active source: " + str(path.relative_to(ROOT)))
        tree = ast.parse(source)
        allowed_modules = {"fractions", "json", "math", "pathlib", "contracts"}
        for node in ast.walk(tree):
            modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                       else [node.module] if isinstance(node, ast.ImportFrom) else [])
            if any(module not in allowed_modules for module in modules):
                failures.append("Unexpected active import: " + str(modules))
    config_text = (ROOT / "configs/toc_delivery/study.json").read_text()
    if forbidden.search(config_text):
        failures.append("Excluded term in active configuration")
    spec = (ROOT / "docs/research/TOC_DELIVERY_SPEC.md").read_text()
    for paragraph in spec.split("\n\n"):
        if forbidden.search(paragraph) and not paragraph.startswith("除外事項："):
            failures.append("Excluded premise outside explicit exclusion paragraph")
    if study["rq"] not in spec or study["rq"] not in readme.decode():
        failures.append("RQ differs between active documents/config")
    with ZipFile(ROOT / plan) as current, ZipFile(HERE / "source_plan_original.docx") as old:
        if current.testzip() is not None:
            failures.append("Invalid DOCX archive")
        modified_parts = [name for name in old.namelist() if current.read(name) != old.read(name)]
        if modified_parts != ["word/document.xml"]:
            failures.append("Unexpected DOCX package changes: " + str(modified_parts))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        root = ET.fromstring(current.read("word/document.xml"))
        paragraphs = ["".join(x.text or "" for x in p.findall(".//w:t", ns))
                      for p in root.findall(".//w:p", ns)]
        if any(forbidden.search(p) for p in paragraphs):
            failures.append("Excluded premise in revised DOCX")
        if "RQ：" + study["rq"] not in paragraphs:
            failures.append("DOCX RQ mismatch")

    # Historical distribution mismatches are reported, never rewritten here.
    manifest = json.loads((ROOT / "reproducibility/release/GITHUB_DISTRIBUTION_MANIFEST.json").read_text())
    mismatches = []
    for record in manifest["files"]:
        name = record["distribution_path"]
        path = ROOT / name
        if path.is_file() and sha(path) != record["sha256"]:
            before = baseline["files"].get(name, {}).get("sha256")
            mismatches.append({"path": name, "manifest_sha256": record["sha256"],
                               "before_sha256": before, "after_sha256": sha(path),
                               "already_mismatched_before": before != record["sha256"]})
    if any(not item["already_mismatched_before"] for item in mismatches):
        failures.append("New historical distribution mismatch")

    results = json.loads((HERE / "TEST_RESULTS.json").read_text())
    if any(item["exit_code"] != 0 for item in results):
        failures.append("A selected contract/API/notebook check failed")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != baseline["head"]:
        failures.append("HEAD changed")
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() != baseline["branch"]:
        failures.append("Branch changed")
    record = {"scope_audit": "PASS" if not failures else "FAIL", "overall": "CONDITIONAL_COMPLETION",
              "baseline_files_checked": len(baseline["files"]), "changed_existing_files": sorted(changed),
              "preserved_existing_files": len(baseline["files"]) - len(changed),
              "historical_readme_body_preserved": readme_preserved,
              "docx_package_changed_parts": modified_parts,
              "historical_distribution_mismatches": mismatches,
              "selected_test_commands": len(results), "experiments": "NOT_RUN",
              "failures": failures}
    (HERE / "VALIDATION.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in record.items() if k != "historical_distribution_mismatches"}, ensure_ascii=False))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
