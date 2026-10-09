"""Frozen mass-to-DC evaluation on existing canonical observed windows only.
No SUMO execution, routing, parameter fitting, endpoint interpolation or authority writes.
Run using .conda/bin/python. Existing output files are never overwritten.
"""
import csv,json,hashlib,math,sys,platform,collections
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[2];O=R/'01_research_design/methodology';B=R/'01_research_design/scenario_evaluation';T=B/'canonical_delivery_trajectories_20261006';W=B/'controlled_dc_full_execution_20261006'
BOUNDARY='OBSERVED_WINDOW_CONTROLLED_DC'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def js(p):return json.loads(Path(p).read_text())
def read(n):return list(csv.DictReader((O/n).open()))
def put(p,x):
 assert not p.exists(),f'Refuse overwrite: {p}'
 p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def table(p,rows,fields=None):
 assert not p.exists(),f'Refuse overwrite: {p}'
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def total(a):return float(np.sum(a,dtype=np.float64))
def near(a,b):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-7)
def preflight():
 m=js(O/'CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json');tf=js(T/'CANONICAL_TRAJECTORY_FREEZE.json');v=js(O/'FULL_TRAJECTORY_INPUT_VALIDATION.json');s=v['status']
 for k in ['INTENDED_ROUTE_COUNT','CANONICAL_TRAJECTORY_COUNT','COMPLETE_TRAJECTORY_COUNT']:assert s[k]==465
 for k in ['FIXED_ROUTE_SEQUENCE_PRESERVED','ASSIGNMENT_PRESERVED','NATIVE_SPEED_TRAJECTORY','STAGE_INDEPENDENT_TRAJECTORY']:assert s[k]=='YES'
 for k in ['TRAJECTORY_HASH_BINDING','FULL_RUN_ADAPTER_DRY_RUN']:assert s[k]=='PASS'
 assert s['TRAJECTORY_COVERAGE']=='COMPLETE' and tf['status']=='COMPLETE_POPULATION'
 mh=sha(O/'CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json');assert mh==tf['energy_model_sha256'];assert sha(T/'CANONICAL_TRAJECTORY_FREEZE.json')==v['trajectory_freeze_sha256']
 for n,h in v['output_hashes'].items():assert sha(O/n)==h,n
 for p,h in m['input_hashes'].items():assert sha(R/p)==h,p
 for n,k in [('CANONICAL_FULL_DELIVERY_TRAJECTORY_MANIFEST.csv','manifest_sha256'),('FULL_TRAJECTORY_COMPLETENESS_AUDIT.csv','completeness_audit_sha256'),('FULL_STAGE_TRAJECTORY_HASH_BINDING.csv','binding_sha256')]:assert sha(O/n)==tf[k]
 for n,k in [('COMPLETENESS_RULES.json','rules_sha256'),('GENERATION_PLAN.json','generation_plan_sha256')]:assert sha(T/n)==tf[k]
 assert (m['CdA']['value'],m['rho']['value'],m['g']['value'],m['rotational_equivalent_mass']['value'],m['eta_prop'])==(1.175,1.2041,9.80665,61,.90)
 assert m['Crr_model']['formula']=='0.005+(0.01+0.0095*(v_kmh/100)^2)/p_bar'
 assert m['integration_rule']['dt_s']==1 and m['grade_model']=='FLAT_ROAD_CONTROLLED' and m['regen_model']=='NO_REGEN_CONTROLLED' and m['auxiliary_scope']=='OUT_OF_SCOPE' and m['turn_loss_scope']=='EXCLUDED_BY_MODEL_BOUNDARY'
 assert [x['e_pack_Wh_kg'] for x in m['stage_inputs']]==[180,220,250]
 assert [x['running_mass_kg'] for x in m['stage_inputs']]==[1155,1134.79797979798,1123.888888888889]
 assert m['stock_accounting']['initial_Wh']==18000
 manifests=read('CANONICAL_FULL_DELIVERY_TRAJECTORY_MANIFEST.csv');bind={x['route_id']:x for x in read('FULL_STAGE_TRAJECTORY_HASH_BINDING.csv')};adapter=read('CONTROLLED_DC_FULL_RUN_ADAPTER_PLAN.csv');assert len(manifests)==465 and len(adapter)==2790
 assert len({x['group_id'] for x in manifests})==182
 rows=list(csv.DictReader((B/'classical_vrptw_baseline_20261005/RESULTS_MANIFEST.csv').open()));assert {x['instance_id'] for x in rows}=={x['route_id'] for x in manifests}
 assert sha(B/'classical_vrptw_baseline_20261005/RESULTS_MANIFEST.csv')==tf['source_manifest_sha256']
 ap=B/'baseline_capacity_fleet_assignment_20260930/CUSTOMER_VEHICLE_ASSIGNMENT_39956.csv';assert sha(ap)==tf['assignment_sha256'];assignment=collections.defaultdict(set)
 for a in csv.DictReader(ap.open(encoding='utf-8-sig')):assignment[a['vehicle_id']].add(a['customer_id'])
 protected=dict(js(T/'PROTECTED_BEFORE.json'))
 for p,h in protected.items():assert sha(R/p)==h,p
 protected.update({str(p.relative_to(R)):sha(p) for p in O.iterdir() if p.is_file()})
 protected[str(T.relative_to(R) / 'CANONICAL_TRAJECTORY_FREEZE.json')]=sha(T/'CANONICAL_TRAJECTORY_FREEZE.json')
 byid={x['route_id']:x for x in manifests};stages={x['stage_id']:x for x in m['stage_inputs']}
 for r in manifests:
  assert r['classification']=='COMPLETE';rid=r['route_id'];h=sha(R/r['trajectory_path']);assert h==r['trajectory_sha256']==tf['trajectory_hashes'][rid]
  assert all(bind[rid][k+'_trajectory_sha256']==h for k in stages) and bind[rid]['status']=='PASS'
  assert sha(r['source_artifact'])==r['source_sha256'];orig=js(r['source_artifact']);assert set(orig['route_sequence'][1:-1])==assignment[rid] and len(orig['route_sequence'][1:-1])==len(assignment[rid])
  protected[r['trajectory_path']]=h
 keys=set()
 for a in adapter:
  assert a['trajectory_hash']==byid[a['route_id']]['trajectory_sha256'] and a['model_freeze_hash']==mh and a['trajectory_path']==byid[a['route_id']]['trajectory_path']
  assert float(a['running_mass'])==stages[a['stage']]['running_mass_kg'] and a['rolling_case'] in m['Crr_model']['cases']
  key=(a['route_id'],a['stage'],a['rolling_case']);assert key not in keys;keys.add(key)
 assert len(keys)==2790
 put(W/'PROTECTED_BEFORE.json',protected)
 put(W/'EXECUTION_PLAN.json',dict(status='PREREGISTERED_BEFORE_ENERGY_CALCULATION',boundary=BOUNDARY,model_sha256=mh,trajectory_freeze_sha256=sha(T/'CANONICAL_TRAJECTORY_FREEZE.json'),expected_routes=465,expected_cases=2790,execution_authorization='Current user explicitly authorizes full controlled DC; historical model-freeze execution flag referred only to the earlier freeze task',model_changed=False,parameters_selected_from_results=False,turn_auxiliary='null with scope tags',terminal_interval='excluded; no assumed zero energy',decomposition='Reduction E0-Ek = sum I0*(component0-componentk)/eta + sum (I0-Ik)*wheel_k/eta. Mechanical deltas reported as k-0. I denotes positive total wheel branch. Baseline-mask attribution convention, not unique causal allocation.',negative_magnitude_fields='*_negative_Wh are nonnegative magnitudes; *_signed_Wh retain signs',float_tolerance=dict(relative=1e-11,absolute_Wh=1e-7),ratio_when_B0_zero=None,stock_negative='Record fail without clipping',script_sha256=sha(Path(__file__)),python=sys.version,numpy=np.__version__,pandas=pd.__version__))
 put(W/'PREFLIGHT_GATE.json',dict(result='PASS',all_465_trajectory_hashes_checked=True,adapter_2790_checked=True,assignment_verified=True,source_route_hashes_verified=True,preexisting_freezes_unchanged=True))
 return m,manifests,protected

