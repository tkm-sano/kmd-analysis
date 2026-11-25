"""Registered holdout pilot for grouped v2 QAOA initial angles."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
from importlib.metadata import version
import math
import os
from pathlib import Path
import random
from statistics import median
import sys

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "qaoa_budget_grouped_v2_20261124"
sys.path.insert(0, str(PREVIOUS))
from pilot import (
    ROOT, SOURCE, POLICY, ScheduleError, cost, evaluate, exact_path, load_policy,
    load_problem, classical, measure_orders, metrics, problem_of, quantum, resources,
    selected_quantum, dump, read, sha, verify_pins,
)
from analyze import eval_header, output_csv
from kmd_toc.grouped_loading_v2.methods import route_view
from kmd_toc.grouped_loading_v2.search import generate
from kmd_toc.iterative_d3.operators import local_target, proposals
from kmd_toc.iterative_d3.rng_v2 import call_seeds, event
from kmd_toc.iterative_v3.order import build

LABEL = "grouped-v2-qaoa-initial-transfer-pilot"
SCALES = ("S1", "S2", "S3")
ARMS = ("A", "B")
FORMAL = HERE.parent / "formal_J30_grouped_v2"
PARENT_SPECS = (("current", 0, 1), ("current", 1, 3),
                ("reallocation", 2, 0), ("reallocation", 3, 2))
ANGLE_NAMES = ("gamma1", "beta1", "gamma2", "beta2")


def formal_guard():
    manifest, freeze = FORMAL / "MANIFEST.json", FORMAL / "FREEZE_RECORD.json"
    mh, fh = sha(manifest), sha(freeze)
    record = read(manifest)
    if (len(record["cases"]) != 90 or record["state"] != "NOT_STARTED"
            or read(freeze)["manifest_sha256"] != mh or (FORMAL / "EXECUTION_STARTED.json").exists()
            or (FORMAL / "trials").exists()):
        raise ValueError("FORMAL_REGISTRATION_NOT_IN_EXPECTED_UNSTARTED_STATE")
    return dict(manifest_sha256=mh, freeze_sha256=fh, cases=90, state="NOT_STARTED")


def canonical(value):
    return (value + math.pi / 2) % math.pi - math.pi / 2


def circle_loss(value, angles):
    return math.fsum(abs(canonical(value-angle)) for angle in angles)


def circular_median(angles):
    """Cut at largest gap and take the midpoint median on the occupied short arc."""
    vals = sorted(angle % math.pi for angle in angles)
    gaps = [y-x for x,y in zip(vals, vals[1:] + [vals[0]+math.pi])]
    cut_after = max(range(len(vals)), key=lambda i: (gaps[i], -i))
    start = vals[(cut_after+1) % len(vals)]
    unwrapped = sorted((v-start) % math.pi for v in vals)
    if unwrapped[-1] >= math.pi/2:
        raise ValueError("CIRCULAR_SAMPLE_NOT_IN_OPEN_SEMICIRCLE")
    mid = canonical(start + median(unwrapped))
    lo = canonical(start + unwrapped[(len(vals)-1)//2])
    hi = canonical(start + unwrapped[len(vals)//2])
    objective = circle_loss(mid, angles)
    # A piecewise linear circular L1 objective reaches its minimum at a
    # sample or its antipode unless it is constant. This checks the full circle.
    best = min(circle_loss(x, angles) for v in angles for x in (v, v+math.pi/2))
    if not math.isclose(best, objective, abs_tol=1e-10):
        raise ValueError("CIRCULAR_MEDIAN_L1_CHECK")
    return dict(value=mid, median_arc_endpoints=[lo, hi], canonical_range="[-pi/2,pi/2)",
                period=math.pi, occupied_arc_length=unwrapped[-1], largest_gap=gaps[cut_after],
                circular_l1_objective=objective, independently_checked_breakpoint_minimum=best)


def archived(item):
    scale, branch, iteration = item
    path = SOURCE / scale / "D_quantum" / f"branch_{branch}" / f"iteration_{iteration:04d}"
    header_path = path / "local_000" / "CASE.json"
    solver = header_path.parent / "solver"
    case = read(header_path)
    receipt = read(solver / "RESULT.json")
    final = eval_header(solver / "FINAL_SAMPLE.json")
    commit = read(path / "COMMIT.json")
    angles = receipt["angles"]
    if (receipt["status"] != "COMPLETE" or receipt["problem_hash"] != case["case_hash"]
            or final["identity"]["problem_hash"] != case["case_hash"] or final["identity"]["angles"] != angles
            or final["identity"]["phase"] != "final_extraction" or final["identity"]["shots"] != 10000
            or sum(final["counts"].values()) != 10000 or len(angles) != 4 or not all(map(math.isfinite, angles))):
        raise ValueError(f"ARCHIVED_FINAL_CONTRACT {path}")
    row = dict(scale=scale, branch=branch, iteration=iteration+1, archive_case_hash=case["case_hash"],
               final_extraction_verified=True, optimizer_success=receipt["optimizer_success"],
               candidate_adopted=any(x.get("id")==commit["adopted"] and x["kind"]=="measured_order_only_QAOA"
                                     for x in commit["candidate_receipts"]),
               final_record=str(solver / "RESULT.json"), final_record_sha256=sha(solver / "RESULT.json"))
    return row | dict(zip(ANGLE_NAMES, angles)), case


def holdout_cases(manifest, excluded):
    duty = load_policy() | {"loading_s": manifest["grouped_conditions"]["loading_s"]}
    samples, extraction = [], []
    cfg = manifest["configuration"]
    for scale in SCALES:
        source = next(c for c in manifest["cases"] if c["scale"]==scale)
        p = load_problem(source["input"], cfg["rest_options"])
        base_file = SOURCE / scale / "B" / "plan.json"
        for index, (origin, branch, checkpoint) in enumerate(PARENT_SPECS):
            ident = f"{scale}-{origin}-{index%2+1}"
            parent_file = (SOURCE / scale / "D_quantum" / f"branch_{branch}" /
                           f"iteration_{checkpoint:04d}" / "state.json")
            parent = read(parent_file)
            view = route_view(parent)
            iteration = 0 if origin=="current" else 1
            rejects = dict(overlap=0, missing_window=0, unaffected_window=0, infeasible_parent=0)
            for attempt in range(256):
                ctx = dict(stage="diagnostic", scale=scale, trial=24000+256*index+attempt, branch=branch)
                settings = cfg["search"] | {"rng_v2":ctx}
                seed = event(ctx, "D_shared", "branch-identity")
                moves = []
                if origin=="reallocation":
                    possible, _ = proposals(generate, p, view, random.Random(seed), settings, seed, iteration, 3)
                    moves = ([possible[0], possible[-1]] if len(possible)>2 and
                             possible[-1]["family"]=="whole_vehicle_transfer" else possible[:2])
                _, targets = local_target(build, p, view, moves, settings, seed, branch, iteration)
                if not targets:
                    rejects["missing_window"] += 1
                    continue
                move, routes, problem = targets[0]
                if move and [problem.vehicle, problem.trip] not in move["affected_slots"]:
                    rejects["unaffected_window"] += 1
                    continue
                signature = tuple(sorted(problem.ids))
                if signature in excluded:
                    rejects["overlap"] += 1
                    continue
                if move:
                    try:
                        insertion_base = evaluate(p, routes, parent["calls_s"], duty)
                    except ScheduleError:
                        rejects["infeasible_parent"] += 1
                        continue
                else:
                    insertion_base = parent
                break
            else:
                raise ValueError(f"HOLDOUT_EXTRACTION_EXHAUSTED {ident}: {rejects}")
            excluded.add(signature)
            folder = HERE / "cases" / ident
            folder.mkdir(parents=True, exist_ok=True)
            local = folder / "CASE.json"
            header = dict(problem=asdict(problem), case_hash=problem.fingerprint, return_limit=4,
                          state_hash=parent["physical_hash"], insertion_parent_hash=insertion_base["physical_hash"],
                          local_source=origin, parent_move=move["move_id"] if move else None)
            for path, data in ((local, header), (folder / "parent.json", insertion_base)):
                if path.is_file():
                    from kmd_toc.iterative_v3.io import digest_payload
                    if digest_payload(read(path)) != digest_payload(data):
                        raise ValueError("UNSEALED_CASE_REBUILD_MISMATCH")
                else:
                    dump(path, data)
            holdout = dict(id=ident, scale=scale, origin=origin, input=source["input"], local=str(local),
                           parent=str(folder / "parent.json"), base=str(base_file), archived_state=str(parent_file),
                           case_hash=problem.fingerprint, window_ids=list(problem.ids), entry=problem.entry,
                           exit=problem.exit, vehicle=problem.vehicle, trip=problem.trip, offset=len(problem.prefix),
                           calls_s=insertion_base["calls_s"], moved_family=move["family"] if move else None,
                           selection_seed=problem.seed, selection_context=ctx, branch_seed=seed, attempts=attempt+1,
                           hashes={str(f):sha(f) for f in (local, folder/"parent.json", base_file, parent_file)})
            samples.append(holdout)
            extraction.append(dict(case=ident, attempts=attempt+1, **rejects))
            print("registered window", ident, "attempt", attempt+1, "offset", len(problem.prefix), flush=True)
    return samples, extraction


def prepare():
    source = SOURCE / "MANIFEST.json"
    manifest = read(source)
    if (read(SOURCE / "REGISTRATION.json")["manifest_sha256"] != sha(source)
            or read(SOURCE / "COMPLETE.json")["status"] != "COMPLETE_PILOT"):
        raise ValueError("SOURCE_REGISTRATION")
    verify_pins(manifest["code_hashes"])
    before = formal_guard()
    study = manifest["configuration"]
    settings = study["search"]["quantum"]
    if ((settings["optimizer_max_evaluations"], settings["optimizer_rhobeg"], settings["optimizer_tol"],
         settings["optimizer_restarts"], study["search"]["local_order_size"],
         study["search"]["returned_order_candidates"], study["p"], study["optimization_shots"],
         study["final_shots"]) != (24, 0.1, 0.01, 1, 12, 4, 2, 1000, 10000)
         or settings["initial_angles"] != [0.3, 0.2, 0.3, 0.2]):
        raise ValueError("CURRENT_QUANTUM_SETTINGS_CHANGED")
    jobs = [(s,b,i) for s in SCALES for b in range(4) for i in range(10)]
    with ThreadPoolExecutor(max_workers=12) as pool:
        trained = list(pool.map(archived, jobs))
    rows, archives = zip(*trained)
    if len(rows)!=120:
        raise ValueError("EXPECTED_120_TRAINING_CALLS")
    b1 = circular_median([r["beta1"] for r in rows])
    b2 = circular_median([r["beta2"] for r in rows])
    angles = dict(A=settings["initial_angles"],
                  B=[median(r["gamma1"] for r in rows), b1["value"], median(r["gamma2"] for r in rows), b2["value"]])
    derivation = dict(expected_calls=120, included_calls=len(rows), missing_calls=0, excluded_calls=0,
                      optimizer_success_count=sum(r["optimizer_success"] for r in rows),
                      adopted_count=sum(r["candidate_adopted"] for r in rows), design_order=ANGLE_NAMES,
                      angles=angles, gamma_rule="ordinary sample median of stored final angle",
                      beta_rule="pi-periodic intrinsic circular L1 median, midpoint of minimizing arc",
                      beta1=b1, beta2=b2, no_search_bounds=True)
    excluded = {tuple(sorted(a["problem"]["ids"])) for a in archives}
    cases, extraction = holdout_cases(manifest, excluded)
    seeds = []
    for n, case in enumerate(cases):
        for rep in (0,1):
            ctx = dict(stage="diagnostic", scale=case["scale"], trial=24100_000+2*n+rep, branch=0)
            stream = call_seeds(ctx, "D_quantum", 0, 24)["measurement_seeds"]
            seeds.append(dict(case_id=case["id"], replicate=rep, context=ctx, **stream,
                              classical=call_seeds(ctx, "D_classical", 0)["rng_seed"]))
    all_seeds = [seed for s in seeds for seed in (*s["optimization"],s["final"],s["classical"])]
    if len(all_seeds)!=len(set(all_seeds)):
        raise ValueError("PAIR_SEED_COLLISION")
    upstream = {str(p):sha(p) for p in (source, Path(__file__), HERE/"report.py",
                                        PREVIOUS/"pilot.py", PREVIOUS/"analyze.py", PREVIOUS/"PROTOCOL.json")}
    protocol = dict(
        version=LABEL, registered_at=datetime.now().astimezone().isoformat(), formal=before, formal_contribution=0,
        environment=dict(host=os.uname().nodename, versions={k:version(k) for k in ("numpy","scipy","qiskit")}),
        source_manifest=str(source), pinned_files=upstream, configuration=study,
        grouped_conditions=manifest["grouped_conditions"], conditions=derivation, cases=cases, seed_pairs=seeds,
        extraction_log=extraction,
        extraction_rule=("Take the four registered archived branch/checkpoint parents per scale. Try diagnostic "
                         "contexts in indexed order, using the grouped D3 proposal and local target functions. "
                         "For reallocation require a window on an affected slot and a feasible pre-order parent. "
                         "Reject any unordered 12-stop set present among the 120 derivation calls or any "
                         "already selected holdout. Use the first eligible result within 256 attempts."),
        evaluation_scope=("Insert returned orders in the fixed parent with fixed calls and retain the B-ranked "
                          "best among the parent and its feasible local orders. The archived pre-move plan is "
                          "provenance. For a reallocated case its feasible post-move plan is the common incumbent."),
        thresholds=dict(final_norm_gain=0.001, shortest_exact_gap_gain_pp=0.5,
                        local_pair_count=16, local_problem_count=8, local_scales=2,
                        global_D_km_gain=0.01, global_W_min_gain=0.25, global_I_dual_gain_pp=0.05,
                        global_pair_count=8, global_problem_count=4, global_scales=2,
                        float_equivalence=dict(normalized=1e-12, local_m=1e-8, exact_gap_pp=1e-10)),
        decision=("For each local material threshold require the all-pair median and at least 16 of 24 pairs "
                  "across at least eight distinct problems and two scales. Propose transfer only if the global "
                  "threshold is met with exact D/W non-worsening in at least eight pairs across at least four "
                  "problems and two scales, the median paired B-reference I_dual gain is nonnegative, "
                  "no pair loses the ability to return a feasible plan, and the feasible-returned-candidate "
                  "fraction is nondecreasing overall and in each scale. Otherwise retain A. Describe costs "
                  "and expectation, shortest-sampled, and shortest-returned quality separately."),
        compute="hayate managed lease, four single-CPU jobs per problem, CPUs cyclically rotated by problem index")
    dump(HERE / "INITIAL_VALUES.json", derivation)
    output_csv(HERE / "initial_angle_source.csv", rows)
    output_csv(HERE / "cases.csv", [dict(id=c["id"],scale=c["scale"],origin=c["origin"],entry=c["entry"],exit=c["exit"],
                                        vehicle=c["vehicle"],trip=c["trip"],offset=c["offset"],attempts=c["attempts"],
                                        case_hash=c["case_hash"],ids=" ".join(c["window_ids"])) for c in cases])
    dump(HERE / "PROTOCOL.json", protocol)
    print("PRE_REGISTERED", len(cases), "problems", angles, flush=True)


def registered():
    protocol = read(HERE / "PROTOCOL.json")
    if any(sha(Path(path))!=expected for path, expected in protocol["pinned_files"].items()):
        raise ValueError("PROTOCOL_SOURCE_DRIFT")
    return protocol


def worker(job_path):
    lease, binding, _ = resources.authorized(Path(os.environ["KMD_D3_LEASE_INTENT"]), worker=True)
    protocol = registered()
    if binding["job"]!=str(job_path) or lease["manifest_sha256"]!=sha(HERE/"PROTOCOL.json"):
        raise ValueError("JOB_REGISTRATION")
    job = read(job_path)
    case = next(c for c in protocol["cases"] if c["id"]==job["case"])
    seed = next(s for s in protocol["seed_pairs"] if (s["case_id"],s["replicate"])==(case["id"],job["replicate"]))
    if any(sha(Path(f))!=wanted for f,wanted in case["hashes"].items()):
        raise ValueError("HOLDOUT_INPUT_DRIFT")
    header = read(Path(case["local"]))
    problem = problem_of(header)
    folder = job_path.parent
    cfg = protocol["configuration"]
    settings = cfg["search"]["quantum"] | dict(initial_angles=protocol["conditions"]["angles"][job["arm"]],
                                              measurement_seeds=dict(optimization=seed["optimization"],final=seed["final"]))
    orders, receipt = selected_quantum(quantum.run, problem, settings, folder/"solver", 4, local_header=header)
    p = load_problem(case["input"],cfg["rest_options"])
    duty = load_policy() | {"loading_s":protocol["grouped_conditions"]["loading_s"]}
    incumbent, base = (read(Path(case[k])) for k in ("parent","base"))
    final = eval_header(folder/"solver"/"FINAL_SAMPLE.json")
    distances = [cost(problem, quantum.decode(bits, problem)) for bits in final["counts"]]
    selected = measure_orders(problem, orders, p, duty, incumbent, base, folder)
    reference = None
    if job["arm"]=="A":
        classical_orders, stats = classical(problem, cfg["search"]["classical"]|{"rng_seed":seed["classical"]}, 4)
        reference = measure_orders(problem, classical_orders, p, duty, incumbent, base, None) | stats
    dump(folder/"RESULT.json", job | selected | dict(
        scale=case["scale"], origin=case["origin"], case_hash=problem.fingerprint, bound_m=problem.lookup["bound_m"],
        exact=exact_path(problem), classical_reference=reference, incumbent=metrics(incumbent,base),
        final_norm=final["objective"], min_measured_m=min(distances), unique_orders=receipt["selector"]["unique_valid_orders"],
        valid_shots=receipt["selector"]["measured_shots"]-receipt["selector"]["invalid_shots"],
        cached_evals=receipt["cached_evaluations_reused"], selected_plan_sha256=sha(folder/"selected_plan.json"),
        **{k:receipt[k] for k in ("training_evaluations","optimizer_success","optimizer_message","optimizer_fun",
                                 "angles","wall_s","CPU_s","final_shots_actual","total_shots_actual","max_TV_bound")}))


def run():
    protocol = registered()
    if protocol["formal"]!=formal_guard():
        raise ValueError("FORMAL_BINDING_DRIFT")
    verify_pins(read(Path(protocol["source_manifest"]))["code_hashes"])
    with resources.acquire(HERE,sha(HERE/"PROTOCOL.json"),POLICY,LABEL,"paired_initial_value_pilot") as lease:
        for index, case in enumerate(protocol["cases"]):
            block = HERE/"runs"/case["id"]
            jobs = []
            for rep in (0,1):
                for ai, arm in enumerate(ARMS):
                    folder = block/f"seed_{rep}"/arm
                    folder.mkdir(parents=True,exist_ok=True)
                    if (folder/"RESULT.json").is_file():
                        continue
                    job = folder/"JOB.json"
                    data = dict(case=case["id"],replicate=rep,arm=arm,cpu=(index+2*rep+ai)%4)
                    if job.is_file():
                        if read(job)!=data:raise ValueError("JOB_CHANGED")
                    else:dump(job,data)
                    jobs.append(dict(path=job,action="_branch"))
            if jobs:
                codes, alarm = resources.supervise(lease,Path(__file__).resolve(),jobs,block,protocol["configuration"])
                if any(codes) or alarm:
                    raise RuntimeError(f"{case['id']} {codes} {alarm}")
            print(case["id"],"COMPLETE",flush=True)
    if not (HERE/"RUN_COMPLETE.json").is_file():
        dump(HERE/"RUN_COMPLETE.json",dict(cases=12,pairs=24,runs=48,formal=formal_guard(),
                                         protocol_sha256=sha(HERE/"PROTOCOL.json")))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action",choices=("prepare","run","_branch","_guard"))
    cli.add_argument("--job",type=Path)
    cli.add_argument("--intent",type=Path)
    args = cli.parse_args()
    if args.action=="_guard":return resources.guard(args.intent)
    if args.action=="_branch":worker(args.job)
    elif args.action=="run":run()
    else:prepare()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
