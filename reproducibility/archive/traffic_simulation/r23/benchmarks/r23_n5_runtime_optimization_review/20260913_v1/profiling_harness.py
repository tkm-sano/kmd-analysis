"""Read-only R23 n=5 profiling harness; not a formal scientific runner."""
from __future__ import annotations
import json, resource, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "05_src"))
from traffic_simulation.r23_qaoa_aer.qaoa import _statevector_and_expectation
from traffic_simulation.r23_qaoa_aer.hamiltonian import build_cost_operator, build_qaoa_circuit
from traffic_simulation.r23_qaoa_aer.metrics import probability_metrics
from traffic_simulation.r20_route_ordering.core import encode_route
from traffic_simulation.r23_n5_scaling.run_n5_scaling import make_input
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

INSTANCE = "routing_v18_n5_rank01"
PARAMETERS = ([0.1], [0.1])

def original_once(inp):
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time.perf_counter()
    value, probs, circuit, timing = _statevector_and_expectation(inp, *PARAMETERS, seed=17, optimization_level=1)
    t1 = time.perf_counter()
    metrics_t0 = time.perf_counter()
    metrics = probability_metrics(probs, inp, threshold=1e-12)
    metrics_t1 = time.perf_counter()
    return {"mode":"original", "objective":value, "timing":timing, "probability_metrics_seconds":metrics_t1-metrics_t0,
            "P_feasible":metrics["P_feasible_exact"], "P_optimal":metrics["P_opt"], "probability_total":metrics["probability_total"],
            "wall_seconds":t1-t0, "ru_maxrss_delta_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss-before,
            "records":len(probs), "circuit_metrics":circuit}

def prototype_once(inp):
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time.perf_counter()
    phases = {}
    s = time.perf_counter(); circuit = build_qaoa_circuit(inp, 1, *PARAMETERS); phases["circuit_construction"] = time.perf_counter()-s
    simulator = AerSimulator(method="statevector", device="CPU")
    s = time.perf_counter(); transpiled = transpile(circuit, simulator, optimization_level=1, seed_transpiler=17); phases["transpile"] = time.perf_counter()-s
    transpiled.save_statevector()
    s = time.perf_counter(); result = simulator.run(transpiled, seed_simulator=17).result(); phases["aer_and_result"] = time.perf_counter()-s
    s = time.perf_counter(); state = Statevector(result.data(0)["statevector"]); phases["statevector_materialization"] = time.perf_counter()-s
    s = time.perf_counter(); operator = build_cost_operator(inp, include_constant=False); value = float(state.expectation_value(operator).real + inp.ising_constant); phases["operator_and_expectation"] = time.perf_counter()-s
    s = time.perf_counter(); probs = state.probabilities(); phases["probability_array"] = time.perf_counter()-s
    feasible_indices = []
    optimal_indices = set()
    for route in __import__("itertools").permutations(inp.customer_ids):
        bits = list(encode_route(route, inp.customer_ids))
        index = sum(bit << i for i, bit in enumerate(bits))
        feasible_indices.append(index)
        if tuple(bits) in inp.exact_optimal_bitstrings: optimal_indices.add(index)
    s = time.perf_counter(); p_feasible = float(probs[feasible_indices].sum()); p_optimal = float(probs[list(optimal_indices)].sum()); phases["feasible_index_aggregation"] = time.perf_counter()-s
    phases["other_measured_harness"] = time.perf_counter()-t0-sum(phases.values())
    return {"mode":"equivalent_index_prototype", "objective":value, "P_feasible":p_feasible, "P_optimal":p_optimal,
            "probability_total":float(probs.sum()), "feasible_count":len(feasible_indices), "phases":phases,
            "wall_seconds":time.perf_counter()-t0, "ru_maxrss_delta_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss-before,
            "circuit_depth":transpiled.depth()}

def main():
    inp = make_input(INSTANCE, ["2026-01-01-13111-bldg-117556", "2026-01-01-13111-bldg-130096", "2026-01-01-13111-bldg-138702", "2026-01-01-13111-bldg-2510665", "2026-01-01-13111-bldg-79791"])
    original = [] if "--prototype-only" in sys.argv else [original_once(inp)]
    output = {"schema_version":"r23-n5-runtime-profiling-v1", "formal_scientific_run":False, "instance":INSTANCE, "parameters":PARAMETERS,
              "original":original, "prototype":[prototype_once(inp), prototype_once(inp), prototype_once(inp)]}
    out = Path(__file__).with_name("profiling_results.json")
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({"output":str(out), "original_wall":(output["original"][0]["wall_seconds"] if output["original"] else None), "prototype_walls":[x["wall_seconds"] for x in output["prototype"]]}))
if __name__ == "__main__": main()
