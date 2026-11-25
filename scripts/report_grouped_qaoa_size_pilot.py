"""Independent directed path, sample, and matched grouped-size reporting."""
from functools import lru_cache
from itertools import pairwise
from fractions import Fraction as F
from pathlib import Path
from statistics import median
import csv
import io
import math
import os
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"output/iterative_d3/qaoa_budget_grouped_v2_20261124"))
from pilot import exact_path
from kmd_toc.iterative_v3.io import atomic, read, sha
from kmd_toc.grouped_loading_v2.model import candidate_key
from kmd_toc.iterative_d3.rng_v2 import call_seeds
from kmd_toc.iterative_v3_study.analysis import delta


def write_csv(path, rows, default=("status",)):
    columns=list(dict.fromkeys(k for row in rows for k in row)) or list(default)
    temp=path.with_suffix(".csv.tmp")
    with temp.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp,path)


def independent_cost(problem, permutation):
    q=problem.lookup
    assert sorted(permutation)==list(range(problem.n))
    return (F(str(q["first"][permutation[0]]))+F(str(q["last"][permutation[-1]]))
            +sum(F(str(q["edge"][a][b])) for a,b in pairwise(permutation)))


def exact_checked(p):
    expected=exact_path(p)
    q=p.lookup
    first,last,edge=[q[k] for k in ("first","last","edge")]
    terms=[F(str(x)) for x in (*first,*last,*(v for row in edge for v in row))]
    unit=math.lcm(*(x.denominator for x in terms))
    fc=[int(F(str(x))*unit) for x in first]
    lc=[int(F(str(x))*unit) for x in last]
    arcs=[[int(F(str(x))*unit) for x in row] for row in edge]
    # Independent reverse recurrence retains only suffix costs, not forward paths.
    @lru_cache(None)
    def suffix(i, available):
        if not available:
            return lc[i]
        return min(arcs[i][j]+suffix(j,available^(1<<j)) for j in range(p.n) if available&(1<<j))
    mask=(1<<p.n)-1
    actual=F(min(fc[i]+suffix(i,mask^(1<<i)) for i in range(p.n)),unit)
    if actual!=F(expected["exact_m"]) or actual!=independent_cost(p,expected["order"]):
        raise ValueError("HELD_KARP_INDEPENDENT_RECHECK_FAILED")
    return expected|dict(independent_exact_m=str(actual),initial_m=float(independent_cost(p,range(p.n))),
                         independent_states=suffix.cache_info().currsize)


def normal_id(job):
    return {k:v for k,v in job.items() if k in ("id","phase","n","scale","method","case","rep","branch")}


