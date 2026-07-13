from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "use_case_scenario"
SOCIO_CSV = ROOT / "data" / "processed" / "449_20260705_socio_technical_variables.csv"
EVRP_SUMMARY_CSV = OUT_DIR / "evrp_benchmark_instance_summary.csv"
QUANTUM_COMPARISON_CSV = OUT_DIR / "906_20260705_v03_evrp_vs_quantum_vrp_scale_comparison.csv"

REQUIREMENT_MAP_CSV = OUT_DIR / "943_20260705_v03_tokyo_evrp_quantum_requirement_map.csv"
REQUIREMENT_SUMMARY_MD = OUT_DIR / "tokyo_evrp_quantum_requirement_map_summary.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def socio_value(variable_id: str) -> str:
    for row in read_csv(SOCIO_CSV):
        if row["variable_id"] == variable_id:
            return f"{row['value']} {row['unit']}".strip()
    return ""


def summary_metric(metric: str) -> dict[str, str]:
    for row in read_csv(EVRP_SUMMARY_CSV):
        if row["metric"] == metric:
            return row
    return {}


def quantum_summary() -> dict[str, Any]:
    rows = read_csv(QUANTUM_COMPARISON_CSV)
    qrows = [row for row in rows if row["comparison_group"] == "quantum_vrp_figure1"]
    def nums(field: str) -> list[int]:
        out = []
        for row in qrows:
            value = row.get(field, "")
            if value and value.isdigit():
                out.append(int(value))
        return out
    entities = nums("problem_entities")
    vehicles = nums("vehicles")
    charging_reported = [row for row in qrows if row.get("has_charging_stations") == "yes"]
    energy_reported = [row for row in qrows if row.get("has_energy_constraint") == "yes"]
    time_windows = [row for row in qrows if "vrptw" in row.get("item_id", "").lower()]
    return {
        "row_count": len(qrows),
        "problem_entities_min": min(entities) if entities else "",
        "problem_entities_max": max(entities) if entities else "",
        "vehicles_min": min(vehicles) if vehicles else "",
        "vehicles_max": max(vehicles) if vehicles else "",
        "charging_reported_count": len(charging_reported),
        "energy_reported_count": len(energy_reported),
        "time_window_related_count": len(time_windows),
    }


def evrp_range(metric: str) -> str:
    row = summary_metric(metric)
    if not row:
        return ""
    return f"{row['min']}-{row['max']} (mean {row['mean']})"


def count_comparison_rows(group: str, **filters: str) -> int:
    rows = read_csv(QUANTUM_COMPARISON_CSV)
    count = 0
    for row in rows:
        if row.get("comparison_group") != group:
            continue
        if all(row.get(key) == value for key, value in filters.items()):
            count += 1
    return count


