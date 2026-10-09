"""Prepared only: one frozen PID/seed. DO NOT RUN during preregistration.

Supervisor serializes runs, enforces wall/AS limits, and preserves every failed attempt.
Scientific output is deterministic for frozen inputs/seeds; timings/RSS are observations.
"""
from pathlib import Path
from decimal import Decimal as D, getcontext
from itertools import combinations
import argparse
import fcntl
import hashlib
import importlib.util
import importlib.metadata
import json
import math
import os
import resource
import signal
import subprocess
import sys
import time
from protocol import PROTOCOL, select_incumbent, in_domain
from validate_plan import ROOT, DEFAULT, validate, sha, read
getcontext().prec=80

class ValidationFailure(Exception): pass
class ProtocolFailure(Exception): pass
class EvaluationCapReached(Exception): pass

def add(poly, support, value):
    support = tuple(sorted(support))
    poly[support] = (
        poly.get(support, D(0))
        + D(value)
    )
    if poly[support] == 0:
        del poly[support]


def square_onehot(poly, ids, A):
    add(poly, (), A)

    for i in ids:
        add(poly, (i,), -A)

    for i, j in combinations(ids, 2):
        add(poly, (i, j), 2*A)


def build_C(model, a):
    n = int(model["n"])
    q = n*n
    A = D(model["penalty_s"])

    poly = {}

    x = lambda customer, pos: (
        (customer - 1)*n + pos
    )

    # Customer exactly once.
    for customer in range(1, n+1):
        square_onehot(
            poly,
            [
                x(customer, pos)
                for pos in range(n)
            ],
            A,
        )

    # Position exactly once.
    for pos in range(n):
        square_onehot(
            poly,
            [
                x(customer, pos)
                for customer in range(1, n+1)
            ],
            A,
        )

    # Frozen physical road-time objective.
    for i in range(1, n+1):
        add(
            poly,
            (x(i, 0),),
            D(str(a["travel"][0, i])),
        )

        add(
            poly,
            (x(i, n-1),),
            D(str(a["travel"][i, 0])),
        )

        for j in range(1, n+1):
            for pos in range(n-1):
                add(
                    poly,
                    (
                        x(i, pos),
                        x(j, pos+1),
                    ),
                    D(str(a["travel"][i, j])),
                )

    # Direct n-local penalty for every frozen infeasible permutation.
    for rec in model["permutations"]:

        feasible = bool(
            model["capacity_ok"]
            and rec["TIME_WINDOW"]
            and rec["RETURN_HORIZON"]
        )

        if feasible:
            continue

        order = list(
            map(int, rec["order"])
        )

        add(
            poly,
            tuple(
                x(customer, pos)
                for pos, customer
                in enumerate(order)
            ),
            A,
        )

    return q, poly


def route_code(order, n):
    code = 0
    for pos, customer in enumerate(order):
        bit = (int(customer)-1)*n + pos
        code |= 1 << bit
    return code


def seed_for(base_seed, pid, tag):
    s = f"{base_seed}|{pid}|{tag}".encode()
    return int(
        hashlib.sha256(s).hexdigest()[:8],
        16,
    )



def write_new(path, data):
    with Path(path).open('x') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

