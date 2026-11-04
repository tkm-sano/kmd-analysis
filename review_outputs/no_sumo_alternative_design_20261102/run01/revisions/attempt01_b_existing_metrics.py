"""Audit saved metrics and recovery-selection bias; 18 new route checks only."""
from support import *
import numpy as np,itertools,statistics
def main():
 t=time.monotonic();manifest=js(S/'mirror_family/MANIFEST.json');meta={x['run_id']:x for x in manifest};refs=rows(P1/'B_PLAN_REFERENCES.csv',['family','variant','run_id','rep']);links=rows(P3/'B_PLAN_RECOVERY_LINKS.csv',['family','config_id','problem_id','rep']);by={(x['family'],x['config_id'],x['problem_id'],x['rep']):x for x in links};saved={};protocols={};refrows=[]
 for fam in ['mirror_family','grover_depth','active_adjacent_p3']:
  protocols[fam]=js(S/fam/'PROTOCOL.json')
  for name in ['CONFIGURATION_FROZEN.json','SOURCE_HASHES.json']: 
   if (S/fam/name).exists():use(S/fam/name).read_text()
  for x in rows(S/fam/'ALL_SEEDS.csv'):
   if x['mode']=='OPTIMIZED':saved[(fam,x['variant'],x['run_id'],x['rep'])]=x
  for p in (S/fam/'SOURCE_SNAPSHOT').rglob('*.py'):use(p).read_text()
 for p in [U/'scripts/complete_swap_qaoa_r5.py',U/'scripts/run_parallel_structural_qaoa.py']:use(p).read_text()
 # Certificate metadata is read back, not solved again. Detailed proof replay is a separate scope.
 prior={};reference_meta=[]
 for m in manifest:
  rid=m['run_id'];p=U/'review_outputs/whole_roster_swap_qaoa_through_r5_20261101/RUNS'/rid/'RESULT.json';q=js(p);prior[rid]=q;base=U/'review_outputs/unified_no_windows_r0_r8_20261022';rp=base/'REFERENCE_REFINED'/rid/'result.json'
  if not rp.exists():rp=base/'REFERENCE'/rid/'result.json'
  d=js(rp);dp=U/'review_outputs/unified_no_windows_dp_qaoa_comparison_20261023/DP'/rid/'RESULT.json'
  if m['scale_id']=='R3' and dp.exists():d=js(dp);rp=dp
  val=d.get('exact_optimum_seconds');match=val is not None and q.get('exact_optimum_seconds') is not None and F(val)==F(q['exact_optimum_seconds'])
  reference_meta.append({'problem_id':rid,'scale':m['scale_id'],'parent_id':m['parent_id'],'source_path':str(use(rp)),'source_sha256':SRC[str(use(rp))]['sha256'],'proved_optimal':d.get('proved_optimal'),'proof':d.get('proof',d.get('status')),'exact_optimum_seconds':val,'matches_staged_parent':match,'proof_scope':'SAVED_CERTIFICATE_METADATA_NOT_NEW_SOLVER_PROOF_REPLAY'})
 table('B_REFERENCE_CERTIFICATE_STATUS.csv',reference_meta)
 check('plan count',36800,len(refs));check('link count',36800,len(by));check('input count',460,len(meta));check('missing linked references',0,sum((x['family'],x['variant'],x['run_id'],x['rep']) not in by for x in refs));check('reference scalar agreement',460,sum(x['matches_staged_parent'] for x in reference_meta))
 enriched=[]
 for x in refs:
  key=(x['family'],x['variant'],x['run_id'],x['rep']);y=saved[key];l=by[key];m=meta[x['run_id']];rawcost=F(y['sampled_best_seconds']);exact=F(prior[x['run_id']]['exact_optimum_seconds']);gap=float(100*(rawcost-exact)/exact);check_needed=False
  # This is a descriptive join/aggregation of existing values, not new NPZ route evaluation.
  enriched.append({'problem_id':x['run_id'],'scale':m['scale_id'],'parent_id':m['parent_id'],'group_prefix':m['parent_id'].rsplit('_V',1)[0],'config_id':x['variant'],'rep':x['rep'],'candidate_id':l['candidate_id'],'recovery_class':l['recovery_class'],'recovered_original':l['recovery_class']=='ORIGINAL_RECOVERED','objective_seconds':float(rawcost),'reported_gap_percent':float(y['sampled_gap_global_percent']) if y.get('sampled_gap_global_percent') else None,'gap_from_saved_scalars_percent':gap,'route_sha256':hashlib.sha256(x['route_indices'].encode()).hexdigest()})
 # Bias distributions retain unrecovered rows and physical/problem dependence.
 bias=[]
 for dim in ['scale','parent_id','group_prefix','config_id','rep','problem_id']:
  groups=collections.defaultdict(list)
  for x in enriched:groups[x[dim]].append(x)
  for group,rr in sorted(groups.items()):
   for label,pred in [('ORIGINAL_RECOVERED',lambda x:x['recovered_original']),('NOT_ORIGINAL_RECOVERED',lambda x:not x['recovered_original'])]:
    xx=[x for x in rr if pred(x)];bias.append({'dimension':dim,'group':group,'recovery_stratum':label,'references':len(xx),'all_group_references':len(rr),'recovery_share_percent':sum(x['recovered_original'] for x in rr)/len(rr)*100,'physical_problems':len({x['problem_id'] for x in xx}),'candidates':len({x['candidate_id'] for x in xx}),'mean_saved_objective_s':statistics.mean(x['objective_seconds'] for x in xx) if xx else None,'mean_gap_from_saved_scalars_percent':statistics.mean(x['gap_from_saved_scalars_percent'] for x in xx) if xx else None,'distinct_saved_routes':len({(x['problem_id'],x['route_sha256']) for x in xx})})
 table('B_RECOVERY_BIAS_DESCRIPTIVE.csv',bias)
 # Route-level audit: one predetermined input per scale, one rep per algorithm family.
 samples=[];resources=[]
 for scale in range(6):
  rid=f'R{scale}_001';m=meta[rid]
  with np.load(use(m['instance_path']),allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
  check(rid+' input hash',m['instance_sha256'],sha(resolve(m['instance_path'])))
  q=prior[rid];initial=q['initial_route'];opt=F(q['exact_optimum_seconds'])
  if scale<=2:
   exact=min(sum((F(str(a['travel'][i,j])) for i,j in zip([0,*rt],[*rt,0])),F(0)) for rt in itertools.permutations(range(1,m['n']+1)));check(rid+' independent tiny exhaustive optimum',opt,exact,1e-8)
  for fam,config in [('mirror_family','MEAN_P2'),('grover_depth','GROVER_P2'),('active_adjacent_p3','ACTIVE_ADJACENT_P3_GRID')]:
   x=next(x for x in refs if (x['family'],x['variant'],x['run_id'],x['rep'])==(fam,config,rid,'0'));raw=js(x['source_path']);record=next(y for y in raw['records'] if str(y['rep'])=='0' and y.get('mode','OPTIMIZED')=='OPTIMIZED');rt=record['route_indices'];cost=sum((F(str(a['travel'][i,j])) for i,j in zip(rt,rt[1:])),F(0));dist=sum((F(str(a['distance'][i,j])) for i,j in zip(rt,rt[1:])),F(0));check(rid+config+' valid permutation',list(range(1,m['n']+1)),sorted(rt[1:-1]));check(rid+config+' cost matches raw',cost,F(str(record.get('sampled_best_seconds',record.get('road_seconds')))),1e-7);check(rid+config+' cost matches reference CSV',float(cost),float(x['objective_seconds']),1e-7)
   gap=100*(cost-opt)/opt;y=saved[(fam,config,rid,'0')]
   if y.get('sampled_gap_global_percent'):check(rid+config+' saved gap',float(gap),float(y['sampled_gap_global_percent']),1e-7)
   samples.append({'problem_id':rid,'config_id':config,'rep':0,'input_sha256':m['instance_sha256'],'route_indices':json.dumps(rt),'objective_OD_seconds':str(cost),'sum_OD_distance_m':str(dist),'model_return_s':str(cost+102*m['n']),'reference_optimum_s':str(opt),'gap_percent':float(gap),'source_path':str(use(x['source_path'])),'source_sha256':sha(resolve(x['source_path'])),'interpretation':'FIXED_OD_NO_CUSTOMER_WINDOWS_NOT_NATIVE_DRIVE'})
   source=Path(x['source_path'])
   if fam=='mirror_family':rdata=js(source.parent/'FIT.json');scope='FIT_ONLY_NOT_MEASUREMENT_OR_INITIAL_CLASSICAL'
   else:rdata=raw;scope='SAVED_RESULT_SCOPE_NOT_ASSUMED_END_TO_END'
   resources.append({'problem_id':rid,'family':fam,'config_id':config,'source_path':str(source.parent/'FIT.json') if fam=='mirror_family' else str(source),'wall_seconds':rdata.get('wall_seconds'),'CPU_seconds':rdata.get('CPU_seconds',rdata.get('cpu_seconds')),'peak_RSS_bytes':rdata.get('peak_RSS_bytes'),'scope':scope,'quantum_hardware_seconds':raw.get('quantum_hardware_seconds'),'shots':8192,'logical_layers':3 if fam=='active_adjacent_p3' else 2,'compiled_native_gate_depth':None,'selected_backend_stats':json.dumps(rdata.get('backend_stats',rdata.get('stats',{})))})
 table('B_SMALL_ROUTE_CHECKS.csv',samples);table('B_RESOURCE_FIELD_EXAMPLES.csv',resources)
 nullgap=sum(x['reported_gap_percent'] is None for x in enriched);coverage=sum(x['recovered_original'] for x in enriched);check('original coverage preserved',24333,coverage);check('sample cost checks count',18,len(samples))
 finish('B',t,{'plan_references':len(refs),'candidates':len({x['candidate_id'] for x in enriched}),'physical_inputs':len(meta),'parent_count':len({m['parent_id'] for m in meta.values()}),'group_prefixes':len({m['parent_id'].rsplit('_V',1)[0] for m in meta.values()}),'original_recovery_reference_coverage':coverage,'recovery_classes':dict(collections.Counter(x['recovery_class'] for x in rows(P3/'B_FINAL_RECOVERY_CLASSIFICATION.csv'))),'exact_reference_metadata_matches':sum(x['matches_staged_parent'] for x in reference_meta),'reported_gap_missing':nullgap,'new_route_cost_evaluations':len(samples),'new_tiny_optimum_checks':3,'new_full_cohort_evaluations':0,'bias_scope':'Existing scalar descriptive aggregation only; no outcome inference on recovered subset','regional_accepted_runs':0,'recommended_energy_option':'B-E3_PRIMARY; B-E2_OPTIONAL_NEW_ASSUMPTIONS; B-E1_HOLD'})
if __name__=='__main__':main()
