"""Recover saved OD paths, never solve routes or run a vehicle."""
from evidence import *
import numpy as np,pyarrow.parquet as pq,xml.etree.ElementTree as ET,gzip,collections,sys,math
from decimal import Decimal as D
def pos(x):return format(D(str(x)).normalize(),'f')
def epkey(a,b):return (a['edge'],b['edge'],a['lane'].rsplit('_',1)[1],b['lane'].rsplit('_',1)[1],pos(a['position']),pos(b['position']))
def partial_paths(directory,needed,visited=None):
 visited=set() if visited is None else visited;result={}
 if str(directory) in visited:return result
 visited.add(str(directory))
 try:
  p=use(directory/'PROVENANCE.json');pro=read(p)
  if pro.get('original_execution'):result.update(partial_paths(Path(pro['original_execution']),needed,visited))
 except FileNotFoundError:pass
 try:
  p=use(directory/'loop_paths.jsonl.gz')
  with gzip.open(p,'rt') as h:
   for line in h:
    x=json.loads(line)
    if int(x['index']) in needed:result[int(x['index'])]=(tuple(map(sys.intern,x['edges'])),None,str(p),'saved_loop_paths')
 except FileNotFoundError:pass
 try:
  p=use(directory/'PAIR_CORRECTIONS.json')
  for x in read(p):
   edge=x.get('corrected_route',x.get('corrected_edges'));ix=int(x['row_index'])
   if ix in needed and isinstance(edge,list) and all(isinstance(y,str) for y in edge):result[ix]=(tuple(map(sys.intern,edge)),None,str(p),'saved_pair_correction')
 except FileNotFoundError:pass
 return result
def stitch(segments):
 if any(s is None for s in segments):return None
 out=[]
 for es in segments:
  if not es:return None
  if out:
   if out[-1]!=es[0]:raise ValueError('Original positional leg junction mismatch')
   out.extend(es[1:])
  else:out.extend(es)
 return out
