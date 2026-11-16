#!/usr/bin/env python3
"""A_human_v1: time human assignment/order, physical completion, and final review.

Does not generate human choices. Sessions and attempts are append-only.
Use start, manually edit assignment.csv, evaluate, review, then accept.
Synthetic checks never produce an empirical human-inclusive T.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import time

ENTRY = time.monotonic()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
CONFIG = ROOT/'configs/toc_delivery/a_human_v1_20261116.json'


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def read(path):
    def bad(value):raise ValueError('NONFINITE_JSON:'+value)
    return json.loads(Path(path).read_text(),parse_constant=bad)


def dump(path,value):
    with Path(path).open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def boot():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def cpus():
    selected=[];seen=set()
    for cpu in sorted(os.sched_getaffinity(0)):
        p=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key=((p/'physical_package_id').read_text(),(p/'core_id').read_text())
        if key not in seen:selected.append(cpu);seen.add(key)
        if len(selected)==4:return selected
    raise ValueError('FOUR_PHYSICAL_CORES_REQUIRED')


def code_pins():
    freeze=read(ROOT/'configs/toc_delivery/comparison_a_rule_v1_freeze_20261115.json')
    for name,h in freeze['files'].items():
        if digest(ROOT/name)!=h:raise ValueError('FROZEN_A_CHANGED:'+name)
    files=[Path(__file__).resolve(),CONFIG,ROOT/'src/kmd_toc/baseline_a/human_v1.py',
           ROOT/'src/kmd_toc/baseline_a/program.py',ROOT/'src/kmd_toc/baseline_a/program_validation.py',
           ROOT/'src/kmd_toc/frozen_demand.py',ROOT/'src/kmd_toc/frozen_demand_pin.py',
           *sorted((ROOT/'src/kmd_toc/common').glob('*.py'))]
    return {**freeze['files'],**{str(p.relative_to(ROOT)):digest(p) for p in files}}


def verify(meta):
    if boot()!=meta['boot_id']:raise ValueError('CLOCK_BOOT_CHANGED')
    for name,h in meta['source_hashes'].items():
        if digest(ROOT/name)!=h:raise ValueError('SOURCE_CHANGED:'+name)
    cfg=read(CONFIG)
    if digest(ROOT/cfg['physical_config'])!=cfg['physical_sha256']:
        raise ValueError('PHYSICAL_CONFIG_CHANGED')
    return cfg


def events(directory):
    result=[];previous=None
    for i,p in enumerate(sorted((directory/'events').glob('*.json'))):
        if p.name!=f'{i:06}.json':raise ValueError('EVENT_SEQUENCE')
        row=read(p)
        if row['previous_sha256']!=previous:raise ValueError('EVENT_HASH_CHAIN')
        if result and row['at_s']<result[-1]['at_s']:raise ValueError('CLOCK_REVERSED')
        result.append(row);previous=digest(p)
    return result


def append(directory,phase,*,at=None,detail=None):
    old=events(directory)
    row={'phase':phase,'at_s':time.monotonic() if at is None else at,
         'utc':datetime.now(timezone.utc).isoformat(),'detail':detail or {},
         'previous_sha256':digest(directory/'events'/f'{len(old)-1:06}.json') if old else None}
    if old and row['at_s']<old[-1]['at_s']:raise ValueError('CLOCK_REVERSED')
    dump(directory/'events'/f'{len(old):06}.json',row)


def load_input(meta):
    if meta['synthetic']:
        from kmd_toc.common.models import load_problem
        p=load_problem(meta['fixture_input'])
        if p.experiment.kind!='synthetic_validation':raise ValueError('NOT_SYNTHETIC_INPUT')
    else:
        from kmd_toc.baseline_a.rule_inputs import load_input as frozen_input
        p=frozen_input(read(ROOT/read(CONFIG)['frozen_rule_config']),meta['scale'])
    if meta.get('input_hash') is not None and p.fingerprint!=meta['input_hash']:
        raise ValueError('INPUT_CHANGED')
    return p


def bounded_setup(cfg,allocated):
    if not set(allocated)<=os.sched_getaffinity(0):raise ValueError('CPU_ALLOCATION_CHANGED')
    os.sched_setaffinity(0,{allocated[0]})
    amount=cfg['address_space_MiB']*1048576
    resource.setrlimit(resource.RLIMIT_AS,(amount,amount))
    def alarm(*_):raise TimeoutError('PROGRAM_WALL_LIMIT')
    signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,cfg['program_wall_limit_s'])


def start(args):
    if not math.isfinite(args.session_wall_limit_s) or args.session_wall_limit_s<=0:
        raise ValueError('EXPLICIT_POSITIVE_SESSION_LIMIT_REQUIRED')
    if not args.operator.strip():raise ValueError('NAMED_PLANNER_REQUIRED')
    cfg=read(CONFIG);pins=code_pins();allocated=cpus()
    meta={'contract_id':cfg['contract_id'],'implementation_id':cfg['implementation_id'],
          'method_version':cfg['method_version'],'method':'A','operator_id':args.operator,
          'run_id':Path(args.output).name,'scale':args.scale,'boot_id':boot(),
          'source_hashes':pins,'physical_hash':cfg['physical_sha256'],
          'session_wall_limit_s':args.session_wall_limit_s,'allocated_cpu_ids':allocated,
          'input_hash':None,'fixture_input':str(Path(args.fixture_input).resolve()) if args.fixture_input else None,
          'synthetic':bool(args.fixture_input),'phase':'synthetic_functional_check' if args.fixture_input else 'human_measurement',
          'staff_count':1,'attention_independently_observed':False,
          'cache_policy':'fresh command processes; OS cache/shared host load uncontrolled'}
    directory=Path(args.output);directory.mkdir(parents=True,exist_ok=False)
    (directory/'events').mkdir();(directory/'attempts').mkdir()
    append(directory,'PROGRAM',at=ENTRY,detail={'stage':'input_hash_read_and_manual_catalog'})
    try:
        bounded_setup(cfg,allocated)
        p=load_input(meta)
        meta.update(input_hash=p.fingerprint,OD_hash=p.od.fingerprint,scenario_id=p.experiment.scenario_id)
        with (directory/'stops.csv').open('x') as f:
            w=csv.writer(f);w.writerow(['stop_id','longitude','latitude','demand'])
            w.writerows((s.stop_id,s.longitude,s.latitude,s.demand) for s in p.stops)
        dump(directory/'vehicles.json',[asdict(v) for v in p.vehicles])
        with (directory/'assignment.csv').open('x') as f:f.write('vehicle_id,sequence,stop_id\n')
        dump(directory/'SESSION.json',meta)
        append(directory,'HUMAN_PLANNING',detail={'task':'human_vehicle_assignment_and_whole_visit_order',
               'session_sha256':digest(directory/'SESSION.json')})
    except Exception as e:
        signal.setitimer(signal.ITIMER_REAL,0)
        if not (directory/'SESSION.json').exists():dump(directory/'SESSION.json',meta)
        append(directory,'ABANDONED',detail={'reason':type(e).__name__+':'+str(e)})
        finish_result(directory,meta,False,False,error=str(e))
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    print(directory/'assignment.csv')
    return 0


def latest_attempt(directory):
    files=sorted((directory/'attempts').glob('*/result.json'))
    return (files[-1].parent,read(files[-1])) if files else (None,None)


def finish_result(directory,meta,valid,attested,*,error=None):
    from kmd_toc.baseline_a.human_v1 import timing
    value=timing(events(directory),validated=valid,human_attested=attested,synthetic=meta['synthetic'])
    _,attempt=latest_attempt(directory)
    row={**meta,**value,'error':error,'human_authorship_attested':attested,
         'D':attempt['D'] if valid else None,'W':attempt['W'] if valid else None,
         'W_first':attempt['W_first'] if valid else None,'W_reload':attempt['W_reload'] if valid else None,
         'plan_validated':valid,'plan_sha256':attempt['plan_sha256'] if valid else None,
         'program_time_scope':'nonoverlapping tool stages, including input preparation, failed attempts and final checks',
         'person_time_scope':'one planner stage timer; not independent observation of continuous attention'}
    dump(directory/'RESULT.json',row)
    return row


def operate(args):
    directory=Path(args.session);meta=read(directory/'SESSION.json');cfg=verify(meta);log=events(directory)
    registration=next((e['detail']['session_sha256'] for e in log if 'session_sha256' in e['detail']),None)
    if registration!=digest(directory/'SESSION.json'):raise ValueError('SESSION_METADATA_CHANGED')
    if (directory/'RESULT.json').exists() or not log or log[-1]['phase'] in {'FINISHED','ABANDONED'}:
        raise ValueError('SESSION_ALREADY_CLOSED')
    if time.monotonic()-log[0]['at_s']>meta['session_wall_limit_s']:
        append(directory,'ABANDONED',detail={'reason':'SESSION_WALL_LIMIT'})
        finish_result(directory,meta,False,False,error='SESSION_WALL_LIMIT')
        return 1
    phase=log[-1]['phase']
    if args.action=='abort':
        append(directory,'ABANDONED',detail={'reason':args.reason})
        finish_result(directory,meta,False,False,error=args.reason)
        return 1
    if args.action=='mark':
        if phase=='PROGRAM':raise ValueError('UNFINISHED_PROGRAM_STAGE_ABORT_REQUIRED')
        if args.stage=='HUMAN_REVIEW':
            _,r=latest_attempt(directory)
            if not r or not r['validated']:raise ValueError('VALIDATED_PLAN_REQUIRED_FOR_REVIEW')
        append(directory,args.stage,detail={'operator_id':meta['operator_id']})
        return 0
    if args.action=='evaluate':
        if phase not in {'HUMAN_PLANNING','HUMAN_REVIEW'}:raise ValueError('HUMAN_PLANNING_STAGE_REQUIRED')
        append(directory,'PROGRAM',detail={'stage':'manual_completion_and_dual_validation'})
        attempt_dir=directory/'attempts'/f'{len(list((directory/"attempts").iterdir()))+1:04}'
        attempt_dir.mkdir(exist_ok=False)
        row={'validated':False,'D':None,'W':None,'W_first':None,'W_reload':None,
             'plan_sha256':None,'error':None}
        begin=time.monotonic()
        try:
            bounded_setup(cfg,meta['allocated_cpu_ids'])
            from kmd_toc.baseline_a.human_v1 import complete_manual
            p=load_input(meta);manual=(directory/'assignment.csv').read_bytes()
            (attempt_dir/'assignment.csv').write_bytes(manual)
            row['manual_sha256']=hashlib.sha256(manual).hexdigest()
            plan,validation=complete_manual(p,manual.decode('utf-8'))
            dump(attempt_dir/'validation.json',validation)
            dump(attempt_dir/'plan.json',asdict(plan))
            row['validated']=validation['validated']
            row['plan_sha256']=digest(attempt_dir/'plan.json')
            if row['validated']:
                v=validation['common'];row.update(D=v['D_km'],W=v['W_min'],W_first=v['W1_min'],W_reload=v['W2_min'])
            else:row['error']='PHYSICAL_OR_INDEPENDENT_VALIDATION_REJECTED'
        except Exception as e:row['error']=type(e).__name__+':'+str(e)
        finally:signal.setitimer(signal.ITIMER_REAL,0)
        row.update(T_program_attempt=time.monotonic()-begin,cpu_affinity=sorted(os.sched_getaffinity(0)),
                   native_threads=1,max_RSS_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        dump(attempt_dir/'result.json',row)
        append(directory,'HUMAN_REVIEW' if row['validated'] else 'HUMAN_PLANNING',detail={
            'attempt':attempt_dir.name,'validated':row['validated'],'error':row['error']})
        return 0 if row['validated'] else 1
    if args.action=='accept':
        if phase!='HUMAN_REVIEW':raise ValueError('FINAL_HUMAN_REVIEW_REQUIRED')
        if not args.attest_human_assignment_and_order:raise ValueError('HUMAN_AUTHORSHIP_ATTESTATION_REQUIRED')
        attempt_dir,row=latest_attempt(directory)
        if not row or not row['validated']:raise ValueError('VALIDATED_PLAN_REQUIRED')
        append(directory,'PROGRAM',detail={'stage':'final_input_source_plan_integrity_checks','human_approval':True})
        try:
            # Necessary integrity work is inside operational elapsed time.
            bounded_setup(cfg,meta['allocated_cpu_ids'])
            verify(meta)
            if (digest(directory/'assignment.csv')!=row['manual_sha256'] or
                    digest(attempt_dir/'assignment.csv')!=row['manual_sha256'] or
                    digest(attempt_dir/'plan.json')!=row['plan_sha256']):
                raise ValueError('PLAN_CHANGED_AFTER_VALIDATION')
            from kmd_toc.common.models import load_plan
            from kmd_toc.common.validation import validate_plan
            from kmd_toc.baseline_a.program_validation import audit_plan
            p=load_input(meta);plan=load_plan(attempt_dir/'plan.json')
            common,independent=validate_plan(p,plan),audit_plan(p,plan)
            if (not common.feasible or not independent['feasible'] or
                    abs(common.D_km-float(independent['D_km']))>1e-7 or
                    abs(common.W_min-float(independent['W_min']))>1e-7):
                raise ValueError('FINAL_PHYSICAL_VALIDATION')
            if (common.D_km,common.W_min,common.W1_min,common.W2_min)!=(
                    row['D'],row['W'],row['W_first'],row['W_reload']):
                raise ValueError('SAVED_METRICS_CHANGED')
            with (directory/'accepted_plan.json').open('xb') as f:
                f.write((attempt_dir/'plan.json').read_bytes())
            if time.monotonic()-log[0]['at_s']>meta['session_wall_limit_s']:
                raise TimeoutError('SESSION_WALL_LIMIT')
            append(directory,'FINISHED',detail={'human_authorship_attested':True})
        except Exception as e:
            append(directory,'ABANDONED',detail={'reason':str(e)})
            finish_result(directory,meta,False,True,error=str(e))
            return 1
        finally:signal.setitimer(signal.ITIMER_REAL,0)
        result=finish_result(directory,meta,True,True)
        print(json.dumps({k:result[k] for k in ['T','T_human','T_program','T_other','T_reason']},ensure_ascii=False))
        return 0
    raise ValueError('UNKNOWN_ACTION')


def main():
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key]='1'
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('start');kind=p.add_mutually_exclusive_group(required=True)
    kind.add_argument('--scale',choices=['S1','S2','S3']);kind.add_argument('--fixture-input')
    p.add_argument('--operator',required=True);p.add_argument('--output',required=True)
    p.add_argument('--session-wall-limit-s',type=float,required=True)
    for action in ('mark','evaluate','accept','abort'):
        p=sub.add_parser(action);p.add_argument('--session',required=True)
        if action=='mark':p.add_argument('--stage',required=True,choices=['HUMAN_PLANNING','HUMAN_REVIEW','PAUSED'])
        if action=='accept':p.add_argument('--attest-human-assignment-and-order',action='store_true')
        if action=='abort':p.add_argument('--reason',required=True)
    args=parser.parse_args()
    try:return start(args) if args.action=='start' else operate(args)
    except Exception as e:
        print(type(e).__name__+': '+str(e),file=sys.stderr);return 2


if __name__=='__main__':sys.exit(main())