def build_rows() -> list[dict[str, Any]]:
    q = quantum_summary()
    evrptw_with_time_windows = count_comparison_rows("e_vrptw_benchmark_instances", has_time_windows="yes")
    return [
        {
            "requirement_id": "REQ-01",
            "evrp_requirement": "customers / demand nodes",
            "why_it_matters": "Represents delivery demand size and the number of service locations in routing.",
            "evrp_benchmark_evidence": f"Parsed E-CVRP and Schneider/Goeke E-VRPTW files: customers range {evrp_range('customers_by_dimension')}.",
            "tokyo_public_data_proxy": f"Tokyo population density: {socio_value('population_density_tokyo_mesh')}; Tokyo population: {socio_value('population_tokyo_2020')}; OSM road network can support synthetic customer placement.",
            "tokyo_subcase_status": "partial",
            "quantum_figure1_evidence": f"Figure 1 parsed problem entities range {q['problem_entities_min']}-{q['problem_entities_max']} where reported; many evaluated rows are 3-6 nodes/locations. Golden_5 reports 200 customers but is resource estimation only.",
            "quantum_gap": "Evaluated quantum VRP evidence is mostly toy-size; large customer counts appear mainly as resource estimates rather than executed/evaluated EVRP instances.",
            "benchmark_design_implication": "Define synthetic Tokyo customer nodes explicitly; do not infer them directly from EV stock or GTFS stops.",
            "limitation": "Tokyo public data are demand proxies, not observed delivery customers.",
        },
        {
            "requirement_id": "REQ-02",
            "evrp_requirement": "vehicles / fleet size",
            "why_it_matters": "Determines fleet coordination, capacity allocation, and route count.",
            "evrp_benchmark_evidence": f"E-CVRP parsed VEHICLES range: {evrp_range('vehicles')}.",
            "tokyo_public_data_proxy": f"Japan van EV stock: {socio_value('ev_stock_vans_japan_2025')}; van EV sales share: {socio_value('ev_sales_share_vans_japan_2025')}.",
            "tokyo_subcase_status": "needs scenario assumption",
            "quantum_figure1_evidence": f"Figure 1 vehicle counts where reported range {q['vehicles_min']}-{q['vehicles_max']}; several rows do not report vehicles in the extracted scope.",
            "quantum_gap": "Quantum rows often report nodes/qubits but not fleet-size scenarios comparable to EVRP benchmark vehicles.",
            "benchmark_design_implication": "Set fleet size as a scenario parameter, not by converting national EV stock.",
            "limitation": "EV stock and sales share are national context indicators, not operator fleet-size data.",
        },
        {
            "requirement_id": "REQ-03",
            "evrp_requirement": "charging stations",
            "why_it_matters": "Distinguishes EVRP from generic VRP by adding station-choice and recharge feasibility.",
            "evrp_benchmark_evidence": f"Parsed E-CVRP and Schneider/Goeke E-VRPTW files: charging stations range {evrp_range('charging_stations_declared')}.",
            "tokyo_public_data_proxy": f"Open Charge Map Tokyo bounding-box stations: {socio_value('charging_stations_tokyo_geocoded_snapshot')}; fast charger share proxy: {socio_value('fast_charger_share_tokyo_snapshot')}.",
            "tokyo_subcase_status": "available as public-data proxy",
            "quantum_figure1_evidence": f"Figure 1 rows with charging stations explicitly reported in parsed scope: {q['charging_reported_count']}.",
            "quantum_gap": "Existing quantum VRP extraction does not show direct charging-station evidence for Figure 1 rows.",
            "benchmark_design_implication": "Use geocoded chargers to define candidate station sets; report coverage limitations.",
            "limitation": "Open Charge Map coverage/status may be incomplete and bounding-box filtering can include surrounding cities.",
        },
        {
            "requirement_id": "REQ-04",
            "evrp_requirement": "vehicle capacity / cargo capacity",
            "why_it_matters": "Represents load feasibility and distinguishes CVRP/E-CVRP from unconstrained routing.",
            "evrp_benchmark_evidence": f"Parsed E-CVRP and Schneider/Goeke E-VRPTW files: vehicle/cargo capacity range {evrp_range('vehicle_capacity')}.",
            "tokyo_public_data_proxy": "No direct public operator load/cargo dataset collected. Capacity must be set from vehicle class or benchmark assumption.",
            "tokyo_subcase_status": "needs scenario assumption",
            "quantum_figure1_evidence": "Figure 1 includes a Golden_5 CVRP resource estimate with capacity 900; other evaluated rows often do not expose comparable cargo-capacity fields in the extracted scope.",
            "quantum_gap": "Capacity appears in some CVRP framing/resource estimate but is not consistently tied to EV logistics constraints.",
            "benchmark_design_implication": "Choose cargo capacity explicitly and separate it from EV stock or population proxies.",
            "limitation": "Public Tokyo data do not provide operator package demand or vehicle payload distribution.",
        },
        {
            "requirement_id": "REQ-05",
            "evrp_requirement": "battery / energy capacity",
            "why_it_matters": "Defines range feasibility and recharge need.",
            "evrp_benchmark_evidence": f"Parsed E-CVRP and Schneider/Goeke E-VRPTW files: energy capacity range {evrp_range('energy_capacity')}; all parsed instances include energy constraints.",
            "tokyo_public_data_proxy": "No vehicle-specific battery-capacity dataset collected. Tokyo charger data provide station/power context, not vehicle battery capacity.",
            "tokyo_subcase_status": "needs scenario assumption",
            "quantum_figure1_evidence": f"Figure 1 rows with energy constraints explicitly reported in parsed scope: {q['energy_reported_count']}.",
            "quantum_gap": "Energy/SOC constraints are central in EVRP benchmark files but are not visible in the extracted Figure 1 quantum VRP rows.",
            "benchmark_design_implication": "Set battery/SOC parameters from benchmark convention or vehicle specification assumptions.",
            "limitation": "Cannot infer battery capacity from charger count or EV stock.",
        },
        {
            "requirement_id": "REQ-06",
            "evrp_requirement": "energy consumption",
            "why_it_matters": "Links route distance to battery depletion.",
            "evrp_benchmark_evidence": "Parsed E-CVRP and Schneider/Goeke E-VRPTW files include energy/fuel consumption fields.",
            "tokyo_public_data_proxy": f"OSM road network: road density {socio_value('road_network_density_tokyo_snapshot')}; road length proxy {socio_value('road_length_tokyo_bbox_snapshot')}.",
            "tokyo_subcase_status": "needs model assumption",
            "quantum_figure1_evidence": "Energy consumption is not a reported field in the extracted Figure 1 quantum VRP scopes.",
            "quantum_gap": "Quantum VRP evidence generally reports routing formulation/width rather than EV energy-consumption feasibility.",
            "benchmark_design_implication": "Define a distance-to-energy model when constructing Tokyo EVRP benchmark instances.",
            "limitation": "OSM roads provide network geometry, not vehicle energy consumption.",
        },
        {
            "requirement_id": "REQ-07",
            "evrp_requirement": "depot",
            "why_it_matters": "Defines vehicle start/end and route feasibility.",
            "evrp_benchmark_evidence": "Parsed E-CVRP and Schneider/Goeke E-VRPTW instances contain one depot.",
            "tokyo_public_data_proxy": "No depot-location dataset collected. Depot must be selected synthetically or from a separate logistics facility dataset.",
            "tokyo_subcase_status": "needs scenario assumption",
            "quantum_figure1_evidence": "Some VRP formulations imply a depot, but depot details are not consistently extracted in Figure 1.",
            "quantum_gap": "Depot assumptions are not consistently reported in a way that supports EVRP benchmark reconstruction.",
            "benchmark_design_implication": "Specify depot coordinates explicitly in the Tokyo benchmark design.",
            "limitation": "Public data do not provide operator depot locations.",
        },
        {
            "requirement_id": "REQ-08",
            "evrp_requirement": "distance / travel-cost representation",
            "why_it_matters": "Defines the route objective and feasibility cost.",
            "evrp_benchmark_evidence": "Parsed E-CVRP files include EUC_2D coordinates and EDGE_WEIGHT_TYPE; Schneider/Goeke E-VRPTW files include coordinates under Euclidean-distance assumptions.",
            "tokyo_public_data_proxy": f"OSM road network and intersections: {socio_value('road_intersections_tokyo_snapshot')}; Toei Bus GTFS is available but is not a delivery road network.",
            "tokyo_subcase_status": "available as public-data proxy",
            "quantum_figure1_evidence": "Figure 1 rows report instance sizes and encodings; distance/cost matrix availability is not consistently captured in the extracted table.",
            "quantum_gap": "Quantum evidence often abstracts the routing cost without public-data-grounded travel-cost construction.",
            "benchmark_design_implication": "Construct or document a distance/travel-time matrix from OSM, and keep GTFS separate as smart-city data readiness evidence.",
            "limitation": "OSM-derived costs are proxy costs unless travel-time calibration is added.",
        },
        {
            "requirement_id": "REQ-09",
            "evrp_requirement": "time windows",
            "why_it_matters": "Represents service promises, delivery timing, and operational feasibility.",
            "evrp_benchmark_evidence": f"Parsed Schneider/Goeke E-VRPTW files with explicit customer ReadyTime, DueDate, and ServiceTime: {evrptw_with_time_windows} instances. E-CVRP files do not include time windows.",
            "tokyo_public_data_proxy": f"Japan LPI Timeliness: {socio_value('lpi_timeliness_japan_2022')}; GTFS stop_time records: {socio_value('gtfs_stop_times_tokyo')}.",
            "tokyo_subcase_status": "benchmark-supported; Tokyo delivery windows still assumed",
            "quantum_figure1_evidence": f"Figure 1 contains VRPTW-related rows count by item_id: {q['time_window_related_count']}, but these do not include EV charging/SOC in the extracted scope.",
            "quantum_gap": "Time-window evidence exists in some quantum VRPTW rows, but EV charging and battery feasibility are not jointly represented.",
            "benchmark_design_implication": "Use Schneider/Goeke E-VRPTW as the benchmark template for time-window fields; assign Tokyo-specific delivery windows as scenario assumptions unless operator data are obtained.",
            "limitation": "LPI and GTFS do not provide parcel delivery time windows.",
        },
        {
            "requirement_id": "REQ-10",
            "evrp_requirement": "validation / feasibility evidence",
            "why_it_matters": "A benchmark should evaluate whether routes satisfy constraints, not only whether a circuit can be mapped.",
            "evrp_benchmark_evidence": "Parsed E-CVRP and Schneider/Goeke E-VRPTW files define feasibility constraints through demand, capacity, energy, stations, depots, and time-window fields.",
            "tokyo_public_data_proxy": "Tokyo data support benchmark construction but do not provide observed feasible operator routes.",
            "tokyo_subcase_status": "benchmark-design only",
            "quantum_figure1_evidence": "Figure 1 has simulation, hardware-aware, hardware-targeted, and resource-estimate stages; resource estimates are not hardware execution.",
            "quantum_gap": "Current quantum evidence needs clearer reporting of EVRP constraint satisfaction and feasibility, not only width/depth.",
            "benchmark_design_implication": "Future quantum VRP evaluation should report constraint coverage and feasible-route evidence against EVRP-style instances.",
            "limitation": "This map does not claim operational deployment or quantum advantage.",
        },
    ]


