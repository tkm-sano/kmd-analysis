#!/usr/bin/env python3
from pathlib import Path
import csv,json,re
import numpy as np, sumolib
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2'
n=sumolib.net.readNet(str(RUN/'three_tier.net.xml')); es=n.getEdges()
tree=cKDTree(np.asarray([e.getShape()[len(e.getShape())//2] for e in es]))
ov=json.loads((RUN/'routeable_edge_overrides.json').read_text())['overrides']; ids=[]; mapped=[]
for r in csv.DictReader((ROOT/'03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv').open()):
 ids.append(r['stop_id'])
 if r['stop_id'] in ov: mapped.append(n.getEdge(ov[r['stop_id']]))
 else:
  m=re.search(r'POINT \(([-0-9.]+) ([-0-9.]+)\)',r['building_representative_point']); x,y=n.convertLonLat2XY(float(m.group(1)),float(m.group(2))); _,i=tree.query((x,y)); mapped.append(es[int(i)])
def evaluate(indexes):
 ok=0; failed=[]
 for a,b in zip(indexes,indexes[1:]):
  if n.getShortestPath(mapped[a],mapped[b],vClass='delivery')[0]: ok+=1
  else: failed.append((ids[a],ids[b],mapped[a].getID(),mapped[b].getID()))
 return ok,failed
base=list(range(0,len(mapped),max(1,len(mapped)//100))); add=list(range(1,len(mapped),max(1,len(mapped)//100)))[:101]
b_ok,b_fail=evaluate(base); a_ok,a_fail=evaluate(add)
out={'status':'PASS' if not b_fail else 'FAIL','primary_sample':{'pairs':len(base)-1,'routeable':b_ok,'failed':b_fail},'additional_deterministic_sample':{'pairs':len(add)-1,'routeable':a_ok,'failed':a_fail},'mapping_fix':'17 failed OD cohort only'}
(RUN/'routeability_after_mapping_fix.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'primary_pairs':len(base)-1,'primary_routeable':b_ok,'additional_pairs':len(add)-1,'additional_routeable':a_ok,'primary_failures':len(b_fail),'additional_failures':len(a_fail)}))
