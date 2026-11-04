"""Audit extra saved resource scopes/classical controls and driving sensitivity."""
from common import *
import numpy as np
def main():
 t=time.monotonic();fits=rows(O/'B_RESOURCES_PER_FIT.csv');long=[];pointer=[];active=[];wanted={'wall_seconds','CPU_seconds','cpu_seconds','peak_RSS_bytes','max_rss_bytes','two_site_gates','work_units','max_core_bytes','max_bond','QR_moves','fit_evaluations','optimizer_iterations','quantum_hardware_seconds'}
 aops={x['PID']:x for x in rows(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv')};ares=[]
 for pid,x in sorted(aops.items()):
  cc=js(x['classical_source']);qq=js(x['quantum_source']);ares.append({'problem_id':pid,'parent_id':x['parent_id'],'input_sha256':cc['instance_sha256'],'classical_search_s':cc['phases']['search_s'],'classical_worker_wall_s':cc.get('worker_wall_s'),'classical_worker_CPU_s':cc.get('worker_CPU_s'),'classical_peak_RSS_KiB':cc.get('worker_peak_RSS_KiB'),'QAOA_simulator_wall_s':qq.get('wall_s'),'QAOA_sampling_wall_s':qq.get('sampling_wall_s'),'QAOA_CPU_s':qq.get('CPU_s'),'QAOA_max_RSS_bytes':qq.get('max_rss_bytes'),'QAOA_final_shots':qq.get('final_shots'),'QAOA_total_shots':qq.get('total_shots'),'QAOA_optimizer_evaluations':qq.get('optimizer_evaluation_count'),'QAOA_final_feasible_count':qq.get('final_feasible_count'),'QAOA_acquired':qq.get('final_feasible_count',0)>0,'classical_source':str(use(x['classical_source'])),'classical_source_sha256':SRC[str(use(x['classical_source']))]['sha256'],'quantum_source':str(use(x['quantum_source'])),'quantum_source_sha256':SRC[str(use(x['quantum_source']))]['sha256'],'condition_id':'ORIGINAL_COMPUTATION_NOT36_POLICIES','status':'OBSERVED_CPU_COMPUTATION_SCOPE_DIFFERENCES_RETAINED','missing_reason':'Q_CPU_NOT_SAVED' if qq.get('CPU_s') is None else '', 'units':'time=s;memory=suffix_bytes_or_KiB;shots=count'})
 table('A_RAW_COMPUTATION_RESOURCES_78.csv',ares)
 def walk(obj,path,base):
  if not isinstance(obj,dict):return
  for k,v in obj.items():
   pp=path+'/'+k
   if k in wanted and isinstance(v,(int,float)) and not isinstance(v,bool):long.append({**base,'json_pointer':pp,'resource_field':k,'value':v,'units':'s' if 'seconds' in k else 'bytes' if 'bytes' in k else 'backend_operations_or_count','scope':'FINAL_VALIDATION' if '/validation/' in pp else 'SELECTED_STATE' if '/selected/' in pp else 'FIT' if base['source_kind']=='FIT' else 'RESULT_ROOT_OR_BACKEND','status':'PASS_SAVED_FIELD_NOT_END_TO_END_BUDGET'})
   if isinstance(v,dict):walk(v,pp,base)
 for x in fits:
  fp=use(x['fit_source_path'],x['fit_source_sha256']);paths=[(fp,'FIT' if fp.name=='FIT.json' else 'RESULT')]
  result=fp.parent/('MEASUREMENTS.json' if x['family']=='mirror_family' else 'RESULT.json')
  if result.is_file() and result!=fp:paths.append((result,'RESULT'))
  for p,kind in paths:
   walk(js(p),'',{'fit_id':x['fit_id'],'problem_id':x['problem_id'],'parent_id':x['parent_id'],'group_id':x['group_id'],'config_id':x['config_id'],'scale':x['scale'],'input_sha256':x['input_sha256'],'source_kind':kind,'source_path':str(use(p)),'source_sha256':SRC[str(use(p))]['sha256']})
  if x['family']=='active_adjacent_p3':
   d=js(fp);active.append({'problem_id':x['problem_id'],'parent_id':x['parent_id'],'group_id':x['group_id'],'scale':x['scale'],'input_sha256':x['input_sha256'],'selected_t':d['selected_t'],'grid_points':json.dumps(d['points']),'source_path':str(fp),'source_sha256':x['fit_source_sha256'],'status':'PASS_SAVED_RESTRICTED_GRID_SELECTION'})
 table('B_ACTIVE_GRID_SELECTION.csv',active)
 table('B_SAVED_RESOURCES_LONG.csv',long)
 group=collections.defaultdict(list)
 for x in long:group[(x['config_id'],x['scale'],x['scope'],x['resource_field'],x['units'])].append(x)
 table('B_RESOURCE_SCOPE_SUMMARY.csv',[{'config_id':k[0],'scale':k[1],'resource_scope':k[2],'resource_field':k[3],'units':k[4],'records':len(rr),'unique_fits':len({x['fit_id'] for x in rr}),'sum_value':math.fsum(float(x['value']) for x in rr),'mean_value':math.fsum(float(x['value']) for x in rr)/len(rr),'max_value':max(float(x['value']) for x in rr),'source_table_sha256':sha(O/'B_SAVED_RESOURCES_LONG.csv'),'status':'SCOPE_SPECIFIC_NO_DUPLICATE_FIT_REP_SUM'} for k,rr in sorted(group.items())])
 # Older classical improvements are auxiliary, not matched to current 8 fit budgets.
 root=U/'review_outputs/cpu_matched_classical_swaps_r0_r5_20261101';cm={x['run_id']:x for x in js(root/'MANIFEST.json')};bm={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')};old=rows(root/'MATCHED_COMPARISON.csv');aux=[]
 for x in old:
  rid=x['run_id'];check('aux classical input identity',bm[rid]['instance_sha256'],cm[rid]['instance_sha256']);aux.append({**x,'problem_id':rid,'input_sha256':bm[rid]['instance_sha256'],'source_path':str(root/'MATCHED_COMPARISON.csv'),'source_sha256':SRC[str(use(root/'MATCHED_COMPARISON.csv'))]['sha256'],'budget_scope':'MATCHED_TO_OLDER_SWAP_EXPERIMENT_NOT_CURRENT_STAGED8','status':'CONDITIONAL_AUXILIARY_CLASSICAL_IMPROVEMENT','missing_reason':'CURRENT_BUDGET_MATCH_NOT_ESTABLISHED','units':'seconds;percent;CPU seconds'})
 table('B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv',aux)
 plan=rows(O/'B_PLAN_REFERENCES_36800.csv');orbit=collections.defaultdict(list)
 for x in plan:
  if x['classical_orbit_delta_s']!='':orbit[(x['scale'],x['config_id'])].append(x)
 table('B_CLASSICAL_ORBIT_COMPARISON.csv',[{'scale':k[0],'config_id':k[1],'references':len(rr),'physical_inputs':len({x['problem_id'] for x in rr}),'mean_sample_minus_exact_orbit_s':math.fsum(float(x['classical_orbit_delta_s']) for x in rr)/len(rr),'mean_orbit_gap_percent':math.fsum(float(x['orbit_gap_percent']) for x in rr)/len(rr),'mean_initial_minus_orbit_s':math.fsum(float(x['classical_initial_s'])-float(x['orbit_optimum_s']) for x in rr)/len(rr),'status':'SAME_MATCHING_SUPPORT_CLASSICAL_DP_EVALUATION_ONLY','units':'s;percent'} for k,rr in sorted(orbit.items())])
 bridge=rows(O/'C_BRIDGE_MASS_DC_FULL.csv');group=collections.defaultdict(list);signs=[]
 for x in bridge:
  group[(x['pair_id'],x['probe_id'],x['rolling_case'],x['reference_running_mass_kg'],x['scale_id'])].append(x);saving=float(x['net_mass_saving_probe_kg']);dc=float(x['recomputed_saving_Wh']);state='CANCELLED' if abs(saving)<1e-10 else 'SAVING' if saving>0 else 'REVERSED';check('C mass to DC sign under saved conditions',True,abs(dc)<1e-7 if state=='CANCELLED' else dc>0 if state=='SAVING' else dc<0);signs.append({'condition_id':x['condition_id'],'problem_id':x['problem_id'],'parent_id':x['parent_id'],'group_id':x['group_id'],'input_sha256':x['input_sha256'],'design_policy':x['design_policy'],'known_boundary_kg':x['known_mass_boundary_kg'],'unknown_difference_kg':x['unknown_mass_difference_probe_kg'],'net_mass_saving_kg':saving,'DC_saving_Wh':dc,'mass_DC_state':state,'status':'CONDITIONAL_SIGN_CONFIRMED_SAVED_TRAJECTORY','missing_reason':'COMPLETE_PACK_MASS_UNKNOWN','units':'kg;Wh'})
 table('C_BOUNDARY_SIGN_VALIDATION.csv',signs);sensitivity=[]
 for k,rr in sorted(group.items()):
  rate=[float(x['individual_saving_percent']) for x in rr];km=[float(x['distance_km']) for x in rr];restart=[float(x['restart_count']) for x in rr];dc=[float(x['recomputed_saving_Wh']) for x in rr]
  def corr(v,w):return float(np.corrcoef(v,w)[0,1]) if np.std(v)>1e-12 and np.std(w)>1e-12 else None
  sensitivity.append({'pair_id':k[0],'probe_id':k[1],'rolling_case':k[2],'reference_running_mass_kg':k[3],'scale':k[4],'trajectory_count':len(rr),'mean_DC_saving_Wh':math.fsum(dc)/len(rr),'mean_individual_percent':math.fsum(rate)/len(rr),'min_individual_percent':min(rate),'max_individual_percent':max(rate),'correlation_DC_saving_distance':corr(dc,km),'correlation_DC_saving_restarts':corr(dc,restart),'status':'DESCRIPTIVE_FIXED_TRAJECTORY_NOT_INDEPENDENT_CAUSAL_REGRESSION','units':'Wh;percent;dimensionless'})
 table('C_DRIVING_CONDITION_SENSITIVITY.csv',sensitivity);table('C_COMPONENT_MASS_BRIDGE.csv',rows(BR/'MASS_COMPONENT_BRIDGE.csv'))
 finish('SUPPLEMENT',t,{'saved_resource_fields':len(long),'auxiliary_classical_rows':len(aux),'bridge_sign_rows':len(signs),'driving_strata':len(sensitivity),'new_parameters':0})
if __name__=='__main__':main()
