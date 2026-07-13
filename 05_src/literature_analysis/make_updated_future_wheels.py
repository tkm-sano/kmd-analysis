from __future__ import annotations

import math
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch
from matplotlib import rcParams


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/use_case_scenario"
FIG = ROOT / "figures" / "06_future_wheels"

NODE_CSV = OUT / "updated_future_wheels_node_scoring.csv"
RANKED_CSV = OUT / "updated_future_wheels_expected_impact_ranked.csv"
LINKAGE_CSV = OUT / "updated_future_wheels_to_tokyo_evrp_linkage.csv"
SUMMARY_MD = OUT / "updated_future_wheels_summary.md"
NETWORK_FIG = FIG / "updated_future_wheels_network.png"
NETWORK_FIG_JA = FIG / "updated_future_wheels_network_ja.png"
BAR_FIG = FIG / "updated_future_wheels_expected_impact_bar_chart.png"
BAR_FIG_JA = FIG / "updated_future_wheels_expected_impact_bar_chart_ja.png"


PLAUSIBILITY = {1: 0.2, 2: 0.5, 3: 0.8}

rcParams["font.family"] = "Hiragino Sans"
rcParams["axes.unicode_minus"] = False


NODE_COLUMNS = [
    "node_id",
    "parent_node_id",
    "node_label",
    "node_label_ja",
    "node_layer",
    "STEEP_tag",
    "desirability",
    "time_horizon",
    "conditional_plausibility_score",
    "conditional_plausibility",
    "impact_axis",
    "impact_score",
    "impact_value",
    "evidence_strength_score",
    "evidence_sources",
    "scoring_rationale",
    "uncertainty_flag",
    "cumulative_plausibility",
    "plausibility_weighted_impact",
    "tokyo_evrp_link",
    "quantum_gap_link",
]


def uncertainty(score: int | float | str) -> str:
    if score == 3:
        return "low"
    if score == 2:
        return "medium"
    if score == 1:
        return "high"
    return ""


def wrap_label(label: object, width: int, japanese: bool = False) -> str:
    text = str(label)
    if japanese:
        return "\n".join(text[i : i + width] for i in range(0, len(text), width))
    return "\n".join(textwrap.wrap(text, width=width))


