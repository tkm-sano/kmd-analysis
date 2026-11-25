"""Freeze the native comparison members once and consume them in every report."""
from collections import Counter
import csv
from fractions import Fraction
from pathlib import Path

from kmd_toc.iterative_v3.io import dump, load_plan, sha
from kmd_toc.iterative_v3_study.analysis import stat, summarize

COMPARISONS = {
    "primary_B_C": ("primary", "B", "C_Idual"),
    "primary_B_Q": ("primary", "B", "D_quantum"),
    "primary_C_Q": ("primary", "C_Idual", "D_quantum"),
    "control_classical_quantum": ("control", "D_classical", "D_quantum"),
}
REQUIRED = {"primary": ("C_Idual", "D_quantum"), "control": ("D_classical", "D_quantum")}
NORMAL = {"NORMAL_CHANGED", "NORMAL_INITIAL_RETAINED"}
METRICS = ("L_km", "D_km_per_parcel", "W_min")
PAIRED = ("delta_D_km", "delta_D_km_per_parcel", "delta_W_min", "relative_D_percent",
          "relative_W_percent", "I_dual_percent", "delta_I_dual_pi0_percentage_points")
A_REF = 0.58


def parcel_evidence(plan_path, expected):
    """Count delivered items from validated stop IDs and pinned integer demands."""
    plan = load_plan(plan_path)
    visits = Counter(v.stop_id for trip in plan.trips for v in trip.visits)
    if visits != Counter(expected.keys()):
        raise ValueError("PLAN_COVERAGE_MISMATCH")
    return sum(expected[s] for s in visits)


def selection(manifest, observations):
    registered = {c["trial_id"]: c for c in manifest["cases"]}
    by_id = {r["trial_id"]: r for r in observations}
    if len(registered) != len(manifest["cases"]) or len(by_id) != len(observations) or registered.keys() != by_id.keys():
        raise ValueError("REGISTERED_OBSERVATION_SET_MISMATCH")
    for trial, row in by_id.items():
        case = registered[trial]
        for field in ("scale", "seed", "problem_hash", "od_hash", "initial_plan_sha256"):
            if row[field] != case[field]:
                raise ValueError(f"OBSERVATION_BINDING_MISMATCH:{trial}:{field}")
        for method, data in row["methods"].items():
            if data["eligible"] != (data["status"] in NORMAL):
                raise ValueError(f"COMPLETION_ELIGIBILITY_MISMATCH:{trial}:{method}")
    native = summarize(observations)
    cohorts = {x["scale"]: x for x in native["cohorts"]}
    comparisons = []
    for scale, cohort in cohorts.items():
        for key, (group, baseline, candidate) in COMPARISONS.items():
            ids = cohort[group + "_trial_ids"]
            excluded = {}
            for trial, case in registered.items():
                if case["scale"] == scale and trial not in ids:
                    excluded[trial] = [
                        {"method": method, "status": data["status"],
                         "reason_code": data.get("reason_code"), "reason": data.get("reason")}
                        for method in REQUIRED[group] if not (data := by_id[trial]["methods"][method])["eligible"]
                    ]
            paired = next(x for x in native["paired_statistics"] if x["scale"] == scale
                          and x["comparison"] == key and x["metric"] == "delta_D_km")
            if paired["paired_trial_ids"] != ids or any(not reason for reason in excluded.values()):
                raise ValueError(f"NATIVE_COMPARISON_MEMBERSHIP_MISMATCH:{scale}:{key}")
            comparisons.append(dict(scale=scale, comparison=key, group=group, baseline=baseline,
                candidate=candidate, required_normal=list(REQUIRED[group]), fixed_B=True,
                trial_ids=ids, J_eff=len(ids), planned_J=manifest["formal_J"], excluded=excluded,
                raw_pairs=paired["values"], bindings={t: {k: registered[t][k] for k in
                  ("input", "problem_hash", "od_hash", "initial_plan_sha256", "seed")} for t in ids}))
    return native, comparisons


