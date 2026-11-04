"""Materialize known fixed inputs and retain unresolved legs. No SUMO/router runs."""
import xml.etree.ElementTree as ET
from decimal import Decimal as D
import collections,json,time,resource
import numpy as np
from common import *
from contracts import complete_id,operation_policy

def num(x):return format(D(str(x)).normalize(),'f')
def leg_key(a,b):return (a['edge'],b['edge'],a['lane'].rsplit('_',1)[1],b['lane'].rsplit('_',1)[1],num(a['position']),num(b['position']))
def trip_key(x):return (x['from'],x['to'],x['departLane'],x['arrivalLane'],num(x['departPos']),num(x['arrivalPos']))
def xml_vehicle(payload):
 root=ET.Element('routes');v=ET.SubElement(root,'vehicle',payload['vehicle']);ET.SubElement(v,'route',edges=' '.join(payload['road_edges']))
 for x in payload['stops']:ET.SubElement(v,'stop',x)
 return ET.tostring(root,encoding='unicode')
def stitch_segments(segments):
 # Do not diagnose connectivity across a segment that has never been materialized.
 if any(x is None for x in segments):return None,[]
 edges=[]
 for es in segments:
  if not es:return None,['EMPTY_CACHED_LEG']
  if edges:
   if edges[-1]!=es[0]:return None,['LEG_STITCH_MISMATCH']
   edges.extend(es[1:])
  else:edges.extend(es)
 return edges,[]
def static_check(p,lanes,adj,edge_delivery=None):
 errors=[];edges=p.get('road_edges');cursor=-1;previous_position=None
 if edges:
  errors.extend('MISSING_OR_UNCONNECTED_EDGE:'+a+'>'+b for a,b in zip(edges,edges[1:]) if (a,b) not in adj)
  if edge_delivery is not None:errors.extend('ROUTE_CLASS_DENIED_OR_MISSING:'+e for e in edges if not edge_delivery.get(e,False))
 for s in p['stops']:
  lane=lanes.get(s['lane']);edge=s['lane'].rsplit('_',1)[0]
  if not lane:errors.append('MISSING_STOP_LANE:'+s['lane']);continue
  if not 0<=float(s['endPos'])<=lane['length']:errors.append('INVALID_STOP_POSITION:'+s['lane'])
  if lane['allow'] and not {'delivery','all'}&set(lane['allow'].split()):errors.append('STOP_CLASS_DENIED:'+s['lane'])
  if {'delivery','all'}&set(lane['disallow'].split()):errors.append('STOP_CLASS_DENIED:'+s['lane'])
  if edges:
   start=max(0,cursor)
   if cursor>=0 and edges[cursor]==edge and previous_position is not None and float(s['endPos'])<previous_position:start=cursor+1
   try:cursor=edges.index(edge,start);previous_position=float(s['endPos'])
   except ValueError:errors.append('STOP_ORDER_NOT_ON_ROUTE:'+s['actType'])
 return errors
