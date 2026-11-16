#!/usr/bin/env python3
"""Bounded reproduction of the unmodified Cook author code on public histories.

This is an external visit-order study, not a replacement for Ota baseline A.
"""
import argparse
from collections import defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from kmd_toc.baseline_a.sequence_validation import (
    actual_order, digest, dump, iter_json_object, metrics, nearest_projection,
    official_normalization, ranked, route_ids, time_matrix, validate_order)
from kmd_toc.baseline_a.area import local_xy, spatial_labels


def canonical_route(route):
    result = copy.deepcopy(route)
    result['stops'] = {s: result['stops'][s] for s in sorted(result['stops'])}
    # Amazon encodes the station's absent zone as NaN; JSON null has the same
    # missing-zone meaning in the unmodified author's utility functions.
    for stop in result['stops'].values():
        if stop['type']=='Station' and not isinstance(stop.get('zone_id'),str):
            stop['zone_id'] = None
    return result


def extract(path, wanted):
    result = {k:v for k,v in iter_json_object(path) if k in wanted}
    if set(result) != set(wanted):
        raise ValueError('MISSING_EXTRACTED_ROUTE')
    return {k:result[k] for k in wanted}


def plan(data, output, config_path):
    output.mkdir(parents=True, exist_ok=False)
    config = json.loads(config_path.read_text())
    manifest = json.loads((data/'MANIFEST.json').read_text())
    for name in ['eval_routes.json','eval_times.json','eval_actual.json']:
        if digest(data/name) != manifest['files'][name]['sha256']:
            raise ValueError('CACHE_HASH:'+name)
    metadata = json.loads((data/'eval_routes.json').read_text())
    prior_path = ROOT/'output/toc_delivery/a_area_v3_20261115_study01/SPLIT.json'
    prior = json.loads(prior_path.read_text())
    prior_ids = set(prior['prior_ids'] + prior['calibration'] + prior['validation'])
    prior_days = {tuple(p) for p in prior['prior_station_days']}
    prior_days |= {(metadata[r]['station_code'],metadata[r]['date_YYYY_MM_DD']) for r in prior_ids}
    previous_stations = {s for s,d in prior_days}
    eligible, excluded = defaultdict(lambda:defaultdict(list)), []
    for rid, route in metadata.items():
        try:
            ids = route_ids(route)
            if not config['minimum_dropoffs'] <= len(ids)-1 <= config['maximum_dropoffs']:
                raise ValueError('DROPOFF_SIZE_BOUND')
            if not all(isinstance(route['stops'][s].get('zone_id'),str) and route['stops'][s]['zone_id'] for s in ids[1:]):
                raise ValueError('INCOMPLETE_ORIGINAL_ZONES')
            key = (route['station_code'],route['date_YYYY_MM_DD'])
            if rid in prior_ids or key in prior_days:
                raise ValueError('PRIOR_SCORED_ROUTE_OR_STATION_DAY')
            eligible[key[0]][key[1]].append(rid)
        except (ValueError,KeyError,TypeError) as error:
            excluded.append({'route_id':rid,'reason':str(error)})
    train_pool = [s for s,dates in eligible.items() if s in previous_stations and s not in config['unknown_stations'] and
        sum(d <= config['training_last_date'] for d in dates) >= config['training_routes_per_station'] and
        sum(d >= config['evaluation_first_date'] for d in dates) >= config['future_routes_per_station']]
    stations = sorted(train_pool,key=lambda s:ranked(config['seed'],'train_station',s))[:config['training_stations']]
    if len(stations) != config['training_stations']:
        raise ValueError('NOT_ENOUGH_TRAINING_STATIONS')
    splits = {'training':[],'same_station_future':[],'unknown_station':[]}
    def select(station, split, count, predicate):
        dates = sorted([d for d in eligible[station] if predicate(d)],
                       key=lambda d:ranked(config['seed'],split,station,d))[:count]
        if len(dates) != count:
            raise ValueError('INSUFFICIENT_DATES:'+station)
        return [min(eligible[station][d],key=lambda r:ranked(config['seed'],split,r)) for d in dates]
    for station in stations:
        splits['training'] += select(station,'training',config['training_routes_per_station'],lambda d:d<=config['training_last_date'])
        splits['same_station_future'] += select(station,'same_station_future',config['future_routes_per_station'],lambda d:d>=config['evaluation_first_date'])
    for station in config['unknown_stations']:
        if station in stations:
            raise ValueError('UNKNOWN_STATION_IN_TRAINING')
        splits['unknown_station'] += select(station,'unknown_station',config['unknown_routes_per_station'],lambda d:d>=config['evaluation_first_date'])
    all_ids = sum(splits.values(),[])
    if len(set(all_ids)) != len(all_ids) or set(all_ids)&prior_ids:
        raise ValueError('ROUTE_SPLIT_LEAKAGE')
    records = {k:[{'route_id':r,'station':metadata[r]['station_code'],
                   'date':metadata[r]['date_YYYY_MM_DD'],'dropoffs':len(metadata[r]['stops'])-1} for r in v] for k,v in splits.items()}
    dump(output/'REGISTRATION.json', {'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'config':config,'config_sha256':digest(config_path),'script_sha256':digest(Path(__file__)),
        'source_hashes':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'src/kmd_toc/baseline_a/sequence_validation.py',ROOT/'src/kmd_toc/baseline_a/area.py']},
        'prior_split_sha256':digest(prior_path),'input_manifest':manifest,
        'split_ids':splits,'split_records':records,'training_stations':stations,
        'previously_scored_ids':sorted(prior_ids),'previously_scored_station_days':sorted(prior_days),
        'excluded_metadata':excluded,'selection_used_actual_order_or_scores':False,
        'original_official_train_test_partition_preserved':False})
    dump(output/'routes.json', {r:canonical_route(metadata[r]) for r in all_ids})
    # Only the training orders are supplied to the author model builder.
    dump(output/'training_actual.json',extract(data/'eval_actual.json',splits['training']))
    dump(output/'selected_times.json',extract(data/'eval_times.json',all_ids))
    dump(output/'PLAN_HASHES.json',{p.name:digest(p) for p in output.iterdir() if p.is_file()})
    print(json.dumps({'status':'PLANNED','training_stations':stations,
        'unknown_stations':config['unknown_stations'],'counts':{k:len(v) for k,v in splits.items()}},ensure_ascii=False),flush=True)


