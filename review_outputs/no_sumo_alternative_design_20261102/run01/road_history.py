"""Historical evidence readback only: do not diagnose or repair the networks anew."""
from support import *
def main():
 t=time.monotonic();history=[];records=[]
 roots=sorted((U/'review_outputs').glob('road_network_*'))
 for root in roots:
  # Restrict to review top level and run levels; exclude environment/source trees.
  for d in [root,*sorted(p for p in root.glob('run*') if p.is_dir())]:
   for pattern in ['*.md','*ACCEPTANCE*.json','*SUMMARY*.json','*GENERATION*.json','*REGRESSION*.json','*REPAIR_PLAN*.json','*FAILURE_HISTORY*.json','*INPUTS*.json']:
    for p in sorted(d.glob(pattern)):
     body=use(p).read_text();records.append({'path':str(p),'sha256':SRC[str(p)]['sha256'],'bytes':len(body.encode()),'scope':'SAVED_REPAIR_HISTORY_NOT_RERUN'})
  for p in sorted(root.glob('**/candidates/*.net.xml')):
   if 'reproduc' in p.name:kind='REPRODUCTION_CONTROL'
   else:kind='HISTORICAL_CANDIDATE'
   use(p);history.append({'version':p.stem,'source_review':root.name,'network_path':str(p),'network_sha256':SRC[str(p)]['sha256'],'kind':kind,'adoption':'NOT_ADOPTED_FOR_REGIONAL_DELIVERY','OD_plan_reuse':'HOLD_NEW_MAPPING_WEIGHTS_OBJECTIVES_IF_CHANGED','evidence_directory':str(p.parents[1]),'verification':'Archived static/dynamic reports and manifests; no new simulation'})
 for p,label in [(R/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml','N0')]:
  use(p);history.append({'version':label,'source_review':'formal_saved_network','network_path':str(p),'network_sha256':SRC[str(p)]['sha256'],'kind':'SAVED_AUTHORITY','adoption':'FAIL_REGIONAL_ACCEPTANCE','OD_plan_reuse':'CONDITIONAL_FROZEN_NUMERIC_BENCHMARK_ONLY','evidence_directory':str(P3),'verification':'Prior independently verified geometry evidence, not recalculated'})
 for x in history:
  name=x['version'];root=x['source_review'];purpose='Preserve archived candidate';change='See generation/semantic diff';static='HOLD';dynamic='NOT_EVALUATED';status='HOLD';remaining='No accepted mapping/dynamic/real-world validation'
  if name=='N0':purpose='External lane endpoint geometry extension';change='External shapes and lengths changed, internal connection geometry retained';static='FAIL_563513_GAPS_GT1M';dynamic='NOT_ACCEPTED';status='FAIL'
  elif name.startswith('A_rollback'):purpose='Rollback external lane extension';change='Restore run2 bytes';static='HOLD_LHT_AND_RESIDUAL';status='HOLD'
  elif name.startswith('B_lht'):purpose='Left-hand rebuild retaining TLS';change='Explicit CLI lefthand; old phases retained';static='FAIL_SIMULTANEOUS_GREEN_FOES';status='FAIL'
  elif name.startswith('B2'):purpose='Left-hand geometry and rebuilt TLS';change='Rebuild internal links/TLS from run2';static='FAIL_RESIDUAL8_GAPS_AND_SIGNAL_PAIRS';status='FAIL'
  elif name.startswith('B3'):purpose='Local endpoint gap repair';change='Local treatment of 8 >1m gaps';static='CONDITIONAL_LOCAL_ONLY';status='CONDITIONAL'
  elif name.startswith('B4'):purpose='Local signal repair';change='Separate protected greens / response-aware G-to-g';static='HOLD_18_PAIRS_12_JUNCTIONS';status='HOLD'
  elif name.startswith('B5'):purpose='Global signal conflict screen repair';change='18 pairs;foes/response/intLanes and protected phases;cycles282-658s';static='PASS_WITHIN_STATIC_REGRESSION';status='HOLD';remaining='Cycle/green ratio/waiting capacity and mapping not accepted'
  elif 'grouped' in name:purpose='Conflict grouping to shorten cycles';change='Grouped protected phases; run02 extends conflict constraints';static='PASS_REGRESSION_HOLD_ACCEPTANCE';dynamic='FAIL_2_COLLISIONS_RUN01;RUN02_NOT_RUN';status='FAIL' if '/run01/' in x['network_path'] else 'HOLD'
  elif 'body_clearance' in name:purpose='Clearance guard/request6-7 prototype';change='Runtime body-occupancy guard plus request patch';static='CONDITIONAL';dynamic='SAFETY_ONLY_PASS_WAITING_THROUGHPUT_FAIL';status='FAIL'
  elif 'priority' in name:purpose='B6 priority/signal reacceptance';change='Priority corrections with preceding static geometry preserved';static='PASS_STATIC_SCOPE';dynamic='FAIL_183_COLLISION_RECORDS';status='FAIL'
  x.update(purpose=purpose,actual_change=change,static_result=static,dynamic_result=dynamic,status=status,unresolved=remaining)
 table('ROAD_NETWORK_VERSION_HISTORY.csv',history);table('ROAD_HISTORY_EVIDENCE_FILES.csv',list({x['path']:x for x in records}.values()))
 n=js(P3/'NETWORK_DIAGNOSIS_SUMMARY.json');s=js(P3/'NETWORK_SUPPLEMENT_SUMMARY.json');check('N0 prior gap count',563513,n['N0']['gap_over1m']);check('N1 archived collision rows',183,n['collision_rows']);check('N1 independent body overlap confirmations',183,s['collision_SAT_passed']);check('regional newly accepted count',0,js(P3/'FINAL_RECOVERY_REVIEW.json')['network_accepted'])
 finish('ROAD',t,{'network_files_located':len(history),'unique_network_hashes':len({x['network_sha256'] for x in history}),'historical_evidence_files':len({x['path'] for x in records}),'new_repairs':0,'new_static_diagnostics':0,'new_native_runs':0,'decision':'STOP_ROAD_REPAIR_FOR_MAIN_THESIS_SCOPE; ARCHIVED_FAIL_REMAINS; REOPEN_ONLY_SEPARATE_VALIDATED_REAL_TRAFFIC_QUESTION'})
if __name__=='__main__':main()