def main():
 start=time.monotonic();old=rows(P2/'B_COMPLETE_RUNS.csv');refs=rows(P2/'B_PLAN_RUN_LINKS.csv');requests=rows(P2/'B_REQUIRED_POSITIONAL_LEGS.csv');end=read(P2/'ENDPOINTS_USED.json');ms=read(U/'review_outputs/staged_qaoa_validation_20261102/mirror_family/MANIFEST.json');arrays={};meta={x['run_id']:x for x in ms}
 for m in ms:
  with np.load(use(m['instance_path'],m['instance_sha256']),allow_pickle=False) as z:arrays[m['run_id']]={k:z[k].copy() for k in ['nodes','partition','travel','distance']}
 targets=collections.defaultdict(dict);candidate_keys={};weight_issues=[]
 for x in old:
  a=arrays[x['problem_id']];rt=json.loads(x['route_indices']);keys=[]
  for ii,jj in zip(rt,rt[1:]):
   aa,bb=str(a['nodes'][ii]),str(a['nodes'][jj]);pi=int(a['partition'][ii,jj]);key=(aa,bb);v=(float(a['travel'][ii,jj]),float(a['distance'][ii,jj]));prior=targets[pi].get(key)
   if prior and prior['weights']!=v:weight_issues.append([pi,aa,bb,prior['weights'],v])
   targets[pi][key]={'weights':v,'endpoint_key':epkey(end[aa+'|ORIGIN'],end[bb+'|DESTINATION'])};keys.append((pi,aa,bb))
  candidate_keys[x['candidate_id']]=keys
 cp=read(B/SC/'sumo_od_final_validation_20261005/CHECKPOINT_ROWS.json');idx=read(B/SC/'sumo_od_final_validation_20261005/ROUTE_NUMERIC_PARTITIONS.json');assert len(cp)==len(idx)==1665
 recovered={};allrows={};partstats=[];checks=[];missingrow=[]
 for counter,pi in enumerate(sorted(targets),1):
  c=cp[pi];q=idx[pi];assert c['partition_id']==q['partition_id'];pf=use(c['output_path'],c['output_hash']);needed=targets[pi]
  cols=['origin_id','destination_id','origin_edge_id','destination_edge_id','origin_lane_id','destination_lane_id','origin_position','destination_position','network_hash','route_status','route_distance_m','static_routing_travel_time_s','router_full_edge_cost_s','route_edge_count','router_sha256','lane_routing_mode','lane_routing_implementation_sha256','distance_authority']
  parquet=pq.ParquetFile(pf);cols=[k for k in cols if k in parquet.schema_arrow.names];data=parquet.read(columns=cols).to_pylist();wanted={};paths={};rp=None
  for rowindex,z in enumerate(data):
   key=(z['origin_id'],z['destination_id'])
   if key not in needed:continue
   wanted[rowindex]=z;t=needed[key];actual=(z['origin_edge_id'],z['destination_edge_id'],z['origin_lane_id'].rsplit('_',1)[1],z['destination_lane_id'].rsplit('_',1)[1],pos(z['origin_position']),pos(z['destination_position']))
   match=(float(z['static_routing_travel_time_s']),float(z['route_distance_m']))==t['weights'];endpoint=actual==t['endpoint_key'];netok=z['network_hash']=='460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2'
   if not (match and endpoint and netok and z['route_status']=='ROUTE_CONFIRMED'):checks.append({'partition':pi,'row':rowindex,'status':'FAIL','weight_match':match,'endpoint_match':endpoint,'net_match':netok})
   allrows[(pi,*key)]={'partition_index':pi,'partition_id':c['partition_id'],'row_index':rowindex,'parquet_path':str(pf),'parquet_sha256':SOURCES[str(pf)]['sha256'],'row':z,'weight_match':match,'endpoint_match':endpoint,'network_match':netok}
  try:
   if q['route_file']:rp=use(q['route_file'],q['route_sha256'])
  except FileNotFoundError:rp=None
  if rp:
   for event,e in ET.iterparse(rp,events=['end']):
    if e.tag!='vehicle':continue
    rid=e.get('id');k=int(rid[1:]) if rid and rid.startswith('R') and rid[1:].isdigit() else -1
    if k in wanted:
     r=e.find('route')
     if r is not None:paths[k]=(tuple(map(sys.intern,r.get('edges').split())),r.get('cost'),str(rp),'original_OD_route_XML')
    e.clear()
  else:paths=partial_paths(Path(c['output_path']).parents[2]/'execution'/c['partition_id'],set(wanted))
  for ri,z in wanted.items():
   key=(pi,z['origin_id'],z['destination_id']);record=allrows[key]
   if ri not in paths:continue
   es,cost,path,kind=paths[ri];rawcostok=cost is None or abs(float(cost)-float(z['router_full_edge_cost_s']))<=1e-7
   good=bool(es) and es[0]==z['origin_edge_id'] and es[-1]==z['destination_edge_id'] and len(es)==z['route_edge_count'] and rawcostok and record['weight_match'] and record['endpoint_match'] and record['network_match']
   if good:recovered[key]=dict(record,edges=es,route_source=path,route_sha256=SOURCES[str(use(path))]['sha256'],route_source_kind=kind,route_cost_string=cost)
   else:checks.append({'partition':pi,'row':ri,'status':'FAIL_ROUTE','cost_ok':rawcostok,'edges_count':len(es),'expected_count':z['route_edge_count']})
  partstats.append({'partition_index':pi,'partition_id':c['partition_id'],'target_pairs':len(needed),'parquet_rows_found':len(wanted),'paths_recovered':sum(k[0]==pi for k in recovered),'route_file':str(rp) if rp else '', 'route_file_sha256':sha(rp) if rp else '', 'status':'ORIGINAL_RECOVERED' if len(paths)==len(wanted)==len(needed) else 'PARTIAL'})
  if counter%20==0:print('partitions',counter,'/',len(targets),'recovered',len(recovered),flush=True)
 table('OD_PARTITION_RECOVERY.csv',partstats)
 # Per-interval evidence and paths are distinct from new whole-B vehicle routes.
 with gzip.open(O/'RECOVERED_OD_LEGS.jsonl.gz','wt') as h:
  for k,x in sorted(recovered.items()):h.write(canon({'key':k,'edges':x['edges'],'route_source':x['route_source'],'route_sha256':x['route_sha256'],'partition_id':x['partition_id'],'row_index':x['row_index'],'parquet_path':x['parquet_path'],'parquet_sha256':x['parquet_sha256'],'OD_time_s':x['row']['static_routing_travel_time_s'],'OD_distance_m':x['row']['route_distance_m'],'network_sha256':x['row']['network_hash'],'router_sha256':x['row']['router_sha256'],'lane_routing_mode':x['row'].get('lane_routing_mode'),'lane_routing_implementation_sha256':x['row'].get('lane_routing_implementation_sha256')})+'\n')
 # Complete recipe payloads from the preceding stage are reused only as templates.
 templates={}
 with use(P2/'RUN_INPUTS.jsonl').open() as h:
  for line in h:
   z=json.loads(line)
   if z['candidate_id'].startswith('B-'):templates[z['candidate_id']]=z['payload']
 result=[];known=[];fullids={};unresolved=[];artificial=[]
 with (O/'RECOVERED_RUN_INPUTS.jsonl').open('w') as h:
  for x in old:
   cid=x['candidate_id'];keys=candidate_keys[cid];missing=[k for k in keys if k not in recovered];segs=[recovered[k]['edges'] if k in recovered else None for k in keys];es=stitch(segs);originwhole='NEW_WHOLE_B_ASSEMBLY_FROM_ORIGINAL_OD_LEGS'
   status='ORIGINAL_RECOVERED' if es else 'PARTIAL' if any(s is not None for s in segs) else 'UNRECOVERABLE';prior_match=None
   if x['run_id']:
    prior=templates[cid]['road_edges'];prior_match=es==prior if es else None
    known.append({'candidate_id':cid,'problem_id':x['problem_id'],'old_run_id':x['run_id'],'all_original_OD_legs_found':es is not None,'full_edge_sequence_equal':prior_match,'old_edge_sha256':digest(prior),'recovered_edge_sha256':digest(es) if es else '', 'position_direction_bound_to_original_OD':all(allrows[k]['endpoint_match'] for k in keys),'OD_time_distance_match_NPZ':all(allrows[k]['weight_match'] for k in keys),'recovery_scope':originwhole,'status':'PASS' if prior_match else 'HOLD_MISSING' if es is None else 'FAIL_PRIOR_ROUTE_NOT_ORIGINAL_OD_SEQUENCE'})
   newrun=''
   if es:
    payload=templates[cid];payload['road_edges']=es;payload['unbound']=[];payload['generator_sha256']=digest({'implementation_sha256':sha(use(Path(__file__))),'scope':originwhole,'OD_partition_manifest_sha256':sha(use(B/SC/'sumo_od_final_validation_20261005/CHECKPOINT_ROWS.json'))});newrun='RECOVERY-RUN-'+digest(payload);fullids[cid]=newrun
    h.write(canon({'candidate_id':cid,'complete_input_id':newrun,'payload':payload,'acceptance':'BLOCKED_BY_NETWORK','whole_B_run_previously_executed':False,'origin_scope':originwhole})+'\n')
   for k in missing:unresolved.append({'candidate_id':cid,'partition_index':k[0],'from_node':k[1],'to_node':k[2],'origin_record_exists':k in allrows,'reason':'ORIGINAL_OD_EDGE_SEQUENCE_NOT_RETAINED' if k in allrows else 'OD_KEY_NOT_FOUND','regeneration_status':'HOLD_NEEDS_EXACT_GENERATOR_PROVENANCE_AND_IDENTITY_TEST'})
   result.append({'candidate_id':cid,'problem_id':x['problem_id'],'scale':x['scale'],'references':int(x['references']),'prior_input_status':x['input_status'],'recovery_status':status,'recovery_scope':originwhole,'total_legs':len(keys),'recovered_legs':len(keys)-len(missing),'unresolved_legs':len(missing),'complete_input_id':newrun,'edge_sequence_sha256':digest(es) if es else '', 'prior37_sequence_equal':prior_match,'network_status':'BLOCKED_BY_NETWORK','operational_reuse_accepted':False,'OD_path_diagnostics':'PASS' if all(allrows.get(k,{}).get('weight_match',False) for k in keys) else 'FAIL','whole_native_route_original_existed':False})
 table('B_ROUTE_RECOVERY_STATUS.csv',result);table('KNOWN37_IDENTITY_COMPARISON.csv',known);table('B_UNRECOVERED_INTERVALS.csv',unresolved)
 # Report requested positional-unit duplicates and coverage without counting policy references as runs.
 reqkeys=[(x['road_sha256'],x['router_sha256'],x['from_edge'],x['to_edge'],x['depart_lane'],x['arrival_lane'],pos(x['depart_pos']),pos(x['arrival_pos']),x['seed'],'delivery') for x in requests]
 rmap={x['candidate_id']:x for x in result};coverage=[]
 for mode in ['scale','config_id','rep']:
  gs=collections.defaultdict(list)
  for x in refs:gs[x[mode] if mode in x else meta[x['problem_id']]['scale_id']].append(x)
  for group,rr in sorted(gs.items()):
   n=sum(bool(rmap[x['candidate_id']]['complete_input_id']) for x in rr);coverage.append({'dimension':mode,'group':group,'references':len(rr),'structurally_recovered_references':n,'coverage_percent':n/len(rr)*100,'network_accepted_references':0})
 table('B_RECOVERY_COVERAGE.csv',coverage)
 count=collections.Counter(x['recovery_status'] for x in result);covered=sum(x['references'] for x in result if x['complete_input_id']);unrecpairs={tuple(k) for x in candidate_keys.values() for k in x if k not in recovered}
 summary={'prior_counts_reconfirmed':{'plan_references':36800,'input_route_candidates':4987,'complete_cached_before':37,'unbound_before':4950,'positional_requests_before':219211},'required_positional_keys_unique':len(set(reqkeys)),'required_positional_key_duplicates':len(reqkeys)-len(set(reqkeys)),'all_OD_pair_keys_requested':sum(map(len,targets.values())),'original_parquet_pairs_located':len(allrows),'original_OD_paths_recovered':len(recovered),'original_OD_paths_not_retained':len(unrecpairs),'input_partitions':len(targets),'candidate_status_counts':dict(count),'structurally_complete_candidates':len(fullids),'covered_plan_references':covered,'coverage_percent':covered/36800*100,'network_accepted_candidates':0,'new_route_solver_runs':0,'new_native_runs':0,'known37_exact_sequence_matches':sum(x['full_edge_sequence_equal'] is True for x in known),'known37_unresolved':sum(x['full_edge_sequence_equal'] is None for x in known),'known37_sequence_differences':sum(x['full_edge_sequence_equal'] is False for x in known),'NPZ_repeated_weight_conflicts':weight_issues,'row_validation_failures':checks,'metrics':metrics(start),'python_executable':sys.executable,'pyarrow_version':__import__('pyarrow').__version__}
 write('ROUTE_RECOVERY_SUMMARY.json',summary);sources('ROUTE_SOURCES.json');print(canon(summary))
if __name__=='__main__':main()
