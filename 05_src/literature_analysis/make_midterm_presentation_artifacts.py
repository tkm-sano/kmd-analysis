from __future__ import annotations

import csv
import textwrap
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "use_case_scenario"
FIG_DIR = ROOT / "figures" / "02_requirement_mapping"

EVRP_REQUIREMENT_CSV = OUT_DIR / "evrp_benchmark_requirement_table.csv"
EVRP_REQUIREMENT_MD = OUT_DIR / "evrp_benchmark_requirement_table.md"
EVRP_REQUIREMENT_PNG = FIG_DIR / "evrp_benchmark_requirement_table.png"

REQUIREMENT_MAP_CSV = OUT_DIR / "943_20260705_v03_tokyo_evrp_quantum_requirement_map.csv"
REQUIREMENT_MAP_PRESENTATION_CSV = OUT_DIR / "945_20260705_v03_tokyo_evrp_quantum_requirement_map_presentation.csv"
REQUIREMENT_MAP_PRESENTATION_MD = OUT_DIR / "tokyo_evrp_quantum_requirement_map_presentation.md"
REQUIREMENT_MAP_PRESENTATION_PNG = FIG_DIR / "tokyo_evrp_quantum_requirement_map_table.png"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def write_md(path: Path, title: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
    lines = [f"# {title}", "", "| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def metric_range(metric_rows: list[dict[str, str]], metric: str) -> str:
    for row in metric_rows:
        if row["metric"] == metric:
            return f"{row['min']}-{row['max']} (mean {row['mean']})"
    return "not available"


def evrp_requirement_rows() -> list[dict[str, str]]:
    summary = read_csv(OUT_DIR / "evrp_benchmark_instance_summary.csv")
    return [
        {
            "requirement": "Customers / demand nodes",
            "benchmark evidence": f"Parsed E-CVRP and E-VRPTW instances: customers {metric_range(summary, 'customers_by_dimension')}.",
            "design rule": "Create synthetic Tokyo customer nodes; do not treat population, GTFS stops, or EV stock as observed delivery customers.",
            "why it matters": "Defines delivery demand size and service-location count.",
        },
        {
            "requirement": "Vehicles / fleet size",
            "benchmark evidence": f"E-CVRP declares vehicles {metric_range(summary, 'vehicles')}; E-VRPTW files do not declare vehicle count.",
            "design rule": "Set fleet size as a scenario parameter or benchmark value; do not convert national EV stock into fleet size.",
            "why it matters": "Defines route count, capacity allocation, and fleet coordination.",
        },
        {
            "requirement": "Charging stations",
            "benchmark evidence": f"Parsed benchmarks include charging stations {metric_range(summary, 'charging_stations_declared')}.",
            "design rule": "Use geocoded chargers as candidate stations and report coverage limits.",
            "why it matters": "Adds station choice and recharge feasibility, separating EVRP from generic VRP.",
        },
        {
            "requirement": "Vehicle / cargo capacity",
            "benchmark evidence": f"Parsed benchmarks include cargo capacity {metric_range(summary, 'vehicle_capacity')}.",
            "design rule": "Use benchmark values or vehicle-spec assumptions; public Tokyo data do not provide operator payload distributions.",
            "why it matters": "Determines load feasibility and CVRP-style constraints.",
        },
        {
            "requirement": "Battery / energy capacity",
            "benchmark evidence": f"Parsed benchmarks include energy capacity {metric_range(summary, 'energy_capacity')}.",
            "design rule": "Set battery/SOC parameters from benchmark convention or vehicle assumptions.",
            "why it matters": "Defines range feasibility and recharge need.",
        },
        {
            "requirement": "Energy consumption",
            "benchmark evidence": "Parsed E-CVRP and E-VRPTW files include energy/fuel consumption fields.",
            "design rule": "Define a distance-to-energy model when translating Tokyo road distances into EVRP instances.",
            "why it matters": "Links route distance to battery depletion.",
        },
        {
            "requirement": "Depot",
            "benchmark evidence": "Parsed benchmark instances contain one depot.",
            "design rule": "Use a synthetic depot or separately sourced logistics-facility data.",
            "why it matters": "Defines vehicle start/end and route feasibility.",
        },
        {
            "requirement": "Distance / travel cost",
            "benchmark evidence": "Benchmarks provide synthetic coordinates and Euclidean-distance assumptions.",
            "design rule": "Build a Tokyo distance or travel-cost matrix from OSM; keep GTFS separate as mobility-data readiness evidence.",
            "why it matters": "Defines the routing objective and feasibility cost.",
        },
        {
            "requirement": "Time windows",
            "benchmark evidence": "Parsed 92 Schneider/Goeke E-VRPTW files with ReadyTime, DueDate, and ServiceTime.",
            "design rule": "Use E-VRPTW as the field template; Tokyo-specific delivery windows remain scenario assumptions unless operator data are obtained.",
            "why it matters": "Represents service promises, delivery timing, and operational feasibility.",
        },
        {
            "requirement": "Validation / feasibility",
            "benchmark evidence": "Benchmarks define constraint fields, but feasibility must be checked by the solution/evaluation method.",
            "design rule": "Report constraint coverage and feasible-route evidence, not only circuit width or depth.",
            "why it matters": "Shows whether routes satisfy EVRP constraints.",
        },
    ]


def requirement_map_presentation_rows() -> list[dict[str, str]]:
    rows = read_csv(REQUIREMENT_MAP_CSV)
    out: list[dict[str, str]] = []
    for row in rows:
        out.append(
            {
                "EVRP requirement": row["evrp_requirement"],
                "benchmark basis": row["evrp_benchmark_evidence"],
                "Tokyo data status": row["tokyo_subcase_status"],
                "current quantum-evidence gap": row["quantum_gap"],
                "use in this study": row["benchmark_design_implication"],
            }
        )
    return out


def draw_table_png(
    rows: list[dict[str, str]],
    columns: list[str],
    title: str,
    subtitle: str,
    path: Path,
    *,
    col_widths: list[float],
    wrap_widths: list[int],
    row_height: float = 0.72,
) -> None:
    nrows = len(rows)
    fig_w = 18
    fig_h = 1.7 + row_height * (nrows + 1)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=180)
    fig.patch.set_facecolor("#F7F4EE")
    ax.set_facecolor("#F7F4EE")
    ax.axis("off")

    ax.text(0.0, 1.02, title, transform=ax.transAxes, fontsize=18, fontweight="bold", va="bottom", color="#1F2933")
    ax.text(0.0, 0.975, subtitle, transform=ax.transAxes, fontsize=9.5, va="top", color="#4B5563")

    table_top = 0.91
    table_left = 0.0
    table_width = 1.0
    total_units = sum(col_widths)
    xs = [table_left]
    for width in col_widths:
        xs.append(xs[-1] + table_width * width / total_units)

    header_h = 0.06
    body_h = table_top - 0.02 - header_h
    row_h = body_h / nrows

    header_color = "#243B53"
    alt_colors = ["#FFFFFF", "#F0ECE4"]
    grid_color = "#D2CCC2"

    for idx, column in enumerate(columns):
        x0 = xs[idx]
        w = xs[idx + 1] - xs[idx]
        ax.add_patch(Rectangle((x0, table_top - header_h), w, header_h, transform=ax.transAxes, facecolor=header_color, edgecolor=grid_color, linewidth=0.8))
        ax.text(x0 + 0.006, table_top - header_h / 2, column, transform=ax.transAxes, color="white", fontsize=8.6, fontweight="bold", va="center", ha="left")

    for r_idx, row in enumerate(rows):
        y0 = table_top - header_h - (r_idx + 1) * row_h
        face = alt_colors[r_idx % 2]
        for c_idx, column in enumerate(columns):
            x0 = xs[c_idx]
            w = xs[c_idx + 1] - xs[c_idx]
            ax.add_patch(Rectangle((x0, y0), w, row_h, transform=ax.transAxes, facecolor=face, edgecolor=grid_color, linewidth=0.55))
            text = textwrap.fill(str(row.get(column, "")), width=wrap_widths[c_idx])
            ax.text(
                x0 + 0.006,
                y0 + row_h / 2,
                text,
                transform=ax.transAxes,
                color="#1F2933",
                fontsize=7.35,
                va="center",
                ha="left",
                linespacing=1.18,
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    requirement_rows = evrp_requirement_rows()
    requirement_fields = ["requirement", "benchmark evidence", "design rule", "why it matters"]
    write_csv(EVRP_REQUIREMENT_CSV, requirement_rows, requirement_fields)
    write_md(EVRP_REQUIREMENT_MD, "EVRP Benchmark Requirement Table", requirement_rows, requirement_fields)
    draw_table_png(
        requirement_rows,
        requirement_fields,
        "EVRP Benchmark Requirement Table",
        "Requirement fields extracted from E-CVRP and Schneider/Goeke E-VRPTW benchmark instances; Tokyo-specific operational values remain scenario assumptions.",
        EVRP_REQUIREMENT_PNG,
        col_widths=[1.2, 2.4, 2.65, 1.8],
        wrap_widths=[24, 46, 52, 34],
        row_height=0.74,
    )

    map_rows = requirement_map_presentation_rows()
    map_fields = ["EVRP requirement", "benchmark basis", "Tokyo data status", "current quantum-evidence gap", "use in this study"]
    write_csv(REQUIREMENT_MAP_PRESENTATION_CSV, map_rows, map_fields)
    write_md(REQUIREMENT_MAP_PRESENTATION_MD, "Tokyo-EVRP-Quantum Requirement Map", map_rows, map_fields)
    draw_table_png(
        map_rows,
        map_fields,
        "Tokyo-EVRP-Quantum Requirement Map",
        "Bridge table connecting Tokyo public-data proxies, EVRP benchmark requirements, and the current quantum VRP evidence summarized in Figure 1.",
        REQUIREMENT_MAP_PRESENTATION_PNG,
        col_widths=[1.15, 2.25, 1.35, 2.45, 2.35],
        wrap_widths=[23, 43, 25, 48, 46],
        row_height=0.82,
    )

    for path in [
        EVRP_REQUIREMENT_CSV,
        EVRP_REQUIREMENT_MD,
        EVRP_REQUIREMENT_PNG,
        REQUIREMENT_MAP_PRESENTATION_CSV,
        REQUIREMENT_MAP_PRESENTATION_MD,
        REQUIREMENT_MAP_PRESENTATION_PNG,
    ]:
        print(path)


if __name__ == "__main__":
    main()
