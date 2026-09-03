from __future__ import annotations

from research_cli.core import OK, unavailable


def classical_status() -> int:
    print("Classical Optimization: DOWNSTREAM / NOT PRODUCTION COMPLETE")
    print("Validated Routing Baseline: MISSING")
    print("Validated Common Delivery Instance: MISSING")
    print("Production classical solver: NOT IMPLEMENTED")
    return OK


def classical_run(*, dry_run: bool = False) -> int:
    return unavailable(
        title="Classical Optimization run",
        missing=("production classical solver", "validated Routing Baseline", "validated Common Delivery Instance"),
        dry_run=dry_run,
    )


def classical_validate(*, dry_run: bool = False) -> int:
    return unavailable(
        title="Classical Optimization validation",
        missing=("production solution artifact and canonical validator",),
        dependency=("validated Common Delivery Instance",),
        dry_run=dry_run,
    )
