from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIT_DIR = ROOT / "literature" / "use_case_scenario"
OUT_DIR = ROOT / "outputs" / "use_case_scenario"

AXES_CSV = LIT_DIR / "212_20260704_morphological_analysis_axes.csv"
COMBINATIONS_CSV = OUT_DIR / "919_20260704_v03_morphological_use_case_candidates.csv"
SUMMARY_MD = OUT_DIR / "morphological_analysis_summary.md"
OPEN_DATA_PLAN_CSV = LIT_DIR / "215_20260704_socio_technical_open_data_collection_plan.csv"


AXES = [
    {
        "axis_id": "A1",
        "axis_name": "routing_problem_type",
        "candidate_values": "CVRP; VRPTW; EVRP; E-VRPTW; dynamic VRP; pickup-delivery VRP",
        "screening_role": "Defines the mathematical routing problem family.",
        "evidence_source": "cevrptw-customer-satisfaction-2025; evrptw-2014-schneider; dvrp-2013-pillac; figure_1_presentation_plot_data.csv",
    },
    {
        "axis_id": "A2",
        "axis_name": "fleet_type",
        "candidate_values": "delivery vans; medium/heavy-duty trucks; mixed fleet; service fleet; passenger EV fleet",
        "screening_role": "Links the routing problem to EV/logistics operations.",
        "evidence_source": "nrel-mdhd-charging-2024; commercial-ev-routing-urban-2020; iea-global-ev-outlook-2026",
    },
    {
        "axis_id": "A3",
        "axis_name": "operation_context",
        "candidate_values": "urban last-mile; depot-based fleet routing; corridor logistics; emergency dispatch; regional delivery",
        "screening_role": "Defines where the use case appears operationally.",
        "evidence_source": "commercial-ev-routing-urban-2020; joint-office-2030-charging-network; nrel-mdhd-charging-2024",
    },
    {
        "axis_id": "A4",
        "axis_name": "constraint_set",
        "candidate_values": "capacity; time windows; SOC; charging station choice; charging time; depot/grid capacity; dynamic demand",
        "screening_role": "Identifies the constraints that make the use case socially specific.",
        "evidence_source": "evrptw-2014-schneider; evrptw-charging-models-2024; nrel-mdhd-charging-2024; dvrp-2013-pillac",
    },
    {
        "axis_id": "A5",
        "axis_name": "decision_frequency",
        "candidate_values": "daily planning; shift-level planning; intra-day reoptimization; real-time dispatch",
        "screening_role": "Separates static planning problems from workflow-intensive dynamic problems.",
        "evidence_source": "dvrp-2013-pillac; 206_20260626_social_quantum_readiness_alignment.csv",
    },
    {
        "axis_id": "A6",
        "axis_name": "data_readiness",
        "candidate_values": "synthetic benchmark; public benchmark; literature case study; operator data; real-time telemetry",
        "screening_role": "Screens whether a use case can be benchmarked and audited.",
        "evidence_source": "figure_1_presentation_plot_data.csv; vrptw-2023-leonidas; cvrp-2023-palackal",
    },
    {
        "axis_id": "A7",
        "axis_name": "quantum_formulation",
        "candidate_values": "QUBO; Ising; route-based encoding; decomposition; HOBO/direct; hybrid heuristic",
        "screening_role": "Maps the use case to possible quantum optimization formulations.",
        "evidence_source": "200_20260625_circuit_resources.csv; figure_1_presentation_plot_data.csv",
    },
    {
        "axis_id": "A8",
        "axis_name": "current_quantum_evidence",
        "candidate_values": "formulation; classical simulation; hardware-aware check; hardware run/target; resource estimate",
        "screening_role": "Records the current evidence level without treating it as deployment readiness.",
        "evidence_source": "figure_1_presentation_plot_data.csv; 202_20260625_quantum_readiness_evidence.csv",
    },
    {
        "axis_id": "A9",
        "axis_name": "benchmark_scale",
        "candidate_values": "toy; small constrained; candidate-route set; benchmark-scale resource estimate; operational proxy",
        "screening_role": "Separates toy benchmarks from socially meaningful operational proxies.",
        "evidence_source": "figure_1_presentation_plot_data.csv; outputs/scale_gap/quantum_benchmark_scale_extracted.csv",
    },
    {
        "axis_id": "A10",
        "axis_name": "evaluation_metric",
        "candidate_values": "feasibility; objective cost; runtime; route validity; charging feasibility; service quality; energy cost",
        "screening_role": "Defines what success should mean for each use case.",
        "evidence_source": "205_20260626_roadmap_gap_matrix.csv; 206_20260626_social_quantum_readiness_alignment.csv",
    },
    {
        "axis_id": "A11",
        "axis_name": "urban_network_complexity",
        "candidate_values": "low road density; medium road density; dense urban grid; multimodal urban network; restricted-access network",
        "screening_role": "Uses OSM/Overture/e-Stat style open data to judge whether the routing environment is spatially complex enough to justify an urban routing benchmark.",
        "evidence_source": "OpenStreetMap; Overture Maps; e-Stat population mesh; national geospatial open data",
    },
    {
        "axis_id": "A12",
        "axis_name": "smart_city_data_readiness",
        "candidate_values": "no public mobility data; static open data; GTFS/static transport data; traffic-count or sensor data; real-time API/telemetry",
        "screening_role": "Screens whether dynamic dispatch, reoptimization, or data-driven benchmark construction can be supported by public smart-city data.",
        "evidence_source": "GTFS feeds; city open data portals; traffic sensor open data; smart-city API catalogs",
    },
    {
        "axis_id": "A13",
        "axis_name": "charging_geospatial_readiness",
        "candidate_values": "no geocoded charger data; station locations only; charger type/power available; availability/status data; depot/grid capacity data",
        "screening_role": "Determines whether EV routing constraints can be grounded in charging infrastructure data rather than treated as abstract constraints.",
        "evidence_source": "Open Charge Map; EAFO; NREL AFDC; national charging infrastructure datasets",
    },
]


