from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
EV_XLSX = ROOT / "data" / "raw" / "iea" / "332_20260704_v02_ev_data_explorer_2026_existing_raw.xlsx"
FIGURE1_CSV = ROOT / "figures" / "01_quantum_vrp_evidence" / "figure_1_presentation_plot_data.csv"
OUT_DIR = ROOT / "outputs" / "scale_gap"
FIG_DIR = ROOT / "figures" / "07_scale_gap_archive"

EV_EXTRACTED_CSV = OUT_DIR / "ev_social_scale_extracted.csv"
QUANTUM_EXTRACTED_CSV = OUT_DIR / "quantum_benchmark_scale_extracted.csv"
INDEX_CSV = OUT_DIR / "social_quantum_scale_index.csv"
GRAPH_DESIGN_CSV = OUT_DIR / "scale_gap_graph_design.csv"
PLOT_PNG = FIG_DIR / "social_quantum_scale_gap_index.png"
GROWTH_CSV = OUT_DIR / "scale_gap_cagr_summary.csv"
GROWTH_PNG = FIG_DIR / "social_quantum_scale_gap_cagr.png"

BASE_YEAR = 2020
EV_REGIONS = ["World", "Japan"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def excel_col_row(ref: str) -> tuple[int, int]:
    match = re.match(r"([A-Z]+)([0-9]+)", ref)
    if match is None:
        raise ValueError(ref)
    col = 0
    for char in match.group(1):
        col = col * 26 + ord(char) - 64
    return col, int(match.group(2))


def read_ev_data_sheet() -> list[dict[str, str]]:
    ns = {
        "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    with ZipFile(EV_XLSX) as z:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", ns):
                shared_strings.append("".join(t.text or "" for t in si.findall(".//a:t", ns)))

        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        headers: list[str] = []
        rows: list[dict[str, str]] = []
        for row_node in root.findall(".//a:sheetData/a:row", ns):
            row_num = int(row_node.attrib["r"])
            values: dict[int, str] = {}
            for cell in row_node.findall("a:c", ns):
                ref = cell.attrib.get("r", "")
                if not ref:
                    continue
                col, _ = excel_col_row(ref)
                value_node = cell.find("a:v", ns)
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                values[col] = value
            if row_num == 1:
                headers = [values.get(i, "") for i in range(1, max(values) + 1)]
                continue
            rows.append({headers[i - 1]: values.get(i, "") for i in range(1, len(headers) + 1)})
    return rows


def extract_ev_social_scale() -> list[dict[str, object]]:
    rows = []
    for row in read_ev_data_sheet():
        if row.get("parameter") != "EV stock":
            continue
        if row.get("category") != "Historical":
            continue
        if row.get("mode") != "Cars":
            continue
        if row.get("powertrain") != "EV":
            continue
        if row.get("region_country") not in EV_REGIONS:
            continue
        year = int(float(row["year"]))
        if year < BASE_YEAR:
            continue
        rows.append(
            {
                "region_country": row["region_country"],
                "year": year,
                "social_scale_metric": "EV stock",
                "mode": row["mode"],
                "powertrain": row["powertrain"],
                "unit": row["unit"],
                "value": float(row["value"]),
                "source_file": str(EV_XLSX.relative_to(ROOT)),
                "use_rule": "EV stock is a social-scale context indicator and is not converted into VRP vehicles or qubits.",
            }
        )
    rows.sort(key=lambda r: (str(r["region_country"]), int(r["year"])))
    return rows


def first_number(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return int(match.group(1).replace(",", "")) if match else None


def extract_quantum_scale() -> list[dict[str, object]]:
    out = []
    for row in read_csv(FIGURE1_CSV):
        scope = row["instance_or_scope"]
        year = first_number(r"(20[0-9]{2})", row["paper_id"])
        nodes = first_number(r"([0-9,]+)-node", scope)
        locations = first_number(r"([0-9,]+)-location", scope)
        cities = first_number(r"([0-9,]+) cities", scope)
        customers = first_number(r"([0-9,]+) customers", scope)
        vehicles = first_number(r"([0-9,]+)-vehicle", scope) or first_number(r"([0-9,]+) vehicles", scope)
        trucks = first_number(r"([0-9,]+) trucks?", scope)
        route_candidates = first_number(r"([0-9,]+)-route candidate", scope)
        capacity = first_number(r"capacity ([0-9,]+)", scope)
        problem_entities = customers or nodes or locations or cities
        if customers:
            scale_type = "customers"
        elif nodes:
            scale_type = "nodes"
        elif locations:
            scale_type = "locations"
        elif cities:
            scale_type = "cities"
        elif route_candidates:
            scale_type = "route_candidates_only"
        else:
            scale_type = "not_extracted"
        out.append(
            {
                "paper_id": row["paper_id"],
                "year": year or "",
                "problem": row["problem"],
                "instance_or_scope": scope,
                "validation_stage": row["validation_stage"],
                "width_qubits": row["width_numeric"],
                "reported_problem_entities": problem_entities or "",
                "problem_entities_type": scale_type,
                "reported_vehicles_or_trucks": vehicles or trucks or "",
                "reported_route_candidates": route_candidates or "",
                "reported_capacity": capacity or "",
                "included_in_scale_index": "no" if row["validation_stage"] == "Resource estimation" else "yes",
                "scale_extraction_method": "regex_from_instance_or_scope",
                "scale_extraction_note": (
                    "Nodes, locations, cities, customers, vehicles, trucks, and route candidates are reported separately; "
                    "they are not treated as identical units. Resource-estimation rows are excluded from the scale index."
                ),
            }
        )
    out.sort(key=lambda r: (int(r["year"]) if r["year"] else 9999, str(r["paper_id"]), str(r["instance_or_scope"])))
    return out


def cumulative_max_by_year(values_by_year: dict[int, list[float]]) -> dict[int, float]:
    out = {}
    current = None
    for year in sorted(values_by_year):
        year_max = max(values_by_year[year])
        current = year_max if current is None else max(current, year_max)
        out[year] = current
    return out


def build_index_rows(ev_rows: list[dict[str, object]], quantum_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ev_by_region_year: dict[str, dict[int, float]] = defaultdict(dict)
    for row in ev_rows:
        ev_by_region_year[str(row["region_country"])][int(row["year"])] = float(row["value"])

    entities_by_year: dict[int, list[float]] = defaultdict(list)
    width_by_year: dict[int, list[float]] = defaultdict(list)
    route_candidates_by_year: dict[int, list[float]] = defaultdict(list)
    for row in quantum_rows:
        if row.get("included_in_scale_index") != "yes":
            continue
        if not row["year"]:
            continue
        year = int(row["year"])
        if row["reported_problem_entities"]:
            entities_by_year[year].append(float(row["reported_problem_entities"]))
        if row["width_qubits"]:
            width_by_year[year].append(float(row["width_qubits"]))
        if row["reported_route_candidates"]:
            route_candidates_by_year[year].append(float(row["reported_route_candidates"]))

    cum_entities = cumulative_max_by_year(entities_by_year)
    cum_width = cumulative_max_by_year(width_by_year)
    cum_routes = cumulative_max_by_year(route_candidates_by_year)
    years = sorted(set().union(*[set(v.keys()) for v in ev_by_region_year.values()], cum_entities.keys(), cum_width.keys()))
    base_entities = cum_entities.get(BASE_YEAR)
    base_width = cum_width.get(BASE_YEAR)
    base_routes = cum_routes.get(BASE_YEAR)
    rows: list[dict[str, object]] = []
    current_entities = None
    current_width = None
    current_routes = None
    for year in years:
        if year < BASE_YEAR:
            continue
        if year in cum_entities:
            current_entities = cum_entities[year]
        if year in cum_width:
            current_width = cum_width[year]
        if year in cum_routes:
            current_routes = cum_routes[year]
        row: dict[str, object] = {
            "year": year,
            "base_year": BASE_YEAR,
            "quantum_cumulative_max_problem_entities": current_entities or "",
            "quantum_benchmark_scale_index": (
                round(current_entities / base_entities * 100, 2) if base_entities and current_entities else ""
            ),
            "quantum_cumulative_max_width_qubits": current_width or "",
            "quantum_width_index": round(current_width / base_width * 100, 2) if base_width and current_width else "",
            "quantum_cumulative_max_route_candidates": current_routes or "",
            "quantum_route_candidate_index": round(current_routes / base_routes * 100, 2) if base_routes and current_routes else "",
            "interpretation_rule": "Indices compare growth patterns only; EV stock is not converted into VRP vehicles or qubits.",
        }
        for region in EV_REGIONS:
            base_ev = ev_by_region_year[region].get(BASE_YEAR)
            value = ev_by_region_year[region].get(year)
            row[f"{region.lower()}_ev_stock"] = value if value is not None else ""
            row[f"{region.lower()}_social_scale_index"] = round(value / base_ev * 100, 2) if value and base_ev else ""
        rows.append(row)
    return rows


def write_graph_design() -> None:
    rows = [
        {
            "graph_element": "title",
            "design_choice": "Scale Gap Between EV Adoption and Evaluated Quantum VRP Benchmarks",
            "reason": "Focuses only on scale gap for evaluated or hardware-aware benchmarks; resource-estimation rows are excluded.",
        },
        {
            "graph_element": "x_axis",
            "design_choice": "Year",
            "reason": "Shows annual change in social-scale indicators and quantum benchmark scale.",
        },
        {
            "graph_element": "y_axis",
            "design_choice": f"Index, {BASE_YEAR}=100; log scale",
            "reason": "Avoids mixing units directly while making order-of-magnitude gaps visible.",
        },
        {
            "graph_element": "social_series",
            "design_choice": "World EV stock index and Japan EV stock index",
            "reason": "EV stock is used as social-scale context.",
        },
        {
            "graph_element": "quantum_series",
            "design_choice": "Cumulative max problem entities index only",
            "reason": "Problem entities show evaluated benchmark scale; circuit width and resource-estimation rows are excluded.",
        },
        {
            "graph_element": "required_note",
            "design_choice": "EV stock is not converted into VRP vehicles or qubits; resource-estimation benchmarks are excluded from the plotted quantum scale index.",
            "reason": "Prevents a false direct mapping and avoids presenting resource estimates as evaluated problem handling.",
        },
    ]
    write_csv(GRAPH_DESIGN_CSV, rows, ["graph_element", "design_choice", "reason"])


def plot_index(rows: list[dict[str, object]]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12.5, 7.2), dpi=220)
    fig.patch.set_facecolor("#F7F7F2")
    ax.set_facecolor("#F7F7F2")

    def series(column: str) -> tuple[list[int], list[float]]:
        xs, ys = [], []
        for row in rows:
            value = row.get(column, "")
            if value == "":
                continue
            xs.append(int(row["year"]))
            ys.append(float(value))
        return xs, ys

    plot_specs = [
        ("world_social_scale_index", "World EV stock index", "#2E7D73", "-"),
        ("japan_social_scale_index", "Japan EV stock index", "#79A66E", "-"),
        ("quantum_benchmark_scale_index", "Quantum benchmark problem-size index", "#B84A62", "--"),
    ]
    for column, label, color, linestyle in plot_specs:
        xs, ys = series(column)
        if xs:
            ax.plot(xs, ys, label=label, color=color, linewidth=2.6, linestyle=linestyle, marker="o", markersize=4.5)

    ax.set_title("Scale Gap Between EV Adoption and Evaluated Quantum VRP Benchmarks", loc="left", fontsize=17, weight="bold", pad=18)
    ax.set_ylabel(f"Index ({BASE_YEAR}=100, log scale)")
    ax.set_xlabel("Year")
    ax.set_yscale("log")
    ax.grid(True, which="major", axis="y", color="#D8D4C8", linewidth=0.9)
    ax.grid(True, which="minor", axis="y", color="#E8E4DA", linewidth=0.55)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=9.5)
    ax.text(
        0.0,
        -0.18,
        "Note: EV stock is a social-scale context indicator and is not converted into VRP vehicles or qubits. "
        "Quantum benchmark problem size uses cumulative maximum reported nodes/customers/locations/cities from evaluated or hardware-aware studies. "
        "Resource-estimation benchmarks, route candidates, and circuit width are kept separate in the CSV.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color="#4A535A",
        wrap=True,
    )
    fig.tight_layout()
    fig.savefig(PLOT_PNG, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def cagr(start_value: float, end_value: float, years: int) -> float:
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1 / years) - 1


def build_cagr_rows(index_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    start = next(row for row in index_rows if int(row["year"]) == BASE_YEAR)
    end = max(index_rows, key=lambda row: int(row["year"]))
    years = int(end["year"]) - int(start["year"])
    rows = [
        {
            "series": "World EV stock",
            "scale_type": "social EV stock",
            "start_year": start["year"],
            "end_year": end["year"],
            "start_value": start["world_ev_stock"],
            "end_value": end["world_ev_stock"],
            "cagr": cagr(float(start["world_ev_stock"]), float(end["world_ev_stock"]), years),
            "interpretation": "Social-scale EV stock expanded rapidly.",
        },
        {
            "series": "Japan EV stock",
            "scale_type": "social EV stock",
            "start_year": start["year"],
            "end_year": end["year"],
            "start_value": start["japan_ev_stock"],
            "end_value": end["japan_ev_stock"],
            "cagr": cagr(float(start["japan_ev_stock"]), float(end["japan_ev_stock"]), years),
            "interpretation": "Japan EV stock increased, but from a smaller base and more slowly than global EV stock.",
        },
        {
            "series": "Evaluated quantum benchmark problem size",
            "scale_type": "reported nodes/customers/locations/cities",
            "start_year": start["year"],
            "end_year": end["year"],
            "start_value": start["quantum_cumulative_max_problem_entities"],
            "end_value": end["quantum_cumulative_max_problem_entities"],
            "cagr": cagr(
                float(start["quantum_cumulative_max_problem_entities"]),
                float(end["quantum_cumulative_max_problem_entities"]),
                years,
            ),
            "interpretation": "Evaluated quantum VRP benchmark size stayed nearly flat after excluding resource-estimation-only benchmarks.",
        },
    ]
    for row in rows:
        row["cagr_percent"] = round(float(row["cagr"]) * 100, 2)
        row["note"] = (
            "CAGR compares growth rates only. EV stock and benchmark problem size are different quantities; "
            "resource-estimation-only benchmarks are excluded from the quantum benchmark series."
        )
    return rows


def plot_cagr(rows: list[dict[str, object]]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10.8, 6.6), dpi=220)
    fig.patch.set_facecolor("#F7F7F2")
    ax.set_facecolor("#F7F7F2")

    labels = [str(row["series"]) for row in rows]
    values = [float(row["cagr_percent"]) for row in rows]
    colors = ["#2E7D73", "#79A66E", "#B84A62"]
    bars = ax.barh(labels, values, color=colors, height=0.58)
    ax.invert_yaxis()

    max_value = max(values) if values else 1
    ax.set_xlim(0, max_value * 1.28)
    ax.set_xlabel("CAGR, 2020-2025 (%)")
    ax.set_title("Scale-Gap Growth Rates: EV Stock vs Evaluated Quantum VRP Benchmarks", loc="left", fontsize=15, weight="bold", pad=16)
    ax.grid(True, axis="x", color="#D8D4C8", linewidth=0.9)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    for bar, value in zip(bars, values):
        ax.text(
            value + max_value * 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            ha="left",
            fontsize=10.5,
            color="#263238",
            weight="bold",
        )

    ax.text(
        0,
        -0.19,
        "Note: CAGR compares growth rates only. EV stock and evaluated benchmark problem size are different quantities. "
        "Resource-estimation-only benchmarks are excluded from the quantum benchmark series.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.7,
        color="#4A535A",
        wrap=True,
    )
    fig.tight_layout()
    fig.savefig(GROWTH_PNG, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    ev_rows = extract_ev_social_scale()
    quantum_rows = extract_quantum_scale()
    index_rows = build_index_rows(ev_rows, quantum_rows)
    write_csv(
        EV_EXTRACTED_CSV,
        ev_rows,
        ["region_country", "year", "social_scale_metric", "mode", "powertrain", "unit", "value", "source_file", "use_rule"],
    )
    write_csv(
        QUANTUM_EXTRACTED_CSV,
        quantum_rows,
        [
            "paper_id",
            "year",
            "problem",
            "instance_or_scope",
            "validation_stage",
            "width_qubits",
            "reported_problem_entities",
            "problem_entities_type",
            "reported_vehicles_or_trucks",
            "reported_route_candidates",
            "reported_capacity",
            "included_in_scale_index",
            "scale_extraction_method",
            "scale_extraction_note",
        ],
    )
    write_csv(
        INDEX_CSV,
        index_rows,
        [
            "year",
            "base_year",
            "world_ev_stock",
            "world_social_scale_index",
            "japan_ev_stock",
            "japan_social_scale_index",
            "quantum_cumulative_max_problem_entities",
            "quantum_benchmark_scale_index",
            "quantum_cumulative_max_width_qubits",
            "quantum_width_index",
            "quantum_cumulative_max_route_candidates",
            "quantum_route_candidate_index",
            "interpretation_rule",
        ],
    )
    write_graph_design()
    plot_index(index_rows)
    cagr_rows = build_cagr_rows(index_rows)
    write_csv(
        GROWTH_CSV,
        cagr_rows,
        [
            "series",
            "scale_type",
            "start_year",
            "end_year",
            "start_value",
            "end_value",
            "cagr",
            "cagr_percent",
            "interpretation",
            "note",
        ],
    )
    plot_cagr(cagr_rows)
    for path in [EV_EXTRACTED_CSV, QUANTUM_EXTRACTED_CSV, INDEX_CSV, GRAPH_DESIGN_CSV, GROWTH_CSV, PLOT_PNG, GROWTH_PNG]:
        print(path)


if __name__ == "__main__":
    main()