def evaluate(t,v,m,pressure,stage):
 dt=np.diff(t);assert np.all(dt==1) and np.isfinite(v).all() and np.all(v>=0)
 cur=v[1:];dv2=cur*cur-v[:-1]*v[:-1];ds=cur*dt;mass=stage['running_mass_kg'];eta=m['eta_prop']
 crr=.005+(.01+.0095*(3.6*cur/100)**2)/pressure
 roll=mass*m['g']['value']*crr*ds
 trans=.5*mass*dv2;rot=.5*m['rotational_equivalent_mass']['value']*dv2
 aero=.5*m['rho']['value']*m['CdA']['value']*cur*cur*ds
 wheel=(roll+trans+rot+aero)/3600
 pos=np.maximum(wheel,0);neg=np.maximum(-wheel,0);dc=pos/eta;stock=18000-np.cumsum(dc)
 assert np.isfinite(wheel).all() and np.isfinite(stock).all()
 out=dict(observed_interval_count=len(dt),observed_distance_m=total(ds),rolling_Wh=total(roll)/3600,translational_signed_Wh=total(trans)/3600,translational_positive_Wh=total(np.maximum(trans,0))/3600,translational_negative_Wh=total(np.maximum(-trans,0))/3600,rotational_signed_Wh=total(rot)/3600,aero_Wh=total(aero)/3600,grade_Wh=0.0,turn_Wh=None,turn_scope='EXCLUDED_BY_MODEL_BOUNDARY',auxiliary_Wh=None,auxiliary_scope='OUT_OF_SCOPE',wheel_positive_Wh=total(pos),wheel_negative_Wh=total(neg),traction_DC_Wh=total(dc),accepted_regen_Wh=0.0,net_DC_Wh=total(dc),Wh_per_observed_km=total(dc)/(total(ds)/1000) if total(ds)>0 else None,initial_stock_Wh=18000,minimum_stock_Wh=min(18000,float(np.min(stock))),terminal_stock_Wh=float(stock[-1]),cumulative_DC_Wh=float(np.cumsum(dc)[-1]),stock_integrity='STOCK_INTEGRITY_FAIL' if np.any(stock<0) else 'PASS',boundary=BOUNDARY,terminal_gap_energy_Wh=None,terminal_gap_status='EXCLUDED_UNKNOWN_NOT_ZERO')
 assert near(out['wheel_positive_Wh']-out['wheel_negative_Wh'],sum(out[k] for k in ['rolling_Wh','translational_signed_Wh','rotational_signed_Wh','aero_Wh','grade_Wh']))
 assert near(out['translational_signed_Wh'],.5*mass*(v[-1]**2-v[0]**2)/3600)
 assert near(out['rotational_signed_Wh'],.5*61*(v[-1]**2-v[0]**2)/3600)
 assert near(out['wheel_positive_Wh']/eta,out['net_DC_Wh']) and near(18000-out['terminal_stock_Wh'],out['net_DC_Wh'])
 return out,dict(roll=roll/3600,translational=trans/3600,rotational=rot/3600,aero=aero/3600,wheel=wheel,dc=dc)

