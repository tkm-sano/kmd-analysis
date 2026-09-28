"""Decimal saved-result audit. No implementation, enumeration, or solver imports."""
from decimal import Decimal,localcontext
from collections import Counter
from itertools import permutations,product

D=Decimal
ET=D('1e-9');TT=D('1e-7')


def validate(instance,od,pre,plans,saved,enabled,*,floating=False):
    errors=[];computed=[];et=ET if floating else D(0);tt=TT if floating else D(0)
    def check(ok,msg):
        if not ok:errors.append(msg)
    def eq(actual,expected,tol,msg):
        check(abs(D(str(actual))-expected)<=tol,msg)
    with localcontext() as context:
        context.prec=80
        depot=instance['depot']['depot_id'];charger=pre['route'][1]
        customers={c['customer_id']:c for c in instance['customers']};vehicles={v['vehicle_id']:v for v in instance['vehicles']}
        initial=D(pre['provisional_initial_battery_kwh']);opening=D(str(instance['depot']['opening_time']));closing=D(str(instance['depot']['closing_time']))
        visit=Counter();totaltravel=totalcharge=D(0)
        check(len(plans)==len(vehicles) and {p['vehicle_id'] for p in plans}==set(vehicles),'vehicle identities')
        for p,claimed in zip(plans,saved['routes']):
            vid=p['vehicle_id'];nodes=p['nodes'];check(claimed['vehicle_id']==vid and claimed['nodes']==nodes,'route identity')
            if not nodes:
                check(claimed['used'] is False and claimed['feasible'] is None,'unused NOT_EVALUABLE');continue
            check(nodes[0]==nodes[-1]==depot and depot not in nodes[1:-1],'depot structure')
            served=[x for x in nodes[1:-1] if x!=charger];visit.update(served)
            check(len(served)>0 and len(served)==len(set(served)),'customer repetition/empty delivery')
            check(all(i!=j for i,j in zip(nodes,nodes[1:])),'consecutive same node')
            check(set(p['charges'])<={str(i) for i,x in enumerate(nodes) if x==charger},'charging location')
            load=sum((D(str(customers[c]['demand'])) for c in served),D(0));cap=load<=D(str(vehicles[vid]['capacity']))
            b=initial;clock=opening;road=dist=energy=charge=duration=D(0);minimum=b;bok=2-et<=b<=20+et;tok=True
            check(len(claimed['events'])==len(nodes)-1 and len(claimed['arcs'])==len(nodes)-1,'event length')
            for pos,(i,j) in enumerate(zip(nodes,nodes[1:]),1):
                edge=od[i+'|'+j];check(edge['reachable'] and edge['validation_status']=='PASS','directed reachability')
                km=D(str(edge['distance_m']))/1000;tau=D(str(edge['travel_time_s']));e=D('0.127')*km
                before=b;b-=e;arrb=b;minimum=min(minimum,b);arrival=clock+tau
                q=D(str(p['charges'].get(str(pos),0)));tc=q*D(360) # independent fixed10kW seconds conversion
                if not enabled:check(q==0,'disabled charging')
                if j in customers:
                    c=customers[j];start=max(arrival,D(str(c['earliest_service_time'])));service=D(str(c['service_duration']));node_t=start<=D(str(c['latest_service_time']))+tt
                else:start=arrival;service=D(0);node_t=True
                clock=start+service+tc;b+=q
                node_b=(2-et<=arrb<=20+et and -et<=q<=20-arrb+et and 2-et<=b<=20+et)
                node_t=node_t and clock<=closing+tt;bok &= node_b;tok &= node_t
                energy+=e;charge+=q;duration+=tc;road+=tau;dist+=km
                ev=claimed['events'][pos-1];ar=claimed['arcs'][pos-1]
                check(ev['node']==j and ev['position']==pos and ar['origin']==i and ar['destination']==j,'occurrence identity')
                for name,val in dict(arrival_time_s=arrival,waiting_s=start-arrival,service_start_s=start,service_s=service,departure_time_s=clock,t_chg_s=tc).items():eq(ev[name],val,tt,'time '+name)
                for name,val in dict(arrival_battery_kwh=arrb,departure_battery_kwh=b,q_chg_kwh=q,SOC_arr_pct=5*arrb,SOC_dep_pct=5*b).items():eq(ev[name],val,5*et,'energy '+name)
                for name,val in dict(distance_km=km,energy_kwh=e,battery_before_kwh=before,battery_after_kwh=arrb).items():eq(ar[name],val,et,'arc '+name)
                eq(ar['travel_time_s'],tau,tt,'arc travel')
                check(ev['battery_feasible']==node_b and ev['temporal_feasible']==node_t,'node flags')
            eq(b,initial+charge-energy,et,'route conservation')
            for name,val in dict(travel_s=road,charging_s=duration,return_time_s=clock).items():eq(claimed[name],val,tt,'summary '+name)
            for name,val in dict(distance_km=dist,energy_kwh=energy,charged_kwh=charge,final_battery_kwh=b,minimum_battery_kwh=minimum,final_SOC_pct=5*b).items():eq(claimed[name],val,5*et,'summary '+name)
            check(claimed['capacity_feasible']==cap and claimed['battery_feasible']==bok and claimed['temporal_feasible']==tok,'component flags')
            feasible=cap and bok and tok;check(claimed['feasible']==feasible,'route feasible')
            if feasible:
                # WIDE/no-wait constant-power lower bound certifies the reference
                # charge optimum for this fixed route without optimizer helpers.
                eq(charge,max(D(0),energy+2-initial),et,'minimum total partial charge')
            computed.append(feasible);totaltravel+=road;totalcharge+=duration
        visits=all(visit[c]==1 for c in customers)
        check(saved['visit_feasible']==visits,'visit status');check(saved['feasible']==(visits and all(computed)),'fleet status')
        eq(saved['primary_travel_s'],totaltravel,tt,'primary travel');eq(saved['secondary_charging_s'],totalcharge,tt,'secondary time')
    return dict(status='PASS' if not errors else 'FAIL',errors=errors,independent_feasible=visits and all(computed),arithmetic='Decimal80; no EV replay/solver helper',energy_tolerance_kwh=str(et),time_tolerance_s=str(tt))


