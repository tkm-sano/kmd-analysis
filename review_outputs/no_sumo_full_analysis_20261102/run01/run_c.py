"""Re-evaluate unchanged frozen DC on saved windows; retain all original rows."""
from common import *
import numpy as np,pandas as pd
sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate
def main():
 batch='--batch' in sys.argv;replay='--replay' in sys.argv;label='C_BATCH' if batch else 'C_REPLAY' if replay else 'C_FULL';t0=time.monotonic()
 if not batch:require_batch('C')
 freeze=js(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json');freezehash=sha(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json');use(R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py');scenarios=js(T8/'SCENARIOS.json')['scenarios'];mass={}
 for s in scenarios:
  p={k:v['value'] for k,v in s['parameters'].items()};Q=p['gross_energy']/p['voltage'];mass[s['scenario_id']]=Q/p['q_ref']/p['utilization']/p['f_positive']+Q*p['np_ratio']/p['q_negative']/p['f_negative']+s['cell_topology']['n_cells']*p['cell_other_mass']+p['pack_other_mass']+p['additional_mass']
 mf=[R/'01_research_design/methodology/MATCHED_CLASSICAL_TRAJECTORY_MANIFEST.csv',R/'01_research_design/scenario_evaluation/matched_quantum_r0_common_protocol_trajectories_20261008/R0_COMMON_PROTOCOL_METHOD_TRAJECTORY_MANIFEST.csv',R/'01_research_design/scenario_evaluation/matched_quantum_r1_trajectories_20261007/R1_METHOD_TRAJECTORY_MANIFEST.csv'];man=[]
 for p in mf:man.extend(rows(p))
 byhash={x['trajectory_sha256']:x for x in man};physical={x['physical_instance_id']:x for x in js(R/'01_research_design/scenario_evaluation/matched_classical_route_scale_20261007/MANIFESTS/PHYSICAL_INSTANCES.json')};energy=rows(T8/'MATERIAL_ENERGY.csv');response=rows(BR/'DC_MASS_RESPONSE.csv');bounds=rows(BR/'T09_MASS_BOUNDARIES.csv');pack=rows(T9/'PACK_20KWH_SENSITIVITY.csv');erow={id(x):i for i,x in enumerate(energy)};brow={id(x):i for i,x in enumerate(response)}
 if batch:
  classical=[x for x in man if x.get('classification')=='COMPLETE' and x.get('scale_id') in ['R0','R3','R5']];chosen={next(x['trajectory_sha256'] for x in classical if x['scale_id']==s) for s in ['R0','R3','R5']};other=next(x['trajectory_sha256'] for x in energy if x['dataset']=='R1' and x['trajectory_sha256'] not in chosen);chosen.add(other);energy=[x for x in energy if x['trajectory_sha256'] in chosen];response=[x for x in response if x['trajectory_sha256'] in chosen];selected={30,31,102,103}|{i for i,x in enumerate(pack) if x['overlap_condition']=='FAIL_IF_SAME_STACK_FOOTPRINT'}
 else:selected=set(range(len(pack)))
 requests=collections.defaultdict(list)
 for x in energy:requests[x['trajectory_sha256']].append(('T08',erow[id(x)],x))
 for x in response:requests[x['trajectory_sha256']].append(('BRIDGE',brow[id(x)],x))
 tout=[];bout=[];pairs=[];traceinfo=[];recomputed=0
 for number,h in enumerate(sorted(requests),1):
  manifest=byhash[h];p=use(R/manifest['trajectory_path'],h);df=pd.read_csv(p,usecols=['timestamp_s','speed_m_s']);t=df.timestamp_s.to_numpy();v=df.speed_m_s.to_numpy();check('C 1s samples',True,bool(np.all(np.diff(t)==1) and np.isfinite(v).all() and np.all(v>=0)));check('C sample count',int(manifest['sample_count']),len(t));pid=manifest['physical_instance_id'];ph=physical[pid];cache={}
  def dc(m,pressure):
   nonlocal recomputed
   key=(float(m),float(pressure))
   if key not in cache:
    val,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':m});cache[key]=val;recomputed+=1
   return cache[key]
  for kind,ix,x in requests[h]:
   meta={'series_id':'C_'+kind,'condition_id':f'{kind}-{ix:06d}','problem_id':x['physical_instance_id'],'parent_id':ph['parent_id'],'group_id':ph['group_id'],'input_sha256':h,'trajectory_path':str(p),'freeze_sha256':freezehash,'status':'CONDITIONAL_FIXED_TRAJECTORY','missing_reason':'REGIONAL_NETWORK_UNACCEPTED;TERMINAL_GAP_ENERGY_UNKNOWN','units':'mass=kg;energy=Wh;time=s;distance=m'}
   if kind=='T08':
    check('T08 pack mass',float(x['pack_mass_kg']),mass[x['scenario_id']],1e-8);r=dc(float(x['running_mass_kg']),4.5 if x['rolling_case']=='CRR_LOWER_BOUND' else 2.6);check('T08 frozen DC readback',float(x['net_DC_Wh']),r['net_DC_Wh'],1e-7);check('T08 observed distance',float(x['observed_distance_m']),r['observed_distance_m'],1e-6);tout.append({**x,**meta,'recomputed_DC_Wh':r['net_DC_Wh'],'DC_recompute_error_Wh':r['net_DC_Wh']-float(x['net_DC_Wh']),'source_path':str(T8/'MATERIAL_ENERGY.csv'),'source_sha256':SRC[str(use(T8/'MATERIAL_ENERGY.csv'))]['sha256'],'source_row':ix+2,'DC_status':r['stock_integrity']})
   else:
    pbar=float(x['pressure_bar']);base=dc(float(x['reference_running_mass_kg']),pbar);alt=dc(float(x['S_running_mass_probe_kg']),pbar);saving=base['net_DC_Wh']-alt['net_DC_Wh'];check('bridge baseline DC',float(x['baseline_DC_Wh']),base['net_DC_Wh'],1e-7);check('bridge S DC',float(x['S_DC_Wh']),alt['net_DC_Wh'],1e-7);check('bridge saving',float(x['DC_saving_Wh']),saving,1e-7);net=float(x['known_mass_boundary_kg'])-float(x['unknown_mass_difference_probe_kg']);check('bridge mass identity',float(x['net_mass_saving_probe_kg']),net,1e-8);bout.append({**x,**meta,'recomputed_baseline_DC_Wh':base['net_DC_Wh'],'recomputed_S_DC_Wh':alt['net_DC_Wh'],'recomputed_saving_Wh':saving,'source_path':str(BR/'DC_MASS_RESPONSE.csv'),'source_sha256':SRC[str(use(BR/'DC_MASS_RESPONSE.csv'))]['sha256'],'source_row':ix+2})
  traceinfo.append({'trajectory_sha256':h,'problem_id':pid,'parent_id':ph['parent_id'],'group_id':ph['group_id'],'scale':manifest['scale_id'],'source_path':str(p),'source_sha256':h,'sample_count':len(t),'first_sample_s':t[0],'last_sample_s':t[-1],'terminal_gap_s':manifest.get('terminal_gap_s'),'energy_evaluations':len(cache),'native_arrival_s':manifest.get('native_arrival_s'),'status':'PASS_SAVED_WINDOW_CONDITIONAL_REGIONAL_VALIDITY'})
  if number%50==0:print('C trajectories',number,'/',len(requests),'energy cases',recomputed,flush=True)
 t9out=[]
 for i,x in enumerate(pack):
  if i not in selected:continue
  b=bounds[i];parts=['positive_coating_kg','negative_coating_kg','Al_mass_kg','Cu_mass_kg','separator_dry_mass_kg','liquid_mass_kg'];known=math.fsum(float(x[k]) for k in parts);check('T09 known sum',float(x['known_cell_components_sum_kg']),known,1e-8);check('T09 full mass unknown','',x['complete_pack_mass_kg']);t9out.append({**x,'series_id':'C_T09','condition_id':b['scenario_id'],'problem_id':b['scenario_id'],'parent_id':'NOT_APPLICABLE_MATERIAL_DESIGN','group_id':'NOT_APPLICABLE_MATERIAL_DESIGN','input_sha256':sha(use(T9/'PACK_20KWH_SENSITIVITY.csv')),'known_sum_recalculated_kg':known,'unknown_mass_boundary_kg':b['unknown_mass_boundary'],'known_LP_minus_S_mass_kg':b['known_LP_minus_S_mass'],'status':'FAIL_FULL_OPPOSING_FOOTPRINT' if x['overlap_condition']=='FAIL_IF_SAME_STACK_FOOTPRINT' else 'HOLD_COMPLETE_PACK_MASS','missing_reason':x['missing_reason'],'units':'kg; design input columns retain original suffix units','source_row':i+2})
 prefix='batch/' if batch else 'replay/' if replay else ''
 for name,x in [('C_T08_ENERGY_FULL.csv',tout),('C_BRIDGE_MASS_DC_FULL.csv',bout),('C_T09_COMPONENTS_183.csv',t9out),('C_TRAJECTORY_READBACK.csv',traceinfo)]:table(prefix+name,x)
 finish(label,t0,{'T08_rows':len(tout),'T09_rows':len(t9out),'bridge_rows':len(bout),'unique_saved_trajectories':len(traceinfo),'DC_recomputations':recomputed,'T09_pack_HOLD':sum(not x['complete_pack_mass_kg'] for x in t9out),'T09_footprint_FAIL':sum(x['overlap_condition']=='FAIL_IF_SAME_STACK_FOOTPRINT' for x in t9out),'new_SUMO_runs':0,'status':'PASS_ARITHMETIC_CONDITIONAL_MODEL_AND_HOLD_FAIL_RETAINED'})
if __name__=='__main__':main()
