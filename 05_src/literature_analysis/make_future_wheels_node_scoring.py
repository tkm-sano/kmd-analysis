from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/use_case_scenario"
PROBABILITY_SCALE = OUT / "future_wheels_probability_scale.csv"
NODE_SCORING = OUT / "future_wheels_node_scoring.csv"
NODE_SCORING_MD = OUT / "future_wheels_node_scoring_summary.md"

NODE_COLUMNS = [
    "node_id",
    "parent_node_id",
    "node_label",
    "node_layer",
    "STEEP_tag",
    "desirability",
    "time_horizon",
    "conditional_probability_score",
    "conditional_probability",
    "impact_axis",
    "impact_score",
    "impact_value",
    "evidence_strength_score",
    "evidence_sources",
    "scoring_rationale",
    "uncertainty_flag",
    "cumulative_probability",
    "expected_impact",
]

NODE_TAGS = {
    "FW0": {"STEEP_tag": "technology", "desirability": "mixed", "time_horizon": "medium"},
    "FW1": {"STEEP_tag": "social", "desirability": "mixed", "time_horizon": "short"},
    "FW1A": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "short"},
    "FW1B": {"STEEP_tag": "technology", "desirability": "negative", "time_horizon": "short"},
    "FW2": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "short"},
    "FW2A": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "short"},
    "FW2B": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "short"},
    "FW2C": {"STEEP_tag": "technology", "desirability": "negative", "time_horizon": "short"},
    "FW3": {"STEEP_tag": "social", "desirability": "mixed", "time_horizon": "medium"},
    "FW3A": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "short"},
    "FW3B": {"STEEP_tag": "technology", "desirability": "negative", "time_horizon": "short"},
    "FW4": {"STEEP_tag": "economic", "desirability": "negative", "time_horizon": "short"},
    "FW4A": {"STEEP_tag": "technical", "desirability": "positive", "time_horizon": "short"},
    "FW4B": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "long"},
    "FW5": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "short"},
    "FW5A": {"STEEP_tag": "technical", "desirability": "positive", "time_horizon": "short"},
    "FW5B": {"STEEP_tag": "technical", "desirability": "mixed", "time_horizon": "medium"},
    "FW6": {"STEEP_tag": "technology", "desirability": "positive", "time_horizon": "short"},
}


def uncertainty_from_evidence(score: int | str) -> str:
    if score == 3:
        return "low"
    if score == 2:
        return "medium"
    if score == 1:
        return "high"
    return ""


