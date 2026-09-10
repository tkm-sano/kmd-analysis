from __future__ import annotations

from research_cli.core import OK, unavailable


def status() -> int:
    print("QUBO formulation: PLANNED / NOT IMPLEMENTED")
    print("QUBO validation: PLANNED / NOT IMPLEMENTED")
    print("QAOA: FUTURE / NOT IMPLEMENTED")
    print("Quantum hardware execution: NOT IMPLEMENTED")
    print("Classical vs Quantum comparison: FUTURE / NOT IMPLEMENTED")
    return OK


def qubo_build(*, dry_run: bool = False) -> int:
    return unavailable(title="QUBO build", missing=("adopted QUBO formulation and production builder", "validated Common Delivery Instance"), dry_run=dry_run)


def qubo_validate(*, dry_run: bool = False) -> int:
    return unavailable(title="QUBO validation", missing=("validated QUBO artifact and canonical validator", "small-instance Classical optimum"), dry_run=dry_run)


def qaoa_run(*, dry_run: bool = False) -> int:
    return unavailable(title="QAOA run", missing=("validated QUBO and adopted QAOA production runner",), dry_run=dry_run)


def compare(*, dry_run: bool = False) -> int:
    return unavailable(title="Classical vs Quantum comparison", missing=("validated Classical and Quantum results under a common protocol",), dry_run=dry_run)
