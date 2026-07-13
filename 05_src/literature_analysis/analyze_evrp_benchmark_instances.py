from __future__ import annotations

import csv
import re
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "data" / "raw" / "evrp_benchmarks" / "e-cvrp_benchmark_instances"
EVRPTW_DIR = ROOT / "data" / "raw" / "evrp_benchmarks" / "e-vrptw_mendeley_schneider" / "evrptw_instances"
FIGURE1_CSV = ROOT / "figures" / "01_quantum_vrp_evidence" / "figure_1_presentation_plot_data.csv"
OUT_DIR = ROOT / "outputs" / "use_case_scenario"

INSTANCE_FIELDS_CSV = OUT_DIR / "evrp_benchmark_instance_fields.csv"
SUMMARY_CSV = OUT_DIR / "evrp_benchmark_instance_summary.csv"
QUANTUM_COMPARISON_CSV = OUT_DIR / "906_20260705_v03_evrp_vs_quantum_vrp_scale_comparison.csv"
SUMMARY_MD = OUT_DIR / "evrp_benchmark_instance_analysis_summary.md"


SPEC_KEYS = {
    "NAME",
    "TYPE",
    "COMMENT",
    "OPTIMAL_VALUE",
    "VEHICLES",
    "DIMENSION",
    "STATIONS",
    "CAPACITY",
    "ENERGY_CAPACITY",
    "ENERGY_CONSUMPTION",
    "EDGE_WEIGHT_TYPE",
}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_scalar(value: str) -> int | float | str:
    value = value.strip()
    if value in {"", "-"}:
        return value
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_instance(path: Path) -> dict[str, Any]:
    spec: dict[str, Any] = {}
    section = ""
    node_coords: list[int] = []
    demand_nodes: list[int] = []
    nonzero_demand_nodes: list[int] = []
    station_nodes: list[int] = []
    depot_nodes: list[int] = []

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "EOF":
            break
        if line in {"NODE_COORD_SECTION", "DEMAND_SECTION", "STATIONS_COORD_SECTION", "STATION_COORD_SECTION", "DEPOT_SECTION"}:
            section = line
            continue
        if ":" in line and not section:
            key, value = line.split(":", 1)
            key = key.strip()
            if key in SPEC_KEYS:
                spec[key] = parse_scalar(value)
            continue
        if section == "NODE_COORD_SECTION":
            parts = line.split()
            if parts and parts[0].lstrip("-").isdigit():
                node_coords.append(int(parts[0]))
        elif section == "DEMAND_SECTION":
            parts = line.split()
            if len(parts) >= 2 and parts[0].lstrip("-").isdigit():
                node = int(parts[0])
                demand = parse_scalar(parts[1])
                demand_nodes.append(node)
                if isinstance(demand, (int, float)) and demand != 0:
                    nonzero_demand_nodes.append(node)
        elif section in {"STATIONS_COORD_SECTION", "STATION_COORD_SECTION"}:
            parts = line.split()
            if parts and parts[0].lstrip("-").isdigit():
                station_nodes.append(int(parts[0]))
        elif section == "DEPOT_SECTION":
            parts = line.split()
            if parts and parts[0].lstrip("-").isdigit():
                depot = int(parts[0])
                if depot != -1:
                    depot_nodes.append(depot)

    dimension = int(spec.get("DIMENSION", 0) or 0)
    stations = int(spec.get("STATIONS", 0) or 0)
    vehicles = int(spec.get("VEHICLES", 0) or 0)
    depot_count = len(depot_nodes)
    customers_by_dimension = dimension - stations - depot_count if dimension else ""
    customers_by_demand = len(nonzero_demand_nodes)
    family = str(spec.get("NAME", path.name)).split("-", 1)[0]

    return {
        "benchmark_id": "e-cvrp-mavrovouniotis-2020",
        "benchmark_family": "E-CVRP",
        "instance_name": spec.get("NAME", path.name),
        "instance_family_prefix": family,
        "source_file": str(path.relative_to(ROOT)),
        "type": spec.get("TYPE", ""),
        "optimal_or_best_known_value": spec.get("OPTIMAL_VALUE", ""),
        "dimension_total_nodes": dimension,
        "customers_by_dimension": customers_by_dimension,
        "customers_with_nonzero_demand": customers_by_demand,
        "vehicles": vehicles,
        "charging_stations_declared": stations,
        "charging_stations_listed": len(station_nodes),
        "depots": depot_count,
        "vehicle_capacity": spec.get("CAPACITY", ""),
        "energy_capacity": spec.get("ENERGY_CAPACITY", ""),
        "energy_consumption": spec.get("ENERGY_CONSUMPTION", ""),
        "edge_weight_type": spec.get("EDGE_WEIGHT_TYPE", ""),
        "node_coord_count": len(node_coords),
        "demand_node_count": len(demand_nodes),
        "has_charging_stations": "yes" if stations > 0 else "no",
        "has_energy_constraint": "yes" if spec.get("ENERGY_CAPACITY", "") != "" else "no",
        "has_capacity_constraint": "yes" if spec.get("CAPACITY", "") != "" else "no",
        "has_time_windows": "no",
        "time_window_customer_count": "",
        "ready_time_min": "",
        "due_date_max": "",
        "service_time_min": "",
        "service_time_max": "",
        "parser_note": "Parsed from .evrp specification and data sections. E-CVRP files include capacity and energy constraints but not customer time windows.",
    }


