#!/usr/bin/env python3
"""Select and map the R09 Baseline depot proxy to the accepted SUMO network."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re
from datetime import datetime, timezone
from pathlib import Path
import sumolib, yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / 'reproducibility/config/traffic_simulation/evrp_r09_depot_v1.yml'

def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))
def point_offset(edge, x, y):
    best = (float('inf'), 0.0); offset = 0.0
    for (x1,y1),(x2,y2) in zip(edge.getShape(), edge.getShape()[1:]):
        dx,dy=x2-x1,y2-y1; length=math.hypot(dx,dy)
        t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/(length*length))) if length else 0
        d=math.hypot(x-(x1+t*dx),y-(y1+t*dy))
        if d < best[0]: best=(d, offset+t*length)
        offset += length
    return best

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',type=Path,default=DEFAULT_CONFIG); ap.add_argument('--run-id',required=True); a=ap.parse_args()
    cp=a.config.resolve(); cfg=yaml.safe_load(cp.read_text(encoding='utf-8'))
    cand=(ROOT/cfg['inputs']['depot_candidates']).resolve(); pop=(ROOT/cfg['inputs']['customer_population']).resolve(); ids_path=(ROOT/cfg['inputs']['customer_ids']).resolve(); netpath=(ROOT/cfg['inputs']['network']).resolve(); acc=(ROOT/cfg['inputs']['network_acceptance']).resolve()
    out=(ROOT/cfg['output_root']/a.run_id).resolve(); out.mkdir(parents=True,exist_ok=False)
    candidates=read_csv(cand); chosen=[r for r in candidates if r['scenario_depot_id']==cfg['selected_depot_id']]
    if len(chosen)!=1: raise ValueError('selected depot candidate is not unique')
    d=chosen[0]; lon,lat=float(d['longitude']),float(d['latitude'])
    if not all(math.isfinite(v) for v in (lon,lat)) or not(-180<=lon<=180 and -90<=lat<=90): raise ValueError('invalid depot coordinates')
    weights=read_csv(pop); customer_ids={r['stop_id'] for r in read_csv(ids_path)}; pts=[]
    for r in weights:
        if r['stop_id'] in customer_ids: pts.append([float(v) for v in re.findall(r'[-+]?\d+(?:\.\d+)?',r['building_representative_point'])])
    cx=sum(x for x,y in pts)/len(pts); cy=sum(y for x,y in pts)/len(pts)
    comparison=[]
    for r in candidates:
        x,y=float(r['longitude']),float(r['latitude']); dist=math.hypot((x-cx)*111000*math.cos(math.radians(cy)),(y-cy)*111000)
        comparison.append({**r,'customer_centroid_distance_m':round(dist,6),'selected':r['scenario_depot_id']==d['scenario_depot_id']})
    net=sumolib.net.readNet(str(netpath),withInternal=False); x,y=net.convertLonLat2XY(lon,lat); found=[]
    for radius in (100,500,2000):
        found=[(e,dist) for e,dist in net.getNeighboringEdges(x,y,radius,includeJunctions=False) if cfg['vehicle_class'] in e.getLane(0).getPermissions()]
        if found: break
    if not found: raise ValueError('no delivery-permitted edge near depot')
    edge,_=min(found,key=lambda z:z[1]); mapping_dist,offset=point_offset(edge,x,y)
    rec={'depot_id':d['scenario_depot_id'],'hub_id':d['hub_id'],'facility_name':d['facility_name'],'longitude':lon,'latitude':lat,'source':'MLIT P31 logistics facility proxy snapshot','classification':'PROXY','proxy_or_observed':'proxy','mapped_sumo_edge_id':edge.getID(),'edge_offset_m':offset,'edge_length_m':edge.getLength(),'mapping_distance_m':mapping_dist,'vehicle_class':cfg['vehicle_class'],'vehicle_access':'accepted SUMO lane permission includes delivery','from_node':edge.getFromNode().getID(),'to_node':edge.getToNode().getID(),'network_hash':sha256(netpath),'network_acceptance_hash':sha256(acc),'selection_rule':'priority rank 1; truck terminal/parcel operator terminal; Ota-ku proxy; not observed operator depot'}
    with (out/'depot_definition.csv').open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=list(rec)); w.writeheader(); w.writerow(rec)
    with (out/'depot_candidate_comparison.csv').open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=list(comparison[0])); w.writeheader(); w.writerows(comparison)
    validation={'candidate_count':len(candidates),'selected_depot_id':d['scenario_depot_id'],'selected_candidate_centroid_distance_m':next(r['customer_centroid_distance_m'] for r in comparison if r['selected']),'mapping_distance_m':mapping_dist,'mapped_edge':edge.getID(),'vehicle_access':cfg['vehicle_class'] in edge.getLane(0).getPermissions(),'accepted_network_hash':sha256(netpath)}
    (out/'r09_depot_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    inputs={'depot_candidates':cand,'customer_population':pop,'customer_ids':ids_path,'network':netpath,'network_acceptance':acc}
    manifest={'schema_version':'evrp-r09-depot-v1','run_id':a.run_id,'created_at':datetime.now(timezone.utc).isoformat(),'fixture':{'n':len(customer_ids),'is_production_problem_size':False},'selected_depot':rec,'inputs':{k:{'path':str(v.relative_to(ROOT)),'sha256':sha256(v)} for k,v in inputs.items()},'config':{'path':str(cp.relative_to(ROOT)),'sha256':sha256(cp)},'code':{'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha256(Path(__file__))},'outputs':{}}
    for p in sorted(out.iterdir()):
        if p.name!='r09_depot_manifest.json': manifest['outputs'][p.name]={'path':str(p.relative_to(ROOT)),'sha256':sha256(p)}
    (out/'r09_depot_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'run_id':a.run_id,'depot':rec},ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