def write_summary(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Tokyo-EVRP-Quantum Requirement Map Summary",
        "",
        "## Purpose",
        "",
        "This table connects three layers: Tokyo public data, parsed EVRP benchmark requirements, and the Figure 1 quantum VRP evidence. It is designed to prevent the analysis from comparing unrelated indicators such as EV stock, GTFS routes, and qubit width directly.",
        "",
        "## Main Finding",
        "",
        "The parsed EVRP benchmark files make the benchmark requirements concrete: E-CVRP provides vehicles, charging stations, capacity, energy capacity, energy consumption, depot, and distance/cost representation; Schneider/Goeke E-VRPTW additionally provides customer ReadyTime, DueDate, and ServiceTime. Tokyo public data can support some requirements, especially charging stations and road-network context, but several fields still require scenario assumptions. Figure 1 quantum VRP evidence remains mostly smaller or less explicit about EV-specific constraints.",
        "",
        "## Requirement Status",
        "",
        "| Requirement | Tokyo status | Main gap |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['evrp_requirement']} | {row['tokyo_subcase_status']} | {row['quantum_gap']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Rule",
            "",
            "Use this map as a bridge table. It does not show that Tokyo EV delivery routes are observed, and it does not show that quantum VRP is deployment-ready. It shows which EVRP benchmark requirements are already supported by public data, which require assumptions, and which are not yet visible in the extracted quantum VRP evidence.",
            "",
        ]
    )
    REQUIREMENT_SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_rows()
    fields = [
        "requirement_id",
        "evrp_requirement",
        "why_it_matters",
        "evrp_benchmark_evidence",
        "tokyo_public_data_proxy",
        "tokyo_subcase_status",
        "quantum_figure1_evidence",
        "quantum_gap",
        "benchmark_design_implication",
        "limitation",
    ]
    write_csv(REQUIREMENT_MAP_CSV, rows, fields)
    write_summary(rows)
    print(REQUIREMENT_MAP_CSV)
    print(REQUIREMENT_SUMMARY_MD)


if __name__ == "__main__":
    main()
