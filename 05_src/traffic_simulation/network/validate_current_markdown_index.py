from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = ROOT / "reproducibility/indexes/research_repository_index_v17.yml"
INVENTORY_PATH = ROOT / "reproducibility/indexes/markdown_inventory_v17.yml"
AUTHORITY_PATH = ROOT / "reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml"
DATE_PREFIX = re.compile(r"^(\d{8})_(\d{8})_.+\.md$")
METADATA_KEYS = ("Document ID", "Role", "Lifecycle", "Created", "Last Updated", "Current Authority")
LINK_PATTERN = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "data:")

RETIRED_CURRENT_PATHS = (
    "docs/research_cli.md",
    "reproducibility/indexes/research_repository_map_v17.md",
    "05_src/traffic_simulation/simulation_model_development_and_vv.md",
    "05_src/traffic_simulation/demand/baseline_demand_and_comparator.md",
    "05_src/traffic_simulation/specifications/15_formal_completion_three_tier_policy_v17.md",
    "05_src/traffic_simulation/specifications/16_network_completion_pipeline_v17.md",
)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return result.stdout


def repository_files() -> list[Path]:
    raw = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return sorted(
        (ROOT / value.decode("utf-8") for value in raw.split(b"\0") if value),
        key=lambda path: path.as_posix(),
    )


