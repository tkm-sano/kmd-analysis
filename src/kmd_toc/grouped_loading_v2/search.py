"""Bounded grouped D3 search, sharing operators, seeds, and order kernels."""
from dataclasses import asdict
import fcntl
from pathlib import Path
import random
import resource
import time

from kmd_toc.iterative_d3.operators import local_target, proposals, selected_quantum
from kmd_toc.iterative_d3.overlay import build_function
from kmd_toc.iterative_d3.rng_v2 import call_seeds
from kmd_toc.iterative_v3 import reallocation
from kmd_toc.iterative_v3.io import assignment_hash, decode_routes, digest_payload, dump, encode_routes, read
from kmd_toc.iterative_v3.order import build, classical, expand
from kmd_toc.iterative_v3.quantum import run as quantum
from .methods import call_move, route_view
from .model import ScheduleError, candidate_key, evaluate, measure

generate = build_function(reallocation,"generate",[
    ("max_candidates=None):", "max_candidates=None, families=('inter_relocate','inter_swap','intra_transfer')):"),
    ("for family in ('inter_relocate','inter_swap','intra_transfer'):","for family in families:"),
])


def summarize(plan):
    return {k:plan[k] for k in ("physical_hash","D_exact","W_exact","W1_s","W2_s","calls_s","before_reception_total_s","final_return_s")}


def candidate(out, p, duty, routes, calls, name, origin, parent, move=None):
    key = digest_payload(dict(routes=encode_routes(routes),calls=list(calls)))
    path = out/(name+".json")
    if path.exists():
        row = read(path)
        if row["candidate_key"] != key or row["parent"]["physical_hash"] != parent["physical_hash"]:
            raise ValueError("GROUPED_CANDIDATE_REPLAY_MISMATCH")
        return row
    row = dict(candidate_key=key,kind=origin,parent=summarize(parent),status="FEASIBLE",
               calls_s=list(calls),move_id=move["move_id"] if move else None)
    try:
        row["plan"] = evaluate(p,routes,calls,duty)
    except ScheduleError as error:
        row.update(status="INFEASIBLE",reason=str(error),plan=None)
    dump(path,row)
    return row


def run(p, base, out, condition, settings, seed, branch, duty, *, pause_after=None):
    if condition not in ("D_classical","D_quantum"):
        raise ValueError("D3_CONDITION")
    out = Path(out)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"LOCK").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return run_locked(p,base,out,condition,settings,seed,branch,duty,pause_after)


