"""Registered finite-work trials, fresh children and all-branch collection."""
import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tarfile
import time
import traceback
from .work import Ledger,key
from kmd_toc.comparison_v1.contract import ROOT,TIME_KIND,read,digest,dump,atomic,fingerprint,input_inventory,check_freeze,check_profile

CONFIG=ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json'


def validate_config(c):
    if c.get('mode')!='finite_work':raise ValueError('FINITE_MODE_REQUIRED')
    prohibited={'timeout','deadline','time_limit','max_time_in_seconds','max_deterministic_time','tau_s','budget_wall_s','native_cap_s','lns_time_limit'}
    def walk(v):
        if isinstance(v,dict):
            if prohibited.intersection(v):raise ValueError('TIME_STOP_FORBIDDEN')
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(c)
    if c['resource']!={'physical_cores':4,'BCD_branches':4,'native_threads':1,'tree_RSS_limit_MiB':32768,'A_address_space_MiB':4096}:raise ValueError('RESOURCE_CONTRACT_CHANGED')
    for section,names in [('A',['candidate_evaluations']),('C',['search_limit_checks_per_stop','minimum_search_limit_checks']),
        ('completion',['max_conflicts_per_internal_solve','max_improving_solutions']),
        ('D',['train_shots','final_shots','p','macro_groups','max_evaluations','restarts','pricing_rounds']),
        ('catalogue',['column_generation_rounds','new_columns_per_round','LP_min_iterations','LP_iterations_per_row_column','IP_nodes_per_vehicle'])]:
        if any(type(c[section][k]) is not int or c[section][k]<1 for k in names):raise ValueError('FINITE_POSITIVE_OPERATION_LIMIT_REQUIRED')
    if c['catalogue']['new_columns_per_round']!=20:raise ValueError('INHERITED_CG_ADDITION_LIMIT_IS_20')
    if c['D']['train_shots']!=10000 or c['D']['final_shots']!=10000:raise ValueError('SHOTS_CONTRACT')
    return c


def code_files():
    return sorted(p for base in ('src/kmd_toc','scripts','tests/toc_termination_v1') for p in (ROOT/base).rglob('*.py'))+[ROOT/'docs/research/termination_rules_20261116_v1/STOPPING_RULES.md',CONFIG,ROOT/'configs/toc_delivery/common_conditions_v1_1.json',ROOT/'configs/toc_delivery/comparison_a_rule_v1_freeze_20261115.json',ROOT/'configs/toc_delivery/a_rule_v1_20261115.json',ROOT/'configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json']


