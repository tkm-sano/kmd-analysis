#!/usr/bin/env python3
"""Create exact R20 evidence from complete-reachability R13 subsets only."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

from .core import ENERGY_ABS_TOLERANCE, energy_equal, enumerate_routes
from .routing_adapter import (
    ADAPTER_VERSION,
    INPUT_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    adapt_routing_artifact,
    select_customer_ids,
)
from .run_validation import LAMBDA_CANDIDATES, run_instance


EVIDENCE_SCHEMA_VERSION = "r20-routing-baseline-complete-reachability-validation-v1"
SELECTION_RULE = "first_n_customer_endpoints_in_endpoint_manifest_input_csv_source_order"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_subset(source: Path, depot: str, count: int) -> dict[str, Any]:
    customers = select_customer_ids(source, count)
    adapter = adapt_routing_artifact(
        source,
        depot,
        customers,
        source_schema_version=SOURCE_SCHEMA_VERSION,
        instance_id=f"routing_baseline_v18_first_{count}_customers",
    )
    if not adapter["accepted"]:
        return {
            "subset_id": f"depot_plus_{count}_customers",
            "selection_rule": SELECTION_RULE,
            "selected_customers": customers,
            "status": "FAIL_ADAPTER_REJECTED",
            "adapter": adapter,
        }
    adapted = adapter["input"]
    raw = adapted["raw_travel_time_matrix_s"]
    normalized = adapted["normalized_travel_time_matrix"]
    raw_reference = enumerate_routes(depot, customers, raw)
    normalized_reference = enumerate_routes(depot, customers, normalized)
    exact = run_instance(adapted["instance_id"], depot, customers, raw, LAMBDA_CANDIDATES)
    raw_routes = {tuple(route) for route in raw_reference["optimal_routes"]}
    normalized_routes = {tuple(route) for route in normalized_reference["optimal_routes"]}
    expected_pairs = (count + 1) * count
    lambda_results = exact["lambda_results"]
    checks = {
        "adapter_accepted": True,
        "complete_reachability": adapted["complete_reachability"],
        "directed_pair_count_exact": adapted["reachable_pair_count"] == expected_pairs,
        "asymmetric_pair_present": bool(adapted["asymmetric_pair_evidence"]),
        "missing_diagonal_allowed": all(edge["origin_id"] != edge["destination_id"] for edge in adapted["raw_directed_edges"]),
        "travel_time_unit_seconds": adapted["source"]["travel_time_unit"] == "s",
        "distance_auxiliary_only": all(record["travel_time"] == sum(raw[a][b] for a, b in zip(record["route"], record["route"][1:])) for record in raw_reference["records"]),
        "normalization_preserves_optimal_routes": raw_routes == normalized_routes,
        "direct_expanded_all_states_all_lambdas": all(item["direct_expanded_mismatch_count"] == 0 and item["direct_expanded_max_abs_difference"] <= ENERGY_ABS_TOLERANCE for item in lambda_results),
        "best_feasible_matches_original_all_lambdas": all(item["checks"]["qubo_route_optimum_matches_original"] for item in lambda_results),
        "decode_correct_all_lambdas": all(item["checks"]["decode_roundtrip_valid"] for item in lambda_results),
        "at_least_one_candidate_has_only_feasible_global_minima": any(item["all_global_minima_feasible"] for item in lambda_results),
        "raw_optimum_scales_to_normalized_optimum": energy_equal(raw_reference["best_route_travel_time"] / adapted["normalization"]["tau_max_s"], normalized_reference["best_route_travel_time"]),
    }
    return {
        "subset_id": f"depot_plus_{count}_customers",
        "selection_rule": SELECTION_RULE,
        "selected_depot": depot,
        "selected_customers": customers,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "adapter": adapter,
        "checks": checks,
        "original_route_enumeration_raw": raw_reference,
        "original_route_enumeration_normalized": normalized_reference,
        "exact_qubo_validation": exact,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=root / "reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted",
    )
    parser.add_argument("--depot", default="DEP_006")
    parser.add_argument(
        "--out",
        type=Path,
        default=root / "reproducibility/outputs/traffic_simulation/r20_real_data_validation/20260910_complete_reachability_v3",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.out.resolve()
    started = time.perf_counter()
    subsets = [run_subset(source, args.depot, count) for count in (2, 3)]
    payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "status": "PASS_FORMULATION_EVIDENCE_ONLY" if all(item["status"] == "PASS" for item in subsets) else "FAIL_VALIDATION_EVIDENCE",
        "scope": "initial_R20_complete_reachability_subsets_only",
        "formal_qaoa_executed": False,
        "formal_ising_conversion": False,
        "unreachable_transition_penalty_implemented": False,
        "formal_lambda_adopted": False,
        "selection_rule": SELECTION_RULE,
        "lambda_candidates": LAMBDA_CANDIDATES,
        "lambda_candidate_reason": "existing monotone exact-validation grid; evidence only; no formal lambda adopted",
        "source": {
            "artifact_path": str(source.relative_to(root)),
            "routing_arcs_sha256": sha256(source / "routing_arcs.csv"),
            "source_schema_version": SOURCE_SCHEMA_VERSION,
            "source_manifest_sha256": sha256(source / "r13_manifest.json"),
        },
        "software": {
            "python": platform.python_version(),
            "adapter_version": ADAPTER_VERSION,
            "adapter_schema_version": INPUT_SCHEMA_VERSION,
            "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        },
        "repository": {
            "source_commit": git_value("rev-parse", "HEAD"),
            "dirty_tracked_state": bool(git_value("status", "--porcelain", "--untracked-files=no")),
        },
        "source_hashes": {
            "routing_adapter.py": sha256(Path(__file__).parent / "routing_adapter.py"),
            "core.py": sha256(Path(__file__).parent / "core.py"),
            "run_validation.py": sha256(Path(__file__).parent / "run_validation.py"),
            "run_real_data_validation.py": sha256(Path(__file__)),
            "R20_QAOA_SUBPROBLEM_SPEC.md": sha256(root / "05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md"),
            "test_r20_route_ordering_exact.py": sha256(root / "05_src/traffic_simulation/validation/test_r20_route_ordering_exact.py"),
            "test_r20_routing_adapter.py": sha256(root / "05_src/traffic_simulation/validation/test_r20_routing_adapter.py"),
        },
        "subsets": subsets,
        "elapsed_seconds": time.perf_counter() - started,
        "research_status": {
            "THEORETICAL_BOUND_PROVED": True,
            "INSTANCE_AWARE_BOUND_PROVED": True,
            "UNRESOLVED_THEORETICAL_BOUND": False,
            "FORMULATION_VERIFIED": "NOT_PASS",
            "R20_Status": "BLOCKED",
            "Next_Allowed_Stage": "NONE",
        },
    }
    output.mkdir(parents=True, exist_ok=False)
    evidence_path = output / "validation_results.json"
    evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "run_id": output.name,
        "status": payload["status"],
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "formal_qaoa_executed": False,
        "formal_ising_conversion": False,
        "source_commit": payload["repository"]["source_commit"],
        "files": {"validation_results.json": sha256(evidence_path)},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "status": payload["status"],
        "subsets": {item["subset_id"]: item["status"] for item in subsets},
        "validation_results_sha256": manifest["files"]["validation_results.json"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
