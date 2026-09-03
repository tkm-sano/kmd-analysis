from __future__ import annotations

from research_cli.core import (
    BASELINE_DEMAND_CONFIG,
    BASELINE_DEMAND_PATH,
    OK,
    REQUESTS_PATH,
    ROOT,
    STOPS_PATH,
    Step,
    portal_summary,
    python_script,
    relative,
    run_steps,
    unavailable,
)


def status() -> int:
    summary = portal_summary()
    by_id = {node["id"]: node for node in summary["maps"]["implementation"]["nodes"]}
    print(f"Demand baseline: {'DONE' if by_id['baseline_demand']['status'] == 'COMPLETE' else by_id['baseline_demand']['status']}")
    print(f"Requests: {'DONE' if by_id['requests']['status'] == 'COMPLETE' else by_id['requests']['status']} — {relative(REQUESTS_PATH)}")
    print(f"Stops: {'DONE' if by_id['stops']['status'] == 'COMPLETE' else by_id['stops']['status']} — {relative(STOPS_PATH)}")
    print(f"Future Demand Parameterization: {by_id['future_demand_parameterization']['status']} / NOT IMPLEMENTED")
    return OK


def validate(*, dry_run: bool = False) -> int:
    steps = (
        Step(
            "Baseline Demand implementation validation",
            (sys_executable(), "-m", "pytest", "-q", "05_src/traffic_simulation/validation/test_prepare_baseline_demand.py"),
            inputs=(BASELINE_DEMAND_PATH,),
            configs=(BASELINE_DEMAND_CONFIG,),
            next_diagnostic="./research demand status",
        ),
        Step(
            "Accepted Requests / Stops mapping consistency",
            python_script("05_src/traffic_simulation/network/validate_current_network_completion_authority.py"),
            inputs=(REQUESTS_PATH, STOPS_PATH),
            next_diagnostic="./research network acceptance",
        ),
    )
    return run_steps(steps, dry_run=dry_run)


def sys_executable() -> str:
    import sys

    return sys.executable


def build(*, dry_run: bool = False) -> int:
    return unavailable(
        title="Demand build",
        missing=("isolated production runner covering Baseline Demand → Requests → Stops",),
        dependency=(
            "existing baseline runner writes fixed canonical outputs",
            "Requests / Stops generator is absent from the current checkout",
        ),
        dry_run=dry_run,
    )


def future() -> int:
    return unavailable(
        title="Future Demand Parameterization",
        missing=("adopted scenario parameters and production implementation",),
    )
