from pathlib import Path
import csv
import re
import textwrap

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "literature" / "200_20260625_circuit_resources.csv"
ALIGNMENT_DATA = ROOT / "literature" / "206_20260626_social_quantum_readiness_alignment.csv"
FIG = ROOT / "figures" / "01_quantum_vrp_evidence"

SOCIAL_AXIS_COLUMNS = [
    "problem_readiness",
    "problem_readiness_score",
    "data_workflow_readiness",
    "data_workflow_readiness_score",
    "constraint_readiness",
    "constraint_readiness_score",
    "resource_readiness",
    "social_resource_readiness_score",
    "technology_readiness",
    "social_technology_readiness_score",
    "social_score_rule",
]


def parse_width(value: str):
    if value is None:
        return None
    text = str(value)
    match = re.search(r"^\s*([0-9][0-9,]*)\s*qubits?", text)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def validation_stage(row):
    backend = str(row.get("hardware_or_backend", "")).lower()
    status = str(row.get("extraction_status", "")).lower()
    notes = str(row.get("notes", "")).lower()
    source = str(row.get("source_location", "")).lower()

    is_simulation = any(token in backend for token in ["simulation", "simulator", "statevector", "qasm", "qiskit simulation"])
    has_hardware_name = any(token in backend for token in ["ibm", "rigetti", "ionq", "quantum system", "hardware"])

    if "resource estimation" in backend:
        return "Resource estimation"
    if has_hardware_name and is_simulation:
        return "Simulator + hardware check"
    if has_hardware_name:
        return "Hardware run / target"
    if is_simulation:
        return "Classical simulation"
    if "theory" in backend or status in {"definition", "methodology"} or "table 1" in source or "theoretical" in notes:
        return "Theory / method"
    return "Other"


def readable_instance_scope(row):
    instance = str(row["instance_or_scope"])
    problem = str(row["problem"])

    tuple_match = re.fullmatch(r"\((\d+),(\d+)\) instance", instance)
    if tuple_match:
        n_locations, n_vehicles = tuple_match.groups()
        return f"{n_locations}-location, {n_vehicles}-vehicle {problem} instance"

    route_match = re.fullmatch(r"(\d+)-route instance", instance)
    if route_match:
        return f"{route_match.group(1)}-route candidate set"

    tsp_match = re.fullmatch(r"(\d+)-node TSP subproblem", instance)
    if tsp_match:
        return f"{tsp_match.group(1)}-node TSP subproblem from CVRP decomposition"

    node_vehicle_match = re.fullmatch(r"(\d+)-node (\d+)-vehicle instance", instance)
    if node_vehicle_match:
        n_nodes, n_vehicles = node_vehicle_match.groups()
        return f"{n_nodes}-node, {n_vehicles}-vehicle {problem} instance"

    node_match = re.fullmatch(r"(\d+)-node instance", instance)
    if node_match:
        return f"{node_match.group(1)}-node {problem} instance"

    hvrp_instances = {
        "problem instance I": "HVRP instance I: 3 cities and 1 truck",
        "problem instance II": "HVRP instance II: 4 cities and 1 truck",
        "problem instance III": "HVRP instance III: 3 cities and 2 trucks",
    }
    if instance in hvrp_instances:
        return hvrp_instances[instance]

    if instance == "Golden_5":
        return "Golden_5 CVRP benchmark instance: 200 customers, 5 vehicles, capacity 900"

    return instance


def short_label(row):
    paper = str(row["paper_id"])
    instance = str(row["instance_or_scope"])
    encoding = str(row["formulation_or_encoding"])

    paper_short = {
        "vrptw-2023-leonidas": "VRPTW 2023",
        "hvrp-2024-fitzek": "HVRP 2024",
        "cvrp-2025-onah-utility": "CVRP 2025",
        "vrp-2020-azad": "VRP 2020",
        "vrp-2025-azfar-arxiv": "VRP 2025",
        "cvrp-2023-xie": "CVRP 2023",
        "cvrp-2023-palackal": "CVRP 2023",
    }.get(paper, paper)

    if len(instance) > 30:
        instance = instance[:27] + "..."
    if len(encoding) > 22:
        encoding = encoding[:19] + "..."
    return f"{paper_short} | {instance} | {encoding}"


PROBLEM_DESCRIPTIONS = {
    "VRP": "Vehicle Routing Problem.",
    "CVRP": "Capacitated Vehicle Routing Problem.",
    "HVRP": "Heterogeneous Vehicle Routing Problem.",
    "VRPTW": "Vehicle Routing Problem with Time Windows.",
    "CVRP / TSP decomposition": "CVRP treated through decomposition into TSP subproblems.",
}