def build_nodes() -> list[dict]:
    return [
        {
            "node_id": "FW0",
            "parent_node_id": "",
            "node_label": "Charging-aware EV last-mile routing in Tokyo",
            "node_layer": "root",
            "conditional_probability_score": "",
            "impact_axis": "",
            "impact_score": "",
            "evidence_strength_score": "",
            "evidence_sources": "selected_use_case_scope; Tokyo public data; EVRP benchmark; quantum VRP Figure 1",
            "scoring_rationale": "Root node fixed by the selected use case; not scored as an uncertain branch.",
            "uncertainty_flag": "",
        },
        {
            "node_id": "FW1",
            "parent_node_id": "FW0",
            "node_label": "Dense Tokyo demand creates many potential customer nodes",
            "node_layer": "first_order",
            "conditional_probability_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-01; e-Stat Tokyo mesh population; N03 Tokyo boundary; Tokyo OSM road-network variables",
            "scoring_rationale": "Tokyo mesh population and boundary data support dense urban demand as a customer-node proxy, while the requirement map treats customers as a core EVRP requirement.",
        },
        {
            "node_id": "FW1A",
            "parent_node_id": "FW1",
            "node_label": "Synthetic customer-node set must be defined explicitly",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-01; EVRP benchmark instance fields; e-Stat mesh population",
            "scoring_rationale": "Population and road data are proxies, not observed delivery customers; therefore Tokyo customer nodes must be scenario-defined.",
        },
        {
            "node_id": "FW1B",
            "parent_node_id": "FW1",
            "node_label": "Existing quantum VRP evidence remains mostly smaller than EVRP-scale customer sets",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "quantum_relevance",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "Figure 1 plot data; REQ-01; EVRP benchmark instance summary",
            "scoring_rationale": "Figure 1 rows are mostly small VRP instances, while EVRP benchmarks include larger customer counts; Golden_5 is resource estimation rather than execution.",
        },
        {
            "node_id": "FW2",
            "parent_node_id": "FW0",
            "node_label": "Charging stations and SOC feasibility become core routing constraints",
            "node_layer": "first_order",
            "conditional_probability_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-03; REQ-05; Schneider/Goeke E-VRPTW; E-CVRP instance fields; Open Charge Map; IEA charging variables",
            "scoring_rationale": "Parsed EVRP benchmarks include charging stations and energy constraints, and Tokyo charging data provide a public-data proxy for station sets.",
        },
        {
            "node_id": "FW2A",
            "parent_node_id": "FW2",
            "node_label": "Candidate charging stations can be geocoded, but coverage remains imperfect",
            "node_layer": "second_order",
            "conditional_probability_score": 2,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 2,
            "evidence_sources": "Open Charge Map Tokyo bounding-box stations; IEA public charging points; REQ-03",
            "scoring_rationale": "Public charging data can support candidate station construction, but station coverage, status, and operator-specific availability remain proxy limitations.",
        },
        {
            "node_id": "FW2B",
            "parent_node_id": "FW2",
            "node_label": "Battery capacity and SOC parameters remain scenario-defined",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-05; EVRP benchmark instance fields; social_stage_variable_extraction",
            "scoring_rationale": "EVRP benchmarks expose battery and energy-consumption fields, but Tokyo public data do not provide vehicle-specific battery capacity for delivery fleets.",
        },
        {
            "node_id": "FW2C",
            "parent_node_id": "FW2",
            "node_label": "Quantum VRP evidence does not yet show direct charging-station or SOC coverage",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "quantum_relevance",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "Figure 1 plot data; REQ-03; REQ-05",
            "scoring_rationale": "Requirement-map comparison shows charging stations and SOC are central in EVRP benchmarks but not visible in the extracted Figure 1 quantum VRP rows.",
        },
        {
            "node_id": "FW3",
            "parent_node_id": "FW0",
            "node_label": "Time windows and service reliability shape routing feasibility",
            "node_layer": "first_order",
            "conditional_probability_score": 2,
            "impact_axis": "delay",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-09; Schneider/Goeke E-VRPTW; World Bank LPI Timeliness; Toei Bus GTFS stop_times",
            "scoring_rationale": "E-VRPTW benchmarks contain ReadyTime, DueDate, and ServiceTime fields; Tokyo/public data support timeliness context but not delivery-specific time windows.",
        },
        {
            "node_id": "FW3A",
            "parent_node_id": "FW3",
            "node_label": "Tokyo delivery time windows need explicit scenario assumptions",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "delay",
            "impact_score": 4,
            "evidence_strength_score": 2,
            "evidence_sources": "REQ-09; World Bank LPI Timeliness; GTFS stop_times; EVRPTW benchmark fields",
            "scoring_rationale": "Public timeliness and schedule data do not directly provide parcel delivery windows, so time-window values must be assigned by scenario design.",
        },
        {
            "node_id": "FW3B",
            "parent_node_id": "FW3",
            "node_label": "EV charging and time-window constraints are rarely combined in current quantum evidence",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "quantum_relevance",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "Figure 1 plot data; REQ-09; REQ-03; REQ-05",
            "scoring_rationale": "Some quantum VRPTW evidence exists, but the extracted scope does not show time windows combined with EV charging and SOC feasibility.",
        },
        {
            "node_id": "FW4",
            "parent_node_id": "FW0",
            "node_label": "Traffic and travel-cost uncertainty affect route feasibility",
            "node_layer": "first_order",
            "conditional_probability_score": 2,
            "impact_axis": "delay",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-08; JARTIC Tokyo traffic API; Tokyo Metropolitan Police traffic statistics; MLIT Road Traffic Census; OSM road network",
            "scoring_rationale": "Tokyo road-network and traffic-volume data support traffic intensity as a routing-context proxy, though not as observed delivery travel times.",
        },
        {
            "node_id": "FW4A",
            "parent_node_id": "FW4",
            "node_label": "Static traffic proxies can support travel-cost stress scenarios",
            "node_layer": "second_order",
            "conditional_probability_score": 3,
            "impact_axis": "delay",
            "impact_score": 3,
            "evidence_strength_score": 3,
            "evidence_sources": "JARTIC summary; Tokyo police border traffic statistics; MLIT Road Traffic Census summary",
            "scoring_rationale": "Multiple traffic data sources are available, but they are best used as stress or uncertainty proxies rather than delivery route observations.",
        },
        {
            "node_id": "FW4B",
            "parent_node_id": "FW4",
            "node_label": "Dynamic dispatch remains an optional extension rather than the first analysis target",
            "node_layer": "outcome",
            "conditional_probability_score": 2,
            "impact_axis": "operational_complexity",
            "impact_score": 3,
            "evidence_strength_score": 2,
            "evidence_sources": "JARTIC hourly API; future_wheels_pre_analysis_action_status; dynamic VRP literature",
            "scoring_rationale": "Hourly traffic data can support a dynamic branch, but current study design does not center realtime dispatch.",
        },
        {
            "node_id": "FW5",
            "parent_node_id": "FW0",
            "node_label": "Fleet size, cargo capacity, and depot choices must be scenario-controlled",
            "node_layer": "first_order",
            "conditional_probability_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-02; REQ-04; REQ-07; E-CVRP instance fields; EVRP benchmark requirement table",
            "scoring_rationale": "EVRP benchmark files define vehicles, capacity, and depot structure, while Tokyo public data do not provide operator-specific fleet or depot data.",
        },
        {
            "node_id": "FW5A",
            "parent_node_id": "FW5",
            "node_label": "Fleet size should not be inferred from national EV stock",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 4,
            "evidence_strength_score": 3,
            "evidence_sources": "REQ-02; IEA Japan EV stock variables; EVRP benchmark instance fields",
            "scoring_rationale": "National EV stock is context only; EVRP vehicle count must be set as a benchmark or operator scenario parameter.",
        },
        {
            "node_id": "FW5B",
            "parent_node_id": "FW5",
            "node_label": "Depot location requires synthetic placement or separate logistics-facility data",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "operational_complexity",
            "impact_score": 3,
            "evidence_strength_score": 2,
            "evidence_sources": "REQ-07; EVRP benchmark instance fields; Tokyo public-data inventory",
            "scoring_rationale": "Benchmarks contain depots, but public Tokyo data collected so far do not identify operator depot locations.",
        },
        {
            "node_id": "FW6",
            "parent_node_id": "FW0",
            "node_label": "Social requirement coverage and quantum validation maturity must be evaluated separately",
            "node_layer": "outcome",
            "conditional_probability_score": 3,
            "impact_axis": "quantum_relevance",
            "impact_score": 5,
            "evidence_strength_score": 3,
            "evidence_sources": "Figure 1 plot data; Tokyo-EVRP-Quantum Requirement Map; EVRP Benchmark Requirement Table",
            "scoring_rationale": "Existing evidence shows quantum validation stages can advance without covering EVRP-specific social and operational requirements.",
        },
    ]


