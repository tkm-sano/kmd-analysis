from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/use_case_scenario"
FIG = ROOT / "figures" / "02_requirement_mapping"

FIG1 = ROOT / "figures" / "01_quantum_vrp_evidence" / "figure_1_presentation_plot_data.csv"
REQ_MAP = OUT / "943_20260705_v03_tokyo_evrp_quantum_requirement_map.csv"
BENCH_FIELDS = OUT / "evrp_benchmark_instance_fields.csv"
SCENARIO_DESIGN = OUT / "tokyo_evrp_scenario_design.csv"
CHARGERS = OUT / "scenario_available_chargers.csv"
DEPOTS = OUT / "scenario_depots.csv"
VEHICLES = OUT / "vehicle_scenario_rules.csv"


REQ_ROWS = [
    {
        "requirement_id": "REQ-01",
        "requirement": "customers / demand nodes",
        "requirement_type": "static EVRP input",
        "tokyo_public_data_basis": "e-Stat population mesh; freight-establishment CSV; Tokyo freight activity CSV",
        "tokyo_public_data_status": "defined as synthetic demand-node rule",
        "classical_evrp_benchmark_basis": "E-CVRP and E-VRPTW benchmark files define customer counts and coordinates.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "Figure 1 has many evaluated instances with 3-6 nodes/locations; Golden_5 has 200 customers but resource estimate only.",
        "quantum_coverage_score": 1,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Quantum evidence handles small static customer sets; larger customer counts are mostly resource-estimation evidence.",
    },
    {
        "requirement_id": "REQ-02",
        "requirement": "vehicles / fleet size",
        "requirement_type": "static EVRP input",
        "tokyo_public_data_basis": "Scenario vehicle count in tokyo_evrp_scenario_design.csv; vehicle specs from official manufacturer sources.",
        "tokyo_public_data_status": "scenario-defined",
        "classical_evrp_benchmark_basis": "E-CVRP declares vehicles; E-VRPTW implies vehicle routing but does not declare vehicle count in files.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "Some Figure 1 rows report 1-5 vehicles/trucks, usually in very small instances.",
        "quantum_coverage_score": 1,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Fleet size appears in some quantum rows, but not as operational EV fleet coordination.",
    },
    {
        "requirement_id": "REQ-03",
        "requirement": "charging stations",
        "requirement_type": "EV-specific static input",
        "tokyo_public_data_basis": "N03-clipped OCM detailed data; scenario_available_chargers.csv has screened CHAdeMO candidates.",
        "tokyo_public_data_status": "defined with screening uncertainty",
        "classical_evrp_benchmark_basis": "E-CVRP and E-VRPTW benchmark files include charging station nodes.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "No Figure 1 row explicitly reports charging stations in the extracted scope.",
        "quantum_coverage_score": 0,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Charging-station choice is central in EVRP but absent from the extracted quantum VRP evidence.",
    },
    {
        "requirement_id": "REQ-04",
        "requirement": "vehicle capacity / cargo capacity",
        "requirement_type": "static EVRP constraint",
        "tokyo_public_data_basis": "Vehicle payload scenarios from official eCanter, ELF EV, Dutro Z EV, and Pixis Van BEV specs.",
        "tokyo_public_data_status": "scenario-defined",
        "classical_evrp_benchmark_basis": "E-CVRP and E-VRPTW benchmark files include cargo/vehicle capacity.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "CVRP framing and Golden_5 capacity exist; several VRP rows do not include capacity constraints.",
        "quantum_coverage_score": 1,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Capacity appears partially, but not as part of full EV logistics feasibility with charging and SOC.",
    },
    {
        "requirement_id": "REQ-05",
        "requirement": "battery / SOC / energy capacity",
        "requirement_type": "EV-specific static constraint",
        "tokyo_public_data_basis": "Vehicle battery/range scenarios and usable-range factor in vehicle_scenario_rules.csv.",
        "tokyo_public_data_status": "scenario-defined",
        "classical_evrp_benchmark_basis": "E-CVRP and E-VRPTW files include battery or energy-capacity fields.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "No extracted Figure 1 row directly reports EV battery, SOC, or energy-capacity constraints.",
        "quantum_coverage_score": 0,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Battery/SOC constraints are established in classical EVRP benchmarks but missing from current quantum VRP evidence.",
    },
    {
        "requirement_id": "REQ-06",
        "requirement": "energy consumption",
        "requirement_type": "EV-specific static model",
        "tokyo_public_data_basis": "Vehicle energy-consumption scenario values estimated from battery/range or official values.",
        "tokyo_public_data_status": "model assumption defined",
        "classical_evrp_benchmark_basis": "E-CVRP and E-VRPTW files include energy/fuel consumption parameters.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "Figure 1 rows generally report routing formulation/width rather than distance-to-energy feasibility.",
        "quantum_coverage_score": 0,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Distance-to-energy coupling is not visible in the quantum VRP extraction.",
    },
    {
        "requirement_id": "REQ-07",
        "requirement": "depot",
        "requirement_type": "static EVRP input",
        "tokyo_public_data_basis": "P31 logistics facilities screened into scenario_depots.csv.",
        "tokyo_public_data_status": "defined as depot candidates",
        "classical_evrp_benchmark_basis": "E-CVRP and E-VRPTW benchmark files include depot nodes.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "Many quantum VRP examples assume a depot implicitly, but depot reporting is not consistently reconstructable.",
        "quantum_coverage_score": 1,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Depot exists as a generic routing element, but not as a public-data-grounded EV logistics condition.",
    },
    {
        "requirement_id": "REQ-08",
        "requirement": "distance / travel-cost matrix",
        "requirement_type": "static EVRP input",
        "tokyo_public_data_basis": "OSM road network is available; baseline scenario defines OSM-derived distance matrix and assumed-speed travel time.",
        "tokyo_public_data_status": "defined as next construction step",
        "classical_evrp_benchmark_basis": "Benchmarks include coordinates and Euclidean-distance assumptions.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "Quantum rows often abstract cost matrices or use small hand-defined graphs.",
        "quantum_coverage_score": 1,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Static distance/cost exists, but public-data-grounded road-network construction is not central in current quantum evidence.",
    },
    {
        "requirement_id": "REQ-09",
        "requirement": "time windows / service time",
        "requirement_type": "static EVRP constraint",
        "tokyo_public_data_basis": "Tokyo-specific time windows are scenario assumptions; benchmark time-window fields provide template.",
        "tokyo_public_data_status": "benchmark-supported scenario assumption",
        "classical_evrp_benchmark_basis": "Schneider/Goeke E-VRPTW instances include ReadyTime, DueDate, and ServiceTime.",
        "classical_benchmark_coverage_score": 2,
        "quantum_figure1_basis": "VRPTW rows exist, but not jointly with EV charging, SOC, and station choice.",
        "quantum_coverage_score": 1,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Time windows are partly represented in quantum VRPTW evidence, but not as complete EVRP feasibility.",
    },
    {
        "requirement_id": "REQ-10",
        "requirement": "static road / freight context",
        "requirement_type": "static or historical context",
        "tokyo_public_data_basis": "Freight-flow CSVs, JARTIC snapshot, Tokyo police traffic statistics, MLIT road census, and important freight roads.",
        "tokyo_public_data_status": "available as context/proxy",
        "classical_evrp_benchmark_basis": "Classical EVRP benchmarks generally use static instances rather than real-time traffic.",
        "classical_benchmark_coverage_score": 1,
        "quantum_figure1_basis": "No Figure 1 row uses changing Tokyo traffic or historical freight context as part of the routing instance.",
        "quantum_coverage_score": 0,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Even static/historical transport context is outside most current quantum VRP reporting.",
    },
    {
        "requirement_id": "REQ-11",
        "requirement": "dynamic traffic adaptation / reoptimization",
        "requirement_type": "dynamic operational capability",
        "tokyo_public_data_basis": "JARTIC traffic snapshot exists only as optional traffic-intensity proxy; no delivery-link travel-time matrix.",
        "tokyo_public_data_status": "not baseline; future extension",
        "classical_evrp_benchmark_basis": "Parsed benchmark files are static; dynamic dispatch requires separate dynamic VRP models.",
        "classical_benchmark_coverage_score": 0,
        "quantum_figure1_basis": "Figure 1 evidence does not demonstrate dynamic traffic adaptation or real-time EV dispatch.",
        "quantum_coverage_score": 0,
        "dynamic_adaptation_coverage_score": 0,
        "gap_interpretation": "Dynamic responsiveness is beyond the immediate quantum-VRP evidence; the nearer gap is static EVRP constraint coverage.",
    },
]


