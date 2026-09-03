from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from research_cli import demand, evaluate, instance, network, optimization, pipeline, portal, quantum, routing, simulation
from research_cli.catalog import print_catalog
from research_cli.inspection import artifacts, status, validate

Handler = Callable[..., int]


def add_action(parent: argparse._SubParsersAction, name: str, help_text: str, handler: Handler, *, dry_run: bool = False) -> argparse.ArgumentParser:
    parser = parent.add_parser(name, help=help_text, description=help_text)
    if dry_run:
        parser.add_argument("--dry-run", action="store_true", help="print dependencies and underlying commands without changing artifacts")
    parser.set_defaults(handler=handler)
    return parser


def domain(subparsers: argparse._SubParsersAction, name: str, help_text: str) -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:
    parser = subparsers.add_parser(name, help=help_text, description=help_text)
    return parser, parser.add_subparsers(dest=f"{name}_command", metavar="COMMAND", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="./research",
        description="Unified thin command hub for governed research pipelines and validators.",
        epilog="Run './research commands' for the canonical command index.",
    )
    top = parser.add_subparsers(dest="command", metavar="COMMAND")

    demand_parser, commands = domain(top, "demand", "Build, validate, and inspect governed demand artifacts")
    add_action(commands, "build", "Run the existing Baseline Demand → Requests → Stops production pipeline", demand.build, dry_run=True)
    add_action(commands, "validate", "Run existing demand and accepted mapping validators", demand.validate, dry_run=True)
    add_action(commands, "status", "Show current demand status", demand.status)
    add_action(commands, "future", "Show Future Demand Parameterization availability", demand.future)

    network_parser, commands = domain(top, "network", "Build, validate, and inspect the governed Formal/SUMO network")
    add_action(commands, "build", "Run an isolated Three-tier network build", network.build, dry_run=True)
    add_action(commands, "validate", "Validate current accepted network through existing validators", network.validate, dry_run=True)
    add_action(commands, "acceptance", "Read current acceptance without modifying it", network.acceptance)
    add_action(commands, "status", "Show current network status", network.status)

    routing_parser, commands = domain(top, "routing", "Build, validate, and inspect Routing Baseline")
    add_action(commands, "build", "Build production Routing Baseline when available", routing.build, dry_run=True)
    add_action(commands, "validate", "Validate production Routing Baseline when available", routing.validate, dry_run=True)
    add_action(commands, "status", "Show Routing Baseline status", routing.status)
    add_action(commands, "inputs", "Show required Routing Baseline inputs and unresolved decisions", routing.inputs)

    instance_parser, commands = domain(top, "instance", "Build and validate the Common Delivery Instance")
    add_action(commands, "build", "Build production Common Delivery Instance when available", instance.build, dry_run=True)
    add_action(commands, "validate", "Validate production Common Delivery Instance when available", instance.validate, dry_run=True)
    add_action(commands, "status", "Show Common Delivery Instance status", instance.status)

    optimization_parser, optimization_commands = domain(top, "optimization", "Run and validate optimization methods")
    classical_parser, classical_commands = domain(optimization_commands, "classical", "Run and validate Classical Optimization")
    add_action(classical_commands, "run", "Run production Classical Optimization when available", optimization.classical_run, dry_run=True)
    add_action(classical_commands, "validate", "Validate Classical Optimization output when available", optimization.classical_validate, dry_run=True)
    add_action(classical_commands, "status", "Show Classical Optimization status", optimization.classical_status)

    quantum_parser, quantum_commands = domain(top, "quantum", "Build and validate QUBO/QAOA and comparison stages")
    qubo_parser, qubo_commands = domain(quantum_commands, "qubo", "Build and validate QUBO")
    add_action(qubo_commands, "build", "Build production QUBO when available", quantum.qubo_build, dry_run=True)
    add_action(qubo_commands, "validate", "Validate QUBO equivalence when available", quantum.qubo_validate, dry_run=True)
    qaoa_parser, qaoa_commands = domain(quantum_commands, "qaoa", "Run QAOA")
    add_action(qaoa_commands, "run", "Run production QAOA when available", quantum.qaoa_run, dry_run=True)
    add_action(quantum_commands, "compare", "Compare validated Classical and Quantum results", quantum.compare, dry_run=True)
    add_action(quantum_commands, "status", "Show Quantum Optimization status", quantum.status)

    simulation_parser, commands = domain(top, "simulation", "Run and validate delivery simulation")
    add_action(commands, "run", "Run production delivery simulation when available", simulation.run, dry_run=True)
    add_action(commands, "validate", "Validate delivery simulation output when available", simulation.validate, dry_run=True)
    add_action(commands, "status", "Show delivery simulation status", simulation.status)

    evaluate_parser, commands = domain(top, "evaluate", "Evaluate governed research outcomes")
    add_action(commands, "fulfillment", "Evaluate delivery_fulfillment_rate when canonical evaluator is available", evaluate.fulfillment, dry_run=True)
    add_action(commands, "status", "Show evaluation status", evaluate.status)

    portal_parser, commands = domain(top, "portal", "Start, build, validate, and inspect Research Portal")
    start = add_action(commands, "start", "Start the existing Research Portal server", portal.start, dry_run=True)
    start.add_argument("--port", type=int, help="set the existing Portal PORT environment value")
    add_action(commands, "check", "Validate Portal reads current canonical state", portal.check, dry_run=True)
    add_action(commands, "build", "Build a standalone Portal handoff when available", portal.build, dry_run=True)
    add_action(commands, "status", "Show Research Portal status", portal.status)

    pipeline_parser, commands = domain(top, "pipeline", "Run governed stage groups with dependency gates")
    add_action(commands, "network", "Reuse/validate current network or run isolated build when available", pipeline.network_pipeline, dry_run=True)
    add_action(commands, "routing", "Run routing inputs → build → validation", pipeline.routing_pipeline, dry_run=True)
    add_action(commands, "optimization", "Run instance → Classical Optimization → validation", pipeline.optimization_pipeline, dry_run=True)
    add_action(commands, "portal", "Run canonical Portal state validation", pipeline.portal_pipeline, dry_run=True)
    add_action(commands, "full", "Run full research pipeline until the first closed dependency gate", pipeline.full, dry_run=True)

    validate_parser = top.add_parser("validate", help="Validate current authority, repository index, and Portal")
    validate_parser.add_argument("--dry-run", action="store_true")
    validate_parser.set_defaults(handler=validate)
    top.add_parser("status", help="Show research-wide current status").set_defaults(handler=status)
    top.add_parser("artifacts", help="List canonical/current artifacts").set_defaults(handler=artifacts)
    top.add_parser("commands", help="Show the canonical research command index").set_defaults(handler=print_catalog)
    top.add_parser("help", help="Show top-level help").set_defaults(handler=lambda: (parser.print_help() or 0))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 0
    kwargs = vars(args).copy()
    handler = kwargs.pop("handler")
    for key in tuple(kwargs):
        if key.endswith("_command") or key == "command":
            kwargs.pop(key)
    try:
        return handler(**kwargs)
    except (OSError, ValueError, KeyError) as exc:
        print(f"CLI orchestration failed: {exc}", file=sys.stderr)
        print("Next diagnostic command: ./research status", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