def calculate_scores(nodes: list[dict]) -> pd.DataFrame:
    prob_map = pd.read_csv(PROBABILITY_SCALE).set_index("score")["probability"].to_dict()
    by_id: dict[str, dict] = {node["node_id"]: node for node in nodes}

    for node in nodes:
        node.update(NODE_TAGS.get(node["node_id"], {}))
        probability_score = node["conditional_probability_score"]
        node["conditional_probability"] = 1.0 if node["node_layer"] == "root" else prob_map[int(probability_score)]
        node["impact_value"] = "" if node["impact_score"] == "" else int(node["impact_score"])
        if not node.get("uncertainty_flag"):
            node["uncertainty_flag"] = uncertainty_from_evidence(node["evidence_strength_score"])

    def cumulative_probability(node_id: str) -> float:
        node = by_id[node_id]
        if node["node_layer"] == "root" or not node["parent_node_id"]:
            return 1.0
        return cumulative_probability(node["parent_node_id"]) * float(node["conditional_probability"])

    for node in nodes:
        node["cumulative_probability"] = round(cumulative_probability(node["node_id"]), 4)
        if node["impact_value"] == "":
            node["expected_impact"] = ""
        else:
            node["expected_impact"] = round(node["cumulative_probability"] * float(node["impact_value"]), 4)

    return pd.DataFrame(nodes, columns=NODE_COLUMNS)


def write_markdown_summary(df: pd.DataFrame) -> None:
    scored = df[df["node_layer"] != "root"].copy()
    top = scored.sort_values("expected_impact", ascending=False).head(8)
    lines = [
        "# Future Wheels node scoring summary",
        "",
        "This table uses rule-based semi-quantitative scoring. Conditional probability is not an observed social probability; it represents the plausibility of adopting a branch in the Future Wheels analysis based on available evidence.",
        "",
        "## Highest expected-impact nodes",
        "",
        "| node_id | node_label | impact_axis | cumulative_probability | impact_value | expected_impact |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in top.to_dict("records"):
        lines.append(
            f"| {row['node_id']} | {row['node_label']} | {row['impact_axis']} | {row['cumulative_probability']} | {row['impact_value']} | {row['expected_impact']} |"
        )
    lines.extend(
        [
            "",
            "## Scoring rule",
            "",
            "- conditional_probability_score: 1=0.2, 2=0.5, 3=0.8.",
            "- impact_value: equals impact_score on the 1-5 scale.",
            "- cumulative_probability: product of conditional probabilities from the root.",
            "- expected_impact: cumulative_probability x impact_value.",
            "- evidence_strength_score is used for auditability and uncertainty flags, not multiplied into expected impact.",
        ]
    )
    NODE_SCORING_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = calculate_scores(build_nodes())
    df.to_csv(NODE_SCORING, index=False)
    write_markdown_summary(df)
    print(NODE_SCORING.relative_to(ROOT))
    print(NODE_SCORING_MD.relative_to(ROOT))


if __name__ == "__main__":
    main()