VALIDATION_STAGE_DESCRIPTIONS = {
    "Resource estimation": "Resource estimate only",
    "Hardware run / target": "Hardware execution or hardware-targeted transpilation evidence",
    "Simulator + hardware check": "Simulation evidence with hardware-aware or hardware-platform checks",
    "Classical simulation": "Quantum algorithm evaluated on a classical simulator",
    "Theory / method": "Theoretical or methodological resource statement.",
    "Other": "Validation stage not classified above.",
}


def problem_description(problem: str) -> str:
    return PROBLEM_DESCRIPTIONS.get(str(problem), "Problem class reported by the source paper.")


def validation_stage_description(stage: str) -> str:
    return VALIDATION_STAGE_DESCRIPTIONS.get(str(stage), "Validation stage assigned from backend and evidence type.")


def qrl_evidence_level(stage: str) -> str:
    return {
        "Resource estimation": "QRL4",
        "Hardware run / target": "QRL3",
        "Simulator + hardware check": "QRL3",
        "Classical simulation": "QRL2",
        "Theory / method": "QRL1",
    }.get(str(stage), "")


def srl_assignment(row):
    paper = str(row.get("paper_id", ""))
    problem = str(row.get("problem", ""))
    instance = str(row.get("instance_or_scope", "")).lower()
    encoding = str(row.get("formulation_or_encoding", "")).lower()

    if paper == "cvrp-2025-onah-utility" or "golden_5" in instance:
        return {
            "social_readiness_level": "SRL4",
            "srl_assignment_basis": "Large benchmark-scale CVRP resource estimate; used as social-side resource-readiness pressure, not as hardware execution evidence.",
            "srl_assignment_confidence": "medium",
        }
    if problem == "VRPTW":
        return {
            "social_readiness_level": "SRL2",
            "srl_assignment_basis": "Time-window routing conditions are specified, but EV charging or dynamic operational workflow is not the reported instance focus.",
            "srl_assignment_confidence": "medium",
        }
    if "CVRP" in problem or "capacity" in instance or "tsp subproblem" in instance or "clustering" in encoding:
        return {
            "social_readiness_level": "SRL2",
            "srl_assignment_basis": "Capacity or decomposed routing conditions are present; this supports constrained routing readiness rather than EV-integrated operation.",
            "srl_assignment_confidence": "medium",
        }
    if problem == "HVRP" or "truck" in instance:
        return {
            "social_readiness_level": "SRL2",
            "srl_assignment_basis": "Vehicle/truck heterogeneity is present, but the reported instance remains small and does not include EV charging or dynamic workflow requirements.",
            "srl_assignment_confidence": "medium",
        }
    if problem == "VRP":
        return {
            "social_readiness_level": "SRL1",
            "srl_assignment_basis": "Small static VRP instance with limited operational constraints; useful as a routing-demand baseline, not deployment readiness.",
            "srl_assignment_confidence": "medium",
        }
    return {
        "social_readiness_level": "SRL1",
        "srl_assignment_basis": "Default conservative assignment for a small or abstract routing instance without explicit operational constraints.",
        "srl_assignment_confidence": "low",
    }


def readiness_relation(srl_level: str, qrl_level: str) -> str:
    srl_match = re.search(r"SRL(\d+)", str(srl_level))
    qrl_match = re.search(r"QRL(\d+)", str(qrl_level))
    if not srl_match or not qrl_match:
        return ""
    diff = int(srl_match.group(1)) - int(qrl_match.group(1))
    if diff == 0:
        return "stage-aligned"
    if diff > 0:
        return "social demand ahead of quantum evidence"
    return "quantum evidence ahead of assigned social scope"


def axis_instance_label(row):
    instance = str(row["instance_or_scope"])
    encoding = str(row["formulation_or_encoding"])

    instance = instance.replace(
        "Golden_5 CVRP benchmark instance: 200 customers, 5 vehicles, capacity 900",
        "Golden_5 CVRP\n200 cust., 5 veh.",
    )
    instance = re.sub(r"(\d+)-node TSP subproblem from CVRP decomposition", r"\1-node TSP\nfrom CVRP", instance)
    instance = re.sub(r"(\d+)-location, (\d+)-vehicle VRP instance", r"\1-loc., \2-veh. VRP", instance)
    instance = re.sub(r"(\d+)-node, (\d+)-vehicle VRP instance", r"\1-node, \2-veh. VRP", instance)
    instance = instance.replace("HVRP instance I: 3 cities and 1 truck", "HVRP I\n3 cities, 1 truck")
    instance = instance.replace("HVRP instance II: 4 cities and 1 truck", "HVRP II\n4 cities, 1 truck")
    instance = instance.replace("HVRP instance III: 3 cities and 2 trucks", "HVRP III\n3 cities, 2 trucks")

    encoding_short = encoding
    encoding_short = encoding_short.replace("edge-based link QUBO / QAOA", "edge-QUBO/QAOA")
    encoding_short = encoding_short.replace("edge-based Ising/QAOA encoding", "Ising/QAOA")
    encoding_short = encoding_short.replace("clustering + TSP; QAOA and hardware-efficient VQE", "cluster+TSP/VQE")
    encoding_short = encoding_short.replace("HOBO/direct encoding", "HOBO/direct")
    encoding_short = encoding_short.replace("minimal encoding", "minimal")
    encoding_short = encoding_short.replace("full encoding", "full")
    encoding_short = encoding_short.replace("Ising mapping", "Ising")
    encoding_short = textwrap.shorten(encoding_short, width=18, placeholder="...")

    return f"{instance}\n{encoding_short}"


