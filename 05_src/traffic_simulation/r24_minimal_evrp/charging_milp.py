"""Independent arc-flow HiGHS formulation. No exact candidate costs injected.

Two solve stages: road travel, then charge time on primary optimum band1e-7s.
Start/end depot are distinct; charger occurrence copies allow every sequence gap.
Positive arc time removes subtours. Waiting/service use existing start-window rule.
"""
import time
import highspy
from .charging import fleet_replay, ENERGY_TOL, TIME_TOL

OPTIONS=dict(threads=1,random_seed=0,presolve='on',mip_rel_gap=0.0,mip_abs_gap=0.0,
             primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9,
             mip_feasibility_tolerance=1e-9,time_limit=60.0,output_flag=False)


def solve(ctx,enabled):
    started=time.perf_counter();h=highspy.Highs()
    for k,v in OPTIONS.items():
        assert h.setOptionValue(k,v)==highspy.HighsStatus.kOk
    names={};rows=[];lower=[];upper=[];integers=[]
    def var(name,lo,hi,integer=False):
        ix=len(names);names[name]=ix
        assert h.addVar(float(lo),float(hi))==highspy.HighsStatus.kOk
        if integer:assert h.changeColIntegrality(ix,highspy.HighsVarType.kInteger)==highspy.HighsStatus.kOk
        lower.append(float(lo));upper.append(float(hi));integers.append(integer);return ix
    def row(coef,lo=-float('inf'),hi=float('inf')):
        assert h.addRow(float(lo),float(hi),len(coef),list(coef),list(map(float,coef.values())))==highspy.HighsStatus.kOk
        rows.append((coef,float(lo),float(hi)))
    b=ctx['base'];customers=list(b['customers']);copies=['@CHG'+str(k) for k in range(len(customers)+1)]
    S='@START';T='@RETURN';inside=customers+copies;nodes=[S,*inside,T];vids=list(b['vehicles'])
    physical=lambda x:b['depot_id'] if x in (S,T) else ctx['charger'] if x in copies else x
    edges=[(i,j) for i in [S,*inside] for j in [*inside,T] if i!=j and not(i==S and j==T) and not(i in copies and j in copies)]
    tt={(i,j):float(ctx['arcs'][physical(i),physical(j)][0]) for i,j in edges}
    ee={(i,j):float(ctx['r']*ctx['arcs'][physical(i),physical(j)][1]) for i,j in edges}
    maximum=float(ctx['maximum']);reserve=float(ctx['reserve']);H=float(b['closing']);opening=float(b['opening']);factor=3600/float(ctx['power'])
    Mt=H+max(tt.values());Mb=maximum+max(ee.values())
    x={};y={};z={};s={};battery={};q={}
    for k in vids:
        z[k]=var(('z',k),0,1,True)
        for n in inside:y[k,n]=var(('y',k,n),0,1,True)
        for n in nodes:
            s[k,n]=var(('s',k,n),opening,H)
            battery[k,n]=var(('battery',k,n),reserve,maximum)
            q[k,n]=var(('q',k,n),0,maximum if enabled and n in copies else 0)
        for i,j in edges:x[k,i,j]=var(('x',k,i,j),0,1,True)
    for n in customers:row({y[k,n]:1 for k in vids},1,1)
    primary={x[k,i,j]:tt[i,j] for k in vids for i,j in edges}
    for k in vids:
        row({s[k,S]:1},opening,opening);row({battery[k,S]:1},float(ctx['initial']),float(ctx['initial']))
        for n in inside:
            incoming={x[k,i,j]:1 for i,j in edges if j==n};incoming[y[k,n]]=-1;row(incoming,0,0)
            outgoing={x[k,i,j]:1 for i,j in edges if i==n};outgoing[y[k,n]]=-1;row(outgoing,0,0)
            row({y[k,n]:1,z[k]:-1},hi=0)
        departure={x[k,i,j]:1 for i,j in edges if i==S};departure[z[k]]=-1;row(departure,0,0)
        returning={x[k,i,j]:1 for i,j in edges if j==T};returning[z[k]]=-1;row(returning,0,0)
        used={y[k,n]:1 for n in customers};used[z[k]]=-1;row(used,lo=0)
        cap={y[k,n]:float(b['customers'][n]['demand']) for n in customers};cap[z[k]]=-float(b['vehicles'][k]);row(cap,hi=0)
        for n in inside:
            row({q[k,n]:1,y[k,n]:-maximum},hi=0)
            row({battery[k,n]:1,q[k,n]:1},hi=maximum)
            serv=float(b['customers'][n]['duration']) if n in customers else 0
            row({s[k,n]:1,y[k,n]:serv,q[k,n]:factor},hi=H)
            if n in customers:row({s[k,n]:1},float(b['customers'][n]['earliest']),float(b['customers'][n]['latest']))
        # Occurrence-copy symmetry only; physical route set unchanged.
        for a,c in zip(copies,copies[1:]):
            row({y[k,c]:1,y[k,a]:-1},hi=0)
            row({s[k,c]:1,s[k,a]:-1,y[k,c]:-H},lo=-H)
        for i,j in edges:
            serv=float(b['customers'][i]['duration']) if i in customers else 0
            coef={s[k,j]:1,s[k,i]:-1,q[k,i]:-factor,x[k,i,j]:-Mt}
            if i in inside:coef[y[k,i]]=-serv
            row(coef,lo=tt[i,j]-Mt)
            # Selected arc fixes battery equality, including return reserve.
            expr={battery[k,j]:1,battery[k,i]:-1,q[k,i]:-1}
            row({**expr,x[k,i,j]:-Mb},lo=-ee[i,j]-Mb)
            row({**expr,x[k,i,j]:Mb},hi=-ee[i,j]+Mb)
    for a,c in zip(vids,vids[1:]):row({z[a]:1,z[c]:-1},lo=0)
    for ix,cost in primary.items():h.changeColCost(ix,cost)
    stages=[]
    def run(stage):
        start=time.perf_counter();status=h.run();ms=h.getModelStatus();info=h.getInfo()
        record=dict(stage=stage,run_status=str(status),model_status=h.modelStatusToString(ms),wall_time_s=time.perf_counter()-start,
                    objective=info.objective_function_value if ms==highspy.HighsModelStatus.kOptimal else None,
                    mip_nodes=info.mip_node_count,mip_gap=info.mip_gap if ms==highspy.HighsModelStatus.kOptimal else None)
        stages.append(record)
        if status!=highspy.HighsStatus.kOk:raise RuntimeError('STOP: HiGHS run failure')
        return ms
    ms=run('primary_road_travel')
    common=dict(solver='HiGHS',version=h.version(),options=OPTIONS,charging_enabled=enabled,stages=stages,
                variable_count=len(names),constraint_count=len(rows),big_M_time_s=Mt,big_M_energy_kwh=Mb,
                occurrence_copies_per_vehicle=len(copies),primary_fix_tolerance_s=1e-7)
    if ms==highspy.HighsModelStatus.kInfeasible:return dict(common,status='PROVEN_INFEASIBLE',wall_time_s=time.perf_counter()-started)
    if ms!=highspy.HighsModelStatus.kOptimal:raise RuntimeError('STOP: primary optimality not proven')
    optimum=h.getInfo().objective_function_value
    row(primary,optimum-1e-7,optimum+1e-7)
    for ix in primary:h.changeColCost(ix,0)
    for k in vids:
        for n in copies:h.changeColCost(q[k,n],factor)
    if run('secondary_charging_time')!=highspy.HighsModelStatus.kOptimal:raise RuntimeError('STOP: secondary optimality not proven')
    values=list(h.getSolution().col_value)
    residual=max([0.0]+[max(lo-sum(float(v)*values[ix] for ix,v in co.items()),sum(float(v)*values[ix] for ix,v in co.items())-hi,0) for co,lo,hi in rows])
    bounds=max([0.0]+[max(lo-v,v-hi,abs(v-round(v)) if integer else 0,0) for v,lo,hi,integer in zip(values,lower,upper,integers)])
    if residual>1e-7 or bounds>1e-7:raise RuntimeError('STOP: MILP primal certificate residual')
    plans=[];raw_schedule=[]
    for k in vids:
        if values[z[k]]<.5:plans.append(dict(vehicle_id=k,nodes=[],charges={}));continue
        sequence=[S];node=S
        while node!=T:
            dest=[j for i,j in edges if i==node and values[x[k,i,j]]>.5]
            if len(dest)!=1 or dest[0] in sequence:raise RuntimeError('STOP: route decode')
            node=dest[0];sequence.append(node)
        charges={str(pos):str(values[q[k,n]]) for pos,n in enumerate(sequence) if n in copies}
        plans.append(dict(vehicle_id=k,nodes=[physical(n) for n in sequence],charges=charges))
        for pos,n in enumerate(sequence):raw_schedule.append(dict(vehicle_id=k,position=pos,model_node=n,node=physical(n),service_start_s=values[s[k,n]],battery_arrival_kwh=values[battery[k,n]],q_chg_kwh=values[q[k,n]]))
    # Feasible earliest replay is a reporting schedule; raw solver slack retained.
    # No quantities clipped, rounded to exact q, or repaired.
    result=fleet_replay(ctx,plans,energy_tol=ENERGY_TOL,time_tol=TIME_TOL)
    return dict(common,status='PROVEN_OPTIMAL',primary_stage_optimum_s=optimum,plans=plans,replay=result,
                raw_schedule=raw_schedule,primal_max_row_residual=residual,primal_max_bound_integrality_residual=bounds,
                raw_variables=[dict(name=list(n),value=values[i]) for n,i in names.items()],
                wall_time_s=time.perf_counter()-started)