def nodes() -> list[dict]:
    return [
        {
            "node_id": "UFW0",
            "parent_node_id": "",
            "node_label": "Tokyo public data are used to define a static EVRP scenario",
            "node_label_ja": "東京公開データから静的EVRPシナリオを定義する",
            "node_layer": "root",
            "STEEP_tag": "technology",
            "desirability": "mixed",
            "time_horizon": "medium",
            "conditional_plausibility_score": "",
            "impact_axis": "",
            "impact_score": "",
            "evidence_strength_score": "",
            "evidence_sources": "tokyo_synthetic_evrp_scenario_assumptions.md; tokyo_evrp_scenario_design.csv",
            "scoring_rationale": "Root node fixed by the updated analysis; not scored as an uncertain branch.",
            "tokyo_evrp_link": "tokyo_evrp_scenario_design.csv",
            "quantum_gap_link": "evrp_requirement_gap_evidence_table.csv",
        },
        {
            "node_id": "UFW1",
            "parent_node_id": "UFW0",
            "node_label": "Public data make static EVRP requirements definable",
            "node_label_ja": "公開データにより静的EVRP要件を定義できる",
            "node_layer": "first_order",
            "STEEP_tag": "social",
            "desirability": "positive",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "requirement_definition",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "OCM detailed chargers; P31 depot candidates; freight-flow CSVs; e-Stat mesh; vehicle specs; OSM context",
            "scoring_rationale": "The updated scenario tables define chargers, depots, vehicles, customer-node rules, and EVRP scenario sizes.",
            "tokyo_evrp_link": "scenario_available_chargers.csv; scenario_depots.csv; vehicle_scenario_rules.csv; synthetic_customer_node_rules.csv",
            "quantum_gap_link": "quantum_evrp_gap_score.csv",
        },
        {
            "node_id": "UFW1A",
            "parent_node_id": "UFW1",
            "node_label": "Synthetic customer nodes must be defined as scenario inputs",
            "node_label_ja": "合成顧客ノードをシナリオ入力として定義する必要がある",
            "node_layer": "outcome",
            "STEEP_tag": "technical",
            "desirability": "positive",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "requirement_definition",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "synthetic_customer_node_rules.csv; freight-flow CSVs; e-Stat mesh",
            "scoring_rationale": "Customer nodes are not observed stops; the update defines small/medium/large synthetic demand-node rules.",
            "tokyo_evrp_link": "synthetic_customer_node_rules.csv",
            "quantum_gap_link": "REQ-01 customers / demand nodes",
        },
        {
            "node_id": "UFW1B",
            "parent_node_id": "UFW1",
            "node_label": "Depot and vehicle assumptions must be treated as controlled variables",
            "node_label_ja": "デポと車両仮定を制御変数として扱う必要がある",
            "node_layer": "outcome",
            "STEEP_tag": "technical",
            "desirability": "positive",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "requirement_definition",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "scenario_depots.csv; vehicle_scenario_rules.csv; official vehicle specification sources",
            "scoring_rationale": "P31 logistics facilities and official vehicle specs allow depot and vehicle assumptions to be controlled rather than inferred from EV stock.",
            "tokyo_evrp_link": "scenario_depots.csv; vehicle_scenario_rules.csv",
            "quantum_gap_link": "REQ-02 vehicles; REQ-07 depot",
        },
        {
            "node_id": "UFW2",
            "parent_node_id": "UFW0",
            "node_label": "Public charger availability must be treated as a scenario uncertainty",
            "node_label_ja": "公共充電器の利用可能性をシナリオ不確実性として扱う必要がある",
            "node_layer": "first_order",
            "STEEP_tag": "technical",
            "desirability": "mixed",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "428_20260705_open_charge_map_tokyo_boundary_clipped_connections.csv; charger_screening_rules.csv; scenario_available_chargers.csv",
            "scoring_rationale": "N03-clipped OCM data provide charger candidates, but usage_type is missing for many CHAdeMO records and strict screening leaves 12 candidates.",
            "tokyo_evrp_link": "charger_screening_rules.csv; scenario_available_chargers.csv",
            "quantum_gap_link": "REQ-03 charging stations",
        },
        {
            "node_id": "UFW2A",
            "parent_node_id": "UFW2",
            "node_label": "Conservative charger screening leaves only 12 usable candidates",
            "node_label_ja": "保守的な充電器選別では利用候補が12件に限られる",
            "node_layer": "outcome",
            "STEEP_tag": "technical",
            "desirability": "negative",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "scenario_available_chargers.csv",
            "scoring_rationale": "Operational + PowerKW + CHAdeMO + Tesla/NACS exclusion produces a small conservative set.",
            "tokyo_evrp_link": "scenario_available_chargers.csv",
            "quantum_gap_link": "REQ-03 charging stations",
        },
        {
            "node_id": "UFW2B",
            "parent_node_id": "UFW2",
            "node_label": "Charger availability sensitivity analysis becomes necessary",
            "node_label_ja": "充電器利用可能性の感度分析が必要になる",
            "node_layer": "outcome",
            "STEEP_tag": "technical",
            "desirability": "mixed",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 5,
            "evidence_strength_score": 2,
            "evidence_sources": "OCM usage_type missingness; charger_screening_rules.csv",
            "scoring_rationale": "OCM usage_type missingness cannot be fully solved from OCM alone, so charger availability must be represented as a scenario assumption.",
            "tokyo_evrp_link": "future charger-set sensitivity: conservative/balanced/broad",
            "quantum_gap_link": "REQ-03 charging stations; REQ-05 SOC",
        },
        {
            "node_id": "UFW3",
            "parent_node_id": "UFW0",
            "node_label": "Charging, SOC, and energy constraints reveal a near-term gap in quantum VRP studies",
            "node_label_ja": "充電・SOC・エネルギー制約が量子VRP研究の直近ギャップを示す",
            "node_layer": "first_order",
            "STEEP_tag": "technology",
            "desirability": "mixed",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "quantum_relevance",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "evrp_requirement_gap_evidence_table.csv; quantum_evrp_gap_score.csv; Figure 1 CSV",
            "scoring_rationale": "Classical EVRP benchmarks directly encode many EVRP constraints, while current quantum VRP evidence is partial or missing for EV-specific requirements.",
            "tokyo_evrp_link": "tokyo_static_evrp_requirement_coverage.png",
            "quantum_gap_link": "quantum_evrp_gap_score.csv",
        },
        {
            "node_id": "UFW3A",
            "parent_node_id": "UFW3",
            "node_label": "Current quantum evidence does not directly cover charging, SOC, and energy use",
            "node_label_ja": "現在の量子側証拠は充電・SOC・エネルギー消費を直接扱えていない",
            "node_layer": "outcome",
            "STEEP_tag": "technology",
            "desirability": "negative",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "quantum_relevance",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "quantum_evrp_gap_score.csv",
            "scoring_rationale": "The updated coverage table marks charging stations, battery/SOC, and energy consumption as missing in the extracted quantum VRP evidence.",
            "tokyo_evrp_link": "vehicle_scenario_rules.csv; scenario_available_chargers.csv",
            "quantum_gap_link": "REQ-03; REQ-05; REQ-06",
        },
        {
            "node_id": "UFW3B",
            "parent_node_id": "UFW3",
            "node_label": "Real-time traffic adaptation should be treated as a later-stage extension",
            "node_label_ja": "リアルタイム交通対応は後段階の拡張として扱うべきである",
            "node_layer": "outcome",
            "STEEP_tag": "technology",
            "desirability": "mixed",
            "time_horizon": "long",
            "conditional_plausibility_score": 3,
            "impact_axis": "quantum_relevance",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "940_20260705_v03_static_vs_dynamic_readiness_table.csv; tokyo_static_evrp_requirement_coverage.png",
            "scoring_rationale": "The updated analysis shows that static EVRP requirements are the nearer gap before real-time traffic adaptation.",
            "tokyo_evrp_link": "940_20260705_v03_static_vs_dynamic_readiness_table.csv",
            "quantum_gap_link": "REQ-11 dynamic traffic adaptation",
        },
        {
            "node_id": "UFW4",
            "parent_node_id": "UFW0",
            "node_label": "Tokyo EVRP instances should first be tested with static distance and assumed travel time",
            "node_label_ja": "東京EVRP事例はまず静的距離と仮定移動時間で検証すべきである",
            "node_layer": "first_order",
            "STEEP_tag": "technical",
            "desirability": "positive",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 2,
            "evidence_sources": "tokyo_evrp_scenario_design.csv; OSM road data; EVRP benchmark fields",
            "scoring_rationale": "The scenario design defines S/M/L instances; the next step is to construct distance matrices and feasibility checks.",
            "tokyo_evrp_link": "tokyo_evrp_scenario_design.csv",
            "quantum_gap_link": "REQ-08 distance / travel-cost matrix",
        },
        {
            "node_id": "UFW4A",
            "parent_node_id": "UFW4",
            "node_label": "Static distance and assumed-speed travel time are sufficient for the baseline test",
            "node_label_ja": "基礎検証では静的距離と仮定速度による移動時間で十分である",
            "node_layer": "outcome",
            "STEEP_tag": "technical",
            "desirability": "positive",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 2,
            "evidence_sources": "tokyo_evrp_scenario_design.csv; 940_20260705_v03_static_vs_dynamic_readiness_table.csv",
            "scoring_rationale": "The baseline should test EVRP feasibility before adding real-time traffic adaptation.",
            "tokyo_evrp_link": "distance_matrix and feasibility outputs, next step",
            "quantum_gap_link": "REQ-08 distance / travel-cost matrix",
        },
        {
            "node_id": "UFW4B",
            "parent_node_id": "UFW4",
            "node_label": "Route feasibility checks must connect routes with SOC, charging time, and payload",
            "node_label_ja": "経路実行可能性判定ではSOC・充電時間・積載を接続する必要がある",
            "node_layer": "outcome",
            "STEEP_tag": "technical",
            "desirability": "positive",
            "time_horizon": "short",
            "conditional_plausibility_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 5,
            "evidence_strength_score": 2,
            "evidence_sources": "vehicle_scenario_rules.csv; scenario_available_chargers.csv; tokyo_evrp_scenario_design.csv",
            "scoring_rationale": "The route feasibility layer converts public-data inputs into the EVRP conditions missing from quantum evidence.",
            "tokyo_evrp_link": "future evrp_feasibility_summary outputs",
            "quantum_gap_link": "REQ-04; REQ-05; REQ-06",
        },
    ]