def trace(folder,job,table):
    solver=folder/"solver"
    call=read(solver/"CALL.json")
    r=read(solver/"RESULT.json")
    p=call["problem"]; c=p["lookup"]; n=len(p["ids"]); width=(n-1).bit_length()
    assert n==job["n"] and (call["p"],call["optimization_shots"],call["final_shots"])==(2,1000,10000)
    setup=call["settings"]
    limit=setup["TV_bound_max"]
    seeds=call_seeds(job["context"],"D_quantum",0,24)["measurement_seeds"]
    assert setup["measurement_seeds"]==seeds and setup["optimizer_max_evaluations"]==24
    assert 1<=r["training_evaluations"]<=24 and r["sdk_qubits"]==n*width+1
    assert c["bound_m"]==max(1,(n+1)*max(c["first"]+c["last"]+[x for row in c["edge"] for x in row]))
    paths=sorted(solver.glob("EVAL_*.json"))
    assert len(paths)==r["training_evaluations"]
    for i,path in enumerate([*paths,solver/"FINAL_SAMPLE.json"]):
        f=read(path); identity=f["identity"]; last=i==len(paths)
        count=10000 if last else 1000
        assert identity["shots"]==count and sum(f["counts"].values())==count
        assert identity["phase"]==("final_extraction" if last else "optimization")
        assert identity["problem_hash"]==call["problem_hash"] and identity["seed"]==(seeds["final"] if last else seeds["optimization"][i])
        if last:
            assert identity["angles"]==r["angles"]
        assert 0<=f["TV_bound"]<=limit and 0<=f["combined_error_estimate"]<=limit
        assert all(abs(u["state_norm_squared_center"]-1)<=limit and u["canonical_residual"]<=limit for u in f["updates"])
        expected={(0,"preparation","PARTIAL_SWAP"):n-1}
        for layer in (1,2):
            expected.update({(layer,"oracle","SINGLE_PHASE"):2,(layer,"oracle","DISTANCE_PHASE"):n-1,
                             (layer,"mixer","PARTIAL_SWAP"):n-1})
        from collections import Counter
        assert Counter((u["layer"],u["stage"],u["kind"]) for u in f["updates"] if u["kind"]!="QR_MOVE")==expected
        costs=[]
        for bits,count_at_bits in f["counts"].items():
            # Decode independently, preserving register order and bit endianness.
            text=bits.zfill(n*width+1)
            assert text[0]=="0" and len(text)==n*width+1
            perm=tuple(int(text[-width*(j+1):len(text)-width*j],2) for j in range(n))
            assert sorted(perm)==list(range(n))
            d=math.fsum([c["first"][perm[0]],*(c["edge"][a][b] for a,b in pairwise(perm)),c["last"][perm[-1]]])
            costs.append((d,count_at_bits))
        mean=math.fsum(d*w for d,w in costs)/count/c["bound_m"]
        assert math.isclose(mean,f["objective"],abs_tol=1e-12,rel_tol=0)
        table.append(normal_id(job)|dict(evaluation=i+1 if not last else 0, phase=identity["phase"],
            seed=identity["seed"],shots=count,objective=mean,TV_bound=f["TV_bound"],peak_bond=f["peak_bond"],
            **dict(zip(("gamma1","beta1","gamma2","beta2"),identity["angles"]))))
    return dict(final_normalized_mean=mean,min_measured_m=min(d for d,_ in costs),
                unique_orders=len(costs),permutation_feasible_rate=1.0,
                order_diversity_entropy_nats=-math.fsum(w/count*math.log(w/count) for _,w in costs))


def local_quality(row, exact):
    shortest_returned=min((r["local_distance_m"] for r in row["candidates"]),default=None)
    best=row.get("min_measured_m",shortest_returned)
    initial,optimum=exact["initial_m"],exact["distance_m"]
    opportunity=F(str(initial))-F(exact["exact_m"])
    def gap(v):
        return None if not optimum or v is None else 100*(v-optimum)/optimum
    return dict(initial_m=initial,exact_m=optimum,opportunity_m=float(opportunity),
        opportunity_is_zero=math.isclose(initial,optimum,abs_tol=1e-8,rel_tol=0),
        shortest_returned_m=shortest_returned, shortest_sample_or_classical_m=best,
        shortest_returned_gap_pp=gap(shortest_returned),best_gap_pp=gap(best),
        improvement_m=initial-shortest_returned if shortest_returned is not None else None,
        improvement_percent=100*(initial-shortest_returned)/initial if initial and shortest_returned is not None else None,
        realized_opportunity_percent=(100*(initial-shortest_returned)/float(opportunity)
            if not math.isclose(initial,optimum,abs_tol=1e-8,rel_tol=0) and shortest_returned is not None else None))


