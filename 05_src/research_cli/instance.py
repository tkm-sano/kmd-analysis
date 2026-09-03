from __future__ import annotations

from research_cli.core import ROOT, OK, unavailable

MODULE = ROOT / "05_src/optimization/common_delivery_instance.py"


def status() -> int:
    print("Common Delivery Instance: PLANNED / NOT PRODUCTION COMPLETE")
    print(f"Current validator: {'AVAILABLE' if MODULE.is_file() else 'MISSING'} — 05_src/optimization/common_delivery_instance.py")
    print("Validated Routing Baseline prerequisite: MISSING")
    print("Production instance: MISSING")
    return OK


def build(*, dry_run: bool = False) -> int:
    return unavailable(
        title="Common Delivery Instance build",
        missing=("production instance generator", "validated Routing Baseline", "resolved depot/vehicle/battery constraints"),
        dry_run=dry_run,
    )


def validate(*, dry_run: bool = False) -> int:
    missing = []
    if not MODULE.is_file():
        missing.append("current 05_src/optimization/common_delivery_instance.py validator")
    missing.append("accepted production Common Delivery Instance")
    return unavailable(title="Common Delivery Instance validation", missing=missing, dry_run=dry_run)
