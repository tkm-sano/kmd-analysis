"""Separate arithmetic checks of collision body overlap and trajectory discontinuity."""
from evidence import *
import math,gzip,collections,xml.etree.ElementTree as ET
def rectangle(front,back,width):
 dx,dy=front[0]-back[0],front[1]-back[1];length=math.hypot(dx,dy);nx,ny=-dy/length*width/2,dx/length*width/2
 return [(front[0]+nx,front[1]+ny),(front[0]-nx,front[1]-ny),(back[0]-nx,back[1]-ny),(back[0]+nx,back[1]+ny)]
def overlap(a,b):
 for poly in [a,b]:
  for p,q in zip(poly,poly[1:]+poly[:1]):
   axis=(-(q[1]-p[1]),q[0]-p[0]);u=[axis[0]*x+axis[1]*y for x,y in a];v=[axis[0]*x+axis[1]*y for x,y in b]
   if max(u)<=min(v) or max(v)<=min(u):return False
 return True
def main():
 start=time.monotonic();root=U/'review_outputs';events=read(root/'road_network_b6_collision_reconstruction_20261028/run01/ALL_EVENT_RECONSTRUCTION.json');out=[]
 for x in events:
  c=x['native_collision'];polys=[]
  for role in ['collider','victim']:
   front=list(map(float,c[role+'Front'].split(',')));back=list(map(float,c[role+'Back'].split(',')));state=next(p['state'] for p in x['participants'] if p['role']==role);polys.append(rectangle(front,back,float(state['width'])))
  actual=overlap(*polys);out.append({'event_id':x['event_id'],'TLS':x['tls'],'native_time':x['native_time'],'collider_lane':x['participants'][0]['state']['lane'],'victim_lane':x['participants'][1]['state']['lane'],'recomputed_overlap':actual,'reported_overlap':x['independent_rectangle_overlap_reconstructed'],'status':'PASS' if actual==x['independent_rectangle_overlap_reconstructed'] else 'FAIL','scope':'SAT of stored native collision front/back and participant width; not new simulation'})
 table('COLLISION_BODY_OVERLAP_INDEPENDENT.csv',out)
 ac=rows(P2/'A_COMPLETE_RUNS.csv')[0];path=use(ac['baseline_trajectory'],ac['baseline_trajectory_sha256']);jumps=[];previous=None;maxjump=0;count=0
 with gzip.open(path,'rt') as h:
  for line,row in enumerate(csv.DictReader(h),2):
   t=float(row['timestamp_s']);x=float(row['x_m']);y=float(row['y_m']);speed=float(row['speed_m_s'])
   if previous:
    pt,px,py=previous;chord=math.hypot(x-px,y-py);ds=speed*(t-pt);excess=chord-ds;maxjump=max(maxjump,excess)
    if excess>1:
     count+=1
     if len(jumps)<30:jumps.append({'source_path':str(path),'source_sha256':SOURCES[str(path)]['sha256'],'CSV_line':line,'PID':ac['PID'],'time_s':t,'XY_chord_m':chord,'speed_dt_m':ds,'excess_m':excess,'lane':row['lane_id']})
   previous=(t,x,y)
 table('SAVED_TRACE_DISCONTINUITY_READBACK.csv',jumps)
 bad=set()
 with gzip.open(use(O/'N0_GAP_PRIMITIVES.csv.gz'),'rt') as h:
  for x in csv.DictReader(h):
   a=x['from_lane'].rsplit('_',1)[0];b=x['to_lane'].rsplit('_',1)[0]
   if not a.startswith(':'):bad.add((a,b))
 exposure=[]
 with use(O/'RECOVERED_RUN_INPUTS.jsonl').open() as h:
  for line in h:
   x=json.loads(line);es=x['payload']['road_edges'];n=sum(z in bad for z in zip(es,es[1:]));exposure.append({'candidate_id':x['candidate_id'],'complete_input_id':x['complete_input_id'],'N0_direct_bad_external_primitives':n,'scope':'Explicit matching external transition; native effects not rerun'})
 table('RECOVERED_B_NETWORK_EXPOSURE.csv',exposure)
 for p in [B/'05_src/traffic_simulation/network/repair_network_geometry_lengths.py',R/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/command_contract.txt',R/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/config_snapshot.yml',R/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/repair_transform_report.json']:use(p)
 cause=rows(root/'road_network_b6_collision_reconstruction_20261028/run01/FINAL_EVENT_CAUSES.csv');pairset={(x['tls'],*sorted([int(x['collider_actual_link']),int(x['victim_actual_link'])])) for x in cause}
 write('NETWORK_SUPPLEMENT_SUMMARY.json',{'collision_SAT_checks':len(out),'collision_SAT_passed':sum(x['status']=='PASS' for x in out),'directed_collision_link_pairs':len({(x['tls'],x['collider_actual_link'],x['victim_actual_link']) for x in cause}),'unordered_collision_movement_pairs':len(pairset),'known_trace_gap_events':count,'known_trace_maximum_XY_excess_m':maxjump,'known_trace_PID':ac['PID'],'recovered_B_inputs':len(exposure),'recovered_B_inputs_with_direct_bad_primitive':sum(x['N0_direct_bad_external_primitives']>0 for x in exposure),'native_executions':0,'metrics':metrics(start)})
 sources('NETWORK_SUPPLEMENT_SOURCES.json');print('SAT',len(out),'pass',sum(x['status']=='PASS' for x in out),'trace jumps',count,'B exposure',len(exposure))
if __name__=='__main__':main()
