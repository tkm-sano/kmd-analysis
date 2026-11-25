#!/usr/bin/env python3
"""Read-only classification of saved plans; no optimizer and no source overwrite."""
import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def memory_available():
    import psutil
    available=psutil.virtual_memory().available
    base=Path('/sys/fs/cgroup')
    relative=Path('/proc/self/cgroup').read_text().strip().split('::')[-1].lstrip('/')
    current=base/relative
    while True:
        maximum=current/'memory.max';usage=current/'memory.current'
        if maximum.is_file() and usage.is_file():
            value=maximum.read_text().strip()
            if value.isdigit():available=min(available,max(0,int(value)-int(usage.read_text())))
        if current==base:break
        current=current.parent
    return available


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    out=Path(args.output).resolve()
    if out.exists():raise FileExistsError('AUDIT_OUTPUT_ALREADY_EXISTS')
    out.mkdir(parents=True,exist_ok=False)
    from kmd_toc.common.models import load_problem,load_plan
    from kmd_toc.fcfs_v1.validation import validate_fcfs
    from kmd_toc.fcfs_v1.scheduler import reschedule
    inputs=ROOT/'output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs'
    pilot=ROOT/'output/toc_delivery/non_time_variance_pilot_20261117_v1/runs'
    records=[]
    for directory in sorted(pilot.iterdir()):
        path=directory/'plan.json';result=directory/'RESULT.json'
        if not path.is_file():
            records.append({'path':str(path),'scale':directory.name[:2],'status':'未確認','reason':'saved_plan_missing'})
            continue
        data=json.loads(result.read_text()) if result.exists() else {}
        records.append({'path':str(path),'scale':data.get('case_id',directory.name[:2]),
                        'method':data.get('method'),'experiment':'non_time_variance_pilot_20261117_v1',
                        'source_sha256':digest(path)})
    groups=ROOT/'output/nkr_p2_20261120_v1/groups'
    if groups.is_dir():
        for path in sorted(groups.glob('*/branch_*/plan.json')):
            job=json.loads((path.parent/'JOB.json').read_text())
            records.append({'path':str(path),'scale':job.get('scale'), 'method':'D',
                            'experiment':'nkr_p2_20261120_v1_snapshot','source_sha256':digest(path)})
    # Save enumeration before reading moving progress. A changing file is UNKNOWN.
    (out/'ENUMERATED.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    begin=time.perf_counter();available=memory_available()
    (out/'RESOURCE_CHECK.json').write_text(json.dumps({'available_bytes':available,
        'minimum_required_bytes':768*1024**2,'parallel_planners_started':0,'method':'one scale input at a time'},indent=2)+'\n')
    for scale in ('S1','S2','S3'):
        selected=[r for r in records if r.get('scale')==scale]
        if memory_available()<768*1024**2:
            for row in selected:row.update(status='未確認',reason='memory_safety_gate')
            continue
        p=load_problem(inputs/scale)
        for row in selected:
            if row.get('method')=='A':
                row.update(status='OUT_OF_SCOPE',reason='A_is_external_reference_legacy_A_plan_not_current_A')
                continue
            path=Path(row['path'])
            if not path.exists():continue
            try:
                if digest(path)!=row['source_sha256']:raise ValueError('SOURCE_CHANGED_SINCE_ENUMERATION')
                plan=load_plan(path);check=validate_fcfs(p,plan)
                if digest(path)!=row['source_sha256']:raise ValueError('SOURCE_CHANGED_DURING_AUDIT')
                status='FCFS適合' if check['feasible'] else 'FCFS不適合' if check['physical']['feasible'] else '未確認'
                row.update(status=status,physical_feasible=check['physical']['feasible'],
                           violation_count=len(check['violations']),violations=check['violations'],
                           D_km=check['physical']['D_km'],old_loading_W_min=check['physical']['loading_W_min'],
                           main_experiment_eligible=False,scope='FCFS eligibility only; other main conditions remain HOLD')
                if path.parent.name=='S1_C_pilot_r01':
                    converted=reschedule(p,plan);newcheck=validate_fcfs(p,converted)
                    with (out/'S1_C_r01_CONVERTED_PLAN.json').open('x') as f:
                        json.dump(asdict(converted),f,ensure_ascii=False,indent=2)
                    witness={'source':str(path),'source_sha256':row['source_sha256'],
                             'role':'actually rescheduled fixed-route regression; not optimization performance or a new main trial',
                             'D_unchanged':newcheck['physical']['D_km']==check['physical']['D_km'],
                             'old_loading_W_min':check['physical']['loading_W_min'],
                             'converted_loading_W_min':newcheck['W_loading_min'],
                             'fcfs_feasible':newcheck['feasible'],
                             'old_example':[{'vehicle_id':t.vehicle_id,'trip_no':t.trip_no,'ready_s':t.ready_s,'load_start_s':t.load_start_s,'return_s':t.return_s}
                                            for t in plan.trips if t.vehicle_id in ('v2','v3')],
                             'new_example':[{'vehicle_id':t.vehicle_id,'trip_no':t.trip_no,'ready_s':t.ready_s,'load_start_s':t.load_start_s,'return_s':t.return_s}
                                            for t in converted.trips if t.vehicle_id in ('v2','v3')]}
                    (out/'S1_C_REGRESSION.json').write_text(json.dumps(witness,ensure_ascii=False,indent=2)+'\n')
            except (OSError,ValueError,KeyError) as error:
                row.update(status='未確認',reason=str(error))
            print(json.dumps({'path':str(path.relative_to(ROOT)),'status':row.get('status')},ensure_ascii=False),flush=True)
        del p
    for row in records:
        if 'status' not in row:row.update(status='未確認',reason='scale_or_source_not_resolved')
    from collections import Counter
    summary=dict(Counter(r['status'] for r in records))
    result={'operating_policy':'FCFS_v1','scope':['registered historical 75-run pilot','existing final plan.json in p2 groups at enumeration'],
            'outside_scope':'Other studies and intermediate/unfinished candidates are UNKNOWN, not assumed FCFS compliant.',
            'elapsed_s':time.perf_counter()-begin,'summary':summary,'records':records,
            'main_experiment':'HOLD','no_optimization_or_quantum_jobs_started':True}
    with (out/'CLASSIFICATION.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    fields=['experiment','scale','method','path','source_sha256','status','physical_feasible','violation_count','D_km','old_loading_W_min','reason']
    with (out/'CLASSIFICATION.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(records)
    print(json.dumps({'summary':summary,'main_experiment':'HOLD'},ensure_ascii=False))


if __name__=='__main__':main()