def build():
 begin=time.monotonic();protect_previous();env=environment();envhash=digest(env)
 cfg={'step_s':1,'fcd_period_s':1,'precision':9,'teleport_after_s':-1,'end_s':86400,'background_traffic':False,'collision_action':'warn (SUMO 1.24 default pinned by binary)','tripinfo_write_unfinished':True,'tripinfo_write_undeparted':True,'energy_model':'EXTERNAL_CONTROLLED_DC_NOT_SUMO_BATTERY','mass_effect_on_speed':'NO_MATERIAL_MASS_IN_DYNAMICS'}
 traffic={'mode':'ISOLATED_SINGLE_VEHICLE','seed':20260930,'demand':[]}
 types=use(L/SC/'matched_classical_trajectories_20261007/types.xml');typehash=sha(types)
 router=use(L/SC/'sumo_od_same_edge_loop_fix_20261001/native_router/duarouter_loop');routerhash=sha(router)
 net=use(NET);nethash=sha(net)
 summary=read(U/'review_outputs/causal_engineering_audit_20261027/run01/C_attempt02/C_SUMMARY.json')
 use(U/'review_outputs/integrated_research_results_20261028/run02/ROAD_NETWORK_CLOSURE.md')
 road_gate={'network_sha256':nethash,'geometry_status':summary['frozen_network_geometry'],'external_traffic_validity':summary['external_traffic_validity'],'source_geometry_gaps_over1m':summary['frozen_gaps_over1m'],'source_maximum_gap_m':summary['maximum_gap_m'],'repair_candidate_status':'DYNAMIC_ACCEPTANCE_FAIL_NOT_ADOPTED','representative_regional_execution':'NO_GO','reason':'Frozen geometry FAIL and unaccepted repair; preserve gate from prior protocol'}
 # Stream the pinned network for lane bounds and graph adjacency; no route search.
 lanes={};adj=set();netroot={};edge_delivery={}
 for event,e in ET.iterparse(net,events=('start','end')):
  if event=='start' and e.tag=='net':netroot=dict(e.attrib)
  if event!='end':continue
  if e.tag=='edge':
   flags=[]
   for ll in e.findall('lane'):
    allow=ll.get('allow','');deny=ll.get('disallow','');lanes[ll.get('id')]={'length':float(ll.get('length')),'allow':allow,'disallow':deny};flags.append((not allow or bool({'delivery','all'}&set(allow.split()))) and not bool({'delivery','all'}&set(deny.split())))
   edge_delivery[e.get('id')]=any(flags)
   e.clear()
  elif e.tag=='connection':adj.add((e.get('from'),e.get('to')));e.clear()
  elif e.tag in ('junction','tlLogic'):e.clear()
 road_gate.update(parsed_lanes=len(lanes),parsed_connection_pairs=len(adj),root=netroot)
 write('ROAD_AND_EXECUTION_GATE.json',road_gate)
 details=read(U/'review_outputs/cpx01_d12_case_design_20261017/D12_INPUT_DETAILS.json')
 candidates=rows(U/'review_outputs/cpx01_d12_case_design_20261017/D12_CANDIDATES.csv')
 ops=rows(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv')
 group=collections.defaultdict(list)
 for x in ops:group[(x['PID'],tuple(json.loads(x['visit_order'])),int(x['t_depart']))].append(x)
 assert len(group)==len(candidates)==303
 A=[];Alinks=[];static=[];payloads=[];old_results=[];baseline_cache={}
 generatorhash=digest({'new_adapter_sha256':sha(use(Path(__file__))),'contracts_sha256':sha(use(O/'contracts.py')),'common_sha256':sha(use(O/'common.py')),'legacy_router_sha256':routerhash,'A':'preserve saved edges, stop duration/until; replace requested departure only','B':'compose exact-endpoint cached legs; omit until; duration102; do not route missing legs'})
 for c in candidates:
  detail=details[c['candidate_id']];key=(c['PID'],tuple(json.loads(c['visit_order'])),int(c['departure_s']));refs=group[key]
  vp=use(detail['vehicle_xml']);assert sha(vp)==detail['vehicle_xml_sha256']
  v=ET.parse(vp).getroot().find('vehicle');attrs=dict(v.attrib);attrs['depart']=num(c['departure_s']);edges=v.find('route').get('edges').split();stops=[dict(s.attrib) for s in v.findall('stop')]
  cp=read(refs[0]['classical_source']);ip=use(B/SC/'matched_classical_route_scale_20261007/INPUTS'/(c['PID']+'.npz'));assert sha(ip)==cp['instance_sha256']
  ccfg=dict(cfg);cmdpath=vp.parent/'command.json'
  if cmdpath.exists():ccfg['end_s']=int(read(cmdpath)[-1])
  p={'series_id':'A_OLD_TW_R1','input_sha256':sha(ip),'vehicle':attrs,'vtype_sha256':typehash,'road_sha256':nethash,'road_edges':edges,'stops':stops,'traffic':traffic,'simulation':ccfg,'environment_sha256':envhash,'generator_sha256':generatorhash,'unbound':[]}
  rid,missing=complete_id(p);assert not missing;payloads.append({'candidate_id':c['candidate_id'],'run_id':rid,'payload':p})
  newdir=O/'A_INPUTS'/c['candidate_id'];newdir.mkdir(parents=True,exist_ok=True);(newdir/'vehicle.xml').write_text(xml_vehicle(p)+'\n')
  errors=static_check(p,lanes,adj,edge_delivery);static.append({'series':'A','candidate_id':c['candidate_id'],'run_id':rid,'errors':errors})
  # Saved output is evidence only; complete historical environment/operational acceptance absent.
  opath=use(detail['execution_path']);ex=read(opath);trip=ET.parse(use(opath.parent/'tripinfo.xml')).getroot().find('tripinfo')
  trace=use(detail['canonical_trajectory']);assert sha(trace)==detail['canonical_sha256']
  A.append({'candidate_id':c['candidate_id'],'PID':c['PID'],'input_sha256':sha(ip),'visit_order':canon(list(key[1])),'methods':';'.join(sorted({x['adopted_method'] for x in refs})),'quantum_acquired':refs[0]['quantum_acquired'],'requested_departure_s':key[2],'actual_departure_s':trip.get('depart') if key[2]==0 else '', 'run_id':rid,'complete_input_sha256':rid[4:],'input_status':'COMPLETE_BOUND_CURRENT_ENVIRONMENT','static_status':'PASS' if not errors else 'FAIL','operational_acceptance':'HOLD','source_baseline_vehicle':str(vp),'baseline_vehicle_sha256':sha(vp),'baseline_trajectory':str(trace),'baseline_trajectory_sha256':sha(trace),'reuse_accepted':False,'new_simulation_needed_if_gates_resolved':True,'current_execution_status':'BLOCKED_ROAD_GATE','references':len(refs),'payload_location':'RUN_INPUTS.jsonl#'+c['candidate_id']})
  old_results.append({'candidate_id':c['candidate_id'],'requested_departure_s':key[2],'baseline_departure_s':trip.get('depart'),'saved_returncode':ex['returncode'],'baseline_current_environment_equality':'NOT_PROVEN','zero_departure_evidence_available':key[2]==0,'reuse_status':'HOLD_NOT_ACCEPTED','trajectory_sha256':sha(trace)})
  for x in refs:
   decision=operation_policy(x['L'],x['T_Q'],x['B'],x['quantum_acquired']=='True');assert decision['method']==x['adopted_method'] and decision['departure_s']==D(x['t_depart'])
   Alinks.append({'scenario_id':x['scenario_id'],'PID':x['PID'],'candidate_id':c['candidate_id'],'run_id':rid,'method':x['adopted_method'],'acquired':x['quantum_acquired'],'hypothetical_C_available_s':x['t_C'],'hypothetical_Q_available_s':x['t_Q'],'adoption_deadline_s':x['t_cut'],'adopt_s':x['t_adopt'],'switch_s':x['t_fallback'],'switch_reason':x['fallback_reason'],'requested_departure_s':x['t_depart'],'actual_departure_s':trip.get('depart') if key[2]==0 else '', 'timing_basis':'HYPOTHETICAL_POLICY_NATIVE_DEPARTURE_SEPARATE'})
 table('A_COMPLETE_RUNS.csv',A);table('A_OPERATION_RUN_LINKS.csv',Alinks);table('A_EXISTING_REUSE_ASSESSMENT.csv',old_results)
 # Cache only already-saved exact positional leg paths. Missing paths stay missing.
 endpoints=read(B/SC/'canonical_delivery_trajectories_20261006/ENDPOINT_READBACK.json');cache=collections.defaultdict(dict)
 for directory in ['matched_classical_trajectories_20261007','canonical_delivery_trajectories_20261006','matched_quantum_r1_trajectories_20261007']:
  base=B/SC/directory;trips=ET.parse(use(base/'fixed_legs.trips.xml')).getroot();tmap={t.get('id'):trip_key(t.attrib) for t in trips.findall('trip')}
  routefile=use(base/'fixed_legs.rou.xml')
  for v in ET.parse(routefile).getroot().findall('vehicle'):
   leg=v.find('route')
   if leg is not None and v.get('id') in tmap:
    edge=tuple(leg.get('edges').split());cache[tmap[v.get('id')]][digest(edge)]={'edges':edge,'source':str(routefile),'source_vehicle':v.get('id')}
 manifests=read(U/'review_outputs/staged_qaoa_validation_20261102/mirror_family/MANIFEST.json');bmeta={m['run_id']:m for m in manifests}
 plans=rows(PREV/'B_PLAN_REFERENCES.csv');bgroup=collections.defaultdict(list)
 for x in plans:bgroup[(x['input_sha256'],x['route_indices'])].append(x)
 assert len(plans)==36800 and len(bgroup)==4987
 arrays={}
 for rid,m in bmeta.items():
  pp=use(m['instance_path']);assert sha(pp)==m['instance_sha256']
  with np.load(pp,allow_pickle=False) as z:arrays[rid]={'nodes':list(map(str,z['nodes'])),'demand':z['demand'].tolist(),'service':z['service'].tolist()}
 Bout=[];Blinks=[];unboundlegs=[];legrequests={};endpoints_used={};tasks=[]
 for index,((ih,routejson),refs) in enumerate(sorted(bgroup.items()),1):
  cid='B-'+format(index,'05d');rid=refs[0]['run_id'];m=bmeta[rid];arr=arrays[rid];order=[arr['nodes'][i] for i in json.loads(routejson)];assert len(order)==m['n']+2
  issues=[];edges=[];stops=[];legsources=[];segments=[]
  for i,(aa,bb) in enumerate(zip(order,order[1:])):
   ea=endpoints.get(aa+'|ORIGIN');eb=endpoints.get(bb+'|DESTINATION')
   if not ea or not eb:issues.append('ENDPOINT_MISSING:'+aa+'>'+bb);segments.append(None);continue
   endpoints_used[aa+'|ORIGIN']=ea;endpoints_used[bb+'|DESTINATION']=eb
   key=leg_key(ea,eb);choices=cache.get(key,{})
   if len(choices)!=1:
    segments.append(None)
    why='MISSING_CACHED_POSITIONAL_LEG' if not choices else 'AMBIGUOUS_CACHED_POSITIONAL_LEG'
    issues.append(why);lid='LEG-'+digest(key);unboundlegs.append({'candidate_id':cid,'leg_index':i,'from_node':aa,'to_node':bb,'leg_id':lid,'status':why,'distinct_cached_paths':len(choices)})
    legrequests[lid]={'leg_id':lid,'from_edge':ea['edge'],'to_edge':eb['edge'],'depart_lane':key[2],'arrival_lane':key[3],'depart_pos':key[4],'arrival_pos':key[5],'router_sha256':routerhash,'road_sha256':nethash,'seed':20260930}
   else:
    choice=next(iter(choices.values()));es=list(choice['edges']);legsources.append(choice['source']+'#'+choice['source_vehicle'])
    segments.append(es)
    if es[0]!=ea['edge'] or es[-1]!=eb['edge']:issues.append('CACHE_ENDPOINT_MISMATCH')
   if i<len(order)-2:stops.append({'lane':eb['lane'],'endPos':str(eb['position']),'duration':'102','actType':bb})
  edges,stitch_errors=stitch_segments(segments);issues.extend(stitch_errors)
  depot=endpoints['DEP_006|ORIGIN'];attrs={'id':rid,'type':'delivery','depart':'0','departLane':depot['lane'].rsplit('_',1)[1],'departPos':str(depot['position']),'arrivalLane':depot['lane'].rsplit('_',1)[1],'arrivalPos':str(depot['position']),'arrivalSpeed':'0'}
  p={'series_id':'B_NOW_NO_TW_R0_R5','input_sha256':ih,'vehicle':attrs,'vtype_sha256':typehash,'road_sha256':nethash,'road_edges':edges if not issues else None,'stops':stops,'traffic':traffic,'simulation':cfg,'environment_sha256':envhash,'generator_sha256':generatorhash,'customer_time_windows':False,'route_indices':json.loads(routejson),'visit_order':order,'od_version':{'source':'UNIFIED_NO_CUSTOMER_WINDOWS_V1','original_source_input_sha256':m['original_sha256'],'original_PID':m['original_physical_instance_id'],'changed_road':False,'cost_reused_for_routing':False},'unbound':sorted(set(issues))}
  fullid,missing=complete_id(p);payloads.append({'candidate_id':cid,'run_id':fullid,'payload':p,'recipe_id':'RECIPE-'+digest(p)})
  errors=static_check(p,lanes,adj,edge_delivery);static.append({'series':'B','candidate_id':cid,'run_id':fullid,'errors':errors})
  if fullid:
   directory=O/'B_INPUTS'/cid;directory.mkdir(parents=True,exist_ok=True);(directory/'vehicle.xml').write_text(xml_vehicle(p)+'\n')
  Bout.append({'candidate_id':cid,'problem_id':rid,'scale':m['scale_id'],'input_sha256':ih,'visit_order':canon(order),'route_indices':routejson,'run_id':fullid or '', 'complete_input_sha256':fullid[4:] if fullid else '', 'recipe_id':'RECIPE-'+digest(p),'input_status':'COMPLETE_BOUND_CURRENT_ENVIRONMENT' if fullid else 'UNBOUND','unbound_fields':';'.join(missing),'static_status':'FAIL' if errors else 'PASS_MATERIALIZED_FIELDS' if not fullid else 'PASS','references':len(refs),'existing_reuse_accepted':False,'new_run_needed_if_gates_resolved':bool(fullid),'current_execution_status':'BLOCKED_ROAD_GATE' if fullid else 'BLOCKED_INPUT_AND_ROAD_GATE','leg_source_count':len(legsources),'payload_location':'RUN_INPUTS.jsonl#'+cid})
  for x in refs:
   si=int(rid.split('_')[0][1:]);ix=int(rid.split('_')[1]);rep=int(x['rep']);family=x['family'];variant=x['variant']
   if family=='mirror_family':entropy=[2026110201,si,ix,['MEAN_P2','CVAR10_P2','CVAR01_P2','COHERENT2_P2','COHERENT4_P2'].index(variant),990,rep];seedfile='run_staged_mirror_qaoa.py'
   elif family=='grover_depth':entropy=[2026110202,si,ix,int(variant[-1]),30,rep];seedfile='run_staged_grover_depth.py'
   else:entropy=[2026110210,si,ix,0,rep];seedfile='run_staged_active_p3.py'
   seedsrc=use(U/'review_outputs/staged_qaoa_validation_20261102'/family/'SOURCE_SNAPSHOT/scripts'/seedfile)
   Blinks.append({'family':family,'config_id':variant,'problem_id':rid,'rep':x['rep'],'measurement_seed_source':x['source_path']+'#/records[mode=OPTIMIZED,rep='+x['rep']+']','measurement_seed_entropy':canon(entropy),'PCG64_seed_state4':canon(np.random.SeedSequence(entropy).generate_state(4).tolist()),'seed_rule_source_sha256':sha(seedsrc),'input_sha256':ih,'candidate_id':cid,'run_id':fullid or '', 'input_status':'COMPLETE' if fullid else 'UNBOUND','route_indices':routejson,'plan_source_sha256':x['source_sha256']})
  for node in order[1:-1]:
   j=arr['nodes'].index(node);tasks.append({'candidate_id':cid,'task_id':node,'q_PE':arr['demand'][j],'service_s':102,'ready_s':None,'deadline_s':None,'scope':'NO_CUSTOMER_TIME_WINDOWS'})
 table('B_COMPLETE_RUNS.csv',Bout);table('B_PLAN_RUN_LINKS.csv',Blinks);table('B_UNBOUND_LEGS.csv',unboundlegs);table('B_REQUIRED_POSITIONAL_LEGS.csv',list(legrequests.values()));write('ENDPOINTS_USED.json',endpoints_used);write('B_TASKS.json',tasks)
 with (O/'RUN_INPUTS.jsonl').open('w') as h:
  for x in payloads:h.write(canon(x)+'\n')
 write('STATIC_INPUT_CHECKS.json',static)
 # Representatives are fixed before execution; record blocked cases as well.
 bpilot={'R0_001','R1_001','R2_001','R3_001','R3_040','R3_078','R4_001','R4_040','R4_078','R5_001','R5_036','R5_070'}
 reps=[dict(x,series='B',pilot_gate='BLOCKED_ROAD' if x['run_id'] else 'BLOCKED_INPUT_AND_ROAD') for x in Bout if x['problem_id'] in bpilot]
 table('B_PILOT_CANDIDATES.csv',reps)
 apilot=rows(U/'review_outputs/cpx01_d12_case_design_20261017/PILOT_CASES.csv');amap={x['candidate_id']:x for x in A}
 table('A_PILOT_CANDIDATES.csv',[dict(x,full_run_id=amap[x['candidate_id']]['run_id'],pilot_gate='BLOCKED_ROAD') for x in apilot])
 # Separate four-condition mechanism references, without silently broadening 303 policy candidates.
 amaplogical={(x['PID'],x['visit_order'],int(x['requested_departure_s'])):x for x in A};success={x['PID'] for x in ops if x['quantum_acquired']=='True'};four=[];mechanism={}
 for x in ops:
  if x['PID'] not in success:continue
  c=read(x['classical_source']);q=read(x['quantum_source']);routes={'C':c['customer_order'],'Q':q['best_final_feasible_route']['route_ids']}
  for rc,tc in [('C','C'),('Q','C'),('C','Q'),('Q','Q')]:
   departure=int(x['t_depart_C'] if tc=='C' else x['t_depart']);match=amaplogical.get((x['PID'],canon(routes[rc]),departure))
   mkey=(x['PID'],canon(routes[rc]),departure)
   if match:fullid=match['run_id'];mechid=''
   else:
    if mkey not in mechanism:
     template=next(y for y in A if y['PID']==x['PID'] and y['visit_order']==canon(routes[rc]));p=json.loads(canon(next(y['payload'] for y in payloads if y['candidate_id']==template['candidate_id'])));p['vehicle']['depart']=str(departure);mid='AMECH-'+str(len(mechanism)+1).zfill(3);fullid,miss=complete_id(p);assert not miss
     mechanism[mkey]={'mechanism_candidate_id':mid,'PID':x['PID'],'visit_order':canon(routes[rc]),'requested_departure_s':departure,'run_id':fullid,'template_policy_candidate':template['candidate_id'],'reuse_accepted':False,'execution_status':'BLOCKED_ROAD_GATE'}
     payloads.append({'candidate_id':mid,'run_id':fullid,'payload':p});dd=O/'A_MECHANISM_INPUTS'/mid;dd.mkdir(parents=True,exist_ok=True);(dd/'vehicle.xml').write_text(xml_vehicle(p)+'\n')
     static.append({'series':'A_MECHANISM','candidate_id':mid,'run_id':fullid,'errors':static_check(p,lanes,adj,edge_delivery)})
    fullid=mechanism[mkey]['run_id'];mechid=mechanism[mkey]['mechanism_candidate_id']
   four.append({'scenario_id':x['scenario_id'],'PID':x['PID'],'condition':rc+tc,'visit_order':canon(routes[rc]),'requested_departure_s':departure,'policy_candidate_id':match['candidate_id'] if match else '', 'mechanism_candidate_id':mechid,'run_id':fullid,'status':'BOUND_POLICY_INPUT' if match else 'BOUND_MECHANISM_ONLY','interpretation':'COUNTERFACTUAL_MECHANISM_NOT_ADOPTION'})
 table('A_FOUR_CONDITION_LINKS.csv',four)
 table('A_ADDITIONAL_MECHANISM_RUNS.csv',list(mechanism.values()))
 write('STATIC_INPUT_CHECKS.json',static)
 with (O/'RUN_INPUTS.jsonl').open('w') as h:
  for x in payloads:h.write(canon(x)+'\n')
 acount=len({x['run_id'] for x in A});bcount=len({x['run_id'] for x in Bout if x['run_id']});unbound=sum(not x['run_id'] for x in Bout)
 result={'A':{'references':len(Alinks),'logical_candidates':303,'complete_unique_runs':acount,'reusable_accepted':0,'new_runs_needed_if_gates_resolved':acount,'unbound':0,'operationally_accepted_runs':0,'zero_departure_evidence':sum(x['requested_departure_s']==0 for x in A),'four_condition_references':len(four),'additional_mechanism_combinations':len(mechanism),'policy_and_mechanism_unique_runs':len({y['run_id'] for y in payloads if y['payload']['series_id']=='A_OLD_TW_R1'})},'B':{'references':len(Blinks),'input_route_pairs':len(Bout),'complete_unique_runs':bcount,'reusable_accepted':0,'new_runs_needed_known_bound_subset':bcount,'unbound_input_route_pairs':unbound,'eventual_runs_unknown':True,'operationally_accepted_runs':0,'missing_positional_leg_requests':len(legrequests),'pilot_problems':12,'pilot_reference_count':sum(x['references'] for x in reps),'pilot_input_route_pairs':len(reps),'pilot_bound_pairs':sum(bool(x['run_id']) for x in reps)},'road_gate':road_gate,'static_error_candidates':sum(bool(x['errors']) for x in static),'builder_wall_s':time.monotonic()-begin,'builder_CPU_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'builder_max_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'regional_SIMULATION_runs_executed':0,'generator_sha256':generatorhash,'environment_sha256':envhash}
 write('RUN_MANIFEST_SUMMARY.json',result);save_sources('MANIFEST_SOURCE_FILES.json');print(canon(result))
if __name__=='__main__':build()
