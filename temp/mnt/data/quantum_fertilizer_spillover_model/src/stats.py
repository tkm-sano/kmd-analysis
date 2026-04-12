from __future__ import annotations

from math import comb
from statistics import median
from typing import Iterable

import pandas as pd


def _binomial_tail_greater(successes: int, trials: int) -> float:
    if trials <= 0:
        return 1.0
    return sum(comb(trials, k) for k in range(successes, trials + 1)) / (2**trials)


def _binomial_tail_less_equal(successes: int, trials: int) -> float:
    if trials <= 0:
        return 1.0
    return sum(comb(trials, k) for k in range(0, successes + 1)) / (2**trials)


def exact_sign_test(differences: Iterable[float], alternative: str = "greater") -> dict[str, float | int | str]:
    values = [float(x) for x in differences]
    positive = sum(1 for x in values if x > 0)
    negative = sum(1 for x in values if x < 0)
    zero = sum(1 for x in values if x == 0)
    non_zero = positive + negative

    if alternative == "greater":
        one_sided = _binomial_tail_greater(positive, non_zero)
    elif alternative == "less":
        one_sided = _binomial_tail_less_equal(positive, non_zero)
    else:
        raise ValueError(f"Unsupported alternative: {alternative}")

    two_sided = min(
        1.0,
        2.0
        * min(
            _binomial_tail_greater(positive, non_zero),
            _binomial_tail_less_equal(positive, non_zero),
        ),
    )

    non_zero_values = [x for x in values if x != 0]
    mean_change = sum(values) / len(values) if values else 0.0
    median_change = median(non_zero_values) if non_zero_values else 0.0

    return {
        "n_pairs": len(values),
        "n_non_zero": non_zero,
        "positive_diffs": positive,
        "negative_diffs": negative,
        "zero_diffs": zero,
        "mean_change": mean_change,
        "median_change": float(median_change),
        "one_sided_p_value": one_sided,
        "two_sided_p_value": two_sided,
    }


def build_statistical_tests(
    group_results: pd.DataFrame,
    disease_results: pd.DataFrame,
) -> pd.DataFrame:
    tests: list[dict[str, float | int | str]] = []

    test_specs = [
        {
            "test_id": "group_intake_increase",
            "analysis_unit": "所得群",
            "metric": "平均野菜摂取量の増加",
            "unit": "g/日",
            "differences": group_results["intake_change_g_per_day"],
            "null_hypothesis": "所得群全体で平均野菜摂取量の増加方向に一貫性がない",
            "alternative_hypothesis": "所得群全体で平均野菜摂取量が増加方向に一貫している",
        },
        {
            "test_id": "group_recommended_share_increase",
            "analysis_unit": "所得群",
            "metric": "推奨摂取量達成率の増加",
            "unit": "割合",
            "differences": group_results["new_recommended_share"] - group_results["baseline_recommended_share"],
            "null_hypothesis": "所得群全体で推奨摂取量達成率の増加方向に一貫性がない",
            "alternative_hypothesis": "所得群全体で推奨摂取量達成率が増加方向に一貫している",
        },
        {
            "test_id": "disease_case_reduction",
            "analysis_unit": "疾患",
            "metric": "症例数の減少",
            "unit": "件",
            "differences": disease_results["cases_reduction"],
            "null_hypothesis": "疾患全体で症例数の減少方向に一貫性がない",
            "alternative_hypothesis": "疾患全体で症例数が減少方向に一貫している",
        },
        {
            "test_id": "disease_daly_reduction",
            "analysis_unit": "疾患",
            "metric": "DALY の減少",
            "unit": "DALY",
            "differences": disease_results["daly_reduction"],
            "null_hypothesis": "疾患全体で DALY の減少方向に一貫性がない",
            "alternative_hypothesis": "疾患全体で DALY が減少方向に一貫している",
        },
        {
            "test_id": "disease_cost_reduction",
            "analysis_unit": "疾患",
            "metric": "年間医療費の減少",
            "unit": "円",
            "differences": disease_results["medical_cost_reduction_jpy"],
            "null_hypothesis": "疾患全体で年間医療費の減少方向に一貫性がない",
            "alternative_hypothesis": "疾患全体で年間医療費が減少方向に一貫している",
        },
    ]

    for spec in test_specs:
        result = exact_sign_test(spec["differences"], alternative="greater")
        tests.append(
            {
                "test_id": spec["test_id"],
                "analysis_unit": spec["analysis_unit"],
                "metric": spec["metric"],
                "unit": spec["unit"],
                "null_hypothesis": spec["null_hypothesis"],
                "alternative_hypothesis": spec["alternative_hypothesis"],
                "n_pairs": result["n_pairs"],
                "n_non_zero": result["n_non_zero"],
                "positive_diffs": result["positive_diffs"],
                "negative_diffs": result["negative_diffs"],
                "zero_diffs": result["zero_diffs"],
                "mean_change": result["mean_change"],
                "median_change": result["median_change"],
                "one_sided_p_value": result["one_sided_p_value"],
                "two_sided_p_value": result["two_sided_p_value"],
                "significant_at_5pct_one_sided": bool(result["one_sided_p_value"] < 0.05),
            }
        )

    return pd.DataFrame(tests)
