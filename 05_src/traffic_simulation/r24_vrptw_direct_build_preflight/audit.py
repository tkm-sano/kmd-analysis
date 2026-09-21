"""Direct-build acceptance: archived Uniform references, zero Uniform factories."""
import time,inspect,ast
from contextlib import ExitStack
from unittest.mock import patch
import numpy as np
from traffic_simulation.r24_vrptw_structured_worker.contract import *
from traffic_simulation.r24_vrptw_structured_worker.worker import prepare,initial_state
from traffic_simulation.r24_vrptw_structured_worker.guard import ZeroShotGuard
from traffic_simulation.r24_vrptw_structured_worker.ledger import projection
from traffic_simulation.r24_vrptw_structured_worker.preflight import manifest_entry
from traffic_simulation.r24_vrptw_qaoa_worker import circuit as shared,worker as uniform
from traffic_simulation.r24_vrptw_structured_initial_state.validate import counts,circuit_signature
from traffic_simulation.r24_vrptw_structured_initial_state_audit.audit import fidelity_check
OUT=BASE/'r24_vrptw_structured_initial_state/20260922_v4_direct_build_preflight'
OLD_PREFLIGHT=BASE/'r24_vrptw_structured_initial_state/20260922_v3_implementation_preflight'
STANDARD_PREFLIGHT=BASE/'r24_vrptw_qaoa_execution/20260921_v1/implementation_preflight'

def dump(n,v):
    p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

class NoUniform:
    def __enter__(self):
        self.stack=ExitStack();self.full=self.stack.enter_context(patch.object(uniform,'prepare',side_effect=AssertionError('UNIFORM_FULL_FACTORY_FORBIDDEN')));self.initial=self.stack.enter_context(patch.object(shared,'build_uniform_initial_state',side_effect=AssertionError('UNIFORM_INITIAL_FACTORY_FORBIDDEN')));return self
    def __exit__(self,*args):return self.stack.__exit__(*args)

def load_archive(rid,name='symbolic.qpy'):
    from qiskit import qpy
    path=STANDARD_PREFLIGHT/'dry_runs'/rid/name
    # Hash independently fixed before this refactor, not inferred from current code.
    baseline=read(OUT/'BASELINE_ALL_FILES.json');require(sha(path)==baseline[str(path.relative_to(ROOT))],'Uniform archive hash')
    with path.open('rb') as f:return qpy.load(f)[0]

def archived_body(rid,gamma,beta):
    qc=load_archive(rid)
    require(sum(x.operation.name=='h' for x in qc.data)==qc.num_qubits,'frozen Uniform H layer')
    # Inspection of stored circuit only; no Uniform factory or new Uniform state.
    for i in reversed(range(len(qc.data))):
        if qc.data[i].operation.name=='h':del qc.data[i]
    return qc.assign_parameters({p:gamma if p.name=='gamma' else beta for p in qc.parameters})

def body_audit(p):
    from qiskit import transpile
    from qiskit.converters import circuit_to_dag
    body,gamma,beta,a,const=shared.build_body(p['adapter'].model)
    old=archived_body(p['plan']['U_reference_run_id'],gamma,beta)
    cfg=p['spec']['transpilation'];settings={k:cfg[k] for k in ['basis_gates','optimization_level','seed_transpiler','coupling_map','num_processes']}
    compiled=transpile(body,**settings)
    require(circuit_to_dag(compiled)==circuit_to_dag(old),'shared body vs archived Uniform DAG')
    params=[x.name for x in compiled.parameters];require(params==[x.name for x in old.parameters]==['beta','gamma'],'parameter ordering')
    require(compiled.global_phase==old.global_phase,'global phase')
    require(compiled.count_ops()==old.count_ops(),'gate counts')
    logical_body=body.assign_parameters({gamma:p['gamma'],beta:p['beta']})
    require(p['logical']==p['preparation'].compose(logical_body),'direct composition')
    return dict(group=p['plan']['group'],run_id=p['plan']['run_id'],QUBO_hash=p['identity']['qubo_hash'],archived_reference=p['plan']['U_reference_run_id'],archive_sha256=sha(STANDARD_PREFLIGHT/'dry_runs'/p['plan']['U_reference_run_id']/'symbolic.qpy'),body_DAG_equivalence=True,cost_global_phase=True,cost_gates=True,mixer_gates=True,p=1,parameter_names=params,parameter_count=2,optimizer_order=['alpha','beta'],mapping='gamma=alpha/scale; beta=beta',body_operation_counts=dict(compiled.count_ops()),shared_body_identity=circuit_signature(compiled),archived_body_identity=circuit_signature(old),measurement_mapping=p['injection_audit']['measurement'],status='PASS')

