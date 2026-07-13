"""Audit helpers used by the submission notebook.

The helpers contain no study results. They inspect files, calculate hashes,
derive tables from executed objects, and record validation outcomes.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import inspect
import json
import os
import platform
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_repository_root(start: Path) -> Path:
    """Find a repository root by durable sentinels, or raise clearly."""
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists() and (candidate / "03_data").is_dir():
            return candidate
    raise FileNotFoundError(
        f"Repository root not found above {start}; expected .git and 03_data."
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_information(root: Path) -> dict[str, object]:
    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    status = run("status", "--porcelain")
    return {
        "git_commit": run("rev-parse", "HEAD"),
        "git_branch": run("branch", "--show-current"),
        "git_dirty": bool(status),
        "git_status_porcelain": status,
    }


def preflight_check(
    root: Path,
    output_root: Path,
    required_files: dict[str, tuple[Path, list[str] | None]],
    required_modules: list[str],
) -> pd.DataFrame:
    """Run all preflight checks, collecting every failure before returning."""
    rows: list[dict[str, object]] = []

    def record(check_id: str, item: str, ok: bool, detail: str) -> None:
        rows.append(
            {
                "check_id": check_id,
                "item": item,
                "status": "PASS" if ok else "FAIL",
                "detail": detail,
            }
        )

    for directory in [root / "03_data", root / "05_src", root / "02_literature"]:
        record("PREFLIGHT-DIR", str(directory.relative_to(root)), directory.is_dir(), "required directory")

    for input_id, (path, required_columns) in required_files.items():
        exists = path.is_file()
        display_path = str(path.relative_to(root)) if path.is_relative_to(root) else path.name
        record("PREFLIGHT-FILE", input_id, exists, display_path)
        if exists and required_columns is not None:
            try:
                observed = list(pd.read_csv(path, nrows=0).columns)
                missing = sorted(set(required_columns) - set(observed))
                record(
                    "PREFLIGHT-COLUMNS",
                    input_id,
                    not missing,
                    f"missing={missing}; observed_columns={len(observed)}",
                )
            except Exception as error:  # audit result, not silent recovery
                record("PREFLIGHT-COLUMNS", input_id, False, repr(error))

    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            record("PREFLIGHT-MODULE", module_name, True, "import succeeded")
        except Exception as error:
            record("PREFLIGHT-MODULE", module_name, False, repr(error))

    record(
        "PREFLIGHT-PYTHON",
        platform.python_version(),
        tuple(map(int, platform.python_version_tuple())) >= (3, 11, 0),
        "Python >= 3.11 required",
    )
    try:
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_root, delete=True) as handle:
            handle.write(b"audit-write-test")
        display_output = str(output_root.relative_to(root)) if output_root.is_relative_to(root) else output_root.name
        record("PREFLIGHT-WRITE", display_output, True, "write/delete succeeded")
    except Exception as error:
        record("PREFLIGHT-WRITE", str(output_root), False, repr(error))
    try:
        info = git_information(root)
        record("PREFLIGHT-GIT", ".", True, json.dumps(info, ensure_ascii=False))
    except Exception as error:
        record("PREFLIGHT-GIT", str(root), False, repr(error))
    return pd.DataFrame(rows)


def package_versions(packages: list[str]) -> pd.DataFrame:
    rows = []
    for package in packages:
        try:
            version = importlib.metadata.version(package)
            status = "AVAILABLE"
        except importlib.metadata.PackageNotFoundError:
            version = ""
            status = "MISSING"
        rows.append({"package": package, "version": version, "status": status})
    return pd.DataFrame(rows)


def extract_slide_text(pptx_path: Path) -> pd.DataFrame:
    namespace = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    with ZipFile(pptx_path) as archive:
        names = sorted(
            (
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ),
            key=lambda name: int(name.split("slide")[-1].split(".")[0]),
        )
        rows = []
        for number, name in enumerate(names, 1):
            root = ET.fromstring(archive.read(name))
            text = [
                (node.text or "").strip()
                for node in root.findall(".//a:t", namespace)
                if (node.text or "").strip()
            ]
            rows.append(
                {
                    "slide_number": number,
                    "slide_title": text[0] if text else "",
                    "slide_text": " | ".join(text),
                }
            )
    return pd.DataFrame(rows)


def provenance_table(specifications: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    for spec in specifications:
        path = Path(spec["processed_file"])
        exists = path.is_file()
        observed_hash = sha256_file(path) if exists else ""
        expected_hash = str(spec.get("expected_sha256", "") or "")
        if not exists:
            hash_status = "FILE_MISSING"
        elif not expected_hash:
            hash_status = "EXPECTED_HASH_MISSING"
        elif observed_hash == expected_hash:
            hash_status = "MATCH"
        else:
            hash_status = "MISMATCH"
        if exists and path.suffix.lower() == ".csv":
            frame = pd.read_csv(path)
            row_count, column_count = frame.shape
        else:
            row_count = column_count = np.nan
        row = dict(spec)
        try:
            repository_root = find_repository_root(path.parent)
            row["processed_file"] = str(path.relative_to(repository_root))
        except (FileNotFoundError, ValueError):
            row["processed_file"] = path.name
        row.update(
            {
                "row_count": row_count,
                "column_count": column_count,
                "observed_sha256": observed_hash,
                "hash_status": hash_status,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_data_dictionary(table_map: dict[str, pd.DataFrame]) -> pd.DataFrame:
    units = {
        "latitude": "decimal degrees",
        "longitude": "decimal degrees",
        "distance": "km",
        "range": "km",
        "demand": "kg",
        "payload": "kg",
        "time": "minutes",
        "duration": "minutes",
        "speed": "km/h",
        "power": "kW",
        "battery": "kWh or ratio; see column",
        "rate": "proportion [0,1]",
        "seed": "integer identifier",
        "count": "records",
    }
    rows = []
    for table_name, frame in table_map.items():
        for column in frame.columns:
            lower = column.lower()
            unit = next((value for key, value in units.items() if key in lower), "dimensionless/text")
            allowed = ""
            if "latitude" in lower:
                allowed = "[-90, 90]"
            elif "longitude" in lower:
                allowed = "[-180, 180]"
            elif "rate" in lower or "ratio" in lower:
                allowed = "[0, 1] unless explicitly percentage"
            elif any(key in lower for key in ["distance", "demand", "payload", "time", "count"]):
                allowed = ">= 0"
            rows.append(
                {
                    "table_name": table_name,
                    "column_name": column,
                    "description": column.replace("_", " "),
                    "data_type": str(frame[column].dtype),
                    "unit": unit,
                    "allowed_range": allowed,
                    "missing_value_policy": "Allowed only when not evaluated/not available; audited by table tests",
                    "source": "frozen input" if table_name.startswith("input_") else "generated",
                    "generated_by": "source module or notebook",
                    "used_in": "scenario synthesis, constraint evaluation, or audit",
                }
            )
    return pd.DataFrame(rows)


def function_registry(functions: list[object], root: Path, git_commit: str) -> pd.DataFrame:
    rows = []
    for function in functions:
        source_file = Path(inspect.getsourcefile(function) or "")
        rows.append(
            {
                "function_name": function.__name__,
                "module_path": str(source_file.relative_to(root)),
                "purpose": (inspect.getdoc(function) or "").split("\n")[0],
                "input_tables": "See function signature and notebook call",
                "input_columns": "Validated by implementation",
                "output_tables": "See notebook assignment",
                "output_columns": "Validated after generation",
                "deterministic_or_stochastic": "stochastic with explicit seed" if any(x in function.__name__ for x in ["generate", "bootstrap"]) else "deterministic",
                "random_seed": "Explicit in notebook/arguments where applicable",
                "formula_or_algorithm": function.__name__.replace("_", " "),
                "validation": "dynamic notebook tests and stored-result comparison",
                "source_file_sha256": sha256_file(source_file),
                "git_commit": git_commit,
            }
        )
    return pd.DataFrame(rows)


def compare_frames(left: pd.DataFrame, right: pd.DataFrame) -> tuple[bool, str]:
    if list(left.columns) != list(right.columns) or left.shape != right.shape:
        return False, f"shape/columns differ: {left.shape} vs {right.shape}"
    for column in left.columns:
        if pd.api.types.is_numeric_dtype(left[column]) and not pd.api.types.is_bool_dtype(left[column]):
            equal = np.allclose(
                pd.to_numeric(left[column], errors="coerce"),
                pd.to_numeric(right[column], errors="coerce"),
                rtol=1e-10,
                atol=1e-10,
                equal_nan=True,
            )
        else:
            equal = left[column].astype("string").fillna("<NA>").equals(
                right[column].astype("string").fillna("<NA>")
            )
        if not equal:
            return False, f"first differing column: {column}"
    return True, "all rows and columns equivalent after explicit NA/type normalization"


def validation_row(
    test_id: str,
    description: str,
    expected: object,
    observed: object,
    condition: bool,
    severity: str = "ERROR",
    error_message: str = "",
) -> dict[str, object]:
    return {
        "test_id": test_id,
        "test_description": description,
        "expected": expected,
        "observed": observed,
        "status": "PASS" if bool(condition) else "FAIL",
        "error_message": "" if condition else error_message or "condition evaluated False",
        "severity": severity,
        "timestamp": utc_now(),
    }


def output_manifest(output_root: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(output_root.rglob("*")):
        if path.is_file():
            try:
                observed_hash = sha256_file(path)
                hash_status = "HASHED"
                error_message = ""
            except OSError as error:
                observed_hash = ""
                hash_status = "UNREADABLE"
                error_message = repr(error)
            rows.append(
                {
                    "relative_path": str(path.relative_to(output_root)),
                    "bytes": path.stat().st_size,
                    "sha256": observed_hash,
                    "hash_status": hash_status,
                    "error_message": error_message,
                    "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                }
            )
    return pd.DataFrame(rows)
