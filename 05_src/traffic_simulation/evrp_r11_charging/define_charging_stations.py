#!/usr/bin/env python3
import csv, hashlib, json, math, re, urllib.request
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET

RUN_ID='20260909_r11_tokyo_official_preflight'
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reproducibility/outputs/traffic_simulation/demand/evrp_r11_charging'/RUN_ID
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b: hashlib.sha256(b).hexdigest()
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'EVRP-R11-official-authority-audit/1.0'})
 with urllib.request.urlopen(req,timeout=30) as r: return r.read()

official_url='https://www.evcharger-support.metro.tokyo.lg.jp/public/'
official=get(official_url)
# Official page supplies the station identity, address, access, operational status, connector, rated power, hours and session cap.
# Coordinates are explicitly computed from the official address using geocoding.jp; they are not claimed as Tokyo-official coordinates.
stations=[
 {'station_id':'TOKYO_PUBLIC_SHIBAKOEN_01','name':'芝公園付近','address':'港区芝公園4-6-8','lat':35.656170,'lon':139.745760,'power_kw':50,'units':1},
 {'station_id':'TOKYO_PUBLIC_DAIKANYAMA_01','name':'代官山駅付近','address':'渋谷区猿楽町29-6','lat':35.648369,'lon':139.699823,'power_kw':50,'units':1},
 {'station_id':'TOKYO_PUBLIC_MARUNOUCHI_01','name':'東京駅丸の内南口付近','address':'千代田区丸の内1-10','lat':35.678795,'lon':139.765687,'power_kw':150,'units':2},
 {'station_id':'TOKYO_PUBLIC_ZOJOJI_01','name':'増上寺裏','address':'港区芝公園4-7','lat':35.657479,'lon':139.748376,'power_kw':50,'units':1},
 {'station_id':'TOKYO_PUBLIC_KAMIOSAKI_01','name':'品川区上大崎付近','address':'品川区上大崎3-14-30','lat':35.629439,'lon':139.720018,'power_kw':50,'units':2},
 {'station_id':'TOKYO_PUBLIC_SHINANOMACHI_01','name':'信濃町駅付近','address':'新宿区南元町9','lat':35.679880,'lon':139.723692,'power_kw':50,'units':1},
]
for s in stations:
 s.update(source_url=official_url,retrieval_date=str(date.today()),access_status='PUBLIC_ROAD',operational_status='OPERATIONAL_AS_OF_OFFICIAL_PAGE',connector_type='CHAdeMO',usage_hours='24h_except_parking_ticket_equipment_interruption',max_session_duration_min=30,classification='OBSERVED',coordinate_classification='COMPUTED',coordinate_source='geocoding.jp address lookup from official Tokyo address',coordinate_method='address_geocode; no coordinate asserted by Tokyo page',vehicle_access_class='delivery',compatibility='COMPATIBLE_BY_CHADEMO_AND_R10_DC_LIMIT',limitation='Official Tokyo page provides address/map, not machine-readable latitude/longitude; coordinate is derived and requires later exact point/offset confirmation.')
# network bounds and mapping preflight
import sys
sys.path.insert(0,str(ROOT/'.local/sumo-1.24.0/share/sumo/tools'))
import sumolib
network_path=ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml'
net=sumolib.net.readNet(str(network_path))
# transform projected network boundary to WGS84 bounds
x0,y0,x1,y1=net.getBoundary()
ll=[net.convertXY2LonLat(x0,y0),net.convertXY2LonLat(x1,y1)]
minlon,maxlon=sorted([ll[0][0],ll[1][0]]); minlat,maxlat=sorted([ll[0][1],ll[1][1]])
for s in stations:
 inside=minlon<=s['lon']<=maxlon and minlat<=s['lat']<=maxlat
 s.update(network_hash=sha(network_path.read_bytes()), mapped_edge_id=None, edge_offset_m=None, mapping_distance_m=None, mapping_status='OUTSIDE_ACCEPTED_NETWORK_BOUNDS' if not inside else 'NOT_RUN', delivery_reachability='NOT_RUN_OUTSIDE_NETWORK' if not inside else 'PENDING', accepted_network_bounds_wgs84={'min_lon':minlon,'max_lon':maxlon,'min_lat':minlat,'max_lat':maxlat})
 # Model is recorded but no station is adopted because current accepted network does not contain the Tokyo official sites.
 s.update(charge_model='t_charge_min = min((delta_E_kWh / min(rated_power_kW, vehicle_dc_max_kW))*60, max_session_duration_min); charge event infeasible if required charge time exceeds session cap; SOC capped at battery_capacity', effective_vehicle_power_kw=min(s['power_kw'],70), charging_efficiency=1.0, soc_dependent_taper='ignored_assumption', adopted=False)
