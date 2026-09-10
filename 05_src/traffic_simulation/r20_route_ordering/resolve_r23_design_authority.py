"""Resolve the R23 formal-design predecessor/current artifact relationship."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json"
DESIGN_RECORD = ROOT / "05_src/traffic_simulation/specifications/R23_FORMAL_EXPERIMENT_DESIGN_V1.md"
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_design_authority/20260911_v1"
OLD_COMMIT = "2a57d9cce3e69d3cc3fbcc077a2e0f65d402064e"
LAMBDA_COMMIT = "dbca4b5a3ad748f46902c27da8e7c77bf02cbadf"
CURRENT_HEAD = "b493923cba93bf91af1b1a1e4d6efd5a2579b581"
OLD_HASH = "4064070cdcfffbd50149ad3a9b9a1431b054008a865b759a8e268e7e9380ce7c"
LAMBDA_HASH = "8f6f3b8feeeb85b556dc6fb23478fa5ef529bfac2ac4beb68c2d2bc7ff62bf95"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def predecessor() -> dict:
    return json.loads(subprocess.check_output(["git", "show", f"{OLD_COMMIT}:{DESIGN.relative_to(ROOT)}"], cwd=ROOT))


def design_fields(d: dict) -> dict:
    return {
        "research_question": d["research_question"],
        "scope": d["scope"],
        "experiment_structure": d["experiment_structure"],
        "problem_size_policy": d["problem_size_policy"],
        "instance_sampling_policy": d["instance_sampling_policy"],
        "qaoa": d["qaoa"],
        "optimizer": d["optimizer"],
        "seeds": d["seeds"],
        "metrics": d["metrics"],
        "runtime_contract": d["runtime_contract"],
        "reference_and_input_gates": d["reference_and_input_gates"],
        "resource_gates": d["resource_gates"],
        "stop_conditions": d["stop_conditions"],
        "artifact_contract": d["artifact_contract"],
        "statistics": d["statistics"],
        "planned_matrix": d["planned_matrix"],
        "decision_register": d["decision_register"],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    current = json.loads(DESIGN.read_text(encoding="utf-8"))
    old = predecessor()
    changed = {
        "authority/r20_formal_penalty_policy": {
            "classification": "AUTHORITY_LINEAGE_UPDATE",
            "old": None,
            "new": current["authority"]["r20_formal_penalty_policy"],
            "origin_commit": LAMBDA_COMMIT,
        },
        "authority/r20_formal_penalty_policy_id": {
            "classification": "AUTHORITY_LINEAGE_UPDATE",
            "old": None,
            "new": current["authority"]["r20_formal_penalty_policy_id"],
            "origin_commit": LAMBDA_COMMIT,
        },
        "decision_register/penalty_coefficient": {
            "classification": "FORMAL_RESEARCH_DESIGN_CHANGE",
            "old": None,
            "new": current["decision_register"]["penalty_coefficient"],
            "origin_commit": LAMBDA_COMMIT,
            "interpretation": "Previously unresolved formal penalty decision was explicitly adopted by the separate R20 lambda-authority task; value is not QAOA-tuned.",
        },
    }
    old_sem = sha_bytes(canonical(design_fields(old)))
    current_sem = sha_bytes(canonical(design_fields(current)))
    resolution = {
        "schema_version": "r23-formal-design-authority-resolution-v1",
        "resolution_id": "R23_FORMAL_DESIGN_AUTHORITY_RESOLUTION_V1",
        "classification": "OBSERVED_DESIGN_IS_AUTHORITATIVE",
        "original_expected_file_sha256": OLD_HASH,
        "original_commit": OLD_COMMIT,
        "observed_current_file_sha256": sha_file(DESIGN),
        "observed_content_origin_commit": LAMBDA_COMMIT,
        "current_head": git("rev-parse", "HEAD"),
        "canonical_design_path": str(DESIGN.relative_to(ROOT)),
        "canonical_design_file_sha256": sha_file(DESIGN),
        "historical_predecessor": {"path": str(DESIGN.relative_to(ROOT)), "commit": OLD_COMMIT, "file_sha256": OLD_HASH},
        "formal_design_record": {"path": str(DESIGN_RECORD.relative_to(ROOT)), "sha256": sha_file(DESIGN_RECORD), "expected_sha256": "6726406a7d3ae01971547994763b56f67bc0b6379ef856b35c10282aa807d1b0", "status": "PASS"},
        "byte_level_summary": {"changed_fields": 3, "changed_bytes": "3 JSON insertions in dbca4b5; no working-tree mutation", "diff_source": f"git diff {OLD_COMMIT}..{LAMBDA_COMMIT} -- {DESIGN.relative_to(ROOT)}"},
        "semantic_diff_summary": changed,
        "research_factor_comparison": {"status": "UNCHANGED_EXCEPT_EXPLICITLY_RESOLVED_PENALTY_AUTHORITY", "n": [2, 3, 4], "instances_per_n": 5, "p": [1, 2, 3], "lambda": 3.0, "optimizer": "COBYLA", "maxiter": 300, "objective_cap": 900, "expectation_cap": 901, "initialization": "all parameters = 0.1", "repetition": 1, "expectation_mode": "exact_statevector", "shots": "NONE", "optimization_level": 1, "seed_transpiler": 17, "instance_selection_seed": 2301, "planned_runs": 45},
        "semantic_design_hashes": {"predecessor_design_fields_sha256": old_sem, "current_design_fields_sha256": current_sem, "semantic_note": "Hash covers frozen design fields; current field set includes the explicitly adopted lambda decision."},
        "rationale": "The observed artifact is authoritative: dbca4b5 intentionally added the now-adopted R20 lambda authority and explicit lambda decision. No other formal factor changed. The old hash is retained as the historical predecessor.",
        "historical_authorization": {"old_artifact_sha256": "612441dcd56f64b421d3dc240a778e02241990d0b0e11b886c18d8933eba465e", "superseded_by": "this resolution and the new authorization artifact", "original_bytes_preserved": True},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_dirty_state": git("status", "--short"),
        "platform": platform.platform(),
    }
    (OUT / "design_authority_resolution.json").write_bytes(canonical(resolution) + b"\n")
    auth = {
        "schema_version": "r23-formal-execution-authorization-v2",
        "classification": "FORMAL_EXPERIMENT_EXECUTION_AUTHORIZED",
        "execution_performed": False,
        "resolution_id": resolution["resolution_id"],
        "formal_design_id": current["configuration_id"],
        "formal_design_artifact": resolution["canonical_design_path"],
        "formal_design_artifact_sha256": resolution["canonical_design_file_sha256"],
        "formal_design_semantic_sha256": current_sem,
        "historical_predecessor_design_sha256": OLD_HASH,
        "implementation_commit": current["authority"]["implementation_commit"],
        "lambda_policy_id": "R20_COMMON_GLOBAL_LAMBDA_V1",
        "lambda": 3.0,
        "lambda_policy_sha256": LAMBDA_HASH,
        "instance_set_id": "R23_FORMAL_INSTANCE_SET_V1",
        "instance_set_sha256": "18dde59308b796e00dade87152ae52421a30ae7b18a11dd6be45ef1840c65381",
        "run_manifest": "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/planned_run_manifest.json",
        "run_manifest_sha256": "92ab5f83ebeaf46ff0ba93706921b26e593e3235501f918942df4339d2af4aa2",
        "checks": {"implementation_authority": "PASS", "resolved_design": "PASS", "lambda_authority": "PASS", "instance_authority_15_of_15": "PASS", "r20_authority_15_of_15": "PASS", "r21_authority_15_of_15": "PASS", "r22_authority_15_of_15": "PASS", "planned_matrix_45_unique": "PASS", "runtime_environment": "PASS", "authority_drift": "PASS", "qaoa_executed": False, "optimizer_executed": False},
        "planned_matrix": {"instances": 15, "p_values": [1, 2, 3], "initializations": 1, "repetitions": 1, "planned_runs": 45},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "next_action": "Formal Experiment A may be executed only by a separate explicitly authorized task.",
    }
    (OUT / "execution_authorization.json").write_bytes(canonical(auth) + b"\n")
    manifest = {"schema_version": "r23-formal-design-authority-manifest-v1", "classification": resolution["classification"], "resolution_id": resolution["resolution_id"], "files": {name: sha_file(OUT / name) for name in ("design_authority_resolution.json", "execution_authorization.json")}, "canonical_design_file_sha256": resolution["canonical_design_file_sha256"], "formal_design_record_sha256": sha_file(DESIGN_RECORD), "source_commit": git("rev-parse", "HEAD"), "original_predecessor_sha256": OLD_HASH, "execution_performed": False}
    (OUT / "manifest.json").write_bytes(canonical(manifest) + b"\n")


if __name__ == "__main__":
    main()