def denominator(row, baseline, candidate):
    values = row["parcel_counts"]
    observed = {method: values.get(method) for method in ("B", baseline, candidate)}
    errors = {}
    for method, value in observed.items():
        if value is None:
            errors[method] = "PARCEL_COUNT_MISSING"
        elif type(value) is not int or value <= 0:
            errors[method] = "PARCEL_COUNT_NOT_POSITIVE_INTEGER"
    if not errors and len(set(observed.values())) != 1:
        errors["comparison"] = "PARCEL_COUNT_MISMATCH"
    return observed, errors


def csvfile(target, name, fields, rows):
    with (target / name).open("x", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metric_stats(values):
    out = stat(values)
    if len(values) > 1 and all(x == values[0] for x in values):
        out.update(SD=0.0, MCSE=0.0, observed_zero_SD=True, mean=values[0])
    return out


def report(target, observations, comparisons):
    by_id = {r["trial_id"]: r for r in observations}
    distances, paired, plot_data, reports = [], [], [], []
    for comp in comparisons:
        key = {k: comp[k] for k in ("scale", "comparison", "group")}
        base, candidate = comp["baseline"], comp["candidate"]
        members = comp["trial_ids"]
        if [r["trial_id"] for r in comp["raw_pairs"]] != members:
            raise ValueError("BOUND_PAIR_IDS_CHANGED")
        errors, values, deltas = {}, {base: [], candidate: []}, []
        for trial, raw in zip(members, comp["raw_pairs"]):
            row = by_id[trial]
            counts, problems = denominator(row, base, candidate)
            if problems:
                errors[trial] = dict(reasons=problems, observed=counts, source=row.get("parcel_evidence_errors", {}))
            record = {}
            for method in (base, candidate):
                metric = row["baseline_metrics"] if method == "B" else row["methods"][method]["metrics"]
                length, wait = Fraction(metric["D_exact"]), Fraction(metric["W_exact"])
                value = dict(**key, trial_id=trial, method=method, parcel_count=counts[method], L_km=float(length),
                             D_km_per_parcel=None if problems else float(length / counts[method]), W_min=float(wait),
                             L_km_exact=str(length), W_min_exact=str(wait), status="INVALID_DENOMINATOR" if problems else "OK")
                values[method].append(value)
                distances.append(value)
                record[method] = length
            delta = dict(**raw, group=comp["group"], delta_D_km_per_parcel=None if problems else
                         float((record[candidate] - record[base]) / counts[candidate]),
                         status="INVALID_DENOMINATOR" if problems else "OK")
            deltas.append(delta)
            paired.append(delta)
        reports.append(dict(**key, trial_ids=members, J_eff=comp["J_eff"], exclusions=comp["excluded"],
                            denominator_errors=errors, state="INVALID_DENOMINATOR" if errors else "READY" if members else "EMPTY"))
        for method, rows in values.items():
            for metric in METRICS:
                plot_data.append(dict(**key, kind="absolute", series=method, metric=metric, trial_ids=members,
                    fixed_reference=method == "B", values=[r[metric] for r in rows]))
        for metric in PAIRED:
            plot_data.append(dict(**key, kind="paired", series=candidate, metric=metric, trial_ids=members,
                fixed_reference=False, values=[r[metric] for r in deltas]))
    for block in plot_data:
        values = block["values"]
        valid = [v for v in values if v is not None]
        block["undefined_trial_ids"] = [t for t, v in zip(block["trial_ids"], values) if v is None]
        if block["metric"] in ("D_km_per_parcel", "delta_D_km_per_parcel") and block["undefined_trial_ids"]:
            block["statistics"] = None
        elif block["fixed_reference"]:
            if len(set(valid)) > 1:
                raise ValueError("FIXED_REFERENCE_CHANGED")
            block["statistics"] = dict(J_eff=0, reference_value=valid[0] if valid else None)
        else:
            block["statistics"] = metric_stats(valid)
    csvfile(target, "DISTANCE_TRIALS.csv", ["scale","comparison","group","trial_id","method","parcel_count",
            *METRICS,"L_km_exact","W_min_exact","status"], distances)
    csvfile(target,"PAIRED_TRIALS.csv",["scale","trial_id","comparison","baseline","candidate","delta_D_km","delta_W_min",
            "relative_D_percent","relative_W_percent","I_dual_percent","strict_dual","nonworse","tolerance_D_km",
            "tolerance_W_min","unit","delta_I_dual_pi0_percentage_points","group","delta_D_km_per_parcel","status"],paired)
    index = plot(target, plot_data)
    dump(target/"PLOT_DATA.json", plot_data)
    dump(target/"FIGURE_INDEX.json", index)
    dump(target/"COMPARISON_REPORT.json", reports)
    csvfile(target,"SUMMARY_TABLE.csv",["scale","comparison","series","kind","metric","comparison_J_eff","metric_J_eff",
              "trial_ids","undefined_trial_ids","mean","SD","MCSE","median","Q1","Q3","IQR","min","max","reference_value"],
            [{k:b[k] for k in ("scale","comparison","series","kind","metric","trial_ids","undefined_trial_ids")} |
             {"comparison_J_eff":len(b["trial_ids"]), "metric_J_eff":(b["statistics"] or {}).get("J_eff")} |
             {k:(b["statistics"] or {}).get(k) for k in ("mean","SD","MCSE","median","Q1","Q3","IQR","min","max","reference_value")}
             for b in plot_data])
    return reports


def plot(target, blocks):
    if not any(b["trial_ids"] for b in blocks):
        return []
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    index = []
    for scale, key in dict.fromkeys((b["scale"], b["comparison"]) for b in blocks if b["trial_ids"]):
        group = [b for b in blocks if (b["scale"], b["comparison"]) == (scale, key)]
        absolute = ("D_km_per_parcel", "W_min")
        extras = ("delta_D_km_per_parcel", "delta_W_min", "relative_D_percent", "relative_W_percent", "I_dual_percent")
        for mode, metrics in (("boxplot", absolute), ("mean_sd", absolute), ("paired", extras)):
            fig, axes = plt.subplots(1,len(metrics),squeeze=False, figsize=(3.5*len(metrics),3.2),layout="constrained")
            plotted = []
            for ax, metric in zip(axes[0], metrics):
                rows = [b for b in group if b["metric"] == metric]
                for x, b in enumerate(rows, 1):
                    valid = [v for v in b["values"] if v is not None]
                    if b["statistics"] is None or not valid:
                        continue
                    if b["fixed_reference"]:
                        ax.axhline(valid[0], color="#596774", linestyle=":", label="Fixed B")
                    elif mode == "boxplot" and len(valid) > 1:
                        ax.boxplot(valid, positions=[x], whis=1.5, manage_ticks=False)
                    else:
                        ax.errorbar(x, b["statistics"]["mean"], yerr=b["statistics"]["SD"] if mode != "boxplot" else None,
                                    fmt="o", color="#176d86")
                    plotted.append({"metric":metric,"series":b["series"],"trial_ids":b["trial_ids"],
                                    "undefined_trial_ids":b["undefined_trial_ids"]})
                if metric == "D_km_per_parcel":
                    ax.axhline(A_REF, color="#b0612c", linestyle="--", label="A (0.58)")
                    ax.legend(frameon=False)
                ax.set_xticks(range(1,len(rows)+1),[b["series"] for b in rows],rotation=20)
                ax.set_title(metric)
            fig.suptitle(f"{scale} · {key} · n={len(group[0]['trial_ids'])}")
            file = f"{scale}_{key}_{mode}.png"
            fig.savefig(target/file,dpi=120)
            plt.close(fig)
            index.append(dict(file=file,sha256=sha(target/file),scale=scale,comparison=key,
                              trial_ids=group[0]["trial_ids"],plotted=plotted))
    return index