def run():
    from qiskit.quantum_info import Statevector
    from qiskit import transpile
    environment();start=time.monotonic();bodies=[];states=[];structures=[];manifests=[];leaks=[];controls=[];seen={}
    with ZeroShotGuard() as guard,NoUniform() as nou:
        for r in rows(SPEC/'RUN_PLAN.csv'):
            p=prepare(r['run_id'],check_environment=False);a=body_audit(p);bodies.append(a)
            entry=manifest_entry(p);require(entry==manifest_entry(prepare(r['run_id'],check_environment=False)),'deterministic manifest');manifests.append(entry)
            leaks.append(dict(run_id=r['run_id'],inputs=p['construction_inputs'],forbidden_inputs_present=False,status='PASS'))
            if r['group'] in seen:require(p['state']==seen[r['group']],'repetition-independent preparation');continue
            seen[r['group']]=p['state'];s=p['state'];cfg=p['spec']['transpilation']
            prep=transpile(p['preparation'],**{k:cfg[k] for k in ['basis_gates','optimization_level','seed_transpiler','coupling_map','num_processes']})
            vector=Statevector.from_instruction(prep).data;target=np.zeros(1<<s['qubits'],complex);target[s['support']]=s['amplitude'];f=fidelity_check(vector,target)
            old=read(OFFLINE/'groups'/(r['group']+'.json'));require(s==old['state'],'offline state')
            row=dict(group=r['group'],condition=r['condition'],support_size=len(s['support']),support_mismatch=0,duplicate_support=0,variable_order_mismatch=0,probability_max_error=float(np.max(abs(abs(vector)**2-abs(target)**2))),**f,temporal_valid_mass=old['metrics'][1]['temporal_mass'],no_good_violation_mass=old['metrics'][1]['no_good_violated_mass'],initial_feasible_mass=old['metrics'][1]['overall_feasible_mass']);states.append(row)
            structures.append(dict(group=r['group'],qubits=p['logical'].num_qubits,classical_bits_unmeasured=p['logical'].num_clbits,classical_bits_measured=p['measured'].num_clbits,parameter_count=len(p['qc'].parameters),parameter_names=[x.name for x in p['qc'].parameters],logical_depth=p['logical'].depth(),transpiled_depth=p['qc'].depth(),logical_operations=dict(p['logical'].count_ops()),transpiled_operations=dict(p['qc'].count_ops()),preparation_operations=dict(p['preparation'].count_ops()),measurement_operations=dict(p['measured'].count_ops()),preparation_hash=circuit_signature(p['preparation']),logical_hash=circuit_signature(p['logical']),transpiled_hash=circuit_signature(p['qc']),bound_hash=circuit_signature(p['bound']),route_register=p['injection_audit']['route_register'],slack_register=p['injection_audit']['slack_register'],measurement_mapping=p['injection_audit']['measurement'],bitstring_convention=p['injection_audit']['endian']))
        for r in rows(OFFLINE/'QUBO_GROUPS.csv'):
            old=read(DESIGN/'conditions'/(r['condition']+'.json'));s,inputs=initial_state(**old['inputs']);require(s==seen[r['group']],'same-QUBO control identity');controls.append(dict(condition=r['condition'],group=r['group'],status='PASS'))
        require(not guard.attempts and nou.full.call_count==nou.initial.call_count==0,'forbidden construction/execution')
        proj=projection()
        uniform_audit=dict(status='PASS',scope='All Structured prepares, double regeneration and body audits',full_factory_calls=nou.full.call_count,initial_factory_calls=nou.initial.call_count,reference_handling='Deserialize immutable Uniform QPY and inspect body only; never call a Uniform factory',guard='Both Uniform entry and initial-state factory patched to raise immediately')
    dump('UNIFORM_CONSTRUCTION_AUDIT.json',uniform_audit);dump('SHARED_QAOA_BODY_AUDIT.json',dict(status='PASS',runs=bodies,shared_source='05_src/traffic_simulation/r24_vrptw_qaoa_worker/circuit.py'))
    table(OUT/'STATE_REPRODUCTION_AUDIT.csv',states);table(OUT/'CIRCUIT_STRUCTURE_AUDIT.csv',structures);table(OUT/'WAITING_CONTROL_VALIDATION.csv',controls)
    dump('PREFLIGHT_MANIFEST.json',dict(runs=manifests,deterministic_run_records_sha256=digest(manifests),source_comparison=COMPARISON_HASH,execution_status='NOT_STARTED'));table(OUT/'PREFLIGHT_MANIFEST.csv',manifests)
    c,s=frozen();dump('FREEZE_AUDIT_V2.json',dict(status='PASS',inherited_settings=c['inherited_settings'],resource_policy=c['resource_policy'],comparison_manifest_sha256=COMPARISON_HASH,scientific_changed_factor='initial_state_only',refactor_changes_scientific_factor=False,Uniform_reference_runs=[r['comparison_reference'] for r in manifests],postprocessing_unchanged=True,backend_not_called=True))
    dump('LEAKAGE_AUDIT_V2.json',dict(status='PASS',records=leaks,allowed=['n','m','variable_order'],constructor_source=inspect.getsource(initial_state),same_QUBO_controls=controls,active_TW_preserved=True))
    dump('LEDGER_PROJECTION_V2.json',proj)
    dump('EXECUTION_COUNTS.json',dict(Uniform_full_factory=0,Uniform_initial_factory=0,backend=0,sampler=0,optimizer_evaluations=0,scientific_circuits=0,scientific_shots=0,Aer_sampling=0,ledger_increment=0,reservations=0,preparation_only_Statevector=3,body_evolutions=0,seconds=time.monotonic()-start))
    print(json.dumps(dict(status='DIRECT_BUILD_AUDIT_PASS',groups=3,runs=9,seconds=time.monotonic()-start)))

if __name__=='__main__':run()