def auto_zones(route, leaf_capacity):
    result = canonical_route(route)
    ids = route_ids(result)
    xy = local_xy([result['stops'][s]['lng'] for s in ids], [result['stops'][s]['lat'] for s in ids],
                  result['stops'][ids[0]]['lng'],result['stops'][ids[0]]['lat'])
    labels = spatial_labels(range(1,len(ids)),xy,ids,leaf_capacity)
    names = {label:f'A-{i+1:02d}.1A' for i,label in enumerate(sorted(set(labels.values())))}
    for i in range(1,len(ids)):
        result['stops'][ids[i]]['zone_id'] = names[labels[i]]
    return result


def parse_tour(path, index_to_stop, expected_ids):
    text = path.read_text()
    lines = text.splitlines()
    start = next(i for i,l in enumerate(lines) if l.strip()=='TOUR_SECTION')+1
    indices = []
    for line in lines[start:]:
        value = int(line.strip())
        if value == -1:
            break
        indices.append(value)
    if len(indices)!=len(set(indices)) or len(indices)!=len(expected_ids):
        raise ValueError('INVALID_TOUR_PERMUTATION')
    order = [index_to_stop[str(i)] for i in indices]
    # Match the official convention station first without reversing direction.
    pos = order.index(expected_ids[0])
    order = order[pos:]+order[:pos]
    validate_order(expected_ids,order)
    match = re.search(r'COMMENT\s*:\s*Cost\s*=\s*(\d+)_(\d+)',text)
    if match:
        penalty, cost = map(int,match.groups())
    else:
        match = re.search(r'COMMENT\s*:\s*Length\s*=\s*(\d+)',text)
        if not match:
            raise ValueError('MISSING_AUTHOR_TOUR_COST')
        penalty, cost = None,int(match.group(1))
    return order, {'penalty':penalty,'integer_travel_cost':cost,'tour_sha256':digest(path)}