OPEN_DATA_COLLECTION_PLAN = [
    {
        "data_layer": "EV adoption and fleet electrification context",
        "candidate_sources": "IEA Global EV Data Explorer; national EV statistics",
        "variables_to_collect": "EV stock; EV sales; EV sales share; vehicle mode; powertrain; country; year",
        "spatial_level": "country / region",
        "temporal_level": "annual",
        "used_for_axis": "fleet_type; operation_context; EV/logistics social context",
        "analysis_use": "Explains whether EV routing or charging-aware routing is socially relevant in the selected country or region.",
        "limitation": "EV stock is not a route count, fleet size, or quantum benchmark size.",
        "collection_status": "local IEA workbook exists; extract selected countries/years",
    },
    {
        "data_layer": "Logistics system maturity",
        "candidate_sources": "World Bank Logistics Performance Index / Data360",
        "variables_to_collect": "LPI overall; Timeliness; Infrastructure; Tracking and tracing; Logistics competence",
        "spatial_level": "country",
        "temporal_level": "survey year",
        "used_for_axis": "logistics pressure; timeliness pressure; operation_context",
        "analysis_use": "Provides a country-level background for why time-window, reliability, and logistics service constraints matter.",
        "limitation": "Country-level proxy; does not describe a specific city route network or operator workflow.",
        "collection_status": "needs source CSV/API download",
    },
    {
        "data_layer": "Charging infrastructure geography",
        "candidate_sources": "Open Charge Map; EAFO; NREL AFDC; national charging station open data",
        "variables_to_collect": "station latitude/longitude; connector type; power level; access type; operator; status if available",
        "spatial_level": "city / corridor / country",
        "temporal_level": "snapshot or dated extract",
        "used_for_axis": "charging_geospatial_readiness; constraint_set; data_readiness",
        "analysis_use": "Converts EVRP charging constraints into geographically grounded station-choice and charging-feasibility conditions.",
        "limitation": "Coverage and update quality differ by platform and country; status/availability may be missing.",
        "collection_status": "needs API or CSV extract for target geography",
    },
    {
        "data_layer": "Road network and urban spatial structure",
        "candidate_sources": "OpenStreetMap; Overture Maps; national geospatial data portals",
        "variables_to_collect": "road graph; road class; intersections; speed/one-way restrictions where available; POIs; depots or logistics facility candidates",
        "spatial_level": "city / metropolitan area",
        "temporal_level": "snapshot",
        "used_for_axis": "urban_network_complexity; routing_problem_type; benchmark_scale",
        "analysis_use": "Supports route-network complexity scoring and construction of realistic urban routing benchmark instances.",
        "limitation": "OSM completeness varies by region; road data still needs demand/depot/customer assumptions.",
        "collection_status": "required for city-level case study",
    },
    {
        "data_layer": "Population and demand concentration",
        "candidate_sources": "e-Stat mesh statistics; census open data; city statistical open data",
        "variables_to_collect": "population density; employment density; commercial area indicators; mesh-level demand proxies",
        "spatial_level": "mesh / municipality / city",
        "temporal_level": "census or annual/statistical period",
        "used_for_axis": "urban_network_complexity; operation_context; benchmark demand design",
        "analysis_use": "Helps select customer-node density and urban delivery pressure without claiming actual operator demand.",
        "limitation": "Demand proxy; not observed parcel, grocery, or service-route demand.",
        "collection_status": "required if constructing city-specific customer distributions",
    },
    {
        "data_layer": "Smart-city mobility data readiness",
        "candidate_sources": "GTFS feeds; city open data portals; traffic count datasets; parking/curb/open mobility APIs",
        "variables_to_collect": "GTFS presence; traffic counts; congestion or travel-time feeds; sensor/API availability; update frequency",
        "spatial_level": "city",
        "temporal_level": "static feed / periodic / real-time",
        "used_for_axis": "smart_city_data_readiness; decision_frequency; data_readiness",
        "analysis_use": "Distinguishes static routing use cases from dynamic dispatch and reoptimization use cases.",
        "limitation": "Data availability is not equal to operator adoption; real-time APIs may have license or access limits.",
        "collection_status": "required for dynamic EV dispatch use cases",
    },
]


