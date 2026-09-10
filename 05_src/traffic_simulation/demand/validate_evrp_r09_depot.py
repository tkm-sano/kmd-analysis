#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
import sumolib
ROOT=Path(__file__).resolve().parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();o=a.output.resolve();m=json.loads((o/'r09_depot_manifest.json').read_text());d=read(o/'depot_definition.csv');assert len(d)==1
    r=d[0]; lon,lat=float(r['longitude']),float(r['latitude']); assert all(math.isfinite(x) for x in (lon,lat)) and -180<=lon<=180 and -90<=lat<=90
    assert r['classification']=='PROXY' and r['proxy_or_observed']=='proxy' and r['vehicle_class']=='delivery'; assert math.isfinite(float(r['mapping_distance_m'])) and float(r['mapping_distance_m'])>=0
    net=sumolib.net.readNet(str(ROOT/m['inputs']['network']['path']),withInternal=False); edge=net.getEdge(r['mapped_sumo_edge_id']); assert edge.getID()==r['mapped_sumo_edge_id']; assert 'delivery' in edge.getLane(0).getPermissions(); assert 0<=float(r['edge_offset_m'])<=float(r['edge_length_m']); assert edge.getFromNode() and edge.getToNode()
    for rec in m['inputs'].values(): assert sha(ROOT/rec['path'])==rec['sha256']
    result={'selected_depot_id':r['depot_id'],'mapped_edge':r['mapped_sumo_edge_id'],'mapping_distance_m':float(r['mapping_distance_m']),'coordinates_valid':True,'accepted_edge_exists':True,'delivery_access':True,'departure_return_nodes_present':True,'input_hash_validation':'PASS'}
    (o/'r09_independent_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