def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    def plausibility_from_score(x: object) -> float:
        if x == "" or pd.isna(x):
            return 1.0
        return float(PLAUSIBILITY[int(float(x))])

    df["conditional_plausibility"] = df["conditional_plausibility_score"].apply(plausibility_from_score)
    df["impact_value"] = df["impact_score"]
    by_id = {r["node_id"]: r for r in df.to_dict("records")}
    cumulative: dict[str, float] = {"UFW0": 1.0}

    def compute(node_id: str) -> float:
        if node_id in cumulative:
            return cumulative[node_id]
        row = by_id[node_id]
        parent = row["parent_node_id"]
        parent_plausibility = compute(parent)
        plausibility = float(row["conditional_plausibility"])
        cumulative[node_id] = parent_plausibility * plausibility
        return cumulative[node_id]

    for node_id in df["node_id"]:
        compute(node_id)
    df["cumulative_plausibility"] = df["node_id"].map(cumulative)
    df["plausibility_weighted_impact"] = df.apply(
        lambda r: "" if r["impact_score"] == "" or pd.isna(r["impact_score"]) else r["cumulative_plausibility"] * float(r["impact_score"]),
        axis=1,
    )
    df["uncertainty_flag"] = df["evidence_strength_score"].apply(
        lambda x: "" if x == "" or pd.isna(x) else uncertainty(int(x))
    )
    return df[NODE_COLUMNS]


