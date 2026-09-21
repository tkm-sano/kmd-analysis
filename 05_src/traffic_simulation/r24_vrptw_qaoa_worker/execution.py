"""Future one-run pipeline. Offline tests inject synthetic callbacks, never Aer.

There is deliberately no scientific CLI. The future supervisor requires explicit
authorization and verified runtime-sanity receipts, separately from this preflight.
"""
import time
import math
import os
from .contract import *
from .ledger import Ledger,atomic,LedgerError
from .results import save

class TrainingCap(Exception):pass

def perform(p,ledger,directory,backend,optimizer,*,synthetic=False,resource_trace=None):
    """Internal pipeline; backend takes (bound circuit, shots, seed) -> counts.

    Production callers MUST use supervised_run, not this dependency-injection seam.
    A production token can only be issued in its monitored child process.
    """
    require(synthetic or _MONITORED_PID==os.getpid(),'supervisor required','EXECUTION_NOT_AUTHORIZED')
    state=ledger.snapshot();require(state['synthetic']==synthetic,'ledger scope')
    prior=ledger.completed(p['identity'])
    if prior:return prior
    ident=p['identity'];rid=ident['run_id'];spec=p['spec'];run=p['plan'];directory=Path(directory)
    require(not directory.exists(),'existing incomplete run path; no automatic retry','DUPLICATE_RUN')
    ledger.order_gate(ident);ledger.wall_gate(ident)
    if not synthetic:require(directory==ROOT/run['planned_output_path'],'output path')
    directory.mkdir(parents=True,exist_ok=False);(directory/'receipts').mkdir()
    reservation=ledger.snapshot()['runs'][rid]['reservation']
    ledger.claim_reservation(reservation['reservation_id'],reservation['context'])
    history=[];incumbent=None;started=time.monotonic()
    def heartbeat(phase):atomic(directory/'HEARTBEAT.json',dict(monotonic=time.monotonic(),phase=phase,identity=ident))
    def call(phase,index,params,seed):
        heartbeat(phase);require(len(params)==2 and all(math.isfinite(float(x)) for x in params),'parameters')
        qc=p['measured'].assign_parameters({p['gamma']:float(params[0])/spec['parameters']['scale'],p['beta']:float(params[1])})
        require(not qc.parameters,'binding')
        shots=spec['shots']['independent_final'] if phase=='final' else spec['shots']['training_per_evaluation']
        ledger.transition(rid,phase,index,'STARTED')
        try:counts=backend(qc,shots,seed)
        except BaseException:
            ledger.transition(rid,phase,index,'UNKNOWN_COUNTED',reason='backend completion unknown; no retry');raise
        try:
            require(isinstance(counts,dict) and all(type(v) is int and v>0 for v in counts.values()) and sum(counts.values())==shots,'backend counts')
            for key in counts:p['adapter'].bits(key)
            artifact=directory/'receipts'/f'{phase}_{index}_COUNTS.json';atomic(artifact,counts)
            receipt=directory/'receipts'/f'{phase}_{index}_RECEIPT.json'
            atomic(receipt,dict(identity=ident,phase=phase,index=index,seed=seed,shots=shots,parameters=list(map(float,params)),
                artifact=artifact.name,artifact_sha256=sha(artifact),validated=True,synthetic=synthetic))
            ledger.transition(rid,phase,index,'SUCCEEDED',receipt=str(receipt))
            heartbeat(phase+'_complete');return counts
        except BaseException:
            ledger.transition(rid,phase,index,'FAILED_COUNTED',reason='completed response invalid');raise
    def objective(params):
        nonlocal incumbent
        index=len(history)
        if index>=spec['optimizer']['training_evaluation_cap']:raise TrainingCap()
        counts=call('training',index,params,run['seeds']['training_simulator_seeds'][index])
        from traffic_simulation.r24_vrptw_quantum_encoding_preflight.model import expanded
        import numpy as np
        energies=expanded(p['adapter'].model,np.array([p['adapter'].bits(k) for k in counts]))
        mean=sum(float(e)*c for e,c in zip(energies,counts.values()))/sum(counts.values())
        require(math.isfinite(mean),'nonfinite objective')
        record=dict(evaluation=index,alpha=float(params[0]),beta=float(params[1]),gamma=float(params[0])/spec['parameters']['scale'],
            seed=run['seeds']['training_simulator_seeds'][index],shots=sum(counts.values()),mean_energy=mean,scaled_objective=mean/spec['parameters']['scale'])
        history.append(record);atomic(directory/'TRAINING_HISTORY.json',history)
        if incumbent is None or mean<incumbent['mean_energy']:incumbent=record.copy();atomic(directory/'INCUMBENT.json',incumbent)
        return record['scaled_objective']
    try:
        heartbeat('optimizer_start')
        try:optimizer(objective,list(run['initial_parameters']),method=spec['optimizer']['name'],options=copy.deepcopy(spec['optimizer']['options']))
        except TrainingCap:pass
        require(incumbent is not None,'optimizer produced no evaluation')
        ledger.release_training(rid)
        counts=call('final',0,[incumbent['alpha'],incumbent['beta']],run['seeds']['final_simulator_seed'])
        # Snapshot the supervisor-owned trace; never mutate hashed run artifacts later.
        (directory/'RESOURCE_TRACE.jsonl').write_text(Path(resource_trace).read_text() if resource_trace else '')
        result=save(directory,p,counts,history,incumbent,synthetic=synthetic)
        ledger.finish(rid,directory/'RESULT.json');return result
    except BaseException as e:
        atomic(directory/'STOP_SNAPSHOT.json',dict(identity=ident,reason=type(e).__name__+': '+str(e),
            ledger=ledger.snapshot()['totals'],automatic_retry=False,synthetic=synthetic))
        ledger.halt(rid,type(e).__name__+': '+str(e));raise
    finally:ledger.account_wall(rid,time.monotonic()-started,ident['batch_id'])