def register(out,fixture=False):
    from kmd_toc.dwt.parallel import cpu_profile,branch_seeds
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    c=validate_config(read(CONFIG));check_freeze()
    profile=cpu_profile(read(ROOT/'configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json'))
    check_profile(profile['cpu_ids'])
    if fixture:
        from kmd_toc.baseline_a.fixtures import artificial_problem
        from kmd_toc.common.models import save_problem
        save_problem(artificial_problem(12,4,1),out/'fixture')
        cases=[{'case_id':'tiny','scale':'tiny','input':input_inventory(out/'fixture')}]
    else:
        a=read(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json')
        cases=[]
        for s in c['scales']:
            pinned=a['inputs']['scenarios'][s]
            inv=input_inventory(ROOT/a['inputs']['input_root']/s)
            if inv['files']!=pinned['files']:raise ValueError('FROZEN_INPUT_CHANGED:'+s)
            cases.append({'case_id':s,'scale':s,'input':inv})
    runs=[]
    import numpy as np
    for case_index,case in enumerate(cases):
        for method_index,m in enumerate(c['methods']):
            seed=np.random.SeedSequence([c['root_seed'],case_index,method_index]).generate_state(2)
            seeds={'solver_seed':int(seed[0])%(2**31-1),'quantum_seed':int(seed[1])}
            branches=[{'solver_seed':None,'quantum_seed':None}] if m=='A' else branch_seeds(seeds,4)
            runs.append({'run_id':case['case_id']+'_'+m+'_check01','case_id':case['case_id'],'method':m,
                         'seeds':seeds if m!='A' else {'solver_seed':None,'quantum_seed':None},'branches':branches})
    sources={str(p.relative_to(ROOT)):digest(p) for p in code_files()}
    with tarfile.open(out/'SOURCE_SNAPSHOT.tar.gz','w:gz') as archive:
        for name in sources:archive.add(ROOT/name,arcname=name)
    manifest={'experiment_id':c['experiment_id'],'phase':'small_fixture' if fixture else 'scale_functional_check',
        'executable':True,'statistical_trial_count_note':'one operational check per scale and method; internal branches are NOT independent repeats',
        'contract_id':'whole-method-finite-work-v1','config':c,'config_hash':digest(CONFIG),
        'T_kind':TIME_KIND,'cpu_profile':profile,'cases':cases,'runs':runs,'source_hashes':sources,
        'snapshot_sha256':digest(out/'SOURCE_SNAPSHOT.tar.gz'),'physical_hash':digest(ROOT/'configs/toc_delivery/common_conditions_v1_1.json'),
        'termination_rules':'docs/research/termination_rules_20261116_v1/STOPPING_RULES.md',
        'stopping':'execute each registered run once, all registered branch procedures; never significance or elapsed-time stopping',
        'selection':'validated rounded D(0.1m), W(seconds), branch_id; all branch outcomes recovered',
        'main_experiment':{'executable':False,'R_a':None,'h_D':None,'reason':'new-setting variance and research precision remain outside this task'},
        'environment':{'python':sys.executable,'python_version':sys.version,'dependency_prefix':c['dependency_prefix']},
        'registered_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
    dump(out/'REGISTERED.json',manifest)
    print(json.dumps({'registered':str(out),'trials':len(runs),'config_hash':manifest['config_hash']}),flush=True)


def branch_entry(job_path):
    job=read(job_path);out=Path(job['out']);c=job['config'];os.sched_setaffinity(0,{job['cpu']})
    start=time.perf_counter();cpu=time.process_time();ledger=Ledger(out/'stages')
    result={'branch_id':job['branch_id'],'pid':os.getpid(),'cpu_affinity':sorted(os.sched_getaffinity(0)),
        'seeds':job['seeds'],'execution_state':'NORMAL','algorithm_termination':None,'plan_state':'NO_PLAN',
        'adoptable':False,'plan_sha256':None,'error':None,'proof':None}
    try:
        if job['method']=='A':
            size=c['resource']['A_address_space_MiB']*1024**2;resource.setrlimit(resource.RLIMIT_AS,(size,size))
        from kmd_toc.common.models import load_problem,save_plan
        from kmd_toc.comparison_v1.execution import physical_checks
        from .methods import generate
        p=load_problem(job['input']['directory'])
        if p.fingerprint!=job['input']['input_hash'] or p.od.fingerprint!=job['input']['OD_hash']:raise ValueError('CHILD_INPUT_HASH_MISMATCH')
        ledger.emit('input_loaded',input_hash=p.fingerprint,OD_hash=p.od.fingerprint)
        plan=generate(p,job['method'],c,ledger,job['seeds'])
        valid,checks=physical_checks(p,plan,job['method']);ledger.capture('final_double_checks',checks)
        result.update(plan_state='VALID' if valid else 'INVALID',adoptable=valid,
                      algorithm_termination='CONSTRUCTION_COMPLETE')
        if valid:
            save_plan(plan,out/'plan.json');result.update(plan_sha256=digest(out/'plan.json'),D=checks['common_physical']['D_km'],W=checks['common_physical']['W_min'],
                final_candidate_source=plan.method_settings.get('completion_selected_source','A_rule_v1_FCFS'))
    except Exception as e:
        traceback.print_exc()
        # A legitimate finite search without a plan is a completed procedure, not an infeasibility certificate.
        if isinstance(e,ValueError) and str(e)=='NO_VERIFIED_COMMON_COMPLETION':
            result.update(algorithm_termination='SEARCH_EXHAUSTED',error={'type':type(e).__name__,'message':str(e)})
        else:result.update(execution_state='RESOURCE_STOP' if isinstance(e,MemoryError) else 'ERROR',error={'type':type(e).__name__,'message':str(e)})
    finally:
        result.update(counts=ledger.counts,wall_s=time.perf_counter()-start,
            cpu_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            cpu_after_entry_s=time.process_time()-cpu,
            max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            observed_threads=int(next(s.split(':')[1] for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('Threads:'))))
        dump(out/'RESULT.json',result)


class Interruption(Exception):
    pass


def stop_owned(process):
    # Only used for explicit user/external cancellation or RSS overrun, never normal algorithm stopping.
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    process.wait()


def select_candidates(p,method,branches,root):
    from kmd_toc.common.models import load_plan
    from kmd_toc.comparison_v1.execution import physical_checks
    candidates=[];checks=[]
    for b in sorted(branches,key=lambda x:x['branch_id']):
        path=Path(root)/f"branch_{b['branch_id']:02d}"/'plan.json'
        if not b.get('adoptable') or not path.exists():continue
        if digest(path)!=b['plan_sha256']:raise ValueError('BRANCH_PLAN_TRANSFER_HASH_MISMATCH')
        plan=load_plan(path)
        if plan.method_id!=('B' if method=='D_CLASSICAL_REPLACEMENT' else method):raise ValueError('BRANCH_METHOD_MISMATCH')
        good,a=physical_checks(p,plan,method);checks.append({'branch_id':b['branch_id'],'checks':a})
        if good:candidates.append((key(plan),b['branch_id'],plan,path))
    candidates.sort(key=lambda v:(v[0],v[1]))
    if not candidates:return None,checks
    selected=candidates[0]
    good,again=physical_checks(p,selected[2],method);checks.append({'selected_repeat_check':selected[1],'checks':again})
    if not good:raise ValueError('SELECTED_FINAL_DOUBLE_CHECK_FAILED')
    return selected,checks


def execute(manifest,run,out):
    from kmd_toc.common.models import load_problem
    from kmd_toc.comparison_v1.telemetry import tree_sample
    from kmd_toc.comparison_v1.execution import auxiliary
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    atomic(out/'STARTED.json',run)
    case=next(x for x in manifest['cases'] if x['case_id']==run['case_id']);c=manifest['config']
    row={**run,'contract_id':manifest['contract_id'],'experiment_id':manifest['experiment_id'],'phase':manifest['phase'],
        'scale':case['scale'],'input_hash':case['input']['input_hash'],'OD_hash':case['input']['OD_hash'],
        'config_hash':manifest['config_hash'],'T_kind':TIME_KIND,'physical_hash':manifest['physical_hash'],
        'input_state':'NOT_CHECKED','execution_state':'NORMAL','algorithm_termination':None,
        'plan_state':'NO_PLAN','validation_state':'NOT_RUN','adoptable':False,'D':None,'W':None,'T_program':None,
        'T_attempt':None,'J':None,'J_reason':'A_REFERENCE_PLAN_MISSING','error':None,'branches':[],
        'target_definition':None,'target_arrival_s':None,'target_met_at_end':None,'target_status':'NO_NEW_QUALITY_TARGET_REGISTERED'}
    start=time.perf_counter();cpu=time.process_time();processes=[];logs=[];peak=0;input_end=None;planning_end=None;validation_end=None
    handlers={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(sig,*_):raise Interruption('USER_CANCELLED' if sig==signal.SIGINT else 'EXTERNAL_INTERRUPTION')
    for s in handlers:signal.signal(s,interrupted)
    try:
        check_profile(manifest['cpu_profile']['cpu_ids']);check_freeze()
        for name,h in manifest['source_hashes'].items():
            if digest(ROOT/name)!=h:raise ValueError('REGISTERED_SOURCE_CHANGED:'+name)
        if digest(CONFIG)!=manifest['config_hash']:raise ValueError('REGISTERED_CONFIG_CHANGED')
        for name,h in case['input']['files'].items():
            if digest(Path(case['input']['directory'])/name)!=h:raise ValueError('REGISTERED_INPUT_CHANGED:'+name)
        p=load_problem(case['input']['directory']);row['input_state']='VALID';input_end=time.perf_counter()
        for i,seeds in enumerate(run['branches']):
            directory=out/f'branch_{i:02d}';directory.mkdir()
            job={'out':str(directory.resolve()),'input':case['input'],'method':run['method'],'branch_id':i,
                'seeds':seeds,'config':c,'cpu':manifest['cpu_profile']['cpu_ids'][i]}
            dump(directory/'JOB.json',job)
            log=(directory/'execution.log').open('x');logs.append(log)
            env={**os.environ,'PYTHONPATH':c['dependency_prefix']+':'+str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
                 'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'}
            process=subprocess.Popen([sys.executable,'-B','-m','kmd_toc.termination_v1.runner','child',str(directory/'JOB.json')],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            processes.append(process)
        next_sample=0.
        while True:
            if time.perf_counter()>=next_sample:
                samples=[tree_sample(proc.pid) for proc in processes if proc.poll() is None]
                total=sum(s['tree_rss_sum_KiB'] for s in samples);peak=max(peak,total)
                with (out/'RESOURCE_SAMPLES.jsonl').open('a') as stream:
                    stream.write(json.dumps({'elapsed_s':time.perf_counter()-start,'tree_rss_sum_KiB':total,'branches':samples})+'\n')
                next_sample=time.perf_counter()+.5
                if total>c['resource']['tree_RSS_limit_MiB']*1024:raise MemoryError('REGISTERED_TREE_RSS_LIMIT')
            if all(proc.poll() is not None for proc in processes):break
            time.sleep(.01) # notification and RSS polling only, never a run deadline
        for process in processes:process.wait()
        planning_end=time.perf_counter()
        for i,process in enumerate(processes):
            path=out/f'branch_{i:02d}'/'RESULT.json'
            b=read(path) if path.exists() else {'branch_id':i,'pid':process.pid,'execution_state':'ERROR','plan_state':'NO_PLAN',
                'adoptable':False,'error':{'message':'CHILD_EXIT_WITHOUT_RESULT','returncode':process.returncode},'counts':{}}
            if process.returncode!=0:b.update(execution_state='EXTERNAL_INTERRUPTION' if process.returncode<0 else 'ERROR',adoptable=False,returncode=process.returncode)
            row['branches'].append(b)
        selected,checks=select_candidates(p,run['method'],row['branches'],out)
        dump(out/'PHYSICAL_CHECKS.json',checks)
        if selected is not None:
            _,branch_id,plan,path=selected
            # Transport bytes and all parent checks complete within T.
            (out/'plan.json').write_bytes(path.read_bytes());aux=auxiliary(p,plan)
            a=checks[-1]['checks']['common_physical']
            row.update(adoptable=True,plan_state='VALID',validation_state='VALIDATED',D=a['D_km'],W=a['W_min'],
                W_first=a['W1_min'],W_reload=a['W2_min'],selected_branch_id=branch_id,plan_sha256=digest(out/'plan.json'),
                final_candidate_source=row['branches'][branch_id].get('final_candidate_source'))
            dump(out/'AUXILIARY.json',aux)
        elif any(b['plan_state']=='INVALID' for b in row['branches']):row.update(plan_state='INVALID',validation_state='INVALID_PLAN')
        else:row['validation_state']='NO_PLAN'
        row['algorithm_termination']='CONSTRUCTION_COMPLETE' if any(b['execution_state']=='NORMAL' for b in row['branches']) else None
        if all(b['execution_state']!='NORMAL' for b in row['branches']):
            states={b['execution_state'] for b in row['branches']}
            row['execution_state']='RESOURCE_STOP' if states=={'RESOURCE_STOP'} else ('EXTERNAL_INTERRUPTION' if states=={'EXTERNAL_INTERRUPTION'} else 'ERROR')
        validation_end=time.perf_counter()
    except Interruption as e:row.update(execution_state=str(e),error=str(e))
    except MemoryError as e:row.update(execution_state='RESOURCE_STOP',error=str(e))
    except BaseException as e:
        traceback.print_exc();row.update(execution_state='ERROR',error={'type':type(e).__name__,'message':str(e)})
    finally:
        if any(proc.poll() is None for proc in processes):
            for proc in processes:stop_owned(proc)
        for log in logs:log.close()
        for s,h in handlers.items():signal.signal(s,h)
        # Keep every launched branch, including interrupted or result-less branches.
        if len(row['branches'])<len(processes):
            row['branches']=[]
            for i,proc in enumerate(processes):
                f=out/f'branch_{i:02d}'/'RESULT.json'
                row['branches'].append(read(f) if f.exists() else {'branch_id':i,'pid':proc.pid,'execution_state':row['execution_state'],
                    'plan_state':'NO_PLAN','adoptable':False,'returncode':proc.returncode,'counts':None})
        end=time.perf_counter();row['T_attempt']=end-start
        if row['adoptable'] and row['execution_state']=='NORMAL':row['T_program']=end-start
        else:row.update(adoptable=False,D=None,W=None,T_program=None)
        row.update(T_input=input_end-start if input_end else None,T_planning=planning_end-input_end if planning_end and input_end else None,
            T_final_processing=validation_end-planning_end if planning_end and validation_end else None,
            parent_cpu_s=time.process_time()-cpu,parent_RSS_highwater_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            sampled_tree_peak_RSS_KiB=peak,CPU_s_branches=sum(b['cpu_s'] for b in row['branches']) if all('cpu_s' in b for b in row['branches']) and row['branches'] else None,
            memory_measurement='RSS sum sampled every 0.5s, branch and parent highwater separately; shared pages double counted; CPU partial if interrupted')
        atomic(out/'RESULT.json',row)
    print(json.dumps({k:row.get(k) for k in ('run_id','execution_state','algorithm_termination','adoptable','D','W','T_attempt')},ensure_ascii=False),flush=True)
    return row


def aggregate(root):
    root=Path(root);m=read(root/'REGISTERED.json');rows=[]
    for run in m['runs']:
        f=root/'runs'/run['run_id']/'RESULT.json'
        rows.append(read(f) if f.exists() else {**run,'execution_state':'NOT_STARTED','adoptable':False,'D':None,'W':None,'T_program':None,'T_attempt':None,'branches':[]})
    for case in m['cases']:
        own=[r for r in rows if r['case_id']==case['case_id']];a=next(r for r in own if r['method']=='A')
        for r in own:
            reason='DEFINED'
            if not r['adoptable']:reason='TARGET_PLAN_INVALID'
            elif not a['adoptable']:reason='REFERENCE_TRIAL_FAILED'
            elif any(a[k]==0 for k in ('D','W','T_program')):reason='ZERO_REFERENCE_DENOMINATOR'
            r['J']=math.fsum(r[k]/a[k] for k in ('D','W','T_program'))/3 if reason=='DEFINED' else None
            r['J_reason']=reason;r['J_reference']='single preregistered A functional-check run per scale; NOT a formal timing reference'
    atomic(root/'ALL_RESULTS.json',rows)
    return rows


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['register','register-fixture','run','aggregate','child']);parser.add_argument('path');args=parser.parse_args()
    if args.action=='child':branch_entry(args.path);return
    if args.action.startswith('register'):register(args.path,args.action=='register-fixture');return
    if args.action=='aggregate':aggregate(args.path);return
    root=Path(args.path).resolve();m=read(root/'REGISTERED.json');validate_config(m['config'])
    if not m['executable'] or m['phase'] not in ('small_fixture','scale_functional_check'):raise ValueError('MAIN_EXPERIMENT_NOT_AUTHORIZED')
    # Uniform shared-check imports before timing, no method-specific solvers imported or inputs loaded.
    from kmd_toc.comparison_v1.execution import physical_checks,auxiliary
    from kmd_toc.common.models import load_problem,load_plan
    (root/'runs').mkdir(exist_ok=True)
    for run in m['runs']:
        out=root/'runs'/run['run_id']
        if out.exists():
            if not (out/'RESULT.json').exists():raise ValueError('INCOMPLETE_ATTEMPT_PRESERVED; explicit new registration needed')
            continue # resumable completed IDs, never overwrite or success-driven retry
        row=execute(m,run,out)
        if row['execution_state'] in ('USER_CANCELLED','EXTERNAL_INTERRUPTION','RESOURCE_STOP'):break
    aggregate(root)

if __name__=='__main__':main()