def official_reference_score(official, actual, candidate, costs):
    # Official score() expects an explicitly closed tour, unlike our validators.
    return official.score([*actual,actual[0]],[*candidate,candidate[0]],copy.deepcopy(costs))


class Runner:
    def __init__(self, output, config):
        self.output, self.config, self.calls = output,config,[]
        self.start = time.perf_counter()
    def call(self, command, cwd, label, timeout):
        if time.perf_counter()-self.start > self.config['study_wall_limit_s']:
            raise TimeoutError('STUDY_WALL_LIMIT')
        begin = time.perf_counter()
        log = self.output/'logs'/f'{len(self.calls):03d}_{label}.log'
        log.parent.mkdir(exist_ok=True)
        process = None
        record = {'command':list(map(str,command)),'cwd':str(cwd),'label':label,
            'native_threads':1,'affinity':sorted(os.sched_getaffinity(0)),
            'wall_timeout_s':timeout,'log':str(log.relative_to(self.output))}
        with log.open('x') as stream:
            try:
                process = subprocess.Popen(list(map(str,command)),cwd=cwd,stdout=stream,
                    stderr=subprocess.STDOUT,start_new_session=True,env=os.environ.copy())
                record['pid'] = process.pid
                record['returncode'] = process.wait(timeout=timeout)
                if record['returncode']:
                    raise RuntimeError('AUTHOR_PROCESS_FAILED:'+label)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
                record['timed_out'] = True
                raise TimeoutError('AUTHOR_PROCESS_TIMEOUT:'+label)
            finally:
                record['wall_s'] = time.perf_counter()-begin
                self.calls.append(record)
                (self.output/'PROCESS_CALLS.json').write_text(json.dumps(self.calls,ensure_ascii=False,indent=2)+'\n')
        return record


