"""Full multi-vehicle A-area candidate, preserving A2 assignment and FCFS policy."""
from dataclasses import asdict
import heapq
import json
import math
import os
from pathlib import Path
import resource
import time

from .area import local_xy, ordered_nodes
from .area_study import settings, CONFIG_SHA256
from .construction import _angular_order, _balance, _chunks, _cost
from .program import ROOT, load_registered, settings as input_settings, digest
from .program_validation import audit_plan
from kmd_toc.common.config import load_conditions
from kmd_toc.common.models import Plan, Trip, Visit
from kmd_toc.common.validation import validate_plan


def load_model(path, expected_sha256):
    if digest(path)!=expected_sha256:
        raise ValueError('AREA_MODEL_HASH')
    model = json.loads(Path(path).read_text())
    config = settings()
    if (model.get('version')!=config['version'] or model.get('config_sha256')!=CONFIG_SHA256 or
            model.get('validation_outcomes_used_for_selection') is not False or
            model.get('full_representativeness_PASS') is not False):
        raise ValueError('AREA_MODEL_SCOPE_OR_VERSION')
    p = model['selected_parameters']
    if p['kind']=='area':
        if p['leaf_capacity'] not in config['candidates']['leaf_capacities'] or p['stay_factor'] not in config['candidates']['stay_factors']:
            raise ValueError('AREA_MODEL_UNREGISTERED_PARAMETERS')
    elif p['kind']!='NN':
        raise ValueError('AREA_MODEL_KIND')
    return model


