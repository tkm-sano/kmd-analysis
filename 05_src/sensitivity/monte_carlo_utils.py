"""Monte Carlo, bootstrap, and sensitivity utilities for route-proxy results."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd


CONSTRAINT_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "constraint_name": "Payload capacity",
        "feasible_column": "payload_feasible",
        "evaluated_column": "__always__",
        "numerator_definition": "Routes whose synthetic route demand exceeds the vehicle payload capacity",
        "denominator_definition": "All route proxies with complete synthetic demand and vehicle payload data",
        "main_assumption": "Synthetic discrete-uniform customer demand and one manufacturer-specification vehicle",
        "evidence_status": "Synthetic data with assumed parameters",
    },
    {
        "constraint_name": "Operating-time limit",
        "feasible_column": "operating_time_feasible",
        "evaluated_column": "__always__",
        "numerator_definition": "Route proxies whose travel plus service duration exceeds the operating-time limit",
        "denominator_definition": "All route proxies with distance, speed, service time, and operating-limit values",
        "main_assumption": "Haversine distance with road multiplier, assumed speed, synthetic service time; no waiting/detour/charging event",
        "evidence_status": "Synthetic route proxy with assumed parameters",
    },
    {
        "constraint_name": "Range feasibility",
        "feasible_column": "range_feasible",
        "evaluated_column": "__always__",
        "numerator_definition": "Route proxies whose estimated distance exceeds usable range",
        "denominator_definition": "All route proxies with route-proxy distance and usable-range values",
        "main_assumption": "Nominal range multiplied by initial-minus-reserve SOC ratio; no SOC trajectory",
        "evidence_status": "Manufacturer range with assumed usable ratio and route proxy",
    },
    {
        "constraint_name": "SOC feasibility",
        "feasible_column": "soc_feasible",
        "evaluated_column": "__never__",
        "numerator_definition": "Not evaluated",
        "denominator_definition": "Not evaluated",
        "main_assumption": "A sequential SOC trajectory and charger-arrival SOC are not modeled",
        "evidence_status": "Not evaluated",
    },
    {
        "constraint_name": "Charging-station access",
        "feasible_column": "charger_geographically_accessible",
        "evaluated_column": "__always__",
        "numerator_definition": "Route proxies with no retained candidate within the condition-specific geographic threshold",
        "denominator_definition": "All route proxies under each charger condition",
        "main_assumption": "Distance from any route-proxy node to a screened OCM candidate; actual public availability is unknown",
        "evidence_status": "Public candidate geography with substantial attribute missingness",
    },
    {
        "constraint_name": "Charging-assisted range feasibility",
        "feasible_column": "charging_assisted_range_feasible",
        "evaluated_column": "charging_assisted_range_evaluated",
        "numerator_definition": "Range-infeasible route proxies not supportable under the simplified two-usable-range and geographic-access rule",
        "denominator_definition": "Only route proxies that exceed usable range",
        "main_assumption": "Simplified geographic range-support proxy; charger-arrival SOC and actual stop choice are not evaluated",
        "evidence_status": "Simplified proxy with public candidate geography",
    },
    {
        "constraint_name": "Charging-duration feasibility",
        "feasible_column": "charging_duration_feasible",
        "evaluated_column": "charging_duration_evaluated",
        "numerator_definition": "Evaluable range-infeasible route proxies whose constant-power supplemental-duration proxy exceeds the threshold",
        "denominator_definition": "Only range-infeasible route proxies with an accessible compatible candidate and known positive power",
        "main_assumption": "Constant reported power; no taper, efficiency loss, queue, operating hours, or event timing",
        "evidence_status": "Simplified duration proxy; actual charging behavior not evaluated",
    },
)


def build_constraint_evaluations(route_results: pd.DataFrame) -> pd.DataFrame:
    """Convert wide route results to auditable long constraint evaluations."""

    required_keys = [
        "scenario_id",
        "scenario_route_proxy_id",
        "seed",
        "customer_count",
        "vehicle_count",
        "charger_condition",
    ]
    missing = sorted(set(required_keys) - set(route_results.columns))
    if missing:
        raise ValueError(f"Route results are missing constraint keys: {missing}.")
    frames: list[pd.DataFrame] = []
    for definition in CONSTRAINT_DEFINITIONS:
        feasible_column = definition["feasible_column"]
        if feasible_column not in route_results.columns:
            raise ValueError(f"Route results are missing feasibility column {feasible_column!r}.")
        frame = route_results[required_keys].copy()
        evaluated_column = definition["evaluated_column"]
        if evaluated_column == "__always__":
            frame["evaluated"] = route_results[feasible_column].notna()
        elif evaluated_column == "__never__":
            frame["evaluated"] = False
        else:
            if evaluated_column not in route_results.columns:
                raise ValueError(f"Route results are missing evaluation column {evaluated_column!r}.")
            frame["evaluated"] = route_results[evaluated_column].fillna(False).astype(bool)
        raw_feasible = route_results[feasible_column]
        if evaluated_column == "__never__":
            frame["feasible"] = pd.array([pd.NA] * len(frame), dtype="boolean")
        else:
            frame["feasible"] = pd.array(raw_feasible, dtype="boolean")
        frame.loc[~frame["evaluated"], "feasible"] = pd.NA
        frame["unmet"] = pd.array(~frame["feasible"], dtype="boolean")
        frame.loc[~frame["evaluated"], "unmet"] = pd.NA
        frame["constraint_name"] = definition["constraint_name"]
        frame["numerator_definition"] = definition["numerator_definition"]
        frame["denominator_definition"] = definition["denominator_definition"]
        frame["main_assumption"] = definition["main_assumption"]
        frame["evidence_status"] = definition["evidence_status"]
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    return result


def build_case_rates(constraint_evaluations: pd.DataFrame) -> pd.DataFrame:
    """Calculate one unmet rate per scenario/seed conditional case."""

    keys = [
        "scenario_id",
        "seed",
        "customer_count",
        "vehicle_count",
        "charger_condition",
        "constraint_name",
    ]
    rows: list[dict[str, object]] = []
    for key, group in constraint_evaluations.groupby(keys, dropna=False, sort=False):
        evaluated = group["evaluated"].astype(bool)
        evaluated_count = int(evaluated.sum())
        unmet_count = int(group.loc[evaluated, "unmet"].fillna(False).astype(bool).sum())
        row = dict(zip(keys, key))
        row.update(
            {
                "evaluated_route_count": evaluated_count,
                "unmet_route_count": unmet_count,
                "case_unmet_rate": unmet_count / evaluated_count if evaluated_count else np.nan,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _bootstrap_ratios(
    seed_counts: pd.DataFrame,
    iterations: int,
    random_seed: int,
) -> np.ndarray:
    seed_values = seed_counts.index.to_numpy()
    if len(seed_values) == 0 or seed_counts["evaluated"].sum() == 0:
        return np.array([], dtype=float)
    rng = np.random.default_rng(random_seed)
    output = np.empty(iterations, dtype=float)
    for index in range(iterations):
        sample = rng.choice(seed_values, size=len(seed_values), replace=True)
        selected = seed_counts.loc[sample]
        denominator = float(selected["evaluated"].sum())
        output[index] = float(selected["unmet"].sum()) / denominator if denominator else np.nan
    return output[np.isfinite(output)]


def cluster_bootstrap_constraint_summary(
    constraint_evaluations: pd.DataFrame,
    case_rates: pd.DataFrame,
    iterations: int = 1000,
    random_seed: int = 20260711,
    spatial_threshold_low: float = 0.05,
    spatial_threshold_high: float = 0.15,
) -> pd.DataFrame:
    """Summarize constraints with seed-cluster bootstrap confidence intervals.

    Seed identifiers are sampled with replacement.  Every conditional case
    and route belonging to a sampled seed is retained, preserving paired
    comparisons across experimental conditions.
    """

    if iterations < 1000:
        raise ValueError("bootstrap iterations must be at least 1000.")
    rows: list[dict[str, object]] = []
    definitions = {item["constraint_name"]: item for item in CONSTRAINT_DEFINITIONS}
    for position, constraint_name in enumerate(definitions):
        group = constraint_evaluations[
            constraint_evaluations["constraint_name"].eq(constraint_name)
        ]
        evaluated_group = group[group["evaluated"].astype(bool)].copy()
        evaluated_count = int(len(evaluated_group))
        unmet_count = int(evaluated_group["unmet"].fillna(False).astype(bool).sum())
        route_rate = unmet_count / evaluated_count if evaluated_count else np.nan
        case_group = case_rates[
            case_rates["constraint_name"].eq(constraint_name)
            & case_rates["case_unmet_rate"].notna()
        ]
        case_rate = float(case_group["case_unmet_rate"].mean()) if len(case_group) else np.nan
        seed_counts = (
            group.assign(
                evaluated_int=group["evaluated"].astype(int),
                unmet_int=group["unmet"].fillna(False).astype(int),
            )
            .groupby("seed")[["evaluated_int", "unmet_int"]]
            .sum()
            .rename(columns={"evaluated_int": "evaluated", "unmet_int": "unmet"})
        )
        seed_rates = seed_counts["unmet"].div(seed_counts["evaluated"].replace(0, np.nan)).dropna()
        bootstrap = _bootstrap_ratios(seed_counts, iterations, random_seed + position)
        ci_low = float(np.quantile(bootstrap, 0.025)) if len(bootstrap) else np.nan
        ci_high = float(np.quantile(bootstrap, 0.975)) if len(bootstrap) else np.nan
        standard_deviation = float(seed_rates.std(ddof=1)) if len(seed_rates) > 1 else np.nan
        if np.isnan(standard_deviation):
            sensitivity = "Not assessable"
        elif standard_deviation < spatial_threshold_low:
            sensitivity = "Low"
        elif standard_deviation < spatial_threshold_high:
            sensitivity = "Medium"
        else:
            sensitivity = "High"
        if np.isnan(route_rate):
            interpretation = "Not evaluated under the current model."
        else:
            level = "high" if route_rate >= 0.50 else "low"
            variability = "large" if sensitivity == "High" else "limited-to-moderate"
            interpretation = (
                f"{level.capitalize()} unmet rate with {variability} seed-level variation under the current "
                "synthetic assumptions; this is not an observed delivery failure rate."
            )
        definition = definitions[constraint_name]
        rows.append(
            {
                "constraint_name": constraint_name,
                "route_weighted_unmet_rate": route_rate,
                "case_weighted_unmet_rate": case_rate,
                "mean_unmet_rate_across_seeds": float(seed_rates.mean()) if len(seed_rates) else np.nan,
                "standard_deviation": standard_deviation,
                "median": float(seed_rates.median()) if len(seed_rates) else np.nan,
                "interquartile_range": float(seed_rates.quantile(0.75) - seed_rates.quantile(0.25)) if len(seed_rates) else np.nan,
                "minimum": float(seed_rates.min()) if len(seed_rates) else np.nan,
                "maximum": float(seed_rates.max()) if len(seed_rates) else np.nan,
                "confidence_interval_lower": ci_low,
                "confidence_interval_upper": ci_high,
                "evaluated_route_count": evaluated_count,
                "unmet_route_count": unmet_count,
                "independent_seed_count": int(group["seed"].nunique()),
                "conditional_evaluation_count": int(
                    case_rates[case_rates["constraint_name"].eq(constraint_name)][
                        ["scenario_id", "seed"]
                    ].drop_duplicates().shape[0]
                ),
                "bootstrap_iterations": int(iterations),
                "bootstrap_random_seed": int(random_seed),
                "spatial_sensitivity": sensitivity,
                "interpretation": interpretation,
                "main_assumption": definition["main_assumption"],
                "evidence_status": definition["evidence_status"],
                "numerator_definition": definition["numerator_definition"],
                "denominator_definition": definition["denominator_definition"],
            }
        )
    return pd.DataFrame(rows)


def scenario_specific_constraint_summary(
    constraint_evaluations: pd.DataFrame,
    iterations: int = 1000,
    random_seed: int = 20260711,
) -> pd.DataFrame:
    """Calculate route-weighted seed-bootstrap intervals for every scenario."""

    rows: list[dict[str, object]] = []
    group_columns = [
        "scenario_id",
        "customer_count",
        "vehicle_count",
        "charger_condition",
        "constraint_name",
    ]
    for position, (key, group) in enumerate(
        constraint_evaluations.groupby(group_columns, dropna=False, sort=False)
    ):
        evaluated = group[group["evaluated"].astype(bool)].copy()
        evaluated_count = len(evaluated)
        unmet_count = int(evaluated["unmet"].fillna(False).astype(bool).sum())
        seed_counts = (
            group.assign(
                evaluated_int=group["evaluated"].astype(int),
                unmet_int=group["unmet"].fillna(False).astype(int),
            )
            .groupby("seed")[["evaluated_int", "unmet_int"]]
            .sum()
            .rename(columns={"evaluated_int": "evaluated", "unmet_int": "unmet"})
        )
        bootstrap = _bootstrap_ratios(seed_counts, iterations, random_seed + position)
        row = dict(zip(group_columns, key))
        row.update(
            {
                "route_weighted_unmet_rate": unmet_count / evaluated_count if evaluated_count else np.nan,
                "confidence_interval_lower": float(np.quantile(bootstrap, 0.025)) if len(bootstrap) else np.nan,
                "confidence_interval_upper": float(np.quantile(bootstrap, 0.975)) if len(bootstrap) else np.nan,
                "evaluated_route_count": int(evaluated_count),
                "unmet_route_count": int(unmet_count),
                "independent_seed_count": int(group["seed"].nunique()),
                "bootstrap_iterations": int(iterations),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _parameter_values(parameters: pd.DataFrame, name: str) -> dict[str, float]:
    selected = parameters[parameters["parameter"].eq(name)]
    if len(selected) != 1:
        raise ValueError(f"Expected exactly one sensitivity parameter row for {name!r}.")
    row = selected.iloc[0]
    return {level: float(row[level]) for level in ("low", "base", "high")}


def run_oat_sensitivity(
    route_results: pd.DataFrame,
    parameters: pd.DataFrame,
    baseline_vehicle: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run three-level one-at-a-time sensitivity on paired route proxies.

    Except for customer-count and vehicle-count levers, the reference subset
    is C=50, V=3, balanced charger policy.  These are exploratory assumption
    tests, not calibrated operational response estimates.
    """

    parameter_names = [
        "assumed_speed_kmh",
        "road_distance_multiplier",
        "service_time_per_customer_min",
        "operating_time_limit_min",
        "vehicle_count",
        "customer_count",
        "usable_battery_ratio",
        "reserve_soc_ratio",
        "vehicle_payload_capacity_kg",
        "customer_demand_scale",
        "charger_power_kw",
        "charging_time_limit_min",
        "maximum_charger_access_distance_km",
    ]
    base_values = {name: _parameter_values(parameters, name)["base"] for name in parameter_names}
    base_initial_soc = float(
        parameters.loc[parameters["parameter"].eq("initial_soc_ratio"), "base"].iloc[0]
    )
    battery_capacity = float(baseline_vehicle["battery_kwh"])
    nominal_range = float(baseline_vehicle["catalog_range_km"])
    energy_per_km = float(baseline_vehicle["energy_consumption_kwh_per_km"])

    results: list[dict[str, object]] = []
    balanced = route_results[route_results["charger_condition"].eq("balanced")].copy()
    for parameter_position, parameter in enumerate(parameter_names):
        levels = _parameter_values(parameters, parameter)
        for level_name, level_value in levels.items():
            values = dict(base_values)
            values[parameter] = level_value
            customer_count = int(values["customer_count"])
            vehicle_count = int(values["vehicle_count"])
            subset = balanced[
                balanced["customer_count"].eq(customer_count)
                & balanced["vehicle_count"].eq(vehicle_count)
            ].copy()
            if subset.empty:
                raise ValueError(
                    f"No paired sensitivity routes for customer_count={customer_count}, vehicle_count={vehicle_count}."
                )
            road_distance = subset["haversine_distance_km"].astype(float) * values[
                "road_distance_multiplier"
            ]
            demand = subset["route_total_demand_kg"].astype(float) * values[
                "customer_demand_scale"
            ]
            if parameter == "service_time_per_customer_min":
                service = subset["customer_count_on_route"].astype(float) * level_value
            else:
                service = subset["service_time_total_min"].astype(float)
            travel = road_distance / values["assumed_speed_kmh"] * 60.0
            operating_feasible = travel + service <= values["operating_time_limit_min"]
            payload_feasible = demand <= values["vehicle_payload_capacity_kg"]
            if parameter == "reserve_soc_ratio":
                usable_ratio = base_initial_soc - level_value
            else:
                usable_ratio = values["usable_battery_ratio"]
            usable_range = nominal_range * usable_ratio
            usable_energy = battery_capacity * usable_ratio
            range_feasible = road_distance <= usable_range
            nearest_distance = (
                subset["nearest_charger_haversine_distance_km"].astype(float)
                * values["road_distance_multiplier"]
            )
            assistance_distance = (
                subset["assistance_candidate_distance_km"].astype(float)
                / base_values["road_distance_multiplier"]
                * values["road_distance_multiplier"]
            )
            charger_access = nearest_distance <= values["maximum_charger_access_distance_km"]
            assistance_access = assistance_distance <= values[
                "maximum_charger_access_distance_km"
            ]
            required = ~range_feasible
            assisted = assistance_access & (road_distance <= 2.0 * usable_range)
            estimated_energy = road_distance * energy_per_km
            supplemental = (estimated_energy - usable_energy).clip(lower=0)
            if parameter == "charger_power_kw":
                power = pd.Series(level_value, index=subset.index, dtype=float)
            else:
                power = subset["assistance_candidate_power_kw"].astype(float)
            duration = supplemental / power * 60.0
            duration_evaluated = required & assistance_access & power.gt(0) & power.notna()
            duration_feasible = duration <= values["charging_time_limit_min"]

            constraint_vectors: Mapping[str, tuple[pd.Series, pd.Series]] = {
                "Payload capacity": (pd.Series(True, index=subset.index), payload_feasible),
                "Operating-time limit": (pd.Series(True, index=subset.index), operating_feasible),
                "Range feasibility": (pd.Series(True, index=subset.index), range_feasible),
                "Charging-station access": (pd.Series(True, index=subset.index), charger_access),
                "Charging-assisted range feasibility": (required, assisted),
                "Charging-duration feasibility": (duration_evaluated, duration_feasible),
            }
            for constraint_name, (evaluated, feasible) in constraint_vectors.items():
                evaluated = evaluated.fillna(False).astype(bool)
                evaluated_count = int(evaluated.sum())
                unmet_count = int((~feasible.fillna(False).astype(bool) & evaluated).sum())
                results.append(
                    {
                        "parameter": parameter,
                        "level": level_name,
                        "parameter_value": float(level_value),
                        "constraint_name": constraint_name,
                        "route_weighted_unmet_rate": unmet_count / evaluated_count
                        if evaluated_count
                        else np.nan,
                        "evaluated_route_count": evaluated_count,
                        "unmet_route_count": unmet_count,
                        "customer_count_for_evaluation": customer_count,
                        "vehicle_count_for_evaluation": vehicle_count,
                        "charger_condition_for_evaluation": "balanced",
                        "independent_seed_count": int(subset["seed"].nunique()),
                        "sensitivity_design": "Three-level one-at-a-time paired-seed analysis",
                        "evidence_status": "Exploratory parameter sensitivity; not calibrated operational evidence",
                    }
                )
    summary = pd.DataFrame(results)
    base = summary[summary["level"].eq("base")][
        ["parameter", "constraint_name", "route_weighted_unmet_rate"]
    ].rename(columns={"route_weighted_unmet_rate": "base_unmet_rate"})
    summary = summary.merge(base, on=["parameter", "constraint_name"], how="left")
    summary["unmet_rate_change_from_base"] = (
        summary["route_weighted_unmet_rate"] - summary["base_unmet_rate"]
    )
    response = (
        summary.groupby(["parameter", "constraint_name"], as_index=False)
        .agg(
            low_unmet_rate=(
                "route_weighted_unmet_rate",
                lambda values: float(values.iloc[0]) if len(values) else np.nan,
            ),
            minimum_unmet_rate=("route_weighted_unmet_rate", "min"),
            maximum_unmet_rate=("route_weighted_unmet_rate", "max"),
            maximum_absolute_change_from_base=(
                "unmet_rate_change_from_base",
                lambda values: float(np.nanmax(np.abs(values))) if np.isfinite(values).any() else np.nan,
            ),
        )
    )
    return summary, response


