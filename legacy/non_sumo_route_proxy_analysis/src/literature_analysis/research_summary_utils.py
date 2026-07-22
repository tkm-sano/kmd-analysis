"""Research-summary and evidence-gap table builders for the EVRP notebook."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


GAP_ITEM_TO_CONSTRAINT: Mapping[str, str] = {
    "Capacity": "Payload capacity",
    "Time windows": "Operating-time limit",
    "Battery/SOC": "Range feasibility",
    "Charging stations": "Charging-station access",
    "Charging duration": "Charging-duration feasibility",
}


def _require_columns(frame: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}.")


def build_scenario_design_table(configurations: pd.DataFrame) -> pd.DataFrame:
    """Build Table 1: factorial experimental conditions and paired-seed counts."""

    required = {
        "scenario_id",
        "scenario_size",
        "customer_count",
        "vehicle_count",
        "customers_per_vehicle",
        "independent_seed_count",
        "conditional_case_count",
        "charger_condition",
        "eligible_charger_candidate_count",
        "selected_charger_count",
        "vehicle_type",
        "payload_capacity_kg",
        "usable_range_km",
        "operating_time_limit_min",
        "assumed_speed_kmh",
        "road_distance_multiplier",
        "route_generation_method",
        "customer_demand_source",
    }
    _require_columns(configurations, required, "scenario configurations")
    columns = [
        "scenario_id",
        "scenario_size",
        "customer_count",
        "vehicle_count",
        "customers_per_vehicle",
        "independent_seed_count",
        "conditional_case_count",
        "charger_condition",
        "eligible_charger_candidate_count",
        "selected_charger_count",
        "vehicle_type",
        "payload_capacity_kg",
        "usable_range_km",
        "operating_time_limit_min",
        "assumed_speed_kmh",
        "road_distance_multiplier",
        "route_generation_method",
        "customer_demand_source",
    ]
    result = configurations[columns].copy()
    result["factorial_design_note"] = (
        "Customer count and vehicle count are crossed independently (3 x 3); charger condition is a third factor."
    )
    return result.sort_values(
        ["customer_count", "vehicle_count", "charger_condition"]
    ).reset_index(drop=True)


def build_constraint_variability_table(constraint_summary: pd.DataFrame) -> pd.DataFrame:
    """Build Table 2 without converting non-evaluated constraints to zero."""

    required = {
        "constraint_name",
        "route_weighted_unmet_rate",
        "case_weighted_unmet_rate",
        "standard_deviation",
        "median",
        "interquartile_range",
        "minimum",
        "maximum",
        "confidence_interval_lower",
        "confidence_interval_upper",
        "evaluated_route_count",
        "unmet_route_count",
        "independent_seed_count",
        "spatial_sensitivity",
        "interpretation",
        "main_assumption",
        "evidence_status",
    }
    _require_columns(constraint_summary, required, "constraint summary")
    result = constraint_summary.copy()
    result["confidence_interval"] = result.apply(
        lambda row: (
            f"{row.confidence_interval_lower:.6f}-{row.confidence_interval_upper:.6f}"
            if pd.notna(row.confidence_interval_lower)
            and pd.notna(row.confidence_interval_upper)
            else "Not evaluated"
        ),
        axis=1,
    )
    result["payload_zero_caution"] = np.where(
        result["constraint_name"].eq("Payload capacity")
        & result["route_weighted_unmet_rate"].eq(0),
        "A 0% result means only that configured synthetic demand did not exceed configured payload; it is not evidence that payload is non-binding in Tokyo operations.",
        "",
    )
    return result


def build_quantum_vrp_gap_detail(
    evidence: pd.DataFrame,
    configurations: pd.DataFrame,
    constraint_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Create a conservative requirement-by-evidence comparison.

    The comparison is limited to the supplied evidence registry.  A missing
    report is never inferred as a numerical zero or as proof of absence from
    the wider literature.
    """

    coverage_columns = {
        "Customer scale": "customer_scale_coverage",
        "Multiple vehicles": "multiple_vehicle_coverage",
        "Capacity": "capacity_coverage",
        "Time windows": "time_window_coverage",
        "Battery/SOC": "battery_soc_coverage",
        "Charging stations": "charging_station_coverage",
        "Charging duration": "charging_duration_coverage",
        "Multi-depot": "multi_depot_coverage",
        "Heterogeneous vehicles": "heterogeneous_vehicle_coverage",
        "Dynamic demand": "dynamic_demand_coverage",
        "Traffic": "traffic_coverage",
        "Driver hours": "driver_hours_coverage",
    }
    _require_columns(
        evidence,
        {
            "reference_id",
            "paper_title",
            "authors",
            "year",
            "doi",
            "url",
            "page_or_section",
            "customer_count",
            "vehicle_count",
            "execution_type",
            "classical_baseline",
            "runtime",
            "solution_quality",
            *coverage_columns.values(),
        },
        "quantum evidence registry",
    )
    route_rate = constraint_summary.set_index("constraint_name")[
        "route_weighted_unmet_rate"
    ].to_dict()
    customer_levels = sorted(configurations["customer_count"].unique())
    vehicle_levels = sorted(configurations["vehicle_count"].unique())
    requirements: dict[str, str] = {
        "Customer scale": f"Factorial levels {customer_levels}; route-proxy analysis only",
        "Multiple vehicles": f"Factorial levels {vehicle_levels}; KMeans assignment proxy",
        "Capacity": "Route demand must not exceed one coherent vehicle payload specification",
        "Time windows": "Operating-time limit evaluated; visit-level time windows Not evaluated",
        "Battery/SOC": "Range threshold evaluated; sequential SOC feasibility Not evaluated",
        "Charging stations": "Geographic candidate access evaluated; actual public availability Not evaluated",
        "Charging duration": "Constant-power duration proxy evaluated only for eligible range-infeasible routes",
        "Multi-depot": "Many depot candidates available but exactly one proxy depot selected per customer configuration",
        "Heterogeneous vehicles": "Not evaluated; one coherent vehicle scenario is used",
        "Dynamic demand": "Not evaluated",
        "Traffic": "Not evaluated; assumed constant speed is used",
        "Driver hours": "Not evaluated beyond a route-level operating-time limit",
        "Classical baseline": "No EVRP optimizer baseline; route proxy only",
        "Runtime": "Pipeline runtime recorded; optimization runtime Not applicable",
        "Solution quality": "Not assessable without an optimization objective or classical optimum/bound",
    }
    rows: list[dict[str, object]] = []
    for item, requirement in requirements.items():
        if item in coverage_columns:
            column = coverage_columns[item]
            coverage_text = evidence[column].fillna("Not reported").astype(str)
            reported = evidence[
                ~coverage_text.str.lower().str.startswith("not reported")
                & coverage_text.str.strip().ne("")
            ]
            if reported.empty:
                coverage = "Not reported in the reviewed evidence set"
                representative = "None in the reviewed evidence set"
                reference_ids = "Not reported"
            else:
                coverage = "Reported in at least one reviewed study"
                representative = "; ".join(reported["reference_id"].astype(str))
                reference_ids = representative
        elif item == "Classical baseline":
            reported = evidence[
                ~evidence["classical_baseline"].astype(str).str.startswith("Not reported")
            ]
            coverage = (
                "Reported in at least one reviewed study"
                if not reported.empty
                else "Not reported in the reviewed evidence set"
            )
            representative = "; ".join(reported["reference_id"].astype(str)) or "Not reported"
            reference_ids = representative
        elif item == "Runtime":
            reported = evidence[~evidence["runtime"].astype(str).str.startswith("Not reported")]
            coverage = "Reported" if not reported.empty else "Not reported in the reviewed evidence set"
            representative = "; ".join(reported["reference_id"].astype(str)) or "Not reported"
            reference_ids = representative
        else:
            reported = evidence[
                ~evidence["solution_quality"].astype(str).str.startswith("Not reported")
            ]
            coverage = "Qualitative comparison reported; normalized metric Not reported"
            representative = "; ".join(reported["reference_id"].astype(str)) or "Not reported"
            reference_ids = representative

        mapped_constraint = GAP_ITEM_TO_CONSTRAINT.get(item)
        if mapped_constraint is not None and pd.notna(route_rate.get(mapped_constraint)):
            importance = (
                f"Current route-weighted unmet rate for {mapped_constraint}: "
                f"{float(route_rate[mapped_constraint]):.6f}; interpretation is assumption-dependent"
            )
        elif item == "Customer scale":
            importance = "Directly varied in the factorial design"
        elif item == "Multiple vehicles":
            importance = "Directly varied in the factorial design"
        else:
            importance = "Not evaluated or not directly quantified in the current analysis"

        evaluated_importance = not importance.startswith("Not evaluated")
        coverage_reported = coverage.startswith("Reported") or coverage.startswith("Qualitative")
        if item == "Customer scale":
            gap = "High"
            gap_basis = "Reviewed evidence reports small/ambiguous problem tuples or route counts not comparable to 25-100 customers."
        elif coverage_reported and evaluated_importance:
            gap = "Medium"
            gap_basis = "Some reviewed coverage exists, but operational scale/definition and evidence type do not match directly."
        elif not coverage_reported and evaluated_importance:
            gap = "High"
            gap_basis = "Requirement matters in the synthetic analysis and is not reported in the reviewed evidence set."
        else:
            gap = "Not assessable"
            gap_basis = "Current analysis does not quantify operational importance sufficiently for a gap classification."

        selected_evidence = reported if not reported.empty else evidence.iloc[0:0]
        rows.append(
            {
                "evaluation_item": item,
                "synthetic_evrp_requirement": requirement,
                "requirement_evidence_from_analysis": importance,
                "analysis_importance": importance,
                "quantum_vrp_coverage": coverage,
                "representative_studies": representative,
                "reported_problem_scale": "; ".join(
                    selected_evidence["customer_count"].astype(str).unique()
                )
                or "Not reported",
                "reported_constraint_coverage": "; ".join(
                    selected_evidence.get("constraint_coverage", pd.Series(dtype=str))
                    .astype(str)
                    .unique()
                )
                or "Not reported",
                "quantum_execution_type": "; ".join(
                    selected_evidence["execution_type"].astype(str).unique()
                )
                or "Not reported",
                "classical_baseline_status": "; ".join(
                    selected_evidence["classical_baseline"].astype(str).unique()
                )
                or "Not reported",
                "evidence_level": "; ".join(
                    selected_evidence["execution_type"].astype(str).unique()
                )
                or "Not reported",
                "evidence_gap": gap,
                "gap_basis": gap_basis,
                "interpretation": (
                    "Comparison is limited to the reviewed evidence registry; Not reported is not proof of absence from all literature."
                ),
                "reference_id": reference_ids,
                "paper_title": "; ".join(selected_evidence["paper_title"].astype(str))
                or "Not reported",
                "authors": "; ".join(selected_evidence["authors"].astype(str))
                or "Not reported",
                "year": "; ".join(selected_evidence["year"].astype(str)) or "Not reported",
                "doi": "; ".join(selected_evidence["doi"].astype(str)) or "Not reported",
                "url": "; ".join(selected_evidence["url"].astype(str)) or "Not reported",
                "page_or_section": "; ".join(
                    selected_evidence["page_or_section"].astype(str)
                )
                or "Not reported",
            }
        )
    return pd.DataFrame(rows)


