"""Isolated, paired optimizer-budget diagnostic for grouped loading v2."""
import argparse
import json
import math
import os
from dataclasses import fields
from fractions import Fraction
from pathlib import Path
import platform
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[name] = "1"
sys.path.insert(0, str(ROOT / "src"))

from kmd_toc.duty_break_v1.policy import load_policy
from kmd_toc.grouped_loading_v2.model import ScheduleError, candidate_key, evaluate
from kmd_toc.iterative_d3.operators import selected_quantum
from kmd_toc.iterative_d3.rng_v2 import call_seeds
from kmd_toc.iterative_d3_ops import resources
from kmd_toc.iterative_d3_ops.operation import POLICY
from kmd_toc.iterative_v3 import quantum
from kmd_toc.iterative_v3.io import dump, load_problem, read, sha, verify_pins
from kmd_toc.iterative_v3.order import OrderProblem, classical, cost, decode_routes, expand

SOURCE = HERE.parent / "grouped_loading_20261124_v2_pilot"
BUDGETS = (24, 48, 96, 192)
SAMPLES = (("S1", 0, 0), ("S2", 1, 2), ("S3", 2, 4))
METHOD = "qaoa-budget-grouped-v2-paired-diagnostic"


def source_files(scale, branch, iteration):
    directory = SOURCE / scale / "D_quantum" / f"branch_{branch}"
    local = directory / f"iteration_{iteration:04d}" / "local_000"
    parent = (directory / f"iteration_{iteration-1:04d}" / "state.json" if iteration else
              SOURCE / scale / "B" / "plan.json")
    return local / "CASE.json", parent, SOURCE / scale / "B" / "plan.json"


def prepare():
    from datetime import datetime
    from importlib.metadata import version

    source = SOURCE / "MANIFEST.json"
    manifest = read(source)
    if read(SOURCE / "REGISTRATION.json")["manifest_sha256"] != sha(source):
        raise ValueError("PILOT_MANIFEST_BINDING")
    verify_pins(manifest["code_hashes"])
    if read(SOURCE / "COMPLETE.json")["status"] != "COMPLETE_PILOT":
        raise ValueError("INCOMPLETE_SOURCE_PILOT")
    cases = []
    for scale, branch, iteration in SAMPLES:
        local, parent, base = source_files(scale, branch, iteration)
        case = next(c for c in manifest["cases"] if c["scale"] == scale)
        header = read(local)
        if (header["local_source"] != "current" or header["parent_move"] is not None
                or len(header["problem"]["ids"]) != 12 or header["return_limit"] != 4
                or header["state_hash"] != read(parent)["physical_hash"]):
            raise ValueError("SOURCE_LOCAL_PROBLEM_CONTRACT")
        cases.append(dict(scale=scale, branch=branch, iteration=iteration, input=case["input"],
                          local=str(local), parent=str(parent), base=str(base),
                          case_hash=header["case_hash"], hashes={str(f): sha(f) for f in (local, parent, base)}))
    if len({c["case_hash"] for c in cases}) != len(cases):
        raise ValueError("REPEATED_LOCAL_PROBLEM")
    protocol = dict(
        version=METHOD, registered_at=datetime.now().astimezone().isoformat(),
        formal_contribution=0, budgets=list(BUDGETS), replicates=[0, 1], mode="paired fixed-parent insertion",
        sampling="One preselected current-state window per scale, selected by index without outcomes. Two diagnostic seed streams per problem.",
        seeds="d3-rng-v2-sha256 stage=diagnostic; trial=replicate; common learning prefix and same independent final stream across caps.",
        compute="hayate cooperative lease; four single-CPU jobs per paired block; cyclic CPU assignment across blocks.",
        stopping_thresholds=dict(
            median_final_mean_normalized_gain_min=0.001,
            median_selected_shortest_gap_gain_pp_min=0.5,
            block_final_mean_gain_min=0.001, block_shortest_gap_gain_pp_min=0.5,
            local_consistent_blocks_min=4, local_consistent_scales_min=2,
            global_D_km_gain_min=0.01, global_W_min_gain_min=0.25,
            global_I_dual_pp_gain_min=0.05, global_blocks_min=2, global_scales_min=2,
            no_candidate_block_losses=True),
        decision=(
            "Compare all larger budgets against the currently retained budget, pairing by scale and replicate. "
            "A local material gain needs the median threshold and at least four of six blocks across at least two "
            "scales meeting that threshold on either independently measured final mean or shortest exact-gap. "
            "A global material gain requires either I_dual gain plus no D/W increase or at least the D or W threshold "
            "plus no increase in the other, in at least two blocks across two scales, with no loss of a block with a "
            "feasible returned candidate and no negative median paired I_dual gain. "
            "Upgrade only on a global material gain, using the smallest qualifying budget. "
            "Report local saturation, seed variability, and measured cost separately. This is an exploratory "
            "pilot decision threshold, not a test or a convergence claim."),
        source_manifest=str(source), source_manifest_sha256=sha(source), entry_sha256=sha(Path(__file__)),
        cases=cases, environment=dict(host=platform.node(), python=sys.version,
                                      packages={k: version(k) for k in ("numpy", "scipy", "qiskit")}),
        configuration=manifest["configuration"], grouped_conditions=manifest["grouped_conditions"])
    dump(HERE / "PROTOCOL.json", protocol)


