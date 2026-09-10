#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--constraints", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    instance = Path(args.instance)
    constraints = Path(args.constraints)
    instance_hash = sha(instance / "common_instance.json")
    instance_id = json.loads((instance / "common_instance.json").read_text())['instance_id']
    constraint_hash = sha(constraints / "constraint_spec.json")

    names = ["Customer Visit", "Depot Departure/Return", "Flow Conservation", "Subtour Elimination", "Vehicle Assignment", "Capacity", "Time Window", "Time Propagation", "Operating Time", "Battery/SOC", "Initial/Final SOC", "Charging", "Reachability"]
    implementations = [
        "RoutingModel node visit plus optional customer disjunction; exact after objective contract is fixed",
        "RoutingModel start/end at depot index 0",
        "RoutingModel route successor flow; independent validator required",
        "RoutingModel route construction plus validator; no disconnected route output",
        "Single RoutingModel vehicle assignment plus validator",
        "AddDimensionWithVehicleCapacity using payload_mass_kg=m_i; delivery_request_count=q_i remains separate",
        "Time dimension with service-start cumul and waiting",
        "Time dimension plus explicit service/charging event transitions; custom model required for charging",
        "Conditional check on enabled flag; baseline disabled",
        "Custom CP-SAT energy/SOC state transitions; RoutingDimension alone is insufficient",
        "Initial SOC fixed at 1.00; depot return SOC >= 0.20 in custom state model",
        "Event-expanded CP-SAT/custom constraints with derived charger event slots; repeated visits permitted and consecutive charger events forbidden",
        "Remove unreachable arcs from allowed arc set; null unreachable is never entered",
    ]
    mapping = []
    for index, (name, implementation) in enumerate(zip(names, implementations), start=1):
        mapping.append({
            "constraint_id": f"HC{index:02d}", "r16_meaning": name,
            "or_tools_implementation": implementation,
            "exact_or_approximate": ("disabled baseline" if index == 9 else "exact finite event-slot encoding for n+1 slots; implementation deferred to R18" if index == 12 else "exact design"),
            "implementation_location": "R17 specification; implementation deferred to R18",
            "validator_check": f"R16 contract check for HC{index:02d}",
            "unresolved_limitation": "" if index == 12 else "",
        })

    solver_config = {
        "ortools_version": "9.12.4544", "first_solution_strategy": "PATH_CHEAPEST_ARC",
        "local_search_metaheuristic": "GUIDED_LOCAL_SEARCH",
        "time_limit_seconds": 300,
        "random_seed": 20260909, "num_workers": 1,
        "deterministic": True, "logging": True, "solution_limit": 1000,
        "scope": "fixture_implementation_validation_only; not production_tuning",
    }
    output_schema = {
        "solver_status": "string", "objective_components": "object", "vehicle_routes": "array",
        "visited_customers": "array", "unserved_customers": "array", "node_sequence": "array",
        "arrival_time_s": "array", "service_start_time_s": "array", "waiting_time_s": "array",
        "service_time_s": "array", "departure_time_s": "array", "soc_before_after_movement": "array",
        "charging_events": "array", "charging_duration_s": "array", "soc_after_charging": "array",
        "route_distance_m": "number", "route_travel_time_s": "number", "total_operating_time_s": "number",
        "capacity_trajectory": "array", "delivery_request_count": "array", "payload_mass_kg": "array", "instance_hash": "string", "constraint_version": "string",
        "solver_config_hash": "string",
    }
    blockers = []
    spec = {
        "formulation_version": "evrp-ortools-formulation-v1",
        "instance_id": instance_id,
        "constraint_version": "evrp-common-hard-constraints-v1", "instance_hash": instance_hash,
        "constraint_spec_hash": constraint_hash,
        "solver_backend_family": "OR-Tools 9.12.4544; RoutingModel plus CP-SAT/custom event-state formulation",
        "formulation_status": "READY_FOR_R18_PENDING_EXECUTION",
        "node_index_rule": "R15 node_order and solver_index are authoritative; depot index 0, customers 1..10, charger 11",
        "vehicle_rule": "vehicle_order from R15; vehicle index 0; depot start/end index 0",
        "arc_cost": "R15 travel_time_s by directed arc; R12 route objective remains separate routing-input provenance",
        "callbacks": {
            "transit": "R15 travel_time_s by directed arc", "distance": "R15 distance_m for reporting",
            "demand": "customer q_i; depot/charger 0",
            "time": "travel_time_s plus service/wait/charge transitions in seconds",
        "capacity": "payload_mass_kg=m_i in kg; vehicle payload_capacity_kg=2000 applies directly; q_i is not kg",
        },
        "unserved": {"representation": "optional customer disjunction / visited boolean; unserved allowed", "penalty": "lexicographic two-phase solve: minimize unserved first, then travel time; numeric penalty not fixed in R17"},
        "objective_priority": ["minimize unserved customers/delivery requests", "then minimize total travel time; distance is reporting/tiebreak only and not R12 route selection"],
        "payload_model": {"definition": "m_i=payload mass of customer i", "delivery_request_count_field": "delivery_request_count=q_i", "payload_mass_field": "payload_mass_kg=m_i", "assignment": "constant 1.1 kg per selected customer", "unit": "kg", "classification": "ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY", "source": "Dalla Chiara et al. (2020), observed delivery-weight median 1.1 kg", "transformation": "copy 1.1 kg to each customer; no q_i-to-kg conversion", "random_seed": "not_applicable_constant", "production_status": "fixture-only"},
        "capacity_note": "Capacity is applied to sum(payload_mass_kg=m_i) in kg against vehicle payload_capacity_kg=2000. q_i=delivery_request_count is separate.",
        "time_model": {"unit": "seconds", "service_start_window": "R15 e_i/l_i hours converted by *3600", "transition": "arrival_j >= departure_i + travel_time_ij; service and waiting explicit; charging duration explicit"},
        "soc_model": {"method": "custom CP-SAT energy state transitions, not a plain RoutingDimension", "energy": "distance_km * 0.35344827586206895 kWh/km", "initial_soc": 1.0, "minimum_soc": 0.2, "return_minimum_soc": True},
        "charging_model": {"station": "R11 adopted station only", "effective_power_kw": 70, "max_session_duration_min": 30, "post_soc_max": 1.0, "revisit": "multiple events allowed; consecutive-session bypass forbidden; no R16 count cap", "finite_encoding": "charger event copies/slots k=1..n+1", "copy_count": "n+1; fixture n=10 => 11", "derivation": "k served customers yield k+2 non-charging visits and k+1 gaps; no consecutive charger visits permits at most one event per gap; k<=n", "status": "FIXED_FOR_R17; route-structure-derived"},
        "reachability": "unreachable R15 arcs removed from allowed arc set; no finite penalty substitution",
        "solver_config": solver_config, "r18_output_schema": output_schema, "mapping_table": mapping, "blockers": blockers,
    }
    (out / "ortools_formulation_spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    (out / "hc_mapping_table.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
    (out / "r18_solver_config.json").write_text(json.dumps(solver_config, ensure_ascii=False, indent=2) + "\n")
    (out / "r18_execution_contract.json").write_text(json.dumps({"instance_id": spec["instance_id"], "instance_hash": instance_hash, "constraint_version": spec["constraint_version"], "formulation_version": spec["formulation_version"], "runner": "NOT_IMPLEMENTED_R17_ONLY", "execution": "R18_ONLY_NOT_EXECUTED", "output_schema": "r18_output_schema", "solver_config": "r18_solver_config.json", "status": "READY_PENDING_R18"}, ensure_ascii=False, indent=2) + "\n")
    (out / "r18_output_schema.json").write_text(json.dumps(output_schema, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "READY_PENDING_R18", "blockers": blockers}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
