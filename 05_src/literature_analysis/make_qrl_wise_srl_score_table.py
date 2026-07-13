from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "figures" / "01_quantum_vrp_evidence" / "figure_1_presentation_plot_data.csv"
ROW_CSV = ROOT / "outputs" / "stage_layer_table_d" / "srl_qrl_placement_from_figure_1_data.csv"
SUMMARY_CSV = ROOT / "outputs" / "stage_layer_table_d" / "qrl_wise_srl_score_summary.csv"
SUMMARY_MD = ROOT / "outputs" / "stage_layer_table_d" / "qrl_wise_srl_score_summary.md"
OLD_PNG = ROOT / "figures" / "02_requirement_mapping" / "figure_1_srl_qrl_matrix.png"


def read_rows() -> list[dict[str, str]]:
    with INPUT.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def level_num(value: str, prefix: str) -> int | None:
    value = str(value)
    if value.startswith(prefix):
        try:
            return int(value.replace(prefix, "").split()[0])
        except ValueError:
            return None
    return None


def evidence_summary(qrl: str) -> str:
    return {
        "QRL2": "HVRP instances with 3-4 cities and 1-2 trucks; VRPTW candidate sets with 128 and 3964 routes.",
        "QRL3": "VRP instances with 3-5 nodes/locations; CVRP-derived TSP subproblems with 4-6 nodes; VRPTW candidate sets with 11 and 16 routes.",
        "QRL4": "Golden_5 CVRP benchmark instance with 200 customers, 5 vehicles, and capacity 900.",
    }.get(qrl, "No Figure 1 evidence assigned.")


def interpretation(qrl: str) -> str:
    return {
        "QRL2": "Simulation evidence contains constrained routing, but does not show hardware-aware workflow.",
        "QRL3": "Hardware-aware evidence exists, but the represented problem instances remain small or decomposed.",
        "QRL4": "Golden_5 raises the SRL score through benchmark-scale CVRP resource pressure, not through deployment or utility evidence.",
    }.get(qrl, "")


def prepare_row_csv(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    qrl_scores: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.get("qrl_evidence_level") and row.get("social_readiness_score"):
            qrl_scores[row["qrl_evidence_level"]].append(float(row["social_readiness_score"]))

    out_rows: list[dict[str, str]] = []
    for row in rows:
        qrl = row.get("qrl_evidence_level", "")
        srl = row.get("social_readiness_level", "")
        qrl_num = level_num(qrl, "QRL")
        srl_num = level_num(srl, "SRL")
        if qrl_num is None or srl_num is None:
            continue
        scores = qrl_scores[qrl]
        out = dict(row)
        out["matrix_x_qrl"] = str(qrl_num)
        out["matrix_y_srl"] = str(srl_num)
        out["cell_srl_score"] = row.get("social_readiness_score", "")
        out["qrl_mean_srl_score"] = f"{sum(scores) / len(scores):.1f}" if scores else ""
        out["qrl_row_count"] = str(len(scores))
        out["srl_assignment_explanation"] = row.get("srl_assignment_basis", "")
        out_rows.append(out)
    return out_rows


def write_row_csv(rows: list[dict[str, str]]) -> None:
    ROW_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "paper_id",
        "problem",
        "instance_or_scope",
        "formulation_or_encoding",
        "width_numeric",
        "validation_stage",
        "qrl_evidence_level",
        "social_readiness_level",
        "social_readiness_label",
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
        "matrix_x_qrl",
        "matrix_y_srl",
        "cell_srl_score",
        "qrl_mean_srl_score",
        "qrl_row_count",
        "srl_assignment_basis",
        "srl_assignment_explanation",
    ]
    with ROW_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def summarize(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["qrl_evidence_level"]].append(row)

    summary_rows: list[dict[str, str]] = []
    for qrl in ["QRL2", "QRL3", "QRL4"]:
        items = grouped.get(qrl, [])
        if not items:
            continue
        scores = [float(row["social_readiness_score"]) for row in items]
        widths = sorted(int(float(row["width_numeric"])) for row in items)
        srl_counts = Counter(row["social_readiness_level"] for row in items)
        stages = Counter(row["validation_stage"] for row in items)
        summary_rows.append(
            {
                "qrl_evidence_level": qrl,
                "qrl_mean_srl_score": f"{sum(scores) / len(scores):.1f}",
                "evidence_rows": str(len(items)),
                "srl_composition": "; ".join(f"{key}: {value}" for key, value in sorted(srl_counts.items())),
                "width_range_qubits": f"{widths[0]:,}-{widths[-1]:,}",
                "validation_stage": "; ".join(f"{key}: {value}" for key, value in stages.items()),
                "problem_instance_summary": evidence_summary(qrl),
                "interpretation": interpretation(qrl),
            }
        )
    return summary_rows


