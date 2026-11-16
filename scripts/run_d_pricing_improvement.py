"""New D artificial experiments; exclusive output, pre-registered config, no S1 IO.

Run each stage under watchdog_d_improvement.py; 300s/RSS safety is secondary.
All actual scientific stops are finite region/CG/node budgets, not target time.
"""
import argparse
import csv
from dataclasses import asdict, replace, is_dataclass
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import shutil
import sys
from time import perf_counter
import numpy as np
from kmd_toc.column_generation.models import Instance, Route, route_cost
from kmd_toc.column_generation.aoa import AOAConfig, PricingAOA
from kmd_toc.column_generation.reduction import contract, exact_domain_routes
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import DayProblem, Vehicle, ObjectiveProfile
from kmd_toc.vehicle_day.generation import seed_plan, make_day
from kmd_toc.vehicle_day.validation import independent_plan_oracle, validate_plan
from kmd_toc.search_improvement.catalogue import build_catalogue, artificial_column_estimate
from kmd_toc.search_improvement.master import CatalogueMaster
from kmd_toc.search_improvement.regions import legacy_regions, expanded_regions, exact_routes, measure_routes
from kmd_toc.search_improvement.study import coverage, pool_from_saved, run_search, zero_face, incumbent_repair, nondominated


def default(v):
    if is_dataclass(v): return asdict(v)
    if isinstance(v,np.ndarray): return v.tolist()
    if isinstance(v,np.generic): return v.item()
    if isinstance(v,set): return sorted(v)
    raise TypeError(str(type(v)))


def save(path,value):
    with path.open('x') as f: json.dump(value,f,default=default,indent=2,allow_nan=False)


def table(path,rows):
    if not rows: return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def synthetic(n,f,b,holdout=False):
    positions=(0,)+tuple(range(n,0,-2))+tuple(range(n-1,0,-2))
    d=np.array([[((y-x) if y>=x else 2*(x-y))/10 for y in positions] for x in positions])
    # Deterministic different holdout distances, fixed before any experiment.
    if holdout:
        d=d+np.array([[0 if i==j else ((7*i+3*j)%5)/50 for j in range(n+1)] for i in range(n+1)])
    base=Instance(f'artificial_{n}_F{f}_B{b}'+('_holdout' if holdout else ''),d,(0,)+(1,)*n,2)
    travel=tuple(tuple(0 if i==j else 120 for j in range(n+1)) for i in range(n+1))
    vehicles=tuple(Vehicle(f'V{i}',2,0,0,1680,120,120) for i in range(f))
    return DayProblem(base,travel,(0,)+(120,)*n,vehicles,b,120)


def input_record(p):
    return {'fingerprint':p.fingerprint,'name':p.base.name,'distance_km':p.base.distance.tolist(),
            'parcel_count':p.base.demand,'travel_s':p.travel_s,'service_s':p.service_s,
            'vehicles':[asdict(v) for v in p.vehicles],'berths':p.berths,'delta_s':p.delta_s}


