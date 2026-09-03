from __future__ import annotations

from research_cli import demand, instance, network, optimization, portal, routing
from research_cli.core import OK, network_gate


def network_pipeline(*, dry_run: bool = False) -> int:
    ready, _ = network_gate()
    if ready:
        print("Build: SKIPPED — reusing current accepted network; accepted run will not be overwritten")
        return network.validate(dry_run=dry_run)
    print("Build: BLOCKED — no safe isolated end-to-end network runner")
    return network.build(dry_run=dry_run)


def routing_pipeline(*, dry_run: bool = False) -> int:
    print("Step 1 — routing inputs")
    routing.inputs()
    print("Step 2 — routing build")
    code = routing.build(dry_run=dry_run)
    if code and not dry_run:
        print("Step 3 — routing validation: SKIPPED (build unavailable)")
        print("Step 4 — routing artifact validation: SKIPPED (no artifact)")
        return code
    if dry_run:
        print("Step 3 — routing validation: BLOCKED by missing build")
        print("Step 4 — routing artifact validation: BLOCKED by missing artifact")
        return OK
    return routing.validate()


def optimization_pipeline(*, dry_run: bool = False) -> int:
    print("Step 1 — Common Delivery Instance")
    code = instance.build(dry_run=dry_run)
    if code and not dry_run:
        print("Step 2 — Classical Optimization: SKIPPED (instance unavailable)")
        print("Step 3 — validation: SKIPPED")
        return code
    print("Step 2 — Classical Optimization")
    optimization.classical_run(dry_run=dry_run)
    print("Step 3 — validation: BLOCKED by upstream stages")
    return OK if dry_run else 3


def portal_pipeline(*, dry_run: bool = False) -> int:
    print("Portal state: dynamic canonical-artifact read; no handoff build required")
    return portal.check(dry_run=dry_run)


def full(*, dry_run: bool = False) -> int:
    print("Demand: DONE — current accepted artifacts will be reused")
    if dry_run:
        demand.validate(dry_run=True)
    print("Network: DONE / ACCEPTED — current accepted run will be reused")
    code = network_pipeline(dry_run=dry_run)
    if code and not dry_run:
        print("Routing: SKIPPED because Network validation failed")
        print("Downstream stages: SKIPPED")
        return code
    print("Routing: BLOCKED — production Routing Baseline runner and decisions are missing")
    routing_pipeline(dry_run=True if dry_run else False)
    print("Common Delivery Instance: SKIPPED — blocked by Routing")
    print("Classical Optimization: SKIPPED — blocked by Common Delivery Instance")
    print("Quantum: SKIPPED — not included automatically and upstream is incomplete")
    print("Delivery Simulation: SKIPPED — validated optimization output is missing")
    print("Fulfillment Evaluation: SKIPPED — validated simulation output is missing")
    print("Portal: PLANNED validation of current canonical state")
    if dry_run:
        portal.check(dry_run=True)
        return OK
    return 3