def make_gap_table() -> pd.DataFrame:
    df = pd.DataFrame(REQ_ROWS)
    df["tokyo_requirement_defined"] = df["tokyo_public_data_status"].apply(
        lambda x: "yes" if "defined" in x or "available" in x or "benchmark-supported" in x else "partial_or_future"
    )
    df["tokyo_public_data_coverage_score"] = df["tokyo_public_data_status"].apply(
        lambda x: 2
        if "defined" in x or "available" in x or "benchmark-supported" in x
        else 1
        if "next construction step" in x or "future" in x or "partial" in x
        else 0
    )
    df["quantum_gap_score"] = df["classical_benchmark_coverage_score"] - df["quantum_coverage_score"]
    df["main_claim_support"] = df.apply(
        lambda r: (
            "supports core claim"
            if r["classical_benchmark_coverage_score"] >= 2 and r["quantum_coverage_score"] <= 1
            else "contextual support"
        ),
        axis=1,
    )
    return df


def make_static_dynamic_table(gap: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "analysis_layer": "Tokyo public data",
            "static_or_historical_conditions": "Can define demand proxies, depot candidates, charger candidates, vehicle specs, freight activity, and road context.",
            "dynamic_conditions": "Only partial traffic-intensity proxies are available; no observed parcel-level dynamic dispatch data.",
            "interpretation": "Tokyo can support public-data-grounded static EVRP scenario design, but not observed real-time EV routing reproduction.",
        },
        {
            "analysis_layer": "Classical EVRP benchmarks",
            "static_or_historical_conditions": "E-CVRP and E-VRPTW encode customers, depots, charging stations, capacity, energy/SOC, and time windows.",
            "dynamic_conditions": "Parsed benchmark files are static instances, not dynamic traffic-adaptation traces.",
            "interpretation": "The immediate benchmark target should be static EVRP constraint coverage before dynamic adaptation.",
        },
        {
            "analysis_layer": "Current quantum VRP evidence",
            "static_or_historical_conditions": "Mostly small static VRP/CVRP/VRPTW/HVRP instances, simulator/hardware-aware checks, and resource estimates.",
            "dynamic_conditions": "No extracted evidence of changing-road-condition response or real-time EV dispatch.",
            "interpretation": "Existing quantum VRP evidence has not yet reached full static EVRP requirements, so dynamic road-traffic responsiveness is a later-stage question.",
        },
    ]
    return pd.DataFrame(rows)


