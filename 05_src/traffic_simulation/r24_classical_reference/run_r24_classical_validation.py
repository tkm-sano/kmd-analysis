#!/usr/bin/env python3
"""Run the mechanically selected R24 classical-reference validation cases."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
from pathlib import Path
from statistics import median

import highspy

from .r24_cvrp_model import (
    FEASIBILITY_TOLERANCE,
    FLEET_SEMANTICS,
    INTEGER_TOLERANCE,
    OBJECTIVE_TOLERANCE,
    SUBTOUR_FORMULATION,
    load_instance,
)
from .r24_exact_reference import solve_exact
from .r24_highs_solver import HIGHS_OPTIONS, solve_highs
from .r24_solution_validator import validate_routes

ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1"
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1"
GRAPH_SHA = "460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2"
ELIGIBLE_SHA = "245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def select_cases() -> tuple[list[dict], dict[str, dict]]:
    with (SUITE / "BASE_INSTANCE_MANIFEST.csv").open(newline="", encoding="utf-8") as handle:
        bases = list(csv.DictReader(handle))
    base_by_id = {row["instance_id"]: row for row in bases}
    selected_ids: list[str] = []
    # Predeclared mechanical rule: R01 at every quantum n, R01 of every n=4
    # structure, and the fixed n=4 anchor; all three rho conditions for each.
    for n in (2, 3, 4):
        selected_ids.append(f"R24-RND-N{n:03d}-R01")
    for structure in ("CLUSTERED", "DISPERSED", "MIXED"):
        selected_ids.append(f"R24-STR-{structure}-N004-R01")
    selected_ids.append("R24-ANCHOR-N004")
    with (SUITE / "CAPACITY_CONDITION_MANIFEST.csv").open(newline="", encoding="utf-8") as handle:
        conditions = list(csv.DictReader(handle))
    selected = sorted(
        (row for row in conditions if row["base_instance_id"] in selected_ids),
        key=lambda row: row["condition_id"],
    )
    if len(selected) != 21:
        raise RuntimeError(f"mechanical selection expected 21 conditions, found {len(selected)}")
    required_statuses = {"READY", "DEGENERATE_REGIME_SAME_M"}
    if {row["condition_status"] for row in selected} != required_statuses:
        raise RuntimeError("selection does not cover degenerate and non-degenerate conditions")
    if {row["regime_label"] for row in selected} != {"LOOSE", "MODERATE", "TIGHT"}:
        raise RuntimeError("selection does not cover all rho regimes")
    if not any(int(base_by_id[row["base_instance_id"]]["duplicate_proxy_group_count"]) > 0 for row in selected):
        raise RuntimeError("selection lacks duplicate-proxy case")
    return selected, base_by_id


def route_json(routes) -> str:
    return json.dumps([list(route) for route in routes], ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    execution_sha = git("rev-parse", "HEAD")
    selected, base_by_id = select_cases()
    exact_rows: list[dict] = []
    highs_rows: list[dict] = []
    compare_rows: list[dict] = []
    validation_rows: list[dict] = []
    case_runtimes: list[float] = []
    duplicate_case_ids: list[str] = []
    asymmetric_case_ids: list[str] = []
    for condition in selected:
        condition_id = condition["condition_id"]
        base_id = condition["base_instance_id"]
        base = base_by_id[base_id]
        instance = load_instance(SUITE, base_id, condition_id)
        has_duplicate = int(base["duplicate_proxy_group_count"]) > 0
        has_zero = int(base["zero_travel_time_ordered_arc_count"]) > 0
        has_asymmetry = any(
            abs(instance.arcs[a, b].travel_time - instance.arcs[b, a].travel_time) > OBJECTIVE_TOLERANCE
            for index, a in enumerate(instance.nodes) for b in instance.nodes[index + 1:]
        )
        if has_duplicate:
            duplicate_case_ids.append(condition_id)
        if has_asymmetry:
            asymmetric_case_ids.append(condition_id)
        exact = solve_exact(instance)
        exact_validation_started = time.perf_counter()
        exact_validation = validate_routes(instance, exact.routes, exact.objective)
        exact_validation_time = time.perf_counter() - exact_validation_started
        highs = solve_highs(instance)
        highs_validation_started = time.perf_counter()
        if highs.decoded is None:
            highs_validation = None
        else:
            highs_validation = validate_routes(instance, highs.decoded.routes, highs.objective, highs.decoded.errors)
        highs_validation_time = time.perf_counter() - highs_validation_started
        difference = None if exact.objective is None or highs.objective is None else abs(exact.objective - highs.objective)
        agreement = (
            exact.status == "OPTIMAL" and highs.status == "OPTIMAL" and difference is not None
            and difference <= OBJECTIVE_TOLERANCE and exact_validation.status == "VALID_SOLUTION"
            and highs_validation is not None and highs_validation.status == "VALID_SOLUTION"
        )
        common = {
            "condition_id": condition_id, "base_instance_id": base_id, "suite": base["suite"],
            "structure": base["structure"], "n": base["n"], "regime_label": condition["regime_label"],
            "target_rho": condition["target_rho"], "actual_rho": condition["actual_rho"],
            "Q": condition["Q"], "available_m": condition["m"],
            "degenerate": condition["degenerate_regime_flag"], "has_duplicate_proxy": has_duplicate,
            "has_zero_arc": has_zero, "has_asymmetric_cost": has_asymmetry,
        }
        exact_rows.append({**common, "status": exact.status, "objective_travel_time_s": exact.objective,
            "total_distance_m": exact.total_distance, "used_vehicles": len(exact.routes),
            "routes_json": route_json(exact.routes), "candidates_evaluated": exact.candidates_evaluated,
            "feasible_candidates": exact.feasible_candidates, "optimum_multiplicity": exact.optimum_multiplicity,
            "enumeration_time_s": exact.runtime_s, "validation_time_s": exact_validation_time})
        hv = highs_validation
        highs_rows.append({**common, "status": highs.status, "model_status": highs.model_status,
            "objective_travel_time_s": highs.objective,
            "recomputed_objective_s": None if hv is None else hv.objective,
            "objective_difference_s": None if hv is None else hv.objective_difference,
            "total_distance_m": None if hv is None else hv.total_distance,
            "used_vehicles": None if hv is None else hv.used_vehicles,
            "route_loads_json": None if hv is None else json.dumps(hv.route_loads),
            "routes_json": "" if highs.decoded is None else route_json(highs.decoded.routes),
            "mip_gap": highs.mip_gap, "build_time_s": highs.build_time_s, "solve_time_s": highs.solve_time_s,
            "decode_time_s": highs.decode_time_s, "validation_time_s": highs_validation_time,
            "total_time_s": highs.total_time_s + highs_validation_time})
        compare_rows.append({**common, "exact_objective_s": exact.objective, "highs_objective_s": highs.objective,
            "absolute_difference_s": difference, "exact_used_vehicles": len(exact.routes),
            "highs_used_vehicles": None if hv is None else hv.used_vehicles,
            "exact_optimal": exact.status == "OPTIMAL", "highs_proven_optimal": highs.status == "OPTIMAL",
            "optimum_agreement": agreement})
        validation_rows.extend([
            {"condition_id": condition_id, "solver": "EXACT_ENUMERATION", "validation_status": exact_validation.status,
             "errors_json": json.dumps(exact_validation.errors), "recomputed_objective_s": exact_validation.objective,
             "objective_difference_s": exact_validation.objective_difference, "capacity_valid": not any("capacity" in e for e in exact_validation.errors)},
            {"condition_id": condition_id, "solver": "HIGHS_MILP", "validation_status": "NO_SOLUTION" if hv is None else hv.status,
             "errors_json": json.dumps(()) if hv is None else json.dumps(hv.errors),
             "recomputed_objective_s": None if hv is None else hv.objective,
             "objective_difference_s": None if hv is None else hv.objective_difference,
             "capacity_valid": False if hv is None else not any("capacity" in e for e in hv.errors)},
        ])
        case_runtimes.append(exact.runtime_s + highs.total_time_s + exact_validation_time + highs_validation_time)

    write_csv(out / "EXACT_REFERENCE_RESULTS.csv", exact_rows)
    write_csv(out / "HIGHS_REFERENCE_RESULTS.csv", highs_rows)
    write_csv(out / "EXACT_VS_HIGHS_COMPARISON.csv", compare_rows)
    write_csv(out / "SOLUTION_VALIDATION_RESULTS.csv", validation_rows)
    passed = all(row["optimum_agreement"] for row in compare_rows)
    validator_failures = sum(row["validation_status"] != "VALID_SOLUTION" for row in validation_rows)
    max_difference = max(float(row["absolute_difference_s"]) for row in compare_rows)
    total_runtime = sum(case_runtimes)
    verdict = "R24_CLASSICAL_REFERENCE_VALIDATED" if passed and validator_failures == 0 else "R24_CLASSICAL_REFERENCE_REQUIRES_REMEDIATION"
    next_task = "run classical R24 reference benchmark" if verdict == "R24_CLASSICAL_REFERENCE_VALIDATED" else "remediate classical R24 reference validation failure"

    (out / "R24_CVRP_MATHEMATICAL_FORMULATION.md").write_text(f"""# R24 CVRP 数学モデル\n\n- 有向CVRP、depot=`DEP_006`、容量 `Q=14`。\n- 主目的: run_3 の有向travel timeの総和を最小化。distanceは副次指標。\n- 変数: arc使用 `x_ijk`、customer割当 `y_ik`、車両使用 `z_k`、MTZ積載順序 `u_ik`。\n- 制約: customer exactly once、assignment/入出flow整合、使用車両のdepot発着、unsplittable capacity、load-MTZ subtour除去。\n- fleet contract: `{FLEET_SEMANTICS}`。使用車両数はcondition-specific `m` 以下。\n- validated OD manifestに存在する全有向arcのみを使用する。\n""", encoding="utf-8")
    (out / "FLEET_SEMANTICS_DECISION.md").write_text("""# Fleet semantics 決定\n\n`R24_FLEET_SEMANTICS = AT_MOST_M` と固定した。capacity contractの `m=ceil(D/(rho*Q))` はavailable methodological fleet sizeであり、standard CVRPと整合する。`z_k` を用いて使用車両数を `m` 以下とする。exactly-mは強制しない。このため、異なるavailable mでもtravel-time最適解の使用台数が同じになり得る点は後続比較の制約である。\n""", encoding="utf-8")
    (out / "SUBTOUR_FORMULATION_DECISION.md").write_text("""# Subtour formulation 決定\n\n`R24_CLASSICAL_SUBTOUR_FORMULATION = LOAD_MTZ` と固定した。各車両/customerの連続積載順序変数に正の需要を累積し、customer-only cycleを矛盾させる。small benchmarkで明示的、compactで、HiGHSへ直接実装できる。車両対称性にはfeasible setを変えない `z_k >= z_{k+1}` のみを用いる。\n""", encoding="utf-8")
    options = "\n".join(f"- `{k} = {v}`" for k, v in HIGHS_OPTIONS.items())
    (out / "HIGHS_SOLVER_CONFIGURATION.md").write_text(f"""# HiGHS solver設定\n\n- HiGHS/highspy: `{highspy.Highs().version()}` / `{importlib.metadata.version('highspy')}`\n{options}\n- objective tolerance: `{OBJECTIVE_TOLERANCE}`\n- feasibility tolerance: `{FEASIBILITY_TOLERANCE}`\n- integer decode tolerance: `{INTEGER_TOLERANCE}`\n- primary solver: HiGHS。代替solverは使用していない。\n""", encoding="utf-8")
    (out / "VALIDATION_CASE_SELECTION.md").write_text("""# Validation case選択\n\nsolver結果を見る前に固定した機械的規則を使用した。\n\n1. Primary RandomのR01を n=2,3,4 から選び、各3 rhoを選択。\n2. StructuralのCLUSTERED/DISPERSED/MIXEDについて n=4, R01を選び、各3 rhoを選択。\n3. `R24-ANCHOR-N004` の全3 rhoを選択。\n\n合計21 conditions。CLUSTERED N004 R01にduplicate proxy/zero arcが含まれ、全体でrandom/structural/anchor、loose/moderate/tight、degenerate/non-degenerateを満たす。selection後のredrawや結果による追加・除外は行っていない。\n""", encoding="utf-8")
    (out / "DUPLICATE_PROXY_ZERO_ARC_TESTS.md").write_text(f"""# Duplicate proxy / zero arc検証\n\n- 対象conditions: {len(set(duplicate_case_ids))}\n- 判定: {'PASS' if duplicate_case_ids and passed else 'FAIL'}\n- building-based customer IDを統合せずcustomer-onceを適用した。\n- flagged zero-distance/time transitionを許容し、ExactとHiGHSの目的値および独立validatorが一致した。\n- conditions: `{', '.join(sorted(set(duplicate_case_ids)))}`\n""", encoding="utf-8")
    (out / "ASYMMETRIC_COST_TEST.md").write_text(f"""# Asymmetric directed cost検証\n\n- asymmetric travel-time pairを含むconditions: {len(set(asymmetric_case_ids))}/{len(selected)}\n- 判定: {'PASS' if asymmetric_case_ids and passed else 'FAIL'}\n- `c_ij` と `c_ji` を別arc parameterとして読み、ExactとHiGHSが独立にdirected costを評価した。\n""", encoding="utf-8")
    cpu = platform.processor() or platform.machine()
    ram_gib = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
    (out / "RUNTIME_ENVIRONMENT.md").write_text(f"""# Runtime環境\n\n- OS: `{platform.platform()}`\n- CPU: `{cpu}` / logical CPUs `{os.cpu_count()}`\n- RAM: `{ram_gib:.2f} GiB`\n- Python: `{platform.python_version()}`\n- HiGHS: `{highspy.Highs().version()}`\n- highspy: `{importlib.metadata.version('highspy')}`\n- validation cases: `{len(selected)}`\n- total measured case wall time: `{total_runtime:.6f} s`\n- median measured case wall time: `{median(case_runtimes):.6f} s`\n""", encoding="utf-8")
    (out / "PROVENANCE.md").write_text(f"""# Provenance\n\n- repository execution SHA: `{execution_sha}`\n- instance suite: `{SUITE.relative_to(ROOT)}`\n- instance suite SHA256SUMS hash: `{sha256(SUITE / 'SHA256SUMS.txt')}`\n- source C_eligible SHA-256: `{ELIGIBLE_SHA}`\n- run_3 graph SHA-256: `{GRAPH_SHA}`\n- dependency: `highspy=={importlib.metadata.version('highspy')}`\n- demand generation: NONE\n- routing graph regeneration: NONE\n- instance generation/resampling: NONE\n- full benchmark/quantum optimization: NONE\n""", encoding="utf-8")
    (out / "R24_CLASSICAL_REFERENCE_VALIDATION.md").write_text(f"""# R24 Classical Reference Validation\n\n## Verdict\n\n`{verdict}`\n\nExact Enumeration、HiGHS MILP、独立solution validatorの三者を、freeze済みsuiteから機械的に選んだsmall 21 conditionsで照合した。\n\n- Exact optimal: {sum(r['status']=='OPTIMAL' for r in exact_rows)}/{len(exact_rows)}\n- HiGHS proven optimal: {sum(r['status']=='OPTIMAL' for r in highs_rows)}/{len(highs_rows)}\n- optimum agreement: {sum(bool(r['optimum_agreement']) for r in compare_rows)}/{len(compare_rows)}\n- maximum objective difference: {max_difference:.12g} s\n- validator failures: {validator_failures}\n- fleet semantics: `{FLEET_SEMANTICS}`\n- subtour formulation: `{SUBTOUR_FORMULATION}`\n- scientific execution: CLASSICAL_REFERENCE_VALIDATION only\n- full 330-condition benchmark: NOT RUN\n\n## 制約\n\n検証は n<=4 に限定され、full-suite runtime/scalingは未評価。available-fleet (`AT_MOST_M`) では異なるmが同じused-vehicle optimumを持ち得る。\n\n`NEXT_EXECUTABLE_TASK = {next_task}`\n""", encoding="utf-8")
    required = [
        "R24_CLASSICAL_REFERENCE_VALIDATION.md", "R24_CVRP_MATHEMATICAL_FORMULATION.md",
        "HIGHS_SOLVER_CONFIGURATION.md", "FLEET_SEMANTICS_DECISION.md", "SUBTOUR_FORMULATION_DECISION.md",
        "VALIDATION_CASE_SELECTION.md", "EXACT_REFERENCE_RESULTS.csv", "HIGHS_REFERENCE_RESULTS.csv",
        "EXACT_VS_HIGHS_COMPARISON.csv", "SOLUTION_VALIDATION_RESULTS.csv",
        "DUPLICATE_PROXY_ZERO_ARC_TESTS.md", "ASYMMETRIC_COST_TEST.md", "RUNTIME_ENVIRONMENT.md", "PROVENANCE.md",
    ]
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as handle:
        for name in required:
            handle.write(f"{sha256(out / name)}  {name}\n")
    print(json.dumps({"verdict": verdict, "cases": len(selected), "agreement": sum(bool(r["optimum_agreement"]) for r in compare_rows),
                      "validator_failures": validator_failures, "max_difference": max_difference,
                      "total_runtime_s": total_runtime, "next_task": next_task}, indent=2))
    return 0 if verdict == "R24_CLASSICAL_REFERENCE_VALIDATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