def registered():
    protocol = read(HERE / "PROTOCOL.json")
    if sha(Path(protocol["source_manifest"])) != protocol["source_manifest_sha256"] or sha(Path(__file__)) != protocol["entry_sha256"]:
        raise ValueError("CHANGED_DIAGNOSTIC_PROTOCOL")
    return protocol


def problem_of(header):
    from kmd_toc.iterative_v3.io import tuples
    raw = header["problem"]
    problem = OrderProblem(**{item.name: tuples(raw[item.name]) if item.name in ("ids", "prefix", "suffix") else raw[item.name]
                              for item in fields(OrderProblem)})
    if problem.fingerprint != header["case_hash"]:
        raise ValueError("LOCAL_PROBLEM_HASH")
    return problem


def exact_path(problem):
    """Held–Karp with exact integer costs for the saved decimal lookup."""
    lookup = problem.lookup
    first = [Fraction(str(x)) for x in lookup["first"]]
    last = [Fraction(str(x)) for x in lookup["last"]]
    edge = [[Fraction(str(x)) for x in row] for row in lookup["edge"]]
    denominator = math.lcm(*(x.denominator for x in (*first, *last, *(x for row in edge for x in row))))
    first = [int(x * denominator) for x in first]
    last = [int(x * denominator) for x in last]
    edge = [[int(x * denominator) for x in row] for row in edge]
    n = problem.n
    full = (1 << n) - 1
    dp = {(1 << i, i): (first[i], (i,)) for i in range(n)}
    for mask in range(1, full):
        for end in range(n):
            current = dp.get((mask, end))
            if current is None:
                continue
            value, path = current
            for nxt in range(n):
                bit = 1 << nxt
                if mask & bit:
                    continue
                candidate = (value + edge[end][nxt], (*path, nxt))
                key = (mask | bit, nxt)
                if key not in dp or candidate < dp[key]:
                    dp[key] = candidate
    total, path = min((dp[full, i][0] + last[i], dp[full, i][1]) for i in range(n))
    exact = Fraction(total, denominator)
    if not math.isclose(cost(problem, path), float(exact), abs_tol=1e-9, rel_tol=1e-14):
        raise ValueError("EXACT_PATH_DISTANCE")
    return dict(distance_m=float(exact), exact_m=str(exact), order=list(path), states=len(dp))


def metrics(plan, base):
    d, w = (Fraction(plan[key]) for key in ("D_exact", "W_exact"))
    bd, bw = (Fraction(base[key]) for key in ("D_exact", "W_exact"))
    return dict(D_km=float(d), W_total_min=float(w), I_dual_B_pp=float(100 * min(1-d/bd, 1-w/bw)),
                D_exact=str(d), W_exact=str(w), physical_hash=plan["physical_hash"])


def measure_orders(problem, candidates, p, duty, incumbent, base, folder):
    def key(plan):
        return candidate_key(plan, base, initial=plan["physical_hash"] == base["physical_hash"])

    selected = incumbent
    best_source = None
    rows = []
    for number, item in enumerate(candidates):
        row = dict(item)
        try:
            plan = evaluate(p, expand(problem, tuple(item["order"])), incumbent["calls_s"], duty)
        except ScheduleError as error:
            row.update(feasible=False, reason=str(error))
        else:
            row.update(feasible=True, **metrics(plan, base))
            if key(plan) < key(selected):
                selected = plan
                best_source = number
        rows.append(row)
    if folder is not None:
        saved = folder / "selected_plan.json"
        if saved.is_file():
            if read(saved) != selected:
                raise ValueError("SELECTED_PLAN_REPLAY")
        else:
            dump(saved, selected)
    return dict(candidates=rows, selected_candidate=best_source, selected=metrics(selected, base),
                feasible_candidates=sum(item["feasible"] for item in rows),
                min_returned_distance_m=min((item["local_distance_m"] for item in rows), default=None))