def make_score_table(gap: pd.DataFrame) -> pd.DataFrame:
    out = gap[
        [
            "requirement_id",
            "requirement",
            "requirement_type",
            "tokyo_public_data_coverage_score",
            "classical_benchmark_coverage_score",
            "quantum_coverage_score",
            "dynamic_adaptation_coverage_score",
            "quantum_gap_score",
            "main_claim_support",
            "gap_interpretation",
        ]
    ].copy()
    out["score_definition"] = "0=not covered; 1=partial/indirect/static-only; 2=directly encoded or explicitly defined"
    return out


def coverage_label(score: int, layer: str) -> str:
    if layer == "tokyo":
        return {2: "Defined", 1: "Partly defined", 0: "Not defined"}.get(int(score), "")
    if layer == "classical":
        return {2: "Direct", 1: "Partial", 0: "Not covered"}.get(int(score), "")
    return {2: "Direct", 1: "Partial", 0: "Missing"}.get(int(score), "")


def coverage_color(score: int, layer: str) -> str:
    if score == 2:
        return "#d9ead3"  # light green
    if score == 1:
        return "#fff2cc"  # light yellow
    return "#f4cccc" if layer == "quantum" else "#eeeeee"


def make_figure(score: pd.DataFrame) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig_df = score[~score["requirement"].str.contains("dynamic traffic", case=False, na=False)].copy()
    fig_df["Tokyo public-data scenario"] = fig_df["tokyo_public_data_coverage_score"].apply(
        lambda x: coverage_label(x, "tokyo")
    )
    fig_df["Classical EVRP benchmark"] = fig_df["classical_benchmark_coverage_score"].apply(
        lambda x: coverage_label(x, "classical")
    )
    fig_df["Current quantum VRP evidence"] = fig_df["quantum_coverage_score"].apply(
        lambda x: coverage_label(x, "quantum")
    )
    fig_df["Main reading"] = fig_df.apply(
        lambda r: "EV-specific gap"
        if r["quantum_coverage_score"] == 0 and r["classical_benchmark_coverage_score"] >= 2
        else "Partial quantum coverage"
        if r["quantum_coverage_score"] == 1
        else "Context only",
        axis=1,
    )
    display = fig_df[
        [
            "requirement",
            "Tokyo public-data scenario",
            "Classical EVRP benchmark",
            "Current quantum VRP evidence",
            "Main reading",
        ]
    ]

    fig_h = max(6, len(display) * 0.55)
    fig, ax = plt.subplots(figsize=(14, fig_h))
    ax.axis("off")
    ax.set_title(
        "EVRP Requirements: Defined in Tokyo/Public Benchmarks, Weakly Covered in Current Quantum VRP Evidence",
        fontsize=13,
        pad=16,
    )

    table = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.25, 0.19, 0.20, 0.22, 0.14],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.45)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d0d0d0")
        if row == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#333333")
            continue
        req_idx = row - 1
        if col == 1:
            score_value = int(fig_df.iloc[req_idx]["tokyo_public_data_coverage_score"])
            cell.set_facecolor(coverage_color(score_value, "tokyo"))
        elif col == 2:
            score_value = int(fig_df.iloc[req_idx]["classical_benchmark_coverage_score"])
            cell.set_facecolor(coverage_color(score_value, "classical"))
        elif col == 3:
            score_value = int(fig_df.iloc[req_idx]["quantum_coverage_score"])
            cell.set_facecolor(coverage_color(score_value, "quantum"))
        elif col == 4:
            if fig_df.iloc[req_idx]["Main reading"] == "EV-specific gap":
                cell.set_facecolor("#f4cccc")
            elif fig_df.iloc[req_idx]["Main reading"] == "Partial quantum coverage":
                cell.set_facecolor("#fff2cc")
            else:
                cell.set_facecolor("#eeeeee")
        else:
            cell.set_facecolor("white")

    ax.text(
        0,
        -0.05,
        "Labels: Defined/Direct = explicitly available or encoded; Partial = indirect or limited static coverage; Missing = not visible in the extracted Figure 1 evidence.",
        transform=ax.transAxes,
        fontsize=9,
        color="#444444",
        va="top",
    )
    fig.tight_layout()
    fig.savefig(FIG / "tokyo_static_evrp_requirement_coverage.png", dpi=220)
    plt.close(fig)


