#!/usr/bin/env python3
"""Provenance-complete R23 clean run; no historical result is an input."""
from __future__ import annotations
import csv, hashlib, json, os, resource, subprocess, sys, time
from pathlib import Path
from traffic_simulation.r20_route_ordering.core import build_expanded_qubo, encode_route, enumerate_routes, normalize_travel_time_matrix
from traffic_simulation.r22_ising_conversion.converter import convert_qubo_to_ising, evaluate_ising
from traffic_simulation.r22_ising_conversion.schema import coefficient_hash, ising_coefficient_hash
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config, R23Input

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent/'clean_runs'
ROUTING=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted/routing_arcs.csv'
SELECTION=ROOT/'reproducibility/outputs/traffic_simulation/r23_n5_scaling_authority/20260911_v1/n5_instance_selection.json'
DEPOT='DEP_006'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(): return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def matrix(customers):
    ids=[DEPOT,*customers]; rows=csv.DictReader(ROUTING.open())
    pairs={(r['origin_id'],r['destination_id']):float(r['travel_time_s']) for r in rows if r['origin_id']!=r['destination_id']}
    return {a:{b:(0.0 if a==b else pairs[(a,b)]) for b in ids} for a in ids}
def make_input(instance, customers):
    raw=matrix(customers); norm,tau=normalize_travel_time_matrix(DEPOT,customers,raw)
    exact=enumerate_routes(DEPOT,customers,raw)
    if exact['evaluated_permutations'] != 120: raise RuntimeError('exact reference enumeration incomplete')
    q=build_expanded_qubo(DEPOT,customers,norm,4.0); ising=convert_qubo_to_ising(q)
    bits=frozenset(tuple(encode_route(r[1:-1],customers)) for r in exact['optimal_routes'])
    spins=frozenset(tuple(1 if b==0 else -1 for b in x) for x in bits)
    return R23Input(instance_id=instance,n=5,customer_ids=tuple(customers),depot_id=DEPOT,
      ising_constant=ising.constant,ising_linear=ising.linear,ising_quadratic=ising.quadratic,
      ising_coefficient_hash=ising_coefficient_hash(ising),qubo_coefficient_hash=coefficient_hash(q),
      lambda_value=4.0,bound=3.0,exact_optimal_bitstrings=bits,exact_optimal_spin_states=spins,
      exact_optimal_routes=frozenset(tuple(r) for r in exact['optimal_routes']),normalized_matrix=norm,
      payload={'tau_max':tau,'independent_exact_cost':exact['best_route_travel_time']})
def main(instance):
    selected={x['instance_id']:x for x in json.loads(SELECTION.read_text())['selected']}; customers=selected[instance]['customer_ids']
    d=OUT/instance; d.mkdir(parents=True,exist_ok=True); start=time.time(); start_iso=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(start)); pid=os.getpid()
    (d/'RUN_START.json').write_text(json.dumps({'event':'RUN_START','timestamp':start_iso,'pid':pid,'host':os.uname().nodename,'git_commit':git(),'environment_path':sys.prefix,'command':sys.argv,'manifest_sha256':os.environ.get('CLEAN_MANIFEST_SHA256')},indent=2)+'\n')
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    try:
      inp=make_input(instance,customers); cfg=R23Config(p=1,optimizer='COBYLA',maxiter=300,max_evaluations=300,initial_parameter=0.1,initialization_id='fixed_0.1',seed=17,repetition=1,expectation_mode='exact_statevector',backend_method='statevector',device='CPU',optimization_level=1,max_logical_qubits=25,max_p=1,memory_limit_gib=8.0,probability_threshold=1e-12)
      result=run_single(inp,cfg,implementation='v4'); end=time.time();
      m=result['probability_metrics']; best=m.get('best_feasible_state') or {}; rec=best.get('record') or {}
      route=rec.get('route'); exact=[list(r) for r in inp.exact_optimal_routes]; found=route is not None and [DEPOT,*route,DEPOT] in exact
      payload={'schema_version':'r23-clean-run-v1','run_id':instance+'_clean_v1','instance_id':instance,'customers':customers,'depot':DEPOT,'n':5,'p':1,'lambda':4.0,'optimizer':'COBYLA','initial_parameters':result['initial_parameters'],'final_parameters':result['final_parameters'],'evaluation_cap':300,'backend':result['backend'],'shots':'NONE','run_classification':result['run_classification'],'optimizer_success':result['optimizer_success'],'nfev':result['nfev'],'termination':result['termination'],'termination_status':result['termination_status'],'exact_optimal_routes':exact,'best_decoded_feasible_route':[DEPOT,*route,DEPOT] if route else None,'exact_optimum_found':found,'independent_exact_cost':inp.payload['independent_exact_cost'],'decoded_objective':best.get('normalized_route_objective'),'P_feasible':m.get('P_feasible_exact'),'P_optimal':m.get('P_opt'),'probability_total':m.get('probability_total'),'invalid_probability_mass':m.get('invalid_probability_mass'),'renormalized':False,'timing':result['timing'],'objective_trace':result['objective_trace'],'source_commit':git(),'source_hashes':{'runner':sha(Path(__file__)),'qaoa':sha(ROOT/'05_src/traffic_simulation/r23_qaoa_aer/qaoa.py'),'optimized_metrics_v4':sha(ROOT/'05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py'),'hamiltonian':sha(ROOT/'05_src/traffic_simulation/r23_qaoa_aer/hamiltonian.py'),'core':sha(ROOT/'05_src/traffic_simulation/r20_route_ordering/core.py'),'routing_input':sha(ROUTING)},'resource':{'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'ru_maxrss_start_kib':before},'started_at':start_iso,'ended_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(end))}
      out=d/'result.json'; out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n'); end_sha=sha(Path(__file__))
      (d/'RUN_END.json').write_text(json.dumps({'event':'RUN_END','timestamp':payload['ended_at'],'pid':pid,'exit_code':0,'output_sha256':sha(out),'runner_sha256_end':end_sha,'source_commit_end':git(),'source_hashes_end':payload['source_hashes'],'optimizer_success':payload['optimizer_success'],'nfev':payload['nfev'],'termination':payload['termination'],'runtime_seconds':payload['timing']['T_total'],'peak_rss_kib':payload['resource']['ru_maxrss_kib']},indent=2)+'\n')
      print(json.dumps({'instance_id':instance,'status':payload['run_classification'],'success':payload['optimizer_success'],'nfev':payload['nfev'],'T_total':payload['timing']['T_total']}))
    except Exception as exc:
      end=time.time(); (d/'RUN_END.json').write_text(json.dumps({'event':'RUN_END','timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(end)),'pid':pid,'exit_code':1,'failure_type':type(exc).__name__,'message':repr(exc),'source_commit_end':git()},indent=2)+'\n'); raise
if __name__=='__main__': main(sys.argv[1])
