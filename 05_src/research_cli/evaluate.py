from __future__ import annotations

from research_cli.core import OK, unavailable


def status() -> int:
    print("Fulfillment Evaluation: PLANNED / NOT IMPLEMENTED")
    print("Primary metric specification: delivery_fulfillment_rate = delivered_parcel_equivalent / total_parcel_equivalent")
    print("Canonical evaluator: MISSING")
    print("Denominator scope and time horizon: UNRESOLVED")
    return OK


def fulfillment(*, dry_run: bool = False) -> int:
    return unavailable(title="Fulfillment Evaluation", missing=("canonical fulfillment evaluator", "validated delivery simulation output", "fixed denominator scope and time horizon"), dry_run=dry_run)