def write_summary_csv(rows: list[dict[str, str]]) -> None:
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "qrl_evidence_level",
        "qrl_mean_srl_score",
        "evidence_rows",
        "srl_composition",
        "width_range_qubits",
        "validation_stage",
        "problem_instance_summary",
        "interpretation",
    ]
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_md(rows: list[dict[str, str]]) -> None:
    lines = [
        "# QRL-wise SRL Score Summary Table",
        "",
        "This table replaces the former QRL-wise SRL score figure because the number of QRL groups is small.",
        "Scores summarize the social-readiness context assigned to Figure 1 evidence rows; they are not deployment, utility, or quantum-performance scores.",
        "",
        "| QRL evidence level | Mean SRL score | Evidence rows | Problem-instance summary | Width range (qubits) | Interpretation |",
        "| --- | ---: | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {qrl_evidence_level} | {qrl_mean_srl_score}/3 | {evidence_rows} | {problem_instance_summary} | {width_range_qubits} | {interpretation} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## What the summary says",
            "",
            "| 言えること | 意味 |",
            "| --- | --- |",
            "| QRLが上がっても、社会側readinessが自動的に上がるわけではない | QRL3はhardware-aware evidenceを含むが、平均SRL scoreは `0.6/3` と低い。つまり、量子側で実機・実機想定に近づいても、扱っている問題は3-5 node/location VRP、小規模CVRP由来TSP、11-16 route程度のVRPTW候補集合が中心で、社会側の問題条件はまだ浅い。 |",
            "| 既存研究の多くは「量子側の検証」は進んでいても、「社会側の問題文脈」は浅い | QRL3に12行あるが、EV運用、SOC、充電ステーション選択、充電時間、depot/grid制約、動的再最適化を直接含む問題インスタンスではない。そのため、hardware-aware evidenceがあることと、EV/logistics実運用に近いことは区別して読む必要がある。 |",
            "| QRL4は高いSRL scoreを示すが、それは実用実証ではなくresource estimateによるもの | QRL4は `2.2/3` だが、これはGolden_5 CVRP benchmarkの資源推定に基づく。Golden_5はOnah and Michielsen (2025)のCVRP quantum utility/resource-estimation文脈で使われるベンチマークで、200 customers、5 vehicles、capacity 900のCVRPを対象に、HOBO/direct encodingでは7,685 qubits・depth 38,425、QUBOでは202,505 qubitsが報告されている。したがって、これは大きめのCVRPを量子回路へ写した場合の資源要求を示す証拠であり、hardware execution、deployment、utility evidenceではない。 |",
            "| simulation段階でも制約付きroutingは扱われている | QRL2は `1.2/3` で、HVRPやVRPTW候補集合を含む。つまり、社会側制約を含む問題設定はsimulation段階には存在する。ただし、規模は小さく、EV chargingやdynamic dispatchを含む実運用条件までは示していない。 |",
            "| EV/logistics側のSRL3-SRL4要求と、量子側の既存証拠にはギャップがある | EV側をSRLとして加えているのは、EV routingではSOC、充電ステーション選択、充電時間、depot charging、grid/depot capacity、需要変動、再最適化頻度が、単なる背景情報ではなく routing problem の制約・運用条件そのものになるためである。ただし、これらのEV統合条件は、Figure 1の根拠としてまとめたCSV内には直接含まれない。 |",
            "",
            "## EV-side SRL rule",
            "",
            "| 観点 | SRLとして扱う理由 | 行別スコアへの扱い |",
            "| --- | --- | --- |",
            "| EV charging and SOC | 充電残量、充電場所、充電時間がroute feasibilityを変えるため、EV routingでは社会側の実問題条件になる。 | 文献の問題インスタンスに直接含まれる場合のみSRL3以上の根拠にする。 |",
            "| Depot and grid constraints | depot charging capacityやgrid/depot制約は、車両経路だけでなく運用可能性を制約する。 | Figure 1の根拠CSVに直接現れない場合は、背景・目標SRLの説明にとどめる。 |",
            "| Dynamic dispatch and reoptimization | 需要、交通、充電混雑が変動すると、static VRPより強いworkflow/runtime要求が生じる。 | 動的再最適化が文献の評価対象でない限り、行別SRLを上げる根拠にはしない。 |",
            "",
            "Use rule: social baseline indicators such as World Bank LPI and EV infrastructure indicators are used for context and target-SRL interpretation, not to raise row-level SRL scores.",
            "",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = read_rows()
    row_csv_rows = prepare_row_csv(rows)
    write_row_csv(row_csv_rows)
    summary_rows = summarize(row_csv_rows)
    write_summary_csv(summary_rows)
    write_summary_md(summary_rows)
    if OLD_PNG.exists():
        OLD_PNG.unlink()
    print(ROW_CSV)
    print(SUMMARY_CSV)
    print(SUMMARY_MD)


if __name__ == "__main__":
    main()
