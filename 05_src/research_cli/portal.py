from __future__ import annotations

import os
import subprocess
import sys

from research_cli.core import OK, ROOT, Step, portal_summary, print_execution_context, python_script, run_steps, unavailable


def status() -> int:
    summary = portal_summary()
    print("Research Portal: READY")
    print(f"Current accepted network: {summary['accepted_network']['network_id']}")
    print(f"Current research stage: {summary['current_position']['current_stage']}")
    print(f"FORMAL_NETWORK_ACCEPTED = {str(summary['formal']['accepted']).lower()}")
    print("Start command: ./research portal start")
    return OK


def check(*, dry_run: bool = False) -> int:
    steps = (
        Step("Current network authority", python_script("05_src/traffic_simulation/network/validate_current_network_completion_authority.py"), next_diagnostic="./research network acceptance"),
        Step("Repository index", python_script("05_src/traffic_simulation/network/validate_research_repository_index.py"), next_diagnostic="./research artifacts"),
        Step("Portal research map and current artifacts", python_script("05_src/traffic_simulation/network/validate_research_map_portal.py"), next_diagnostic="./research portal status"),
    )
    return run_steps(steps, dry_run=dry_run)


def build(*, dry_run: bool = False) -> int:
    return unavailable(
        title="Portal build",
        missing=("formal standalone Portal state/handoff generator",),
        dependency=("current Portal reads canonical artifacts dynamically through research_portal/serve.py",),
        dry_run=dry_run,
    )


def start(*, port: int | None = None, dry_run: bool = False) -> int:
    command = (sys.executable, str(ROOT / "research_portal/serve.py"))
    step = Step("Research Portal server", command, inputs=(ROOT / "research_portal/serve.py",), outputs=())
    if dry_run:
        return run_steps((step,), dry_run=True)
    print_execution_context(step, dry_run=False)
    print(f"Starting Research Portal at http://127.0.0.1:{port or int(os.getenv('PORT', '8876'))}/")
    env = os.environ.copy()
    if port is not None:
        env["PORT"] = str(port)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(ROOT / "05_src") + (os.pathsep + existing if existing else "")
    try:
        return subprocess.call(command, cwd=ROOT, env=env)
    except KeyboardInterrupt:
        print("Portal stopped.")
        return OK
    except OSError as exc:
        print("Research Portal server: FAILED")
        print(f"Failed underlying command: {' '.join(command)}")
        print(f"Relevant log path: not declared by underlying server ({exc})")
        print("Next diagnostic command: ./research portal check")
        return 1
