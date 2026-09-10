#!/usr/bin/env python3
"""Independent structural/provenance validation for the common EVRP instance."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--instance-dir',required=True); a=ap.parse_args(); d=Path(a.instance_dir); x=json.loads((d/'common_instance.json').read_text()); checks={}
 cs=x['customers']; nodes=x['node_order']; arcs=x['routing']['arcs']; ids=[z['customer_id'] for z in cs]; nodeids=[z['endpoint_id'] for z in nodes]
 checks['fixture_n10']=x['fixture_or_production']['n']==10 and x['fixture_or_production']['is_production_problem_size'] is False
 checks['customer_count_and_unique']=len(cs)==10 and len(ids)==10 and len(set(ids))==10
 checks['customer_fields_complete']=all(z['demand']['q_i']==1 and z['demand']['delivery_request_count']==z['demand']['q_i'] and z['payload']['payload_mass_kg']==z['payload']['m_i']==1.1 and z['payload']['unit']=='kg per delivery request' and z['time_window']['e_i']<=z['time_window']['l_i'] and math.isfinite(z['service_time']['value']) and z['service_time']['value']>=0 for z in cs)
 checks['depot_one']=sum(z['node_type']=='depot' for z in nodes)==1
 checks['vehicle_present']=len(x['vehicles'])>=1 and all(float(v['payload_capacity_kg'])>0 and float(v['battery_capacity_kwh'])>0 for v in x['vehicles'])
 checks['charger_present']=len(x['charging_stations'])>=1 and all(float(s['rated_power_kw'])>0 and float(s['effective_charging_power_kw'])>0 for s in x['charging_stations'])
 checks['node_index_unique']=len(nodeids)==len(set(nodeids)) and [z['solver_index'] for z in nodes]==list(range(len(nodes)))
 checks['endpoint_role_counts']={'depot':sum(z['node_type']=='depot' for z in nodes),'customer':sum(z['node_type']=='customer' for z in nodes),'charger':sum(z['node_type']=='charger' for z in nodes)}
 checks['node_order_consistent']=ids==x['customer_order'] and x['vehicle_order']==[v['vehicle_id'] for v in x['vehicles']]
 checks['routing_od_132']=len(arcs)==132 and len({(z['origin_id'],z['destination_id']) for z in arcs})==132 and all(z['origin_id']!=z['destination_id'] for z in arcs)
 checks['routing_reachable_and_values']=all(z['reachable'] and z['distance_m'] is not None and z['travel_time_s'] is not None and math.isfinite(z['distance_m']) and math.isfinite(z['travel_time_s']) and z['distance_m']>=0 and z['travel_time_s']>=0 for z in arcs)
 checks['routing_authority']=x['routing']['network_hash']=='460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2' and all(z['network_hash']==x['routing']['network_hash'] for z in arcs)
 checks['routing_contract']=x['routing']['vehicle_class']=='delivery' and x['routing']['routing_objective']=='travel_time_minimizing'
 checks['ev_soc']=all(v['initial_soc']>v['minimum_soc'] and abs(v['operational_available_energy_kwh']-32.8)<1e-9 and 0<=v['minimum_soc']<=1<=v['initial_soc'] for v in x['vehicles'])
 checks['charging_contract']=all(s['external_operator_access']=='ASSUMED_AVAILABLE_FOR_MODELING' and float(s['max_session_duration_min'])==30 for s in x['charging_stations'])
 checks['source_hashes']=all(Path(ROOT/r['path']).exists() and sha(ROOT/r['path'])==r['sha256'] for r in x['source_hashes'].values())
 checks['provenance_complete']=all(all(k in r for k in ('path','sha256','classification','unit','transformation','assumption_reason')) for r in x['source_hashes'].values())
 checks['coordinates_and_mapping']=all(math.isfinite(float(z['latitude'])) and math.isfinite(float(z['longitude'])) and z['mapped_edge_id'] for z in nodes)
 result={'status':'PASS' if all(v is True for v in checks.values() if not isinstance(v,dict)) else 'FAIL','checks':checks,'instance_sha256':sha(d/'common_instance.json')}
 (d/'r15_validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(result,ensure_ascii=False)); return 0 if result['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
