"""Static network diagnosis and saved collision readback; zero native executions."""
from evidence import *
import xml.etree.ElementTree as ET,math,collections,heapq,gzip,sys
def structured(e):return {'tag':e.tag,'attributes':dict(e.attrib),'children':[structured(c) for c in e]}
def profile(path,label,shape_lanes):
 path=use(path);lanes={};edges={};hashes={};connections=[];root={};junction_xy={}
 for event,e in ET.iterparse(path,events=['start','end']):
  if event=='start' and e.tag=='net':root=dict(e.attrib)
  if event!='end':continue
  if e.tag=='edge':
   eid=e.get('id');edges[eid]=dict(e.attrib);hashes[('edge',eid)]=digest(dict(e.attrib))
   for ln in e.findall('lane'):
    lid=ln.get('id');pts=ln.get('shape','').split();first=tuple(map(float,pts[0].split(','))) if pts else None;last=tuple(map(float,pts[-1].split(','))) if pts else None
    lanes[lid]={'edge':eid,'length':float(ln.get('length')),'speed':float(ln.get('speed')),'first':first,'last':last,'allow':ln.get('allow',''),'disallow':ln.get('disallow',''),'shape':ln.get('shape') if lid in shape_lanes else None};hashes[('lane',lid)]=digest(dict(ln.attrib))
   e.clear()
  elif e.tag=='connection':
   a=dict(e.attrib);key=canon([a.get(k) for k in ['from','to','fromLane','toLane']]);hashes[('connection',key)]=digest(a);connections.append(a);e.clear()
  elif e.tag=='junction':
   jid=e.get('id');hashes[('junction',jid)]=digest(structured(e));junction_xy[jid]=(float(e.get('x')),float(e.get('y')));e.clear()
  elif e.tag=='tlLogic':hashes[('tlLogic',e.get('id')+'|'+e.get('programID',''))]=digest(structured(e));e.clear()
 gaps=0;missing=0;maximum=0;tops=[];badpairs=set();affected=set()
 with gzip.open(O/(label+'_GAP_PRIMITIVES.csv.gz'),'wt',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['connection_index','from_lane','next_lane','to_lane','junction','gap_m']);w.writeheader()
  for i,c in enumerate(connections):
   fl=c['from']+'_'+c['fromLane'];tl=c['to']+'_'+c['toLane'];nxt=c.get('via') or tl
   if fl not in lanes or nxt not in lanes or not lanes[fl]['last'] or not lanes[nxt]['first']:missing+=1;continue
   gap=math.dist(lanes[fl]['last'],lanes[nxt]['first']);maximum=max(maximum,gap)
   if gap>1:
    gaps+=1;j=edges[c['from']].get('to') or (c['from'][1:].rsplit('_',1)[0] if c['from'].startswith(':') else 'UNKNOWN');affected.add(j)
    row={'connection_index':i,'from_lane':fl,'next_lane':nxt,'to_lane':tl,'junction':j,'gap_m':gap};w.writerow(row)
    item=(gap,i,row)
    if len(tops)<30:heapq.heappush(tops,item)
    elif gap>tops[0][0]:heapq.heapreplace(tops,item)
    if not c['from'].startswith(':'):badpairs.add((c['from'],c['to']))
 out={'label':label,'path':str(path),'sha256':SOURCES[str(path)]['sha256'],'root':root,'edges':len(edges),'lanes':len(lanes),'connections':len(connections),'connection_key_count':sum(k[0]=='connection' for k in hashes),'junctions':len(junction_xy),'gap_over1m':gaps,'maximum_gap_m':maximum,'missing_lane_references':missing,'affected_junctions':len(affected),'top_gaps':[x[2] for x in sorted(tops,reverse=True)]}
 write(label+'_PROFILE.json',out);return out,lanes,edges,hashes,badpairs,junction_xy
def point(lane,position):
 if not lane or not lane['shape'] or position<0 or position>lane['length']:return None
 pts=[tuple(map(float,x.split(','))) for x in lane['shape'].split()];lens=[math.dist(a,b) for a,b in zip(pts,pts[1:])];target=position/lane['length']*sum(lens)
 for a,b,dist in zip(pts,pts[1:],lens):
  if target<=dist and dist>0:return [a[0]+(b[0]-a[0])*target/dist,a[1]+(b[1]-a[1])*target/dist]
  target-=dist
 return list(pts[-1])