def validate_exhaustive(instance,od,pre,reference):
    """Reconstruct full discrete domain independently and check every saved plan."""
    vids=[x['vehicle_id'] for x in instance['vehicles']];cs=[x['customer_id'] for x in instance['customers']];d=instance['depot']['depot_id'];c=pre['route'][1]
    expected=set()
    for assigned in product(vids,repeat=len(cs)):
        choices=[]
        for v in vids:
            mine=[x for x,a in zip(cs,assigned) if a==v];routes=[]
            if not mine:routes=[()]
            else:
                for order in permutations(mine):
                    for mask in range(2**(len(mine)+1)):
                        route=[d]
                        for k in range(len(mine)+1):
                            if mask & (1<<k):route.append(c)
                            if k<len(mine):route.append(order[k])
                        routes.append(tuple(route+[d]))
            choices.append(routes)
        expected.update(product(*choices))
    observed=set();valid=[];checks=[]
    for candidate in reference['candidates']:
        observed.add(tuple(tuple(p['nodes']) for p in candidate['plans']))
        check=validate(instance,od,pre,candidate['plans'],candidate['result'],reference['charging_enabled']);checks.append(check)
        if check['independent_feasible']:valid.append((D(str(candidate['result']['primary_travel_s'])),D(str(candidate['result']['secondary_charging_s']))))
    errors=[]
    if observed!=expected or len(reference['candidates'])!=len(expected):errors.append('domain completeness/duplicates')
    if any(x['status']!='PASS' for x in checks):errors.append('candidate validation')
    best=min(valid) if valid else None
    if best!=(tuple(map(lambda x:D(str(x)),reference['objective'])) if reference['objective'] else None):errors.append('lex optimum')
    return dict(status='PASS' if not errors else 'FAIL',errors=errors,domain_count=len(expected),all_candidate_checks=checks,feasible_count=len(valid),independent_objective=None if best is None else list(map(str,best)))


def validate_raw_milp(instance,od,pre,milp):
    """Check original solver time/battery states, allowing legitimate waiting slack.

    This does not replace them by earliest replay or normalize charging amounts.
    """
    errors=[]
    with localcontext() as context:
        context.prec=80
        cs={x['customer_id']:x for x in instance['customers']};closing=D(str(instance['depot']['closing_time']))
        for plan in milp['plans']:
            if not plan['nodes']:continue
            raw=[x for x in milp['raw_schedule'] if x['vehicle_id']==plan['vehicle_id']]
            if [r['node'] for r in raw]!=plan['nodes']:errors.append('raw node sequence');continue
            if abs(D(str(raw[0]['battery_arrival_kwh']))-D(pre['provisional_initial_battery_kwh']))>ET:errors.append('raw initial battery')
            if abs(D(str(raw[0]['service_start_s']))-D(str(instance['depot']['opening_time'])))>TT:errors.append('raw initial time')
            for pos,r in enumerate(raw):
                b=D(str(r['battery_arrival_kwh']));q=D(str(r['q_chg_kwh']));t=D(str(r['service_start_s']))
                if b<2-ET or b+q>20+ET or q<-ET:errors.append('raw battery bound')
                if r['node']!=pre['route'][1] and abs(q)>ET:errors.append('raw illegal charging')
                if t>closing+TT:errors.append('raw horizon')
                if r['node'] in cs:
                    c=cs[r['node']]
                    if t<D(str(c['earliest_service_time']))-TT or t>D(str(c['latest_service_time']))+TT:errors.append('raw window')
                if pos:
                    prev=raw[pos-1];edge=od[prev['node']+'|'+r['node']]
                    energy=D(str(edge['distance_m']))*D('.000127')
                    expected=D(str(prev['battery_arrival_kwh']))+D(str(prev['q_chg_kwh']))-energy
                    if abs(b-expected)>ET:errors.append('raw arc conservation')
                    serv=D(str(cs[prev['node']]['service_duration'])) if prev['node'] in cs else D(0)
                    earliest=D(str(prev['service_start_s']))+serv+360*D(str(prev['q_chg_kwh']))+D(str(edge['travel_time_s']))
                    if t<earliest-TT:errors.append('raw temporal propagation')
    return dict(status='PASS' if not errors else 'FAIL',errors=errors,method='Independent Decimal raw solver certificate; waiting slack allowed, no repair')
