"""Independent status/coverage review and raw native-distance evidence for known controls."""
from evidence import *
import collections,gzip,xml.etree.ElementTree as ET,numpy as np
def native(directory,wanted,visited=None):
 visited=set() if visited is None else visited
 if str(directory) in visited:return {}
 visited.add(str(directory));out={}
 try:
  pro=read(directory/'PROVENANCE.json');out.update(native(Path(pro['original_execution']),wanted,visited))
 except FileNotFoundError:pass
 for name in ['tripinfo.xml.gz','fallback_tripinfo.xml.gz','tripinfo.xml']:
  try:p=use(directory/name)
  except FileNotFoundError:continue
  opener=gzip.open if p.suffix=='.gz' else open
  with opener(p,'rb') as h:
   for event,e in ET.iterparse(h,events=['end']):
    if e.tag=='tripinfo':
     if e.get('id') in wanted:out[e.get('id')]=(dict(e.attrib),str(p),SOURCES[str(p)]['sha256'])
     e.clear()
 try:
  p=use(directory/'PAIR_CORRECTIONS.json')
  for x in read(p):
   key='R'+str(x['row_index']);raw=x.get('native_execution',{}).get('tripinfo')
   if key in wanted and raw:out[key]=(raw,str(p),SOURCES[str(p)]['sha256'])
 except FileNotFoundError:pass
 return out
def main():
 start=time.monotonic();status=rows(O/'B_ROUTE_RECOVERY_STATUS.csv');old={x['candidate_id']:x for x in rows(P2/'B_COMPLETE_RUNS.csv')};known=rows(O/'KNOWN37_IDENTITY_COMPARISON.csv');controls={x['candidate_id'] for x in known};ms=read(U/'review_outputs/staged_qaoa_validation_20261102/mirror_family/MANIFEST.json');meta={x['run_id']:x for x in ms};cp=read(B/SC/'sumo_od_final_validation_20261005/CHECKPOINT_ROWS.json');needed=set()
 for cid in controls:
  x=old[cid]
  with np.load(use(meta[x['problem_id']]['instance_path']),allow_pickle=False) as z:
   rt=json.loads(x['route_indices'])
   for i,j in zip(rt,rt[1:]):needed.add((int(z['partition'][i,j]),str(z['nodes'][i]),str(z['nodes'][j])))
 found={}
 with gzip.open(use(O/'RECOVERED_OD_LEGS.jsonl.gz'),'rt') as h:
  for line in h:
   x=json.loads(line);k=tuple(x['key'])
   if k in needed:found[k]=x
 bypartition=collections.defaultdict(list)
 for k,x in found.items():bypartition[k[0]].append((k,x))
 checks=[]
 for pi,items in bypartition.items():
  directory=Path(cp[pi]['output_path']).parents[2]/'execution'/cp[pi]['partition_id'];ids={'R'+str(x['row_index']) for k,x in items};raw=native(directory,ids)
  for k,x in items:
   witness=raw.get('R'+str(x['row_index']));value=float(witness[0]['routeLength']) if witness else None
   checks.append({'partition_index':pi,'row_index':x['row_index'],'from_node':k[1],'to_node':k[2],'OD_distance_m':x['OD_distance_m'],'raw_tripinfo_routeLength_m':value,'difference_m':value-float(x['OD_distance_m']) if value is not None else None,'status':'PASS' if value==float(x['OD_distance_m']) else 'HOLD_RAW_NATIVE_NOT_LOCATED' if value is None else 'FAIL','source_path':witness[1] if witness else '', 'source_sha256':witness[2] if witness else ''})
 table('KNOWN37_RAW_NATIVE_DISTANCE_CHECKS.csv',checks)
 final=[]
 for x in status:
  y=dict(x);cid=x['candidate_id']
  if x['complete_input_id']:y['recovery_class']='ORIGINAL_RECOVERED';y['available_physical_input_id']=x['complete_input_id'];y['identity_note']='Original OD leg bytes recovered; whole B native run is newly assembled, never an existing executed result'
  elif old[cid]['run_id']:y['recovery_class']='ALTERNATIVE_RECONSTRUCTED';y['available_physical_input_id']=old[cid]['run_id'];y['identity_note']='SAVED_FIXED_LEG_CACHE_FROM_PRIOR_STAGE; no new search; exact original OD edge sequence unproven'
  else:y['recovery_class']=x['recovery_status'];y['available_physical_input_id']='';y['identity_note']='Some original OD edge sequences unretained; do not issue a full run ID'
  final.append(y)
 table('B_FINAL_RECOVERY_CLASSIFICATION.csv',final);fm={x['candidate_id']:x for x in final};refs=rows(P2/'B_PLAN_RUN_LINKS.csv');counts=collections.Counter(x['recovery_class'] for x in final);cover=[]
 for mode in ['scale','config_id','rep','problem_id']:
  groups=collections.defaultdict(list)
  for x in refs:groups[meta[x['problem_id']]['scale_id'] if mode=='scale' else x[mode]].append(x)
  for group,rr in sorted(groups.items()):
   orig=sum(fm[x['candidate_id']]['recovery_class']=='ORIGINAL_RECOVERED' for x in rr);available=sum(bool(fm[x['candidate_id']]['available_physical_input_id']) for x in rr);cover.append({'dimension':mode,'group':group,'references':len(rr),'original_OD_identity_covered':orig,'original_coverage_percent':orig/len(rr)*100,'physical_input_available_including_identity_HOLD':available,'network_accepted':0})
 table('B_FINAL_COVERAGE.csv',cover)
 pilot={x['problem_id'] for x in rows(P2/'B_PILOT_CANDIDATES.csv')};table('PILOT_INPUT_RECOVERY_COVERAGE.csv',[x for x in cover if x['dimension']=='problem_id' and x['group'] in pilot])
 orig=sum(int(x['references']) for x in final if x['recovery_class']=='ORIGINAL_RECOVERED');available=sum(int(x['references']) for x in final if x['available_physical_input_id']);summary={'classes':dict(counts),'strict_original_candidates':counts['ORIGINAL_RECOVERED'],'original_plan_reference_coverage':orig,'original_plan_reference_coverage_percent':orig/36800*100,'physical_input_candidates_available':sum(bool(x['available_physical_input_id']) for x in final),'physical_input_reference_coverage':available,'physical_input_reference_coverage_percent':available/36800*100,'two_prior_cache_candidates_identity_HOLD':[x['candidate_id'] for x in final if x['recovery_class']=='ALTERNATIVE_RECONSTRUCTED'],'raw_native_control_pairs_needed':len(needed),'raw_native_distance_checks':len(checks),'raw_native_check_status':dict(collections.Counter(x['status'] for x in checks)),'network_accepted':0,'new_solver_executions':0,'metrics':metrics(start)}
 write('FINAL_RECOVERY_REVIEW.json',summary);sources('RECOVERY_REVIEW_SOURCES.json');print(canon(summary))
if __name__=='__main__':main()