USE_CASES = [
    {
        "use_case_id": "uc-01",
        "candidate_use_case": "Charging-aware EV last-mile routing",
        "routing_problem_type": "E-VRPTW",
        "fleet_type": "delivery vans",
        "operation_context": "urban last-mile",
        "constraint_set": "SOC; charging station choice; charging time; customer time windows; capacity",
        "decision_frequency": "daily planning or intra-day reoptimization",
        "data_readiness": "literature case study / operator data needed",
        "quantum_formulation": "QUBO or route-based encoding",
        "current_quantum_evidence": "current Figure 1 evidence has VRPTW and small VRP, but not direct EV charging/SOC evidence",
        "benchmark_scale": "small constrained benchmarks currently; operational proxy needed",
        "evaluation_metric": "feasible route rate; charging feasibility; service quality; runtime",
        "urban_network_complexity": "dense urban grid required; use OSM/Overture road graph and population mesh to justify customer-node density",
        "smart_city_data_readiness": "static city data sufficient for daily planning; traffic or API data improves intra-day reoptimization",
        "charging_geospatial_readiness": "geocoded public chargers with connector/power attributes needed",
        "required_open_data": "IEA EV indicators; Open Charge Map/EAFO/NREL charging stations; OSM or Overture road network; e-Stat/city population mesh; optional GTFS/traffic data",
        "social_stage": "EV-integrated routing",
        "social_need_score": 1.6,
        "quantum_evidence_score": 0.4,
        "quantum_gap_score": 1.2,
        "conditional_probability": 0.75,
        "impact_value": 4,
        "confidence_weight": 0.75,
        "evidence_strength": "medium",
        "evidence_sources": "evrptw-2014-schneider; evrptw-charging-models-2024; vrptw-2023-leonidas; 208_20260625_social_stage_variable_extraction.csv",
    },
    {
        "use_case_id": "uc-02",
        "candidate_use_case": "Depot charging-aware fleet routing",
        "routing_problem_type": "EVRP / depot-constrained CVRP",
        "fleet_type": "medium/heavy-duty trucks or delivery vans",
        "operation_context": "depot-based fleet routing",
        "constraint_set": "depot charging capacity; charging schedule; SOC; route duration; vehicle capacity",
        "decision_frequency": "daily or shift-level planning",
        "data_readiness": "operator or depot data needed",
        "quantum_formulation": "decomposition or QUBO with depot constraints",
        "current_quantum_evidence": "no direct depot/grid-constrained quantum VRP evidence in Figure 1 source CSV",
        "benchmark_scale": "operational proxy not yet present",
        "evaluation_metric": "depot capacity feasibility; route feasibility; runtime; energy cost",
        "urban_network_complexity": "medium to high; road graph and depot-service-area structure needed",
        "smart_city_data_readiness": "static data sufficient for shift planning; depot telemetry would be operator-specific and not open data",
        "charging_geospatial_readiness": "public charger data is useful, but depot charger capacity usually requires assumptions or operator data",
        "required_open_data": "IEA EV indicators; OSM/Overture road network; population or business-density proxy; public charging data for fallback charging context",
        "social_stage": "EV-integrated routing",
        "social_need_score": 1.6,
        "quantum_evidence_score": 0.2,
        "quantum_gap_score": 1.4,
        "conditional_probability": 0.75,
        "impact_value": 5,
        "confidence_weight": 0.75,
        "evidence_strength": "medium",
        "evidence_sources": "nrel-mdhd-charging-2024; joint-office-2030-charging-network; 208_20260625_social_stage_variable_extraction.csv",
    },
    {
        "use_case_id": "uc-03",
        "candidate_use_case": "Dynamic EV dispatch with charging constraints",
        "routing_problem_type": "dynamic EVRP / dynamic VRP",
        "fleet_type": "mixed EV fleet",
        "operation_context": "urban or regional dynamic dispatch",
        "constraint_set": "dynamic demand; traffic; SOC; charging congestion; reoptimization frequency",
        "decision_frequency": "intra-day reoptimization or real-time dispatch",
        "data_readiness": "real-time telemetry required",
        "quantum_formulation": "hybrid heuristic or rolling-horizon decomposition",
        "current_quantum_evidence": "current quantum VRP evidence does not directly cover dynamic EV dispatch",
        "benchmark_scale": "operational proxy absent",
        "evaluation_metric": "reoptimization latency; feasibility; service quality; energy cost",
        "urban_network_complexity": "high; dense road graph and demand concentration needed",
        "smart_city_data_readiness": "traffic, sensor, GTFS, or city API evidence required because the use case depends on dynamic operation",
        "charging_geospatial_readiness": "geocoded chargers plus status/availability data desirable; otherwise charging congestion must be scenario-assumed",
        "required_open_data": "OSM/Overture road network; GTFS or traffic open data; city open-data API inventory; charging station data; IEA EV indicators",
        "social_stage": "dynamic EV logistics",
        "social_need_score": 2.2,
        "quantum_evidence_score": 0.2,
        "quantum_gap_score": 2.0,
        "conditional_probability": 0.50,
        "impact_value": 5,
        "confidence_weight": 0.50,
        "evidence_strength": "low-to-medium",
        "evidence_sources": "dvrp-2013-pillac; 208_20260625_social_stage_variable_extraction.csv; 205_20260626_roadmap_gap_matrix.csv",
    },
    {
        "use_case_id": "uc-04",
        "candidate_use_case": "Urban constrained CVRP/VRPTW without EV charging",
        "routing_problem_type": "CVRP / VRPTW",
        "fleet_type": "delivery vans or mixed fleet",
        "operation_context": "urban last-mile",
        "constraint_set": "capacity; time windows; depot/service constraints",
        "decision_frequency": "daily planning",
        "data_readiness": "public or synthetic benchmarks possible",
        "quantum_formulation": "QUBO, route-based encoding, or decomposition",
        "current_quantum_evidence": "small VRPTW, HVRP, and CVRP-derived TSP evidence exists",
        "benchmark_scale": "small constrained benchmarks",
        "evaluation_metric": "route feasibility; objective cost; runtime",
        "urban_network_complexity": "medium to high; OSM/Overture can define realistic road-network and customer-node structure",
        "smart_city_data_readiness": "static open data sufficient; real-time data not required",
        "charging_geospatial_readiness": "not required because EV charging is intentionally excluded",
        "required_open_data": "OSM/Overture road network; e-Stat/city population or business-density proxy; optional LPI/timeliness context",
        "social_stage": "urban constrained routing",
        "social_need_score": 1.2,
        "quantum_evidence_score": 0.6,
        "quantum_gap_score": 0.6,
        "conditional_probability": 0.90,
        "impact_value": 3,
        "confidence_weight": 1.0,
        "evidence_strength": "high",
        "evidence_sources": "cvrp-2023-palackal; vrptw-2023-leonidas; hvrp-2024-fitzek; 206_20260626_social_quantum_readiness_alignment.csv",
    },
    {
        "use_case_id": "uc-05",
        "candidate_use_case": "Charging station availability integrated with route planning",
        "routing_problem_type": "EVRP / location-routing",
        "fleet_type": "delivery vans or passenger EV service fleet",
        "operation_context": "urban or corridor routing",
        "constraint_set": "charging station availability; charging time; SOC; route duration",
        "decision_frequency": "daily or intra-day planning",
        "data_readiness": "charging infrastructure data needed",
        "quantum_formulation": "QUBO or decomposition",
        "current_quantum_evidence": "EV charging station choice is not directly represented in Figure 1 source CSV",
        "benchmark_scale": "operational proxy not yet present",
        "evaluation_metric": "charging feasibility; station assignment; route cost; runtime",
        "urban_network_complexity": "medium; corridor or urban road graph needed to connect customers and chargers",
        "smart_city_data_readiness": "static data sufficient unless station availability or traffic-aware rerouting is modeled",
        "charging_geospatial_readiness": "core requirement; geocoded stations, connector type, and power level are needed",
        "required_open_data": "Open Charge Map/EAFO/NREL charging stations; OSM/Overture road network; IEA EV indicators; optional traffic/city open data",
        "social_stage": "EV-integrated routing",
        "social_need_score": 1.6,
        "quantum_evidence_score": 0.2,
        "quantum_gap_score": 1.4,
        "conditional_probability": 0.75,
        "impact_value": 4,
        "confidence_weight": 0.75,
        "evidence_strength": "medium",
        "evidence_sources": "iea-ev-charging-2026; evrptw-2014-schneider; joint-office-2030-charging-network",
    },
    {
        "use_case_id": "uc-06",
        "candidate_use_case": "Large CVRP utility/resource-gap benchmark",
        "routing_problem_type": "CVRP",
        "fleet_type": "generic logistics fleet",
        "operation_context": "benchmark-scale logistics",
        "constraint_set": "capacity; customer demand; vehicle count",
        "decision_frequency": "offline benchmark",
        "data_readiness": "benchmark instance available",
        "quantum_formulation": "QUBO or HOBO/direct",
        "current_quantum_evidence": "resource estimate exists, but not hardware execution or deployment evidence",
        "benchmark_scale": "benchmark-scale resource estimate",
        "evaluation_metric": "logical qubits; theoretical depth; volume; feasibility assumptions",
        "urban_network_complexity": "not required for the benchmark itself; can be used only to compare benchmark abstraction against real urban networks",
        "smart_city_data_readiness": "not required",
        "charging_geospatial_readiness": "not required unless extending the benchmark into EVRP",
        "required_open_data": "none required for the quantum resource benchmark; optional OSM/IEA data only for contextual gap discussion",
        "social_stage": "dynamic EV logistics / resource pressure",
        "social_need_score": 2.2,
        "quantum_evidence_score": 0.5,
        "quantum_gap_score": 1.7,
        "conditional_probability": 0.25,
        "impact_value": 3,
        "confidence_weight": 0.75,
        "evidence_strength": "medium",
        "evidence_sources": "cvrp-2025-onah-utility; 200_20260625_circuit_resources.csv; qrl_wise_srl_score_summary.csv",
    },
]


