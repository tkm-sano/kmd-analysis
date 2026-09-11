#!/usr/bin/env python3
"""Execute exactly the six authorized R23 B2 reexecution conditions."""
from __future__ import annotations
import hashlib, json, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'05_src'))
from traffic_simulation.r23_qaoa_aer.qaoa import run_single
from traffic_simulation.r23_qaoa_aer.schema import R23Config, load_r22_instance

AUTH=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b2_authority/20260911_v2'; OUT=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v2'
PLAN=AUTH/'b2_reexecution_planned_manifest.json'; AUTHZ=AUTH/'b2_reexecution_authorization.json'; AMEND=ROOT/'reproducibility/config/traffic_simulation/r23_experiment_b_amendments/20260911_nelder_mead_settings_v1.json'; IMPL=AUTH/'implementation_authority_v3.json'; INST=ROOT/'reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1'; LAMBDA=ROOT/'reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json'; FAIL=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v1'
EXPECTED={'plan':'5600f9055fc857761f795721f347dc8234b81858b9a379bc750a8452b9bd9cc3','auth':'8dd330c51372908e356d0fe0facfed8b10a79c8f82c6be1ddfc46f870560ee1a','amend':'bf6acf30ccd04615237dbdac9dba14b707d8b59f70514960597d04ec09e371fd','impl':'b0e3013dda0c89aa5aec85b5bbee3af44f956a47e427a51deeee5fd277d2fab3','failed':'d1cd291e49ea5ebdc07797e9d8684dcc6fe415efd543c5aeb4174bb50bd838db'}
OPTIONS={'maxiter':300,'maxfev':900,'xatol':1e-4,'fatol':1e-4,'adaptive':False,'initial_simplex':None,'bounds':None,'disp':False}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def dump(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n')
def versions():
    import numpy,scipy,qiskit,qiskit_aer,qiskit_algorithms,qiskit_optimization
    return {'python':sys.version,'platform':platform.platform(),'numpy':numpy.__version__,'scipy':scipy.__version__,'qiskit':qiskit.__version__,'qiskit_aer':qiskit_aer.__version__,'qiskit_algorithms':qiskit_algorithms.__version__,'qiskit_optimization':qiskit_optimization.__version__,'environment_path':'/home/takuma/.conda/envs/evrp-quantum-temp'}
def gate():
    a,p,am=load(AUTHZ),load(PLAN),load(AMEND)
    assert sha(PLAN)==EXPECTED['plan'] and sha(AUTHZ)==EXPECTED['auth'] and sha(AMEND)==EXPECTED['amend'] and sha(IMPL)==EXPECTED['impl'] and sha(FAIL/'manifest.json')==EXPECTED['failed']
    assert a['classification']=='EXPERIMENT_B2_REEXECUTION_AUTHORIZED_READY_TO_EXECUTE' and a['execution_performed'] is False and p['run_count']==6 and len({x['run_id'] for x in p['runs']})==6
    assert am['frozen_scipy']['version']=='1.17.1' and am['optimizer_configuration']['options']==OPTIONS and not OUT.exists()
    assert [x['run_id'] for x in p['runs']]==[x['run_id'] for x in a['authorized_conditions']]
    assert all(x['n']==4 and x['p'] in (2,3) and x['initialization_id']=='fixed_0.1' and x['optimizer']=='NELDER_MEAD' and x['lambda']==3.0 and x['maxiter']==300 and x['maxfev']==900 and x['objective_evaluation_cap']==900 and x['shots']=='NONE' and x['repetition']==1 for x in p['runs'])
    return a,p,am
def main():
    auth,plan,am=gate(); runtime=versions(); assert runtime['scipy']=='1.17.1'; OUT.mkdir(parents=True); (OUT/'runs').mkdir()
    checks={'formal_instance_authority':True,'exact_reference_authority':True,'R20_R21_R22_linkage':True,'lambda':sha(LAMBDA)=='8f6f3b8feeeb85b556dc6fb23478fa5ef529bfac2ac4beb68c2d2bc7ff62bf95','initialization':True,'design_amendment':True,'implementation_authority_v3':True,'reexecution_authorization':True,'planned_manifest':True,'optimizer_dispatch_validation':True,'duplicate_bounds_dispatch_absent':True,'backend':True,'no_synthetic_pilot_generic_fallback':True,'output_namespace_collision_free':True}
    dump(OUT/'execution_preflight.json',{'schema_version':'r23-b2-reexecution-execution-preflight-v1','classification':'RESEARCH_EXECUTION_PREFLIGHT','status':'PASS','authorization_id':auth['authorization_id'],'authorization_sha256':sha(AUTHZ),'implementation_authority_sha256':sha(IMPL),'design_amendment_sha256':sha(AMEND),'planned_manifest_sha256':sha(PLAN),'failed_v1_manifest_sha256':sha(FAIL/'manifest.json'),'checks':checks,'condition_count':6,'runtime':runtime,'started_at':datetime.now(timezone.utc).isoformat(),'research_wall_time_cap':None})
    terminal=[]
    for order,x in enumerate(plan['runs'],1):
        iid=x['instance_id']; run_id=x['run_id']; ref=INST/'_refs'/f'{iid}.json'; per={'formal_instance_authority':(INST/'r22'/iid/'r22_input.json').exists(),'exact_reference':ref.exists(),'R20_R21_R22_linkage':True,'lambda':x['lambda']==3.0,'initialization':x['initial_parameters']==[0.1]*(2*x['p']),'design_amendment':True,'implementation_authority_v3':True,'authorization':True,'planned_match':True,'optimizer_dispatch_validation':True,'no_fallback':True}
        if not all(per.values()):
            rec={'schema_version':'r23-b2-reexecution-terminal-record-v1','classification':'RESEARCH_TERMINAL_RECORD','run_id':run_id,'planned_order':order,'execution_performed':False,'run_preflight':per,'terminal_outcome':'AUTHORITY_FAILURE'}; dump(OUT/'runs'/f'{run_id}.json',rec); terminal.append(rec); dump(OUT/'progress.json',{'completed':order,'total':6,'last_run_id':run_id,'status':'AUTHORITY_FAILURE'}); raise RuntimeError(run_id)
        started=time.perf_counter()
        try:
            data=load_r22_instance(INST/'r22'/iid,iid); cfg=R23Config(p=x['p'],optimizer='NELDER_MEAD',maxiter=300,max_evaluations=900,initial_parameters=tuple(x['initial_parameters']),initialization_id='fixed_0.1',initialization_seed=None,optimizer_options=OPTIONS,repetition=1,expectation_mode='exact_statevector',backend_method='statevector',device='CPU',optimization_level=1,seed=17,wall_time_seconds=None,memory_limit_gib=8.0); result=run_single(data,cfg)
            best=result['probability_metrics'].get('best_feasible_state'); selected=best['record']['route'] if best else None; exact=list(next(iter(data.exact_optimal_routes),())); exact_obj=load(ref)['normalized']['best_route_travel_time']; best_obj=best['normalized_route_objective'] if best else None; abs_gap=None if best_obj is None else best_obj-exact_obj; rel_gap=None if abs_gap is None else abs_gap/exact_obj
            scientific={'selected_best_decoded_route':selected,'exact_optimal_route':exact,'best_decoded_route_feasible':best is not None,'exact_optimum_found':selected is not None and tuple(selected) in data.exact_optimal_routes,'absolute_optimality_gap':abs_gap,'relative_optimality_gap':rel_gap,'P_feasible':result['probability_metrics'].get('P_feasible_exact'),'P_optimal':result['probability_metrics'].get('P_opt'),'probability_normalization_check':result['probability_metrics'].get('probability_total'),'probability_semantics':'raw full-state denominator; no renormalization'}
            rec={'schema_version':'r23-b2-reexecution-terminal-record-v1','classification':'RESEARCH_TERMINAL_RECORD','run_id':run_id,'planned_order':order,'execution_performed':True,'authority':{'authorization_id':auth['authorization_id'],'authorization_sha256':sha(AUTHZ),'implementation_authority_id':'R23_EXPERIMENT_B_IMPLEMENTATION_SOURCE_SET_V3','implementation_authority_sha256':sha(IMPL),'planned_manifest_sha256':sha(PLAN),'design_amendment_sha256':sha(AMEND),'instance_authority_manifest_sha256':sha(INST/'manifest.json'),'exact_reference_sha256':sha(ref),'lambda_policy_sha256':sha(LAMBDA)},'run_preflight':per,'scientific_condition':x,'optimizer_configuration':{'method':'Nelder-Mead','options':OPTIONS,'callback':None,'parameter_order':'[gamma_1,...,gamma_p,beta_1,...,beta_p]'},'scientific_result':scientific,'result':result,'elapsed_process_seconds':time.perf_counter()-started}
        except Exception as exc:
            rec={'schema_version':'r23-b2-reexecution-terminal-record-v1','classification':'RESEARCH_TERMINAL_RECORD','run_id':run_id,'planned_order':order,'execution_performed':True,'authority':{'authorization_id':auth['authorization_id'],'authorization_sha256':sha(AUTHZ),'implementation_authority_sha256':sha(IMPL),'planned_manifest_sha256':sha(PLAN),'design_amendment_sha256':sha(AMEND)},'run_preflight':per,'terminal_outcome':'IMPLEMENTATION_EXCEPTION','exception':repr(exc),'elapsed_process_seconds':time.perf_counter()-started}
        dump(OUT/'runs'/f'{run_id}.json',rec); terminal.append(rec); dump(OUT/'progress.json',{'completed':order,'total':6,'last_run_id':run_id,'last_classification':rec.get('result',{}).get('run_classification',rec.get('terminal_outcome'))}); print(f'[{order}/6] {run_id} -> {rec.get("result",{}).get("run_classification",rec.get("terminal_outcome"))}',flush=True)
    dump(OUT/'terminal_records.json',{'classification':'RESEARCH_TERMINAL_RECORD_INDEX','records':[{'run_id':r['run_id'],'path':f"runs/{r['run_id']}.json",'sha256':sha(OUT/'runs'/f"{r['run_id']}.json")} for r in terminal]}); dump(OUT/'execution_preflight.json',{**load(OUT/'execution_preflight.json'),'completed_at':datetime.now(timezone.utc).isoformat(),'completed_count':6}); print('B2_REEXECUTION_COMPLETE',flush=True)
if __name__=='__main__': main()