def parse_evrptw_instance(path: Path) -> dict[str, Any]:
    location_rows: list[dict[str, Any]] = []
    params: dict[str, Any] = {}
    in_locations = False

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            in_locations = False
            continue
        if line.startswith("StringID"):
            in_locations = True
            continue
        if in_locations:
            parts = line.split()
            if len(parts) >= 8:
                location_rows.append(
                    {
                        "string_id": parts[0],
                        "type": parts[1],
                        "x": parse_scalar(parts[2]),
                        "y": parse_scalar(parts[3]),
                        "demand": parse_scalar(parts[4]),
                        "ready_time": parse_scalar(parts[5]),
                        "due_date": parse_scalar(parts[6]),
                        "service_time": parse_scalar(parts[7]),
                    }
                )
            continue
        param_match = re.match(r"([QCrgv])\s+.+?/([^/]+)/", line)
        if param_match:
            params[param_match.group(1)] = parse_scalar(param_match.group(2))

    customers = [row for row in location_rows if row["type"] == "c"]
    stations = [row for row in location_rows if row["type"] == "f"]
    depots = [row for row in location_rows if row["type"] == "d"]
    ready_times = [float(row["ready_time"]) for row in customers if isinstance(row["ready_time"], (int, float))]
    due_dates = [float(row["due_date"]) for row in customers if isinstance(row["due_date"], (int, float))]
    service_times = [float(row["service_time"]) for row in customers if isinstance(row["service_time"], (int, float))]
    family = re.match(r"([a-z]+)", path.stem, flags=re.IGNORECASE)

    return {
        "benchmark_id": "e-vrptw-schneider-goeke-2019",
        "benchmark_family": "E-VRPTW",
        "instance_name": path.name,
        "instance_family_prefix": family.group(1).lower() if family else "",
        "source_file": str(path.relative_to(ROOT)),
        "type": "EVRPTW",
        "optimal_or_best_known_value": "",
        "dimension_total_nodes": len(location_rows),
        "customers_by_dimension": len(customers),
        "customers_with_nonzero_demand": len([row for row in customers if row["demand"] != 0]),
        "vehicles": "",
        "charging_stations_declared": len(stations),
        "charging_stations_listed": len(stations),
        "depots": len(depots),
        "vehicle_capacity": params.get("C", ""),
        "energy_capacity": params.get("Q", ""),
        "energy_consumption": params.get("r", ""),
        "edge_weight_type": "EUC_2D",
        "node_coord_count": len(location_rows),
        "demand_node_count": len(customers),
        "has_charging_stations": "yes" if stations else "no",
        "has_energy_constraint": "yes" if params.get("Q", "") != "" else "no",
        "has_capacity_constraint": "yes" if params.get("C", "") != "" else "no",
        "has_time_windows": "yes" if ready_times and due_dates else "no",
        "time_window_customer_count": len(customers) if ready_times and due_dates else 0,
        "ready_time_min": min(ready_times) if ready_times else "",
        "due_date_max": max(due_dates) if due_dates else "",
        "service_time_min": min(service_times) if service_times else "",
        "service_time_max": max(service_times) if service_times else "",
        "parser_note": "Parsed from Schneider/Goeke Mendeley E-VRPTW .txt instance file. Customer rows include ReadyTime, DueDate, and ServiceTime; vehicle count is not declared in the instance file.",
    }


