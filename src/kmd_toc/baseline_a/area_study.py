"""Calibrate A-area candidates and test once at previously unused stations."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np

from .area import local_xy, ordered_nodes
from .sequence_validation import (ROOT, digest, dump, iter_json_object, ranked, route_ids,
    time_matrix, geographic_matrix, actual_order, official_normalization, metrics)

CONFIG = ROOT/'configs/toc_delivery/a_area_v3.json'
CONFIG_SHA256 = '70080f36a2404a5e7533a31d8bd81cd8e8260368da721d937b9aa180a36e6f94'


def settings():
    if digest(CONFIG) != CONFIG_SHA256:
        raise ValueError('AREA_V3_SETTINGS_HASH')
    return json.loads(CONFIG.read_text())


def split_metadata(metadata, prior_ids, config, prior_pilot_rows=()):
    prior_stations = {metadata[r]['station_code'] for r in prior_ids} | {r['station_code'] for r in prior_pilot_rows}
    prior_groups = ({(metadata[r]['station_code'],metadata[r]['date_YYYY_MM_DD']) for r in prior_ids} |
                    {(r['station_code'],r['date_YYYY_MM_DD']) for r in prior_pilot_rows})
    eligible, excluded = defaultdict(lambda:defaultdict(list)), []
    for rid, row in metadata.items():
        try:
            route_ids(row)
        except (ValueError,TypeError,KeyError) as error:
            excluded.append({'route_id':rid,'reason':str(error)})
            continue
        station, day = row['station_code'], row['date_YYYY_MM_DD']
        if (station,day) not in prior_groups:
            eligible[station][day].append(rid)
    result = {'prior_ids':list(prior_ids), 'prior_station_days':[list(x) for x in sorted(prior_groups)],
              'excluded_metadata':excluded, 'calibration':[], 'validation':[]}
    for split in ['calibration','validation']:
        pool = [s for s in eligible if (s in prior_stations) == (split=='calibration')]
        stations = sorted(pool,key=lambda s:ranked(config['seed'],split,s))[:config['split'][split+'_stations']]
        for station in stations:
            days = sorted(eligible[station],key=lambda d:ranked(config['seed'],split,station,d))[:config['split']['dates_per_station']]
            for day in days:
                result[split] += sorted(eligible[station][day],key=lambda r:ranked(config['seed'],split,r))[:config['split']['routes_per_date']]
    cs = {metadata[r]['station_code'] for r in result['calibration']}
    vs = {metadata[r]['station_code'] for r in result['validation']}
    if not cs or not vs or cs & vs or set(prior_ids) & (set(result['calibration'])|set(result['validation'])):
        raise ValueError('AREA_SPLIT_LEAKAGE_OR_EMPTY')
    result['calibration_stations'],result['validation_stations'] = sorted(cs),sorted(vs)
    result['station_disjoint'] = True
    return result


def candidates(config):
    result = [{'id':'NN','kind':'NN','leaf_capacity':None,'stay_factor':None}]
    for k in config['candidates']['leaf_capacities']:
        for f in config['candidates']['stay_factors']:
            result.append({'id':f'area_k{k}_stay{f if f is not None else "all"}',
                           'kind':'area','leaf_capacity':k,'stay_factor':f})
    return result


def route_xy(ids, route):
    return local_xy([route['stops'][s]['lng'] for s in ids], [route['stops'][s]['lat'] for s in ids],
                    route['stops'][ids[0]]['lng'],route['stops'][ids[0]]['lat'])


def propose(ids, matrix, route, parameters, *, supplied=False, geographic=False):
    xy = route_xy(ids,route)
    costs = geographic_matrix(ids,route) if geographic else matrix
    labels = {j:route['stops'][s].get('zone_id') for j,s in enumerate(ids) if j} if supplied else None
    order,trace = ordered_nodes(range(1,len(ids)),costs,xy,ids,parameters,labels)
    return [ids[0],*[ids[j] for j in order]],trace


def fit_loss(measured, actual_metrics):
    if measured['zone_reentries_per_dropoff'] is None or actual_metrics['zone_reentries_per_dropoff'] is None:
        raise ValueError('NO_KNOWN_ZONE_FOR_CALIBRATION')
    ratio = measured['matrix_travel_time_ratio_to_actual']
    if ratio is None or ratio <= 0:
        raise ValueError('CALIBRATION_TIME_RATIO_UNDEFINED')
    return (measured['amazon_score'] +
            abs(measured['zone_reentries_per_dropoff']-actual_metrics['zone_reentries_per_dropoff']) +
            abs(math.log(ratio)))/3


def choose(rows, parameters):
    losses = defaultdict(lambda:defaultdict(list))
    for row in rows:
        if row['status'] == 'SCORED':
            losses[row['method']][(row['station_code'],row['date'])].append(row['fit_loss'])
    scores = {}
    expected = len({r['route_id'] for r in rows})
    for p in parameters:
        own = [r for r in rows if r['method']==p['id']]
        if len(own)!=expected or any(r['status']!='SCORED' for r in own):
            scores[p['id']] = {'eligible':False,'reason':'missing or failed calibration row'}
        else:
            scores[p['id']] = {'eligible':True,'loss':float(np.mean([np.mean(v) for v in losses[p['id']].values()])),
                              'routes':len(own),'station_days':len(losses[p['id']])}
    def complexity(p):
        return (0,0,0) if p['kind']=='NN' else (1,p['leaf_capacity'],p['stay_factor'] or float('inf'))
    def pick(pool):
        feasible = [p for p in pool if scores[p['id']]['eligible']]
        if not feasible:
            raise ValueError('NO_VALID_CALIBRATION_CANDIDATE')
        best = min(scores[p['id']]['loss'] for p in feasible)
        return min((p for p in feasible if scores[p['id']]['loss']<=best+1e-12),key=complexity)
    return pick(parameters),pick([p for p in parameters if p['kind']=='area']),scores


def describe(rows, config):
    result = {'attempts':len(rows),'failures':sum(r['status']!='SCORED' for r in rows),'methods':{},'contrasts':{}}
    columns = ['amazon_score','directed_edge_agreement','zone_reentries','zone_reentries_per_dropoff',
               'matrix_travel_time_ratio_to_actual','normalized_Kendall_inversions','fit_loss']
    for method in sorted({r['method'] for r in rows}):
        own = [r for r in rows if r['method']==method]
        record = {'attempts':len(own),'failures':sum(r['status']!='SCORED' for r in own)}
        for key in columns:
            values = [r[key] for r in own if r['status']=='SCORED' and r[key] is not None]
            record[key] = {'n':len(values),'mean':float(np.mean(values)) if values else None,
                           'median':float(np.median(values)) if values else None}
        result['methods'][method] = record
    lookup = {(r['route_id'],r['method']):r for r in rows if r['status']=='SCORED'}
    for method in ['Selected_auto_time','Best_area_auto_time','Best_area_supplied_time','Best_area_auto_geo']:
        per_station = defaultdict(list)
        for row in rows:
            if row['method']!=method or row['status']!='SCORED':
                continue
            ref = lookup.get((row['route_id'],'NN_time'))
            if ref:
                per_station[row['station_code']].append(row['fit_loss']-ref['fit_loss'])
        means = np.array([np.mean(v) for v in per_station.values()])
        if len(means)>1:
            rng = np.random.default_rng(config['seed'])
            boot = rng.choice(means,size=(config['bootstrap_repetitions'],len(means)),replace=True).mean(axis=1)
            low,high = np.quantile(boot,[.025,.975])
            result['contrasts'][method] = {'stations':len(means),'mean_station_loss_difference':float(means.mean()),
                'descriptive_95_interval':[float(low),float(high)],'improvement_supported_on_sample':bool(high<0),
                'equivalent_to_operations':None,'primary':method=='Selected_auto_time'}
    result['full_representativeness'] = 'NOT_ESTABLISHED'
    return result


def run(data_root, output):
    config = settings()
    out = Path(output)
    out.mkdir(parents=True,exist_ok=False)
    start = time.perf_counter()
    def check():
        if time.perf_counter()-start>config['limits']['analysis_wall_s']:
            raise TimeoutError('AREA_STUDY_TIME_LIMIT')
    source = [Path(__file__),ROOT/'src/kmd_toc/baseline_a/area.py',CONFIG]
    code_hashes = {str(p.relative_to(ROOT)):digest(p) for p in source}
    dump(out/'REGISTRATION.json',{'timestamp':datetime.now(timezone.utc).isoformat(),'config':config,
        'config_sha256':CONFIG_SHA256,'source_hashes':code_hashes,'validation_outcomes_used':False})
    rows = []
    try:
        data = Path(data_root)
        manifest = json.loads((data/'MANIFEST.json').read_text())
        for name,record in manifest['files'].items():
            if digest(data/name)!=record['sha256']:
                raise ValueError('AREA_INPUT_HASH:'+name)
        check()
        dump(out/'INPUT_MANIFEST.json',manifest)
        metadata = json.loads((data/'eval_routes.json').read_text())
        previous = json.loads((ROOT/config['prior_selection']).read_text())
        prior = previous['eval']
        pilot_metadata = json.loads((data/'pilot_routes.json').read_text())
        split = split_metadata(metadata,prior,config,[pilot_metadata[r] for r in previous['pilot']])
        dump(out/'SPLIT.json',split)
        selected = set(split['calibration']+split['validation'])
        problems = {}
        for rid,raw in iter_json_object(data/'eval_times.json'):
            check()
            if rid in selected:
                ids = route_ids(metadata[rid])
                matrix = time_matrix(ids,raw)
                problems[rid] = (ids,matrix,metadata[rid])
        if set(problems)!=selected:
            raise ValueError('AREA_MATRIX_COVERAGE')
        calibration_actual = {rid:row for rid,row in iter_json_object(data/'eval_actual.json') if rid in set(split['calibration'])}
        params = candidates(config)
        calibration_proposals = {}
        for rid in split['calibration']:
            ids,matrix,route = problems[rid]
            actual = actual_order(calibration_actual[rid],ids)
            normalized = official_normalization(matrix)
            actual_metrics = metrics(ids,actual,actual,matrix,route,normalized)
            calibration_proposals[rid] = {}
            for p in params:
                check()
                row = {'split':'calibration','route_id':rid,'station_code':route['station_code'],
                       'date':route['date_YYYY_MM_DD'],'method':p['id']}
                try:
                    sequence,trace = propose(ids,matrix,route,p)
                    calibration_proposals[rid][p['id']] = sequence
                    measured = metrics(ids,sequence,actual,matrix,route,normalized)
                    row.update(measured,fit_loss=fit_loss(measured,actual_metrics),status='SCORED')
                except Exception as error:
                    row.update(status='FAILED',error=str(error))
                rows.append(row)
        dump(out/'CALIBRATION_PROPOSALS.json',calibration_proposals)
        dump(out/'CALIBRATION_METRICS.json',rows)
        winner,best_area,scores = choose(rows,params)
        model = {'version':config['version'],'selected_parameters':winner,'best_area_parameters':best_area,
                 'calibration_scores':scores,'config_sha256':CONFIG_SHA256,
                 'split_sha256':digest(out/'SPLIT.json'),'calibration_metric_sha256':digest(out/'CALIBRATION_METRICS.json'),
                 'calibration_routes':len(split['calibration']),'validation_outcomes_used_for_selection':False,
                 'road_distance_validated':False,'full_representativeness_PASS':False,
                 'fit_criterion_is_research_assumption':True}
        dump(out/'SELECTED_MODEL.json',model)
        proposals,decision_traces = {},{}
        for rid in split['validation']:
            ids,matrix,route = problems[rid]
            comparisons = [('NN_time',params[0],False,False),('Selected_auto_time',winner,False,False),
                ('Best_area_auto_time',best_area,False,False),('Best_area_supplied_time',best_area,True,False),
                ('Best_area_auto_geo',best_area,False,True),('NN_geo',params[0],False,True)]
            proposals[rid],decision_traces[rid] = {},{}
            for name,p,supplied,geo in comparisons:
                sequence,trace = propose(ids,matrix,route,p,supplied=supplied,geographic=geo)
                proposals[rid][name] = sequence
                decision_traces[rid][name] = trace
        dump(out/'VALIDATION_PROPOSALS.json',proposals)
        dump(out/'AREA_DECISION_TRACES.json',decision_traces)
        dump(out/'BEFORE_VALIDATION_OUTCOMES.json',{'selected_model_sha256':digest(out/'SELECTED_MODEL.json'),
            'validation_proposals_sha256':digest(out/'VALIDATION_PROPOSALS.json'),
            'validation_outcomes_used':False,'elapsed_s':time.perf_counter()-start})
        validation_actual = {rid:row for rid,row in iter_json_object(data/'eval_actual.json') if rid in set(split['validation'])}
        validation_rows = []
        for rid in split['validation']:
            ids,matrix,route = problems[rid]
            actual = actual_order(validation_actual[rid],ids)
            normalized = official_normalization(matrix)
            reference = metrics(ids,actual,actual,matrix,route,normalized)
            sequences = {**proposals[rid],'Actual':actual}
            for method,sequence in sequences.items():
                check()
                row = {'split':'validation','route_id':rid,'station_code':route['station_code'],
                       'date':route['date_YYYY_MM_DD'],'method':method,'dropoffs':len(ids)-1}
                try:
                    measured = metrics(ids,sequence,actual,matrix,route,normalized)
                    row.update(measured,fit_loss=fit_loss(measured,reference),status='SCORED')
                except Exception as error:
                    row.update(status='FAILED',error=str(error))
                validation_rows.append(row)
        dump(out/'VALIDATION_METRICS.json',validation_rows)
        dump(out/'SUMMARY.json',describe(validation_rows,config))
        import csv
        fields = sorted({k for r in rows+validation_rows for k in r})
        with (out/'ALL_METRICS.csv').open('x',newline='') as stream:
            writer = csv.DictWriter(stream,fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows+validation_rows)
        dump(out/'RUN_STATUS.json',{'status':'COMPLETE','elapsed_s':time.perf_counter()-start,
            'calibration_routes':len(split['calibration']),'validation_routes':len(split['validation']),
            'source_stable':all(digest(ROOT/p)==h for p,h in code_hashes.items()),
            'main_experiment_eligible':False})
    except Exception as error:
        dump(out/'FAILURE.json',{'type':type(error).__name__,'message':str(error),'elapsed_s':time.perf_counter()-start})
        raise
    finally:
        dump(out/'OUTPUT_HASHES.json',{p.name:digest(p) for p in out.iterdir() if p.is_file()})
    return model
