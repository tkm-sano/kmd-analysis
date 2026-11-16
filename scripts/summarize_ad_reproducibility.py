"""Same-seed repeats, paired A extrema and observed D/W nondominance."""
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112_route_v2'))
def read(condition):return json.loads((ROOT/'experiments/S1'/condition/'result.json').read_text())
def triphash(result):return hashlib.sha256(json.dumps(result['plan']['trips'],sort_keys=True,separators=(',',':')).encode()).hexdigest()

if __name__=='__main__':
    checks=[]
    for method in ['A2','B','C','D']:
        before,after=('A2_angle0','A2_repeat_angle0') if method=='A2' else (method+'_primaryD_epsW_1',method+'_repeat_primaryD_epsW_1')
        a,b=read(before),read(after)
        checks.append({'method':method,'conditions':[before,after],'same_input_and_OD':a['input_hash']==b['input_hash'] and a['OD_hash']==b['OD_hash'],
                       'D_difference_km':b['D_km']-a['D_km'],'W_difference_min':b['W_min']-a['W_min'],'physical_trip_records_identical':triphash(a)==triphash(b),'T_program_s':[a['T_program_s'],b['T_program_s']],
                       'interpretation':'one same-seed repeat, not statistical repeatability proof'})
    (ROOT/'REPRODUCIBILITY_CHECK.json').write_text(json.dumps(checks,indent=2)+'\n')
    times=[]
    for path in sorted((ROOT/'experiments/S1').glob('D*/result.json')):
        r=json.loads(path.read_text())
        if r['status']!='FEASIBLE':continue
        e={x['name']:x['elapsed_s'] for x in r['timing_events']};q=r['plan']['method_settings']['quantum']
        times.append({'condition':path.parent.name,'input_s':e['input_load_end'],'classical_seed_s':e['D_classical_seed_completion_end']-e['input_load_end'],
                      'bridge_base_CG_s':e['D_classical_base_column_generation_end']-e['D_classical_seed_completion_end'],
                      'AOA_proposal_wall_s':e['D_AOA_round_1_end']-e['D_classical_base_column_generation_end'],
                      'training_simulator_wall_s':sum(x['result']['training_seconds'] for x in q),'Qiskit_circuit_wall_s':sum(x['result']['qiskit_seconds'] for x in q),
                      'expanded_catalogue_LP_IP_s':e['D_restricted_LP_IP_zero_face_end']-e['D_AOA_round_1_end'],
                      'assembly_s':e['method_all_processing_end']-e['D_restricted_LP_IP_zero_face_end'],
                      'common_validation_s':e['independent_validation_end']-e['independent_validation_start'],'T_program_s':r['T_program_s'],'quantum_hardware_time_s':None})
    with (ROOT/'D_TIME_BREAKDOWN.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(times[0]));w.writeheader();w.writerows(times)
    rows=[r for r in csv.DictReader((ROOT/'A_TO_D_COMPARISON.csv').open()) if r['scenario']=='S1' and r['status']=='FEASIBLE' and r['is_replicate']=='False']
    baseline=[r for r in rows if r['method'].startswith('A')];witness={}
    for field in ['D_km','W_min']:
        witness[field]={'minimum_plan':min(baseline,key=lambda r:float(r[field])),'maximum_plan':max(baseline,key=lambda r:float(r[field]))}
    (ROOT/'A_BOUND_WITNESSES.json').write_text(json.dumps({'bounds':witness,'separate_extrema_must_not_be_combined':True},indent=2)+'\n')
    pareto=[r for r in rows if not any(float(o['D_km'])<=float(r['D_km'])+1e-7 and float(o['W_min'])<=float(r['W_min'])+1e-7 and (float(o['D_km'])<float(r['D_km'])-1e-7 or float(o['W_min'])<float(r['W_min'])-1e-7) for o in rows)]
    with (ROOT/'S1_OBSERVED_DW_PARETO.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(pareto)
    print('same-seed metrics equal',all(x['same_input_and_OD'] and abs(x['D_difference_km'])<1e-7 and abs(x['W_difference_min'])<1e-7 for x in checks),'observed non-dominated plans',len(pareto))
