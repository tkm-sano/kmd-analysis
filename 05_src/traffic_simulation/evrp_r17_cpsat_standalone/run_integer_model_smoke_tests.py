#!/usr/bin/env python3
"""Small CP-SAT integer-model smoke tests for the frozen R17 formulation.

This is not the R18 production solver.  It uses the same route/slot/time/
energy/charging constraint components on deliberately minimal fixed routes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

from ortools.sat.python import cp_model
import ortools


BATTERY = 147_600_000
MIN_ENERGY = 29_520_000
POWER_J_PER_MS = 70
MAX_DURATION = 1_800_000
SLOTS = 11
TIME_HORIZON = 10_000_000
CONFIG = {
    "ortools_version": "9.12.4544",
    "random_seed": 20260909,
    "num_search_workers": 1,
    "max_time_in_seconds": 2.0,
    "log_search_progress": False,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def make_model(route, energies, *, initial_energy=BATTERY, duration_fixes=None,
               duration_cap=True, capacity_cap=True, minimum_cap=True,
               force_unused_slots=None):
    """Build one fixed-route model using the R17 slot/state components."""
    duration_fixes = duration_fixes or {}
    force_unused_slots = set(force_unused_slots or [])
    pcount = len(route)
    assert len(energies) == pcount - 1
    model = cp_model.CpModel()
    active = [model.NewBoolVar(f"active_{p}") for p in range(pcount)]
    node_at = {(p, node): model.NewBoolVar(f"node_at_{p}_{node}_{k}") for p, node in enumerate(route) for k, node in enumerate([node])}
    charger_at = [model.NewBoolVar(f"charger_at_{p}") for p in range(pcount)]
    for p, node in enumerate(route):
        model.Add(active[p] == 1)
        model.Add(node_at[(p, node)] == 1)
        model.Add(charger_at[p] == int(node == "H"))
    model.Add(node_at[(0, "D")] == 1)
    customer_positions = [p for p, node in enumerate(route) if node.startswith("C")]
    for customer in sorted({route[p] for p in customer_positions}):
        model.Add(sum(node_at[(p, customer)] for p in customer_positions if route[p] == customer) <= 1)

    slot_used = [model.NewBoolVar(f"slot_used_{c}") for c in range(SLOTS)]
    slot_position = [model.NewIntVar(0, pcount - 1, f"slot_position_{c}") for c in range(SLOTS)]
    slot_duration = [model.NewIntVar(0, MAX_DURATION if duration_cap else MAX_DURATION + 1, f"slot_duration_{c}") for c in range(SLOTS)]
    slot_energy = [model.NewIntVar(0, POWER_J_PER_MS * (MAX_DURATION + 1), f"slot_energy_{c}") for c in range(SLOTS)]
    slot_at = {(c, p): model.NewBoolVar(f"slot_at_{c}_{p}") for c in range(SLOTS) for p in range(pcount)}

    for c in range(SLOTS - 1):
        model.AddImplication(slot_used[c + 1], slot_used[c])
        model.Add(slot_position[c + 1] > slot_position[c]).OnlyEnforceIf(slot_used[c + 1])
    for c in range(SLOTS):
        model.Add(sum(slot_at[(c, p)] for p in range(pcount)) == slot_used[c])
        model.Add(slot_position[c] == 0).OnlyEnforceIf(slot_used[c].Not())
        model.Add(slot_duration[c] >= 1).OnlyEnforceIf(slot_used[c])
        model.Add(slot_duration[c] == 0).OnlyEnforceIf(slot_used[c].Not())
        model.Add(slot_energy[c] == POWER_J_PER_MS * slot_duration[c])
        if c in force_unused_slots:
            model.Add(slot_used[c] == 0)
        if c in duration_fixes:
            model.Add(slot_duration[c] == duration_fixes[c])
        for p in range(pcount):
            model.Add(slot_position[c] == p).OnlyEnforceIf(slot_at[(c, p)])

    for p in range(pcount):
        model.Add(sum(slot_at[(c, p)] for c in range(SLOTS)) == charger_at[p])
        if p + 1 < pcount:
            model.Add(charger_at[p] + charger_at[p + 1] <= 1)

    arrival = [model.NewIntVar(0, TIME_HORIZON, f"arrival_{p}") for p in range(pcount)]
    departure = [model.NewIntVar(0, TIME_HORIZON, f"departure_{p}") for p in range(pcount)]
    wait = [model.NewIntVar(0, TIME_HORIZON, f"wait_{p}") for p in range(pcount)]
    service = [0 if node in ("D", "H") else 100 for node in route]
    charge_at_p = [model.NewIntVar(0, MAX_DURATION if duration_cap else MAX_DURATION + 1, f"charge_at_{p}") for p in range(pcount)]
    charge_energy_at_p = [model.NewIntVar(0, POWER_J_PER_MS * (MAX_DURATION + 1), f"charge_energy_at_{p}") for p in range(pcount)]
    energy_arrival = [model.NewIntVar(0, BATTERY, f"energy_arrival_{p}") for p in range(pcount)]
    energy_departure = [model.NewIntVar(0, BATTERY if capacity_cap else BATTERY + POWER_J_PER_MS * (MAX_DURATION + 1), f"energy_departure_{p}") for p in range(pcount)]
    model.Add(arrival[0] == 0)
    model.Add(energy_arrival[0] == initial_energy)
    for p in range(pcount):
        model.Add(wait[p] == 0)
        model.Add(departure[p] == arrival[p] + wait[p] + service[p] + charge_at_p[p])
        model.Add(energy_departure[p] == energy_arrival[p] + charge_energy_at_p[p])
        if minimum_cap:
            model.Add(energy_arrival[p] >= MIN_ENERGY)
            model.Add(energy_departure[p] >= MIN_ENERGY)
        if capacity_cap:
            model.Add(energy_departure[p] <= BATTERY)
        if route[p] != "H":
            model.Add(charge_at_p[p] == 0)
            model.Add(charge_energy_at_p[p] == 0)
        else:
            for c in range(SLOTS):
                model.Add(charge_at_p[p] == slot_duration[c]).OnlyEnforceIf(slot_at[(c, p)])
                model.Add(charge_energy_at_p[p] == slot_energy[c]).OnlyEnforceIf(slot_at[(c, p)])
    for p, e in enumerate(energies):
        model.Add(arrival[p + 1] == departure[p] + 1000)
        model.Add(energy_arrival[p + 1] == energy_departure[p] - e)
    model.Minimize(sum(slot_duration))
    return {
        "model": model, "slot_used": slot_used, "slot_position": slot_position,
        "slot_duration": slot_duration, "slot_energy": slot_energy,
        "slot_at": slot_at, "arrival": arrival, "departure": departure,
        "energy_arrival": energy_arrival, "energy_departure": energy_departure,
        "charge_at_p": charge_at_p, "charge_energy_at_p": charge_energy_at_p,
        "route": route,
    }


def solve_case(case):
    built = make_model(**case["model"])
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = CONFIG["random_seed"]
    solver.parameters.num_search_workers = CONFIG["num_search_workers"]
    solver.parameters.max_time_in_seconds = CONFIG["max_time_in_seconds"]
    solver.parameters.log_search_progress = CONFIG["log_search_progress"]
    started = time.monotonic()
    status_code = solver.Solve(built["model"])
    runtime = time.monotonic() - started
    status = solver.StatusName(status_code)
    decoded = {"status": status, "runtime_seconds": runtime, "objective": None, "route": case["model"]["route"]}
    if status in ("OPTIMAL", "FEASIBLE"):
        decoded.update({
            "objective": solver.ObjectiveValue(),
            "slot_used": [solver.Value(x) for x in built["slot_used"]],
            "slot_position": [solver.Value(x) for x in built["slot_position"]],
            "slot_duration_ms": [solver.Value(x) for x in built["slot_duration"]],
            "slot_energy_j": [solver.Value(x) for x in built["slot_energy"]],
            "arrival_ms": [solver.Value(x) for x in built["arrival"]],
            "departure_ms": [solver.Value(x) for x in built["departure"]],
            "energy_arrival_j": [solver.Value(x) for x in built["energy_arrival"]],
            "energy_departure_j": [solver.Value(x) for x in built["energy_departure"]],
        })
        decoded["validation"] = validate_solution(decoded, case)
    return decoded


def validate_solution(decoded, case):
    used = decoded["slot_used"]
    pos = decoded["slot_position"]
    dur = decoded["slot_duration_ms"]
    en = decoded["slot_energy_j"]
    checks = {
        "prefix": all(not used[c + 1] or used[c] for c in range(SLOTS - 1)),
        "strict_used_order": all(not used[c + 1] or pos[c + 1] > pos[c] for c in range(SLOTS - 1)),
        "used_duration_positive": all(not used[c] or 0 < dur[c] <= MAX_DURATION for c in range(SLOTS)),
        "unused_duration_zero": all(used[c] or dur[c] == 0 for c in range(SLOTS)),
        "exact_energy_relation": all(en[c] == POWER_J_PER_MS * dur[c] for c in range(SLOTS)),
        "unused_energy_zero": all(used[c] or en[c] == 0 for c in range(SLOTS)),
        "energy_bounds": all(MIN_ENERGY <= x <= BATTERY for x in decoded["energy_arrival_j"] + decoded["energy_departure_j"]),
        "time_monotonic": all(decoded["arrival_ms"][p + 1] >= decoded["departure_ms"][p] for p in range(len(case["model"]["route"]) - 1)),
    }
    expected_used = case.get("expected_used_slots")
    if expected_used is not None:
        checks["expected_slot_count"] = sum(used) == expected_used
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output-dir", required=True); args = ap.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=False)
    cases = [
        {"id":"T01_no_charger","expected":"FEASIBLE","expected_used_slots":0,"model":{"route":["D","C_A","D"],"energies":[1000,1000]}},
        {"id":"T02_one_charger","expected":"FEASIBLE","expected_used_slots":1,"model":{"route":["D","H","C_A","D"],"energies":[200000,200000,200000],"initial_energy":30000000}},
        {"id":"T03_multiple_revisit","expected":"FEASIBLE","expected_used_slots":2,"model":{"route":["D","C_A","H","C_B","H","D"],"energies":[1000000,1000000,50000000,50000000,50000000]}},
        {"id":"T04_consecutive_charger","expected":"INFEASIBLE","model":{"route":["D","H","H","D"],"energies":[0,0,0]}},
        {"id":"T05_duration_over_cap","expected":"INFEASIBLE","model":{"route":["D","H","D"],"energies":[0,0],"duration_fixes":{0:1800001}}},
        {"id":"T06_capacity_overflow","expected":"INFEASIBLE","model":{"route":["D","H","D"],"energies":[0,0],"initial_energy":147000100,"duration_fixes":{0:10000}}},
        {"id":"T07_minimum_energy","expected":"INFEASIBLE","model":{"route":["D","C_A","D"],"energies":[480001,0],"initial_energy":30000000}},
        {"id":"T08_unused_slot_neutrality","expected":"FEASIBLE","expected_used_slots":1,"model":{"route":["D","H","C_A","D"],"energies":[200000,200000,200000],"initial_energy":30000000}},
    ]
    per_test = []
    for case in cases:
        actual = solve_case(case)
        result = {"id": case["id"], "expected": case["expected"], "actual": actual, "pass": actual["status"] == case["expected"] and (actual.get("validation", {}).get("status", "PASS") == "PASS")}
        if case["id"] == "T04_consecutive_charger":
            relaxed = dict(case); relaxed["model"] = dict(case["model"]); relaxed["model"]["route"] = ["D","H","C_A","D"]
            result["constraint_diagnostic"] = {"relaxed_expected": "FEASIBLE", "relaxed_actual": solve_case(relaxed)}
        if case["id"] == "T05_duration_over_cap":
            relaxed = dict(case); relaxed["model"] = dict(case["model"]); relaxed["model"]["duration_cap"] = False
            result["constraint_diagnostic"] = {"relaxed_expected": "FEASIBLE", "relaxed_actual": solve_case(relaxed)}
        if case["id"] == "T06_capacity_overflow":
            relaxed = dict(case); relaxed["model"] = dict(case["model"]); relaxed["model"]["capacity_cap"] = False
            result["constraint_diagnostic"] = {"relaxed_expected": "FEASIBLE", "relaxed_actual": solve_case(relaxed)}
        if case["id"] == "T07_minimum_energy":
            relaxed = dict(case); relaxed["model"] = dict(case["model"]); relaxed["model"]["minimum_cap"] = False
            result["constraint_diagnostic"] = {"relaxed_expected": "FEASIBLE", "relaxed_actual": solve_case(relaxed)}
        per_test.append(result)
        write_json(out / f"{case['id']}.json", result)

    repeat = {}
    for case in [cases[0], cases[1], cases[2], cases[7]]:
        a, b = solve_case(case), solve_case(case)
        keys = ["status", "route", "slot_used", "slot_position", "slot_duration_ms", "slot_energy_j", "arrival_ms", "departure_ms", "energy_arrival_j", "energy_departure_j", "objective"]
        repeat[case["id"]] = {"match": all(a.get(k) == b.get(k) for k in keys), "run_1": a, "run_2": b}
    write_json(out / "repeated_run_comparison.json", repeat)
    aggregate = {"status": "PASS" if all(x["pass"] for x in per_test) and all(x["match"] for x in repeat.values()) else "FAIL", "test_count": 8, "tests": [{"id":x["id"],"expected":x["expected"],"actual":x["actual"]["status"],"pass":x["pass"]} for x in per_test], "repeated_run": {k:v["match"] for k,v in repeat.items()}, "config": CONFIG, "solver_implemented_for_smoke_only": true}
    write_json(out / "aggregate_validation_report.json", aggregate)
    write_json(out / "manifest.json", {"run_id": out.name, "status": aggregate["status"], "files": {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}, "software": {"python": platform.python_version(), "ortools": ortools.__version__}, "r18_executed": False, "r19_executed": False})
    return 0 if aggregate["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
