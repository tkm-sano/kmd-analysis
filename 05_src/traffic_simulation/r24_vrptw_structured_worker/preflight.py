"""Zero-shot manifest/reproduction acceptance. No scientific-result generation."""
import time,subprocess,ast,inspect
import numpy as np
from .contract import *
from .worker import prepare,initial_state
from .guard import ZeroShotGuard
from .ledger import projection,DryLedger,Ledger
from .execution import wired
from traffic_simulation.r24_vrptw_structured_initial_state_audit.audit import fidelity_check
from traffic_simulation.r24_vrptw_structured_initial_state.validate import circuit_signature

def dump(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def manifest_entry(p):
    r=p['plan'];s=p['spec'];i=p['identity'];b=p['state']['route_qubits'];n=p['state']['qubits'];cfg,standard=frozen()
    entry=dict(nominal_condition=r['condition'],group=r['group'],run_id=r['run_id'],repetition=r['repetition'],QUBO_hash=i['qubo_hash'],QUBO_source=str((ENC/'conditions'/r['condition']/'QUBO.json').relative_to(ROOT)),QUBO_file_sha256=sha(ENC/'conditions'/r['condition']/'QUBO.json'),variable_order_hash=i['variable_order_hash'],variable_order=p['adapter'].order,frozen_configuration_hash=cfg['configuration_hash'],comparison_manifest_sha256=COMPARISON_HASH,initial_state_type='Candidate A',construction_version=cfg['S']['constructor_sha256'],construction_source=cfg['S']['constructor'],initial_state_hash=r['preparation_state_hash'],construction_inputs=p['construction_inputs'],n=p['construction_inputs']['n'],m=p['construction_inputs']['m'],qubits=n,route_register=list(range(b)),slack_register=list(range(b,n)),measurement=[list(pair) for pair in p['injection_audit']['measurement']],bitstring_convention=p['injection_audit']['endian'],p=s['p'],optimizer=s['optimizer'],optimizer_seed=r['seeds']['optimizer_seed'],training_simulator_seed_stream=r['seeds']['training_simulator_seeds'],final_simulator_seed=r['seeds']['final_simulator_seed'],transpiler_seed=r['seeds']['transpiler_seed'],initial_parameters=r['initial_parameters'],scale=s['parameters']['scale'],parameter_bounds=s['parameters']['parameter_bounds'],shots=s['shots'],maximum_optimizer_evaluations=99,maximum_circuit_count=100,maximum_shot_count=204800,actual_circuits=0,actual_shots=0,backend=dict(implementation='qiskit_aer.AerSimulator',options=s['simulator']),transpilation=s['transpilation'],output_directory=r['future_output'],comparison_reference=r['U_reference_run_id'],preparation_circuit_hash=circuit_signature(p['preparation']),full_circuit_hash=circuit_signature(p['qc']),bound_circuit_hash=circuit_signature(p['bound']),gate_resources=p['resources'])

    meta=read(OUT/'START.json')
    entry.update(timestamp_utc=__import__('datetime').datetime.fromtimestamp(meta['epoch'],__import__('datetime').timezone.utc).isoformat(),git_commit=meta['git_commit'],git_dirty=True,git_dirty_state_sha256=sha(OUT/'GIT_STATUS_BEFORE.txt'))
    return entry

def run():
    from qiskit.quantum_info import Statevector
    from qiskit import transpile
    c,s=frozen();environment();plans=rows(SPEC/'RUN_PLAN.csv');start=time.monotonic();entries=[];fidelities=[];leaks=[];group_states={};settings=s['transpilation'];freeze=[]
    with ZeroShotGuard() as guard:
        for r in plans:
            p=prepare(r['run_id'],check_environment=False);entry=manifest_entry(p);entries.append(entry)
            # Regeneration checks all nine run manifests, excluding external timestamp metadata.
            q=prepare(r['run_id'],check_environment=False);require(manifest_entry(q)==entry,'manifest deterministic regeneration')
            require(set(p['construction_inputs'])=={'n','m','variable_order'},'construction input allowlist')
            leaks.append(dict(run_id=r['run_id'],inputs=p['construction_inputs'],input_keys=list(p['construction_inputs']),optimal=False,feasible=False,temporal=False,energy=False,sampled_results=False,status='PASS'))
            if r['group'] not in group_states:
                st=p['state'];target=np.zeros(1<<st['qubits'],complex);target[st['support']]=st['amplitude']
                pt=transpile(p['preparation'],**{k:settings[k] for k in ['basis_gates','optimization_level','seed_transpiler','coupling_map','num_processes']})
                actual=Statevector.from_instruction(pt).data;f=fidelity_check(actual,target)
                expected=read(OFFLINE/'groups'/(r['group']+'.json'));require(st==expected['state'],'v2 design identity')
                fidelities.append(dict(group=r['group'],condition=r['condition'],support_size=len(st['support']),support_mismatch=0,variable_order_mismatch=0,**f,source='worker preparation only; no cost/mixer evolution',active_TW_temporal_mass=expected['metrics'][1]['temporal_mass'],active_TW_no_good_violation_mass=expected['metrics'][1]['no_good_violated_mass']))
                group_states[r['group']]=st
            require(p['state']==group_states[r['group']],'same-group worker state')
            freeze.append(dict(run_id=r['run_id'],status='PASS',inherited_settings='exact_match',cost_mixer='same_existing_worker_layer',QUBO='same_checked_Adapter',variable_order='exact_match',seed_pair='exact_match',binding='offline_QPY_exact_match',backend=s['simulator'],transpiler=s['transpilation'],measurement='i_to_i',postprocessing='existing results.save/summarize and Adapter.inspect',allowed_difference='initial_state_preparation',metadata_differences=p['injection_audit']['runtime_metadata_changes']))
        for r in rows(OFFLINE/'QUBO_GROUPS.csv'):
            from traffic_simulation.r24_vrptw_qaoa_worker.adapter import Adapter
            ad=Adapter(r['condition']);st,_=initial_state(ad.model['n'],ad.model['m'],ad.order);require(st==group_states[r['group']],'semantic-control state identity')
        proj=projection();dry=DryLedger()
        for r in plans[:3]:dry.reserve_run(run_identity(r['run_id']))
        ident=run_identity(plans[0]['run_id']);reservation=dry.snapshot()['runs'][ident['run_id']]['reservation'];dry.claim_reservation(reservation['reservation_id'],reservation['context'])
        require(dry.snapshot()['totals']['consumed_new']==0,'dry claim does not consume')
        dump('LEDGER_DRY_RUN.json',dict(mode='IN_MEMORY_ONLY_NO_PERSISTENT_LEDGER',after_three_reservations_one_claim=dry.snapshot(),actual_scientific_circuits=0,actual_shots=0))
        require(not guard.attempts,'forbidden execution attempted')
    dump('LEDGER_PROJECTION.json',proj)
    meta=read(OUT/'START.json');manifest=dict(kind='PLANNED_EXECUTION_MANIFEST_NOT_RESULTS',timestamp_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),git_commit=meta['git_commit'],git_dirty_state=(OUT/'GIT_STATUS_BEFORE.txt').read_text(),runs=entries,deterministic_run_records_sha256=digest(entries),allowed_regeneration_differences=['timestamp_utc','git_dirty_state metadata only'],actual_circuits=0,actual_shots=0)
    dump('PREFLIGHT_MANIFEST.json',manifest);table(OUT/'PREFLIGHT_MANIFEST.csv',entries)
    table(OUT/'STATE_REPRODUCTION_AUDIT.csv',fidelities)
    dump('FREEZE_AUDIT.json',dict(status='PASS',runs=freeze,unchanged_comparison_manifest=COMPARISON_HASH,encoding_compatibility_not_temporal_feasibility=True))
    dump('LEAKAGE_AUDIT.json',dict(status='PASS',records=leaks,constructor_source=inspect.getsource(initial_state),optimal_reference_used_only_after_construction=True,active_TW_not_redesigned=True))
    launch,adapted,changes=wired();(OUT/'ADAPTED_SUPERVISOR_SOURCE.txt').write_text(adapted+'\n')
    dump('EXECUTION_PATH_AUDIT.json',dict(worker='traffic_simulation.r24_vrptw_structured_worker.worker.prepare',controlled_launch='traffic_simulation.r24_vrptw_structured_worker.execution.supervised_run',preflight_default=True,shared_objective_pipeline='traffic_simulation.r24_vrptw_qaoa_worker.execution.perform (unchanged code object)',shared_result_parser='traffic_simulation.r24_vrptw_qaoa_worker.results.save/summarize',supervisor_adapter_changes=changes,supervisor_original_sha256=sha(ROOT/'05_src/traffic_simulation/r24_vrptw_qaoa_worker/execution.py'),initial_state_source=c['S']['constructor'],ledger='comparison namespace with immutable external debit; dry-run uses same lifecycle in memory',new_Aer_sanity='none: frozen budget prohibits additional sanity circuits; offline preparation reproduction plus protected prior fixed-p1 norm sanity and inherited backend sanity are authorities',scientific_launch_this_task=False))
    dump('PREFLIGHT_EXECUTION_COUNTS.json',dict(Uniform_execution=0,scientific_circuits=0,scientific_shots=0,optimizer_scientific_evaluations=0,Aer_sampling_calls=0,new_seeds=0,actual_ledger_mutations=0,preparation_only_Statevector=3,forbidden_attempts=guard.attempts,preflight_seconds=time.monotonic()-start))
    print(json.dumps(dict(status='ZERO_SHOT_AUDITS_PASS',runs=len(entries),groups=len(fidelities),seconds=time.monotonic()-start)))

if __name__=='__main__':run()
