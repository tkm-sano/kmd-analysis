#!/usr/bin/env python3
import csv, hashlib, json, math, subprocess, urllib.request, xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
import sumolib
ROOT=Path(__file__).resolve().parents[3]
RUN_ID='20260909_r11_ota_primary_station'
OUT=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r11_charging'/RUN_ID
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'EVRP-R11-Ota-primary-station-audit/1.0'})
 with urllib.request.urlopen(req,timeout=30) as r:return r.read()
# Address is from JMT official source; coordinate is explicitly computed from that address.
coord_url='https://www.geocoding.jp/api/?q=%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%A4%A7%E7%94%B0%E5%8C%BA%E5%B9%B3%E5%92%8C%E5%B3%B62-1-1'
coord_xml=fetch(coord_url); root=ET.fromstring(coord_xml); lat=float(root.findtext('./coordinate/lat')); lon=float(root.findtext('./coordinate/lng'))
jmt='https://www.j-m-t.co.jp/terminal/keihin.html'; jmt_release='https://www.j-m-t.co.jp/news/item/news20251201.pdf'; emp='https://www.evcharger.e-mobipower.co.jp/ia-eweb/em/charger_spot_list/?charger__nw_provider=NWPEP&page=24&sort=chg_station__city__city_code%2Cchg_station_id%2Cgrouping_charger_id%2Ccharger_id'
# Station details are primary-source fields; max session duration is unknown and retained null.
station={'station_id':'OTA_KEIHIN_TRUCK_TERMINAL_A','station_name':'京浜トラックターミナル 急速A-1/A-2','address':'東京都大田区平和島2-1-1','latitude':lat,'longitude':lon,'operator':'株式会社e-Mobility Power / 日本自動車ターミナル株式会社','source_urls':[jmt,jmt_release,emp],'retrieval_date':str(date.today()),'operational_status':'OPERATIONAL / 24 hours','public_access':'e-Mobility Power network; JMT states use by terminal tenants, related parties and employees; general unrestricted public access is not explicitly stated','connector_type':'CHAdeMO','rated_power_kw':90,'ports':2,'usage_hours':'24 hours','max_session_duration_min':None,'source_classification':'PRIMARY_SOURCE_COMBINED','coordinate_classification':'COMPUTED_FROM_OFFICIAL_ADDRESS','coordinate_source_url':coord_url,'coordinate_source_hash':sha(coord_xml),'mapped_edge_id':None,'edge_offset_m':None,'mapping_distance_m':None,'network_hash':None,'delivery_class_access':None,'depot_reachability':None,'fixture_customer_reachability':None,'ecanters_compatibility':'CHAdeMO compatible; R10 F5 DC max 70 kW','adopted':False,'limitation':'Public access wording is facility-user scoped rather than explicit unrestricted public access; max session duration is not specified in the primary sources.'}
netp=ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml'; net=sumolib.net.readNet(str(netp)); station['network_hash']=sha(netp.read_bytes())
x,y=net.convertLonLat2XY(lon,lat); near=[(d,e) for e,d in net.getNeighboringEdges(x,y,500,includeJunctions=False) if 'delivery' in (e.getPermissions() or [])]; d,e=min(near,key=lambda z:z[0]); station['mapped_edge_id']=e.getID(); station['mapping_distance_m']=d
# linear edge offset for deterministic record
(a,b)= (e.getFromNode().getCoord(),e.getToNode().getCoord());dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)));station['edge_offset_m']=t*e.getLength();station['delivery_class_access']=True
# map fixture customers and route all depot/station and customer/station directions
weights=list(csv.DictReader(open(ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r04_demand_weight/20260909_r04_demand_weight_v3/candidate_demand_weights.csv'))); by={r['stop_id']:r for r in weights}; ids=list(csv.DictReader(open(ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r05_pps_sampling/20260909_r05_pps_n10_seed20260909/customer_ids.csv')))
def map_edge(wkt):
 lo,la=map(float,wkt.replace('POINT (','').replace(')','').split()); xx,yy=net.convertLonLat2XY(lo,la); q=[(dd,ee) for ee,dd in net.getNeighboringEdges(xx,yy,500,includeJunctions=False) if 'delivery' in (ee.getPermissions() or [])]; return min(q,key=lambda z:z[0])
