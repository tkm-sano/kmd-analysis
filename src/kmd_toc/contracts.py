"""Small, standalone contracts for the ToC delivery study.

These functions do not generate geographic demand, solve routes, or run circuits.
Unknown configuration fields are rejected at every level.
"""

from fractions import Fraction
import json
import math
from pathlib import Path


class HoldError(ValueError):
    """Required research decisions or source data are unresolved."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _shape(value, schema, path="study"):
    if isinstance(schema, dict):
        if not isinstance(value, dict) or set(value) != set(schema):
            raise ValueError(f"Unexpected or missing fields at {path}")
        for key, child in schema.items():
            _shape(value[key], child, f"{path}.{key}")
    elif isinstance(schema, list):
        if not isinstance(value, list):
            raise ValueError(f"Expected list at {path}")
        for index, child in enumerate(value):
            _shape(child, schema[0], f"{path}[{index}]")
    elif not isinstance(value, schema) or (isinstance(value, bool) and schema is not bool):
        raise ValueError(f"Invalid type at {path}")


_TEXT_OR_NULL = (str, type(None))
_NUMBER_OR_NULL = (int, float, type(None))
_SCHEMA = {
    "schema_version": int, "study_id": str, "status": str, "rq": str,
    "hypothesis": str, "policy_id": str,
    "scope": {"delivery_type": str, "region": str, "depot": str,
              "vehicle_label": str, "depots": int, "trips_per_vehicle": int,
              "customer_time_windows": bool},
    "cases": [{"id": str, "N": int, "vehicles": int, "berths": int}],
    "operations": {"first_loading_ready_s": _NUMBER_OR_NULL,
                   "shift_end_s": _NUMBER_OR_NULL, "loading_duration_s": _NUMBER_OR_NULL,
                   "turnaround_s": _NUMBER_OR_NULL, "capacity_PE_per_trip": _NUMBER_OR_NULL,
                   "service_s_per_stop": _NUMBER_OR_NULL, "empty_trip_policy": _TEXT_OR_NULL},
    "provisional_parameters": [{"name": str, "value": (int, float), "unit": str,
                                "status": str, "source": str}],
    "demand": {"allocation": str, "tie_break": str, "N_meaning": _TEXT_OR_NULL,
               "population": {"source_url": _TEXT_OR_NULL, "statistical_date": _TEXT_OR_NULL,
                              "table": _TEXT_OR_NULL, "sha256": _TEXT_OR_NULL},
               "geography": {"boundary_path": _TEXT_OR_NULL, "boundary_sha256": _TEXT_OR_NULL,
                             "crs": _TEXT_OR_NULL, "crosswalk_56_path": _TEXT_OR_NULL,
                             "crosswalk_56_sha256": _TEXT_OR_NULL},
               "residential_candidates_path": _TEXT_OR_NULL,
               "customer_order_stop_rule": _TEXT_OR_NULL, "PE_rule": _TEXT_OR_NULL,
               "sampling_rule": _TEXT_OR_NULL, "input_seeds": [int],
               "road_matrix_manifest": _TEXT_OR_NULL},
    "comparisons": {"A": str, "B": str, "C": str, "D": str,
                    "D_classical_control": str,
                    "solver_seeds": [int], "repetitions": (int, type(None)),
                    "candidate_selection_rule": _TEXT_OR_NULL,
                    "subproblem_rule": _TEXT_OR_NULL, "subproblem_size": (int, type(None))},
    "metrics": {"D": str, "W": str, "W_total": str, "W_loading": str, "W_unloading": str, "comparison": str},
    "figures": {"count": int, "panels": [str], "colors": {"A": str, "B": str,
                "C": str, "D": str}, "no_results": str},
}


def load_study(path):
    """Load a strict specification, allowing explicit unresolved null values."""
    data = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    _shape(data, _SCHEMA)
    if (data["schema_version"], data["study_id"], data["status"]) != (
            3, "ota_toc_two_trip", "SPECIFIED_WITH_HOLDS"):
        raise ValueError("Unsupported study identity/version/status")
    from .cargo_wait_v2.policy import POLICY_ID, RQ, HYPOTHESIS
    if (data['policy_id'], data['rq'], data['hypothesis']) != (POLICY_ID, RQ, HYPOTHESIS):
        raise ValueError("Research policy/RQ/hypothesis differs from the adopted specification")
    if data["scope"] != {"delivery_type": "ToC", "region": "東京都大田区",
                         "depot": "京浜トラックターミナルを起点とする仮想拠点",
                         "vehicle_label": "配送車両", "depots": 1,
                         "trips_per_vehicle": 2, "customer_time_windows": False}:
        raise ValueError("Study scope differs from the adopted specification")
    cases = [(x["id"], x["N"], x["vehicles"], x["berths"]) for x in data["cases"]]
    if cases != [("S1", 1000, 10, 2), ("S2", 2000, 20, 4), ("S3", 4000, 40, 8)]:
        raise ValueError("Unexpected study cases")
    if data["demand"]["allocation"] != "largest_remainder_population_share":
        raise ValueError("Unexpected allocation rule")
    if data["demand"]["tie_break"] != "region_id_ascending":
        raise ValueError("Unexpected tie rule")
    if data["demand"]["N_meaning"] not in (None, "customers", "unique_visit_stops"):
        raise ValueError("Unsupported N meaning")
    for name, value in data["operations"].items():
        if isinstance(value, (int, float)) and (not math.isfinite(value) or value < 0):
            raise ValueError(f"Invalid operation value: {name}")
    allowed = {"capacity_PE_per_trip", "service_s_per_stop",
               "loading_duration_s", "first_loading_ready_s"}
    for item in data["provisional_parameters"]:
        if (item["name"] not in allowed or item["status"] != "HOLD_NOT_ADOPTED"
                or not math.isfinite(item["value"]) or item["value"] < 0):
            raise ValueError("Invalid provisional parameter")
    expected_metrics = {"D": "total_distance_km", "W": "mean_cargo_wait_min_per_operation",
                        "W_total": "total_cargo_wait_min", "W_loading": "loading_cargo_wait_min",
                        "W_unloading": "unloading_cargo_wait_min",
                        "comparison": "direct_BCD_and_separate_external_A_levels"}
    if data["metrics"] != expected_metrics:
        raise ValueError("Unexpected metric boundary")
    if (data["figures"]["count"] != 4 or data["figures"]["panels"] != ["S1", "S2", "S3"]
            or data["figures"]["no_results"] != "DO_NOT_GENERATE"):
        raise ValueError("Unexpected figure contract")
    return data


def require_ready(study):
    """Fail closed: the current specification does not authorize experiments.

    Removing this gate requires a reviewed runnable schema, provenance/hash
    verification, and resolved decisions; filling a few nulls is insufficient.
    """
    raise HoldError("H01-H09: study execution is HOLD; use the decision register")


def allocate_customers(populations, total):
    """Hamilton allocation with exact fractions and stable region-ID ties.

    Low-level arithmetic only: callers must first verify the population sources,
    boundaries and counting unit. Zero population receives zero customers.
    """
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("total must be a nonnegative integer")
    if not populations or any(not isinstance(k, str) or not k for k in populations):
        raise ValueError("Nonempty string region IDs are required")
    weights = {}
    for key, value in populations.items():
        if isinstance(value, bool):
            raise ValueError("Invalid population")
        try:
            weight = Fraction(str(value))
        except (ValueError, ZeroDivisionError, TypeError) as exc:
            raise ValueError("Population must be finite and nonnegative") from exc
        if weight < 0:
            raise ValueError("Population must be nonnegative")
        weights[key] = weight
    denominator = sum(weights.values())
    if denominator <= 0:
        raise ValueError("Population sum must be positive")
    quotas = {key: total * weights[key] / denominator for key in sorted(weights)}
    result = {key: q.numerator // q.denominator for key, q in quotas.items()}
    order = sorted(quotas, key=lambda key: (-(quotas[key] - result[key]), key))
    for key in order[:total - sum(result.values())]:
        result[key] += 1
    return result


def compare_objectives(candidate, baseline):
    """Compare successful plans on the same input as (D km, W min).

    Pairing, provenance and feasibility must be verified by the caller. Missing
    plans have null objectives and must not be passed to this numeric function.
    """
    for vector in (candidate, baseline):
        if len(vector) != 2 or any(isinstance(x, bool) or not isinstance(x, (int, float))
                                   or not math.isfinite(x) or x < 0 for x in vector):
            raise ValueError("Expected two finite nonnegative objective values")
    delta = [x - y for x, y in zip(candidate, baseline)]
    dominates = all(x <= 0 for x in delta) and any(x < 0 for x in delta)
    dominated = all(x >= 0 for x in delta) and any(x > 0 for x in delta)
    relation = "DOMINATES" if dominates else "DOMINATED" if dominated else (
        "EQUAL" if all(x == 0 for x in delta) else "INCOMPARABLE")
    return {"delta": delta, "relative_delta": [d / b if b else None
            for d, b in zip(delta, baseline)], "relation": relation}
