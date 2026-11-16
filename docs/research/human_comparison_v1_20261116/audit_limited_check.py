#!/usr/bin/env python3
"""Read-only audit of the completed fixture's real code paths and resources."""
import csv
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.human_comparison_v1.contract import read,dump,digest,load_registration
from kmd_toc.human_comparison_v1.analysis import verify_session


def main():
 out=Path(sys.argv[1]).resolve();reg=load_registration(out/'registration/REGISTERED.json')
 rows=[];last_end=None;inputs=set();ODs=set();cpus=set(reg['cpu_ids'])
 for m in 'ABCD':
  r=verify_session(out/m,reg)
  assert r['status']=='success' and not r['observed'] and r['T_total_sec'] is None
  assert r['T_human_sec'] is None and r['T_machine_sec'] is None and r['T_compute_sec'] is None
  inputs.add(r['problem_hash']);ODs.add(r['OD_hash'])
  if last_end is not None:assert r['monotonic_start_ns']>last_end
  last_end=r['monotonic_end_ns']
  q={'method':m,'method_version':r['method_version'],'observed':False,'status':r['status'],
    'D_km_fixture':r['D_km'],'W_min_fixture':r['W_min'],'W_first_min_fixture':r['W_first_min'],
    'W_reload_min_fixture':r['W_reload_min'],'diagnostic_elapsed_sec':r['T_attempt_sec'],
    'diagnostic_algorithm_union_sec':r['diagnostic_elapsed']['T_compute_sec'],
    'adopted_T_total_sec':None,'plan_sha256':r['plan_sha256'],'evidence_path':r['evidence_path']}
  assert all(a['cleanup_proved'] for a in r['attempts'])
  if m=='A':
   assert not list((out/m).rglob('native'))
   final=r['attempts'][-1]['result']['human_specific']
   assert final['assignment_and_order_preserved'] and final['FCFS_valid']
   q['route']='manual_identity_order_capacity_split_FCFS'
  else:
   dest=next((out/m/'attempts').glob('*_evaluate/native'))
   native=read(dest/'worker_result.json');branches=native['parallel_branches']
   assert len(branches)==4 and len({b['pid'] for b in branches})==4
   assert {b['cpu_affinity'][0] for b in branches}==cpus and all(len(b['cpu_affinity'])==1 for b in branches)
   assert all(b['status']=='VALIDATED' for b in branches)
   events=[read(f)['event'] for f in dest.glob('branches/*/observation_*_end.json')]
   assert events.count('algorithm_generate_including_completion')==4
   assert 'classical_CP_SAT_completion' in events
   if m=='C':assert 'classical_OR_Routing' in events
   if m=='D':
    assert 'parameter_optimization_including_objective_simulation' in events
    assert native['total_quantum_calls']>0 and native['quantum_accounting_complete']
    assert native['quantum_backend_environment']['statevector_backend']=='qiskit'
   q.update(route=native['plan']['method_settings']['algorithm'],branches=branches,
    backend=native['quantum_backend_environment'],quantum_calls=native['total_quantum_calls'],
    all_training_shots=native['total_training_shots'],all_final_shots=native['total_final_shots'])
  rows.append(q)
 assert len(inputs)==len(ODs)==1
 decision=read(out/'ADOPTION.json')
 assert decision['IMPLEMENTED'] and not decision['MEASURED'] and not decision['COMPARABLE'] and not decision['formal_adoption']
 report={'status':'PASS','phase':'contract_check','real_human_measurements':0,
  'common_input_and_OD':True,'sequential_methods':True,'all_group_cleanup':True,
  'A_to_D_paths':rows,'empirical_statistics_produced':False}
 dump(out/'PATH_AUDIT.json',report)
 columns=['method','status','observed','D_km_fixture','W_min_fixture','W_first_min_fixture',
    'W_reload_min_fixture','diagnostic_elapsed_sec','diagnostic_algorithm_union_sec','adopted_T_total_sec','plan_sha256']
 with (out/'FIXTURE_DIAGNOSTICS.csv').open('x') as f:
  w=csv.DictWriter(f,columns,extrasaction='ignore');w.writeheader();w.writerows(rows)
 print(json.dumps({k:v for k,v in report.items() if k!='A_to_D_paths'}))


if __name__=='__main__':main()