def main():
 start=time.monotonic();eps=read(P2/'ENDPOINTS_USED.json');wanted={x['lane'] for x in eps.values()};root=U/'review_outputs';gen=read(root/'road_network_b6_priority_reacceptance_20261028/run01/GENERATION.json');n1=use(gen['output'],gen['output_sha256'])
 zero,l0,e0,h0,bad0,j0=profile(NET,'N0',wanted);print('N0 profile complete',flush=True)
 one,l1,e1,h1,bad1,j1=profile(n1,'N1',wanted);print('N1 profile complete',flush=True)
 diff=collections.Counter()
 with gzip.open(O/'NETWORK_ELEMENT_DIFF.csv.gz','wt',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['element_type','element_id','change','N0_sha256','N1_sha256']);w.writeheader()
  for key in sorted(set(h0)|set(h1)):
   a,b=h0.get(key),h1.get(key)
   if a==b:continue
   change='ADDED' if a is None else 'REMOVED' if b is None else 'CHANGED';diff[(key[0],change)]+=1;w.writerow({'element_type':key[0],'element_id':key[1],'change':change,'N0_sha256':a,'N1_sha256':b})
 table('NETWORK_DIFF_COUNTS.csv',[{'element_type':k[0],'change':k[1],'count':v} for k,v in sorted(diff.items())])
 # Quantify endpoint reuse; an unchanged lane id/offset does not imply same coordinate.
 epout=[]
 for key,x in eps.items():
  pos=float(x['position']);a=l0.get(x['lane']);b=l1.get(x['lane']);pa=point(a,pos);pb=point(b,pos)
  epout.append({'endpoint_key':key,'lane':x['lane'],'position_m':pos,'N0_length_m':a['length'] if a else None,'N1_length_m':b['length'] if b else None,'N1_lane_present':b is not None,'N1_position_in_bounds':b is not None and 0<=pos<=b['length'],'same_offset_coordinate_difference_m':math.dist(pa,pb) if pa and pb else None,'identity_scope':'MODEL_PROJECTION_RATIO_WITH_DECLARED_LANE_LENGTH_NOT_REAL_GATE','mapping_status':x['mapping_status']})
 table('ENDPOINT_REUSE_N0_N1.csv',epout)
 # Fixed external lane0 path proxy: demonstrate changing weights, not a recomputed OD matrix.
 def lane0path(es,vehicle,lanes):
  vals=[lanes.get(e+'_0') for e in es]
  if not all(vals):return None,None
  dep=float(vehicle['departPos']);arr=float(vehicle['arrivalPos'])
  if dep>vals[0]['length'] or arr>vals[-1]['length']:return None,None
  distances=[x['length'] for x in vals];distances[0]-=dep;distances[-1]-=vals[-1]['length']-arr
  return math.fsum(distances),math.fsum(d/x['speed'] for d,x in zip(distances,vals))
 paths=[]
 with use(P2/'RUN_INPUTS.jsonl').open() as f:
  for line in f:
   x=json.loads(line);p=x['payload']
   if not p['road_edges']:continue
   a,b=lane0path(p['road_edges'],p['vehicle'],l0);c,d=lane0path(p['road_edges'],p['vehicle'],l1);pairs=list(zip(p['road_edges'],p['road_edges'][1:]));paths.append({'candidate_id':x['candidate_id'],'series':p['series_id'],'source_run_id':x['run_id'],'edge_count':len(p['road_edges']),'N0_direct_bad_external_pair_occurrences':sum(pair in bad0 for pair in pairs),'N1_missing_external_edges':sum(e not in e1 for e in p['road_edges']),'N0_lane0_path_distance_proxy_m':a,'N1_lane0_path_distance_proxy_m':c,'proxy_distance_change_m':c-a if c is not None and a is not None else None,'N0_freeflow_proxy_s':b,'N1_freeflow_proxy_s':d,'proxy_time_change_s':d-b if d is not None and b is not None else None,'interpretation':'STATIC_FIXED_PATH_LANE0_PROXY_NOT_NATIVE_DISTANCE_OR_OD_OPTIMUM'})
 table('SAVED_RUN_NETWORK_EXPOSURE.csv',paths)
 # Collision event causes and acceptance recomputed from row evidence, not the narrative total.
 ce=rows(root/'road_network_b6_collision_reconstruction_20261028/run01/FINAL_EVENT_CAUSES.csv');recon=rows(root/'road_network_b6_collision_reconstruction_20261028/run01/ALL_EVENT_RECONSTRUCTION.csv');contrast=rows(root/'road_network_b6_collision_reconstruction_20261028/BEFORE_AFTER.csv');cc=collections.Counter(x['category'] for x in ce);tls=sorted({x['tls'] for x in ce});pairs=sorted({(x['tls'],x['collider_actual_link'],x['victim_actual_link']) for x in ce})
 expected=read(root/'road_network_b6_collision_reconstruction_20261028/FINAL_ACCEPTANCE.json');eventok=len(ce)==expected['all_original_events_reconstructed'] and dict(cc)==expected['causal_groups'] and all(x['rectangles_overlap']=='True' for x in ce)
 totals={col:sum(int(x[col]) for x in contrast) for col in ['scheduled','before_collisions','after_collisions','before_arrived','after_arrived','before_abnormal_stops','after_abnormal_stops']}
 table('COLLISION_EVENT_CAUSES.csv',ce);table('COLLISION_LANE_RECONSTRUCTION.csv',recon)
 commands=[]
 for p in (root/'road_network_b6_collision_reconstruction_20261028/run01').glob('*_REPLAY_COMMAND.json'):commands.append({'source_path':str(use(p)),'source_sha256':sha(p),'command':read(p),'purpose':'Saved exact-signature replay of diagnosed collision events; not executed in this task'})
 write('MINIMAL_REPLAY_EVIDENCE.json',{'first_collision_event':ce[0],'first_collision_lanes':recon[0],'saved_replay_commands':commands,'new_native_runs':0,'reason_no_new_run':'Raw 183-event geometry/state/cause and saved exact replay already available; static diagnosis suffices to reject adoption','future_limit':{'max_runs':10,'max_wall_per_run_s':120},'not_claimed_minimality':'Existing probe 540 scheduled vehicles, not mathematically minimal two-vehicle witness'})
 # Locate the maximum-gap primitive in original pre-extension run2 without loading another full network.
 maxrow=zero['top_gaps'][0];selected={maxrow['from_lane'],maxrow['next_lane'],maxrow['to_lane']};run2=use(R/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml');before={}
 for event,el in ET.iterparse(run2,events=['end']):
  if el.tag=='lane' and el.get('id') in selected:before[el.get('id')]=dict(el.attrib)
  if el.tag=='edge':el.clear()
 case={'N0_gap_record':maxrow,'pre_extension_run2_selected_lanes':before,'run2_sha256':SOURCES[str(run2)]['sha256'],'N0_selected_lanes':{k:l0[k] for k in selected if k in l0},'N1_same_ID_lanes':{k:l1[k] for k in selected if k in l1},'note':'N1 internal IDs can change semantic movement; compare stable external movements, not internal numeric ID alone'};write('MAX_GAP_ROOT_CAUSE_CASE.json',case)
 # Root cause and change records from original generation sources.
 for p in [root/'road_network_static_repair_20261027/run01/REPORT.md',root/'road_network_static_repair_20261027/run01/INTRODUCED_GAP_CAUSAL_MATCH.csv',root/'road_network_local_repair_20261028/run01/GENERATION.json',root/'road_network_b6_priority_reacceptance_20261028/run01/TLS_PATCH.json',root/'road_network_b6_collision_reconstruction_20261028/FINAL_ACCEPTANCE.json',root/'road_network_downstream_control_20261028/run01/FINAL_ACCEPTANCE.json']:use(p)
 summary={'N0':zero,'N1':one,'N2':{'state':'NOT_BUILT','sha256':None,'adoption':'HOLD_NO_ACCEPTED_MINIMAL_GLOBAL_FIX'},'N0_gap_recalculation_matches_prior':zero['gap_over1m']==563513 and abs(zero['maximum_gap_m']-97.03372815676067)<1e-9,'diff_counts':[{'element_type':k[0],'change':k[1],'count':v} for k,v in sorted(diff.items())],'used_endpoints':len(epout),'N1_missing_used_lanes':sum(not x['N1_lane_present'] for x in epout),'N1_out_of_bounds_used_endpoints':sum(not x['N1_position_in_bounds'] for x in epout),'N1_coordinate_shift_over0_1m_in_bounds':sum(x['same_offset_coordinate_difference_m'] is not None and x['same_offset_coordinate_difference_m']>.1 for x in epout),'saved_bound_routes_checked':len(paths),'saved_bound_routes_with_direct_bad_primitive':sum(x['N0_direct_bad_external_pair_occurrences']>0 for x in paths),'fixed_path_proxy_changed':sum(x['proxy_distance_change_m'] is not None and abs(x['proxy_distance_change_m'])>1e-7 for x in paths),'collision_rows':len(ce),'collision_cause_counts':dict(cc),'collision_TLS':tls,'collision_link_pairs':pairs,'collision_row_match':eventok,'collision_comparison_totals':totals,'new_native_runs':0,'OD_actual_new_matrix_equality':'HOLD_NOT_RECOMPUTED; fixed path/endpoint changes disallow automatic reuse','metrics':metrics(start)}
 write('NETWORK_DIAGNOSIS_SUMMARY.json',summary);sources('NETWORK_SOURCES.json');print(canon({k:v for k,v in summary.items() if k not in ['N0','N1']}))
if __name__=='__main__':main()