def build_time_constraint_diagnostics(sensitivity: pd.DataFrame) -> pd.DataFrame:
    """Build a transparent factor/impact table for operating-time feasibility."""

    labels = {
        "assumed_speed_kmh": "Assumed travel speed",
        "road_distance_multiplier": "Road-distance multiplier",
        "service_time_per_customer_min": "Service time per customer",
        "operating_time_limit_min": "Operating-time limit",
        "vehicle_count": "Vehicle count",
        "customer_count": "Customer count",
    }
    rows: list[dict[str, object]] = []
    operating = sensitivity[
        sensitivity["constraint_name"].eq("Operating-time limit")
    ]
    for parameter, label in labels.items():
        group = operating[operating["parameter"].eq(parameter)]
        if group.empty:
            continue
        values = {row.level: row for row in group.itertuples(index=False)}
        rows.append(
            {
                "factor": label,
                "parameter": parameter,
                "baseline_value": values["base"].parameter_value,
                "sensitivity_range": f"{values['low'].parameter_value:g}-{values['high'].parameter_value:g}",
                "unmet_rate_impact": float(
                    group["route_weighted_unmet_rate"].max()
                    - group["route_weighted_unmet_rate"].min()
                ),
                "interpretation": "Exploratory one-at-a-time effect under the route-proxy model",
            }
        )
    rows.extend(
        [
            {
                "factor": "Route-proxy inefficiency",
                "parameter": "route_generation_method",
                "baseline_value": "KMeans + nearest neighbor",
                "sensitivity_range": "Alternative route generators not evaluated",
                "unmet_rate_impact": np.nan,
                "interpretation": "Not quantified; route proxy is not an optimized EVRP solution.",
            },
            {
                "factor": "Supplemental charging duration",
                "parameter": "charging_time_total_min",
                "baseline_value": 0,
                "sensitivity_range": "Not included in operating-time constraint",
                "unmet_rate_impact": np.nan,
                "interpretation": "Evaluated separately as a duration proxy; no charging event is assumed.",
            },
            {
                "factor": "Waiting and charger detour time",
                "parameter": "waiting_time_total_min/detour_time_min",
                "baseline_value": 0,
                "sensitivity_range": "Not modeled",
                "unmet_rate_impact": np.nan,
                "interpretation": "Data unavailable; zero is a model boundary, not evidence of no waiting or detour.",
            },
        ]
    )
    return pd.DataFrame(rows)


