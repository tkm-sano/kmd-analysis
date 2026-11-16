"""Independent post-run membership/edge/time and author-converter checks."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True,type=Path)
    parser.add_argument('--plan',required=True,type=Path)
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--code',required=True,type=Path)
    parser.add_argument('--author-python',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    reg=json.loads((args.plan/'REGISTRATION.json').read_text())
    routes=json.loads((args.plan/'routes.json').read_text())
    costs=json.loads((args.plan/'selected_times.json').read_text())
    truth=json.loads((args.data/'eval_actual.json').read_text())
    proposals=json.loads((args.run/'ALL_PROPOSALS_BEFORE_SCORING.json').read_text())
    measured=json.loads((args.run/'METRICS.json').read_text())
    checks=[]
    def cycle(order):
        return list(zip(order,order[1:]+order[:1]))
    for row in measured:
        if row['status']!='SCORED':
            checks.append({'route':row['route_id'],'method':row['method'],'passed':False,'reason':'FAILED'})
            continue
        rid,method=row['route_id'],row['method']
        actual=sorted(truth[rid]['actual'],key=truth[rid]['actual'].__getitem__)
        seq=actual if method=='Actual_reference' else proposals[method][rid]
        station=[s for s,v in routes[rid]['stops'].items() if v['type']=='Station']
        assert len(station)==1 and seq[0]==station[0]
        assert len(seq)==len(set(seq))==len(routes[rid]['stops'])
        assert set(seq)==set(routes[rid]['stops'])
        time=sum(costs[rid][a][b] for a,b in cycle(seq))
        actual_time=sum(costs[rid][a][b] for a,b in cycle(actual))
        agreement=len(set(cycle(actual))&set(cycle(seq)))/len(seq)
        assert math.isclose(time,row['matrix_travel_time_s_closed_route'],abs_tol=1e-7)
        assert math.isclose(time/actual_time,row['matrix_travel_time_ratio_to_actual'],abs_tol=1e-12)
        assert math.isclose(agreement,row['directed_edge_agreement'],abs_tol=1e-12)
        checks.append({'route':rid,'method':method,'passed':True})
    # Run the author's own converter separately and compare its directed ordering.
    converter_checks=[]
    for form in reg['config']['formulations']:
        directory=args.run/'Cook_public_zones'/form
        converted=out/(form+'_author_proposed.json')
        command=[str(args.author_python.absolute()),str(args.code/'scripts/tsplib2json.py'),
            '--tour_dir',str(directory.resolve()),'--tsplib2amz_file',str((directory/'tsp2amz.json').resolve()),
            '--out_json',str(converted)]
        with (out/(form+'_converter.log')).open('x') as f:
            subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
        native=json.loads(converted.read_text())
        trace=json.loads((args.run/'Cook_public_zones/SOLVER_TRACES.json').read_text())
        for rid,record in native.items():
            seq=sorted(record['proposed'],key=record['proposed'].__getitem__)
            station=next(s for s,v in routes[rid]['stops'].items() if v['type']=='Station')
            assert seq[0]==station
            selected=trace['selection'][rid]['selected_formulation']==form
            if selected:
                assert seq==proposals['Cook_public_zones'][rid]
            converter_checks.append({'route':rid,'formulation':form,'station_first':True,
                                     'selected':selected,'selected_matches_wrapper':True if selected else None})
    ids=reg['split_ids']
    train_stations={routes[r]['station_code'] for r in ids['training']}
    assert not set(ids['training'])&(set(ids['same_station_future'])|set(ids['unknown_station']))
    assert not train_stations&{routes[r]['station_code'] for r in ids['unknown_station']}
    assert max(routes[r]['date_YYYY_MM_DD'] for r in ids['training']) < min(routes[r]['date_YYYY_MM_DD'] for r in ids['same_station_future'])
    identical_inputs=[]
    for form in reg['config']['formulations']:
        mapping=json.loads((args.run/'Cook_public_zones'/form/'tsp2amz.json').read_text())
        for name,record in mapping.items():
            if record['route_id'] in ids['unknown_station']:
                a=args.run/'Cook_public_zones'/form/(name+'.ctsptw')
                b=args.run/'Cook_no_station_history'/form/(name+'.ctsptw')
                identical_inputs.append({'route':record['route_id'],'formulation':form,
                                        'byte_identical':a.read_bytes()==b.read_bytes()})
    fields=sorted(set().union(*(r.keys() for r in measured)))
    with (out/'METRICS.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(measured)
    write(out/'INDEPENDENT_CHECKS.json',{'membership_edges_time_checks':checks,
        'author_converter_checks':converter_checks,'no_route_or_station_leakage':True,
        'same_station_training_precedes_validation':True,
        'unknown_station_public_vs_history_removed_inputs':identical_inputs,
        'all_passed':all(x['passed'] for x in checks)})
    calls=json.loads((args.run/'PROCESS_CALLS.json').read_text())
    write(out/'RESOURCE_TOTALS.json',{'process_count':len(calls),'process_wall_s_sum':sum(c['wall_s'] for c in calls),
        'timed_out':sum(c.get('timed_out',False) for c in calls),
        'nonzero_return_codes':sum(c.get('returncode',0)!=0 for c in calls),
        'by_label':{label:{'count':sum(c['label'].startswith(label) for c in calls),
            'wall_s':sum(c['wall_s'] for c in calls if c['label'].startswith(label))} for label in reg['config']['variants']},
        'includes_unselected_formulations_and_repeats':True})
    write(out/'INPUT_HASHES.json',{'registration':sha(args.plan/'REGISTRATION.json'),
        'metrics':sha(args.run/'METRICS.json'),'proposals':sha(args.run/'ALL_PROPOSALS_BEFORE_SCORING.json'),
        'truth':sha(args.data/'eval_actual.json'),'audit_code':sha(Path(__file__))})
    print(json.dumps({'checks':len(checks),'converter_routes':len(converter_checks),
                      'all_passed':all(x['passed'] for x in checks)}))


if __name__=='__main__':
    main()
