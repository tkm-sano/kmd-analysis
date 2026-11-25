#!/usr/bin/env python3
"""Recheck saved grouped-v2 plans and render the pilot publication figures."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, stdev
import sys

SCALES = ("S1", "S2", "S3")
LABELS = dict(zip(SCALES, ("実験①", "実験②", "実験③")))
METHODS = {"B": "B", "C": "C_Idual", "D": "D_quantum"}
METRICS = ("dual_pct", "km_per_parcel", "wait_min_per_research_run")
COLORS = {"B": "#626970", "C": "#2666A1", "D": "#C46224"}
DIST_URL = "https://www.mlit.go.jp/common/001102289.pdf#page=4"
WAIT_URL = "https://www.mlit.go.jp/report/press/content/002011131.pdf#page=2"
REPORT_URL = "https://www.mlit.go.jp/common/001106397.pdf#page=9"
VERSION = "grouped-loading-20261124-v2"
A_ROWS = [
    dict(metric="走行距離", reference_value="0.58", unit="km／行政資料の取扱個数", sd="",
         agency="国土交通省", source="宅配の再配達の発生による社会的損失の試算について",
         publication="2015-08-25", page="PDF p.4, 注1", source_url=DIST_URL, confirming_url=REPORT_URL,
         scope="宅配事業者数社の配達車。幹線輸送を除く。大田区の研究条件との対応は未確認。",
         denominator="資料提供事業者の取扱個数。事業者別の分母・標本数は非公表。",
         calculation="配達車の走行距離 ÷ 取扱個数。2014年度全国取扱個数は別途CO2試算に使用。",
         comparability="km／個で表示できる外部参照。取扱個数と配送済み箱数の対応、再配達・地域・運用条件の一致は未確認。"),
    dict(metric="荷待ち時間", reference_value="60", unit="分／行政調査上の運行", sd="",
         agency="国土交通省", source="トラックドライバーの1運行当たりの平均拘束時間に関する調査結果",
         publication="2026-07-10", page="PDF pp.1–2, 2025年度", source_url=WAIT_URL,
         confirming_url="https://www.mlit.go.jp/report/press/tokatsu02_hh_000084.html",
         scope="一般貨物自動車運送事業の実運送事業者。宅配限定ではない。2025年4～8月の通常期の代表的な1日の運行。",
         denominator="2025年度比較グラフ n=1,032。便を何件束ねたか、ゼロ荷待ち回答の扱い・重み付けの詳細は公表資料から確定できない。",
         calculation="1運行当たり平均拘束時間の内訳のうち荷待ち1時間。荷役・附帯作業との合計は2時間2分。",
         comparability="行政調査の運行単位と待機範囲は研究上の稼働車両日・拠点積込待機に換算できない。図3の独立参照欄に表示。"),
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def archived_path(root, path):
    parts = Path(path).parts
    return root.joinpath(*parts[parts.index("output"):])


def publication_status(plan_path, receipt_path, audit_row):
    if not (plan_path.is_file() and receipt_path.is_file()):
        if (plan_path.exists() or receipt_path.exists() or (audit_row and audit_row["status"] == "PASS")):
            return "MISSING", "計画と完了受領証の組が不足"
        if (plan_path.parent / "JOB.json").is_file() or any(plan_path.parent.glob("branch_*/JOB.json")):
            return "MISSING", "投入の証跡はあり、完了結果が欠損"
        return "NOT_RUN", "投入・完了の証跡なし"
    receipt = read(receipt_path)
    state = receipt.get("status")
    if state in ("INFEASIBLE", "NO_FEASIBLE_PLAN"):
        return "INFEASIBLE", state
    if state != "COMPLETE":
        return "ABNORMAL", str(state)
    if not audit_row:
        return "MISSING", "独立監査行が欠損"
    if audit_row["status"] != "PASS":
        return "ABNORMAL", audit_row["status"]
    return "VALID", ""


def build_trials(root):
    sys.path[:0] = [str(root / "scripts"), str(root / "src")]
    from audit_grouped_loading_v2 import independently_build, recheck
    from run_grouped_formal_v2 import completion
    from run_grouped_loading_v2 import load_problem, load_policy
    from kmd_toc.iterative_v3_study.analysis import delta

    outputs = root / "output/iterative_d3"
    pilot, formal, audit = (outputs / name for name in ("grouped_loading_20261124_v2_pilot",
                           "formal_J30_grouped_v2", "grouped_loading_20261124_v2_audit"))
    ppath, fpath = pilot / "MANIFEST.json", formal / "MANIFEST.json"
    freeze_path, audit_path = formal / "FREEZE_RECORD.json", audit / "RECHECK.json"
    p, f, freeze, evidence = map(read, (ppath, fpath, freeze_path, audit_path))
    if (p["stage"] != "pilot" or f["stage"] != "formal" or p["version"] != VERSION
            or freeze["manifest_sha256"] != sha(fpath) or freeze.get("status") != "GO"
            or read(pilot / "REGISTRATION.json")["manifest_sha256"] != sha(ppath)
            or any(p[k] != f[k] for k in ("version", "configuration", "classical_configuration", "grouped_conditions"))):
        raise ValueError("Pilot/Freeze version or configuration binding")
    if read(root / "configs/grouped_loading_20261124_v2/conditions.json") != p["grouped_conditions"]:
        raise ValueError("Grouped operating configuration drift")
    with ThreadPoolExecutor(max_workers=12) as pool:
        source_hashes_now = dict(zip(p["code_hashes"],pool.map(sha, (root/name for name in p["code_hashes"]))))
        actual_input_hashes = dict(zip(f["input_hashes"],pool.map(sha, (archived_path(root,name) for name in f["input_hashes"]))))
    if source_hashes_now != p["code_hashes"] or any(f["code_hashes"].get(name) != h for name, h in p["code_hashes"].items()):
        raise ValueError("Pinned pilot source or formal-source binding")
    if actual_input_hashes != f["input_hashes"] or any(actual_input_hashes.get(k) != v for k,v in p["input_hashes"].items()):
        raise ValueError("Pinned input and directed OD hashes")
    if Counter(c["scale"] for c in f["cases"]) != {s:30 for s in SCALES}:
        raise ValueError("Formal J does not equal 30 per scale")
    formal_status_path = formal / "empty_analysis" / "STATUS.csv"
    formal_status = read_csv(formal_status_path)
    if (f["state"] != "NOT_STARTED" or (formal / "EXECUTION_STARTED.json").exists()
            or (formal / "trials").exists()
            or len(formal_status) != 270 or any(r["status"] != "NOT_STARTED" for r in formal_status)):
        raise ValueError("Unexpected formal execution state")
    if Counter(c["scale"] for c in p["cases"]) != {s:1 for s in SCALES}:
        raise ValueError("Expected the one-case-per-scale pilot registration")
    audit_table = {(r["scale"],r["trial_id"],r["method"]): r for r in read_csv(audit / "RESULTS.csv")}
    source_hashes = {archived_path(root,k): v for k,v in evidence["source_sha256"].items()}
    files = {path.relative_to(root).as_posix(): sha(path) for path in
             (ppath, fpath, freeze_path, audit_path, audit / "RESULTS.csv", formal_status_path)}
    rows, conditions, checked = [], [], 0
    duty = load_policy() | {"loading_s":p["grouped_conditions"]["loading_s"]}
    for case in p["cases"]:
        scale, trial = case["scale"], case["trial_id"]
        data = load_problem(archived_path(root, case["input"]), p["configuration"]["rest_options"])
        if (case["context"]["stage"] != "pilot" or data.fingerprint != case["problem_hash"]
                or data.od.fingerprint != case["od_hash"]):
            raise ValueError(f"Case input/OD identity {trial}")
        fleet, stops = len(data.vehicles), len(data.stops)
        berths = {b.berth_id:(b.opening_s,b.closing_s) for b in data.berths}
        if any(s.demand != 1 for s in data.stops) or p["grouped_conditions"]["parcel"]["per_stop"] != 1:
            raise ValueError("Cannot identify parcel count from grouped-v2 box assumption")
        if (fleet, len(berths)) != tuple(p["grouped_conditions"]["scales"][scale][k] for k in ("vehicles","berths")):
            raise ValueError("Fleet/berths drift")
        conditions.append(dict(scale=scale, trial_id=trial, delivery_stops=stops, assumed_parcels=stops,
                               configured_vehicles=fleet, berths=len(berths), group_size=p["grouped_conditions"]["group_size"],
                               loading_seconds=duty["loading_s"], customer_service_seconds=duty["service_s"], max_trips_per_vehicle=2,
                               version=p["version"], D_search=p["configuration"]["search"]["variant"], local_size=12, depth=2,
                               training_shots=1000, extraction_shots=10000, COBYLA_max_evals=24, return_limit=4,
                               input_path=archived_path(root,case["input"]).relative_to(root).as_posix(),
                               problem_hash=case["problem_hash"],od_hash=case["od_hash"],
                               planned_formal_J=30, registered_pilot_cases=1))
        base_path = pilot / scale / "B" / "plan.json"
        base = read(base_path) if base_path.is_file() else None
        if base is not None and sha(base_path) != f["fixed_initials"][scale]["plan_sha256"]:
            raise ValueError("Fixed B mismatch")
        group = []
        for public, internal in METHODS.items():
            folder = pilot / scale / internal
            plan_path, receipt = folder / "plan.json", folder / "RESULT.json"
            audit_row = audit_table.get((scale, trial, internal))
            status, reason = publication_status(plan_path, receipt, audit_row)
            row = dict(stage="pilot", version=VERSION, scale=scale, experiment=LABELS[scale],
                       trial_id=trial, method=public, internal_method=internal, status=status, reason=reason,
                       sample_role="fixed_reference" if public=="B" else "outer_trial",
                       problem_hash=case["problem_hash"], od_hash=case["od_hash"], delivery_stops=stops,
                       configured_vehicles=fleet, berths=len(berths), plan_path=plan_path.relative_to(root).as_posix())
            if status == "VALID":
                digest = sha(plan_path)
                if any(sha(path) != source_hashes.get(path) for path in (plan_path, receipt)) or audit_row["plan_sha256"] != digest:
                    raise ValueError(f"Invalid audit hash {plan_path}")
                if public != "B" and base is not None and completion(folder, internal, base) is None:
                    raise ValueError(f"No validated publication {plan_path}")
                plan = read(plan_path)
                if (plan["version"] != VERSION or plan["base_problem_hash"] != case["problem_hash"]
                        or plan["od_hash"] != case["od_hash"]):
                    raise ValueError("Saved plan pairing")
                jobs = independently_build(data, plan)
                proof = recheck.recheck(plan,jobs,berths,duty,data.rest_options,data.depot.depot_id)
                checked += proof["rechecked_trips"]
                trips = len(plan["trips"])
                active = len({trip["vehicle_id"] for trip in plan["trips"]})
                parcels = sum(t["parcels"] for t in plan["trips"])
                d, w = Fraction(plan["D_exact"]), Fraction(plan["W_exact"])
                if (parcels != stops or active != plan["active_vehicles"] or trips != plan["active_trips"]
                        or w != Fraction(plan["W_total_s"],60)):
                    raise ValueError("Parcel count, operations or W mismatch")
                for path in (plan_path, receipt):
                    files[path.relative_to(root).as_posix()] = source_hashes[path]
                capacity = p["grouped_conditions"]["vehicle"]
                row.update(plan_sha256=digest,physical_hash=plan["physical_hash"],D_exact_km=str(d),W_exact_min=str(w),
                           parcel_count=parcels,capacity_model_per_trip=capacity["model_capacity_per_trip"],
                           capacity_model_unit=capacity["model_capacity_unit"],active_trips=trips,active_vehicle_days=active,
                           km_per_parcel_exact=str(d/parcels),wait_min_per_research_run_exact=str(w/active),
                           freeze_wait_min_per_configured_vehicle_day_exact=str(w/fleet),
                           wait_min_per_active_trip_exact=str(w/trips),km_per_parcel=float(d/parcels),
                           wait_min_per_research_run=float(w/active),W_research_scope="depot reception-to-load-start")
            group.append(row)
        matched = all(r["status"] == "VALID" for r in group)
        for row in group:
            row["matched_BCD"] = matched
            if not matched:
                row["dual_status"] = "MISSING_MATCHED_COHORT"
                continue
            c = next(r for r in group if r["method"]=="C")
            d, w = Fraction(row["D_exact_km"]), Fraction(row["W_exact_min"])
            dc, wc = Fraction(c["D_exact_km"]), Fraction(c["W_exact_min"])
            rd = 100*(dc-d)/dc if dc>0 else None
            rw = 100*(wc-w)/wc if wc>0 else None
            score = min(rd,rw) if rd is not None and rw is not None else None
            if delta({"D_exact":str(d),"W_exact":str(w)},
                     {"D_exact":str(dc),"W_exact":str(wc)})["I_dual_percent"] != (None if score is None else float(score)):
                raise ValueError("Frozen zero-baseline or improvement rule drift")
            row.update(C_plan_sha256=c["plan_sha256"],C_D_exact_km=str(dc),C_W_exact_min=str(wc),
                       distance_improvement_pct=None if rd is None else float(rd),
                       wait_improvement_pct=None if rw is None else float(rw),
                       dual_pct_exact=None if score is None else str(score),
                       dual_pct=None if score is None else float(score),
                       absolute_D_gain_km_exact=str(dc-d),absolute_W_gain_min_exact=str(wc-w),
                       dual_status="UNDEFINED_ZERO_BASELINE" if score is None else "DEFINED")
        rows.extend(group)
    metadata = dict(stage="pilot_publication", version=VERSION, p_source_files=len(p["code_hashes"]),
                    plan_trips_independently_rechecked=checked, formal_cases=len(f["cases"]), formal_state=f["state"],
                    formal_observations=0, sources_sha256=files, operating_conditions=p["grouped_conditions"],
                    solver_search=p["configuration"]["search"], classical_search=p["classical_configuration"]["C"],
                    classical_completion=p["classical_configuration"]["completion"], formal_environment=f["environment"])
    return rows, conditions, metadata


def summarize(rows):
    result = []
    for scale in SCALES:
        for method in METHODS:
            group = [r for r in rows if r["scale"]==scale and r["method"]==method and r["matched_BCD"]]
            row = dict(stage="pilot",scale=scale,experiment=LABELS[scale],method=method,valid_n=len(group))
            for metric in METRICS:
                v = [Fraction(r[metric+"_exact"]) for r in group if r.get(metric+"_exact") is not None]
                row.update({metric+"_n":len(v),metric+"_mean":float(mean(v)) if v else None,
                            metric+"_sample_sd":stdev(v) if len(v)>1 else None})
            result.append(row)
    return result


def status_counts(rows):
    result = []
    for scale in SCALES:
        for method in METHODS:
            group = [r for r in rows if (r["scale"],r["method"])==(scale,method)]
            counts = Counter(r["status"] for r in group)
            result.append(dict(stage="pilot",scale=scale,method=method,registered_cases=len(group),
                               matched_n=sum(r["matched_BCD"] for r in group),
                               **{s:counts[s] for s in ("VALID","NOT_RUN","INFEASIBLE","MISSING","ABNORMAL")}))
        for m in ("C","D","D古典対照"):
            result.append(dict(stage="formal",scale=scale,method=m,registered_cases=30,matched_n=0,
                               VALID=0,NOT_RUN=30,INFEASIBLE=0,MISSING=0,ABNORMAL=0))
    return result


def configure_fonts(font_file):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager, pyplot as plt
    font_manager.fontManager.addfont(font_file)
    bold = font_file.with_name(font_file.name.replace("-Regular","-Bold"))
    if bold != font_file and bold.is_file():
        font_manager.fontManager.addfont(bold)
    family = font_manager.FontProperties(fname=font_file).get_name()
    plt.rcParams.update({"font.family":family,"font.size":12,"axes.unicode_minus":True,
                         "pdf.fonttype":42,"axes.edgecolor":"#687582","axes.labelcolor":"#192834",
                         "xtick.color":"#25313D","ytick.color":"#25313D","savefig.facecolor":"white"})
    return plt


def sheet(plt, title, number, *, boxplot=False):
    fig = plt.figure(figsize=(11,6.4),facecolor="white")
    label = "予備実験結果  ／  箱ひげ図" if boxplot else "予備実験結果"
    fig.text(.09,.948,label,fontsize=11,color="#475867",weight="bold")
    fig.text(.09,.875,f"{number}　{title}",fontsize=22,color="#142532",weight="bold")
    return fig


def foot(fig, lines):
    for i,line in enumerate(lines):
        fig.text(.09,.114-i*.042,line,fontsize=10.4,color="#40505D")


def figure_table(plt, table):
    fig = sheet(plt,"規模別の記述統計","表1")
    ax = fig.add_axes((.09,.18,.82,.62))
    ax.axis("off")
    headings = ["実験","手法","有効\n試行数","両立改善率\n平均［%］","同 SD",
                "走行距離\n平均［km／個］","同 SD","荷待ち時間\n平均［分／研究運行］","同 SD"]
    grid = []
    for row in table:
        display = [row["experiment"],row["method"],row["valid_n"]]
        for metric,digits in zip(METRICS,(2,3,2)):
            for suffix in ("_mean","_sample_sd"):
                value = row[metric+suffix]
                display.append("—" if value is None else f"{value:.{digits}f}")
        grid.append(display)
    tbl = ax.table(cellText=grid,colLabels=headings,cellLoc="center",colWidths=[.10,.065,.085,.14,.06,.15,.06,.18,.06],
                   bbox=(0,0,1,1))
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11.3)
    for (i,j), cell in tbl.get_celld().items():
        cell.set_edgecolor("#CFD7DE")
        cell.set_linewidth(.55)
        if i==0:
            cell.set_facecolor("#213949")
            cell.set_text_props(color="white",weight="bold")
            cell.set_height(.135)
        else:
            cell.set_facecolor("#F0F4F7" if ((i-1)//3)%2 else "#FFFFFF")
            if j==1:
                cell.set_text_props(color=COLORS[grid[i-1][1]],weight="bold")
    foot(fig,["SDは標本標準偏差。—は算出不可（n=1）。Bは各規模の固定参照計画1件。",
              "研究運行＝稼働車両1台・1日。Aは外部参照（距離0.58 km／個、荷待ち60分／行政調査上の運行）。"])
    return fig


def figure_metric(plt, rows, metric):
    from matplotlib.cbook import boxplot_stats
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FormatStrFormatter

    number,title,ylabel,step,minimum,maximum = {
        "dual_pct":("図1","走行距離と荷待ち時間の両立改善率","両立改善率［%］",20,-60,60),
        "km_per_parcel":("図2","荷物1個当たりの走行距離","走行距離［km／個］",.2,0,.8),
        "wait_min_per_research_run":("図3","1運行当たりの荷待ち時間","荷待ち時間［分／研究運行］",20,0,80),
    }[metric]
    fig = sheet(plt,title,number,boxplot=True)
    ax = fig.add_axes((.126,.238,.60,.535))
    right = fig.add_axes((.765,.238,.17,.535))
    right.axis("off")
    points = [r[metric] for r in rows if r["matched_BCD"] and r.get(metric) is not None]
    if metric == "dual_pct":
        maximum = max(maximum,step*math.ceil(max(map(abs,points),default=0)/step))
        minimum = -maximum
        ax.axhline(0,color="#AAB5BE",linewidth=1.0,zorder=1)
    else:
        maximum = max(maximum,step*math.ceil(max(points,default=0)/step))
    if metric == "km_per_parcel":
        ax.axhline(.58,color="black",linestyle="--",linewidth=1.4,zorder=2)
    box_rows = []
    for i, scale in enumerate(SCALES):
        for j,method in enumerate(METHODS):
            v = [r[metric] for r in rows if (r["scale"],r["method"])==(scale,method)
                 and r["matched_BCD"] and r.get(metric) is not None]
            x, color = i+(j-1)*.235,COLORS[method]
            if not v:
                ax.text(x,.03,"欠測",transform=ax.get_xaxis_transform(),ha="center",color="#55616A",fontsize=9)
                continue
            box = boxplot_stats(v,whis=1.5,autorange=False)[0]
            if metric=="dual_pct" and method=="C" and any(value!=0 for value in v):
                raise ValueError("Defined C reference must be zero")
            artists = ax.bxp([box],positions=[x],widths=.176,showfliers=True,showmeans=False,
                             manage_ticks=False,patch_artist=True,zorder=4,
                             boxprops=dict(facecolor=color+"40",edgecolor=color,linewidth=1.1),
                             medianprops=dict(color=color,linewidth=2.7,solid_capstyle="butt"),
                             whiskerprops=dict(color=color,linewidth=1.1),
                             capprops=dict(color=color,linewidth=1.1),
                             flierprops=dict(marker="o",markersize=4,markerfacecolor="none",markeredgecolor=color))
            if len(v)==1:
                if any(box[k]!=v[0] for k in ("q1","med","q3","whislo","whishi")) or box["fliers"].size:
                    raise ValueError("The computed singleton boxplot does not collapse to the observation")
                if any(y!=v[0] for y in artists["medians"][0].get_ydata()):
                    raise ValueError("The rendered median differs from the recorded observation")
                label = f"{v[0]:.3f}" if metric=="km_per_parcel" else f"{v[0]:.2f}"
                if metric=="dual_pct" and v[0]>0:
                    label = "+"+label
                top = v[0]>maximum-.08*(maximum-minimum)
                ax.annotate(label,(x,v[0]),xytext=(0,-7 if top else 6),textcoords="offset points",
                            ha="center",va="top" if top else "bottom",fontsize=9.8,color=color)
            box_rows.append(dict(metric=metric,scale=scale,method=method,n=len(v),q1=float(box["q1"]),
                                 median=float(box["med"]),q3=float(box["q3"]),whisker_low=float(box["whislo"]),
                                 whisker_high=float(box["whishi"]),outliers=json.dumps(box["fliers"].tolist())))
    ticks = [round(minimum+i*step,8) for i in range(round((maximum-minimum)/step)+1)]
    ax.set(xticks=range(3),xticklabels=LABELS.values(),xlim=(-.52,2.52),
           ylim=(minimum,maximum),yticks=ticks,ylabel=ylabel)
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f" if step<1 else "%.0f"))
    ax.set_axisbelow(True)
    ax.grid(axis="y",color="#D9E2E9",linewidth=.75)
    ax.spines[["top","right"]].set_visible(False)
    handles = [Line2D([],[],color=color,linestyle="-",linewidth=2.7,solid_capstyle="butt",
               label=label) for color,label in zip(COLORS.values(),("B　従来法","C　OR-Tools","D　古典＋QAOA"))]
    singleton_note = "各規模・手法 n=1。第1・第3四分位数、中央値、両端のひげが重なり、横線になります。"
    if metric == "dual_pct":
        foot(fig,[singleton_note,"青線は比較基準Cの0%。対応するCの総距離・総積込待機に対する改善率の小さい方。上ほど改善。"])
    elif metric == "km_per_parcel":
        handles.append(Line2D([],[],color="black",linestyle="--",label="A：行政統計（0.58 km／個）"))
        foot(fig,[singleton_note,
                  "下ほど短い。研究は1配送先1箱。Aは国交省（2015）資料2・p.4の配達車距離（幹線除外）／取扱個数。",
                  "Aと研究の再配達・地域・運用条件や、取扱個数と配送済み箱数の対応は未確認。"])
    else:
        # Explicitly separate measurement units despite the same numeric range.
        ref = fig.add_axes((.803,.443,.141,.263))
        ref.set(xlim=(0,1),ylim=(0,80),xticks=[],yticks=[0,20,40,60,80],title="行政統計の参照欄")
        ref.tick_params(axis="y",labelsize=9,pad=3)
        ref.yaxis.tick_right()
        ref.spines[["top","left"]].set_visible(False)
        ref.spines[["bottom","right"]].set_color("#9AA7B0")
        ref.axhline(60,color="black",linestyle="--",linewidth=1.4)
        ref.text(.02,.53,"A：行政統計\n（60分／運行）",transform=ref.transAxes,fontsize=10)
        ref.text(.5,-.11,"分／行政調査上の運行",transform=ref.transAxes,ha="center",fontsize=9)
        foot(fig,[singleton_note,"研究運行は稼働車両1台・1日。下ほど待機が短い。運行単位・待機範囲の一致は未確認。",
                  "Aは国交省2025年度調査・p.2。一般貨物を対象とし、宅配には限定しない。"])
    right.legend(handles=handles,loc="lower left" if metric=="wait_min_per_research_run" else "center left",
                 frameon=False,fontsize=11 if metric=="wait_min_per_research_run" else 10.7,
                 borderaxespad=0,handlelength=1.6,labelspacing=.8)
    return fig, dict(min=minimum,max=maximum,ticks=ticks,observed_points=len(points)), box_rows


def render(rows, table, out, font_file):
    from matplotlib.backends.backend_pdf import PdfPages
    plt = configure_fonts(font_file)
    result = {}
    box_rows = []
    with PdfPages(out/"PILOT_TABLE_AND_FIGURES.pdf",metadata={"Title":"予備実験結果　表1・図1〜図3"}) as book:
        fig = figure_table(plt,table)
        for fmt in ("pdf","png"):
            fig.savefig(out/f"TABLE_1.{fmt}",dpi=250)
        book.savefig(fig)
        plt.close(fig)
        for index,metric in enumerate(METRICS,1):
            fig, info, boxes = figure_metric(plt,rows,metric)
            result[metric] = info
            box_rows.extend(boxes)
            for fmt in ("pdf","png"):
                fig.savefig(out/f"FIGURE_{index}.{fmt}",dpi=250)
            book.savefig(fig)
            plt.close(fig)
    write_csv(out/"BOXPLOT_STATISTICS.csv",box_rows)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    args = parser.parse_args()
    root,out = args.repo_root.resolve(),args.output.resolve()
    rows, conditions, meta = build_trials(root)
    table = summarize(rows)
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/"PILOT_TRIALS.csv",rows)
    write_csv(out/"TABLE_1.csv",table)
    write_csv(out/"STUDY_CONDITIONS.csv",conditions)
    write_csv(out/"STATUS_COUNTS.csv",status_counts(rows))
    write_csv(out/"ADMIN_REFERENCES.csv",A_ROWS)
    limits = render(rows,table,out,args.font.resolve())
    for row in table:
        for metric in METRICS:
            values = [r[metric] for r in rows if r["matched_BCD"] and (r["scale"],r["method"])==(row["scale"],row["method"])
                      and r.get(metric) is not None]
            if len(values)!=row[metric+"_n"] or (len(values)==1 and (
                    values[0]!=row[metric+"_mean"] or row[metric+"_sample_sd"] is not None)):
                raise ValueError("Table and figure cohort/metric mismatch")
    for metric,v in limits.items():
        pool = [r[metric] for r in rows if r["matched_BCD"] and r.get(metric) is not None]
        if len(pool)!=v["observed_points"] or any(not v["min"]<=x<=v["max"] for x in pool):
            raise ValueError("Figure axis clips an observation")
    write_json(out/"VERIFICATION.json",meta | dict(
        table_and_figures_same_matched_data=True,limits=limits,statistics_file_sha256=sha(out/"TABLE_1.csv"),
        trial_file_sha256=sha(out/"PILOT_TRIALS.csv"),source_script_sha256=sha(Path(__file__)),
        sampling_note="One matched pilot case per scale. B is a fixed reference, and no branch/shots are counted as trials.",
        figure_note="Tukey 1.5 IQR boxplots with linear quartiles for all groups. Singleton boxes and whiskers coincide with the median.",
        boxplot_statistics_sha256=sha(out/"BOXPLOT_STATISTICS.csv"),
        wait_publication_definition="W/active vehicle-days. Each active driver with one or two trips counts once. Current Freeze display W/configured vehicle-days is retained separately.",
        administrative_wait_conversion="No validated mapping for the operation denominator or waiting coverage. Separate reference panel."))
    print(f"{len(rows)} method rows; {meta['plan_trips_independently_rechecked']} trips rechecked; {out}")


if __name__=="__main__":
    main()