def execute_child(plan_path, run_id):
    """Only the supervised child invokes numerical libraries or quantum sampling."""
    started=time.perf_counter()
    assert not sys.flags.optimize
    assert os.environ.get('R1_V2_SUPERVISED_CHILD')==run_id
    assert sys.executable==PROTOCOL['python']
    assert resource.getrlimit(resource.RLIMIT_AS)==(4294967296,4294967296)
    for k,v in PROTOCOL['thread_environment'].items():assert os.environ[k]==v
    plan,pre=validate(plan_path)
    run=next(r for r in plan['runs'] if r['run_id']==run_id)
    out=ROOT/run['output_dir'];assert (out/'ATTEMPT.json').exists() and not (out/'result.json').exists()
    versions={k:importlib.metadata.version(k) for k in PROTOCOL['versions']}
    if versions!=PROTOCOL['versions']:
        raise RuntimeError('INFRASTRUCTURE_ENVIRONMENT_VERSION_MISMATCH')
    # Imports occur only here, never during plan validation, tests or summarization.
    import numpy as np
    from scipy.optimize import minimize
    from qiskit import qpy
    from qiskit.primitives import StatevectorSampler
    with (ROOT/run['circuit_path']).open('rb') as f: circuits=qpy.load(f)
    assert len(circuits)==1 and circuits[0].num_qubits==PROTOCOL['logical_qubits']
    qc=circuits[0];params={p.name:p for p in qc.parameters}
    assert set(params)=={'gamma','beta'}
    model=read(ROOT/run['model_path']);assert model['n']==math.isqrt(PROTOCOL['logical_qubits']) and model['capacity_ok']
    with np.load(ROOT/run['instance_path'],allow_pickle=False) as z:a={k:z[k] for k in z.files}
    spec=importlib.util.spec_from_file_location('frozen_independent',ROOT/run['validator_path'])
    ind=importlib.util.module_from_spec(spec);spec.loader.exec_module(ind)
    q,poly=build_C(model,a);assert q==PROTOCOL['logical_qubits']
    codes=np.arange(1<<q,dtype=np.uint32);energies=np.zeros(1<<q,dtype=np.float64)
    for support,coeff in poly.items():
        if not support:energies+=float(coeff)
        else:
            mask=np.uint32(sum(1<<i for i in support));energies+=((codes & mask)==mask)*float(coeff)
    feasible_routes={}
    for rec in model['permutations']:
        if not (model['capacity_ok'] and rec['TIME_WINDOW'] and rec['RETURN_HORIZON']):continue
        order=list(map(int,rec['order']));route=[0]+order+[0]
        try: authority=ind.validate(a,route)
        except AssertionError as error:raise ValidationFailure('INTERNAL_FEASIBLE_ROUTE_FAILED_VALIDATOR') from error
        feasible_routes[route_code(order,int(model['n']))]={'order':order,'route':route,'objective_s':str(authority['totals']['road_travel_seconds'])}
    assert feasible_routes
    exact_optimum=min(D(r['objective_s']) for r in feasible_routes.values())
    # Exact optimum is a retrospective metric only; never used by COBYLA or selection.
    classical=read(ROOT/run['classical_reference_path'])
    assert exact_optimum==D(str(classical['objective']))
    evals=[];sampling_total=0.0;final_started=False
    def sample(theta,shots,seed):
        nonlocal sampling_total
        bound=qc.assign_parameters({params['gamma']:float(theta[0]),params['beta']:float(theta[1])})
        sampler=StatevectorSampler(seed=seed);t=time.perf_counter()
        sampled=sampler.run([bound],shots=shots).result()[0]
        sampling_total+=time.perf_counter()-t
        counts={int(k.replace(' ',''),2):int(v) for k,v in sampled.data.meas.get_counts().items()}
        if sum(counts.values())!=shots:raise ProtocolFailure('SHOT_COUNT_MISMATCH')
        return {'counts':counts,'mean_energy_s':sum(float(energies[k])*v for k,v in counts.items())/shots,
                'feasible_count':sum(v for k,v in counts.items() if k in feasible_routes),
                'optimal_count':sum(v for k,v in counts.items() if k in feasible_routes and D(feasible_routes[k]['objective_s'])==exact_optimum)}
    def objective(theta):
        if len(evals)>=100:raise EvaluationCapReached
        if not np.isfinite(theta).all():raise ProtocolFailure('NONFINITE_OPTIMIZER_POINT')
        i=len(evals);score=sample(theta,2048,run['optimizer_sampler_seeds'][i])
        rec={'evaluation_index':i,'gamma':float(theta[0]),'beta':float(theta[1]),'in_formal_domain':in_domain(float(theta[0]),float(theta[1])),
             'mean_energy_s':score['mean_energy_s'],'feasible_count':score['feasible_count'],'optimal_count':score['optimal_count'],
             'sampler_seed':run['optimizer_sampler_seeds'][i],'shots':2048}
        evals.append(rec);print(json.dumps({'evaluation':rec}),flush=True)
        return rec['mean_energy_s']
    constraints=[{'type':'ineq','fun':lambda x:x[0]}, {'type':'ineq','fun':lambda x:2*math.pi-x[0]},
                 {'type':'ineq','fun':lambda x:x[1]}, {'type':'ineq','fun':lambda x:math.pi-x[1]}]
    opt_result=None;opt_exception=None
    try:
        res=minimize(objective,np.array([0.1,0.1],dtype=float),method='COBYLA',constraints=constraints,options=PROTOCOL['cobyla_options'])
        opt_result={'success':bool(res.success),'status':int(res.status),'message':str(res.message),'nfev':int(res.nfev),'fun':float(res.fun),'x':list(map(float,res.x))}
    except EvaluationCapReached:opt_exception='EVALUATION_CAP_REACHED'
    if not 1<=len(evals)<=100:raise ProtocolFailure('INVALID_EVALUATION_COUNT')
    try:selected,no_feasible=select_incumbent(evals)
    except ValueError as error:raise ProtocolFailure(str(error)) from error
    write_new(out/'OPTIMIZER_EVALUATIONS.json',evals)
    write_new(out/'FINAL_SAMPLING_STARTED.json',{'seed':run['final_sampler_seed'],'shots':4096,'selected_evaluation_index':selected['evaluation_index']})
    final_started=True
    final=sample([selected['gamma'],selected['beta']],4096,run['final_sampler_seed'])
    final_counts={format(k,f'0{q}b'):v for k,v in sorted(final['counts'].items())}
    write_new(out/'FINAL_COUNTS.json',final_counts)
    routes=[]
    for code,count in final['counts'].items():
        if code not in feasible_routes:continue
        internal=feasible_routes[code]
        try: validation=ind.validate(a,internal['route'])
        except AssertionError as error:raise ValidationFailure('FINAL_ROUTE_FAILED_INDEPENDENT_VALIDATOR') from error
        obj=validation['totals']['road_travel_seconds']
        if D(obj)!=D(internal['objective_s']):raise ValidationFailure('OBJECTIVE_MISMATCH')
        routes.append({'bitstring':format(code,f'0{q}b'),'count':count,'route_indices':internal['route'],
                       'route_ids':[str(a['nodes'][i]) for i in internal['route']], 'road_travel_objective_s':obj,
                       'optimal':D(obj)==exact_optimum,'time_window_validity':'PASS','return_horizon_validity':'PASS','capacity_validity':'PASS',
                       'independent_validation':validation})
    if sum(r['count'] for r in routes)!=final['feasible_count']:raise ValidationFailure('COUNT_MISMATCH')
    best=min(routes,key=lambda r:(D(r['road_travel_objective_s']),int(r['bitstring'],2))) if routes else None
    scientific={'physical_instance_id':run['physical_instance_id'],'seed_tag':run['seed_tag'],'resolved_seed':run['resolved_seed'],
                'optimizer_evaluations':evals,'selected_incumbent':selected,'NO_FEASIBLE_SAMPLE_OBSERVED_DURING_OPTIMIZATION':no_feasible,
                'final_counts':final_counts,'final_feasible_count':final['feasible_count'],'final_optimal_count':final['optimal_count'],
                'sampled_feasible_routes':routes,'best_final_feasible_route':best}
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    if rss>=4294967296:raise ProtocolFailure('RESOURCE_CAP_EXCEEDED')
    result={**scientific,'status':'PASS','execution_status':'COMPLETED','infrastructure_status':'PASS','run_id':run_id,'stratum':run['stratum'],
            'protocol':PROTOCOL,'preregistration_sha256':plan['preregistration_sha256'],'plan_sha256':sha(plan_path),'worker_sha256':sha(ENTRYPOINT),
            'input_hashes':{run[k+'_path']:run[k+'_sha256'] for k in ['circuit','instance','model','validator','classical_reference']},
            'optimizer_evaluation_count':len(evals),'optimizer_observed_any_feasible_sample':any(r['feasible_count']>0 for r in evals),
            'eligible_optimizer_observed_feasible_sample':not no_feasible,'optimizer_result':opt_result,'optimizer_exception':opt_exception,
            'selected_incumbent_index':selected['evaluation_index'],'selected_gamma':selected['gamma'],'selected_beta':selected['beta'],
            'selected_incumbent_feasible_count':selected['feasible_count'],'selected_incumbent_mean_energy':selected['mean_energy_s'],
            'final_shots':4096,'final_sampler_seed':run['final_sampler_seed'],'final_feasible_probability':final['feasible_count']/4096,
            'final_optimal_probability':final['optimal_count']/4096,'exact_physical_optimum_s':str(exact_optimum),
            'independent_validation_status':'PASS','max_rss_bytes':rss,'wall_s':time.perf_counter()-started,'sampling_wall_s':sampling_total,
            'python':sys.executable,'versions':versions,'process_cap_bytes':4294967296,'RLIMIT_AS':list(resource.getrlimit(resource.RLIMIT_AS)),
            'sampler_run_calls':len(evals)+1,'total_shots':len(evals)*2048+4096,'automatic_retry':False,'protocol_deviation':False,
            'scientific_payload_sha256':hashlib.sha256(json.dumps(scientific,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'FULL_R1_RUN_ALLOWED':False}
    write_new(out/'result.json',result)

def supervisor(plan_path,run_id):
    assert not sys.flags.optimize
    plan,pre=validate(plan_path)
    run=next(r for r in plan['runs'] if r['run_id']==run_id)
    folder=Path(plan_path).resolve().parent
    with (folder/'SERIAL_EXECUTION.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=ROOT/run['output_dir'];out.mkdir(parents=True,exist_ok=False) # existing attempt cannot be retried
        env=os.environ.copy();env.update(PROTOCOL['thread_environment']);env['PYTHONDONTWRITEBYTECODE']='1';env['R1_V2_SUPERVISED_CHILD']=run_id
        command=[PROTOCOL['python'],str(Path(ENTRYPOINT).resolve()),'--plan',str(Path(plan_path).resolve()),'--run-id',run_id,'--internal-child']
        write_new(out/'ATTEMPT.json',{'run_id':run_id,'command':command,'plan_sha256':sha(plan_path),'worker_sha256':sha(ENTRYPOINT),'attempt':1,'automatic_retry':False})
        def limits():
            os.setsid();resource.setrlimit(resource.RLIMIT_AS,(4294967296,4294967296));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        t=time.perf_counter();timeout=False
        with (out/'EXECUTION.log').open('x') as log:
            try:
                proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
                try:code=proc.wait(timeout=3600)
                except subprocess.TimeoutExpired:
                    timeout=True;os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
            except (OSError, subprocess.SubprocessError) as error:
                log.write('INFRASTRUCTURE_LAUNCH_FAILURE: '+repr(error)+'\n');code=1
        status={0:'PASS',20:'VALIDATION_FAILURE',21:'INTEGRITY_FAILURE',22:'PROTOCOL_FAILURE'}.get(code,'INFRASTRUCTURE_FAILURE')
        write_new(out/'PROCESS.json',{'run_id':run_id,'status':status,'returncode':code,'timeout':timeout,'wall_s':time.perf_counter()-t,'execution_log_sha256':sha(out/'EXECUTION.log'),'retry':False})
        if not (out/'result.json').exists():
            write_new(out/'result.json',{'run_id':run_id,'physical_instance_id':run['physical_instance_id'],'stratum':run['stratum'],
                'seed_tag':run['seed_tag'],'resolved_seed':run['resolved_seed'],'status':status if status!='PASS' else 'PROTOCOL_FAILURE',
                'final_feasible_count':None,'final_optimal_count':None,'FULL_R1_RUN_ALLOWED':False,
                'notes':'Incomplete/failed execution is not a scientific zero. No automatic rerun.'})
        return code

