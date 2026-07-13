from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "stage_layer_table_d" / "qrl_wise_srl_score_summary.csv"
OUTPUT = ROOT / "outputs" / "stage_layer_table_d" / "602_20260703_v02_quantum_social_readiness_explanatory_table.csv"


STAGE_TEXT = {
    "QRL2": {
        "quantum_evidence_stage": "Small-scale classical simulation evidence",
        "what_quantum_side_has_shown": (
            "Quantum routing algorithms were evaluated on classical simulators for small constrained-routing cases."
        ),
        "social_problem_stage": "Constrained urban or commercial routing, but still small and non-operational",
        "plain_language_interpretation": (
            "The studies include routing constraints such as heterogeneous vehicles or time-window route candidates, "
            "but they do not yet show hardware-aware execution or EV charging operations."
        ),
        "main_message": (
            "Simulation-stage work can include meaningful routing constraints, but it remains far from EV/logistics deployment."
        ),
        "important_limitation": (
            "The source CSV does not contain direct EV charging, SOC, depot/grid, or dynamic dispatch evidence for these rows."
        ),
    },
    "QRL3": {
        "quantum_evidence_stage": "Hardware-aware or hardware-targeted evidence",
        "what_quantum_side_has_shown": (
            "The studies include hardware runs, hardware-targeted transpilation, or simulator checks tied to a hardware platform."
        ),
        "social_problem_stage": "Mostly simple or small constrained routing instances",
        "plain_language_interpretation": (
            "The quantum evidence is stronger than simulation-only evidence, but the represented problems remain toy-scale, "
            "small, or decomposed routing instances."
        ),
        "main_message": (
            "Stronger quantum validation does not automatically mean stronger social or EV/logistics readiness."
        ),
        "important_limitation": (
            "Most rows are 3-5 node/location VRP, small CVRP-derived TSP subproblems, or 11-16 route VRPTW candidate sets."
        ),
    },
    "QRL4": {
        "quantum_evidence_stage": "Resource-estimation evidence for a larger CVRP benchmark",
        "what_quantum_side_has_shown": (
            "The study estimated circuit resources required for a larger CVRP benchmark, without hardware execution."
        ),
        "social_problem_stage": "Large-scale logistics pressure represented through benchmark-scale CVRP resources",
        "plain_language_interpretation": (
            "The high social-readiness score comes from the benchmark scale and resource pressure, not from actual deployment."
        ),
        "main_message": (
            "Resource estimates show how quickly practical-scale CVRP can become resource-intensive for quantum approaches."
        ),
        "important_limitation": (
            "This is not hardware execution, deployment evidence, or application-level utility evidence."
        ),
    },
}


def read_summary() -> list[dict[str, str]]:
    with INPUT.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        qrl = row["qrl_evidence_level"]
        text = STAGE_TEXT[qrl]
        out.append(
            {
                "quantum_evidence_stage": text["quantum_evidence_stage"],
                "what_quantum_side_has_shown": text["what_quantum_side_has_shown"],
                "social_problem_stage": text["social_problem_stage"],
                "mean_social_readiness_score_out_of_3": row["qrl_mean_srl_score"],
                "score_basis": (
                    "Mean of the social-readiness scores assigned to the Figure 1 source-CSV rows in this evidence stage. "
                    "Each social-readiness score is the mean of five axes: problem, data/workflow, constraints, resources, and technology."
                ),
                "evidence_rows_in_source_csv": row["evidence_rows"],
                "source_csv_problem_evidence": row["problem_instance_summary"],
                "source_csv_width_range_qubits": row["width_range_qubits"],
                "plain_language_interpretation": text["plain_language_interpretation"],
                "main_message": text["main_message"],
                "important_limitation": text["important_limitation"],
                "original_quantum_stage_code": qrl,
                "original_social_stage_composition": row["srl_composition"],
            }
        )
    return out


def write_csv(rows: list[dict[str, str]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "quantum_evidence_stage",
        "what_quantum_side_has_shown",
        "social_problem_stage",
        "mean_social_readiness_score_out_of_3",
        "score_basis",
        "evidence_rows_in_source_csv",
        "source_csv_problem_evidence",
        "source_csv_width_range_qubits",
        "plain_language_interpretation",
        "main_message",
        "important_limitation",
        "original_quantum_stage_code",
        "original_social_stage_composition",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows(read_summary())
    write_csv(rows)
    print(OUTPUT)


if __name__ == "__main__":
    main()
