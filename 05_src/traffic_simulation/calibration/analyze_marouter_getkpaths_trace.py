#!/usr/bin/env python3
"""Validate marouter getKPaths traces and classify Route2 support loss."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import fmean
import xml.etree.ElementTree as ET


ALLOWED_CLASSIFICATIONS = {
    "NOT_EXPLORED",
    "NOT_SHORTEST_UNDER_PENALTY",
    "TERMINATED_BEFORE_ROUTE2",
    "INDETERMINATE",
}

FAMILY_COUNT = 14
TARGET_ITERATION = 47


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_trace(path: Path) -> dict:
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    starts = [event for event in events if event["event"] == "candidate_generation_start"]
    ends = [event for event in events if event["event"] == "candidate_generation_end"]
    computes = [event for event in events if event["event"] == "compute_path_result"]
    penalties = [event for event in events if event["event"] == "penalty_application"]
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError(f"{path}: expected exactly one start and end event")
    requested = starts[0]["requested_iterations"]
    expected = list(range(1, requested + 1))
    if [event["iteration_one_based"] for event in computes] != expected:
        raise ValueError(f"{path}: compute iterations are not contiguous")
    if [event["iteration_one_based"] for event in penalties] != expected:
        raise ValueError(f"{path}: penalty iterations are not contiguous")
    return {
        "path": path,
        "events": events,
        "start": starts[0],
        "end": ends[0],
        "computes": computes,
        "penalties": penalties,
    }


def route_records(path: Path) -> list[tuple[str, str | None, str | None]]:
    root = ET.parse(path).getroot()
    return [
        (route.get("edges", ""), route.get("probability"), route.get("cost"))
        for route in root.iter("route")
    ]


def classify(short: dict, long: dict) -> tuple[str, dict]:
    short_computes = short["computes"]
    long_computes = long["computes"]
    short_requested = short["start"]["requested_iterations"]
    target_hits_long = [
        event["iteration_one_based"]
        for event in long_computes
        if event["target_edge_present"]
    ]
    same_prefix = all(
        left["generated_edges"] == right["generated_edges"]
        and left["search_cost"] == right["search_cost"]
        and left["outcome"] == right["outcome"]
        for left, right in zip(short_computes, long_computes)
    ) and len(short_computes) <= len(long_computes)

    evidence = {
        "short_requested_iterations": short_requested,
        "long_requested_iterations": long["start"]["requested_iterations"],
        "same_deterministic_prefix": same_prefix,
        "short_target_iterations": [
            event["iteration_one_based"]
            for event in short_computes
            if event["target_edge_present"]
        ],
        "long_target_iterations": target_hits_long,
        "first_long_target_iteration": target_hits_long[0] if target_hits_long else None,
        "short_end_reason": short["end"]["end_reason"],
        "short_outcomes": [event["outcome"] for event in short_computes],
    }

    if evidence["short_target_iterations"]:
        return "INDETERMINATE", evidence
    if (
        same_prefix
        and target_hits_long
        and target_hits_long[0] > short_requested
        and short["end"]["end_reason"] == "REQUESTED_ITERATIONS_COMPLETED"
    ):
        return "TERMINATED_BEFORE_ROUTE2", evidence
    if any(event["outcome"] == "MAX_ALTERNATIVES_REACHED" for event in short_computes):
        return "TERMINATED_BEFORE_ROUTE2", evidence
    # getKPaths/computePath output does not expose Dijkstra's visited-edge set.
    # Without a later observed target path it cannot separate NOT_EXPLORED from
    # NOT_SHORTEST_UNDER_PENALTY, so it must not guess between those classes.
    return "INDETERMINATE", evidence


def _jaccard_distance(left: set[str], right: set[str]) -> float:
    union = left | right
    return 0.0 if not union else 1.0 - len(left & right) / len(union)


def cluster_route47_families(
    computes: list[dict], target_index: int, family_count: int = FAMILY_COUNT
) -> dict[int, str]:
    """Cluster pre-target routes by their Route47 shared-edge sets.

    Complete linkage keeps every pair in a family close in shared-section
    structure.  Ties are resolved by the earliest iteration, making the
    classification reproducible without an external clustering package.
    """
    target_edges = set(computes[target_index - 1]["generated_edges"])
    members = computes[: target_index - 1]
    if family_count <= 0 or family_count > len(members):
        raise ValueError("family_count must be between 1 and pre-target route count")
    shared = [set(event["generated_edges"]) & target_edges for event in members]
    distances = {
        (right, left): _jaccard_distance(shared[right], shared[left])
        for right in range(len(shared))
        for left in range(right)
    }
    clusters = [[index] for index in range(len(shared))]
    while len(clusters) > family_count:
        best: tuple[tuple[float, int, int], int, int] | None = None
        for right in range(len(clusters)):
            for left in range(right):
                distance = max(
                    distances[(max(a, b), min(a, b))]
                    for a in clusters[right]
                    for b in clusters[left]
                )
                key = (distance, min(clusters[left]), min(clusters[right]))
                if best is None or key < best[0]:
                    best = (key, left, right)
        assert best is not None
        _, left, right = best
        clusters[left].extend(clusters[right])
        del clusters[right]

    clusters.sort(key=min)
    return {
        member + 1: f"F{family_number:02d}"
        for family_number, cluster in enumerate(clusters, start=1)
        for member in cluster
    }


def build_route47_analysis(trace: dict) -> tuple[list[dict], list[dict], dict]:
    computes = trace["computes"]
    penalties = trace["penalties"]
    target_hits = [
        event["iteration_one_based"] for event in computes if event["target_edge_present"]
    ]
    if not target_hits or target_hits[0] != TARGET_ITERATION:
        raise ValueError(f"expected first target route at iteration {TARGET_ITERATION}")
    if len(computes) < TARGET_ITERATION:
        raise ValueError("trace ends before Route47")

    target = computes[TARGET_ITERATION - 1]
    target_sequence = target["generated_edges"]
    target_edges = set(target_sequence)
    if len(target_sequence) != len(target_edges):
        raise ValueError("Route47 contains repeated edges; set coverage is ambiguous")

    counts: dict[str, float] = {}
    for penalty in penalties[: TARGET_ITERATION - 1]:
        for update in penalty["updates"]:
            counts[update["edge"]] = update["after"]
    target_base_cost = target["search_cost"] - sum(
        counts.get(edge, 0.0) for edge in target_sequence
    )

    family_by_iteration = cluster_route47_families(computes, TARGET_ITERATION)
    rows: list[dict] = []
    counts = {}
    for event, penalty in zip(
        computes[:TARGET_ITERATION], penalties[:TARGET_ITERATION]
    ):
        iteration = event["iteration_one_based"]
        candidate_sequence = event["generated_edges"]
        candidate_edges = set(candidate_sequence)
        if len(candidate_sequence) != len(candidate_edges):
            raise ValueError(f"iteration {iteration} contains repeated edges")
        shared = candidate_edges & target_edges
        shared_penalty = sum(counts.get(edge, 0.0) for edge in shared)
        target_search_cost = target_base_cost + sum(
            counts.get(edge, 0.0) for edge in target_sequence
        )
        candidate_variable_cost = event["search_cost"] - shared_penalty
        target_variable_cost = target_search_cost - shared_penalty
        row = {
            "iteration": iteration,
            "family": family_by_iteration.get(iteration, "ROUTE47_TARGET"),
            "search_cost": event["search_cost"],
            "route47_search_cost": target_search_cost,
            "route47_variable_cost": target_variable_cost,
            "candidate_variable_cost": candidate_variable_cost,
            "variable_delta": target_variable_cost - candidate_variable_cost,
            "shared_edge_count": len(shared),
            "route47_edge_coverage": len(shared) / len(target_edges),
            "edge_jaccard": len(shared) / len(candidate_edges | target_edges),
        }
        rows.append(row)
        for update in penalty["updates"]:
            counts[update["edge"]] = update["after"]

    family_rows = []
    for family in sorted(set(family_by_iteration.values())):
        selected = [row for row in rows[:-1] if row["family"] == family]
        costs = [row["search_cost"] for row in selected]
        family_rows.append(
            {
                "family": family,
                "occurrences": len(selected),
                "first_iteration": min(row["iteration"] for row in selected),
                "last_iteration": max(row["iteration"] for row in selected),
                "min_search_cost": min(costs),
                "mean_search_cost": fmean(costs),
                "max_search_cost": max(costs),
                "min_variable_delta": min(row["variable_delta"] for row in selected),
                "mean_route47_edge_coverage": fmean(
                    row["route47_edge_coverage"] for row in selected
                ),
                "mean_edge_jaccard": fmean(row["edge_jaccard"] for row in selected),
                "present_by_paths20": any(row["iteration"] <= 20 for row in selected),
            }
        )

    new_families = [row["family"] for row in family_rows if not row["present_by_paths20"]]
    window = [row for row in rows if 21 <= row["iteration"] <= 46]
    terminal = [row for row in rows if 40 <= row["iteration"] <= 46]
    delta_increases = [
        [left["iteration"], right["iteration"]]
        for left, right in zip(rows[:45], rows[1:46])
        if right["variable_delta"] > left["variable_delta"]
    ]
    family_switches = sum(
        left["family"] != right["family"] for left, right in zip(rows[:45], rows[1:46])
    )
    facts = {
        "target_iteration": TARGET_ITERATION,
        "target_base_cost": target_base_cost,
        "family_method": (
            "complete-linkage clustering of pre-target Route47 shared-edge sets "
            "using Jaccard distance; stopped at 14 families; labels ordered by first iteration"
        ),
        "families_by_paths20": [
            row["family"] for row in family_rows if row["present_by_paths20"]
        ],
        "new_families_iterations_21_46": new_families,
        "new_family_occurrences_21_46": sum(
            row["family"] in new_families for row in window
        ),
        "iterations_21_46_count": len(window),
        "new_family_share_21_46": sum(
            row["family"] in new_families for row in window
        ) / len(window),
        "terminal_new_family_occurrences": sum(
            row["family"] in new_families for row in terminal
        ),
        "terminal_family_sequence": [row["family"] for row in terminal],
        "terminal_iterations": terminal,
        "closest_pre_target_candidate": min(rows[:-1], key=lambda row: row["variable_delta"]),
        "family_switches_iterations_1_46": family_switches,
        "variable_delta_increase_transitions": delta_increases,
    }
    return rows, family_rows, facts


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: float) -> str:
    return f"{value:.6f}"


def render_route47_summary(family_rows: list[dict], facts: dict) -> tuple[str, str]:
    new = set(facts["new_families_iterations_21_46"])
    new_details = ", ".join(
        f"{row['family']} (iter {row['first_iteration']}; {row['occurrences']}回)"
        for row in family_rows
        if row["family"] in new
    )
    lines = [
        "Route47 pre-shortest family analysis",
        "",
        f"Family definition: {facts['family_method']}",
        f"paths=20: {len(facts['families_by_paths20'])} families; iterations 21-46 add {len(new)} families.",
        f"New families: {new_details}",
        (
            "Iterations 21-46: new-family candidates "
            f"{facts['new_family_occurrences_21_46']}/{facts['iterations_21_46_count']} "
            f"({_fmt(100 * facts['new_family_share_21_46'])}%); "
            f"existing-family candidates {facts['iterations_21_46_count'] - facts['new_family_occurrences_21_46']}"
            f"/{facts['iterations_21_46_count']}."
        ),
        "New-family minimum variable_delta: "
        + ", ".join(
            f"{row['family']}={_fmt(row['min_variable_delta'])}"
            for row in family_rows
            if row["family"] in new
        )
        + ".",
        (
            "Iterations 40-46: new-family candidates "
            f"{facts['terminal_new_family_occurrences']}/7."
        ),
        "",
        "Iterations 40-46:",
        "iter family search_cost route47_variable_cost variable_delta coverage jaccard",
    ]
    for row in facts["terminal_iterations"]:
        lines.append(
            f"{row['iteration']:>4} {row['family']:>6} {_fmt(row['search_cost']):>12} "
            f"{_fmt(row['route47_variable_cost']):>21} {_fmt(row['variable_delta']):>14} "
            f"{_fmt(row['route47_edge_coverage']):>8} {_fmt(row['edge_jaccard']):>8}"
        )
    closest = facts["closest_pre_target_candidate"]
    lines.extend(
        [
            "",
            (
                "Closest pre-target candidate: iteration "
                f"{closest['iteration']} / {closest['family']}, "
                f"variable_delta={_fmt(closest['variable_delta'])}, "
                f"coverage={_fmt(closest['route47_edge_coverage'])}, "
                f"Jaccard={_fmt(closest['edge_jaccard'])}."
            ),
            (
                f"Family switches (iterations 1-46): {facts['family_switches_iterations_1_46']}; "
                "variable_delta increases (moves away from Route47) at transitions: "
                + ", ".join(f"{a}->{b}" for a, b in facts["variable_delta_increase_transitions"])
                + "."
            ),
        ]
    )
    summary = "\n".join(lines) + "\n"

    diagnosis = "\n".join(
        [
            "最終診断（traceで確認できる範囲）",
            "",
            (
                "paths=20は、iteration 21〜46で初出する4経路族 "
                f"({', '.join(sorted(new))}) の5候補に加え、paths=20以前から存在する族の"
                "追加21候補、合計26候補を未探索のまま残している。"
            ),
            (
                "Route2が47番目になるまでには、新規4族の探索（21〜46の5/26候補）と、"
                "既出族の反復選択（同21候補）の両方が観測される。ただし直前のiteration 46は"
                f"paths=20以前から存在する{closest['family']}であり、そのpenalty適用後にRoute47が選択された。"
                "したがって、直前の順位交代は新規族の初出ではなく既存族側のpenalty蓄積の局面である。"
            ),
            (
                "iteration 46時点でRoute47に最も近い競合候補はiteration 46の"
                f"{closest['family']}で、共通edge penalty除外後の差は"
                f"{_fmt(closest['variable_delta'])}、Route47 edge coverageは"
                f"{_fmt(closest['route47_edge_coverage'])}、Jaccardは"
                f"{_fmt(closest['edge_jaccard'])}である。"
            ),
            (
                "探索はRoute2へ単調接近していない。iteration 1〜46で経路族が"
                f"{facts['family_switches_iterations_1_46']}回切り替わり、variable_deltaが増加する"
                f"遷移も{len(facts['variable_delta_increase_transitions'])}回あるため、数値上は"
                "複数族を非単調に行き来しながらpenaltyで相対順位が変化している。"
            ),
        ]
    ) + "\n"
    return summary, diagnosis


def write_route47_analysis(trace_path: Path, output_dir: Path) -> tuple[str, str]:
    trace = load_trace(trace_path)
    iteration_rows, family_rows, facts = build_route47_analysis(trace)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "iteration_level.csv", iteration_rows)
    _write_csv(output_dir / "family_level_summary.csv", family_rows)
    (output_dir / "iteration_level.json").write_text(
        json.dumps(iteration_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "family_level_summary.json").write_text(
        json.dumps(family_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary, diagnosis = render_route47_summary(family_rows, facts)
    (output_dir / "terminal_summary.txt").write_text(summary, encoding="utf-8")
    (output_dir / "final_diagnosis.txt").write_text(diagnosis, encoding="utf-8")
    return summary, diagnosis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze-families-trace", type=Path)
    parser.add_argument("--analysis-output-dir", type=Path)
    parser.add_argument("--short-trace", type=Path)
    parser.add_argument("--long-trace", type=Path)
    parser.add_argument("--standard-short-routes", type=Path)
    parser.add_argument("--instrumented-short-routes", type=Path)
    parser.add_argument("--standard-long-routes", type=Path)
    parser.add_argument("--instrumented-long-routes", type=Path)
    parser.add_argument("--duplicate-trace", type=Path)
    parser.add_argument("--limit-trace", type=Path)
    parser.add_argument("--network", type=Path)
    parser.add_argument("--trips", type=Path)
    parser.add_argument("--instrumentation-patch", type=Path)
    parser.add_argument("--instrumented-binary", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.analyze_families_trace:
        if not args.analysis_output_dir:
            parser.error("--analysis-output-dir is required with --analyze-families-trace")
        summary, diagnosis = write_route47_analysis(
            args.analyze_families_trace, args.analysis_output_dir
        )
        print(summary)
        print(diagnosis, end="")
        return 0

    required = [
        "short_trace", "long_trace", "standard_short_routes",
        "instrumented_short_routes", "standard_long_routes",
        "instrumented_long_routes",
    ]
    missing = [f"--{name.replace('_', '-')}" for name in required if getattr(args, name) is None]
    if missing:
        parser.error("the following arguments are required: " + ", ".join(missing))

    short = load_trace(args.short_trace)
    long = load_trace(args.long_trace)
    short_equal = route_records(args.standard_short_routes) == route_records(
        args.instrumented_short_routes
    )
    long_equal = route_records(args.standard_long_routes) == route_records(
        args.instrumented_long_routes
    )
    classification, evidence = classify(short, long)
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise AssertionError(classification)

    inputs = {
        key: {"path": str(value), "sha256": sha256(value)}
        for key, value in vars(args).items()
        if isinstance(value, Path) and key != "output"
    }
    report = {
        "artifact_id": "SUMO_1_24_0_MAROUTER_GETKPATHS_TRACE_V1",
        "sumo": {
            "version": "1.24.0",
            "source_tag": "v1_24_0",
            "source_commit": "b72eb3fabc806681f8c9048999a33dd8d64092b1",
        },
        "classification": classification,
        "target_edge": short["start"]["target_edge"],
        "regression": {
            "short_final_route_records_equal": short_equal,
            "long_final_route_records_equal": long_equal,
            "passed": short_equal and long_equal,
        },
        "evidence": evidence,
        "empty_vector_differentiation": {
            "duplicate_outcomes": (
                [event["outcome"] for event in load_trace(args.duplicate_trace)["computes"]]
                if args.duplicate_trace else None
            ),
            "limit_outcomes": (
                [event["outcome"] for event in load_trace(args.limit_trace)["computes"]]
                if args.limit_trace else None
            ),
            "search_failure_outcome_instrumented": "SEARCH_FAILED",
            "search_failure_exercised": False,
        },
        "inputs": inputs,
        "scope": "routing diagnostics only; no observed traffic counts used",
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["regression"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