def generate(runner, code, python, training_path, model_path, routes, times, variant, directory):
    directory.mkdir(parents=True,exist_ok=False)
    config = runner.config
    input_routes = {r:(auto_zones(v,config['automatic_zone_leaf_capacity']) if variant=='Cook_auto_zones' else canonical_route(v)) for r,v in routes.items()}
    if variant=='Cook_no_zones':
        for route in input_routes.values():
            for stop in route['stops'].values():
                stop['zone_id'] = None
    dump(directory/'route_data.json',input_routes)
    ordered_times = {r:{a:{b:times[r][a][b] for b in input_routes[r]['stops']} for a in input_routes[r]['stops']} for r in routes}
    dump(directory/'travel_times.json',ordered_times)
    dump(directory/'package_stop_order.json',{r:{s:{} for s in v['stops']} for r,v in input_routes.items()})
    outputs, traces = {},{}
    for formulation in config['formulations']:
        tsp = directory/formulation
        args = [python,code/'scripts/build_TSPLIB.py','--r_file',directory/'route_data.json',
            '--t_file',directory/'travel_times.json','--p_file',directory/'package_stop_order.json',
            '--z_file',model_path,'--br_file',training_path,'-noPrune','-noPruneFailed',
            '-zoneNeighborTrans','-superNeighborTrans']
        if formulation=='author_precedence_transitive':
            args += ['-superPred','-trans']
        if variant=='Cook_no_zones':
            args += ['-noZone','-noZonePred']
        args.append(tsp)
        runner.call(args,directory,variant+'_'+formulation+'_prepare',config['preprocessing_wall_limit_s'])
        mapping = json.loads((tsp/'tsp2amz.json').read_text())
        form_sequences, form_traces = {},{}
        for pname, record in mapping.items():
            rid = record['route_id']
            tour = tsp/(pname+'.tour')
            parameter = tsp/(pname+'.par')
            parameter.write_text(f'PROBLEM_FILE = {tsp/(pname+".ctsptw")}\nCTSP_TRANSFORM = YES\nSEED = {config["solver_seed"]}\nTIME_LIMIT = {config["solver_cpu_limit_s_per_formulation"]}\nTRACE_LEVEL = 0\nTOUR_FILE = {tour}\n')
            proc = runner.call([code/'LKH-AMZ/LKH',parameter],directory,variant+'_'+formulation+'_'+pname,config['solver_wall_limit_s_per_formulation'])
            order, trace = parse_tour(tour,record['stops'],route_ids(routes[rid]))
            # Check IDs against the canonical route stop order independently of the author map.
            assert [record['stops'][str(i+1)] for i in range(len(record['stops']))] == list(input_routes[rid]['stops'])
            independent_cost = sum(int(10*times[rid][a][b]) for a,b in zip(order,order[1:]+order[:1]))
            if independent_cost != trace['integer_travel_cost']:
                raise ValueError('AUTHOR_COST_RECALCULATION_MISMATCH')
            form_sequences[rid] = order
            form_traces[rid] = trace | {'process':proc,'ctsptw_sha256':digest(tsp/(pname+'.ctsptw')),
                'ctsptw_sections':[l for l in (tsp/(pname+'.ctsptw')).read_text().splitlines() if l.endswith('_SECTION')]}
        outputs[formulation],traces[formulation] = form_sequences,form_traces
    chosen, selected = {},{}
    for rid in routes:
        c1 = traces['author_path'][rid]['integer_travel_cost']
        c2 = traces['author_precedence_transitive'][rid]['integer_travel_cost']
        winner = 'author_path' if c1 <= (101*c2)//100 else 'author_precedence_transitive'
        chosen[rid] = outputs[winner][rid]
        selected[rid] = {'selected_formulation':winner,'path_cost':c1,'precedence_cost':c2}
    dump(directory/'PROPOSALS.json',chosen)
    dump(directory/'SOLVER_TRACES.json',{'formulations':traces,'selection':selected})
    return chosen


