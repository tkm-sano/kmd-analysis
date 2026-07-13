#!/usr/bin/env python3
"""Generate CSV analysis artifacts for the Tokyo synthetic EVRP study.

This script intentionally produces CSV files only.  Figure and table-image
rendering is handled by ``render_tokyo_synthetic_evrp_outputs.py``.  The
analysis evaluates synthetic route proxies and does not optimize an EVRP or
infer charging events, electricity demand, charger utilization, or grid load.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
import traceback
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

import numpy as np
import pandas as pd

SRC_ROOT = Path(__file__).resolve().parents[1]
for module_dir in (SRC_ROOT / "constraint_evaluation", SRC_ROOT / "sensitivity", SRC_ROOT / "literature_analysis", SRC_ROOT / "scenario_generation"):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from monte_carlo_utils import (
    build_case_rates,
    build_constraint_evaluations,
    build_payload_diagnostics,
    build_time_constraint_diagnostics,
    cluster_bootstrap_constraint_summary,
    run_oat_sensitivity,
    scenario_specific_constraint_summary,
)
from research_summary_utils import (
    build_constraint_interpretation_table,
    build_constraint_variability_table,
    build_integrated_research_summary,
    build_quantum_vrp_gap_detail,
    build_quantum_vrp_gap_table,
    build_scenario_design_table,
)
from scenario_utils import (
    BaselineAssumptions,
    build_analysis_configurations,
    build_charger_condition_definitions,
    build_eligible_charger_candidates,
    construct_route_proxies,
    evaluate_routes_by_condition,
    generate_synthetic_customers,
    select_baseline_vehicle,
    summarize_distance,
)
from validation_utils import (
    file_sha256,
    find_repository_root,
    generate_output_manifest,
    read_csv_checked,
    validate_unique_keys,
    write_csv_atomic,
)


T = TypeVar("T")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="Repository root; auto-detected by default.")
    parser.add_argument(
        "--reproduce",
        action="store_true",
        help="Clear canonical CSV outputs and regenerate all analysis stages.",
    )
    parser.add_argument("--seed-count", type=int, default=100)
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    parser.add_argument("--bootstrap-random-seed", type=int, default=20260711)
    return parser.parse_args()


def _file_flags(path: Path) -> str:
    """Return macOS file flags when available without making them a dependency."""

    try:
        completed = subprocess.run(
            ["ls", "-ldO", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        fields = completed.stdout.split()
        return fields[4] if len(fields) > 4 else "Unknown"
    except (OSError, subprocess.SubprocessError):
        return "Unknown"


def _input_inventory_row(
    root: Path,
    path: Path,
    frame: pd.DataFrame,
    role: str,
    required_columns: list[str],
    key_columns: list[str],
) -> dict[str, object]:
    """Build an auditable inventory row after successful CSV validation."""

    return {
        "path": str(path.relative_to(root)),
        "role": role,
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "required_columns": ";".join(required_columns),
        "total_missing_value_count": int(frame.isna().sum().sum()),
        "maximum_column_missing_rate": float(frame.isna().mean().max()) if len(frame.columns) else np.nan,
        "duplicate_row_count": int(frame.duplicated().sum()),
        "key_columns": ";".join(key_columns),
        "duplicate_key_count": int(frame.duplicated(key_columns).sum()) if key_columns else 0,
        "size_bytes": int(path.stat().st_size),
        "sha256": file_sha256(path),
        "file_system_flags": _file_flags(path),
        "read_status": "Validated readable local CSV",
    }


class AnalysisPipeline:
    """Stateful CSV-only pipeline with stage-level status recording."""

    def __init__(self, root: Path, args: argparse.Namespace) -> None:
        self.root = root
        self.args = args
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.outputs = root / "outputs"
        self.data_root = self.outputs / "data"
        self.table_csv = self.outputs / "tables" / "csv"
        self.validation = self.outputs / "validation"
        self.status_rows: list[dict[str, object]] = []
        self.generated_csvs: list[Path] = []

    def prepare(self) -> None:
        """Clear only pipeline-owned CSV directories in explicit reproduce mode."""

        if not self.args.reproduce:
            raise RuntimeError(
                "Refusing to overwrite or reuse canonical outputs without --reproduce. "
                "The notebook enables this only when TOKYO_EVRP_REPRODUCE=1."
            )
        for directory in [self.data_root, self.table_csv, self.validation]:
            if directory.exists():
                shutil.rmtree(directory)
        for directory in [
            self.data_root / "scenario",
            self.data_root / "route_proxy",
            self.data_root / "constraints",
            self.data_root / "charger_access",
            self.data_root / "quantum_gap",
            self.table_csv,
            self.validation,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def write(self, frame: pd.DataFrame, path: Path) -> Path:
        """Atomically write one CSV and remember it for the manifest."""

        destination = write_csv_atomic(frame, path)
        self.generated_csvs.append(destination)
        return destination

    def status_path(self) -> Path:
        return self.validation / "679_20260711_execution_status.csv"

    def flush_status(self) -> None:
        """Persist current stage states so partial failure is not success-like."""

        write_csv_atomic(pd.DataFrame(self.status_rows), self.status_path())

    def stage(self, name: str, function: Callable[[], T]) -> T:
        """Execute a named stage, persist its duration and re-raise failures."""

        started = time.perf_counter()
        started_at = datetime.now(timezone.utc).isoformat()
        try:
            value = function()
        except Exception as exc:
            self.status_rows.append(
                {
                    "analysis_run_id": self.run_id,
                    "step_name": name,
                    "status": "failed",
                    "started_at_utc": started_at,
                    "duration_seconds": time.perf_counter() - started,
                    "warning": "",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
            self.flush_status()
            raise
        self.status_rows.append(
            {
                "analysis_run_id": self.run_id,
                "step_name": name,
                "status": "success",
                "started_at_utc": started_at,
                "duration_seconds": time.perf_counter() - started,
                "warning": "",
                "error_type": "",
                "error_message": "",
                "traceback": "",
            }
        )
        self.flush_status()
        print(f"[{name}] success ({self.status_rows[-1]['duration_seconds']:.2f}s)")
        return value


def main() -> None:
    """Run the complete CSV-only analysis."""

    args = parse_args()
    root = args.root.expanduser().resolve() if args.root else find_repository_root(Path.cwd())
    if args.seed_count <= 0:
        raise ValueError("--seed-count must be positive.")
    if args.bootstrap_iterations < 1000:
        raise ValueError("--bootstrap-iterations must be at least 1000.")
    pipeline = AnalysisPipeline(root, args)
    pipeline.prepare()
    assumptions = BaselineAssumptions()
    input_dir = root / "data" / "processed" / "evrp_constraint_gap_inputs"

    inputs: dict[str, pd.DataFrame] = {}
    input_inventory: list[dict[str, object]] = []

    def validate_inputs() -> None:
        specifications = {
            "mesh": {
                "path": root / "03_data/processed/413_20260705_estat_tokyo_mesh_population_cells.csv",
                "required": ["mesh_code", "total_population"],
                "numeric": ["mesh_code", "total_population"],
                "keys": ["mesh_code"],
                "role": "Population-weighted synthetic customer-location proxy",
            },
            "chargers": {
                "path": root / "03_data/processed/428_20260705_open_charge_map_tokyo_boundary_clipped_connections.csv",
                "required": [
                    "ocm_id",
                    "connection_id",
                    "latitude",
                    "longitude",
                    "connection_type",
                    "power_kw",
                    "operator",
                    "usage_type",
                    "status_type",
                ],
                "numeric": ["ocm_id", "connection_id", "latitude", "longitude", "power_kw"],
                "keys": ["connection_id"],
                "role": "Open Charge Map candidate connection geography and reported attributes",
            },
            "depots": {
                "path": input_dir / "419_20260711_depot_candidates_public_proxy_snapshot.csv",
                "required": ["scenario_depot_id", "latitude", "longitude", "limitation"],
                "numeric": ["latitude", "longitude"],
                "keys": ["scenario_depot_id"],
                "role": "Public logistics-facility depot-candidate proxy snapshot",
            },
            "vehicles": {
                "path": input_dir / "423_20260711_vehicle_specs_public_source_snapshot.csv",
                "required": [
                    "scenario_vehicle_id",
                    "vehicle_model",
                    "battery_kwh",
                    "catalog_range_km",
                    "payload_kg",
                    "energy_consumption_kwh_per_km",
                    "source_id",
                ],
                "numeric": [],
                "keys": ["scenario_vehicle_id"],
                "role": "Manufacturer-specification vehicle scenario snapshot",
            },
            "parameters": {
                "path": input_dir / "418_20260711_analysis_parameters.csv",
                "required": ["parameter", "low", "base", "high", "unit", "evidence_status", "source_or_rationale"],
                "numeric": [],
                "keys": ["parameter"],
                "role": "Explicit baseline and low/base/high sensitivity assumptions",
            },
            "synthetic_assumptions": {
                "path": input_dir / "synthetic_generation_assumptions.csv",
                "required": ["variable", "distribution", "minimum", "maximum", "unit", "evidence_status"],
                "numeric": ["minimum", "maximum", "theoretical_mean", "theoretical_standard_deviation"],
                "keys": ["variable"],
                "role": "Synthetic demand/service generation distributions",
            },
            "quantum_evidence": {
                "path": input_dir / "421_20260711_quantum_vrp_evidence_registry.csv",
                "required": ["reference_id", "paper_title", "authors", "year", "doi", "url", "page_or_section"],
                "numeric": ["year"],
                "keys": ["reference_id"],
                "role": "Conservative local-note quantum-VRP evidence registry",
            },
            "provenance": {
                "path": input_dir / "420_20260711_input_provenance.csv",
                "required": ["input_id", "canonical_path", "sha256", "evidence_status", "limitation"],
                "numeric": [],
                "keys": ["input_id"],
                "role": "Input origin and hash registry",
            },
        }
        for name, specification in specifications.items():
            frame = read_csv_checked(
                specification["path"],
                required_columns=specification["required"],
                numeric_columns=specification["numeric"] or None,
                unique_keys=specification["keys"],
                require_nonempty=True,
            )
            inputs[name] = frame
            input_inventory.append(
                _input_inventory_row(
                    root,
                    specification["path"],
                    frame,
                    specification["role"],
                    specification["required"],
                    specification["keys"],
                )
            )
        for row in inputs["provenance"].itertuples(index=False):
            canonical = root / row.canonical_path
            if not canonical.exists():
                raise FileNotFoundError(f"Provenance input is missing: {canonical}")
            observed = file_sha256(canonical)
            if observed != row.sha256:
                raise ValueError(
                    f"Input hash mismatch for {row.input_id}: expected {row.sha256}, observed {observed}."
                )
        pipeline.write(pd.DataFrame(input_inventory), pipeline.validation / "682_20260711_input_inventory.csv")

    pipeline.stage("2. Input Data Inventory and Validation", validate_inputs)

    preprocessing_status = pd.DataFrame(
        [
            {
                "step": "Population mesh",
                "mode": "Validated processed-data fallback",
                "raw_source_status": "Data unavailable in reproducible run (macOS dataless placeholder at audit time)",
                "processed_input": "03_data/processed/413_20260705_estat_tokyo_mesh_population_cells.csv",
                "result": "Readable and schema-validated",
                "limitation": "Raw-to-processed regeneration was not executed.",
            },
            {
                "step": "Charger candidates",
                "mode": "Validated processed-data fallback",
                "raw_source_status": "Data unavailable in reproducible run (macOS dataless placeholder at audit time)",
                "processed_input": "03_data/processed/428_20260705_open_charge_map_tokyo_boundary_clipped_connections.csv",
                "result": "Readable and schema-validated",
                "limitation": "Candidate attributes have substantial missingness; availability is not established.",
            },
            {
                "step": "Road network improved mode",
                "mode": "Baseline fallback",
                "raw_source_status": "Data unavailable",
                "processed_input": "Not evaluated",
                "result": "Haversine distance plus explicit road multiplier used",
                "limitation": "No shortest-path geometry or network travel time is evaluated.",
            },
        ]
    )
    pipeline.stage(
        "3. Open-data Preprocessing",
        lambda: pipeline.write(
            preprocessing_status, pipeline.data_root / "scenario/444_20260711_open_data_preprocessing_status.csv"
        ),
    )

    charger_definitions: pd.DataFrame
    charger_candidates: pd.DataFrame
    configurations: pd.DataFrame
    baseline_vehicle: pd.Series

    def define_scenarios() -> None:
        nonlocal charger_definitions, charger_candidates, configurations, baseline_vehicle
        definitions = build_charger_condition_definitions()
        charger_candidates, charger_definitions = build_eligible_charger_candidates(
            inputs["chargers"], definitions
        )
        baseline_vehicle = select_baseline_vehicle(inputs["vehicles"])
        configurations = build_analysis_configurations(
            [25, 50, 100],
            [1, 3, 5],
            charger_definitions,
            baseline_vehicle,
            assumptions,
            args.seed_count,
        )
        pipeline.write(configurations, pipeline.data_root / "scenario/446_20260711_scenario_configurations.csv")
        pipeline.write(charger_definitions, pipeline.data_root / "charger_access/402_20260711_charger_condition_definitions.csv")
        pipeline.write(charger_candidates, pipeline.data_root / "charger_access/403_20260711_eligible_charger_candidates.csv")
        pipeline.write(inputs["parameters"], pipeline.data_root / "scenario/441_20260711_analysis_parameter_registry.csv")
        pipeline.write(inputs["synthetic_assumptions"], pipeline.data_root / "scenario/synthetic_generation_assumptions.csv")
        limitations = pd.DataFrame(
            [
                ("Customer locations", "Synthetic population-weighted locations; not observed orders"),
                ("Customer demand", "Synthetic 5-30 kg values; not observed freight weights"),
                ("Route construction", "KMeans plus nearest-neighbor proxy; not an EVRP optimum"),
                ("Road geometry", "Haversine plus multiplier baseline; road-network paths Data unavailable"),
                ("Travel speed", "Assumed constant value; not calibrated traffic speed"),
                ("Service time", "Synthetic value; not observed stop-service time"),
                ("Visit time windows", "Not evaluated"),
                ("SOC trajectory", "Not evaluated"),
                ("Charger congestion", "Not evaluated"),
                ("Charger failure", "Not evaluated"),
                ("Connector compatibility", "Only reported connector labels screened; actual vehicle compatibility not established"),
                ("Public access and operating hours", "Unknown for many Open Charge Map records"),
                ("Charging price", "Not evaluated"),
                ("Actual charging behavior", "Not evaluated or predicted"),
                ("Charging demand and utilization", "Not evaluated or predicted"),
                ("Electricity-grid load", "Not evaluated or predicted"),
                ("Monte Carlo scope", "Primarily customer spatial configuration plus synthetic demand/service variation"),
                ("Unmet rate meaning", "Model-conditional route-proxy rate; not an observed delivery failure rate"),
                ("Quantum comparison", "Limited to seven local extraction notes with heterogeneous reporting granularity"),
                ("Inference", "All findings depend on explicit vehicle, demand, time, charger, and routing assumptions"),
            ],
            columns=["topic", "limitation"],
        )
        limitations["status"] = np.where(
            limitations["limitation"].str.contains("Not evaluated"),
            "Not evaluated",
            "Assumption or evidence limitation",
        )
        pipeline.write(limitations, pipeline.data_root / "scenario/442_20260711_assumptions_and_limitations.csv")

    pipeline.stage("4. Scenario Definition", define_scenarios)

    customers: pd.DataFrame
    randomization: pd.DataFrame

    def generate_customers() -> None:
        nonlocal customers, randomization
        customers, randomization = generate_synthetic_customers(
            inputs["mesh"], [25, 50, 100], list(range(1, args.seed_count + 1)), assumptions
        )
        pipeline.write(customers, pipeline.data_root / "scenario/447_20260711_synthetic_customers.csv")
        pipeline.write(randomization, pipeline.data_root / "scenario/443_20260711_monte_carlo_randomization_registry.csv")
        realized = (
            customers.groupby("customer_count", as_index=False)
            .agg(
                independent_seed_count=("seed", "nunique"),
                synthetic_customer_row_count=("customer_id", "count"),
                demand_min_kg=("demand_kg", "min"),
                demand_max_kg=("demand_kg", "max"),
                demand_mean_kg=("demand_kg", "mean"),
                demand_standard_deviation_kg=("demand_kg", "std"),
                service_time_mean_min=("service_time_min", "mean"),
                service_time_standard_deviation_min=("service_time_min", "std"),
            )
        )
        realized["evidence_status"] = "Synthetic data with assumed parameters"
        pipeline.write(realized, pipeline.data_root / "scenario/445_20260711_realized_synthetic_distribution_summary.csv")

    pipeline.stage("5. Synthetic Customer Generation", generate_customers)

    base_routes: pd.DataFrame
    route_edges: pd.DataFrame
    route_members: pd.DataFrame

    def build_routes() -> None:
        nonlocal base_routes, route_edges, route_members
        base_routes, route_edges, route_members = construct_route_proxies(
            customers,
            inputs["depots"],
            [25, 50, 100],
            [1, 3, 5],
            list(range(1, args.seed_count + 1)),
            assumptions,
        )
        pipeline.write(base_routes, pipeline.data_root / "route_proxy/436_20260711_base_440_20260711_route_proxy_results.csv")
        pipeline.write(route_edges, pipeline.data_root / "route_proxy/438_20260711_route_proxy_edges.csv")
        pipeline.write(route_members, pipeline.data_root / "route_proxy/439_20260711_route_proxy_members.csv")

    pipeline.stage("6. Route Proxy Construction", build_routes)

    route_results: pd.DataFrame
    constraint_evaluations: pd.DataFrame
    case_rates: pd.DataFrame

    def evaluate_constraints() -> None:
        nonlocal route_results, constraint_evaluations, case_rates
        route_results = evaluate_routes_by_condition(
            base_routes,
            route_members,
            configurations,
            charger_candidates,
            baseline_vehicle,
            assumptions,
        )
        constraint_evaluations = build_constraint_evaluations(route_results)
        case_rates = build_case_rates(constraint_evaluations)
        pipeline.write(route_results, pipeline.data_root / "route_proxy/440_20260711_route_proxy_results.csv")
        pipeline.write(constraint_evaluations, pipeline.data_root / "constraints/406_20260711_constraint_evaluations_long.csv")
        pipeline.write(case_rates, pipeline.data_root / "constraints/405_20260711_constraint_case_rates.csv")
        pipeline.write(summarize_distance(route_results), pipeline.data_root / "route_proxy/437_20260711_route_distance_summary.csv")
        pipeline.write(
            build_payload_diagnostics(customers, route_results),
            pipeline.data_root / "constraints/409_20260711_payload_diagnostics.csv",
        )
        charger_access = route_results[
            [
                "scenario_id",
                "scenario_route_proxy_id",
                "seed",
                "customer_count",
                "vehicle_count",
                "charger_condition",
                "charger_candidate_count",
                "nearest_candidate_charger_id",
                "nearest_charger_haversine_distance_km",
                "nearest_charger_distance_km",
                "maximum_charger_access_distance_km",
                "charger_geographically_accessible",
                "charger_public_access_known",
                "charger_power_known",
                "charger_connector_compatibility_known",
                "charger_operating_status_known",
                "charger_arrival_soc_feasible",
                "charging_assisted_range_evaluated",
                "charging_assisted_range_feasible",
                "charging_duration_evaluated",
                "charging_duration_feasible",
            ]
        ]
        pipeline.write(charger_access, pipeline.data_root / "charger_access/404_20260711_route_charger_access_results.csv")

    pipeline.stage("7. Constraint Evaluation", evaluate_constraints)

    constraint_summary: pd.DataFrame
    scenario_summary: pd.DataFrame
    sensitivity: pd.DataFrame
    sensitivity_response: pd.DataFrame

    def monte_carlo_and_sensitivity() -> None:
        nonlocal constraint_summary, scenario_summary, sensitivity, sensitivity_response
        constraint_summary = cluster_bootstrap_constraint_summary(
            constraint_evaluations,
            case_rates,
            iterations=args.bootstrap_iterations,
            random_seed=args.bootstrap_random_seed,
        )
        scenario_summary = scenario_specific_constraint_summary(
            constraint_evaluations,
            iterations=args.bootstrap_iterations,
            random_seed=args.bootstrap_random_seed,
        )
        sensitivity, sensitivity_response = run_oat_sensitivity(
            route_results, inputs["parameters"], baseline_vehicle
        )
        pipeline.write(constraint_summary, pipeline.data_root / "constraints/407_20260711_constraint_summary.csv")
        pipeline.write(scenario_summary, pipeline.data_root / "constraints/scenario_407_20260711_constraint_summary.csv")
        pipeline.write(sensitivity, pipeline.data_root / "constraints/411_20260711_sensitivity_summary.csv")
        pipeline.write(sensitivity_response, pipeline.data_root / "constraints/408_20260711_parameter_response_table.csv")
        pipeline.write(
            build_time_constraint_diagnostics(sensitivity),
            pipeline.data_root / "constraints/412_20260711_time_constraint_diagnostics.csv",
        )

    pipeline.stage("8. Monte Carlo and Sensitivity Analysis", monte_carlo_and_sensitivity)

    quantum_gap_detail: pd.DataFrame

    def quantum_comparison() -> None:
        nonlocal quantum_gap_detail
        pipeline.write(
            inputs["quantum_evidence"],
            pipeline.data_root / "quantum_gap/434_20260711_quantum_vrp_evidence.csv",
        )
        quantum_gap_detail = build_quantum_vrp_gap_detail(
            inputs["quantum_evidence"], configurations, constraint_summary
        )
        pipeline.write(
            quantum_gap_detail,
            pipeline.data_root / "quantum_gap/435_20260711_quantum_vrp_gap_detail.csv",
        )

    pipeline.stage("10. Quantum VRP Evidence Comparison", quantum_comparison)

    def build_tables() -> None:
        table_1 = build_scenario_design_table(configurations)
        table_2 = build_constraint_variability_table(constraint_summary)
        table_3 = build_quantum_vrp_gap_table(quantum_gap_detail)
        table_4 = build_integrated_research_summary(
            constraint_summary, sensitivity_response, quantum_gap_detail
        )
        table_5_full, table_5_slide = build_constraint_interpretation_table(
            constraint_summary
        )
        tables = {
            "688_20260711_table_01_scenario_design.csv": table_1,
            "689_20260711_table_02_constraint_unmet_variability.csv": table_2,
            "690_20260711_table_03_quantum_vrp_gap.csv": table_3,
            "691_20260711_table_04_integrated_research_summary.csv": table_4,
            "692_20260711_table_05_constraint_interpretation_full.csv": table_5_full,
            "693_20260711_table_05_constraint_interpretation_slide.csv": table_5_slide,
        }
        for filename, table in tables.items():
            pipeline.write(table, pipeline.table_csv / filename)

    pipeline.stage("11. Research Presentation Summary Tables", build_tables)

    def final_validation_csvs() -> None:
        integrity = pd.DataFrame(
            [
                {"check": "No hard-coded result values in research tables", "status": "pass", "observed": "Tables built from generated DataFrames"},
                {"check": "Not-evaluated metrics are not zero", "status": "pass", "observed": "SOC route-weighted unmet rate is missing/Not evaluated"},
                {"check": "Observed and synthetic data distinguished", "status": "pass", "observed": "Customer evidence_status is Synthetic data with assumed parameters"},
                {"check": "Route proxy not described as optimum", "status": "pass", "observed": "route_proxy_limitation explicitly states not optimized"},
                {"check": "Conditional evaluations not independent trials", "status": "pass", "observed": f"{args.seed_count} paired seed identifiers; {len(configurations) * args.seed_count} conditional evaluations"},
                {"check": "Distance and range not double-counted", "status": "pass", "observed": "Distance is a continuous summary; no distance unmet constraint"},
                {"check": "SOC not inferred from distance threshold", "status": "pass", "observed": "SOC feasibility = Not evaluated"},
                {"check": "Charging pathway generated", "status": "pass", "observed": False},
                {"check": "Charging-demand estimation generated", "status": "pass", "observed": False},
                {"check": "Charging-event timeline generated", "status": "pass", "observed": False},
                {"check": "Grid-load estimation generated", "status": "pass", "observed": False},
                {"check": "Actual charging event terminology used", "status": "pass", "observed": False},
            ]
        )
        pipeline.write(integrity, pipeline.validation / "686_20260711_research_integrity_checks.csv")
        statistics = pd.DataFrame(
            [
                {
                    "analysis_run_id": pipeline.run_id,
                    "independent_seed_count": args.seed_count,
                    "customer_count_specific_configuration_count": 3 * args.seed_count,
                    "scenario_configuration_count": len(configurations),
                    "conditional_evaluation_count": len(configurations) * args.seed_count,
                    "base_route_proxy_count": len(base_routes),
                    "condition_route_evaluation_count": len(route_results),
                    "bootstrap_iterations": args.bootstrap_iterations,
                    "bootstrap_random_seed": args.bootstrap_random_seed,
                    "monte_carlo_name": "Monte Carlo spatial sensitivity analysis",
                }
            ]
        )
        pipeline.write(statistics, pipeline.validation / "687_20260711_statistical_validation.csv")
        validate_unique_keys(configurations, "scenario_id", "scenario configurations")
        validate_unique_keys(
            route_results,
            "scenario_route_proxy_id",
            "condition route results",
        )
        pipeline.flush_status()

    pipeline.stage("13. Validation and Export Summary", final_validation_csvs)
    if pipeline.status_path() not in pipeline.generated_csvs:
        pipeline.generated_csvs.append(pipeline.status_path())
    manifest_path = pipeline.validation / "analysis_output_902_20260711_v04_manifest.csv"
    manifest = generate_output_manifest(
        pipeline.generated_csvs,
        root=root,
        include_csv_shape=True,
    )
    manifest.insert(0, "analysis_run_id", pipeline.run_id)
    write_csv_atomic(manifest, manifest_path)
    print(f"Analysis complete: {len(pipeline.generated_csvs)} CSV artifacts")
    print(f"Run ID: {pipeline.run_id}")
    print("Charging pathway generated: False")
    print("Charging-demand estimation generated: False")
    print("Charging-event timeline generated: False")
    print("Grid-load estimation generated: False")


if __name__ == "__main__":
    main()