def plot(out, local, full, traces):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    dest=out/"figures";dest.mkdir(exist_ok=True)
    def points(name, data, specs):
        fig, axes=plt.subplots(1,len(specs),figsize=(4.2*len(specs),4),squeeze=False,layout="constrained")
        for ax,(col,title) in zip(axes[0],specs):
            for method,marker in (("D_classical","x"),("D_quantum","o")):
                rows=[r for r in data if r["method"]==method and r.get(col) is not None]
                if rows:
                    ax.scatter([r["n"] for r in rows],[r[col] for r in rows],marker=marker,alpha=.6,label=method)
            ax.set(xlabel="Local window n",ylabel=title,xticks=[10,12,14])
            if ax.get_legend_handles_labels()[0]:ax.legend()
        fig.savefig(dest/(name+".svg"));plt.close(fig)
    points("local_quality",local,[("shortest_returned_gap_pp","Returned gap to exact (%)"),
                                    ("opportunity_m","Distance opportunity (m)")])
    points("global_quality",full,[("L_km","Total distance (km)"),("W_min_per_configured_vehicle_day","Wait (min/vehicle/day)"),
                                  ("I_dual_B_pp","I_dual vs B (%)")])
    points("compute",full,[("wall_s","Measured wall (s)"),("peak_RSS_MiB","Peak branch RSS (MiB)")])
    for name,cols in (("learning_expectation",["objective"]),("angle_trace",["gamma1","beta1","gamma2","beta2"])):
        fig,axes=plt.subplots(len(cols),3,figsize=(12,2.8*len(cols)),squeeze=False,layout="constrained")
        for l,col in enumerate(cols):
            for j,n in enumerate((10,12,14)):
                ax=axes[l][j]
                ids={r["id"] for r in traces if r["n"]==n and r["phase"]=="optimization"}
                for ident in sorted(ids):
                    rows=[r for r in traces if r["id"]==ident and r["phase"]=="optimization"]
                    ax.plot([r["evaluation"] for r in rows],[r[col] for r in rows],alpha=.22)
                ax.set(title=f"n={n}",xlabel="COBYLA evaluation",ylabel=col)
        fig.savefig(dest/(name+".svg"));plt.close(fig)


