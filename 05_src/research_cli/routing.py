from __future__ import annotations

from research_cli.core import OK, REQUESTS_PATH, STOPS_PATH, accepted_paths, network_gate, print_gate, relative, unavailable


def inputs() -> int:
    ready, issues = network_gate()
    _, network, _, mapping = accepted_paths()
    print(f"Accepted network: {relative(network)} [{'READY' if ready else 'BLOCKED'}]")
    print(f"Accepted Stop mapping: {relative(mapping)} [{'READY' if mapping.is_file() else 'MISSING'}]")
    print(f"Requests: {relative(REQUESTS_PATH)} [{'READY' if REQUESTS_PATH.is_file() else 'MISSING'}]")
    print(f"Stops: {relative(STOPS_PATH)} [{'READY' if STOPS_PATH.is_file() else 'MISSING'}]")
    print("Depot: UNRESOLVED")
    print("Delivery vehicle class: UNRESOLVED")
    print("Routing scope: UNRESOLVED")
    print("Routing cost definition: UNRESOLVED")
    print("Decision record: RESEARCH_OVERVIEW.md#stage-1--routing-baseline-next")
    if not ready:
        print_gate("Formal Network prerequisite", False, issues)
    return OK


def status() -> int:
    ready, issues = network_gate()
    print("Routing Baseline: NEXT / NOT YET PRODUCTION COMPLETE")
    print_gate("Formal Network prerequisite", ready, issues)
    print("Production routing runner: NOT IMPLEMENTED")
    print("Validated routing artifact: MISSING")
    return OK


def build(*, dry_run: bool = False) -> int:
    ready, issues = network_gate()
    if not ready:
        print_gate("Formal Network prerequisite", False, issues)
        return 0 if dry_run else 3
    return unavailable(
        title="Routing Baseline build",
        missing=("production routing baseline runner", "adopted depot, vehicle class, routing scope, and routing cost definition"),
        dependency=("FORMAL_NETWORK_ACCEPTED = true [PASS]",),
        dry_run=dry_run,
    )


def validate(*, dry_run: bool = False) -> int:
    return unavailable(
        title="Routing Baseline validation",
        missing=("validated Routing Baseline artifact and canonical production validator",),
        dependency=("successful ./research routing build",),
        dry_run=dry_run,
    )
