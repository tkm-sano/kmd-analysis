from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "05_src"
AUTHORITY_PATH = ROOT / "reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml"
RESEARCH_MAP_PATH = ROOT / "reproducibility/config/research_portal/research_map_v1.yml"
OVERVIEW_PATH = ROOT / "RESEARCH_OVERVIEW.md"
REQUESTS_PATH = ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv"
STOPS_PATH = ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv"
BASELINE_DEMAND_PATH = ROOT / "03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet"
BASELINE_DEMAND_CONFIG = ROOT / "reproducibility/config/traffic_simulation/baseline_demand.yml"

OK = 0
FAILED = 1
UNAVAILABLE = 3


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]
    inputs: tuple[Path, ...] = ()
    configs: tuple[Path, ...] = ()
    outputs: tuple[Path, ...] = ()
    next_diagnostic: str = "./research status"


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def authority() -> dict:
    return load_yaml(AUTHORITY_PATH)


def accepted_paths() -> tuple[dict, Path, Path, Path]:
    auth = authority()
    accepted = auth["accepted_run"]
    network = ROOT / accepted["network_file"]
    acceptance = ROOT / accepted["acceptance_artifact"]
    mapping = ROOT / accepted["path"] / "request_stop_mapping.json"
    return auth, network, acceptance, mapping


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def network_gate() -> tuple[bool, list[str]]:
    issues: list[str] = []
    try:
        auth, network, acceptance_path, mapping = accepted_paths()
        for path in (network, acceptance_path, mapping):
            if not path.is_file():
                issues.append(f"missing artifact: {relative(path)}")
        if issues:
            return False, issues
        acceptance = load_json(acceptance_path)
        if acceptance.get("FORMAL_NETWORK_ACCEPTED") is not True:
            issues.append("FORMAL_NETWORK_ACCEPTED is not true")
        if sha256(network) != auth["accepted_run"]["network_sha256"]:
            issues.append("accepted network SHA-256 mismatch")
    except (OSError, KeyError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        issues.append(f"authority read failed: {exc}")
    return not issues, issues


def portal_summary() -> dict:
    path = ROOT / "research_portal/serve.py"
    spec = importlib.util.spec_from_file_location("research_portal_serve", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative(path)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summary()


def command_environment() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SOURCE) + (os.pathsep + existing if existing else "")
    return env


def python_script(path: str) -> tuple[str, ...]:
    return (sys.executable, str(ROOT / path))


def git_state() -> tuple[str, str]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    ).stdout.strip() or "UNAVAILABLE"
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=False
    ).stdout
    return commit, "DIRTY" if dirty else "CLEAN"


def print_execution_context(step: Step, *, dry_run: bool) -> None:
    commit, tree = git_state()
    print(f"Stage: {step.name}")
    print(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
    print(f"Timestamp: {datetime.now().astimezone().isoformat(timespec='seconds')}")
    print(f"Git commit: {commit}")
    print(f"Working tree: {tree}")
    print(f"Runtime: Python {sys.version.split()[0]}")
    print(f"Command: {shlex.join(step.command)}")
    print("Inputs: " + (", ".join(relative(p) for p in step.inputs) or "none"))
    print("Configs: " + (", ".join(relative(p) for p in step.configs) or "none"))
    print("Outputs: " + (", ".join(relative(p) for p in step.outputs) or "none (read-only)"))


def run_step(step: Step, *, dry_run: bool = False) -> int:
    missing = [path for path in (*step.inputs, *step.configs) if not path.exists()]
    print_execution_context(step, dry_run=dry_run)
    if missing:
        print("Result: BLOCKED")
        for path in missing:
            print(f"Missing: {relative(path)}")
        print(f"Next diagnostic command: {step.next_diagnostic}")
        return UNAVAILABLE
    if dry_run:
        print("Result: PLANNED (no command executed; no artifact changed)")
        return OK
    try:
        completed = subprocess.run(
            step.command,
            cwd=ROOT,
            env=command_environment(),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        print("Result: FAILED")
        print(f"Failed stage: {step.name}")
        print(f"Failed underlying command: {shlex.join(step.command)}")
        print(f"Relevant log path: not declared by underlying command ({exc})")
        print("Partial artifact: none known")
        print(f"Next diagnostic command: {step.next_diagnostic}")
        return FAILED
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    if completed.returncode:
        print("Result: FAILED")
        print(f"Failed stage: {step.name}")
        print(f"Failed underlying command: {shlex.join(step.command)}")
        print("Relevant log path: not declared by underlying command")
        print("Partial artifact: inspect the underlying command output above")
        print(f"Next diagnostic command: {step.next_diagnostic}")
        return completed.returncode
    print("Result: PASS")
    return OK


def run_steps(steps: Iterable[Step], *, dry_run: bool = False) -> int:
    for step in steps:
        code = run_step(step, dry_run=dry_run)
        if code:
            return code
    return OK


def unavailable(*, title: str, missing: Sequence[str], dependency: Sequence[str] = (), dry_run: bool = False) -> int:
    print(f"{title}: NOT IMPLEMENTED")
    for item in missing:
        print(f"Missing: {item}")
    for item in dependency:
        print(f"Dependency: {item}")
    if dry_run:
        print("Dry-run: no command executed; no artifact changed")
        return OK
    print("No command executed; no artifact changed")
    return UNAVAILABLE


def print_gate(name: str, ready: bool, issues: Sequence[str]) -> None:
    print(f"{name}: {'PASS' if ready else 'BLOCKED'}")
    for issue in issues:
        print(f"  - {issue}")
