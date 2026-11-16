"""Post-experiment raw-dictionary audit; no route builder or solver validation.

This audit is outside each method's already measured common-validation T.
"""
from collections import Counter,defaultdict
from decimal import Decimal
import csv
import hashlib
import itertools
import json
import os
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from kmd_toc.common.models import load_problem

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112'))

def table(path,rows):
    if not rows:return
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)

def raw_audit(p,r):
    errors=[];q=r['plan'];seen=[];by=defaultdict(list);events=[];d=Decimal(0);w=0;idx={s:i for i,s in enumerate(p.od.ids)}
    checks=0
    def require(ok,code):
        nonlocal checks
        checks+=1
        if not ok:errors.append(code)
    require(q['problem_hash']==p.fingerprint and q['od_hash']==p.od.fingerprint,'input_identity')
    for t in q['trips']:by[t['vehicle_id']].append(t)
    require(set(by)<=set(v.vehicle_id for v in p.vehicles),'physical_vehicle_ids')
    for vi,v in enumerate(p.vehicles):
        trips=sorted(by[v.vehicle_id],key=lambda t:t['trip_no']);require(len(trips)<=2,'max_two');ready=28800+3600*(2*vi+1)//(2*len(p.vehicles))
        for k,t in enumerate(trips,1):
            require(t['trip_no']==k and t['origin_id']==p.depot.depot_id and t['destination_id']==p.depot.depot_id,'depot_trip_sequence')
            require(t['ready_s']==ready and t['load_start_s']>=ready,'exogenous_ready_and_connection')
            require(t['load_end_s']-t['load_start_s']==1800 and t['departure_s']==t['load_end_s'],'loading')
            require(t['berth_id'] in [b.berth_id for b in p.berths],'berth_id')
            require(28800<=t['load_start_s'] and t['return_s']<=72000,'shift')
            events.extend([(t['load_start_s'],1,t['berth_id']),(t['load_end_s'],-1,t['berth_id'])]);w+=t['load_start_s']-ready
            clock=t['departure_s'];node=0;trip_d=Decimal(0);load=0
            for s in t['visits']:
                j=idx[s['stop_id']];seen.append(s['stop_id']);load+=p.stops[j-1].demand
                clock+=math.ceil(float(p.od.duration_s[node,j]));trip_d+=Decimal(str(p.od.distance_m[node,j]))
                require(s['arrival_s']==clock and s['service_start_s']==s['arrival_s'] and s['service_end_s']-s['service_start_s']==120,'travel_service')
                clock=s['service_end_s'];node=j
            clock+=math.ceil(float(p.od.duration_s[node,0]));trip_d+=Decimal(str(p.od.distance_m[node,0]));require(t['return_s']==clock,'return_travel')
            require(load<=60,'capacity');require(abs(float(trip_d)-t['distance_m'])<1e-6,'trip_distance');require(t['waiting_s']==t['load_start_s']-ready,'trip_wait')
            d+=trip_d;ready=t['return_s']
    require(Counter(seen)==Counter({s.stop_id:1 for s in p.stops}),'coverage')
    active=0;berths=Counter()
    for time,delta,b in sorted(events):
        active+=delta;berths[b]+=delta;require(0<=active<=len(p.berths) and 0<=berths[b]<=1,'berth_exclusion')
    D=float(d/1000);W=w/60
    require(abs(D-r['D_km'])<1e-7 and abs(W-r['W_min'])<1e-7,'D_W_recalculation')
    ev=r['timing_events'];require(ev[0]['name']=='input_load_start' and ev[0]['elapsed_s']==0 and ev[-1]['name']=='independent_validation_end','T_boundaries')
    require(all(a['elapsed_s']<=b['elapsed_s'] for a,b in zip(ev,ev[1:])) and r['T_program_s']==ev[-1]['elapsed_s'],'T_elapsed')
    if r.get('other_limit') is not None:require((W if r['primary']=='D' else D)<=r['other_limit']+1e-6,'epsilon')
    return {'passed':not errors,'errors':sorted(set(errors)),'D_km':D,'W_min':W,'checks':checks}

