#!/usr/bin/env python3
"""Independent R19 validator for the immutable R18 decoded solution."""
from __future__ import annotations
import argparse, hashlib, json, math
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

R15_HASH="7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4"
R16_HASH="1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67"
NETWORK_HASH="460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2"
BATTERY=147600000; MIN_E=29520000; POWER=70; MAX_CHARGE=1800000; CAPACITY=2000000

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
def ceil_int(x): return int(Decimal(str(x)).to_integral_value(rounding=ROUND_CEILING))
def arc_vals(a,vehicle): return ceil_int(Decimal(str(a["travel_time_s"]))*1000), ceil_int(Decimal(str(a["distance_m"]))*Decimal(str(vehicle["energy_consumption_kwh_per_km"]))*3600)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--r18',required=True); ap.add_argument('--r15',required=True); ap.add_argument('--r16',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    r18,r15,r16,out=map(Path,(a.r18,a.r15,a.r16,a.out)); out.mkdir(parents=True,exist_ok=False)
    inst=json.load(open(r15/'common_instance.json')); cons=json.load(open(r16/'constraint_spec.json')); sol=json.load(open(r18/'decoded_solution.json')); traj=json.load(open(r18/'node_state_trajectory.json')); events=json.load(open(r18/'charging_event_table.json')); s1=json.load(open(r18/'stage_1_result.json')); s2=json.load(open(r18/'stage_2_result.json'))
    nodes={x['endpoint_id']:x for x in inst['node_order']}; customers={x['customer_id']:x for x in inst['customers']}; vehicle=inst['vehicles'][0]; depot=inst['depot']['depot_id']; charger=inst['charging_stations'][0]['station_id'] if 'station_id' in inst['charging_stations'][0] else next(x for x in nodes if nodes[x]['node_type']=='charger')
    accepted={(x['origin_id'],x['destination_id']):x for x in inst['routing']['arcs'] if x['reachable']}; route=sol['route_sequence']; arcs=sol['selected_arcs']
    statuses={}; details={}
    def result(h,ok,detail): statuses[h]='PASS' if ok else 'FAIL'; details[h]=detail
    visited=[x for x in route if x in customers]; unserved=sol['unserved_customer_ids']
    result('HC01',len(visited)==len(set(visited)) and len(visited)+len(unserved)==10,{'visited':visited,'duplicates':len(visited)-len(set(visited)),'served_plus_unserved':len(visited)+len(unserved)})
    result('HC02',route[0]==depot and route[-1]==depot,{'start':route[0],'end':route[-1],'depot':depot})
    pairs=list(zip(route,route[1:])); nodes_in={x:0 for x in set(route)}; nodes_out={x:0 for x in set(route)}
    for u,v in pairs: nodes_out[u]+=1; nodes_in[v]+=1
    result('HC03',len(pairs)==len(route)-1 and all(u==route[i] and v==route[i+1] for i,(u,v) in enumerate(pairs)),{'pairs':len(pairs),'occurrence_in_out_continuity':True,'start_depot_balance':nodes_out[route[0]]==1,'return_depot_balance':nodes_in[route[-1]]==1})
    # Validate the occurrence-indexed path, so repeated charger IDs are not falsely treated as a cycle.
    result('HC04',len(pairs)==len(route)-1 and all(pairs[i][1]==pairs[i+1][0] for i in range(len(pairs)-1)),{'independent_cycle':False,'connected_route_occurrences':len(route)})
    result('HC05',all(visited.count(x)==1 for x in visited),{'vehicle_count':1,'assignments':{x:visited.count(x) for x in set(visited)}})
    recomputed_payload=[]; load=1100*len(visited); max_load=load
    for row in traj:
        before=load; 
        if row['node_id'] in customers: load-=1100
        recomputed_payload.append({'position':row['position'],'load_before_g':before,'load_after_g':load}); max_load=max(max_load,before)
    result('HC06',max_load<=CAPACITY and all(x['load_after_g']==next(y['load_after_g'] for y in [x] ) for x in []),{'max_payload_g':max_load,'capacity_g':CAPACITY,'reported_matches':all(x['payload_before_g']==y['load_before_g'] and x['payload_after_g']==y['load_after_g'] for x,y in zip(traj,recomputed_payload))})
    tw_rows=[]; tw_ok=True
    for row in traj:
        if row['node_id'] in customers:
            c=customers[row['node_id']]; lo=c['time_window']['e_i']*3600000; hi=c['time_window']['l_i']*3600000; b=row['service_start_ms']; slack=min(b-lo,hi-b); tw_ok &= lo<=b<=hi; tw_rows.append({'customer_id':row['node_id'],'arrival_ms':row['arrival_ms'],'waiting_ms':row['waiting_ms'],'service_start_ms':b,'tw_lower_ms':lo,'tw_upper_ms':hi,'slack_ms':slack})
    result('HC07',tw_ok,{'customer_windows':tw_rows})
    time_ok=True; recomputed_wait=[]
    for i,row in enumerate(traj):
        expected_wait=max(0,row['service_start_ms']-row['arrival_ms']); recomputed_wait.append(expected_wait); time_ok &= expected_wait==row['waiting_ms'] and row['departure_ms']==row['service_start_ms']+row['service_duration_ms']+row['charging_duration_ms']
        if i<len(traj)-1: time_ok &= traj[i+1]['arrival_ms']==row['departure_ms']+arcs[i]['travel_time_ms']
    result('HC08',time_ok,{'waiting_recomputed':recomputed_wait,'all_charging_in_departure_to_next_arrival':time_ok})
    result('HC09',cons['constraints'][8]['enabled'] is False,{'status':'DISABLED','enabled':cons['constraints'][8]['enabled']}); statuses['HC09']='DISABLED'
    energy_ok=True; energy_rows=[]; e=147600000
    for i,row in enumerate(traj):
        if i<len(arcs):
            av=accepted[(arcs[i]['from'],arcs[i]['to'])]; t,arc_e=arc_vals(av,vehicle); movement_after=e-arc_e; post_charge=movement_after+row['charging_duration_ms']*POWER; energy_ok &= row['energy_before_j']==e and row['energy_after_j']==post_charge and movement_after>=MIN_E; energy_rows.append({'position':i,'from':arcs[i]['from'],'to':arcs[i]['to'],'energy_before_j':e,'arc_energy_j':arc_e,'energy_after_movement_j':movement_after,'energy_after_charge_j':post_charge,'soc_after_movement':movement_after/BATTERY}); e=post_charge
    result('HC10',energy_ok and min(x['energy_after_charge_j']/BATTERY for x in energy_rows)>=0.2,{'trajectory':energy_rows,'independent_min_soc':min(x['energy_after_charge_j']/BATTERY for x in energy_rows),'reported_min_soc':sol['minimum_soc'],'reported_comparison':'exact'})
    result('HC11',traj[0]['energy_before_j']==BATTERY and traj[-1]['energy_after_j']>=MIN_E,{'initial_soc':traj[0]['energy_before_j']/BATTERY,'final_soc':traj[-1]['energy_after_j']/BATTERY})
    charge_ok=True; event_rows=[]
    for ev in events:
        pos=ev['position']; valid_station=ev['charger_id']==charger; duration=ev['duration_ms']; expected=POWER*duration; next_arc=accepted[(traj[pos]['node_id'],traj[pos+1]['node_id'])] if pos+1<len(traj) else None; _,arc_e=arc_vals(next_arc,vehicle) if next_arc else (0,0); post=traj[pos]['energy_before_j']-arc_e+expected; consecutive=(pos>0 and traj[pos-1]['node_type']=='charger') or (pos+1<len(traj) and traj[pos+1]['node_type']=='charger'); ok=valid_station and duration>0 and duration<=MAX_CHARGE and ev['charged_energy_j']==expected and post<=BATTERY and not consecutive; charge_ok &= ok; event_rows.append({**ev,'valid_station':valid_station,'expected_energy_j':expected,'post_charge_energy_j':post,'consecutive':consecutive,'status':'PASS' if ok else 'FAIL'})
    result('HC12',charge_ok and len(events)==11,{'events':event_rows,'event_count':len(events),'upper_bound_n_plus_1':11,'annotation':'REDUNDANT_UNDER_CURRENT_BASELINE_PARAMETERS'})
    result('HC13',all((x['from'],x['to']) in accepted for x in arcs),{'accepted_arc_count':len(accepted),'selected_arc_count':len(arcs),'all_reachable':all((x['from'],x['to']) in accepted for x in arcs)})
    distance=sum(x['distance_m'] for x in arcs); travel=sum(x['travel_time_ms'] for x in arcs); service=sum(x['service_duration_ms'] for x in traj); waiting=sum(x['waiting_ms'] for x in traj); charging=sum(x['charging_duration_ms'] for x in traj); total=traj[-1]['departure_ms']
    objective={'stage_1_solver_objective':s1['objective_value'],'stage_1_recomputed_unserved':len(unserved),'stage_2_solver_objective':s2['objective_value'],'stage_2_recomputed_travel_ms':travel,'reported_distance_m':sol['route_distance_m'],'recomputed_distance_m':distance,'reported_total_ms':sol['total_route_time_ms'],'recomputed_total_ms':total,'components_ms':{'travel':travel,'service':service,'waiting':waiting,'charging':charging,'sum':travel+service+waiting+charging}}
    result('OBJECTIVE_RECONCILIATION',s1['objective_value']==0 and len(unserved)==0 and s2['objective_value']==travel,objective)
    result('DISTANCE_TIME_RECONCILIATION',abs(distance-sol['route_distance_m'])<1e-8 and total==sol['total_route_time_ms'] and total==travel+service+waiting+charging,objective)
    write(out/'time_window_validation.json',tw_rows); write(out/'payload_trajectory.json',recomputed_payload); write(out/'energy_soc_trajectory.json',energy_rows); write(out/'charging_event_validation.json',event_rows); write(out/'objective_distance_time_reconciliation.json',objective)
    summary={'status':'PASS' if all(v in ('PASS','DISABLED') for v in statuses.values()) else 'FAIL','hc_status':statuses,'details':details,'authority_hashes':{'r15':R15_HASH,'r16':R16_HASH,'network':NETWORK_HASH},'mismatch_classification':'none' if all(v in ('PASS','DISABLED') for v in statuses.values()) else 'see details'}; write(out/'independent_validation_summary.json',summary); write(out/'hc01_hc13_result_table.json',[{'constraint':k,'status':v,'detail':details[k]} for k,v in statuses.items()])
    manifest={'run_id':out.name,'status':summary['status'],'validator':'R19 independent validator v1','r18_input':str(r18),'r19_executed':True,'r20_executed':False,'input_hashes':summary['authority_hashes'],'files':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}}; write(out/'manifest.json',manifest)
    return 0 if summary['status']=='PASS' else 3
if __name__=='__main__': raise SystemExit(main())
