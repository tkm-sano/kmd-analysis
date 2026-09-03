from __future__ import annotations

from research_cli.core import OK, unavailable


def status() -> int:
    print("Delivery Simulation: PLANNED / NOT PRODUCTION COMPLETE")
    print("Traffic/network validation simulations are not treated as delivery simulation.")
    print("Validated optimization output: MISSING")
    return OK


def run(*, dry_run: bool = False) -> int:
    return unavailable(title="Delivery Simulation run", missing=("production optimization-to-delivery-simulation runner", "validated optimization output"), dry_run=dry_run)


def validate(*, dry_run: bool = False) -> int:
    return unavailable(title="Delivery Simulation validation", missing=("production delivery simulation artifact and canonical validator",), dry_run=dry_run)
