from __future__ import annotations

from research_cli.core import (
    AUTHORITY_PATH,
    OK,
    ROOT,
    Step,
    accepted_paths,
    load_json,
    network_gate,
    print_gate,
    python_script,
    relative,
    run_steps,
    unavailable,
)


def status() -> int:
    ready, issues = network_gate()
    auth, network, acceptance_path, mapping = accepted_paths()
    print(f"Formal Network: {'COMPLETE / ACCEPTED' if ready else 'BLOCKED'}")
    print(f"Run: {auth['accepted_run']['run_id']}")
    print(f"Network: {relative(network)}")
    print(f"SHA-256: {auth['accepted_run']['network_sha256']}")
    print(f"Acceptance: {relative(acceptance_path)}")
    print(f"Stop mapping: {relative(mapping)}")
    print_gate("Authority gate", ready, issues)
    return OK if ready else 1


def acceptance() -> int:
    ready, issues = network_gate()
    _, _, acceptance_path, _ = accepted_paths()
    if not acceptance_path.is_file():
        print_gate("Formal Network Acceptance", False, issues)
        return 1
    value = load_json(acceptance_path)
    print(f"FORMAL_NETWORK_ACCEPTED = {str(value.get('FORMAL_NETWORK_ACCEPTED')).lower()}")
    print(f"Artifact: {relative(acceptance_path)}")
    for key in ("sumo_build", "lane_validity", "speed_validity", "permission_validity", "connectivity", "delivery_routeability"):
        print(f"{key}: {value.get('validation', {}).get(key, 'UNAVAILABLE')}")
    mapping = value.get("mapping", {})
    print(f"Stop mapping: {mapping.get('mapped', 'UNAVAILABLE')} / {mapping.get('total_stops', 'UNAVAILABLE')}")
    print_gate("Acceptance consistency", ready, issues)
    return OK if ready else 1


def validation_steps() -> tuple[Step, ...]:
    auth, network, acceptance_path, mapping = accepted_paths()
    return (
        Step(
            "Network completion policy/registry validation",
            python_script("05_src/traffic_simulation/network/validate_formal_completion_three_tier_registry.py"),
            configs=(ROOT / auth["registry"]["path"], ROOT / auth["schema"]["policy_path"], ROOT / auth["schema"]["record_path"]),
            next_diagnostic="./research network status",
        ),
        Step(
            "Network pipeline definition validation",
            python_script("05_src/traffic_simulation/network/validate_network_completion_pipeline.py"),
            configs=(ROOT / "reproducibility/config/traffic_simulation/network_completion_pipeline_v17.yml",),
            next_diagnostic="./research network status",
        ),
        Step(
            "Accepted network authority and artifact consistency",
            python_script("05_src/traffic_simulation/network/validate_current_network_completion_authority.py"),
            inputs=(network, acceptance_path, mapping),
            configs=(AUTHORITY_PATH,),
            next_diagnostic="./research network acceptance",
        ),
        Step(
            "Accepted lane/speed/permission/connectivity/mapping/routeability state",
            python_script("05_src/traffic_simulation/network/validate_research_map_portal.py"),
            inputs=(network, acceptance_path, mapping),
            configs=(ROOT / "reproducibility/config/research_portal/research_map_v1.yml",),
            next_diagnostic="./research network acceptance",
        ),
    )


def validate(*, dry_run: bool = False) -> int:
    ready, issues = network_gate()
    if not ready:
        print_gate("Required accepted network", False, issues)
        return 3
    result = run_steps(validation_steps(), dry_run=dry_run)
    if result == OK and not dry_run:
        return acceptance()
    return result


def build(*, dry_run: bool = False) -> int:
    return unavailable(
        title="Network build",
        missing=("isolated end-to-end Three-tier production runner with caller-supplied unique run ID",),
        dependency=(
            "existing completion/materialization/mapping/finalizer scripts use fixed run_1/run_2 paths",
            "accepted and historical artifacts must not be overwritten",
        ),
        dry_run=dry_run,
    )
