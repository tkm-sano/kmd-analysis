"""R23 remediation equivalence harness; never materializes probabilities_dict()."""
from __future__ import annotations
import csv, hashlib, itertools, json, os, resource, sys, time
from pathlib import Path
import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "05_src"))
from traffic_simulation.r20_route_ordering.core import (build_expanded_qubo, encode_route, enumerate_routes,
    normalize_travel_time_matrix, route_travel_time, validate_bitstring, ValidationStatus)
from traffic_simulation.r22_ising_conversion.converter import convert_qubo_to_ising, evaluate_ising
from traffic_simulation.r22_ising_conversion.schema import coefficient_hash, ising_coefficient_hash
from traffic_simulation.r23_qaoa_aer.hamiltonian import build_cost_operator, build_qaoa_circuit, repository_parameters
from traffic_simulation.r23_qaoa_aer.metrics import qiskit_label_to_bits, probability_metrics
from traffic_simulation.r23_qaoa_aer.schema import R23Input

OUT = Path(__file__).resolve().parent
DEPOT = "DEP_006"
CUSTOMERS = ["2026-01-01-13111-bldg-117556", "2026-01-01-13111-bldg-130096", "2026-01-01-13111-bldg-138702", "2026-01-01-13111-bldg-2510665", "2026-01-01-13111-bldg-79791"]
ROUTING = ROOT / "reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted/routing_arcs.csv"
TOL = 1e-12

def make_input(customers, iid):
    nodes = [DEPOT, *customers]
    rows = list(csv.DictReader(ROUTING.open(encoding="utf-8")))
    pairs = {(r["origin_id"], r["destination_id"]): float(r["travel_time_s"]) for r in rows if r["origin_id"] != r["destination_id"]}
    raw = {a: {b: (0.0 if a == b else pairs[(a,b)]) for b in nodes} for a in nodes}
    normalized, tau = normalize_travel_time_matrix(DEPOT, customers, raw)
    exact = enumerate_routes(DEPOT, customers, raw)
    qubo = build_expanded_qubo(DEPOT, customers, normalized, 4.0)
    ising = convert_qubo_to_ising(qubo)
    optimal_bits = frozenset(tuple(encode_route(r[1:-1], customers)) for r in exact["optimal_routes"])
    optimal_spins = frozenset(tuple(1 if b == 0 else -1 for b in bits) for bits in optimal_bits)
    return R23Input(iid, len(customers), tuple(customers), DEPOT, ising.constant, ising.linear, ising.quadratic,
        ising_coefficient_hash(ising), coefficient_hash(qubo), 4.0, 3.0, optimal_bits, optimal_spins,
        frozenset(tuple(r) for r in exact["optimal_routes"]), normalized,
        {"ising_global_minimum_energy": evaluate_ising(next(iter(optimal_spins)), ising), "tau_max": tau})

def simulate(inp, params):
    gamma, beta = repository_parameters(params, 1)
    qc = build_qaoa_circuit(inp, 1, gamma, beta)
    sim = AerSimulator(method="statevector", device="CPU")
    tqc = transpile(qc, sim, optimization_level=1, seed_transpiler=17); tqc.save_statevector()
    result = sim.run(tqc, seed_simulator=17).result()
    return Statevector(result.data(0)["statevector"]), tqc

def own_reference_indices(inp):
    # Independent construction: fill x[i,t] and check both one-hot constraints directly.
    out = []
    for route in itertools.permutations(range(inp.n)):
        bits = [0] * (inp.n * inp.n)
        for position, customer in enumerate(route): bits[customer * inp.n + position] = 1
        if all(sum(bits[i*inp.n:(i+1)*inp.n]) == 1 for i in range(inp.n)) and all(sum(bits[i::inp.n]) == 1 for i in range(inp.n)):
            out.append(sum(bit << i for i, bit in enumerate(bits)))
    return out

def candidate_indices(inp):
    return [sum(bit << i for i, bit in enumerate(encode_route(route, inp.customer_ids))) for route in itertools.permutations(inp.customer_ids)]