def priority(row: dict[str, object]) -> float:
    return (
        float(row["conditional_probability"])
        * float(row["social_need_score"])
        * float(row["quantum_gap_score"])
        * float(row["confidence_weight"])
    )


def expected_impact(row: dict[str, object]) -> float:
    return float(row["conditional_probability"]) * float(row["impact_value"])


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def write_summary(rows: list[dict[str, object]]) -> None:
    lines = [
        "# Morphological Use-Case Analysis",
        "",
        "This analysis adds a morphological layer before the Futures Wheel. It enumerates plausible EV/logistics routing use-case combinations and scores them for scenario-screening purposes.",
        "",
        "The scores are not observed probabilities or claims of quantum deployment readiness. They are literature-informed screening weights used to prioritize candidate use cases for later Futures Wheel and SRL/QRL gap analysis.",
        "",
        "## Scoring Rule",
        "",
        "| Score | Meaning |",
        "| --- | --- |",
        "| `conditional_probability` | Scenario-screening probability that the use case follows from the relevant driver path. |",
        "| `social_need_score` | Reuses the social-side readiness scale from SRL scoring. |",
        "| `quantum_evidence_score` | Approximate current quantum evidence weight; resource estimate is not treated as deployment evidence. |",
        "| `quantum_gap_score` | Social need minus current quantum evidence, expressed as a research-gap signal. |",
        "| `confidence_weight` | Evidence-strength correction: high=1.0, medium=0.75, low=0.5. |",
        "| `priority_score` | `conditional_probability * social_need_score * quantum_gap_score * confidence_weight`. |",
        "| `expected_impact` | `conditional_probability * impact_value`. |",
        "",
        "## Ranked Candidates",
        "",
        "| Rank | Use case | Priority score | Expected impact | Main reason |",
        "| ---: | --- | ---: | ---: | --- |",
    ]
    for idx, row in enumerate(rows, start=1):
        lines.append(
            "| {rank} | {candidate_use_case} | {priority_score:.3f} | {expected_impact:.3f} | {current_quantum_evidence} |".format(
                rank=idx,
                candidate_use_case=row["candidate_use_case"],
                priority_score=float(row["priority_score"]),
                expected_impact=float(row["expected_impact"]),
                current_quantum_evidence=row["current_quantum_evidence"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The strongest candidates are not necessarily the ones with the most advanced quantum evidence. They are the cases where EV/logistics relevance is high and current quantum VRP evidence is still limited.",
            "",
            "Use this table to select which branches should be expanded in the Futures Wheel. The Futures Wheel should then assign explicit parent-child conditional probabilities and compute cumulative probability from the root.",
            "",
        ]
    )
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    axis_fields = ["axis_id", "axis_name", "candidate_values", "screening_role", "evidence_source"]
    write_csv(AXES_CSV, AXES, axis_fields)
    write_csv(
        OPEN_DATA_PLAN_CSV,
        OPEN_DATA_COLLECTION_PLAN,
        [
            "data_layer",
            "candidate_sources",
            "variables_to_collect",
            "spatial_level",
            "temporal_level",
            "used_for_axis",
            "analysis_use",
            "limitation",
            "collection_status",
        ],
    )

    rows = []
    for row in USE_CASES:
        out = dict(row)
        out["expected_impact"] = round(expected_impact(row), 3)
        out["priority_score"] = round(priority(row), 3)
        if out["use_case_id"] == "uc-06":
            out["screening_decision"] = "supporting_resource_gap_case"
        else:
            out["screening_decision"] = "expand_in_futures_wheel" if out["priority_score"] >= 0.9 else "watch_or_supporting_case"
        out["method_note"] = "Morphological screening score; not an observed probability or operational quantum-readiness claim."
        rows.append(out)
    rows.sort(key=lambda row: float(row["priority_score"]), reverse=True)

    combo_fields = [
        "use_case_id",
        "candidate_use_case",
        "routing_problem_type",
        "fleet_type",
        "operation_context",
        "constraint_set",
        "decision_frequency",
        "data_readiness",
        "quantum_formulation",
        "current_quantum_evidence",
        "benchmark_scale",
        "evaluation_metric",
        "urban_network_complexity",
        "smart_city_data_readiness",
        "charging_geospatial_readiness",
        "required_open_data",
        "social_stage",
        "social_need_score",
        "quantum_evidence_score",
        "quantum_gap_score",
        "conditional_probability",
        "impact_value",
        "expected_impact",
        "confidence_weight",
        "priority_score",
        "evidence_strength",
        "evidence_sources",
        "screening_decision",
        "method_note",
    ]
    write_csv(COMBINATIONS_CSV, rows, combo_fields)
    write_summary(rows)
    for path in [AXES_CSV, OPEN_DATA_PLAN_CSV, COMBINATIONS_CSV, SUMMARY_MD]:
        print(path)


if __name__ == "__main__":
    main()
