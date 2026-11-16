"""Auditable A-only experiments; missing research inputs never become fixtures."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics
from kmd_toc.common.models import load_problem, save_problem, load_plan
from kmd_toc.common.runtime import run_measured, environment
from kmd_toc.frozen_demand import load_frozen_demand
from .config import load_settings, SHA256
from .construction import create_plan
from .fixtures import artificial_problem
from .human_time import human_time_sensitivity
from .independent import recompute


def dump(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def write_csv(path, rows):
    if not rows:return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in rows:
            w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else v for k,v in row.items()})


def summary(rows):
    result=[]
    for case in sorted({r['scenario_id'] for r in rows}):
        for condition in ['ALL','A1','A2','A3']:
            subset=[r for r in rows if r['scenario_id']==case and (condition=='ALL' or r['condition']==condition)]
            good=[r for r in subset if r['status']=='FEASIBLE']
            attempted=[r for r in subset if r['status'] not in ('INPUT_HOLD','NOT_RUN')]
            record={'scenario_id':case,'condition':condition,'registered_conditions':len(subset),
                    'attempted_plans':len(attempted),'feasible_plans':len(good),
                    'feasible_rate':len(good)/len(attempted) if attempted else None,
                    'input_hold':sum(r['status']=='INPUT_HOLD' for r in subset),
                    'failure_reasons':dict(Counter(r.get('reason','') for r in subset if r['status']!='FEASIBLE')),
                    'range_kind':'observed_condition_set_not_confidence_interval'}
            for key in ['D_km','W_min','T_program_s']:
                vals=[r[key] for r in good if r.get(key) is not None]
                for stat,fn in [('min',min),('max',max),('median',statistics.median)]:
                    record[key+'_'+stat]=fn(vals) if vals else None
            result.append(record)
    return result


def frozen_preflight():
    rows=[]
    for scenario in ['S1','S2','S3']:
        f=load_frozen_demand(scenario,method_id='A');N=sum(s.parcel_count for s in f.stops)
        rows.append({'scenario_id':scenario,'N':f.N,'total_demand':N,'vehicles':f.vehicles,'berths':f.berths,
                     'total_two_trip_capacity':f.vehicles*2*60,'capacity_necessary_condition':N<=f.vehicles*120,
                     'minimum_trips':math.ceil(N/60),'maximum_trips':f.vehicles*2,
                     'minimum_loading_occupancy_min':math.ceil(math.ceil(N/60)/f.berths)*30,
                     'service_only_parallel_lower_bound_s':math.ceil(N*120/f.vehicles),
                     'manifest_sha256':f.manifest_sha256,'csv_sha256':f.csv_sha256,
                     'consumer_method_id':f.consumer_method_id,'feasibility_proved':False})
    return rows


def run_case(input_dir, case, output, *, expected_kind, expected_scenario=None):
    cfg=load_settings();rows=[];human=[]
    for condition in cfg['methods']:
        for offset in cfg['angle_offsets_deg']:
            runid=f'{case}-{condition}-angle{offset}';captured={}
            def loader():
                p=load_problem(input_dir)
                if p.experiment.kind!=expected_kind or (expected_scenario and p.experiment.scenario_id!=expected_scenario):
                    raise ValueError('A_INPUT_KIND_OR_SCENARIO')
                captured['problem']=p;return p
            result=run_measured(loader,lambda p,mark:create_plan(p,condition,offset,mark))
            result['T_program_s']=result.pop('T_s')
            result['T_semantics']='program wall seconds, NOT measured or estimated human time'
            row={'run_id':runid,'scenario_id':case,'condition':condition,'angle_offset_deg':offset,
                 'settings_sha256':SHA256,'input_kind':expected_kind,'status':result['status'],
                 'D_km':result['D_km'],'W_min':result['W_min'],'T_program_s':result['T_program_s'],
                 'elapsed_wall_s':result['elapsed_wall_s'],'T_human_min_s':None,'T_human_max_s':None,
                 'T_human_median_s':None,'reason':'','independent_match':None}
            if result['plan'] is not None:
                planpath=output/(runid+'.plan.json');dump(planpath,result['plan'])
                plan=load_plan(planpath)
                if result['status']=='FEASIBLE':
                    audit=recompute(captured['problem'],plan)
                    match=audit['feasible'] and abs(float(audit['D_km'])-row['D_km'])<1e-7 and abs(float(audit['W_min'])-row['W_min'])<1e-7
                    result['second_recalculation']=audit;row['independent_match']=match
                    if not match:
                        row.update(status='AUDIT_FAILURE',D_km=None,W_min=None,T_program_s=None,reason='INDEPENDENT_RECALCULATION_FAILED')
                    else:
                        p=captured['problem'];counts=Counter()
                        for t in plan.trips:counts[t.vehicle_id]+=len(t.visits)
                        events={e['name']:e['elapsed_s'] for e in result['timing_events']}
                        overhead=events['input_load_end']+events['independent_validation_end']-events['independent_validation_start']
                        estimates=human_time_sensitivity([counts[v.vehicle_id] for v in p.vehicles],measured_io_validation_s=overhead)
                        for r in estimates:human.append({'run_id':runid,'scenario_id':case,'condition':condition,
                                                       'scope':'artificial_validation' if expected_kind=='synthetic_validation' else 'research_rule_plan',**r})
                        vals=[r['T_human_estimate_s'] for r in estimates]
                        row.update(T_human_min_s=min(vals),T_human_max_s=max(vals),T_human_median_s=statistics.median(vals))
                        row['problem_hash']=p.fingerprint;row['od_hash']=p.od.fingerprint
                        row['used_vehicles']=len(counts);row['trips']=len(plan.trips)
            if result['status']!='FEASIBLE':
                row['reason']=result['error']['message'] if result['error'] else '|'.join(sorted({v['code'] for v in result['validation']['violations']}))
            dump(output/(runid+'.runtime.json'),result);rows.append(row)
    return rows,human


def run_study(output, *, inputs_root=None, validation_only=False):
    cfg=load_settings();out=Path(output);out.mkdir(parents=True,exist_ok=False)
    (out/'runs').mkdir();(out/'inputs').mkdir()
    dump(out/'ENVIRONMENT.json',environment());preflight=frozen_preflight();write_csv(out/'FROZEN_PREFLIGHT.csv',preflight)
    rows=[];human=[]
    for case in cfg['validation_cases']:
        p=artificial_problem(case['stops'],case['vehicles'],case['berths'])
        path=out/'inputs'/case['id'];save_problem(p,path)
        r,h=run_case(path,case['id'],out/'runs',expected_kind='synthetic_validation');rows.extend(r);human.extend(h)
    statuses=[]
    for case in preflight:
        sid=case['scenario_id'];path=Path(inputs_root)/sid if inputs_root else None
        if not validation_only and path and (path/'input.json').exists():
            r,h=run_case(path,sid,out/'runs',expected_kind='frozen_research',expected_scenario=sid);rows.extend(r);human.extend(h)
            statuses.extend(r)
        else:
            reason='VALIDATION_ONLY' if validation_only else 'VERIFIED_DEPOT_SNAPS_AND_COMMON_OSM_OSRM_OD_BUNDLE_MISSING'
            for condition in cfg['methods']:
                for offset in cfg['angle_offsets_deg']:
                    r={'run_id':f'{sid}-{condition}-angle{offset}','scenario_id':sid,'condition':condition,
                       'angle_offset_deg':offset,'settings_sha256':SHA256,'input_kind':'frozen_research',
                       'status':'NOT_RUN' if validation_only else 'INPUT_HOLD','D_km':None,'W_min':None,
                       'T_program_s':None,'T_human_min_s':None,'T_human_max_s':None,'T_human_median_s':None,'reason':reason}
                    rows.append(r);statuses.append(r)
    structural=[]
    for case in preflight:
        N,V=case['N'],case['vehicles'];counts=[N//V+(i<N%V) for i in range(V)]
        for r in human_time_sensitivity(counts):
            structural.append({'scenario_id':case['scenario_id'],'scope':'structural_sensitivity_only_NOT_experiment',
                               'assignment_assumption':'equal_stop_counts_no_routing_feasibility_claim',**r})
    write_csv(out/'CONDITIONAL_RESULTS.csv',rows);write_csv(out/'HUMAN_TIME_BY_PLAN.csv',human)
    write_csv(out/'HUMAN_TIME_STRUCTURAL_SENSITIVITY.csv',structural);write_csv(out/'RESEARCH_SCENARIO_STATUS.csv',statuses)
    stats=summary(rows);write_csv(out/'OBSERVED_RANGES.csv',stats)
    dump(out/'SUMMARY.json',{'version':cfg['baseline_version'],'settings_sha256':SHA256,'rows':rows,'ranges':stats,
                            'structural_human_sensitivity':structural,'frozen_preflight':preflight,
                            'synthetic_is_not_S1_to_S3':True,'BD_results_used':False,'Sagawa_actual':False})
    return out
