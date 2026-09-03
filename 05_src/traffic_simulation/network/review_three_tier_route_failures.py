#!/usr/bin/env python3
from pathlib import Path
import csv,json,re
import sumolib
from scipy.spatial import cKDTree
import numpy as np
ROOT=Path(__file__).resolve().parents[3]; RUN=ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2'; NET=RUN/'three_tier.net.xml'; STOPS=ROOT/'03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv'
def main():
 n=sumolib.net.readNet(str(NET)); es=n.getEdges(); tree=cKDTree(np.asarray([e.getShape()[len(e.getShape())//2] for e in es])); mapped=[]; ids=[]
 for r in csv.DictReader(STOPS.open()):
  m=re.search(r'POINT \(([-0-9.]+) ([-0-9.]+)\)',r['building_representative_point']); x,y=n.convertLonLat2XY(float(m.group(1)),float(m.group(2))); _,i=tree.query((x,y)); mapped.append(es[int(i)]); ids.append(r['stop_id'])
 sample=list(range(0,len(mapped),max(1,len(mapped)//100))); failures=[]; success=0
 for a,b in zip(sample,sample[1:]):
  path=n.getShortestPath(mapped[a],mapped[b],vClass='delivery')[0]
  if path: success+=1
  else: failures.append({'from_stop_id':ids[a],'to_stop_id':ids[b],'from_edge':mapped[a].getID(),'to_edge':mapped[b].getID(),'from_component':[mapped[a].getFromNode().getID(),mapped[a].getToNode().getID()],'to_component':[mapped[b].getFromNode().getID(),mapped[b].getToNode().getID()]})
 out={'status':'REVIEW_REQUIRED','sample_pairs':len(sample)-1,'routeable_pairs':success,'failed_pairs':len(failures),'failure_cohort':failures,'scope':'failed sampled delivery OD pairs only'}; (RUN/'route_failure_cohort.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({'sample_pairs':len(sample)-1,'routeable_pairs':success,'failed_pairs':len(failures)}))
if __name__=='__main__': main()
