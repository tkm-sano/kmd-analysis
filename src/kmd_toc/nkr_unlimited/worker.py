"""One native thread; every completed local call commits a resumable state."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

from kmd_toc.duty_break_v1.local import complete
from kmd_toc.d_local_design.completion import preserves
from kmd_toc.d_final_selection_v1.ranking import metric_record
from kmd_toc.main_experiment_d.quantum import backend_modules
from . import kernel
from .common import *


def assessment(p,plan,local,decoded,folder,provenance,limit):
    base,_=checked(p,plan);best=base;chosen=plan;chosen_path=None;ledger=[];checked_count=0;screened=0
    demand={s.stop_id:s.demand for s in p.stops};caps={v.vehicle_id:v.capacity for v in p.vehicles}
    routes={(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips};ids=set(local.customer_ids)
    for energy,bits,decision,count in decoded:
        if any(sum(demand[s] for s in routes[key] if s not in ids)+sum(demand[s] for s in route)>caps[key[0]]
               for key,route in zip(local.trip_ids,(decision.trip_1,decision.trip_2))):
            screened+=1;continue
        if checked_count>=limit:break
        checked_count+=1;row={'bits':bits,'count':count,'decision':asdict(decision),'proxy':energy}
        try:proposal=complete(p,plan,local,decision,quantum_provenance=provenance)
        except ValueError as e:ledger.append({**row,'status':'COMPLETION_REJECT','reason':str(e)});continue
        m,validation=checked(p,proposal)
        if not preserves(proposal,local,decision,plan):raise ValueError('QUANTUM_OR_OUTSIDE_ORDER_CHANGED')
        name=f'candidate_{checked_count}.json.gz';gzsave(folder/name,asdict(proposal))
        accept=(m.D<=base.D and m.W<=base.W and m!=base and m.D<=best.D and m.W<=best.W and m!=best)
        if accept:chosen=proposal;best=m;chosen_path=str(folder/name)
        ledger.append({**row,'status':'ACCEPT' if accept else 'KEEP_INCUMBENT','metrics':recorded(m),
                       'plan':name,'model_feasible':validation['model_feasible'],
                       'site_feasibility':validation['stopping_site_feasibility']})
    return chosen,chosen_path,{'checked':checked_count,'capacity_screened':screened,'ledger':ledger}


def recover_decoded(p,plan,local,folder):
    q,_=backend_modules();lookup=q.boundary_lookups(p,plan,local)
    final=None
    with (folder/'evaluations.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if r.get('event')=='sampling_completed' and r.get('phase')=='final_extraction':final=r
    if final is None:raise ValueError('FINAL_COUNTS_NOT_RECOVERABLE')
    label={s:i+1 for i,s in enumerate(local.customer_ids)};decoded=[]
    for bits,count in final['counts'].items():
        decision=q.decode_register(int(bits,2),local.customer_ids)
        order=tuple(label[s] for s in decision.trip_1)+(0,)+tuple(label[s] for s in decision.trip_2)
        decoded.append((q.lookup_cost(order,lookup)/lookup['bound_m'],int(bits,2),decision,count))
    decoded.sort(key=lambda x:(x[0],x[1]));return decoded,read(folder/'RESULT.json')


def run(job_path):
    job=read(job_path);out=Path(job['output']);cohort=Path(job['cohort']);check_pins(cohort)
    os.sched_setaffinity(0,{job['cpu']});start=time.perf_counter();cpu=time.process_time();current_call=None
    state_path=out/'CHECKPOINT.json';status='FAILED';reason=None
    old_cpu=0.;old_wall=0.
    try:
        p=problem(job['scale'])
        if state_path.exists():
            state=read(state_path);plan=payload_plan(state['plan']);seen=set(state['seen']);ordinal=state['completed_slots']
            rows=state['rows'];old_cpu=state.get('CPU_s',0.);old_wall=state.get('wall_s',0.)
        else:
            plan=load_plan(cohort/'baselines'/job['scale']/'plan.json');seen=set();ordinal=0;rows=[]
        initial=load_plan(cohort/'baselines'/job['scale']/'plan.json');initial_metrics,_=checked(p,initial)
        checked(p,plan)
        for position in range(ordinal,job['K']*job['R']):
            r,k=divmod(position,job['K']);r+=1;k+=1;current_call=f'r{r:03d}_k{k:03d}'
            seed=legacy.seed_for(job['outer_seed'],job['branch'],r,k)
            begin=time.perf_counter();local=legacy.pick(p,plan,seen,job['n'],seed);generation_s=time.perf_counter()-begin
            root=out/'calls'/current_call;root.mkdir(parents=True,exist_ok=True)
            commit=root/'COMMIT.json';before,_=checked(p,plan)
            if commit.exists():
                record=read(commit)
                if record.get('after_plan_path'):plan=load_payload(record['after_plan_path'])
                if local is not None:seen.update(local.customer_ids)
                rows.append(record['row'])
            elif local is None:
                row={'r':r,'k':k,'seed':seed,'call_id':current_call,'status':'NO_SELECTION','quantum_calls':0,'generation_s':generation_s}
                rows.append(row);dump(commit,{'row':row,'after_plan_path':None})
            else:
                q,_=backend_modules();lookup=q.boundary_lookups(p,plan,local)
                oracle=legacy.validate_oracle(p,plan,local,q,lookup,2)
                attempts=sorted(root.glob('attempt_*'))
                recover=next((a for a in reversed(attempts) if (a/'RESULT.json').exists()),None)
                if recover:
                    folder=recover;decoded,quantum=recover_decoded(p,plan,local,folder);quantum_reused=True
                else:
                    folder=root/f'attempt_{len(attempts)+1:03d}';quantum_reused=False
                    dump(out/'HEARTBEAT.json',{'phase':'quantum','call_id':current_call,'r':r,'k':k,'PID':os.getpid()})
                    decoded,quantum=kernel.run(p,plan,local,read(CONFIG),folder)
                begin=time.perf_counter();chosen,path,ledger=assessment(p,plan,local,decoded,folder,
                    {'measured':True,'CALL_sha256':digest(folder/'CALL.json'),'RESULT_sha256':digest(folder/'RESULT.json'),
                     'p':2,'optimization_shots':1000,'final_shots':10000,'seed':seed},read(CONFIG)['postmeasurement_checks'])
                after,_=checked(p,chosen);seen.update(local.customer_ids)
                row={'r':r,'k':k,'call_id':current_call,'seed':seed,'status':'COMPLETE','customer_ids':local.customer_ids,
                     'quantum_calls':1,'generation_s':generation_s,'oracle':oracle,'quantum_folder':str(folder),
                     'quantum_recovered_without_rerun':quantum_reused,'quantum':quantum,'assessment':ledger,
                     'assessment_s':time.perf_counter()-begin,'before':recorded(before),'after':recorded(after),'adopted':chosen is not plan}
                dump(commit,{'row':row,'after_plan_path':path});rows.append(row);plan=chosen
            checked(p,plan)
            dump(state_path,{'completed_slots':position+1,'plan':asdict(plan),'seen':sorted(seen),'rows':rows,
                'wall_s':old_wall+time.perf_counter()-start,'CPU_s':old_cpu+time.process_time()-cpu,'PID':os.getpid()})
            dump(out/'HEARTBEAT.json',{'phase':'committed','call_id':current_call,'completed_slots':position+1,
                 'planned_slots':job['K']*job['R'],'PID':os.getpid()})
        final,validation=checked(p,plan);dump(out/'plan.json',asdict(plan));status='COMPLETE'
    except Exception as e:
        reason=f'{type(e).__name__}:{e}'
        dump(out/'FAILURE.json',{'reason':reason,'call_id':current_call,'traceback':traceback.format_exc()})
    result={'status':status,'reason':reason,'job':job,'PID':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),
        'native_threads':1,'CPU_s':old_cpu+time.process_time()-cpu,'wall_s':old_wall+time.perf_counter()-start,
        'RSS_highwater_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    if status=='COMPLETE':result.update(initial=recorded(initial_metrics),after=recorded(final),rows=rows,
        model_feasible=validation['model_feasible'],site_feasibility=validation['stopping_site_feasibility'],
        coverage=legacy.coverage([set(r['customer_ids']) for r in rows if r.get('customer_ids')],len(p.stops)))
    dump(out/'RESULT.json',result)
    if status!='COMPLETE':raise SystemExit(2)


def reference(job_path):
    from kmd_toc.termination_v1.work import Ledger
    from .reference import generate_reference
    job=read(job_path);out=Path(job['output']);check_pins(job['cohort']);os.sched_setaffinity(0,{job['cpu']})
    start=time.perf_counter();cpu=time.process_time();ledger=Ledger(out)
    try:
        p=problem(job['scale']);cfg=read(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')
        plan=generate_reference(p,'C',cfg,ledger,{'solver_seed':job['seed'],'quantum_seed':job['seed']})
        m,v=checked(p,plan);dump(out/'plan.json',asdict(plan))
        result={'status':'COMPLETE','after':recorded(m),'model_feasible':v['model_feasible'],'site_feasibility':v['stopping_site_feasibility']}
    except Exception as e:
        result={'status':'FAILED','reason':f'{type(e).__name__}:{e}','traceback':traceback.format_exc()}
    result.update(job=job,PID=os.getpid(),executable=sys.executable,python=sys.version,affinity=sorted(os.sched_getaffinity(0)),
                  native_threads=1,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,
                  RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,counts=ledger.counts)
    dump(out/'RESULT.json',result)
    if result['status']!='COMPLETE':raise SystemExit(2)
