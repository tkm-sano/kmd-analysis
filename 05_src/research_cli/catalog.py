from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandInfo:
    category: str
    command: str
    purpose: str
    implemented: str
    main_input: str
    main_output: str


COMMANDS = (
    CommandInfo("Demand", "demand build", "Baseline Demand → Requests → Stopsを再生成", "NO — safe integrated runner missing", "governed demand sources/config", "isolated demand artifacts"),
    CommandInfo("Demand", "demand validate", "既存需要実装とaccepted mappingを検証", "YES", "baseline demand, Requests, Stops", "read-only validation result"),
    CommandInfo("Demand", "demand status", "current需要状態を表示", "YES", "Portal/current artifacts", "status"),
    CommandInfo("Demand", "demand future", "Future Demand Parameterization", "NO — unresolved", "scenario assumptions", "scenario demand"),
    CommandInfo("Network", "network build", "Three-tier networkをisolated build", "NO — fixed-output runners unsafe", "source/formal inputs", "unique isolated run"),
    CommandInfo("Network", "network validate", "accepted networkと全accepted gateを検証", "YES", "current authority and accepted artifacts", "read-only validation result"),
    CommandInfo("Network", "network acceptance", "acceptance artifactをread-only表示", "YES", "network_acceptance.json", "acceptance state"),
    CommandInfo("Network", "network status", "current network状態を表示", "YES", "current authority", "status"),
    CommandInfo("Routing", "routing inputs", "Routing Baseline入力と未決定事項を表示", "YES", "accepted network/mapping/Requests/Stops", "readiness report"),
    CommandInfo("Routing", "routing build", "production routing costsを生成", "NO — runner/methodology missing", "routing inputs", "routing artifact"),
    CommandInfo("Routing", "routing validate", "Routing Baselineを検証", "NO — artifact/validator missing", "routing artifact", "validation result"),
    CommandInfo("Routing", "routing status", "Routing Baseline状態を表示", "YES", "current research map", "status"),
    CommandInfo("Instance", "instance build", "Common Delivery Instanceを生成", "NO — generator/upstream missing", "validated routing and constraints", "production instance"),
    CommandInfo("Instance", "instance validate", "Common Delivery Instanceを検証", "NO — current validator/artifact missing", "production instance", "validation result"),
    CommandInfo("Instance", "instance status", "Common Delivery Instance状態を表示", "YES", "repository", "status"),
    CommandInfo("Optimization", "optimization classical run", "Classical baselineを実行", "NO — solver/upstream missing", "validated common instance", "classical solution"),
    CommandInfo("Optimization", "optimization classical validate", "Classical resultを検証", "NO — result/validator missing", "classical solution", "validation result"),
    CommandInfo("Optimization", "optimization classical status", "Classical状態を表示", "YES", "repository", "status"),
    CommandInfo("Quantum", "quantum qubo build", "QUBOを生成", "NO", "fixed formulation/instance", "QUBO"),
    CommandInfo("Quantum", "quantum qubo validate", "QUBO equivalenceを検証", "NO", "QUBO/classical optimum", "validation result"),
    CommandInfo("Quantum", "quantum qaoa run", "QAOAを実行", "NO", "validated QUBO", "quantum candidate"),
    CommandInfo("Quantum", "quantum compare", "Classical vs Quantumを比較", "NO", "validated common results", "comparison evidence"),
    CommandInfo("Quantum", "quantum status", "Quantum工程状態を表示", "YES", "research map", "status"),
    CommandInfo("Simulation", "simulation run", "optimization planをdelivery simulationで実行", "NO", "validated optimization output", "simulation outcome"),
    CommandInfo("Simulation", "simulation validate", "delivery simulation結果を検証", "NO", "simulation outcome", "validation result"),
    CommandInfo("Simulation", "simulation status", "delivery simulation状態を表示", "YES", "research map", "status"),
    CommandInfo("Evaluation", "evaluate fulfillment", "delivery_fulfillment_rateを評価", "NO — canonical evaluator missing", "validated simulation output", "fulfillment metrics"),
    CommandInfo("Evaluation", "evaluate status", "評価工程状態を表示", "YES", "research map", "status"),
    CommandInfo("Portal", "portal start", "既存Research Portal serverを起動", "YES", "canonical artifacts", "local Portal server"),
    CommandInfo("Portal", "portal check", "Portalのauthority/map/artifact読取を検証", "YES", "authority/index/research map", "read-only validation result"),
    CommandInfo("Portal", "portal build", "standalone handoffを生成", "NO — generator missing", "canonical artifacts", "Portal handoff"),
    CommandInfo("Portal", "portal status", "Portal状態を表示", "YES", "dynamic Portal summary", "status"),
    CommandInfo("Pipeline", "pipeline network", "accepted network pipelineを検証・将来はisolated再build", "YES — accepted reuse/validation", "current accepted run", "validation result"),
    CommandInfo("Pipeline", "pipeline routing", "inputs → build → validationをorchestrate", "PARTIAL — stops at missing build", "accepted network and decisions", "routing artifact"),
    CommandInfo("Pipeline", "pipeline optimization", "instance → Classical → validationをorchestrate", "PARTIAL — blocked upstream", "validated routing", "classical baseline"),
    CommandInfo("Pipeline", "pipeline portal", "canonical state → Portal validation", "YES", "canonical artifacts", "validation result"),
    CommandInfo("Pipeline", "pipeline full", "end-to-end research stagesをgate順にorchestrate", "PARTIAL — stops at Routing", "governed upstream artifacts", "stage summary"),
    CommandInfo("Validation", "validate", "current authority/index/Portalを横断検証", "YES", "canonical current state", "read-only validation result"),
    CommandInfo("Inspection", "status", "研究全体の現在地を表示", "YES", "authority and research map", "status"),
    CommandInfo("Inspection", "artifacts", "canonical/current artifactsを一覧", "YES", "repository index/current authority", "artifact paths"),
    CommandInfo("Inspection", "commands", "研究commandの唯一の目次", "YES", "CLI catalog", "command index"),
)


def print_catalog() -> int:
    current = None
    for item in COMMANDS:
        if item.category != current:
            current = item.category
            print(f"\n{current}")
            print("-" * len(current))
        print(f"./research {item.command}")
        print(f"  purpose: {item.purpose}")
        print(f"  implemented: {item.implemented}")
        print(f"  input: {item.main_input}")
        print(f"  output: {item.main_output}")
    return 0