def small_exact(p):
    n=len(p.stops);full=(1<<n)-1;best={};orders={}
    for k in range(1,n+1):
        for order in itertools.permutations(range(1,n+1),k):
            mask=sum(1<<(i-1) for i in order);nodes=(0,*order,0);cost=sum(Decimal(str(p.od.distance_m[a,b])) for a,b in zip(nodes,nodes[1:]))
            if mask not in best or cost<best[mask]:best[mask]=cost;orders[mask]=order
    dp={(0,0):(Decimal(0),())}
    for k in range(2*len(p.vehicles)):
        for mask in range(full+1):
            if (mask,k) not in dp:continue
            left=full^mask;subset=left
            while subset:
                old,path=dp[mask,k];value=old+best[subset];key=(mask|subset,k+1)
                if key not in dp or value<dp[key][0]:dp[key]=(value,path+(orders[subset],))
                subset=(subset-1)&left
    value,routes=min((dp[full,k] for k in range(1,2*len(p.vehicles)+1) if (full,k) in dp),key=lambda x:x[0])
    # Construct a distinct greedy physical schedule and verify return/bays.
    from kmd_toc.pipeline.completion import greedy_assignment,assemble
    candidate=assemble(p,greedy_assignment(p,routes),'B',{'independent_exact_distance_reference':True})
    from kmd_toc.common.validation import validate_plan
    report=validate_plan(p,candidate)
    return {'D_lower_bound_km':float(value/1000),'bound_attained_by_feasible_plan':report.feasible and abs(report.D_km-float(value/1000))<1e-8,'routes':routes,'plan_D_km':report.D_km,'plan_W_min':report.W_min,'states':len(dp),'scope':'all route permutations and <=2V trips; exact distance only when independent lower bound is attained by feasible schedule'}

def main():
    rows=[];audits=[];problems={};human=[]
    for path in sorted((ROOT/'experiments').glob('*/*/result.json')):
        r=json.loads(path.read_text());case=path.parents[1].name;condition=path.parent.name
        row={k:r.get(k) for k in ['method','status','primary','other_limit','D_km','W_min','T_program_s','elapsed_wall_s','max_rss_KiB','input_hash','OD_hash']};row.update(scenario=case,condition=condition,source=str(path),T_kind='program_measured_wall',human_measured=False,is_replicate='repeat' in condition)
        # Rejected plans retain their input identity inside the saved plan.
        # Expose that evidence in the summary without modifying raw results.
        saved_plan=r.get('plan') or {}
        row['input_hash_source']='result' if row['input_hash'] else 'saved_plan'
        row['input_hash']=row['input_hash'] or saved_plan.get('problem_hash')
        row['OD_hash']=row['OD_hash'] or saved_plan.get('od_hash')
        if r['status']=='FEASIBLE':
            if case not in problems:problems[case]=load_problem(ROOT/'roads/inputs'/case)
            a=raw_audit(problems[case],r);audits.append({'source':str(path),**a});row['third_audit_pass']=a['passed']
            e=r['timing_events'];row['input_s']=next(x['elapsed_s'] for x in e if x['name']=='input_load_end');row['validation_s']=e[-1]['elapsed_s']-next(x['elapsed_s'] for x in e if x['name']=='independent_validation_start');row['construction_optimization_post_s']=r['T_program_s']-row['input_s']-row['validation_s']
            for h in r.get('human_time_sensitivity',[]):human.append({'scenario':case,'condition':condition,**{k:h[k] for k in ['profile','staff_rule','workers','N','used_vehicles','workflow_elapsed_s','person_seconds','measured_io_validation_s','T_human_estimate_s','human_measured','kind']}})
        else:row['failure']=json.dumps(r.get('error') or r.get('reason') or r.get('validation'),ensure_ascii=False)
        rows.append(row)
    table(ROOT/'A_TO_D_COMPARISON.csv',rows);table(ROOT/'A_HUMAN_TIME_SENSITIVITY.csv',human)
    ranges=[]
    for case in sorted({r['scenario'] for r in rows}):
        for method in ['A1','A2','A3','A_ALL','B','C','D']:
            allrows=[r for r in rows if r['scenario']==case and not r['is_replicate'] and (r['method'].startswith('A') if method=='A_ALL' else r['method']==method)];good=[r for r in allrows if r['status']=='FEASIBLE']
            if not allrows:continue
            row={'scenario':case,'method':method,'attempts':len(allrows),'feasible':len(good),'feasible_rate':len(good)/len(allrows)}
            for key in ['D_km','W_min','T_program_s']:
                values=[r[key] for r in good];row.update({key+'_min':min(values) if values else None,key+'_median':statistics.median(values) if values else None,key+'_max':max(values) if values else None})
            ranges.append(row)
    table(ROOT/'OBSERVED_RANGES.csv',ranges)
    result={'plans_audited':len(audits),'all_passed':all(a['passed'] for a in audits),'checks':sum(a['checks'] for a in audits),'audits':audits}
    (ROOT/'INDEPENDENT_RAW_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    if 'ROAD_N6' in problems:(ROOT/'ROAD_N6_EXACT_REFERENCE.json').write_text(json.dumps(small_exact(problems['ROAD_N6']),indent=2)+'\n')
    print('audited',len(audits),'all_passed',result['all_passed'],flush=True)

if __name__=='__main__':main()