def build_quantum_vrp_gap_table(gap_detail: pd.DataFrame) -> pd.DataFrame:
    """Build Table 3 from paper-row evidence and conservative gap rules."""

    required = {
        "evaluation_item",
        "synthetic_evrp_requirement",
        "analysis_importance",
        "quantum_vrp_coverage",
        "evidence_level",
        "evidence_gap",
        "gap_basis",
    }
    _require_columns(gap_detail, required, "quantum gap detail")
    return gap_detail.copy()


def _parameter_sensitivity_label(
    sensitivity_response: pd.DataFrame, constraint_name: str
) -> tuple[str, float]:
    selected = sensitivity_response[
        sensitivity_response["constraint_name"].eq(constraint_name)
    ]
    if selected.empty or selected["maximum_absolute_change_from_base"].dropna().empty:
        return "Not assessable", np.nan
    maximum = float(selected["maximum_absolute_change_from_base"].max())
    if maximum < 0.05:
        return "Low", maximum
    if maximum < 0.15:
        return "Medium", maximum
    return "High", maximum


def build_integrated_research_summary(
    constraint_summary: pd.DataFrame,
    sensitivity_response: pd.DataFrame,
    gap_detail: pd.DataFrame,
) -> pd.DataFrame:
    """Build Table 4 using transparent ordinal rules rather than a pseudo-score."""

    gap_lookup = gap_detail.set_index("evaluation_item")
    constraint_to_gap = {
        "Payload capacity": "Capacity",
        "Operating-time limit": "Time windows",
        "Range feasibility": "Battery/SOC",
        "SOC feasibility": "Battery/SOC",
        "Charging-station access": "Charging stations",
        "Charging-assisted range feasibility": "Charging stations",
        "Charging-duration feasibility": "Charging duration",
    }
    rows: list[dict[str, object]] = []
    for summary in constraint_summary.itertuples(index=False):
        sensitivity_label, maximum_change = _parameter_sensitivity_label(
            sensitivity_response, summary.constraint_name
        )
        gap_item = constraint_to_gap[summary.constraint_name]
        gap = gap_lookup.loc[gap_item]
        rate = summary.route_weighted_unmet_rate
        if pd.isna(rate):
            priority = "Evidence-dependent"
            interpretation = "Constraint is not evaluated; implementation and evidence are prerequisites to prioritization."
        elif summary.constraint_name == "Payload capacity" and float(rate) == 0.0:
            priority = "Evidence-dependent"
            interpretation = (
                "0% unmet under synthetic demand assumptions; constraint was non-binding only under current assumptions."
            )
        elif (float(rate) >= 0.50 and gap.evidence_gap in {"High", "Medium"}) or (
            sensitivity_label == "High" and gap.evidence_gap == "High"
        ):
            priority = "High"
            interpretation = "Binding or highly assumption-sensitive in the proxy analysis and incompletely covered in reviewed quantum evidence."
        elif float(rate) >= 0.10 or sensitivity_label in {"Medium", "High"} or gap.evidence_gap == "High":
            priority = "Medium"
            interpretation = "Merits further study, but inference remains limited by synthetic inputs and route-proxy assumptions."
        else:
            priority = "Evidence-dependent"
            interpretation = "Currently non-binding or weakly varying; stronger operational evidence is needed before deprioritizing."
        rows.append(
            {
                "constraint_or_requirement": summary.constraint_name,
                "synthetic_scenario_definition": summary.numerator_definition,
                "route_weighted_unmet_rate": rate,
                "confidence_interval": (
                    f"{summary.confidence_interval_lower:.6f}-{summary.confidence_interval_upper:.6f}"
                    if pd.notna(summary.confidence_interval_lower)
                    else "Not evaluated"
                ),
                "spatial_variability": summary.spatial_sensitivity,
                "parameter_sensitivity": sensitivity_label,
                "maximum_parameter_response": maximum_change,
                "main_assumption": summary.main_assumption,
                "evidence_quality": summary.evidence_status,
                "quantum_vrp_coverage": gap.quantum_vrp_coverage,
                "evidence_gap": gap.evidence_gap,
                "research_priority": priority,
                "interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows)


def build_constraint_interpretation_table(
    constraint_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build full and slide versions of Table 5 with valid/invalid claims."""

    content = {
        "Payload capacity": {
            "display_name_ja": "積載量",
            "metric_name": "Route-weighted payload unmet rate",
            "what_high_value_means": "Many route proxies exceed configured vehicle payload under synthetic demand.",
            "what_low_value_means": "Configured synthetic route demand usually remains within configured payload.",
            "valid_interpretation": "現在の需要仮定では積載量制約がどの程度拘束的だったか。",
            "invalid_interpretation": "東京都のEV配送では積載量制約が存在しない。",
        },
        "Operating-time limit": {
            "display_name_ja": "運行時間上限",
            "metric_name": "Route-weighted operating-time unmet rate",
            "what_high_value_means": "Travel plus service duration often exceeds the configured operating limit.",
            "what_low_value_means": "Route proxies usually fit the configured limit under assumed speed/service time.",
            "valid_interpretation": "現在の速度・時間上限・顧客数・route proxyの下で時間制約が拘束した。",
            "invalid_interpretation": "東京都の実配送の同じ割合が時間内に終了しない。",
        },
        "Range feasibility": {
            "display_name_ja": "航続距離",
            "metric_name": "Route-weighted range unmet rate",
            "what_high_value_means": "Many route-proxy distances exceed configured usable range.",
            "what_low_value_means": "Most route-proxy distances fit configured usable range.",
            "valid_interpretation": "現在のvehicle rangeとroute proxyでは途中補完なしで成立しない候補がある。",
            "invalid_interpretation": "実車両が同じ割合で電欠する。",
        },
        "SOC feasibility": {
            "display_name_ja": "SOC",
            "metric_name": "Not evaluated",
            "what_high_value_means": "Not evaluated",
            "what_low_value_means": "Not evaluated",
            "valid_interpretation": "SOC trajectoryは未評価である。",
            "invalid_interpretation": "単純な距離閾値によりSOC feasibleである。",
        },
        "Charging-station access": {
            "display_name_ja": "充電器候補への地理アクセス",
            "metric_name": "Route-weighted geographic candidate-access unmet rate",
            "what_high_value_means": "No screened candidate lies within the configured distance for many route proxies.",
            "what_low_value_means": "A screened geographic candidate is usually within the configured threshold.",
            "valid_interpretation": "設定した地理的・条件的閾値で候補が見つかるか。",
            "invalid_interpretation": "実運用でも確実に充電器を利用できる。",
        },
        "Charging-assisted range feasibility": {
            "display_name_ja": "単純化した充電補完可能性",
            "metric_name": "Unmet rate among range-infeasible route proxies",
            "what_high_value_means": "Simplified geographic/two-range support still fails for many routes needing support.",
            "what_low_value_means": "The simplified support rule covers many routes that exceed direct range.",
            "valid_interpretation": "単純化した充電補完モデルでも解消できない航続距離条件が残る。",
            "invalid_interpretation": "実車両が特定の充電器を特定時刻に利用する。",
        },
        "Charging-duration feasibility": {
            "display_name_ja": "充電時間上限",
            "metric_name": "Unmet rate among duration-evaluable range-infeasible route proxies",
            "what_high_value_means": "Constant-power supplemental-duration proxy often exceeds the configured limit.",
            "what_low_value_means": "The simplified duration proxy often fits the configured limit.",
            "valid_interpretation": "一定出力の単純計算で補完時間が設定上限内か。",
            "invalid_interpretation": "実際の充電時間・待ち時間・充電行動が予測できた。",
        },
    }
    rows: list[dict[str, object]] = []
    for summary in constraint_summary.itertuples(index=False):
        item = content[summary.constraint_name]
        observed = (
            float(summary.route_weighted_unmet_rate)
            if pd.notna(summary.route_weighted_unmet_rate)
            else "Not evaluated"
        )
        rows.append(
            {
                "constraint_name": summary.constraint_name,
                "display_name_ja": item["display_name_ja"],
                "metric_name": item["metric_name"],
                "numerator_definition": summary.numerator_definition,
                "denominator_definition": summary.denominator_definition,
                "observed_value": observed,
                "confidence_interval": (
                    f"{summary.confidence_interval_lower:.6f}-{summary.confidence_interval_upper:.6f}"
                    if pd.notna(summary.confidence_interval_lower)
                    else "Not evaluated"
                ),
                "what_high_value_means": item["what_high_value_means"],
                "what_low_value_means": item["what_low_value_means"],
                "main_assumptions": summary.main_assumption,
                "evidence_status": summary.evidence_status,
                "valid_interpretation": item["valid_interpretation"],
                "invalid_interpretation": item["invalid_interpretation"],
                "recommended_presentation_statement": item["valid_interpretation"],
            }
        )
    full = pd.DataFrame(rows)
    slide = full[
        [
            "display_name_ja",
            "observed_value",
            "valid_interpretation",
            "main_assumptions",
        ]
    ].rename(
        columns={
            "display_name_ja": "constraint",
            "observed_value": "result",
            "valid_interpretation": "what_this_result_shows",
            "main_assumptions": "main_caution",
        }
    )
    return full, slide
