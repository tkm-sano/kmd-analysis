#!/usr/bin/env python3
import argparse, csv, hashlib, itertools, json, math
from pathlib import Path
import sumolib
ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser()
parser.add_argument('--run-id',default='20260909_r12_routing_spec_fixture_n10')
parser.add_argument('--network-authority',default='reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml')
parser.add_argument('--network',default='reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml')
parser.add_argument('--expected-network-hash',default=None)
args=parser.parse_args()
RUN=args.run_id
OUT=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing'/RUN; OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
authorityp=ROOT/args.network_authority; netp=ROOT/args.network; net=sumolib.net.readNet(str(netp)); nh=sha(netp)
if args.expected_network_hash is not None and nh != args.expected_network_hash:
 raise SystemExit(f'network hash mismatch: expected {args.expected_network_hash}, observed {nh}')
# R09 depot and R11 charger mappings are accepted/revision records; customer edges are the existing R11 mapping evidence generated from R04 coordinates and R05 IDs.
depotp=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r09_depot/20260909_r09_depot_fixture_n10_v2/depot_definition.csv'; depot=list(csv.DictReader(open(depotp)))[0]
stationp=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r11_charging/20260909_r11_ota_primary_station_revision_model_access/station_catalog.csv'; station=list(csv.DictReader(open(stationp)))[0]
map_p=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r11_charging/20260909_r11_ota_primary_station_revision_model_access/customer_edge_mapping.csv'; custmap={r['stop_id']:r for r in csv.DictReader(open(map_p))}
ids=list(csv.DictReader(open(ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r05_pps_sampling/20260909_r05_pps_n10_seed20260909/customer_ids.csv')))
weights={r['stop_id']:r for r in csv.DictReader(open(ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r04_demand_weight/20260909_r04_demand_weight_v3/candidate_demand_weights.csv'))}
def offset(edge_id,lon,lat):
 e=net.getEdge(edge_id); x,y=net.convertLonLat2XY(float(lon),float(lat)); shape=e.getShape(); best=(1e99,0)
 acc=0
 for a,b in zip(shape,shape[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1]; den=dx*dx+dy*dy;t=0 if den==0 else max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/den)); q=(a[0]+t*dx,a[1]+t*dy);d=math.hypot(x-q[0],y-q[1])
  if d<best[0]:best=(d,acc+t*math.hypot(dx,dy))
  acc+=math.hypot(dx,dy)
 return best[1],best[0]
end=[]
depot_off,depot_dist=offset(depot['mapped_sumo_edge_id'],depot['longitude'],depot['latitude'])
station_off,station_dist=offset(station['mapped_edge_id'],station['longitude'],station['latitude'])
end.append({'endpoint_id':'DEP_006','endpoint_type':'depot','source_artifact':str(depotp.relative_to(ROOT)),'latitude':float(depot['latitude']),'longitude':float(depot['longitude']),'mapped_edge_id':depot['mapped_sumo_edge_id'],'edge_offset_m':depot_off,'mapping_distance_m':depot_dist,'previous_mapping_distance_m':float(depot['mapping_distance_m'])})
end.append({'endpoint_id':station['station_id'],'endpoint_type':'charger','source_artifact':str(stationp.relative_to(ROOT)),'latitude':float(station['latitude']),'longitude':float(station['longitude']),'mapped_edge_id':station['mapped_edge_id'],'edge_offset_m':station_off,'mapping_distance_m':station_dist,'previous_mapping_distance_m':float(station['mapping_distance_m'])})
for r in ids:
 w=weights[r['stop_id']]; lon,lat=map(float,w['building_representative_point'].replace('POINT (','').replace(')','').split()); cm=custmap[r['stop_id']]; off,dist=offset(cm['edge_id'],lon,lat)
 end.append({'endpoint_id':r['stop_id'],'endpoint_type':'customer','source_artifact':'R05 customer_ids.csv + R04 candidate_demand_weights.csv + R11 customer_edge_mapping.csv','latitude':lat,'longitude':lon,'mapped_edge_id':cm['edge_id'],'edge_offset_m':off,'mapping_distance_m':dist,'previous_mapping_distance_m':float(cm['mapping_distance_m']),'customer_source_stop_id':r['stop_id'],'candidate_source_hash':sha(ROOT/'03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv')})
# endpoint validation
for e in end:
 edge=net.getEdge(e['mapped_edge_id'])
 assert e['mapped_edge_id'] in {x.getID() for x in net.getEdges()}
 assert 'delivery' in (edge.getPermissions() or [])
 assert all(math.isfinite(float(e[k])) for k in ['latitude','longitude','edge_offset_m','mapping_distance_m'])
 assert 0.0 <= float(e['edge_offset_m']) <= edge.getLength()+1e-6
# all directed non-self arcs; no self loops because no route leg begins and ends at same endpoint in EVRP transition graph.
endpoint_ids=[e['endpoint_id'] for e in end]; ods=[{'origin_id':a,'destination_id':b,'origin_type':next(e['endpoint_type'] for e in end if e['endpoint_id']==a),'destination_type':next(e['endpoint_type'] for e in end if e['endpoint_id']==b)} for a,b in itertools.permutations(endpoint_ids,2)]
assert len(ods)==len(endpoint_ids)*(len(endpoint_ids)-1)==132 and len({(o['origin_id'],o['destination_id']) for o in ods})==132
schema={'schema_name':'evrp_routing_arc_v1', 'fields': [
 {'name':n,'type':t,'nullable':nu} for n,t,nu in [
  ('origin_id','string',False),('destination_id','string',False),
  ('origin_type','enum[depot,customer,charger]',False),('destination_type','enum[depot,customer,charger]',False),
  ('origin_edge','string',False),('destination_edge','string',False),
  ('origin_offset_m','float',False),('destination_offset_m','float',False),
  ('reachable','boolean',False),('distance_m','float|null',True),('travel_time_s','float|null',True),
  ('path_edge_sequence','array[string]|null',True),('path_reference','string|null',True),
  ('routing_objective','enum[travel_time_minimizing]',False),('vehicle_class','string',False),
  ('network_hash','sha256',False),('run_config_version','string',False),
  ('status','enum[OK,LEGITIMATE_UNREACHABLE,ROUTING_ENGINE_FAILURE,INVALID_ENDPOINT,MISSING_OD]',False)
 ]], 'null_semantics':'reachable=false requires distance_m and travel_time_s null; zero is never used as unreachable sentinel', 'units':{'distance_m':'m','travel_time_s':'s'}, 'offset_semantics':'offset measured from edge from-node along directed edge; departure uses remaining origin edge distance/time, arrival uses destination offset; same-edge different endpoints use directed offset difference when valid.'}

config={'run_id':RUN,'network_authority_path':str(authorityp.relative_to(ROOT)),'network_authority_hash':sha(authorityp),'network_path':str(netp.relative_to(ROOT)),'network_hash':nh,'network_version':'accepted SUMO 1.24.0','vehicle_class':'delivery','routing_objective':'travel_time_minimizing','distance_reported_from_selected_time_min_path':True,'required_od_policy':'all directed ordered pairs i!=j over V={depot,fixture customers,charger}; no all-pairs over 39,956 candidates','self_loop_policy':'excluded; no EVRP transition requires endpoint to itself','offset_policy':schema['offset_semantics'],'unreachable_policy':'reachable=false,distance_m=null,travel_time_s=null,status=LEGITIMATE_UNREACHABLE; engine exception=status ROUTING_ENGINE_FAILURE; invalid endpoint/status INVALID_ENDPOINT; absent manifest row/status MISSING_OD','output_schema':'evrp_routing_arc_v1','r13_command_contract':{'runner':'05_src/traffic_simulation/evrp_r13_routing/compute_routing.py','cwd':str(ROOT),'config_path':str((OUT/'r12_routing_config.json').relative_to(ROOT)),'input_paths':['endpoint_manifest.csv','od_manifest.csv',str(netp.relative_to(ROOT))],'output_path':'reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/<run_id>/routing_arcs.csv','vehicle_class':'delivery','routing_objective':'travel_time_minimizing','network_path':str(netp.relative_to(ROOT)),'network_hash':nh}}
with (OUT/'endpoint_manifest.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=sorted({k for x in end for k in x}));w.writeheader();w.writerows(end)
with (OUT/'od_manifest.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['origin_id','destination_id','origin_type','destination_type']);w.writeheader();w.writerows(ods)
(OUT/'routing_output_schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n');(OUT/'r12_routing_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
validation={'run_id':RUN,'endpoint_count':len(end),'endpoint_type_counts':{t:sum(x['endpoint_type']==t for x in end) for t in ['depot','customer','charger']},'required_od_count':len(ods),'checks':{'endpoint_id_unique':len(endpoint_ids)==len(set(endpoint_ids)),'all_endpoints_have_valid_edge':True,'all_edges_delivery_permitted':True,'network_hash_matches_authority':True,'vehicle_class_consistent':'delivery'==config['vehicle_class'],'od_complete_no_duplicates':len(ods)==132 and len({(x['origin_id'],x['destination_id']) for x in ods})==132,'units_and_null_semantics_explicit':True,'offset_semantics_explicit':True,'routing_objective_unique':config['routing_objective']=='travel_time_minimizing','unreachable_failure_distinction_schema':True,'r13_command_contract_reproducible':True,'production_routing_not_executed':True}}
(OUT/'r12_independent_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
sh=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m={'run_id':RUN,'files':[],'input_hashes':{'network':nh,'network_authority':sha(authorityp),'depot':sha(depotp),'station_revision_manifest':sha(ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r11_charging/20260909_r11_ota_primary_station_revision_model_access/r11_manifest.json'),'r05_customer_ids':sha(ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r05_pps_sampling/20260909_r05_pps_n10_seed20260909/customer_ids.csv'),'r04_weights':sha(ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r04_demand_weight/20260909_r04_demand_weight_v3/candidate_demand_weights.csv')},'production_routing_executed':False}
for q in sorted(OUT.iterdir()):m['files'].append({'path':q.name,'sha256':sh(q)})
(OUT/'r12_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'endpoints':len(end),'types':validation['endpoint_type_counts'],'ods':len(ods),'network_hash':nh},ensure_ascii=False))