def run_locked(p,base,out,condition,settings,seed,branch,duty,pause_after):
    start, cpu = time.monotonic(), time.process_time()
    contract = dict(version="grouped-loading-20261124-v2",condition=condition,branch=branch,
                    seed=seed,settings=settings,initial_hash=base["physical_hash"],duty=duty)
    if (out/"START.json").exists():
        if read(out/"START.json")!=contract:raise ValueError("GROUPED_BRANCH_CONTRACT_CHANGED")
    else:dump(out/"START.json",contract)
    if (out/"RESULT.json").exists():
        return read(out/"RESULT.json")
    key = lambda p: candidate_key(p,base,initial=p["physical_hash"]==base["physical_hash"])
    state = best = base
    tabu = reallocation.Tabu(settings["tabu_tenure"])
    rng = random.Random(seed)
    used = calls = shots = 0
    completed = 0
    for i in range(settings["outer_iterations"]):
        folder = out/f"iteration_{i:04d}"
        folder.mkdir(exist_ok=True)
        marker = folder/"COMMIT.json"
        if marker.exists():
            row = read(marker)
            if row["input_hash"]!=state["physical_hash"]:raise ValueError("GROUPED_REPLAY_STATE_CHAIN")
            state,best = read(folder/row["state_file"]),read(folder/row["best_file"])
            if (state["physical_hash"],best["physical_hash"]) != (row["state_hash"],row["best_hash"]):
                raise ValueError("GROUPED_REPLAY_PLAN_HASH")
            used,calls,shots = row["used"],row["calls"],row["shots"]
            tabu = reallocation.Tabu(settings["tabu_tenure"],row["tabu"])
            completed += 1
            continue
        remaining = settings["physical_completion_budget"]-used
        if remaining<=0:break
        source = route_view(state)
        rs = decode_routes(state["routes"])
        # Reserve one of the three existing classical evaluation slots for time.
        possible, audit = proposals(generate,p,source,rng,settings,seed,i,3)
        if len(possible)>2:
            possible = [possible[0],possible[-1]] if possible[-1]["family"]=="whole_vehicle_transfer" else possible[:2]
        moves = possible[:min(2,max(0,remaining-1))]
        admissible = [(state,None,"current")]
        receipts = []
        prior_best = best

        def submit(routes, times, cid, origin, parent, move=None):
            nonlocal used,best
            row = candidate(folder,p,duty,routes,times,cid,origin,parent,move)
            used += 1
            receipts.append({k:v for k,v in row.items() if k!="plan"}|
                            dict(id=cid,metrics=summarize(row["plan"]) if row["plan"] else None))
            plan = row["plan"]
            if plan:
                if key(plan)<key(best):best=plan
                if move is None or not tabu.prohibited(move,i) or key(plan)<key(prior_best):
                    admissible.append((plan,move,cid))
            return plan

        timing = call_move(p,rs,state["calls_s"],i)
        submit(rs,timing,"timing","reception_time",state)
        parents = {}
        for j,move in enumerate(moves):
            rs_move = decode_routes(move["routes"])
            plan = submit(rs_move,state["calls_s"],f"reallocation_{j}","classical_reallocation_only",state,move)
            parents[move["move_id"]] = plan
        local_source,targets = local_target(build,p,source,moves,settings,seed,branch,i)
        for move,assigned,case in targets:
            limit = min(settings["returned_order_candidates"],settings["physical_completion_budget"]-used)
            if limit<=0:break
            local = folder/"local_000"
            local.mkdir(exist_ok=True)
            header = dict(problem=asdict(case),case_hash=case.fingerprint,assignment_before=case.assignment_hash,
                          return_limit=limit,state_hash=state["physical_hash"],
                          parent_move=move["move_id"] if move else None,local_source=local_source)
            case_file = local/"CASE.json"
            if case_file.exists():
                if digest_payload(read(case_file))!=digest_payload(header):raise ValueError("GROUPED_LOCAL_RESUME_CONTRACT")
            else:dump(case_file,header)
            calls += 1
            seeds = call_seeds(settings["rng_v2"],condition,i,settings["quantum"]["optimizer_max_evaluations"])
            if condition=="D_quantum":
                orders,receipt = selected_quantum(quantum,case,settings["quantum"]|seeds,local/"solver",limit,
                                                  local_header=header)
            else:
                saved = local/"CLASSICAL_RESULT.json"
                if saved.exists():
                    cached = read(saved)
                    orders,receipt = cached["orders"],cached["receipt"]
                else:
                    orders,receipt = classical(case,settings["classical"]|seeds,limit)
                    dump(saved,dict(orders=orders,receipt=receipt))
            shots += receipt.get("total_shots_actual",0)
            parent = state if move is None else parents[move["move_id"]]
            for j,item in enumerate(orders):
                expanded = expand(case,tuple(item["order"]))
                if assignment_hash(expanded)!=case.assignment_hash:raise ValueError("ORDER_CHANGED_ASSIGNMENT")
                # Infeasible pre-order completions are retained as explicitly unavailable parent metrics.
                submit(expanded,state["calls_s"],f"order_{j}",item["source"],parent or state,move)
                receipts[-1]["matching_parent_available"] = parent is not None
            receipts.append(dict(kind="local_search",case_hash=case.fingerprint,seed=seeds,receipt=receipt))
        chosen,move,origin = min(admissible,key=lambda x:key(x[0]))
        if chosen["physical_hash"]!=state["physical_hash"] and move:tabu.record(move,i)
        for file,val in (("state.json",chosen),("best.json",best)):
            if (folder/file).exists():
                if read(folder/file)!=val:raise ValueError("GROUPED_UNCOMMITTED_STATE_MISMATCH")
            else:dump(folder/file,val)
        row = dict(iteration=i,input_hash=state["physical_hash"],input_calls_s=state["calls_s"],
                   state_hash=chosen["physical_hash"],state_calls_s=chosen["calls_s"],best_hash=best["physical_hash"],
                   state_file="state.json",best_file="best.json",adopted=origin,tabu=tabu.entries,
                   candidate_receipts=receipts,neighbor_audit=audit,used=used,calls=calls,shots=shots)
        dump(marker,row)
        state = chosen
        completed += 1
        if pause_after is not None and completed>=pause_after:return dict(status="PAUSED",completed=completed)
    if used>settings["physical_completion_budget"]:raise ValueError("GROUPED_COMPLETION_LIMIT")
    if (out/"plan.json").exists():
        if read(out/"plan.json")!=best:raise ValueError("GROUPED_FINAL_PLAN_MISMATCH")
    else:dump(out/"plan.json",best)
    result = dict(status="COMPLETE",branch=branch,condition=condition,completed=completed,used=used,calls=calls,shots=shots,
                  stop_reason="completion_limit" if used==settings["physical_completion_budget"] else "iteration_limit",
                  metrics=summarize(best),wall_s=time.monotonic()-start,cpu_s=time.process_time()-cpu,
                  rss_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    dump(out/"RESULT.json",result)
    return result
