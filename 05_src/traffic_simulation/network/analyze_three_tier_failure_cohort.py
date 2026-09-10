#!/usr/bin/env python3
from pathlib import Path
import json, sumolib
ROOT=Path(__file__).resolve().parents[3]; RUN=ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2'; C=json.loads((RUN/'route_failure_cohort.json').read_text())['failure_cohort']; n=sumolib.net.readNet(str(RUN/'three_tier.net.xml'))
def desc(e):
 return {'edge':e.getID(),'from':e.getFromNode().getID(),'to':e.getToNode().getID(),'delivery_allowed':any(l.allows('delivery') for l in e.getLanes()),'permissions':[sorted(l.getPermissions()) for l in e.getLanes()]}
out=[]
for x in C:
 a=n.getEdge(x['from_edge']); b=n.getEdge(x['to_edge']); path=n.getShortestPath(a,b,vClass='delivery')[0]
 ac=n.getNeighboringEdges(*a.getFromNode().getCoord(),100,False); bc=n.getNeighboringEdges(*b.getFromNode().getCoord(),100,False)
 ac=[(d,e) for e,d in ac if e.getID()!=a.getID()]; bc=[(d,e) for e,d in bc if e.getID()!=b.getID()]
 alternatives=[]; alt_route=False
 for da,ea in ac[:20]:
  for db,eb in bc[:20]:
   if ea.allows('delivery') and eb.allows('delivery') and n.getShortestPath(ea,eb,vClass='delivery')[0]: alt_route=True; alternatives.append({'from_edge':ea.getID(),'to_edge':eb.getID(),'from_distance_m':da,'to_distance_m':db}); break
  if alt_route: break
 reason='ROUTABLE' if path else ('ALTERNATIVE_MAPPING_ROUTEABLE' if alt_route else 'DISCONNECTED_COMPONENT_OR_DIRECTED_TOPOLOGY')
 out.append({'origin_stop_id':x['from_stop_id'],'destination_stop_id':x['to_stop_id'],'origin':desc(a),'destination':desc(b),'sumo_route_exists':bool(path),'nearby_routeable_alternative':alt_route,'nearby_alternatives':alternatives,'root_cause':reason})
(RUN/'failure_cohort_analysis.json').write_text(json.dumps({'sample_pairs':len(out),'failures_reproduced':sum(not z['sumo_route_exists'] for z in out),'pairs':out},indent=2)+'\n')
from collections import Counter
print(Counter(z['root_cause'] for z in out)); print('reproduced failures',sum(not z['sumo_route_exists'] for z in out))