def scalar_check(t,v,m,p,stage,vector):
 # Independent scalar loop / math.fsum and sequential stock, one full route six cases.
 work=[];stock=18000.0
 for i in range(1,len(t)):
  ds=float(v[i])*(float(t[i])-float(t[i-1]));dv=float(v[i])**2-float(v[i-1])**2
  w=math.fsum([stage['running_mass_kg']*m['g']['value']*(.005+(.01+.0095*(3.6*float(v[i])/100)**2)/p)*ds,.5*stage['running_mass_kg']*dv,.5*61*dv,.5*1.2041*1.175*float(v[i])**2*ds])/3600
  e=max(w,0)/.90;stock-=e;work.append(e)
 assert near(math.fsum(work),vector['net_DC_Wh']) and near(stock,vector['terminal_stock_Wh'])

def main():
 m,manifest,protected=preflight();route_rows=[];diff=[];decomp=[];violations=[];switches=[]
 for idx,r in enumerate(manifest):
  # Same in-memory trajectory reused for every stage and rolling case.
  df=pd.read_csv(R/r['trajectory_path'],usecols=['timestamp_s','speed_m_s']);t=df.timestamp_s.to_numpy();v=df.speed_m_s.to_numpy();assert len(t)==int(r['sample_count']) and len(t)-1==int(r['integration_interval_count'])
  for case,c in m['Crr_model']['cases'].items():
   group=[];arrays=[]
   for stage in m['stage_inputs']:
    out,arr=evaluate(t,v,m,c['p_bar'],stage)
    if idx==0:scalar_check(t,v,m,c['p_bar'],stage,out)
    out=dict(group_id=r['group_id'],route_id=r['route_id'],vehicle_id=r['vehicle_id'],stage=stage['stage_id'],e_pack_Wh_kg=stage['e_pack_Wh_kg'],vehicle_mass_kg=stage['vehicle_mass_kg'],running_mass_kg=stage['running_mass_kg'],rolling_case=case,p_bar=c['p_bar'],trajectory_hash=r['trajectory_sha256'],**out)
    group.append(out);arrays.append(arr);route_rows.append(out)
   b=group[0];a=arrays[0]
   assert all(x['aero_Wh']==b['aero_Wh'] and x['rotational_signed_Wh']==b['rotational_signed_Wh'] for x in group)
   if not b['net_DC_Wh']+1e-7>=group[1]['net_DC_Wh']>=group[2]['net_DC_Wh']-1e-7:violations.append(dict(route_id=r['route_id'],rolling_case=case,energies=[x['net_DC_Wh'] for x in group]))
   for out,z in zip(group[1:],arrays[1:]):
    saved=b['net_DC_Wh']-out['net_DC_Wh'];ratio=saved/b['net_DC_Wh'] if b['net_DC_Wh'] else None
    diff.append(dict(scope='ROUTE',group_id=r['group_id'],route_id=r['route_id'],rolling_case=case,comparison='B0_TO_'+out['stage'],B0_DC_Wh=b['net_DC_Wh'],Bk_DC_Wh=out['net_DC_Wh'],Delta_DC_Bk_minus_B0_Wh=-saved,absolute_reduction_Wh=saved,reduction_fraction=ratio,reduction_pct=100*ratio if ratio is not None else None,boundary=BOUNDARY,terminal_gap_status='EXCLUDED_UNKNOWN_NOT_ZERO'))
    i0=a['wheel']>0;ik=z['wheel']>0;corr=total((i0.astype(int)-ik.astype(int))*z['wheel'])/m['eta_prop']
    d=dict(scope='ROUTE',group_id=r['group_id'],route_id=r['route_id'],rolling_case=case,comparison='B0_TO_'+out['stage'])
    for comp in ['roll','translational','rotational','aero']:
     d['Delta_'+comp+'_Bk_minus_B0_signed_Wh']=total(z[comp]-a[comp]);d[comp+'_baseline_positive_mask_DC_saving_Wh']=total((a[comp]-z[comp])[i0])/m['eta_prop']
    d.update(Delta_grade_Bk_minus_B0_signed_Wh=0,grade_baseline_positive_mask_DC_saving_Wh=0,directional_branch_correction_Wh=corr,branch_switch_interval_count=int(np.count_nonzero(i0!=ik)),B0_positive_Bk_nonpositive_count=int(np.count_nonzero(i0 & ~ik)),B0_nonpositive_Bk_positive_count=int(np.count_nonzero(~i0 & ik)),actual_DC_reduction_Wh=saved,boundary=BOUNDARY,attribution='BASELINE_POSITIVE_WHEEL_MASK_PLUS_EXACT_BRANCH_CORRECTION',terminal_gap_status='EXCLUDED_UNKNOWN_NOT_ZERO')
    reconstructed=sum(d[c+'_baseline_positive_mask_DC_saving_Wh'] for c in ['roll','translational','rotational','aero','grade'])+corr;d['decomposition_residual_Wh']=saved-reconstructed;assert near(saved,reconstructed);decomp.append(d)
    for ii in np.flatnonzero(i0!=ik):switches.append(dict(route_id=r['route_id'],rolling_case=case,comparison=d['comparison'],interval_index=int(ii+1),start_s=float(t[ii]),end_s=float(t[ii+1]),B0_wheel_Wh=float(a['wheel'][ii]),Bk_wheel_Wh=float(z['wheel'][ii]),B0_DC_Wh=float(a['dc'][ii]),Bk_DC_Wh=float(z['dc'][ii])))
  if idx%50==0:print('ENERGY_ROUTES',idx+1,flush=True)
 assert len(route_rows)==2790 and len(diff)==1860
 aggregate=[];sumkeys=['observed_interval_count','observed_distance_m','rolling_Wh','translational_signed_Wh','translational_positive_Wh','translational_negative_Wh','rotational_signed_Wh','aero_Wh','grade_Wh','wheel_positive_Wh','wheel_negative_Wh','traction_DC_Wh','accepted_regen_Wh','net_DC_Wh']
 for case in m['Crr_model']['cases']:
  for stage in m['stage_inputs']:
   rs=[x for x in route_rows if x['rolling_case']==case and x['stage']==stage['stage_id']];assert len(rs)==465
   a=dict(rolling_case=case,stage=stage['stage_id'],route_count=465,**{k:math.fsum(x[k] for x in rs) for k in sumkeys})
   a.update(TOTAL_OBSERVED_WINDOW_DELIVERY_DC_ENERGY_Wh=a['net_DC_Wh'],TOTAL_OBSERVED_WINDOW_DELIVERY_DC_ENERGY_kWh=a['net_DC_Wh']/1000,Wh_per_observed_km=a['net_DC_Wh']/(a['observed_distance_m']/1000),minimum_route_stock_Wh=min(x['minimum_stock_Wh'] for x in rs),stock_failure_count=sum(x['stock_integrity']!='PASS' for x in rs),turn_Wh=None,turn_scope='EXCLUDED_BY_MODEL_BOUNDARY',auxiliary_Wh=None,auxiliary_scope='OUT_OF_SCOPE',boundary=BOUNDARY,terminal_gap_status='EXCLUDED_UNKNOWN_NOT_ZERO',event_inclusive_full_trip_energy=False);aggregate.append(a)
 for case in m['Crr_model']['cases']:
  ag=[x for x in aggregate if x['rolling_case']==case];base=ag[0]['net_DC_Wh'];assert base>=ag[1]['net_DC_Wh']>=ag[2]['net_DC_Wh']
  for a in ag[1:]:
   saved=base-a['net_DC_Wh'];diff.append(dict(scope='AGGREGATE',group_id=None,route_id=None,rolling_case=case,comparison='B0_TO_'+a['stage'],B0_DC_Wh=base,Bk_DC_Wh=a['net_DC_Wh'],Delta_DC_Bk_minus_B0_Wh=-saved,absolute_reduction_Wh=saved,reduction_fraction=saved/base,reduction_pct=100*saved/base,boundary=BOUNDARY,terminal_gap_status='EXCLUDED_UNKNOWN_NOT_ZERO'))
   rs=[d for d in decomp if d['scope']=='ROUTE' and d['rolling_case']==case and d['comparison']=='B0_TO_'+a['stage']];row=rs[0].copy();row.update(scope='AGGREGATE',group_id=None,route_id=None)
   for k in row:
    if isinstance(rs[0][k],(int,float)):row[k]=math.fsum(d[k] for d in rs)
   assert near(row['actual_DC_reduction_Wh'],saved);decomp.append(row)
 distribution=[]
 for case in m['Crr_model']['cases']:
  for stage in ['B1','B2']:
   vals=[x['reduction_pct'] for x in diff if x['scope']=='ROUTE' and x['rolling_case']==case and x['comparison']=='B0_TO_'+stage and x['reduction_pct'] is not None]
   distribution.append(dict(rolling_case=case,comparison='B0_TO_'+stage,qualified_ratio_count=len(vals),zero_B0_count=465-len(vals),unweighted_route_percentiles_pct=dict(zip(['min','p05','p25','median','p75','p95','max'],map(float,np.quantile(vals,[0,.05,.25,.5,.75,.95,1]))))))
 table(O/'FULL_B0_B1_B2_CONTROLLED_DC_ROUTE_RESULTS.csv',route_rows)
 table(O/'FULL_B0_B1_B2_CONTROLLED_DC_AGGREGATE.csv',aggregate)
 table(O/'FULL_B0_B1_B2_STAGE_DIFFERENCES.csv',diff)
 table(O/'FULL_B0_B1_B2_COMPONENT_DECOMPOSITION.csv',decomp)
 table(W/'DIRECTIONAL_BRANCH_SWITCH_INTERVALS.csv',switches,['route_id','rolling_case','comparison','interval_index','start_s','end_s','B0_wheel_Wh','Bk_wheel_Wh','B0_DC_Wh','Bk_DC_Wh'])
 put(W/'ROUTE_REDUCTION_DISTRIBUTION.json',distribution);put(W/'ORDERING_VIOLATIONS.json',violations)
 changed=[p for p,h in protected.items() if sha(R/p)!=h];assert not changed
 stock_fail=sum(x['stock_integrity']!='PASS' for x in route_rows)
 status=dict(ROUTE_COUNT=465,EXPECTED_CASE_COUNT=2790,ENERGY_CASE_COUNT=len(route_rows),ALL_ROUTE_ENERGY_CALCULATED='YES',STAGE_CONTROL_EQUALITY='PASS',ENERGY_ACCOUNTING='PASS',STOCK_ACCOUNTING='FAIL' if stock_fail else 'PASS',ENERGY_ORDERING='PARTIAL' if violations else 'PASS',AGGREGATE_STAGE_ENERGY='CALCULATED',ENERGY_REDUCTION='CALCULATED',PHYSICAL_COMPONENT_DECOMPOSITION='CALCULATED',EVENT_INCLUSIVE_FULL_TRIP_ENERGY='NO',FINAL_RESULT_BOUNDARY=BOUNDARY)
 put(W/'EXECUTION_VALIDATION_BASE.json',dict(status=status,protected_count=len(protected),protected_files_changed=changed,route_ordering_violation_count=len(violations),stock_failure_count=stock_fail,branch_switch_interval_rows=len(switches),all_interval_finite_and_sampling_checks=True,scalar_reference_check='PASS_FIRST_ROUTE_ALL_SIX_CASES',kinetic_telescoping_checks='PASS_ALL_CASES',decomposition_conservation='PASS_ALL_ROUTE_AND_AGGREGATE_COMPARISONS',regeneration='ZERO_BY_CONTROL_NOT_MEASURED',turn_and_auxiliary='NULL_WITH_SCOPE_FLAGS',route_ratio_distribution=distribution,energy_model_unchanged=True,trajectory_generation_executed=False,route_optimization_executed=False,authority_modified=False,terminal_gap='Every route last-sample-to-arrival1s excluded; energy unknown, not zero',next_stage='ROBUSTNESS_ANALYSIS_OF_CONTROLLED_DC_RESULT_THEN_INTEGRATE_BATTERY_AXIS_WITH_ROUTE_COMPUTATION_SCALE_EXPERIMENT_THEN_ANALYZE_ROUTE_SCALE_X_BATTERY_LEVEL_INTERACTION' if not stock_fail and not violations else 'RESOLVE_ACCOUNTING_OR_ORDERING_FAILURES'))
 print(json.dumps(dict(status=status,aggregate=aggregate,aggregate_differences=[x for x in diff if x['scope']=='AGGREGATE'],aggregate_components=[x for x in decomp if x['scope']=='AGGREGATE'],distribution=distribution),indent=2),flush=True)
if __name__=='__main__':main()
