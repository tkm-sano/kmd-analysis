#!/usr/bin/env python3
"""Regenerate scheduled-reception slides from validated pilot files."""
import argparse
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
import numpy as np

METHODS=("B","C_Idual","D_classical","D_quantum")
LABELS=("B｜従来法（Clarke–Wright法）","C｜古典最適化（OR-Tools）",
        "D古典対照｜古典局所探索","D量子｜古典＋QAOA")
COLORS=("#255467","#986347","#238477","#76549f")
SCALES=("S1","S2","S3")


def load(p):
    return json.loads(p.read_bytes())


def records(p):
    if not p.exists(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def clock(x,_=None):
    x=int(x)
    return f"{x//3600:02}:{x//60%60:02}:{x%60:02}"


def save(fig,where,name):
    fig.savefig(where/f"{name}.svg",bbox_inches="tight")
    plt.close(fig)


def model(where):
    fig,ax=plt.subplots(figsize=(12,4),layout="constrained")
    ax.axis("off")
    entries=(("固定条件","需要と有向OD、容量60個、バース2／4／8\n5台ずつの固定グループ、積込900秒"),
             ("決定変数","車両・便別の配送先割当と訪問順序\n第2グループ以降の受付予定時刻"),
             ("計画の計算結果","FCFSで積込開始・終了、出発・帰着\n第2便の受付と距離・待ち、稼働台数"))
    for i,(title,body) in enumerate(entries):
        x=.02+i*.334
        ax.text(x,.8,title,transform=ax.transAxes,weight="bold",color=COLORS[i],fontsize=17)
        ax.text(x,.55,body,transform=ax.transAxes,fontsize=12,linespacing=1.6,
                bbox=dict(facecolor="#eff3f5",edgecolor=COLORS[i],boxstyle="round,pad=.65"))
    ax.text(.02,.15,"第1便は受付、第2便は帰着から荷待ちを計測。受付前経過は補助記録。",transform=ax.transAxes,fontsize=13)
    save(fig,where,"01_model")


def gantts(pilot,where):
    methods=[m for m in METHODS if (pilot/"S1"/m/"plan.json").exists() and (pilot/"S1"/m/"RESULT.json").exists()]
    if not methods:return
    fig,ax=plt.subplots(figsize=(10,3.6),layout="constrained")
    for m in methods:
        plan=load(pilot/"S1"/m/"plan.json")
        idx=METHODS.index(m)
        for j,t in enumerate(plan["calls_s"]):
            ax.scatter(t,idx,c=COLORS[idx],s=52)
            ax.annotate(f"G{j+1}",(t,idx),xytext=(0,7),textcoords="offset points",ha="center")
    ax.set_yticks([METHODS.index(m) for m in methods],[LABELS[METHODS.index(m)] for m in methods])
    ax.set_ylim(-.6,3.6);ax.set_xlim(28700,32500)
    ax.xaxis.set_major_formatter(FuncFormatter(clock));ax.grid(axis="x",alpha=.25)
    ax.set(title="S1 グループ別の第1便受付",xlabel="時刻")
    save(fig,where,"02_group_reception")
    m=methods[-1];plan=load(pilot/"S1"/m/"plan.json");title=LABELS[METHODS.index(m)]
    palette={"受付前経過":"#bdb2a7","受付後荷待ち":"#e6bf6c","積込":"#286a8d","配送・走行":"#69aa96","休憩":"#b68eb1"}
    fig,ax=plt.subplots(figsize=(12,3.2),layout="constrained")
    berth=sorted({x["berth_id"] for x in plan["trips"]})
    for t in plan["trips"]:
        s,e=t["load_start_s"],t["load_end_s"]
        y=berth.index(t["berth_id"])
        ax.barh(y,e-s,left=s,height=.6,color=COLORS[METHODS.index(m)])
        ax.text((s+e)/2,y,f'{t["vehicle_id"]}.{t["trip_no"]}',ha="center",va="center",fontsize=7,color="white")
    ax.set_yticks(range(len(berth)),berth)
    ax.set(title=f"S1 バース別の積込  |  {title}",xlabel="時刻")
    ax.xaxis.set_major_formatter(FuncFormatter(clock))
    save(fig,where,"03_berth_gantt")
    fig,ax=plt.subplots(figsize=(13,5),layout="constrained")
    vehicles=sorted({t["vehicle_id"] for t in plan["trips"]},key=lambda v:int(v[1:]))
    for y,vehicle in enumerate(vehicles):
        for t in (x for x in plan["trips"] if x["vehicle_id"]==vehicle):
            q,s,e,ret=[t[k] for k in ("actual_reception_s","load_start_s","load_end_s","return_s")]
            fields=[(q,s,"受付後荷待ち"),(s,e,"積込"),(e,ret,"配送・走行")]
            if t["trip_no"]==1:fields.insert(0,(28800,q,"受付前経過"))
            for a,b,label in fields:
                ax.barh(y,b-a,left=a,color=palette[label],height=.62,label=label)
        for br in (x for x in plan["breaks"] if x["vehicle_id"]==vehicle):
            ax.barh(y,br["end_s"]-br["start_s"],left=br["start_s"],color=palette["休憩"],height=.62,label="休憩")
    ax.set_yticks(range(len(vehicles)),vehicles);ax.invert_yaxis()
    ax.set(title=f"S1 車両別の第1便・第2便  |  {title}",xlabel="時刻")
    ax.xaxis.set_major_formatter(FuncFormatter(clock))
    h,l=ax.get_legend_handles_labels();unique=dict(zip(l,h))
    ax.legend(unique.values(),unique,loc="lower center",bbox_to_anchor=(.5,-.3),ncol=5)
    save(fig,where,"04_vehicle_gantt")

    manifest=load(pilot/"MANIFEST.json")
    inp=load(Path(next(c["input"] for c in manifest["cases"] if c["scale"]=="S1"))/"input.json")
    coord={s["stop_id"]:(s["longitude"],s["latitude"]) for s in inp["stops"]}
    depot=inp["depot"];base=(depot["longitude"],depot["latitude"])
    fig,ax=plt.subplots(figsize=(8,7),layout="constrained")
    for t in plan["trips"]:
        coords=[base,*[coord[v["stop_id"]] for v in t["visits"]],base]
        x,y=zip(*coords)
        ax.plot(x,y,color=COLORS[METHODS.index(m)],alpha=.27 if t["trip_no"]==1 else .53,
                 lw=.6,linestyle=":" if t["trip_no"]==2 else "-")
    ax.scatter(*base,marker="D",c="black",s=42)
    ax.set(title=f"S1 配送訪問順  |  {title}",xlabel="経度",ylabel="緯度")
    ax.text(.01,.01,"実線 第1便／点線 第2便。訪問先を直線で結んだ模式図。",transform=ax.transAxes)
    ax.set_aspect(1/np.cos(np.deg2rad(base[1])))
    save(fig,where,"05_route_order")


def comparison(audit,where):
    rows={(r["scale"],r["method"]):r for r in records(audit/"RESULTS.csv") if r["status"]=="PASS"}
    pairs=records(audit/"PAIRED.csv")
    if not rows:return
    for number,fields,title in (
        ("06_absolute",(("D_km_per_parcel","距離［km／個］"),("W_min_per_configured_vehicle_day","荷待ち［分／台・日］")),
         "独立検算済みの限定予備｜各規模・方式1ケース"),
        ("08_wait_components",(("W1_s","第1便荷待ち［分／台・日］"),("W2_s","第2便荷待ち［分／台・日］"),
          ("before_reception_total_s","受付前経過［分／台・日］")),"荷待ちと受付前経過の内訳")):
        fig,axes=plt.subplots(1,len(fields),figsize=(5.2*len(fields),4.3),layout="constrained")
        for ax,(field,title_axis) in zip(axes,fields):
            for j,m in enumerate(METHODS):
                pts=[]
                for i,s in enumerate(SCALES):
                    if (s,m) not in rows:continue
                    r=rows[s,m];v=float(r[field])
                    if number=="08_wait_components":v/=60*int(r["configured_vehicles"])
                    pts.append((i+(j-1.5)*.13,v))
                if pts:
                    xx,yy=zip(*pts);ax.scatter(xx,yy,c=COLORS[j],label=LABELS[j])
            ax.set_xticks(range(3),SCALES);ax.set_ylabel(title_axis);ax.grid(axis="y",alpha=.25)
        h,l=axes[0].get_legend_handles_labels()
        fig.legend(h,l,loc="outside lower center",ncol=2)
        fig.suptitle(title)
        save(fig,where,number)
    fig,ax=plt.subplots(figsize=(9,4.1),layout="constrained")
    kinds=("B_vs_C","B_vs_Dq","C_vs_Dq","Dclassic_vs_Dq")
    labels=("B→C","B→D量子","C→D量子","D古典対照→D量子")
    ax.axhline(0,color="#999999")
    for k,(kind,label) in enumerate(zip(kinds,labels)):
        for r in (r for r in pairs if r["comparison"]==kind):
            off=(k-1.5)*.13;v=r["I_dual_percent"]
            if v:
                ax.scatter(SCALES.index(r["scale"])+off,float(v),marker=("o","s","D","^")[k],
                    c=COLORS[METHODS.index(r["candidate"])],label=label)
    h,l=ax.get_legend_handles_labels()
    legend=dict(zip(l,h))
    if legend:ax.legend(legend.values(),legend)
    ax.set_xticks(range(3),SCALES);ax.set_ylabel("両立改善率［%］")
    ax.set_title("対応比較ごとの両立改善率｜正が改善。分母0は未定義")
    save(fig,where,"07_dual_paired")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pilot",type=Path);cli.add_argument("audit",type=Path);cli.add_argument("output",type=Path)
    cli.add_argument("--font",type=Path,default=Path("/home/takuma/.local/share/fonts/NotoSansJP-Regular.ttf"))
    a=cli.parse_args()
    font_manager.fontManager.addfont(str(a.font))
    plt.rcParams.update({"font.family":font_manager.FontProperties(fname=a.font).get_name(),"svg.fonttype":"path"})
    a.output.mkdir(parents=True,exist_ok=False)
    model(a.output);gantts(a.pilot,a.output);comparison(a.audit,a.output)