def markdown_files() -> list[Path]:
    return [path for path in repository_files() if path.is_file() and path.suffix.lower() == ".md"]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def metadata(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key in METADATA_KEYS:
        match = re.search(rf"(?m)^{re.escape(key)}:\s*`?([^`\n]+?)`?\s{{0,2}}$", text)
        if match:
            values[key] = match.group(1).strip()
    return values


def title(text: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else "UNKNOWN"


def git_history(path: str) -> dict[str, str]:
    lines = [
        line.split("|", 1)
        for line in run_git("log", "--follow", "--format=%ad|%H", "--date=short", "--", path).splitlines()
        if "|" in line
    ]
    if not lines:
        return {
            "created": "UNKNOWN",
            "updated": "UNKNOWN",
            "first_git_commit": "UNKNOWN",
            "latest_git_commit": "UNKNOWN",
        }
    latest_date, latest_commit = lines[0]
    created_date, first_commit = lines[-1]
    return {
        "created": created_date,
        "updated": latest_date,
        "first_git_commit": first_commit,
        "latest_git_commit": latest_commit,
    }


def resolve_markdown_link(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split(maxsplit=1)[0].strip("'\"")
    if not target or target.startswith("#") or target.startswith(EXTERNAL_PREFIXES):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return None
    candidate = (source.parent / target).resolve()
    return candidate if candidate.suffix.lower() == ".md" else None


def markdown_relationships(paths: list[Path]) -> tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
    path_set = {path.resolve() for path in paths}
    references_to: dict[str, set[str]] = defaultdict(set)
    referenced_by: dict[str, set[str]] = defaultdict(set)
    broken: list[str] = []
    for source in paths:
        source_rel = relative(source)
        for raw_target in LINK_PATTERN.findall(read_text(source)):
            target = resolve_markdown_link(source, raw_target)
            if target is None:
                continue
            if not target.is_file():
                broken.append(f"{source_rel}: {raw_target}")
                continue
            target_rel = relative(target)
            references_to[source_rel].add(target_rel)
            if target in path_set:
                referenced_by[target_rel].add(source_rel)
    return (
        {key: sorted(value) for key, value in references_to.items()},
        {key: sorted(value) for key, value in referenced_by.items()},
        sorted(broken),
    )


def classify(path: str, important: dict[str, dict], text: str) -> tuple[str, str, bool]:
    if path in important:
        item = important[path]
        return item["role"], item["lifecycle"], False
    if path == "RESEARCH_OVERVIEW.md":
        return "PRIMARY_ENTRY", "CURRENT", False
    name = Path(path).name.lower()
    generated = (
        (path.startswith("03_data/processed/") and name != "readme.md")
        or path.startswith("06_outputs/")
        or path.startswith("reproducibility/outputs/")
        or name.endswith("_report.md")
    )
    if generated:
        return "GENERATED_REPORT", "GENERATED", True
    if path.startswith("legacy/"):
        return "HISTORICAL_REFERENCE", "HISTORICAL", False
    if path in {
        "README_v2.md",
        "RESEARCH_STATUS.md",
        "2-3_20260823_PARTIAL_交通量較正.md",
        "05_src/traffic_simulation/specifications/14_formal_network_completion_policy_v17.md",
    }:
        return "HISTORICAL_REFERENCE", "SUPERSEDED", False
    if "complete" in name or "histor" in text[:1000].lower() or "legacy" in name:
        return "HISTORICAL_REFERENCE", "HISTORICAL", False
    if name == "readme.md":
        return "REPOSITORY_REFERENCE", "CURRENT", False
    if "specification" in name or "policy" in name or "/specifications/" in path:
        return "NORMATIVE_SPECIFICATION", "HISTORICAL", False
    return "RESEARCH_NOTE", "CURRENT", False


def write_inventory(index: dict) -> None:
    md_paths = markdown_files()
    md_rel = [relative(path) for path in md_paths]
    important = {item["path"]: item for item in index["important_markdown"]}
    references_to, markdown_referenced_by, broken = markdown_relationships(md_paths)
    all_text = {relative(path): read_text(path) for path in repository_files() if path.is_file()}
    records = []
    for path, path_rel in zip(md_paths, md_rel):
        text = read_text(path)
        role, lifecycle, generated = classify(path_rel, important, text)
        history = git_history(path_rel)
        literal_references = {
            source
            for source, source_text in all_text.items()
            if source not in {path_rel, relative(INVENTORY_PATH)} and path_rel in source_text
        }
        ref_by = sorted(literal_references | set(markdown_referenced_by.get(path_rel, [])))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hash_references = [
            source for source, source_text in all_text.items() if source != path_rel and digest in source_text
        ]
        portal_dependency = any(
            source.startswith("research_portal/") or source.startswith("reproducibility/config/research_portal/")
            for source in ref_by
        )
        validator_dependency = any(
            "validat" in source.lower() or "/test" in source.lower() for source in ref_by
        )
        fixed_name = path.name.lower() == "readme.md" or path_rel == "RESEARCH_OVERVIEW.md"
        safe_to_rename = bool(
            lifecycle == "CURRENT"
            and not generated
            and not hash_references
            and not fixed_name
            and not portal_dependency
            and not validator_dependency
        )
        records.append(
            {
                "path": path_rel,
                "filename": path.name,
                "title": title(text),
                "role": role,
                "lifecycle": lifecycle,
                "current": lifecycle == "CURRENT",
                "authoritative": role == "CURRENT_NORMATIVE",
                "generated": generated,
                **history,
                "referenced_by": ref_by,
                "references_to": references_to.get(path_rel, []),
                "safe_to_rename": safe_to_rename,
                "hash_bound": bool(hash_references),
                "hash_references": sorted(hash_references),
                "portal_dependency": portal_dependency,
                "validator_dependency": validator_dependency,
            }
        )
    payload = {
        "schema_version": 1,
        "inventory_id": "MARKDOWN-INVENTORY-V17",
        "date_authority": "git_log_follow",
        "unknown_policy": "UNKNOWN means no Git history was available; no filesystem mtime was used.",
        "markdown_count": len(records),
        "broken_internal_markdown_links_at_generation": broken,
        "documents": records,
    }
    INVENTORY_PATH.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8"
    )


def validate(index: dict) -> dict:
    errors: list[str] = []
    manual_review: list[str] = []
    important = index.get("important_markdown", [])
    priorities = [item.get("priority") for item in important]
    document_ids = [item.get("document_id") for item in important]
    if len(priorities) != len(set(priorities)):
        errors.append("duplicate important_markdown priority")
    if len(document_ids) != len(set(document_ids)):
        errors.append("duplicate current document_id")
    for item in important:
        path = ROOT / item["path"]
        if not path.is_file():
            errors.append(f"missing important Markdown: {item['path']}")
            continue
        values = metadata(read_text(path))
        expected_metadata = {
            "Document ID": item["document_id"],
            "Role": item["role"],
            "Lifecycle": item["lifecycle"],
            "Created": item["created"],
            "Last Updated": item["updated"],
        }
        for key, expected in expected_metadata.items():
            if values.get(key) != expected:
                errors.append(f"metadata mismatch {item['path']} {key}: {values.get(key)!r} != {expected!r}")
        if not values.get("Current Authority"):
            errors.append(f"missing Current Authority metadata: {item['path']}")
        if item["naming_policy"] == "dated_canonical":
            match = DATE_PREFIX.match(path.name)
            expected_prefix = item["created"].replace("-", "") + "_" + item["updated"].replace("-", "")
            if not match or "_".join(match.groups()) != expected_prefix:
                errors.append(f"filename date mismatch: {item['path']}")
        history = git_history(item["path"])
        if history["created"] == "UNKNOWN":
            manual_review.append(f"Git history unavailable until commit: {item['path']}")
        else:
            if history["created"] != item["created"]:
                errors.append(f"Git created mismatch {item['path']}: {history['created']} != {item['created']}")
            dirty = bool(run_git("status", "--porcelain", "--", item["path"]).strip())
            if dirty:
                manual_review.append(f"Git latest update pending commit: {item['path']}")
            elif history["updated"] != item["updated"]:
                errors.append(f"Git updated mismatch {item['path']}: {history['updated']} != {item['updated']}")

    md_paths = markdown_files()
    _, _, broken = markdown_relationships(md_paths)
    errors.extend(f"broken Markdown link: {item}" for item in broken)

    if not INVENTORY_PATH.is_file():
        errors.append(f"missing Markdown inventory: {relative(INVENTORY_PATH)}")
    else:
        inventory = yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))
        indexed = {item["path"] for item in inventory.get("documents", [])}
        actual = {relative(path) for path in md_paths}
        if indexed != actual:
            errors.append(
                f"Markdown inventory coverage mismatch: missing={sorted(actual-indexed)} stale={sorted(indexed-actual)}"
            )

    searchable = {
        relative(path): read_text(path)
        for path in repository_files()
        if path.is_file() and relative(path) != relative(Path(__file__))
    }
    for retired in RETIRED_CURRENT_PATHS:
        users = [source for source, text in searchable.items() if retired in text]
        if users:
            errors.append(f"retired current path still referenced: {retired} by {users}")

    authority = yaml.safe_load(AUTHORITY_PATH.read_text(encoding="utf-8"))
    accepted = authority["accepted_run"]
    network = ROOT / accepted["network_file"]
    actual_sha = hashlib.sha256(network.read_bytes()).hexdigest() if network.is_file() else "MISSING"
    if actual_sha != accepted["network_sha256"]:
        errors.append("accepted network SHA-256 mismatch")
    acceptance_path = ROOT / accepted["acceptance_artifact"]
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8")) if acceptance_path.is_file() else {}
    if acceptance.get("FORMAL_NETWORK_ACCEPTED") is not True:
        errors.append("FORMAL_NETWORK_ACCEPTED is not true")

    result = {
        "current_markdown_index": "passed" if not errors else "failed",
        "important_markdown": len(important),
        "all_markdown": len(md_paths),
        "broken_internal_markdown_links": len(broken),
        "duplicate_current_document_ids": len(document_ids) - len(set(document_ids)),
        "accepted_network_sha256": actual_sha,
        "formal_network_accepted": acceptance.get("FORMAL_NETWORK_ACCEPTED"),
        "manual_review": manual_review,
        "errors": errors,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-inventory", action="store_true")
    args = parser.parse_args()
    index = yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8"))
    if args.write_inventory:
        write_inventory(index)
    result = validate(index)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["current_markdown_index"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