def summarize_instances(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numeric_fields = [
        "dimension_total_nodes",
        "customers_by_dimension",
        "customers_with_nonzero_demand",
        "vehicles",
        "charging_stations_declared",
        "vehicle_capacity",
        "energy_capacity",
        "time_window_customer_count",
    ]
    out: list[dict[str, Any]] = []
    for field in numeric_fields:
        values = [float(row[field]) for row in rows if isinstance(row.get(field), (int, float)) or str(row.get(field, "")).replace(".", "", 1).isdigit()]
        out.append(
            {
                "metric": field,
                "instance_count": len(values),
                "min": min(values) if values else "",
                "mean": round(mean(values), 3) if values else "",
                "max": max(values) if values else "",
                "interpretation": interpretation_for_metric(field, values),
            }
        )
    out.append(
        {
            "metric": "constraint_coverage",
            "instance_count": len(rows),
            "min": "",
            "mean": "",
            "max": "",
            "interpretation": "All parsed E-CVRP instances include declared vehicles, charging stations, vehicle capacity, energy capacity, and Euclidean coordinates; time windows are not present in this benchmark family.",
        }
    )
    evrptw_rows = [row for row in rows if row.get("benchmark_family") == "E-VRPTW"]
    out.append(
        {
            "metric": "evrptw_constraint_coverage",
            "instance_count": len(evrptw_rows),
            "min": "",
            "mean": "",
            "max": "",
            "interpretation": "Parsed Schneider/Goeke E-VRPTW instances include customers, depots, charging stations, cargo capacity, battery capacity, energy consumption, ReadyTime, DueDate, and ServiceTime. Vehicle count is not declared in these instance files.",
        }
    )
    return out


def interpretation_for_metric(field: str, values: list[float]) -> str:
    if not values:
        return ""
    if field == "dimension_total_nodes":
        return "Total nodes include customers, depot, and charging stations."
    if field == "customers_by_dimension":
        return "Customer count is inferred as DIMENSION minus declared charging stations and depots."
    if field == "customers_with_nonzero_demand":
        return "Nonzero-demand customer count is parsed from DEMAND_SECTION."
    if field == "vehicles":
        return "VEHICLES gives the minimum number of EVs that can be used according to the benchmark README."
    if field == "charging_stations_declared":
        return "STATIONS gives the number of recharging station nodes."
    if field == "vehicle_capacity":
        return "CAPACITY gives EV cargo capacity."
    if field == "energy_capacity":
        return "ENERGY_CAPACITY gives EV battery capacity."
    if field == "time_window_customer_count":
        return "Number of customer rows with explicit ReadyTime and DueDate fields."
    return ""


def first_number(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return int(match.group(1).replace(",", "")) if match else None


def quantum_rows() -> list[dict[str, Any]]:
    if not FIGURE1_CSV.exists():
        return []
    out: list[dict[str, Any]] = []
    for row in read_csv(FIGURE1_CSV):
        scope = row.get("instance_or_scope", "")
        nodes = first_number(r"([0-9,]+)-node", scope)
        locations = first_number(r"([0-9,]+)-location", scope)
        cities = first_number(r"([0-9,]+) cities", scope)
        customers = first_number(r"([0-9,]+) customers", scope)
        vehicles = first_number(r"([0-9,]+)-vehicle", scope) or first_number(r"([0-9,]+) vehicles", scope)
        problem_entities = customers or nodes or locations or cities
        out.append(
            {
                "comparison_group": "quantum_vrp_figure1",
                "item_id": row.get("paper_id", ""),
                "item_label": row.get("instance_or_scope", ""),
                "validation_stage": row.get("validation_stage", ""),
                "problem_entities": problem_entities or "",
                "problem_entities_type": "customers" if customers else "nodes/locations/cities" if problem_entities else "",
                "vehicles": vehicles or "",
                "charging_stations": "",
                "has_charging_stations": "not_reported",
                "has_energy_constraint": "not_reported",
                "has_capacity_constraint": "not_reported_or_problem_dependent",
                "has_time_windows": "not_reported_or_problem_dependent",
                "width_qubits": row.get("width_numeric", ""),
                "note": "Parsed from Figure 1 instance_or_scope; absence of a constraint in this table means not reported in the extracted Figure 1 row, not necessarily absent from the original paper.",
            }
        )
    return out


def comparison_rows(evrp_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = [
        {
            "comparison_group": "e_cvrp_benchmark_instances" if row["benchmark_family"] == "E-CVRP" else "e_vrptw_benchmark_instances",
            "item_id": row["instance_name"],
            "item_label": row["instance_name"],
            "validation_stage": "classical benchmark instance",
            "problem_entities": row["customers_by_dimension"],
            "problem_entities_type": "customers inferred from DIMENSION-STATIONS-depots" if row["benchmark_family"] == "E-CVRP" else "customer rows parsed from E-VRPTW file",
            "vehicles": row["vehicles"],
            "charging_stations": row["charging_stations_declared"],
            "has_charging_stations": row["has_charging_stations"],
            "has_energy_constraint": row["has_energy_constraint"],
            "has_capacity_constraint": row["has_capacity_constraint"],
            "has_time_windows": row["has_time_windows"],
            "width_qubits": "",
            "note": "Parsed from Mavrovouniotis E-CVRP .evrp instance file." if row["benchmark_family"] == "E-CVRP" else "Parsed from Schneider/Goeke Mendeley E-VRPTW .txt file; customer rows include ReadyTime, DueDate, and ServiceTime.",
        }
        for row in evrp_rows
    ]
    out.extend(quantum_rows())
    return out


def write_summary_md(instance_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# EVRP Benchmark Instance Analysis",
        "",
        "## Purpose",
        "",
        "This analysis parses actual benchmark instance files from two EVRP families: Mavrovouniotis et al. E-CVRP files and Schneider/Goeke E-VRPTW files. The purpose is to make EVRP requirements concrete before comparing them with the smaller or less-constrained quantum VRP evidence summarized in Figure 1.",
        "",
        "## Parsed Source",
        "",
        "| Source | Value |",
        "| --- | --- |",
        "| Benchmark families | E-CVRP; E-VRPTW |",
        "| E-CVRP repository | `03_data/raw/evrp_benchmarks/e-cvrp_benchmark_instances` |",
        "| E-VRPTW repository | `03_data/raw/evrp_benchmarks/e-vrptw_mendeley_schneider/evrptw_instances` |",
        f"| Parsed instances | {len(instance_rows)} |",
        "| Instance format | `.evrp` files and Schneider/Goeke `.txt` files |",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Count | Min | Mean | Max | Interpretation |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['metric']} | {row['instance_count']} | {row['min']} | {row['mean']} | {row['max']} | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Main Implication",
            "",
            "The parsed EVRP benchmark files show that an EV routing benchmark is not defined only by node count. It can explicitly include charging stations, cargo capacity, battery capacity, energy consumption, customer time windows, and service time. This gives a concrete comparison basis for asking whether quantum VRP evidence has moved beyond generic small VRP instances toward EVRP-style constraints.",
            "",
            "## Limitations",
            "",
            "- E-CVRP files include declared vehicles, but do not include time windows.",
            "- E-VRPTW files include time windows, but vehicle count is not declared in the instance file.",
            "- Coordinates are synthetic benchmark coordinates, not Tokyo road-network coordinates.",
            "- Customer count is inferred as `DIMENSION - STATIONS - depots`; this is consistent with the file structure but should be reported as an inferred value.",
            "",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    instance_paths = sorted(BENCH_DIR.glob("*.evrp"))
    evrptw_paths = sorted(path for path in EVRPTW_DIR.glob("*.txt") if path.name.lower() != "318_20190122_v02_readme.txt")
    rows = [parse_instance(path) for path in instance_paths]
    rows.extend(parse_evrptw_instance(path) for path in evrptw_paths)
    write_csv(
        INSTANCE_FIELDS_CSV,
        rows,
        [
            "benchmark_id",
            "benchmark_family",
            "instance_name",
            "instance_family_prefix",
            "source_file",
            "type",
            "optimal_or_best_known_value",
            "dimension_total_nodes",
            "customers_by_dimension",
            "customers_with_nonzero_demand",
            "vehicles",
            "charging_stations_declared",
            "charging_stations_listed",
            "depots",
            "vehicle_capacity",
            "energy_capacity",
            "energy_consumption",
            "edge_weight_type",
            "node_coord_count",
            "demand_node_count",
            "has_charging_stations",
            "has_energy_constraint",
            "has_capacity_constraint",
            "has_time_windows",
            "time_window_customer_count",
            "ready_time_min",
            "due_date_max",
            "service_time_min",
            "service_time_max",
            "parser_note",
        ],
    )
    summary = summarize_instances(rows)
    write_csv(SUMMARY_CSV, summary, ["metric", "instance_count", "min", "mean", "max", "interpretation"])
    comp = comparison_rows(rows)
    write_csv(
        QUANTUM_COMPARISON_CSV,
        comp,
        [
            "comparison_group",
            "item_id",
            "item_label",
            "validation_stage",
            "problem_entities",
            "problem_entities_type",
            "vehicles",
            "charging_stations",
            "has_charging_stations",
            "has_energy_constraint",
            "has_capacity_constraint",
            "has_time_windows",
            "width_qubits",
            "note",
        ],
    )
    write_summary_md(rows, summary)
    for path in [INSTANCE_FIELDS_CSV, SUMMARY_CSV, QUANTUM_COMPARISON_CSV, SUMMARY_MD]:
        print(path)


if __name__ == "__main__":
    main()
