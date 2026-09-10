from __future__ import annotations

from research_cli.cli import build_parser, main
from research_cli.core import UNAVAILABLE, network_gate


def test_required_top_level_commands_exist() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    for command in (
        "demand",
        "network",
        "routing",
        "instance",
        "optimization",
        "quantum",
        "simulation",
        "evaluate",
        "portal",
        "pipeline",
        "validate",
        "status",
        "artifacts",
        "commands",
        "help",
    ):
        assert command in help_text


def test_current_network_gate_passes() -> None:
    ready, issues = network_gate()
    assert ready is True
    assert issues == []


def test_unimplemented_routing_build_is_safe() -> None:
    assert main(["routing", "build"]) == UNAVAILABLE


def test_unimplemented_routing_dry_run_is_successful_inspection() -> None:
    assert main(["routing", "build", "--dry-run"]) == 0


def test_full_pipeline_dry_run_stops_without_failure() -> None:
    assert main(["pipeline", "full", "--dry-run"]) == 0
