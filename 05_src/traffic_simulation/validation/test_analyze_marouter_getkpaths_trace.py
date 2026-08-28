from pathlib import Path
import sys

import pytest


MODULE_DIR = Path(__file__).resolve().parents[1] / "calibration"
sys.path.insert(0, str(MODULE_DIR))

from analyze_marouter_getkpaths_trace import build_route47_analysis, classify, load_trace  # noqa: E402


def run(iterations, target=()):
    computes = [
        {
            "iteration_one_based": index,
            "generated_edges": [f"e{index}"],
            "search_cost": float(index),
            "outcome": "NEW_ROUTE",
            "target_edge_present": index in target,
        }
        for index in range(1, iterations + 1)
    ]
    return {
        "start": {"requested_iterations": iterations},
        "end": {"end_reason": "REQUESTED_ITERATIONS_COMPLETED"},
        "computes": computes,
    }


def test_classifies_later_target_as_terminated_before_route2():
    classification, evidence = classify(run(2), run(4, target={3}))
    assert classification == "TERMINATED_BEFORE_ROUTE2"
    assert evidence["same_deterministic_prefix"] is True
    assert evidence["first_long_target_iteration"] == 3


def test_does_not_guess_without_router_exploration_trace():
    classification, _ = classify(run(2), run(4))
    assert classification == "INDETERMINATE"


def test_max_alternatives_is_termination_evidence():
    short = run(2)
    short["computes"][-1]["outcome"] = "MAX_ALTERNATIVES_REACHED"
    classification, _ = classify(short, run(4))
    assert classification == "TERMINATED_BEFORE_ROUTE2"


def test_route47_family_analysis_reproduces_trace_facts():
    trace_path = (
        Path(__file__).resolve().parents[3]
        / "reproducibility/outputs/traffic_simulation/routing"
        / "20260828_route2_down_getkpaths_instrumentation_v1"
        / "instrumented_paths50.trace.jsonl"
    )
    iteration_rows, family_rows, facts = build_route47_analysis(load_trace(trace_path))

    assert len(iteration_rows) == 47
    assert len(family_rows) == 14
    assert sum(row["present_by_paths20"] for row in family_rows) == 10
    assert facts["new_families_iterations_21_46"] == ["F11", "F12", "F13", "F14"]
    assert facts["new_family_occurrences_21_46"] == 5
    assert facts["terminal_family_sequence"] == [
        "F12", "F02", "F14", "F02", "F02", "F05", "F02"
    ]
    assert iteration_rows[45]["variable_delta"] == pytest.approx(3.902774533448337)
    assert iteration_rows[46]["variable_delta"] == pytest.approx(0.0)
    assert facts["closest_pre_target_candidate"]["iteration"] == 46
    assert facts["family_switches_iterations_1_46"] == 38