def worker(job_path):
    lease, binding, _ = resources.authorized(Path(os.environ["KMD_D3_LEASE_INTENT"]), worker=True)
    protocol = registered()
    if lease["manifest_sha256"] != sha(HERE / "PROTOCOL.json") or binding["job"] != str(job_path):
        raise ValueError("PAIRED_DIAGNOSTIC_LEASE_BINDING")
    job = read(job_path)
    case = next(c for c in protocol["cases"] if c["scale"] == job["scale"])
    cfg = protocol["configuration"]
    for path, wanted in case["hashes"].items():
        if sha(Path(path)) != wanted:
            raise ValueError("SOURCE_ARTIFACT_HASH")
    folder = job_path.parent
    local = read(Path(case["local"]))
    problem = problem_of(local)
    context = dict(stage="diagnostic", scale=case["scale"], trial=job["replicate"], branch=case["branch"])
    cap = job["budget"]
    seed = call_seeds(context, "D_quantum", case["iteration"], cap)
    settings = cfg["search"]["quantum"] | dict(optimizer_max_evaluations=cap) | seed
    orders, receipt = selected_quantum(quantum.run, problem, settings, folder / "solver", 4, local_header=local)
    if not (folder / "OPTIMIZER.json").exists():
        dump(folder / "OPTIMIZER.json", receipt)
    p = load_problem(case["input"], cfg["rest_options"])
    duty = load_policy() | {"loading_s": protocol["grouped_conditions"]["loading_s"]}
    incumbent, base = (read(Path(case[k])) for k in ("parent", "base"))
    sampled = receipt["selector"]
    measured_costs = [cost(problem, quantum.decode(bits, problem))
                      for bits in read(folder / "solver" / "RESULT.json")["sample_counts"]]
    final = read(folder / "solver" / "FINAL_SAMPLE.json")
    probabilities = [n / receipt["final_shots_actual"] for n in final["counts"].values()]
    result = dict(job | dict(
        case_hash=problem.fingerprint, bound_m=problem.lookup["bound_m"], incumbent=metrics(incumbent, base),
        classical_reference=None, exact=exact_path(problem), initial_cost_m=cost(problem, tuple(range(problem.n))),
        evals=receipt["training_evaluations"], optimizer_success=receipt["optimizer_success"],
        optimizer_message=receipt["optimizer_message"], training_best_normalized=receipt["optimizer_fun"],
        final_mean_normalized=final["objective"], final_mean_m=final["objective"] * problem.lookup["bound_m"],
        angles=receipt["angles"], minimum_measured_m=min(measured_costs), unique_valid_orders=sampled["unique_valid_orders"],
        valid_shots=sampled["measured_shots"]-sampled["invalid_shots"],
        final_shots=receipt["final_shots_actual"], shots=receipt["total_shots_actual"],
        entropy_effective_orders=math.exp(-math.fsum(p * math.log(p) for p in probabilities)),
        wall_s=receipt["wall_s"], cpu_s=receipt["CPU_s"], max_TV_bound=receipt["max_TV_bound"],
        **measure_orders(problem, orders, p, duty, incumbent, base, folder)))
    if cap == BUDGETS[0]:
        cseed = call_seeds(context, "D_classical", case["iteration"])
        candidates, counts = classical(problem, cfg["search"]["classical"] | cseed, 4)
        result["classical_reference"] = measure_orders(problem, candidates, p, duty, incumbent, base, None) | counts
    dump(folder / "RESULT.json", result)


def run():
    protocol = registered()
    verify_pins(read(SOURCE / "MANIFEST.json")["code_hashes"])
    with resources.acquire(HERE, sha(HERE / "PROTOCOL.json"), POLICY, METHOD, "optimizer_budget_pilot") as lease:
        for i, case in enumerate(protocol["cases"]):
            for rep in protocol["replicates"]:
                block = HERE / "runs" / case["scale"] / f"seed_{rep}"
                jobs = []
                for j, cap in enumerate(BUDGETS):
                    target = block / f"cap_{cap}"
                    target.mkdir(parents=True, exist_ok=True)
                    if (target / "RESULT.json").exists():
                        continue
                    job = target / "JOB.json"
                    data = dict(scale=case["scale"], replicate=rep, budget=cap, cpu=(i * 2 + rep + j) % 4)
                    if not job.exists():
                        dump(job, data)
                    elif read(job) != data:
                        raise ValueError("CHANGED_DIAGNOSTIC_JOB")
                    jobs.append(dict(path=job, action="_branch"))
                if jobs:
                    codes, alarm = resources.supervise(lease, Path(__file__).resolve(), jobs, block, protocol["configuration"])
                    if any(codes) or alarm:
                        raise RuntimeError(f"{case['scale']} {rep} {codes} {alarm}")
                print(case["scale"], rep, "COMPLETE", flush=True)
    if not (HERE / "RUN_COMPLETE.json").exists():
        dump(HERE / "RUN_COMPLETE.json", dict(blocks=6, runs=24, formal_jobs=0, protocol_sha256=sha(HERE / "PROTOCOL.json")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "_branch", "_guard"))
    parser.add_argument("--intent", type=Path)
    parser.add_argument("--job", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "run":
        run()
    elif args.action == "_branch":
        worker(args.job)
    else:
        return resources.guard(args.intent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