def create_plan(problem, model, model_sha256, mark=None):
    problem.validate()
    config = settings()
    operations = load_conditions()['operations']
    capacity = operations['capacity_per_trip']
    vehicles = len(problem.vehicles)
    if sum(s.demand for s in problem.stops)>sum(v.capacity*v.max_trips for v in problem.vehicles):
        raise ValueError('AREA_TOTAL_CAPACITY_INSUFFICIENT')
    ordered = _angular_order(problem,0)
    ranks = {j:i for i,j in enumerate(ordered)}
    groups = [ordered[len(ordered)*v//vehicles:len(ordered)*(v+1)//vehicles] for v in range(vehicles)]
    initial = {problem.stops[j-1].stop_id:v for v,g in enumerate(groups) for j in g}
    balance = _balance(groups,problem,ranks,capacity,vehicles)
    ids = [problem.depot.depot_id,*[s.stop_id for s in problem.stops]]
    xy = local_xy([problem.depot.longitude,*[s.longitude for s in problem.stops]],
                  [problem.depot.latitude,*[s.latitude for s in problem.stops]],
                  problem.depot.longitude,problem.depot.latitude)
    routes,area_traces = [],{}
    for index,group in enumerate(groups):
        if group:
            order,trace = ordered_nodes(group,problem.od.distance_m,xy,ids,model['selected_parameters'])
            area_traces[problem.vehicles[index].vehicle_id] = trace
        else:
            order = []
        parts = _chunks(order,capacity)
        if len(parts)>operations['max_trips_per_vehicle']:
            raise ValueError('AREA_TRIP_COUNT_OVERFLOW')
        routes.append(parts)
    if mark:
        mark('area_assignment_order_and_trip_split_end')
    events = [(v.first_ready_s,i,0) for i,v in enumerate(problem.vehicles) if routes[i]]
    heapq.heapify(events)
    available = {b.berth_id:b.opening_s for b in problem.berths}
    trips = []
    while events:
        ready,v,k = heapq.heappop(events)
        berth = min(problem.berths,key=lambda b:(available[b.berth_id],b.berth_id))
        start = max(ready,available[berth.berth_id],berth.opening_s)
        end = start+operations['loading_s']
        available[berth.berth_id] = end
        clock,current,visits = end,0,[]
        for j in routes[v][k]:
            clock += math.ceil(float(problem.od.duration_s[current,j]))
            visits.append(Visit(ids[j],clock,clock,clock+operations['service_s']))
            clock += operations['service_s']
            current = j
        clock += math.ceil(float(problem.od.duration_s[current,0]))
        trips.append(Trip(problem.vehicles[v].vehicle_id,k+1,problem.depot.depot_id,problem.depot.depot_id,
            tuple(visits),ready,berth.berth_id,start,end,end,clock,
            _cost(routes[v][k],problem.od.distance_m),start-ready))
        if k+1<len(routes[v]):
            heapq.heappush(events,(clock+operations['preparation_s'],v,k+1))
    if mark:
        mark('area_FCFS_and_timestamps_end')
    final = {problem.stops[j-1].stop_id:v for v,g in enumerate(groups) for j in g}
    metadata = {'version':config['version'],'model_sha256':model_sha256,'selected_parameters':model['selected_parameters'],
        'calibration_selected_parameters':model.get('calibration_selected_parameters',model['selected_parameters']),
        'execution_role':model.get('execution_role','calibration_selected'),
        'initial_assignment':initial,'final_assignment':final,'balance_moves':balance,'area_traces':area_traces,
        'assignment_rule':'unchanged A2 angle0 and at most V boundary moves',
        'order_rule':'calibration-selected NN or input-derived area preference; shared road-distance costs',
        'trip_rule':'successive capacity chunks, maximum two','loading_rule':'FCFS',
        'automatic_repair':False,'operator_actual_algorithm':False,'road_distance_behavior_validated':False,
        'calibration_scope':'US historical-time ordering component; transfer to Ota road distance is unvalidated',
        'main_experiment_eligible':False,'seed':None}
    return Plan('1.0',f'{problem.experiment.scenario_id}-A-area-v3','A',problem.fingerprint,
                problem.od.fingerprint,tuple(trips),metadata,'classical')


def measured(loader, model_loader, *, limit_s=180, clock=time.perf_counter):
    start,cpu = clock(),time.process_time()
    events = [{'name':'input_and_model_load_start','elapsed_s':0.}]
    def mark(name):
        elapsed = clock()-start
        events.append({'name':name,'elapsed_s':elapsed})
        if elapsed>limit_s:
            raise TimeoutError('AREA_PROGRAM_LIMIT')
    row = {'status':'ERROR','D_km':None,'W_min':None,'T_program_s':None,'T_A_program':None,
        'T_A_human_reference':None,'physical_feasible':False,'T_kind':'program_wall',
        'T_scope':['model_read_and_hash','input_read_and_hash','assignment','order','trip_split','FCFS',
                   'all_timestamps','common_validation','independent_recalculation','agreement'],
        'validation':None,'second_validation':None,'error':None,'J':None,'reference_status':'NOT_FROZEN',
        'full_representativeness':'NOT_ESTABLISHED','main_experiment_eligible':False}
    plan,problem = None,None
    stage = 'INPUT'
    try:
        model,model_hash = model_loader()
        problem = loader()
        mark('input_and_model_load_end')
        stage = 'GENERATION'
        plan = create_plan(problem,model,model_hash,mark)
        mark('generation_end')
        stage = 'VALIDATION'
        common = validate_plan(problem,plan)
        row['validation'] = common.as_dict()
        mark('common_validation_end')
        independent = audit_plan(problem,plan)
        row['second_validation'] = independent
        mark('independent_recalculation_end')
        agrees = (common.feasible and independent['feasible'] and
            abs(common.D_km-float(independent['D_km']))<1e-7 and
            abs(common.W_min-float(independent['W_min']))<1e-7)
        row['status'] = 'VALIDATED' if agrees else 'REJECTED_PLAN'
        if agrees:
            row.update(D_km=common.D_km,W_min=common.W_min,physical_feasible=True)
        mark('agreement_end')
    except Exception as error:
        row.update(status='TIME_LIMIT' if isinstance(error,TimeoutError) else ('INPUT_HOLD' if stage=='INPUT' else 'ERROR'),
                   error={'stage':stage,'type':type(error).__name__,'message':str(error)})
        events.append({'name':'failed','elapsed_s':clock()-start})
    elapsed = events[-1]['elapsed_s']
    row.update(T_attempt_wall_s=elapsed,cpu_time_s=time.process_time()-cpu,timing_events=events,
               max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,budget_met=elapsed<=limit_s)
    if row['status']=='VALIDATED':
        row.update(T_program_s=elapsed,T_A_program=elapsed)
    else:
        row.update(D_km=None,W_min=None,physical_feasible=False)
    if problem:
        row.update(scenario_id=problem.experiment.scenario_id,input_hash=problem.fingerprint,OD_hash=problem.od.fingerprint,
                   visited_count=sum(len(t.visits) for t in plan.trips) if plan else 0)
    return row,plan


def dump(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def execute(case,model_path,model_hash,output,setup=None,diagnostic_best_area=False):
    out = Path(output)
    out.mkdir(parents=True,exist_ok=False)
    cfg = settings()
    registered = input_settings()
    dump(out/'config.json',cfg)
    def model_loader():
        model = load_model(model_path,model_hash)
        if diagnostic_best_area:
            model = {**model,'calibration_selected_parameters':model['selected_parameters'],
                     'selected_parameters':model['best_area_parameters'],
                     'execution_role':'best_area_diagnostic_NOT_selected'}
        return model,model_hash
    row,plan = measured(lambda:load_registered(ROOT/registered['input_root']/case,registered['scenarios'][case],case),
                        model_loader,limit_s=cfg['limits']['program_limit_s'])
    row.update(method='A',version=cfg['version'],selected_model_sha256=model_hash,setup=setup,
               pid=os.getpid(),cpu_affinity=sorted(os.sched_getaffinity(0)),
               execution_role='best_area_diagnostic_NOT_selected' if diagnostic_best_area else 'calibration_selected')
    export_start = time.perf_counter()
    (out/'selected_model.json').write_bytes(Path(model_path).read_bytes())
    if plan:
        dump(out/('plan.json' if row['status']=='VALIDATED' else 'rejected_plan.json'),asdict(plan))
        import csv
        fields = ['vehicle_id','trip_no','berth_id','ready_s','load_start_s','load_end_s','departure_s','return_s',
                  'distance_m','waiting_s','stop_count']
        with (out/'trips.csv').open('x',newline='') as stream:
            writer = csv.DictWriter(stream,fieldnames=fields)
            writer.writeheader()
            for t in plan.trips:
                writer.writerow({**{k:getattr(t,k) for k in fields if k!='stop_count'},'stop_count':len(t.visits)})
    dump(out/'validation.json',{'status':row['status'],'common':row['validation'],
        'independent':row['second_validation'],'error':row['error']})
    dump(out/'metrics.json',row)
    dump(out/'manifest.json',{'version':cfg['version'],'status':row['status'],'model_sha256':model_hash,
        'input_files_sha256':registered['scenarios'][case]['files'],'T_scope':row['T_scope'],
        'products_sha256':{p.name:digest(p) for p in out.iterdir() if p.is_file()},
        'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'src/kmd_toc/baseline_a/area.py']},
        'main_experiment_eligible':False})
    dump(out/'EXPORT_TIMING.json',{'primary_products_export_wall_s':time.perf_counter()-export_start,
        'scope':'through primary manifest write; excludes timing/hash footer writes'})
    dump(out/'OUTPUT_HASHES.json',{p.name:digest(p) for p in out.iterdir() if p.is_file()})
    return row
