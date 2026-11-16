"""Reproduce phase costs, fixed-pilot resources and quantum observations."""
import json
from pathlib import Path
import hashlib

DOC=Path(__file__).resolve().parent
ROOT=DOC.parents[2]
OUT=ROOT/'output/toc_delivery/comparison_design_20261116_v1'
def read(p):return json.loads(Path(p).read_text())

def main():
 telemetry=read(OUT/'design/TELEMETRY.json')
 analysis=read(OUT/'design/variance_ANALYSIS.json')
 rows=[];phases=[]
 for stage in ('selection_lean','selection_retained','variance','confirmation'):
  group=read(OUT/stage/'ALL_RESULTS.json');rows.extend(group)
  phases.append({'stage':stage,'attempts':len(group),'adopted':sum(r['adoptable'] for r in group),
    'wall_s':sum(r['T_attempt'] for r in group),
    'coordinator_setup_s':read(OUT/stage/'COORDINATOR_SETUP.json')['wall_s'],
    'measured_partial_export_s':sum(r.get('T_export') or 0 for r in group)})
 memory=[]
 for scale in ('S1','S2','S3'):
  group=[r for r in telemetry if r['stage']=='variance' and r['case_id']==scale]
  sampled=max(r.get('sampled_tree_peak_RSS_KiB') or 0 for r in group)
  native=max((r.get('native_resources') or {}).get('aggregate_RSS_upper_bound_KiB') or 0
             for r in rows if r['phase']=='variance_pilot' and r['case_id']==scale)
  parent=max(r.get('parent_RSS_highwater_KiB') or 0 for r in group)
  memory.append({'scale':scale,'sampled_worker_tree_peak_GiB':sampled/1048576,
    'native_tree_HWM_sum_GiB':native/1048576,'parent_HWM_GiB':parent/1048576,
    'conservative_memory_proxy_GiB':(max(sampled,native)+parent)/1048576})
 quantum=[r for r in telemetry if r['method']=='D']
 summary={'phase_costs':phases,'memory_by_scale':memory,
  'primary':next(r for r in analysis if r['case_id']=='S2'),
  'quantum_observations':{'started_calls':sum(r['quantum_started'] for r in quantum),
    'completed_calls':sum(r['quantum_completed_trace'] for r in quantum),
    'observed_training_shots':sum(r['observed_training_shots'] for r in quantum),
    'observed_final_shots':sum(r['observed_final_shots'] for r in quantum),
    'incomplete_calls':sum(r['incomplete_quantum_calls'] for r in quantum),
    'native_accounting_flag_incomplete_trials':sum(not r['shots_accounting_complete'] for r in quantum),
    'qubits':sorted({q for r in quantum for q in r['qubits_observed']}),
    'scope':'completed-call observations include unselected branches; native completeness flags separately retained'},
  'planned_trial_caps_s':sum(r['budget_wall_s'] for r in rows),
  'T_attempt_sum_s':sum(r['T_attempt'] for r in rows),
  'summary_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (DOC/'SUMMARY_DATA.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print('Measurement summary reproduced from stored pilot records')

if __name__=='__main__':main()