_MONITORED_PID=None

def supervised_run(run_id,authorization):
    """Future authorized entry. NOT called by offline acceptance or its tests."""
    require(authorization==dict(execution_spec_sha256=MANIFEST_SHA256,scientific_execution_authorized=True),
        'separate explicit scientific authorization required','EXECUTION_NOT_AUTHORIZED')
    import fcntl
    import multiprocessing as mp
    from .worker import prepare
    from traffic_simulation.r24_qaoa_resource_gate_redesign.gates import GateEngine,snapshot,process_memory,durable_json
    spec=load();environment();ident=identity(spec,plan(spec,run_id))
    ledger=Ledger(ROOT/read(FREEZE/'LEDGER_SPEC.json')['planned_path'])
    require(ledger.path.exists() and not ledger.snapshot()['synthetic'],'production ledger must be separately initialized')
    previous=ledger.completed(ident)
    if previous:return previous
    lockpath=ledger.path.with_suffix('.executor.lock')
    with lockpath.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ledger.order_gate(ident);ledger.wall_gate(ident)
        sanity=read(Path(ledger.snapshot()['supplemental'][ident['condition']]['receipt']['path']))
        require(sanity.get('synthetic') is False and sanity.get('Aer_runtime_sanity') is True,'real runtime sanity receipt required')
        require(sanity.get('identity')=={k:ident[k] for k in ['condition','execution_spec_sha256','qubo_hash','variable_order_hash','encoding_hash','configuration_hash']},'runtime sanity identity')
        cfg=spec['resource_gate'];limits=cfg['execution_limits'];p=prepare(run_id)
        directory=ROOT/p['plan']['planned_output_path'];require(not directory.exists(),'incomplete path; no retry')
        monitor=ledger.path.parent/'monitor'/run_id;monitor.mkdir(parents=True,exist_ok=False)
        baseline=snapshot(None,process_memory(os.getpid()),dict(run_id=run_id));engine=GateEngine(baseline,cfg)
        decision=engine.evaluate(baseline)
        if decision['stop']:
            durable_json(monitor/'STOP_SNAPSHOT.json',dict(snapshot=baseline,decision=decision));ledger.halt(run_id,'resource pre-start gate');raise Stop(str(decision))
        def child():
            global _MONITORED_PID
            _MONITORED_PID=os.getpid()
            try:
                from qiskit_aer import AerSimulator
                from scipy.optimize import minimize
                backend=AerSimulator(**spec['simulator'])
                def sample(qc,shots,seed):return dict(backend.run(qc,shots=shots,seed_simulator=seed).result().get_counts())
                perform(p,ledger,directory,sample,minimize,resource_trace=monitor/'RESOURCE_TRACE.jsonl')
            except BaseException as e:
                atomic(monitor/'CHILD_FAILURE.json',dict(type=type(e).__name__,message=str(e)));raise
        (monitor/'RESOURCE_TRACE.jsonl').touch(exist_ok=False)
        proc=mp.get_context('fork').Process(target=child);start=time.monotonic();proc.start();peak=0;last=0;halted=False
        try:
            with (monitor/'RESOURCE_TRACE.jsonl').open('a') as trace:
                while proc.is_alive():
                    current=time.monotonic();memory=process_memory(proc.pid,peak)
                    if memory.get('process_exited'):break
                    peak=memory['peak_rss_bytes']
                    if current-last>=cfg['system_poll_seconds']:snap=snapshot(proc.pid,memory,dict(run_id=run_id));last=current
                    else:snap=copy.deepcopy(baseline if last==0 else snap);snap.update(monotonic=current,process=memory)
                    triggers=[]
                    if current-start>=limits['run_wall_seconds']:triggers.append('RUN_WALL_STOP')
                    beat=directory/'HEARTBEAT.json';progress=read(beat)['monotonic'] if beat.exists() else start
                    if current-progress>=limits['heartbeat_stall_seconds']:triggers.append('HEARTBEAT_STALL_STOP')
                    try:ledger.wall_gate(ident,current-start,0)
                    except LedgerError:triggers.append('CUMULATIVE_WALL_STOP')
                    snap['external_stop_triggers']=[dict(label=t,scope='run',metric='wall',observed=current-start,threshold=limits['run_wall_seconds']) for t in triggers]
                    # PSI persistence is advanced only on fresh system observations.
                    if current==last:decision=engine.evaluate(snap)
                    else:
                        rss_engine=GateEngine(baseline,cfg);decision=rss_engine.evaluate(snap)
                    if current==last or decision['stop']:
                        trace.write(json.dumps(dict(snap,decision=decision))+'\n');trace.flush()
                    if decision['stop']:
                        durable_json(monitor/'STOP_SNAPSHOT.json',dict(snapshot=snap,decision=decision));ledger.halt(run_id,str(decision['stop_reasons']))
                        proc.terminate();halted=True;break
                    time.sleep(cfg['process_poll_seconds'])
        finally:
            proc.join(timeout=2)
            if proc.is_alive():proc.kill();proc.join()
        if halted or proc.exitcode!=0:
            ledger.halt(run_id,'worker failed/unknown; no retry')
            if run_id in ledger.snapshot()['runs']:ledger.recover(run_id,directory/'receipts')
            raise Stop('WORKER_FAILED_OR_UNKNOWN_COMPLETION')
        result=ledger.completed(ident);require(result is not None,'missing completed artifact','UNKNOWN_BACKEND_COMPLETION')
        return result