def build_node_scoring() -> pd.DataFrame:
    df = pd.DataFrame(nodes())
    for col in NODE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return calculate_scores(df)


def positions() -> dict[str, tuple[float, float]]:
    return {
        "UFW0": (0.0, 0.0),
        "UFW1": (-3.0, 1.8),
        "UFW2": (3.0, 1.8),
        "UFW3": (-3.0, -1.8),
        "UFW4": (3.0, -1.8),
        "UFW1A": (-5.6, 2.8),
        "UFW1B": (-5.6, 1.0),
        "UFW2A": (5.6, 2.8),
        "UFW2B": (5.6, 1.0),
        "UFW3A": (-5.6, -1.0),
        "UFW3B": (-5.6, -2.8),
        "UFW4A": (5.6, -1.0),
        "UFW4B": (5.6, -2.8),
    }


COLORS = {
    "requirement_definition": "#5DAE8B",
    "operational_complexity": "#F0A35E",
    "quantum_relevance": "#8C6BB1",
}


def draw_network(df: pd.DataFrame, path: Path, japanese: bool = False) -> None:
    pos = positions()
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.axis("off")

    for _, r in df[df["parent_node_id"].astype(str).ne("")].iterrows():
        start = pos[r["parent_node_id"]]
        end = pos[r["node_id"]]
        arrow = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.2,
            color="#777777",
            shrinkA=30,
            shrinkB=30,
            alpha=0.85,
        )
        ax.add_patch(arrow)

    for _, r in df.iterrows():
        x, y = pos[r["node_id"]]
        label = r["node_label_ja"] if japanese else r["node_label"]
        label = wrap_label(label, width=18 if japanese else 18, japanese=japanese)
        color = "#e7eef8" if r["node_layer"] == "root" else COLORS.get(r["impact_axis"], "#dddddd")
        size = 0.76 if r["node_layer"] == "root" else 0.72
        circle = plt.Circle((x, y), size, facecolor=color, edgecolor="#333333", linewidth=1.5, alpha=0.95)
        ax.add_patch(circle)
        ax.text(x, y, label, ha="center", va="center", fontsize=8.4)

    title = (
        "Updated Future Wheels: Tokyo static EVRP requirements before dynamic traffic adaptation"
        if not japanese
        else "Updated Future Wheels: 動的交通対応の前に静的EVRP要件を定義する"
    )
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlim(-6.8, 6.8)
    ax.set_ylim(-4.0, 4.0)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def draw_bar(df: pd.DataFrame, path: Path, japanese: bool = False) -> pd.DataFrame:
    ranked = df[df["node_layer"].ne("root")].copy()
    ranked["plausibility_weighted_impact"] = pd.to_numeric(ranked["plausibility_weighted_impact"], errors="coerce")
    ranked_desc = ranked.sort_values("plausibility_weighted_impact", ascending=False)
    ranked_desc.to_csv(RANKED_CSV, index=False)
    top = ranked_desc.head(10).sort_values("plausibility_weighted_impact", ascending=True)
    labels = top["node_label_ja" if japanese else "node_label"].apply(
        lambda x: wrap_label(x, width=20 if japanese else 38, japanese=japanese)
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = [COLORS.get(axis, "#999999") for axis in top["impact_axis"]]
    ax.barh(labels, top["plausibility_weighted_impact"], color=colors, edgecolor="#333333", linewidth=0.7)
    ax.set_xlabel("Plausibility-weighted impact = cumulative plausibility x impact value")
    title = (
        "Updated Future Wheels: Plausibility-Weighted Impact"
        if not japanese
        else "Updated Future Wheels: plausibility加重インパクト"
    )
    ax.set_title(title, fontsize=14, pad=12)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return ranked_desc


def make_linkage(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        [
            "node_id",
            "node_label",
            "node_label_ja",
            "tokyo_evrp_link",
            "quantum_gap_link",
            "evidence_sources",
            "scoring_rationale",
        ]
    ].copy()


def make_summary(df: pd.DataFrame) -> str:
    ranked = df[df["node_layer"].ne("root")].copy()
    ranked["plausibility_weighted_impact"] = pd.to_numeric(ranked["plausibility_weighted_impact"], errors="coerce")
    ranked = ranked.sort_values("plausibility_weighted_impact", ascending=False).head(6)
    lines = [
        "# Updated Future Wheels Summary",
        "",
        "## Goal",
        "",
        "The updated Future Wheels is used as an evidence-informed impact mapping method. It shows how a public-data-grounded static EVRP scenario for Tokyo creates requirements and uncertainty before dynamic traffic adaptation is considered.",
        "",
        "This is not a validated probabilistic forecast. The score named plausibility represents a researcher-defined, evidence-informed judgment about whether each impact link is supported by the available data, benchmarks, and literature.",
        "",
        "## Main Interpretation",
        "",
        "Tokyo public data can define static EVRP requirements, but current quantum VRP evidence remains weak for EV-specific requirements such as charging stations, battery/SOC, and energy consumption. Therefore, dynamic traffic adaptation is a later-stage question; the nearer research gap is static EVRP constraint coverage.",
        "",
        "## Top Plausibility-Weighted Impact Nodes",
        "",
        "| node_id | node | plausibility_weighted_impact | interpretation |",
        "|---|---|---:|---|",
    ]
    for _, r in ranked.iterrows():
        lines.append(
            f"| {r['node_id']} | {r['node_label']} | {float(r['plausibility_weighted_impact']):.2f} | {r['scoring_rationale']} |"
        )
    lines += [
        "",
        "## Scoring Notes",
        "",
        "| item | meaning |",
        "|---|---|",
        "| conditional_plausibility | Researcher-defined link plausibility, scored as 0.2 / 0.5 / 0.8 from weak to strong support. |",
        "| cumulative_plausibility | Product of conditional plausibility values from the root to the node. |",
        "| impact_value | Researcher-defined importance of the impact for the study, scored from 1 to 5. |",
        "| plausibility_weighted_impact | cumulative_plausibility x impact_value. This ranks which impact chains deserve priority, not real-world event probability. |",
    ]
    lines += [
        "",
        "## Outputs",
        "",
        "- `updated_future_wheels_node_scoring.csv`",
        "- `updated_future_wheels_expected_impact_ranked.csv`",
        "- `updated_future_wheels_to_tokyo_evrp_linkage.csv`",
        "- `06_outputs/figures/active/06_future_wheels/updated_future_wheels_network.png`",
        "- `06_outputs/figures/active/06_future_wheels/updated_future_wheels_network_ja.png`",
        "- `06_outputs/figures/active/06_future_wheels/updated_future_wheels_expected_impact_bar_chart.png`",
        "- `06_outputs/figures/active/06_future_wheels/updated_future_wheels_expected_impact_bar_chart_ja.png`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    df = build_node_scoring()
    df.to_csv(NODE_CSV, index=False)
    ranked = draw_bar(df, BAR_FIG, japanese=False)
    draw_bar(df, BAR_FIG_JA, japanese=True)
    draw_network(df, NETWORK_FIG, japanese=False)
    draw_network(df, NETWORK_FIG_JA, japanese=True)
    make_linkage(df).to_csv(LINKAGE_CSV, index=False)
    SUMMARY_MD.write_text(make_summary(df), encoding="utf-8")

    for path in [
        NODE_CSV,
        RANKED_CSV,
        LINKAGE_CSV,
        SUMMARY_MD,
        NETWORK_FIG,
        NETWORK_FIG_JA,
        BAR_FIG,
        BAR_FIG_JA,
    ]:
        print(path)


if __name__ == "__main__":
    main()
