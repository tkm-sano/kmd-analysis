from __future__ import annotations

from research_cli.core import (
    AUTHORITY_PATH,
    BASELINE_DEMAND_CONFIG,
    BASELINE_DEMAND_PATH,
    OK,
    OVERVIEW_PATH,
    REQUESTS_PATH,
    ROOT,
    STOPS_PATH,
    accepted_paths,
    network_gate,
    portal_summary,
    relative,
)
from research_cli.portal import check as portal_check


def status() -> int:
    summary = portal_summary()
    ready, issues = network_gate()
    print("Current Milestone: M1 Network Ready — DONE")
    print(f"Current Research Stage: {summary['current_position']['current_stage']}")
    print("Immediate Next Task: Define routing scope for delivery instances")
    print(f"Demand: {'DONE' if all(path.is_file() for path in (BASELINE_DEMAND_PATH, REQUESTS_PATH, STOPS_PATH)) else 'INCOMPLETE'}")
    print(f"Network: {'COMPLETE / ACCEPTED' if ready else 'BLOCKED'}")
    print("Routing Baseline: NEXT / NOT YET PRODUCTION COMPLETE")
    print("Common Delivery Instance: PLANNED / NOT PRODUCTION COMPLETE")
    print("Classical Optimization: DOWNSTREAM / NOT PRODUCTION COMPLETE")
    print("Quantum / Simulation / Evaluation: FUTURE / NOT PRODUCTION COMPLETE")
    for issue in issues:
        print(f"Network issue: {issue}")
    return OK if ready else 1


def artifacts() -> int:
    auth, network, acceptance, mapping = accepted_paths()
    rows = (
        ("Research overview", OVERVIEW_PATH),
        ("Repository index", ROOT / "reproducibility/indexes/research_repository_index_v17.yml"),
        ("Current network authority", AUTHORITY_PATH),
        ("Accepted network", network),
        ("Network acceptance", acceptance),
        ("Accepted Stop mapping", mapping),
        ("Baseline demand config", BASELINE_DEMAND_CONFIG),
        ("Baseline demand", BASELINE_DEMAND_PATH),
        ("Requests", REQUESTS_PATH),
        ("Stops", STOPS_PATH),
        ("Portal research map", ROOT / "reproducibility/config/research_portal/research_map_v1.yml"),
    )
    for label, path in rows:
        print(f"{label}: {relative(path)} [{'EXISTS' if path.exists() else 'MISSING'}]")
    print(f"Accepted network SHA-256: {auth['accepted_run']['network_sha256']}")
    print("Routing Baseline artifact: MISSING")
    print("Common Delivery Instance: MISSING")
    print("Classical/Quantum/Delivery Simulation/Fulfillment artifacts: MISSING")
    return OK


def validate(*, dry_run: bool = False) -> int:
    return portal_check(dry_run=dry_run)