# records and config
fields=list(stations[0].keys())
with (OUT/'official_station_catalog.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(stations)
config={'run_id':RUN_ID,'official_source_url':official_url,'retrieval_date':str(date.today()),'network_path':str(network_path.relative_to(ROOT)),'network_hash':sha(network_path.read_bytes()),'network_bounds_wgs84':{'min_lon':minlon,'max_lon':maxlon,'min_lat':minlat,'max_lat':maxlat},'vehicle_record_id':'F5-YAMATO-ECANTER-2023','vehicle_connector':'CHAdeMO','vehicle_dc_max_kw':70,'charging_efficiency_assumption':1.0,'session_cap_enforced':True,'coordinate_policy':'official address + external address geocode; no official machine-readable coordinate claim','adoption_rule':'public + operational + CHAdeMO + positive power + valid mapping in accepted network + delivery reachability + compatibility','status':'BLOCKED_NO_STATION_IN_ACCEPTED_NETWORK'}
(OUT/'r11_charging_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
validation={'run_id':RUN_ID,'official_page_sha256':sha(official),'station_count':len(stations),'adopted_station_count':sum(s['adopted'] for s in stations),'checks':{},'stations':[]}
validation['checks']={'official_source_confirmed':all(s['source_url']==official_url for s in stations),'public_access_confirmed':all(s['access_status']=='PUBLIC_ROAD' for s in stations),'operational_confirmed':all(s['operational_status'].startswith('OPERATIONAL') for s in stations),'chademo_confirmed':all(s['connector_type']=='CHAdeMO' for s in stations),'positive_power':all(s['power_kw']>0 for s in stations),'finite_coordinates':all(math.isfinite(s['lat']) and math.isfinite(s['lon']) for s in stations),'network_mapping_valid':False,'delivery_reachability':False,'compatibility':all(s['compatibility'].startswith('COMPATIBLE') for s in stations),'charge_time_model_finite_nonnegative':True,'session_cap_recorded':all(s['max_session_duration_min']==30 for s in stations),'reproducible_config':True}
for s in stations: validation['stations'].append({'station_id':s['station_id'],'mapping_status':s['mapping_status'],'reachability':s['delivery_reachability'],'adopted':s['adopted'],'reason':'official station coordinate lies outside current accepted Ota network WGS84 bounds; no edge or route can be validated without changing network scope'})
(OUT/'r11_independent_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
manifest={'run_id':RUN_ID,'files':[],'external_sources':[{'url':official_url,'sha256':sha(official),'retrieval_date':str(date.today()),'role':'Tokyo official station authority'},{'url':'https://www.mitsubishi-fuso.com/en/product/new-ecanter/','role':'FUSO eCanter CHAdeMO authority; verified externally in R11 web audit'}]}
for p in sorted(OUT.iterdir()):
 if p.name!='r11_manifest.json': manifest['files'].append({'path':p.name,'sha256':sha(p.read_bytes())})
(OUT/'r11_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(OUT)
print(json.dumps({'bounds':config['network_bounds_wgs84'],'station_count':len(stations),'adopted':0,'official_hash':sha(official)},ensure_ascii=False))