def make_md(gap: pd.DataFrame, static_dynamic: pd.DataFrame, score: pd.DataFrame) -> str:
    core = score[score["main_claim_support"].eq("supports core claim")]
    lines = [
        "# EVRP Requirement Gap Interpretation",
        "",
        "## Main Claim",
        "",
        "Tokyo public data can define the static requirements of a charging-aware EVRP scenario, and classical EVRP benchmarks already encode many of these constraints. However, the current Figure 1 quantum VRP evidence remains mostly at small, static routing instances and does not yet cover the EV-specific requirements needed even before dynamic traffic adaptation is considered.",
        "",
        "## What The Analysis Shows",
        "",
        "| Point | Evidence | Interpretation |",
        "|---|---|---|",
        "| Tokyo public data can define EVRP requirements | OCM chargers, P31 depot candidates, freight-flow CSVs, e-Stat mesh, vehicle specs, OSM/traffic context | Tokyo can support public-data-grounded static EVRP scenario design. |",
        "| Classical EVRP benchmark requirements are already richer than generic VRP | Parsed E-CVRP and E-VRPTW files include charging stations, energy/SOC, capacity, depots, and time windows | These are not speculative requirements; they are established benchmark fields. |",
        "| Current quantum VRP evidence is still limited | Figure 1 rows are mostly small static VRP/CVRP/VRPTW/HVRP cases or resource estimates | The immediate gap is static EVRP constraint coverage, not real-time traffic adaptation. |",
        "| Dynamic road-traffic responsiveness is a later-stage question | No extracted Figure 1 evidence demonstrates changing-road-condition response or real-time EV dispatch | It is premature to benchmark quantum VRP by dynamic traffic adaptation before static EVRP requirements are covered. |",
        "",
        "## Requirements Supporting The Core Claim",
        "",
        "| Requirement | Classical score | Quantum score | Gap | Interpretation |",
        "|---|---:|---:|---:|---|",
    ]
    for _, r in core.iterrows():
        lines.append(
            f"| {r['requirement']} | {int(r['classical_benchmark_coverage_score'])} | {int(r['quantum_coverage_score'])} | {int(r['quantum_gap_score'])} | {r['gap_interpretation']} |"
        )
    lines += [
        "",
        "## Static vs Dynamic Interpretation",
        "",
        static_dynamic.to_markdown(index=False),
        "",
        "## Suggested Paper Wording",
        "",
        "> Even before considering real-time traffic adaptation, current quantum VRP evidence remains largely at the level of static routing instances. The nearer research gap is whether quantum VRP can handle EVRP constraints already established in classical benchmarks and public-data-grounded static Tokyo scenarios, including charging stations, SOC, depot selection, vehicle capacity, energy consumption, and time windows.",
        "",
        "## Outputs",
        "",
        "- `evrp_requirement_gap_evidence_table.csv`",
        "- `940_20260705_v03_static_vs_dynamic_readiness_table.csv`",
        "- `quantum_evrp_gap_score.csv`",
        "- `06_outputs/figures/active/02_requirement_mapping/tokyo_static_evrp_requirement_coverage.png`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gap = make_gap_table()
    static_dynamic = make_static_dynamic_table(gap)
    score = make_score_table(gap)

    gap.to_csv(OUT / "evrp_requirement_gap_evidence_table.csv", index=False)
    static_dynamic.to_csv(OUT / "940_20260705_v03_static_vs_dynamic_readiness_table.csv", index=False)
    score.to_csv(OUT / "quantum_evrp_gap_score.csv", index=False)
    make_figure(score)
    (OUT / "evrp_requirement_gap_interpretation_summary.md").write_text(
        make_md(gap, static_dynamic, score),
        encoding="utf-8",
    )

    for path in [
        OUT / "evrp_requirement_gap_evidence_table.csv",
        OUT / "940_20260705_v03_static_vs_dynamic_readiness_table.csv",
        OUT / "quantum_evrp_gap_score.csv",
        FIG / "tokyo_static_evrp_requirement_coverage.png",
        OUT / "evrp_requirement_gap_interpretation_summary.md",
    ]:
        print(path)


if __name__ == "__main__":
    main()