def report(out,manifest,rows,allowed,formal):
    protocol=read(out/"PROTOCOL.json")
    exact={}; classical=[]; quantum=[]; traces=[]; candidates=[]; incomplete=[]; full=[]; branch_groups={}
    for row in rows:
        j=row["job"]; identity=normal_id(j); status=row["status"]
        if status!="COMPLETE":
            incomplete.append(identity|dict(status=status,reason=row.get("result")))
            continue
        v=row["result"]
        if j["phase"]=="exact":
            exact[j["case"],j["n"]]=identity|v
        if j["phase"] in ("classical","local","technical"):
            folder=out/"jobs"/j["id"]
            check=trace(folder,j,traces) if j["phase"]!="classical" else {}
            if j["phase"]=="technical":
                continue
            r=identity|{k:val for k,val in v.items() if k not in ("candidates","selected")}
            r|=v["selected"]|check|local_quality(v|check,exact[j["case"],j["n"]])
            (classical if j["phase"]=="classical" else quantum).append(r)
            candidates.extend(identity|record for record in v["candidates"])
        if j["phase"]=="outer":
            branch_groups.setdefault((j["scale"],j["n"],j["method"]),[]).append(row)
    for (scale,n,method),group in branch_groups.items():
        base=read(Path(manifest["saved_references"][scale]["B"]["path"]))
        cp=read(Path(manifest["saved_references"][scale]["C_Idual"]["path"]))
        plans=[]; adoption=[]; windows=[]; completed=0
        for r in group:
            j=r["job"]; v=r["result"]
            folder=out/"jobs"/j["id"]/"branch"
            plan=read(folder/"plan.json")
            assert v["metrics"]["physical_hash"]==plan["physical_hash"] and v["used"]<=70 and v["completed"]<=10
            plans.append((j["branch"],plan))
            old_used=0; chain=base["physical_hash"]; call_count=0
            for f in sorted(folder.glob("iteration_*/COMMIT.json")):
                marker=read(f)
                assert marker["input_hash"]==chain
                chain=marker["state_hash"]
                local=f.parent/"local_000"/"CASE.json"
                if local.is_file():
                    ids=read(local)["problem"]["ids"]
                    assert len(ids)==n
                    windows.extend(ids)
                    call_count+=1
                adopted=next((x["kind"] for x in marker["candidate_receipts"] if x.get("id")==marker["adopted"]),None)
                adoption.append(adopted)
                attempts=sum(r["kind"]!="local_search" for r in marker["candidate_receipts"])
                assert attempts<=7 and marker["used"]-old_used==attempts
                old_used=marker["used"]
            assert old_used==v["used"] and call_count==v["calls"]
            completed+=old_used
        assert len(plans)==4
        b, plan=min(plans,key=lambda t:candidate_key(t[1],base,initial=t[1]["physical_hash"]==base["physical_hash"],branch_id=t[0]))
        full.append(dict(scale=scale,n=n,method=method,chosen_branch=b,status="COMPLETE",L_km=plan["L_km"],
            D_exact=plan["D_exact"],W_exact=plan["W_exact"],W_total_min=plan["W_total_min"],
            D_km_per_parcel=plan["D_km_per_parcel"],W_min_per_configured_vehicle_day=plan["W_min_per_configured_vehicle_day"],
            W1_s=plan["W1_s"],W2_s=plan["W2_s"],before_reception_total_s=plan["before_reception_total_s"],
            I_dual_B_pp=delta(plan,base)["I_dual_percent"],I_dual_C_posthoc_pp=delta(plan,cp)["I_dual_percent"],
            selected_plan_sha256=sha(out/"jobs"/next(r["job"]["id"] for r in group if r["job"]["branch"]==b)/"branch/plan.json"),
            local_adoptions=sum(k is not None and "order" in k for k in adoption),
            reception_adoptions=adoption.count("reception_time"),reallocation_adoptions=adoption.count("classical_reallocation_only"),
            completed_searches=4,completions=completed,window_exposures=len(windows),unique_customers=len(set(windows)),
            exposure_overlap_count=len(windows)-len(set(windows)),coverage_percent=100*len(set(windows))/plan["parcels"],
            cpu_s=sum(r["cpu_s"] for r in group),wall_s=max(r["wall_s"] for r in group),
            peak_RSS_MiB=max(r["peak_RSS_MiB"] for r in group)))
    paired=[]
    for data,keys,metrics in ((quantum,("case","rep"),("best_gap_pp","shortest_returned_gap_pp","opportunity_m","L_km","W_total_min")),
        (full,("scale","method"),("L_km","W_total_min","I_dual_B_pp","wall_s","peak_RSS_MiB"))):
        b={tuple(r[k] for k in keys):r for r in data if r["n"]==12}
        for r in data:
            ref=b.get(tuple(r[k] for k in keys))
            if r["n"]==12 or ref is None: continue
            paired.append({k:r[k] for k in keys}|dict(layer="local" if "rep" in keys else "outer",
                scale=r["scale"],n=r["n"],ref_n=12)|{k:r[k]-ref[k] for k in metrics if r.get(k) is not None and ref.get(k) is not None})
    classic_by_key={(r["case"],r["rep"],r["n"]):r for r in classical}
    for r in quantum:
        other=classic_by_key[r["case"],r["rep"],r["n"]]
        r["Q_minus_classical_shortest_returned_m"]=r["shortest_returned_m"]-other["shortest_returned_m"]
        paired.append(dict(layer="QAOA_vs_classical",case=r["case"],scale=r["scale"],rep=r["rep"],n=r["n"],
                           shortest_returned_m=r["Q_minus_classical_shortest_returned_m"],
                           L_km=r["L_km"]-other["L_km"],W_total_min=r["W_total_min"]-other["W_total_min"]))
    thresholds=protocol["budgets"]; qfull=[r for r in paired if r["layer"]=="outer" and r["method"]=="D_quantum"]
    decisions={}
    recommend=12 if 12 in allowed else None
    for n in (10,14):
        a=[r for r in qfull if r["n"]==n]
        local=[r for r in paired if r["layer"]=="local" and r["n"]==n and "shortest_returned_gap_pp" in r]
        if len(a)!=3 or len(local)!=24:
            decisions[n]="insufficient paired results";continue
        mg=median(r["shortest_returned_gap_pp"] for r in local)
        dk=thresholds["global_D_km_gain_min"]; wk=thresholds["global_W_min_gain_min"]; ik=thresholds["global_I_dual_pp_gain_min"]
        gains=sum(r["L_km"]<=0 and r["W_total_min"]<=0 and
                  (r["L_km"]<=-dk or r["W_total_min"]<=-wk or r.get("I_dual_B_pp",-math.inf)>=ik) for r in a)
        any_loss=any(r["L_km"]>0 or r["W_total_min"]>0 for r in a)
        qualifies=(gains>=2 and not any_loss) if n==14 else (
            mg<=thresholds["block_shortest_gap_gain_pp_min"] and all(r["L_km"]<dk and r["W_total_min"]<wk for r in a)
            and median(r["wall_s"] for r in a)<0 and median(r["peak_RSS_MiB"] for r in a)<0)
        decisions[n]=dict(qualifies=qualifies,median_local_gap_difference_pp=mg,material_global_gains=gains)
        if qualifies and recommend is not None: recommend=n
    resources_=[normal_id(r["job"])|{k:r[k] for k in ("status","wall_s","cpu_s","peak_RSS_MiB") if k in r} for r in rows]
    for name,data in (("EXACT_SOLUTIONS",list(exact.values())),("CLASSICAL_RESULTS",classical),("QAOA_RESULTS",quantum),
        ("QAOA_EVALUATIONS",traces),("CANDIDATES",candidates),("FULL_PLAN_RESULTS",full),
        ("PAIRED_COMPARISONS",paired),("RESOURCE_USAGE",resources_),("UNEXECUTED_OR_FAILED",incomplete)):
        write_csv(out/f"{name}.csv",data)
    plot(out,classical+quantum,full,traces)
    atomic(out/"FINAL_VALIDATION.json",dict(formal=formal,allowed_sizes=sorted(allowed),exact_rechecks=len(exact),
        sample_records_rechecked=len(traces),combined_local_rows=len(classical)+len(quantum), full_plan_count=len(full),
        incomplete_count=len(incomplete),recommendation=recommend,decision_detail=decisions))
    lines=["# grouped-v2 QAOA局所サイズ限定予備",f"採用提案 n＝{recommend}" if recommend else "採用提案 HOLD",
        f"技術通過 {sorted(allowed)}。局所QAOA {len(quantum)}／72、外側の方式実行 {len(full)}／18。",
        f"失敗・未実行 {len(incomplete)}件。登録の全件と理由は UNEXECUTED_OR_FAILED.csv を参照。",
        "", "| 規模 | n | 方式 | 総距離 km | 荷待ち 分/台・日 | B基準I_dual % | 壁秒 | 最大枝RSS MiB |",
        "|---|---:|---|---:|---:|---:|---:|---:|"]
    for r in full:
        label=f'{r["I_dual_B_pp"]:.4f}' if r["I_dual_B_pp"] is not None else "NA"
        lines.append(f'| {r["scale"]} | {r["n"]} | {r["method"]} | {r["L_km"]:.4f} | '
            f'{r["W_min_per_configured_vehicle_day"]:.4f} | {label} | {r["wall_s"]:.3f} | {r["peak_RSS_MiB"]:.1f} |')
    lines+=["",f"採用基準への照合 {decisions}。","", "各規模1ケースの記述比較である。"
        "異なるnは局所境界と正規化係数が変わるため、期待値の水準はn内の最適化軌跡として解釈する。"
        "外側の適応探索では軌跡が分かれ得る。正式条件への反映には研究者の承認が必要である。"]
    text=out/"FINAL_REPORT.md.tmp";text.write_text("\n".join(lines)+"\n",encoding="utf-8")
    text.replace(out/"FINAL_REPORT.md")
