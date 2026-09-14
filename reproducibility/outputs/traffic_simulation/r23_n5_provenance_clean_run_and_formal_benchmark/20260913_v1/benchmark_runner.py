#!/usr/bin/env python3
import csv,json,resource,subprocess,sys
from pathlib import Path
from traffic_simulation.r20_route_ordering.core import build_expanded_qubo,encode_route,enumerate_routes,normalize_travel_time_matrix
from traffic_simulation.r22_ising_conversion.converter import convert_qubo_to_ising
from traffic_simulation.r22_ising_conversion.schema import coefficient_hash,ising_coefficient_hash
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config,R23Input
ROOT=Path(__file__).resolve().parents[5]; ROUTING=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted/routing_arcs.csv'; DEPOT='DEP_006'
IDS=['2026-01-01-13111-bldg-117556','2026-01-01-13111-bldg-130096','2026-01-01-13111-bldg-138702']
def make_input():
    nodes=[DEPOT,*IDS]; rows=csv.DictReader(ROUTING.open()); pairs={(r['origin_id'],r['destination_id']):float(r['travel_time_s']) for r in rows if r['origin_id']!=r['destination_id']}; raw={a:{b:(0.0 if a==b else pairs[(a,b)]) for b in nodes} for a in nodes}; norm,tau=normalize_travel_time_matrix(DEPOT,IDS,raw); exact=enumerate_routes(DEPOT,IDS,raw); q=build_expanded_qubo(DEPOT,IDS,norm,4.0); ising=convert_qubo_to_ising(q); bits=frozenset(tuple(encode_route(r[1:-1],IDS)) for r in exact['optimal_routes']); spins=frozenset(tuple(1 if b==0 else -1 for b in x) for x in bits)
    return R23Input(instance_id='controlled_n3_rank01',n=3,customer_ids=tuple(IDS),depot_id=DEPOT,ising_constant=ising.constant,ising_linear=ising.linear,ising_quadratic=ising.quadratic,ising_coefficient_hash=ising_coefficient_hash(ising),qubo_coefficient_hash=coefficient_hash(q),lambda_value=4.0,bound=3.0,exact_optimal_bitstrings=bits,exact_optimal_spin_states=spins,exact_optimal_routes=frozenset(tuple(r) for r in exact['optimal_routes']),normalized_matrix=norm,payload={'tau_max':tau})
def main():
    impl=sys.argv[1]; rep=int(sys.argv[2]); inp=make_input(); cfg=R23Config(p=1,optimizer='COBYLA',maxiter=20,max_evaluations=20,initial_parameter=0.1,initialization_id='fixed_0.1',seed=17,repetition=1,expectation_mode='exact_statevector',backend_method='statevector',device='CPU',optimization_level=1,max_logical_qubits=9,max_p=1,memory_limit_gib=8.0,probability_threshold=1e-12); result=run_single(inp,cfg,implementation=impl); m=result['probability_metrics']; best=m.get('best_feasible_state') or {}; rec=best.get('record') or {}; print(json.dumps({'implementation':impl,'rep':rep,'n':3,'T_TOTAL':result['timing']['T_total'],'T_AER':result['timing']['T_Aer_total'],'T_POSTPROCESS':result['timing']['T_decode_total'],'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'objective':best.get('normalized_route_objective'),'P_feasible':m.get('P_feasible_exact'),'P_optimal':m.get('P_opt'),'optimizer_success':result['optimizer_success'],'nfev':result['nfev'],'termination':result['termination_status'],'route':rec.get('route'),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}))
if __name__=='__main__': main()