def compare(inp, params, include_full_small):
    state, tqc = simulate(inp, params); data = np.asarray(state.data)
    reference_probs = np.abs(data) ** 2
    ref_indices = own_reference_indices(inp); cand_indices = candidate_indices(inp)
    feasible = np.asarray(cand_indices, dtype=np.int64)
    optimal = np.asarray([i for i in cand_indices if tuple([(i >> q) & 1 for q in range(inp.n_logical)]) in inp.exact_optimal_bitstrings], dtype=np.int64)
    # Candidate path: only indexed amplitudes for reporting metrics; norm is direct statevector norm.
    candidate_p_total = float(np.vdot(data, data).real)
    candidate_pf = float(np.abs(data[feasible]) @ np.abs(data[feasible]))
    candidate_po = float(np.abs(data[optimal]) @ np.abs(data[optimal]))
    reference_p_total = float(reference_probs.sum(dtype=np.float64))
    reference_pf = float(reference_probs[np.asarray(ref_indices, dtype=np.int64)].sum(dtype=np.float64))
    reference_po = float(reference_probs[optimal].sum(dtype=np.float64))
    # Independent objective reference: diagonal energy evaluated from basis bits, in chunks.
    op = build_cost_operator(inp, include_constant=False)
    sparse_expectation = float(state.expectation_value(op).real + inp.ising_constant)
    # Chunked independent diagonal reference avoids a second full-size energy array.
    independent_expectation = 0.0
    for start in range(0, len(data), 1_048_576):
        stop = min(start + 1_048_576, len(data)); ids = np.arange(start, stop, dtype=np.uint64)
        energy = np.full(stop-start, float(inp.ising_constant), dtype=np.float64)
        signs = {}
        for q in set(inp.ising_linear) | {q for pair in inp.ising_quadratic for q in pair}: signs[q] = 1.0 - 2.0 * ((ids >> q) & 1)
        for q, c in inp.ising_linear.items(): energy += float(c) * signs[q]
        for (a,b), c in inp.ising_quadratic.items(): energy += float(c) * signs[a] * signs[b]
        independent_expectation += float(reference_probs[start:stop] @ energy)
    route_rows = []
    for route in itertools.permutations(inp.customer_ids):
        idx = sum(bit << i for i, bit in enumerate(encode_route(route, inp.customer_ids)))
        route_rows.append((float(reference_probs[idx]), route, idx))
    best = max(route_rows, key=lambda x: (x[0], x[2]))
    return {"parameters": list(params), "statevector_sha256": hashlib.sha256(data.tobytes()).hexdigest(),
      "state_dimension": len(data), "reference": {"P_total": reference_p_total, "P_feasible": reference_pf, "P_optimal": reference_po, "P_invalid": reference_p_total-reference_pf, "expectation": independent_expectation},
      "candidate": {"P_total": candidate_p_total, "P_feasible": candidate_pf, "P_optimal": candidate_po, "P_invalid": candidate_p_total-candidate_pf, "expectation": sparse_expectation},
      "differences": {"P_total": abs(reference_p_total-candidate_p_total), "P_feasible": abs(reference_pf-candidate_pf), "P_optimal": abs(reference_po-candidate_po), "P_invalid": abs((reference_p_total-reference_pf)-(candidate_p_total-candidate_pf)), "expectation": abs(independent_expectation-sparse_expectation)},
      "route_index_counts": {"reference": len(ref_indices), "candidate": len(cand_indices), "candidate_unique": len(set(cand_indices)), "candidate_reference_same_set": set(cand_indices)==set(ref_indices)},
      "best_feasible_route": list(best[1]), "best_feasible_basis_index": best[2], "transpiled_depth": tqc.depth(),
      "small_full_method": include_full_small}

def main():
    results = {"n2": compare(make_input(CUSTOMERS[:2], "equiv_n2"), [0.1,0.1], True), "n3": compare(make_input(CUSTOMERS[:3], "equiv_n3"), [0.1,0.1], True), "n4": compare(make_input(CUSTOMERS[:4], "equiv_n4"), [0.1,0.1], True)}
    points = {"A_rank01_initial": [0.1,0.1], "C_fixed_profiling": [0.37,-0.22]}
    n5 = {name: compare(make_input(CUSTOMERS, "routing_v18_n5_rank01"), p, False) for name,p in points.items()}
    # Three repetitions for the candidate post-processing benchmark on A; no dictionary path.
    inp = make_input(CUSTOMERS, "routing_v18_n5_rank01"); times=[]; rss=[]
    for _ in range(3):
        state,_ = simulate(inp, points["A_rank01_initial"]); data=np.asarray(state.data); idx=np.asarray(candidate_indices(inp),dtype=np.int64)
        before=time.perf_counter(); total=float(np.vdot(data,data).real); pf=float(np.abs(data[idx]) @ np.abs(data[idx])); po=float(np.abs(data[idx[-1:]]) @ np.abs(data[idx[-1:]])); invalid=total-pf; times.append({"total_norm":total,"P_feasible":pf,"P_optimal_lookup":po,"P_invalid":invalid,"elapsed_seconds":time.perf_counter()-before}); rss.append(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    out={"schema_version":"r23-n5-runtime-equivalence-remediation-v2","tolerance":TOL,"small_n":results,"n5":n5,"benchmark":{"repetitions":3,"postprocessing":times,"peak_rss_kib":max(rss),"peak_rss_gib":max(rss)/1048576,"note":"candidate indexed amplitudes; no probabilities_dict and no full Python object dictionary"},"environment":{"python":sys.version,"numpy":np.__version__}}
    (OUT/"harness_results.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"output":str(OUT/"harness_results.json"),"n5_points":list(n5),"peak_rss_gib":max(rss)/1048576}))
if __name__ == "__main__": main()