customer_edges=[]
for r in ids:
 d0,e0=map_edge(by[r['stop_id']]['building_representative_point']); customer_edges.append({'stop_id':r['stop_id'],'edge_id':e0.getID(),'mapping_distance_m':d0})
station_edge=station['mapped_edge_id']; depot_edge='617631294'; pairs=[('DEPOT',depot_edge,'STATION',station_edge),('STATION',station_edge,'DEPOT',depot_edge)]
for c in customer_edges:pairs += [(c['stop_id'],c['edge_id'],'STATION',station_edge),('STATION',station_edge,c['stop_id'],c['edge_id'])]
trips=OUT/'route_check_trips.xml'; routes=OUT/'route_check_routes.xml'
with trips.open('w') as f:
 f.write('<routes><vType id="delivery" vClass="delivery"/><trips>')
 for i,(_,a,_,b) in enumerate(pairs):f.write(f'<trip id="r11_{i}" type="delivery" depart="0" from="{a}" to="{b}"/>')
 f.write('</trips></routes>')
cmd=[str(ROOT/'.local/sumo-1.24.0/bin/duarouter'),'--net-file',str(netp),'--route-files',str(trips),'--output-file',str(routes),'--ignore-errors','--no-warnings']; pr=subprocess.run(cmd,capture_output=True,text=True,timeout=120); (OUT/'duarouter.stderr').write_text(pr.stderr)
rt=ET.parse(routes).getroot(); found={v.attrib['id'] for v in rt.findall('vehicle')}; station['depot_reachability']=len(found)>=2 and {'r11_0','r11_1'}<=found; station['fixture_customer_reachability']=all(f'r11_{i}' in found for i in range(2,len(pairs)))
with (OUT/'station_catalog.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=station.keys());w.writeheader();w.writerow(station)
(OUT/'customer_edge_mapping.csv').write_text('stop_id,edge_id,mapping_distance_m\n'+'\n'.join(f"{x['stop_id']},{x['edge_id']},{x['mapping_distance_m']}" for x in customer_edges)+'\n')
summary={'run_id':RUN_ID,'candidate_count':1,'primary_source_confirmed_count':1,'network_inside_count':1,'adopted_count':0,'official_candidate':station,'route_pair_count':len(pairs),'route_success_count':len(found),'route_success_all':len(found)==len(pairs),'route_command':cmd,'route_stderr_hash':sha(pr.stderr.encode()),'adoption_rule':'requires explicit public/general access wording; candidate is retained but not adopted because JMT wording is facility-user scoped and max session is unknown'}
(OUT/'r11_independent_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
config={'run_id':RUN_ID,'network_path':str(netp.relative_to(ROOT)),'network_hash':station['network_hash'],'vehicle_record_id':'F5-YAMATO-ECANTER-2023','vehicle_connector':'CHAdeMO','vehicle_dc_max_kw':70,'route_vehicle_class':'delivery','customer_fixture_n':10,'public_access_policy':'unknown or facility-limited access is not adopted as unrestricted public access','network_expansion':False}
(OUT/'r11_charging_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
files=[]
for p in sorted(OUT.iterdir()):
 if p.name!='r11_manifest.json':files.append({'path':p.name,'sha256':sha(p.read_bytes())})
manifest={'run_id':RUN_ID,'files':files,'sources':[{'url':u,'sha256':sha(fetch(u)),'retrieval_date':str(date.today())} for u in [jmt,jmt_release,emp]],'coordinate_source':{'url':coord_url,'sha256':sha(coord_xml),'retrieval_date':str(date.today())}}
(OUT/'r11_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'station':station['station_name'],'lat':lat,'lon':lon,'edge':e.getID(),'mapping_distance_m':d,'routes':len(found),'pairs':len(pairs),'adopted':0},ensure_ascii=False))