def build_payload_diagnostics(
    customers: pd.DataFrame,
    route_results: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize demand and payload utilization without over-interpreting zero unmet."""

    unique_routes = route_results.drop_duplicates("base_route_proxy_id")
    return pd.DataFrame(
        [
            {
                "customer_demand_distribution": "Discrete uniform integer 5-30 kg (synthetic)",
                "customer_demand_min_kg": float(customers["demand_kg"].min()),
                "customer_demand_max_kg": float(customers["demand_kg"].max()),
                "customer_demand_mean_kg": float(customers["demand_kg"].mean()),
                "customer_demand_standard_deviation_kg": float(
                    customers["demand_kg"].std(ddof=1)
                ),
                "route_demand_mean_kg": float(unique_routes["route_total_demand_kg"].mean()),
                "route_demand_max_kg": float(unique_routes["route_total_demand_kg"].max()),
                "vehicle_payload_capacity_kg": float(
                    unique_routes["vehicle_payload_capacity_kg"].iloc[0]
                ),
                "maximum_payload_utilization_ratio": float(
                    unique_routes["payload_utilization_ratio"].max()
                ),
                "percentile_95_payload_utilization_ratio": float(
                    unique_routes["payload_utilization_ratio"].quantile(0.95)
                ),
                "evidence_status": "Synthetic data with assumed parameters",
                "interpretation_caution": "A zero unmet rate would mean only that this synthetic demand did not exceed the configured capacity.",
            }
        ]
    )