def run(data, plan_dir, output, code, python):
    output.mkdir(parents=True,exist_ok=False)
    reg = json.loads((plan_dir/'REGISTRATION.json').read_text())
    config = reg['config']
    for name,h in json.loads((plan_dir/'PLAN_HASHES.json').read_text()).items():
        if digest(plan_dir/name)!=h:
            raise ValueError('PLAN_CHANGED:'+name)
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip()
    if commit != config['author_commit']:
        raise ValueError('AUTHOR_COMMIT_MISMATCH')
    tracked = subprocess.check_output(['git','ls-files'],cwd=code,text=True).splitlines()
    author_hashes = {name:digest(code/name) for name in tracked if (code/name).is_file()}
    bin_hash = digest(code/'LKH-AMZ/LKH')
    cpu = min(os.sched_getaffinity(0))
    os.sched_setaffinity(0,{cpu})
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[key] = '1'
    dump(output/'ENVIRONMENT.json',{'python':sys.version,'executable':sys.executable,'author_python':str(python),
        'platform':platform.platform(),'cpu_affinity':[cpu],'threads':1,
        'gcc':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
        'author_commit':commit,'author_tracked_hashes':author_hashes,'binary_sha256':bin_hash,
        'T_scope':'external inference diagnostics; not Ota T_A_program or human planning time'})
    runner = Runner(output,config)
    runner.call([python,'-c','import sys,natsort; print(sys.executable); print(natsort.__version__)'],
                output,'author_python_preflight',config['preprocessing_wall_limit_s'])
    routes = json.loads((plan_dir/'routes.json').read_text())
    times = json.loads((plan_dir/'selected_times.json').read_text())
    splits = reg['split_ids']
    training = {r:routes[r] for r in splits['training']}
    evaluation_ids = splits['same_station_future'] + splits['unknown_station']
    if {routes[r]['station_code'] for r in splits['unknown_station']} & {r['station_code'] for r in training.values()}:
        raise ValueError('UNKNOWN_STATION_LEAKAGE')
    dump(output/'training_routes.json',training)
    training_orders = json.loads((plan_dir/'training_actual.json').read_text())
    for rid in training:
        actual_order(training_orders[rid],route_ids(training[rid]))
    runner.call([python,code/'scripts/analyze_zone_id_order_main.py','--r_file',output/'training_routes.json',
        '--s_file',plan_dir/'training_actual.json','--out_file',output/'model.json'],output,
        'model_training',config['preprocessing_wall_limit_s'])
    model = json.loads((output/'model.json').read_text())
    no_history = copy.deepcopy(model)
    no_history['station_infos'], no_history['superSets'] = {},{}
    dump(output/'model_no_station_history.json',no_history)
    model_stations = set(model['station_infos']) | set(model['superSets'])
    if model_stations & set(config['unknown_stations']):
        raise ValueError('LEARNED_MODEL_UNKNOWN_STATION_LEAKAGE')
    dump(output/'MODEL_AUDIT.json',{'training_routes':list(training),'model_stations':sorted(model_stations),
        'unknown_stations_absent':True,'cluster_keys':model['clusterKeys'],
        'held_out_actual_orders_passed_to_generator':False,'model_sha256':digest(output/'model.json')})
    proposals, errors = {},[]
    eval_routes = {r:routes[r] for r in evaluation_ids}
    for variant in config['variants']:
        try:
            mp = output/('model_no_station_history.json' if variant in ['Cook_no_station_history','Cook_auto_zones'] else 'model.json')
            proposals[variant] = generate(runner,code,python,output/'training_routes.json',mp,eval_routes,times,variant,output/variant)
        except Exception as error:
            errors.append({'method':variant,'type':type(error).__name__,'error':str(error)})
            dump(output/(variant+'_FAILURE.json'),errors[-1])
        print(json.dumps({'completed':variant,'success':variant in proposals}),flush=True)
    proposals['NN_time'] = {r:nearest_projection(route_ids(routes[r]),time_matrix(route_ids(routes[r]),times[r])) for r in evaluation_ids}
    repeats = {}
    for group in ['same_station_future','unknown_station']:
        rid = splits[group][0]
        try:
            repeat = generate(runner,code,python,output/'training_routes.json',output/'model.json',
                {rid:routes[rid]},times,'Cook_public_zones',output/('repeat_'+group))
            repeats[group] = {'route_id':rid,'identical_order':repeat[rid]==proposals.get('Cook_public_zones',{}).get(rid)}
        except Exception as error:
            repeats[group] = {'route_id':rid,'error':str(error)}
    dump(output/'ALL_PROPOSALS_BEFORE_SCORING.json',proposals)
    dump(output/'BEFORE_SCORING.json',{'proposals_sha256':digest(output/'ALL_PROPOSALS_BEFORE_SCORING.json'),
        'model_sha256':digest(output/'model.json'),'repeats':repeats,'errors':errors,
        'selected_evaluation_actual_orders_loaded_by_run':False})
    score_saved_proposals(data,output,config,splits,routes,times,proposals,repeats,errors)
    source_changed = [name for name,h in author_hashes.items() if digest(code/name)!=h]
    if source_changed or digest(code/'LKH-AMZ/LKH')!=bin_hash:
        raise ValueError('AUTHOR_CODE_CHANGED_DURING_STUDY')
    dump(output/'RUN_STATUS.json',{'status':'COMPLETE' if not errors else 'COMPLETE_WITH_FAILURES',
        'wall_s':time.perf_counter()-runner.start,'author_sources_unchanged':True,
        'source_changed':source_changed,'main_experiment_eligible':False})
    dump(output/'OUTPUT_HASHES.json',{str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps({'status':'COMPLETE' if not errors else 'COMPLETE_WITH_FAILURES','failures':len(errors),'wall_s':time.perf_counter()-runner.start}),flush=True)


def score_saved_proposals(data,output,config,splits,routes,times,proposals,repeats,errors):
    evaluation_ids = splits['same_station_future']+splits['unknown_station']
    # Withheld outcomes enter only after every proposal and repeat has been fixed.
    truth = extract(data/'eval_actual.json',evaluation_ids)
    scorer_path = ROOT/'docs/research/baseline_a_sequence_validation_20261114_v1/sources/OFFICIAL_SCORE.py'
    spec = importlib.util.spec_from_file_location('cook_official_reference',scorer_path)
    official = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(official)
    measured, parity = [],[]
    for rid in evaluation_ids:
        ids = route_ids(routes[rid])
        matrix = time_matrix(ids,times[rid])
        actual = actual_order(truth[rid],ids)
        norm = official_normalization(matrix)
        for method in config['variants']+['NN_time','Actual_reference']:
            candidate = actual if method=='Actual_reference' else proposals.get(method,{}).get(rid)
            record = {'route_id':rid,'station_code':routes[rid]['station_code'],'date':routes[rid]['date_YYYY_MM_DD'],
                'split':'same_station_future' if rid in splits['same_station_future'] else 'unknown_station','method':method,'dropoffs':len(ids)-1}
            if candidate is None:
                measured.append(record | {'status':'FAILED'})
                continue
            values = metrics(ids,candidate,actual,matrix,routes[rid],norm)
            # Official scorer mutates its matrix and requires explicit closure.
            reference = official_reference_score(official,actual,candidate,times[rid])
            difference = float(abs(values['amazon_score']-reference))
            parity.append({'route_id':rid,'method':method,'absolute_error':difference,'passed':bool(difference<=1e-10)})
            if difference>1e-10:
                raise ValueError('OFFICIAL_SCORER_PARITY')
            measured.append(record | {'status':'SCORED'} | values)
    dump(output/'METRICS.json',measured)
    dump(output/'OFFICIAL_SCORER_PARITY.json',{'source_sha256':digest(scorer_path),'checks':parity,'all_passed':all(p['passed'] for p in parity)})
    summary = {'by_split':{},'failures':errors,'repeats':repeats,
        'all_order_checks_passed':not errors and len(measured)==len(evaluation_ids)*(len(config['variants'])+2),
        'ota_representativeness':'NOT_ESTABLISHED','original_full_challenge_result_reproduced':False}
    columns = ['amazon_score','directed_edge_agreement','zone_reentries','normalized_Kendall_inversions','matrix_travel_time_ratio_to_actual']
    for split in ['same_station_future','unknown_station']:
        result = {}
        for method in config['variants']+['NN_time','Actual_reference']:
            own = [r for r in measured if r['split']==split and r['method']==method]
            success = [r for r in own if r['status']=='SCORED']
            result[method] = {'attempts':len(own),'failures':len(own)-len(success),
                **{k:sum(r[k] for r in success)/len(success) if success else None for k in columns}}
        summary['by_split'][split] = result
    lookup = {(r['route_id'],r['method']):r for r in measured if r['status']=='SCORED'}
    summary['paired_score_differences'] = []
    for split in ['same_station_future','unknown_station']:
        for method in config['variants']:
            deltas = [{'route_id':rid,'station':routes[rid]['station_code'],
                'difference_vs_NN':lookup[(rid,method)]['amazon_score']-lookup[(rid,'NN_time')]['amazon_score']}
                for rid in splits[split] if (rid,method) in lookup]
            summary['paired_score_differences'].append({'split':split,'method':method,'values':deltas,
                'mean':sum(r['difference_vs_NN'] for r in deltas)/len(deltas) if deltas else None,
                'inference':'descriptive only; two stations per split; no equivalence or population significance claim'})
    summary['unknown_public_vs_no_history_identical_orders'] = all(
        proposals.get('Cook_public_zones',{}).get(r)==proposals.get('Cook_no_station_history',{}).get(r)
        for r in splits['unknown_station']) if all(v in proposals for v in ['Cook_public_zones','Cook_no_station_history']) else None
    dump(output/'SUMMARY.json',summary)
    return summary


def finalize(data,plan_dir,existing,output,code):
    """Re-score hash-fixed proposals into a new directory; never run a solver."""
    begin=time.perf_counter()
    reg=json.loads((plan_dir/'REGISTRATION.json').read_text())
    before=json.loads((existing/'BEFORE_SCORING.json').read_text())
    for name,key in [('ALL_PROPOSALS_BEFORE_SCORING.json','proposals_sha256'),('model.json','model_sha256')]:
        if digest(existing/name)!=before[key]:
            raise ValueError('SAVED_OUTPUT_CHANGED:'+name)
    env=json.loads((existing/'ENVIRONMENT.json').read_text())
    if any(digest(code/name)!=h for name,h in env['author_tracked_hashes'].items()):
        raise ValueError('AUTHOR_SOURCE_CHANGED')
    if digest(code/'LKH-AMZ/LKH')!=env['binary_sha256']:
        raise ValueError('AUTHOR_BINARY_CHANGED')
    excluded={'METRICS.json','OFFICIAL_SCORER_PARITY.json','SUMMARY.json','RUN_STATUS.json','OUTPUT_HASHES.json','RUN_FAILURE.json'}
    shutil.copytree(existing,output,ignore=lambda directory,names:[n for n in names if n in excluded])
    summary=score_saved_proposals(data,output,reg['config'],reg['split_ids'],
        json.loads((plan_dir/'routes.json').read_text()),json.loads((plan_dir/'selected_times.json').read_text()),
        json.loads((existing/'ALL_PROPOSALS_BEFORE_SCORING.json').read_text()),before['repeats'],before['errors'])
    if (existing/'METRICS.json').exists() and digest(existing/'METRICS.json')!=digest(output/'METRICS.json'):
        raise ValueError('SAVED_METRICS_RECOMPUTATION_DIFFERED')
    calls=json.loads((existing/'PROCESS_CALLS.json').read_text())
    dump(output/'FINALIZATION_PROVENANCE.json',{'source_run':str(existing),'source_proposals_sha256':before['proposals_sha256'],
        'saved_metrics_recalculated_byte_identical':True,'solver_reexecuted':False,
        'inference_script_sha256':reg['script_sha256'],'finalization_script_sha256':digest(Path(__file__))})
    dump(output/'RUN_STATUS.json',{'status':'COMPLETE_FROM_SAVED_PROPOSALS' if not before['errors'] else 'COMPLETE_WITH_FAILURES',
        'original_inference_wall_s':None,'subprocess_wall_s_sum':sum(c['wall_s'] for c in calls),
        'finalization_wall_s':time.perf_counter()-begin,'author_sources_unchanged':True,'main_experiment_eligible':False})
    dump(output/'OUTPUT_HASHES.json',{str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps({'status':'FINALIZED','solver_reexecuted':False,'failures':len(before['errors'])}),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['plan','run','finalize'])
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--code',type=Path)
    parser.add_argument('--author-python',type=Path)
    parser.add_argument('--existing-run',type=Path)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/toc_delivery/a_cook_transfer_v1.json')
    args = parser.parse_args()
    if args.phase=='plan':
        plan(args.data.resolve(),args.output.resolve(),args.config.resolve())
    elif args.phase=='finalize':
        if any(v is None for v in [args.plan,args.code,args.existing_run]):
            parser.error('finalize requires --plan, --code and --existing-run')
        finalize(args.data.resolve(),args.plan.resolve(),args.existing_run.resolve(),args.output.resolve(),args.code.resolve())
    else:
        if any(v is None for v in [args.plan,args.code,args.author_python]):
            parser.error('run requires --plan, --code and --author-python')
        try:
            # Resolving a venv's python symlink would select the base interpreter.
            run(args.data.resolve(),args.plan.resolve(),args.output.resolve(),args.code.resolve(),args.author_python.absolute())
        except Exception as error:
            if args.output.is_dir():
                failure = args.output/'RUN_FAILURE.json'
                if not failure.exists():
                    dump(failure,{'type':type(error).__name__,'error':str(error)})
            raise


if __name__=='__main__':
    main()