def main():
    with DATA.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    with ALIGNMENT_DATA.open(newline="", encoding="utf-8-sig") as f:
        alignment_rows = list(csv.DictReader(f))
    alignment_by_srl = {row["social_readiness_level"]: row for row in alignment_rows}

    for row in rows:
        row["instance_or_scope"] = readable_instance_scope(row)
        row["width_numeric"] = parse_width(row.get("circuit_width_qubits"))
        row["validation_stage"] = validation_stage(row)
        row["label"] = short_label(row)
        row["problem_description"] = problem_description(row["problem"])
        row["validation_stage_description"] = validation_stage_description(row["validation_stage"])
        row["qrl_evidence_level"] = qrl_evidence_level(row["validation_stage"])
        row.update(srl_assignment(row))
        alignment = alignment_by_srl.get(row["social_readiness_level"], {})
        row["social_readiness_label"] = alignment.get("social_readiness_label", "")
        row["social_condition"] = alignment.get("social_condition", "")
        row["corresponding_quantum_readiness"] = alignment.get("corresponding_quantum_readiness", "")
        row["social_readiness_score"] = alignment.get("social_readiness_score", "")
        for column in SOCIAL_AXIS_COLUMNS:
            row[column] = alignment.get(column, "")
        row["srl_qrl_relation"] = readiness_relation(row["social_readiness_level"], row["qrl_evidence_level"])

    plot_df = [row for row in rows if row["width_numeric"] is not None]
    stage_order = [
        "Resource estimation",
        "Hardware run / target",
        "Simulator + hardware check",
        "Classical simulation",
        "Theory / method",
        "Other",
    ]
    stage_rank = {stage: i for i, stage in enumerate(stage_order)}
    plot_df = sorted(
        plot_df,
        key=lambda row: (
            stage_rank.get(row["validation_stage"], 99),
            -float(row["width_numeric"]),
            row["paper_id"],
        ),
    )

    colors = {
        "Resource estimation": "#A63D57",
        "Hardware run / target": "#D17433",
        "Simulator + hardware check": "#6B63A6",
        "Classical simulation": "#2B7A6B",
        "Theory / method": "#566775",
        "Other": "#8E8E8E",
    }
    stage_labels = {
        "Resource estimation": "QRL4\nResource\nestimate",
        "Hardware run / target": "QRL3\nHardware\nrun/target",
        "Simulator + hardware check": "QRL3\nHardware-\naware sim.",
        "Classical simulation": "QRL2\nClassical\nsimulator",
        "Theory / method": "QRL1\nTheory /\nmethod",
        "Other": "Other",
    }

    fig_h = max(7.8, 0.50 * len(plot_df) + 1.9)
    fig, (stage_ax, label_ax, ax) = plt.subplots(
        ncols=3,
        figsize=(16.2, fig_h),
        dpi=180,
        gridspec_kw={"width_ratios": [0.13, 0.12, 0.75], "wspace": 0.001},
    )
    fig.patch.set_facecolor("#F7F4EE")
    stage_ax.set_facecolor("#F7F4EE")
    label_ax.set_facecolor("#F7F4EE")
    ax.set_facecolor("#F7F4EE")

    y_positions = list(range(len(plot_df)))
    widths = [float(row["width_numeric"]) for row in plot_df]
    bar_colors = [colors.get(row["validation_stage"], "#9A9A9A") for row in plot_df]
    ax.barh(y_positions, widths, color=bar_colors, height=0.66)

    present_stages = [stage for stage in stage_order if stage in {row["validation_stage"] for row in plot_df}]
    for stage in present_stages:
        stage_indices = [i for i, row in enumerate(plot_df) if row["validation_stage"] == stage]
        y0 = min(stage_indices) - 0.42
        y1 = max(stage_indices) + 0.42
        y_mid = (y0 + y1) / 2
        stage_ax.axhspan(y0, y1, color=colors[stage], alpha=0.18, linewidth=0)
        label_ax.axhspan(y0, y1, color=colors[stage], alpha=0.035, linewidth=0)
        ax.axhspan(y0, y1, color=colors[stage], alpha=0.045, linewidth=0)
        if y0 > -0.42:
            ax.axhline(y0, color="#C9C1B7", linewidth=0.8)
            label_ax.axhline(y0, color="#C9C1B7", linewidth=0.8)
            stage_ax.axhline(y0, color="#C9C1B7", linewidth=0.8)
        stage_ax.text(
            0.04,
            y_mid,
            stage_labels.get(stage, stage),
            va="center",
            ha="left",
            fontsize=7.5,
            color="#202020",
            fontweight="bold",
            linespacing=1.14,
        )

    ax.set_xscale("log")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([])
    for chart_ax in (stage_ax, label_ax, ax):
        chart_ax.set_ylim(len(plot_df) - 0.38, -0.55)
    ax.set_xlabel("Width / qubits (log scale)", fontsize=11, labelpad=12)
    ax.set_title(
        "Figure 1. Circuit width by problem instance and evidence hierarchy",
        fontsize=17,
        loc="left",
        pad=18,
        fontweight="bold",
    )
    ax.set_xlim(max(1, min(widths) / 1.8), max(widths) * 2.4)
    ax.grid(axis="x", which="major", color="#D8D2C8", linewidth=0.8)
    ax.grid(axis="x", which="minor", color="#E7E1D8", linewidth=0.45, alpha=0.6)
    ax.tick_params(axis="x", labelsize=9)
    ax.tick_params(axis="y", length=0, labelleft=False)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#BDB5AA")

    stage_ax.set_xlim(0, 1)
    stage_ax.set_xticks([])
    stage_ax.set_yticks(y_positions)
    stage_ax.tick_params(axis="y", left=False, labelleft=False)
    for spine in ["top", "right", "left", "bottom"]:
        stage_ax.spines[spine].set_visible(False)
    stage_ax.set_title(
        "Evidence\nhierarchy",
        fontsize=9,
        loc="left",
        pad=18,
        fontweight="bold",
        color="#202020",
    )

    label_ax.set_xlim(0, 1)
    label_ax.set_xticks([])
    label_ax.set_yticks(y_positions)
    label_ax.tick_params(axis="y", left=False, labelleft=False)
    for spine in ["top", "right", "left", "bottom"]:
        label_ax.spines[spine].set_visible(False)
    label_ax.set_title(
        "Instance /\nencoding",
        fontsize=9,
        loc="left",
        pad=18,
        fontweight="bold",
        color="#202020",
    )
    for y, row in zip(y_positions, plot_df):
        label_ax.text(
            0.0,
            y,
            axis_instance_label(row),
            va="center",
            ha="left",
            fontsize=6.35,
            color="#232323",
            linespacing=1.12,
        )

    for y, width in zip(y_positions, widths):
        ax.text(width * 1.06, y, f"{int(width):,}", va="center", fontsize=8.0, color="#303030")

    fig.text(
        0.59,
        0.025,
        "Width/qubits definition: circuit width is the number of qubits required to encode the reported problem instance. Only extractable numeric qubit counts are plotted.",
        fontsize=8.7,
        color="#333333",
        ha="center",
    )

    fig.subplots_adjust(left=0.025, right=0.985, top=0.925, bottom=0.11, wspace=0.001)
    canonical_path = FIG / "figure_1_width_by_instance.png"
    fig.savefig(canonical_path, facecolor=fig.get_facecolor(), bbox_inches="tight")

    out_csv = FIG / "figure_1_presentation_plot_data.csv"
    csv_columns = [
        "paper_id",
        "problem",
        "problem_description",
        "instance_or_scope",
        "formulation_or_encoding",
        "width_numeric",
        "validation_stage",
        "validation_stage_description",
        "qrl_evidence_level",
        "social_readiness_level",
        "social_readiness_label",
        "social_condition",
        "corresponding_quantum_readiness",
        "social_readiness_score",
        "problem_readiness",
        "problem_readiness_score",
        "data_workflow_readiness",
        "data_workflow_readiness_score",
        "constraint_readiness",
        "constraint_readiness_score",
        "resource_readiness",
        "social_resource_readiness_score",
        "technology_readiness",
        "social_technology_readiness_score",
        "social_score_rule",
        "srl_qrl_relation",
        "srl_assignment_basis",
        "srl_assignment_confidence",
        "source_location",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows({column: row[column] for column in csv_columns} for row in plot_df)
    print(canonical_path)
    print(out_csv)


if __name__ == "__main__":
    main()