def independent_route_bound(p):
    """Independent customer-mask/trip-count DP, no day catalogue/master matrix.

    A valid schedule attaining this distance lower bound proves artificial IP
    optimality. It is not a general VRP/scheduling sufficiency theorem.
    """
    n=len(p.base.customers); full=(1<<n)-1; dp={(0,0):(0.,())}
    for mask in range(full+1):
        for k in range(2*len(p.vehicles)):
            if (mask,k) not in dp: continue
            value,path=dp[mask,k]
            unseen=[i for i in p.base.customers if not mask>>(i-1)&1]
            if not unseen: continue
            i=unseen[0]
            options=[(i,)]
            for j in unseen[1:]: options.extend([(i,j),(j,i)])
            for route in options:
                newmask=mask|sum(1<<(a-1) for a in route)
                cost=value+route_cost(p.base,Route(route))
                key=(newmask,k+1)
                if key not in dp or cost<dp[key][0]-1e-9: dp[key]=(cost,path+(route,))
    cost,path=min(v for (mask,k),v in dp.items() if mask==full)
    # Independent assignment in waves with earliest slot by explicit occupancy.
    occupied=[0]*p.slots; ready=[v.ready_s for v in p.vehicles]; days=[[] for _ in p.vehicles]; starts=[[] for _ in p.vehicles]
    for k,route in enumerate(path):
        vi=k%len(p.vehicles); v=p.vehicles[vi]; found=False
        for t in range(ready[vi],v.shift_end_s,p.delta_s):
            if occupied[t//p.delta_s]>=p.berths: continue
            try: c=make_day(p,v.vehicle_id,tuple(days[vi]+[Route(route)]),tuple(starts[vi]+[t]))
            except ValueError: continue
            days[vi].append(Route(route)); starts[vi].append(t);occupied[t//p.delta_s]+=1
            ready[vi]=c.trips[-1].return_s+v.preparation_s;found=True;break
        if not found: return {'lower_bound_D':cost,'attained':False,'dp_states':len(dp)}
    plan=[make_day(p,v.vehicle_id,tuple(days[i]),tuple(starts[i])) for i,v in enumerate(p.vehicles) if days[i]]
    metrics=validate_plan(p,plan)
    return {'lower_bound_D':cost,'attained':metrics['valid'] and abs(cost-metrics['D_km'])<1e-7,
            'metrics':metrics,'dp_states':len(dp),'route_sequences':path}


def execute(args):
    cfgpath=Path('configs/toc_delivery_d_pricing_improvement_v1.json'); cfg=json.loads(cfgpath.read_text())
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    root=Path(args.baseline); config=AOAConfig(**cfg['aoa'])
    started=perf_counter()
    sources=list(Path('src/kmd_toc/search_improvement').glob('*.py'))+list(Path('src/kmd_toc/vehicle_day').glob('*.py'))+list(Path('src/kmd_toc/column_generation').glob('*.py'))+[Path(__file__),cfgpath]
    save(out/'EXECUTION_MANIFEST.json',{'started_utc':datetime.now(timezone.utc).isoformat(),
         'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
         'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
         'config':cfg,'source_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
         'stage':args.stage,'S1_executions':0,'no_parameter_search':True})
    for p in sources:
        relative=p.relative_to(Path.cwd()) if p.is_absolute() else p
        dest=out/'SOURCE_SNAPSHOT'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    def master(p,name):
        begin=perf_counter(); columns=build_catalogue(p,cfg['safety']['max_catalogue_columns']); m=CatalogueMaster(p,columns)
        duration=perf_counter()-begin
        save(out/(name+'_INPUT.json'),input_record(p))
        save(out/(name+'_CATALOGUE.json'),{'columns':len(columns),'route_count':len(m.route_index),
             'construction_and_validation_seconds':duration,'matrix_nnz':m.a.nnz,
             'sparse_array_bytes':m.a.data.nbytes+m.a.indices.nbytes+m.a.indptr.nbytes,
             'ordered_column_ids_sha256':hashlib.sha256('\n'.join(m.ids).encode()).hexdigest()})
        return m,duration

    if args.stage=='coverage':
        m,prep=master(small_problem(6,1),'N6_B1')
        base=json.loads((root/'AOA_N6_B1_D.json').read_text());pool=pool_from_saved(m,base)
        final=base['final_lp']['dual']; initial=base['trace'][0]['lp']['dual']
        fullw=m.lp(list(range(len(m.columns))),ObjectiveProfile('W'))
        snapshots=[('regression_final_D',m,pool,final,ObjectiveProfile(),len(base['trace'])-1),
                   ('regression_initial_D',m,[m.index[c.column_id] for c in seed_plan(m.problem)],initial,ObjectiveProfile(),0),
                   ('zero_negative_W',m,list(range(len(m.columns))),fullw['dual'],ObjectiveProfile('W'),0)]
        h,_=master(synthetic(6,2,1,True),'HOLDOUT6')
        hp=[h.index[c.column_id] for c in seed_plan(h.problem)]
        snapshots.append(('holdout_initial_D',h,hp,h.lp(hp,ObjectiveProfile())['dual'],ObjectiveProfile(),0))
        wp=[m.index[c.column_id] for c in seed_plan(m.problem)]
        snapshots.append(('regression_initial_W',m,wp,m.lp(wp,ObjectiveProfile('W'))['dual'],ObjectiveProfile('W'),0))
        rows=[]
        for name,cat,ids,dual,profile,it in snapshots:
            save(out/(name+'_SNAPSHOT.json'),{'dual':dual,'profile':vars(profile),'pool_ids':[cat.ids[i] for i in ids]})
            for version,regions in [('old',legacy_regions(cat.problem,dual,it)),('expanded',expanded_regions(cat.problem,dual,it))]:
                exact=exact_routes(cat.problem,dual,profile,regions)
                cr=coverage(cat,ids,dual,profile,regions,exact)
                rows.append({'snapshot':name,'region_version':version,'sampler':'same_scope_classical','seed':'',**{k:v for k,v in cr.items() if not isinstance(v,list)}})
                for seed in cfg['snapshot_seeds']:
                    begin=perf_counter(); sampled,logs=measure_routes(cat.problem,dual,profile,regions,replace(config,solver_seed=seed),it)
                    r=coverage(cat,ids,dual,profile,regions,sampled)
                    save(out/f'{name}_{version}_{seed}.json',{'domains':regions,'pool':ids,'dual':dual,'profile':vars(profile),
                         'coverage':r,'sampled_routes':sampled,'quantum':logs,'seconds':perf_counter()-begin})
                    total=sum(x['result']['measured_shots'] for x in logs); feasible=sum(x['result']['feasible_shots'] for x in logs)
                    rows.append({'snapshot':name,'region_version':version,'sampler':'aoa','seed':seed,
                         **{k:v for k,v in r.items() if not isinstance(v,list)},'shots':total,'feasible_shots':feasible,
                         'feasible_shot_rate':feasible/total,'seconds':perf_counter()-begin,'domains':len(regions),
                         'max_qubits':max(x['result']['qubits'] for x in logs),'max_logical_depth':max(x['result']['logical_depth'] for x in logs),
                         'angle_evaluations':sum(z['nfev'] for x in logs for z in x['result']['history'])})
                print(name,version,'scope',cr['candidate_coverage'],flush=True)
        table(out/'COVERAGE.csv',rows)
        # Macro variants all compared at the exact SAME frozen final dual.
        macro_rows=[]
        partitions={'paired':[(1,2),(3,4),(5,6)],'split':[(1,),(2,),(3,)],
                    'boundary_shift':[(2,3),(4,5),(6,1)],'cross_vehicle':[(1,3),(2,5),(4,6)],
                    'merge_after_split':[(1,2),(3,),(4,)]}
        for name,groups in partitions.items():
            domain=contract(m.problem.base,final['customer'],groups,'macro_'+name,slots=3)
            routes={r.customers for r in exact_domain_routes(m.problem.base,domain)}
            # Verify exact cost, quantity and dual-profit preservation independently.
            checks=[]
            for local in exact_domain_routes(domain.pricing,contract(domain.pricing,domain.dual,[(i,) for i in domain.pricing.customers],'identity',slots=3)):
                expanded=domain.expand(local)
                checks.append(abs(route_cost(domain.pricing,local)-route_cost(m.problem.base,expanded))<1e-8 and
                    sum(domain.pricing.demand[i] for i in local.customers)==sum(m.problem.base.demand[i] for i in expanded.customers) and
                    abs(sum(domain.dual[i-1] for i in local.customers)-sum(final['customer'][i-1] for i in expanded.customers))<1e-8)
            rc=m.rc(final,ObjectiveProfile()); neg=set(np.flatnonzero(rc < -1e-7).tolist())
            scope=m.complete(routes,m.known(pool)); got=PricingAOA(domain.pricing,domain.dual,config).run()
            measured={domain.expand(Route(tuple(r))).customers for r in got['routes']}
            actual=m.complete(measured,m.known(pool))
            record={'variant':name,'groups':groups,'routes':sorted(routes),'scope_negative':len(neg&scope),
                  'outside_scope_negative':len(neg-scope),'obtained_negative':len(neg&actual),
                  'qubits':got['qubits'],'logical_depth':got['logical_depth'],'invariants_pass':all(checks),'quantum':got}
            save(out/f'MACRO_{name}.json',record)
            macro_rows.append({k:v for k,v in record.items() if k not in ('quantum','groups','routes')})
        table(out/'MACROS.csv',macro_rows)

    elif args.stage=='integrated':
        summaries=[]; gaps=[]; epsilon=[]
        for name,p in [('N6_B1',small_problem(6,1)),('N5_B1',small_problem(5,1)),('HOLDOUT6',synthetic(6,2,1,True))]:
            m,prep=master(p,name); allids=list(range(len(m.columns))); full_lp=m.lp(allids,ObjectiveProfile()); full_ip=m.ip(allids,ObjectiveProfile())
            independent=independent_plan_oracle(p,m.columns,ObjectiveProfile())
            assert independent['feasible'] and abs(independent['objective']-full_ip['objective'])<1e-7
            save(out/(name+'_FULL_REFERENCE.json'),{'lp':full_lp,'ip':full_ip,'independent':independent})
            pools={}
            if name in ('N6_B1','N5_B1'):
                for kind,fn in [('old_aoa','AOA'),('old_classical','CG')]:
                    saved=json.loads((root/f'{fn}_N{len(p.base.customers)}_B1_D.json').read_text())
                    pools[kind]=pool_from_saved(m,saved)
            for mode in ['same_scope_classical','aoa']:
                seeds=cfg['snapshot_seeds'] if name=='N6_B1' and mode=='aoa' else [2101]
                for seed in seeds:
                    key=f'{mode}_{seed}'
                    result=run_search(m,ObjectiveProfile(),replace(config,solver_seed=seed),mode=mode,max_rounds=cfg['cg']['max_rounds'],batch_size=cfg['cg']['batch_size'],max_calls=cfg['safety']['max_aoa_calls_per_case'])
                    save(out/f'{name}_{key}.json',result);pools[key]=result['pool']
                    metrics=result['ip'].get('metrics',{})
                    summaries.append({'case':name,'method':key,'columns':len(m.columns),'pool':len(result['pool']),
                        'LP':result['lp'].get('objective'),'IP':result['ip'].get('objective'),'full_IP':full_ip['objective'],
                        'D':metrics.get('D_km'),'W':metrics.get('W_min'),'gap':result['ip'].get('objective',0)-full_ip['objective'] if result['ip'].get('objective') is not None else None,
                        'stop':result['stop'],'final_min_rc':result['final_global_min_rc_diagnostic'],'rounds':len(result['trace']),
                        'aoa_calls':result['aoa_calls'],'aoa_s':result['aoa_seconds'],'warm_T_s':result['warm_method_seconds'],
                        'catalogue_s':prep,'cold_T_s':prep+result['warm_method_seconds'],'diagnostic_s':result['diagnostic_seconds'],
                        'ip_s':result['ip'].get('seconds'),'valid':metrics.get('valid')})
                    print(name,key,summaries[-1],flush=True)
            # Enrichment and repair independently, also applied to classical controls.
            for key,pool in pools.items():
                lp=m.lp(pool,ObjectiveProfile()); ip=m.ip(pool,ObjectiveProfile())
                face=zero_face(m,pool,ObjectiveProfile()); repair=incumbent_repair(m,pool,ObjectiveProfile())
                save(out/f'{name}_{key}_INTEGER_EXTENSIONS.json',{'zero_face':face,'vehicle_repair':repair})
                gaps.append({'case':name,'method':key,'full_LP':full_lp['objective'],'restricted_LP':lp['objective'],
                    'full_IP':full_ip['objective'],'restricted_IP':ip.get('objective'),
                    'lp_missing':lp['objective']-full_lp['objective'],
                    'restricted_integrality':ip['objective']-lp['objective'] if ip['success'] else None,
                    'full_integrality':full_ip['objective']-full_lp['objective'],
                    'integer_gap':ip['objective']-full_ip['objective'] if ip['success'] else None,
                    'integer_gap_percent':100*(ip['objective']-full_ip['objective'])/full_ip['objective'] if ip['success'] and full_ip['objective'] else None,
                    'before_D':ip.get('metrics',{}).get('D_km'),'before_W':ip.get('metrics',{}).get('W_min'),
                    'face_IP':face.get('ip',{}).get('objective'),'face_D':face.get('ip',{}).get('metrics',{}).get('D_km'),
                    'face_W':face.get('ip',{}).get('metrics',{}).get('W_min'),'face_added':face.get('added'),
                    'face_classical_s':face['seconds'],'face_negative_remaining':face.get('negative_columns_not_inserted'),
                    'repair_IP':repair['ip'].get('objective'),'repair_D':repair['ip'].get('metrics',{}).get('D_km'),
                    'repair_W':repair['ip'].get('metrics',{}).get('W_min'),'repair_classical_s':repair['seconds'],'repair_added_selected':repair.get('added_selected')})
            if name=='N6_B1':
                profiles=[ObjectiveProfile('D',e) for e in cfg['epsilon_D_subject_to_W']]+[ObjectiveProfile('W',e) for e in cfg['epsilon_W_subject_to_D']]
                observed={}
                selected_pools={'full_reference':allids,'old_aoa':pools['old_aoa'],'old_classical':pools['old_classical'],
                                'expanded_aoa':pools['aoa_2101'],'expanded_classical':pools['same_scope_classical_2101']}
                for profile in profiles:
                    full=m.ip(allids,profile)
                    for key,pool in selected_pools.items():
                        raw=m.ip(pool,profile); face=zero_face(m,pool,profile)
                        for variant,ip in [('raw',raw),('classical_zero_face',face.get('ip',{'success':False}))]:
                            metrics=ip.get('metrics',{})
                            row={'primary':profile.primary,'epsilon':profile.other_limit,'pool':key,'variant':variant,
                                 'success':ip['success'],'value':ip.get('objective'),'reference':full.get('objective'),
                                 'gap':ip['objective']-full['objective'] if ip['success'] and full['success'] else None,
                                 'D':metrics.get('D_km'),'W':metrics.get('W_min'),'certified_optimal':ip.get('certified_optimal',False)}
                            epsilon.append(row)
                            if ip['success']:observed.setdefault(key+'_'+variant,[]).append((metrics['D_km'],metrics['W_min']))
                front={k:nondominated(v) for k,v in observed.items()}
                reference=front.get('full_reference_raw',[])
                save(out/'OBSERVED_NONDOMINATED.json',{'fronts':front,'finite_profiles_only':True,
                    'missing_reference_points':{k:[p for p in reference if not any(abs(p[0]-q[0])<1e-7 and abs(p[1]-q[1])<1e-7 for q in v)] for k,v in front.items()}})
        table(out/'INTEGRATED.csv',summaries);table(out/'INTEGER_GAPS.csv',gaps);table(out/'EPSILON.csv',epsilon)

    elif args.stage=='scaling':
        estimates=[];rows=[]
        for n,f,b in cfg['scale_candidates']:
            count=artificial_column_estimate(n,f); memory=count*cfg['safety']['catalogue_estimated_bytes_per_column']
            allowed=count<=cfg['safety']['max_catalogue_columns'] and n<=12 and f<=3 and memory<cfg['safety']['max_rss_mib']*1024**2
            estimates.append({'N':n,'F':f,'B':b,'estimated_columns':count,'estimated_catalogue_mib':memory/1024**2,
                              'decision':'RUN' if allowed else 'SKIP_BEFORE_GENERATION','reason':'COLUMN_MEMORY_DOMAIN_GUARD' if not allowed else 'INSIDE_PREDECLARED_LIMITS'})
        save(out/'RESOURCE_PREFLIGHT.json',estimates)
        for estimate in estimates:
            if estimate['decision']!='RUN':continue
            n,f,b=(estimate[k] for k in ('N','F','B')); name=f'N{n}_F{f}_B{b}'
            m,prep=master(synthetic(n,f,b),name);allids=list(range(len(m.columns)))
            assert len(allids)==estimate['estimated_columns']
            full_lp=m.lp(allids,ObjectiveProfile());full_ip=m.ip(allids,ObjectiveProfile());ind=independent_route_bound(m.problem)
            assert full_ip['success'] and ind['attained'] and abs(full_ip['objective']-ind['lower_bound_D'])<1e-7
            save(out/f'{name}_FULL_REFERENCE.json',{'lp':full_lp,'ip':full_ip,'independent_route_dp':ind})
            # Finite expanded AOAs at root; complete CG for all feasible V2 cases.
            for mode in ['same_scope_classical','aoa']:
                result=run_search(m,ObjectiveProfile(),config,mode=mode,max_rounds=40,batch_size=20,max_calls=800)
                save(out/f'{name}_{mode}.json',result)
                face=zero_face(m,result['pool'],ObjectiveProfile())
                save(out/f'{name}_{mode}_ZERO_FACE.json',face)
                metrics=result['ip'].get('metrics',{})
                q=[x['result'] for t in result['trace'] for x in t['quantum']]
                rows.append({'case':name,'N':n,'F':f,'B':b,'columns':len(allids),'rmp_rows':m.a.shape[0],
                    'pool':len(result['pool']),'mode':mode,'LP':result['lp'].get('objective'),'full_LP':full_lp['objective'],
                    'IP':result['ip'].get('objective'),'full_IP':full_ip['objective'],'D':metrics.get('D_km'),'W':metrics.get('W_min'),
                    'gap':result['ip'].get('objective',0)-full_ip['objective'] if result['ip'].get('objective') is not None else None,
                    'face_IP':face.get('ip',{}).get('objective'),'face_added':face.get('added'),'face_s':face['seconds'],
                    'stop':result['stop'],'min_rc':result['final_global_min_rc_diagnostic'],'rounds':len(result['trace']),
                    'aoa_calls':result['aoa_calls'],'lp_s':result['lp_seconds'],'aoa_s':result['aoa_seconds'],
                    'warm_T_s':result['warm_method_seconds'],'cold_T_s':prep+result['warm_method_seconds'],
                    'catalogue_s':prep,'IP_s':result['ip'].get('seconds'),'full_IP_s':full_ip['seconds'],
                    'qubits':max((r['qubits'] for r in q),default=0),'logical_depth':max((r['logical_depth'] for r in q),default=0),
                    'measured_shots':sum(r['measured_shots'] for r in q),'angle_evaluations':sum(z['nfev'] for r in q for z in r['history']),
                    'peak_rss_mib_process_to_date':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'valid':metrics.get('valid')})
                print(name,mode,rows[-1],flush=True)
        table(out/'SCALING.csv',rows)
    save(out/'STAGE_COMPLETE.json',{'seconds':perf_counter()-started,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
         'safety_limit_triggered':False,'study_runs':0})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--baseline',required=True)
    parser.add_argument('--stage',choices=['coverage','integrated','scaling'],required=True)
    execute(parser.parse_args())
