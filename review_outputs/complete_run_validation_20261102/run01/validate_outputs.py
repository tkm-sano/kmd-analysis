"""Independent readback of new manifests, saved native events and synthetic DC."""
import json,hashlib,xml.etree.ElementTree as ET,sys,collections
import numpy as np
from common import *
from contracts import delivery_event,scalar_dc
sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate
from kmd_quantitative.simulation.trajectory_io import read_dc_input
def main():
 protect_previous();checks=[]
 def ck(name,ok,detail=None):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
 a=rows(O/'A_COMPLETE_RUNS.csv');b=rows(O/'B_COMPLETE_RUNS.csv');ar=rows(O/'A_OPERATION_RUN_LINKS.csv');br=rows(O/'B_PLAN_RUN_LINKS.csv');four=rows(O/'A_FOUR_CONDITION_LINKS.csv');mechanism=rows(O/'A_ADDITIONAL_MECHANISM_RUNS.csv')
 payloads={}
 with (O/'RUN_INPUTS.jsonl').open() as h:
  for line in h:
   x=json.loads(line);cid=x['candidate_id'];p=x['payload'];payloads[cid]=x
   if x['run_id']:
    independent=json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode();ck('run content sha '+cid,x['run_id']=='RUN-'+hashlib.sha256(independent).hexdigest())
    directory=('A_MECHANISM_INPUTS' if cid.startswith('AMECH') else 'A_INPUTS' if cid.startswith('D12') else 'B_INPUTS');vp=O/directory/cid/'vehicle.xml';v=ET.parse(vp).getroot().find('vehicle')
    ck('materialized vehicle '+cid,dict(v.attrib)==p['vehicle'] and v.find('route').get('edges').split()==p['road_edges'] and [dict(s.attrib) for s in v.findall('stop')]==p['stops'])
   else:ck('unbound candidate no full ID '+cid,bool(p['unbound']) and p['road_edges'] is None)
 ck('A references',len(ar)==2808 and len({(x['scenario_id'],x['PID']) for x in ar})==2808)
 ck('B references',len(br)==36800 and len({(x['family'],x['config_id'],x['problem_id'],x['rep']) for x in br})==36800)
 ck('all references bound or explicitly unbound',all(x['run_id'] or x['input_status']=='UNBOUND' for x in br))
 ck('four mechanism references',len(four)==9216 and all(x['run_id'] for x in four))
 ck('mechanism distinct policy',len(mechanism)==15 and not {x['run_id'] for x in mechanism}&{x['run_id'] for x in a})
 # Saved A normalization: this changes only the new event adapter, not prior evidence status.
 task=rows(U/'review_outputs/causal_engineering_audit_20261027/run01/A_NATIVE_TASK_COMPLETION.csv');events=[]
 for x in task:
  stops=ET.parse(use(x['stop_source'])).getroot().findall('stopinfo');s=stops[int(x['stop_order'])-1]
  ev=delivery_event(stop_start=float(s.get('started')),stop_end=float(s.get('ended')),ready=float(x['ready_s']),service=102,deadline=float(x['D03_completion_deadline_s']))
  ck('saved A candidate agreement '+x['run_id']+'/'+x['task_id'],ev['work_complete_model_s']==float(x['model_completion_s']))
  events.append({'run_id':x['run_id'],'PID':x['PID'],'task_id':x['task_id'],'physical_arrival_s':None,**ev,'q_PE':x['q_PE'],'deadline_D03_s':x['D03_completion_deadline_s'],'evidence':'SAVED_ZERO_DEPARTURE_NATIVE_DIAGNOSTIC_ONLY','return_s':None,'missing_real_service_evidence':True})
 table('A_SAVED_EVENT_READBACK.csv',events)
 # Preserve classical baseline references, including the 12 pilot baselines.
 manifests=read(U/'review_outputs/staged_qaoa_validation_20261102/mirror_family/MANIFEST.json');baselines=[];bm={(x['input_sha256'],x['route_indices']):x for x in b}
 for m in manifests:
  f=use(U/'review_outputs/staged_qaoa_validation_20261102/mirror_family/RUNS/MEAN_P2'/m['run_id']/'FIT.json');fit=read(f);route=[0]+fit['initial_route']+[0];x=bm[(m['instance_sha256'],canon(route))]
  baselines.append({'classical_reference_id':'CLASSICAL_INITIAL-'+m['run_id'],'problem_id':m['run_id'],'input_sha256':m['instance_sha256'],'route_indices':canon(route),'candidate_id':x['candidate_id'],'run_id':x['run_id'],'input_status':x['input_status'],'source_path':str(f),'source_sha256':sha(f)})
 table('B_CLASSICAL_BASELINE_LINKS.csv',baselines);ck('classical baseline coverage',len(baselines)==460)
 # Raw seed identity independent readback on predefined representatives; no resampling.
 representative={'R0_001','R1_001','R2_001','R3_001','R3_040','R3_078','R4_001','R4_040','R4_078','R5_001','R5_036','R5_070'};done=set();seed_checks=0
 for x in br:
  if x['family']!='mirror_family' or x['problem_id'] not in representative:continue
  key=(x['config_id'],x['problem_id'])
  if key in done:continue
  done.add(key);p=U/'review_outputs/staged_qaoa_validation_20261102/mirror_family/RUNS'/key[0]/key[1]/'MEASUREMENTS.json';raw=read(p)
  ix={(r['mode'],str(r['rep'])):r for r in raw['records']}
  for xx in (z for z in br if z['config_id']==key[0] and z['problem_id']==key[1]):
   ck('measurement seed stream '+key[0]+'/'+key[1]+'/'+xx['rep'],json.loads(xx['PCG64_seed_state4'])==ix['OPTIMIZED',xx['rep']]['stream']);seed_checks+=1
 # New native outputs -> strict CSV reader -> frozen kernel -> separate scalar.
 model=read(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json');native=read(O/'NATIVE_UNIT_PROCESS_RESULTS.json');ener=[]
 env=read(O/'ENVIRONMENT.json');use(O/'native_unit_validation.py')
 for x in native:
  d=O/'NATIVE_UNIT'/x['case'];rr=[]
  for step in ET.parse(d/'fcd.xml').getroot().findall('timestep'):
   v=step.find('vehicle')
   if v is not None:rr.append({'timestamp_s':step.get('time'),'speed_m_s':v.get('speed')})
  table('NATIVE_UNIT/'+x['case']+'/trajectory.csv',rr);path=d/'trajectory.csv';t,v=read_dc_input(path,expected_sha256=sha(path))
  frozen,_=evaluate(t,v,model,4.5,{'running_mass_kg':1200});scalar=scalar_dc(t,v,1200,4.5,arrival=x['return_s']);error=abs(frozen['net_DC_Wh']-scalar['DC_Wh']);ck('new native strict reader/kernel/scalar '+x['case'],error<=1e-7,{'error_Wh':error})
  inp={'core_input_sha256':x['input_sha256'],'standalone_unit_harness_sha256':sha(O/'native_unit_validation.py'),'environment_sha256':env['fingerprint'],'engine':'STANDALONE_SUMO_SYNTHETIC_UNIT_NOT_FROZEN_FORK','command':x['argv']}
  ener.append({'case':x['case'],'complete_unit_input_sha256':digest(inp),'trajectory_sha256':sha(path),'running_mass_kg':1200,'pressure_bar':4.5,'W1_Wh':scalar['W1_Wh'],'W2_Wh':scalar['W2_Wh'],'W3_Wh':scalar['W3_Wh'],'W4_Wh':scalar['W4_Wh'],'DC_Wh_frozen':frozen['net_DC_Wh'],'DC_Wh_scalar':scalar['DC_Wh'],'difference_Wh':error,'observed_distance_m':frozen['observed_distance_m'],'native_routeLength_m':float(ET.parse(d/'tripinfo.xml').getroot().find('tripinfo').get('routeLength')),'terminal_gap_s':scalar['terminal_gap_s'],'terminal_gap_Wh':None,'status':'PASS_UNIT_CONDITIONAL_MODEL','not_regional_pilot':True})
 table('NATIVE_UNIT_ENERGY_VALIDATION.csv',ener)
 write('B_ENERGY_INPUT_CONTRACT.json',{'motion_mass':'vType defaults pinned by native binary; no material mass injection into speed dynamics','controlled_DC_running_mass_kg':None,'adoption_status':'HOLD_EXPLICIT_B_COMPARISON_MASS_NOT_FIXED','freeze_model_sha256':sha(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'),'pressure_cases':model['Crr_model']['cases'],'future_requirement':'Explicit common route-comparison mass before B scientific DC; do not silently transfer T08 or T09 pack mass','synthetic_unit_mass_kg':1200,'synthetic_unit_mass_is_not_B_adoption':True})
 write('INDEPENDENT_VALIDATION.json',{'checks':len(checks),'failed':[x for x in checks if x['status']=='FAIL'],'seed_stream_records_checked':seed_checks,'native_DC_checks':len(ener),'saved_event_rows':len(events),'regional_pilot_runs':0})
 write('INDEPENDENT_CHECKS.json',checks);save_sources('VALIDATION_SOURCE_FILES.json');print('independent validation',len(checks),'checks','failed',sum(x['status']=='FAIL' for x in checks))
 if any(x['status']=='FAIL' for x in checks):raise RuntimeError('Validation failure')
if __name__=='__main__':main()
