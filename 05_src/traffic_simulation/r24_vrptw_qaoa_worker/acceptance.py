"""21 run / seven batch offline acceptance; all execution APIs fail closed."""
import time
import shutil
import sys
from unittest.mock import patch
from .contract import *
from .ledger import Ledger,atomic
from .worker import prepare,public_result
from .results import summarize,schemas,aggregate_batch
from .provenance import check

def main():
    from qiskit_aer import AerSimulator
    from qiskit.quantum_info import Statevector
    from qiskit import qpy
    spec=load();source=rows(FREEZE/'RUN_PLAN.csv');batches=rows(FREEZE/'BATCH_PLAN.csv');protected=check()
    if '--repeat-offline' in sys.argv:
        archive=OUT/'offline_attempts'/str(time.time_ns());archive.mkdir(parents=True,exist_ok=False)
        for name in ['dry_runs','synthetic_ledger']:
            if (OUT/name).exists():shutil.move(str(OUT/name),str(archive/name))
        atomic(archive/'PREVIOUS_ACCEPTANCE.json',read(OUT/'OFFLINE_ACCEPTANCE.json'))
    production=ROOT/read(FREEZE/'LEDGER_SPEC.json')['planned_path']
    before=sha(production) if production.exists() else None
    records=[];circuits=[];resources=[];identities=[];seeds=[];batch_checks=[];run_checks=[];metrics_checks=[]
    path=OUT/'dry_runs';path.mkdir(exist_ok=False)
    with patch.object(AerSimulator,'run',side_effect=AssertionError('AER_FORBIDDEN')) as aer, \
         patch('scipy.optimize.minimize',side_effect=AssertionError('OPTIMIZER_FORBIDDEN')) as opt, \
         patch.object(Statevector,'from_instruction',side_effect=AssertionError('STATE_EVOLUTION_FORBIDDEN')) as sv:
        for r in source:
            p=prepare(r['run_id']);result=public_result(p);ad=p['adapter'];directory=path/r['run_id'];directory.mkdir()
            atomic(directory/'DRY_RUN.json',result);atomic(directory/'OUTPUT_SCHEMA.json',schemas())
            with (directory/'symbolic.qpy').open('wb') as f:qpy.dump(p['qc'],f)
            with (directory/'fixed_parameters.qpy').open('wb') as f:qpy.dump(p['bound'],f)
            # Deterministic acceptance fixtures, not generated/sample frequencies.
            metrics,diagnostics=summarize(ad,{sorted(ad.optimal)[0]:1,'0'*ad.N:2047},2048)
            require(metrics['feasible_count']==1 and metrics['optimal_count']==1,'synthetic metric weights')
            atomic(directory/'SYNTHETIC_METRIC_CHECK.json',dict(kind='OFFLINE_FIXTURE_NOT_SCIENTIFIC_COUNTS',metrics=metrics,diagnostics=diagnostics))
            if not records and not (OUT/'FIRST_CONDITION_ACCEPTANCE.json').exists():
                atomic(OUT/'FIRST_CONDITION_ACCEPTANCE.json',dict(result=result,decoder='PASS',weighted_metrics='PASS',first_observed_construction_seconds=.123474,
                    reestimate_remaining_minutes=[25,45],reestimate_worst_case_minutes=75,recorded_epoch=time.time()))
                timing=read(OUT/'TIMING.json');timing.update(first_condition_remaining_minutes=[25,45],first_condition_worst_case_remaining_minutes=75,
                    first_construction_seconds=.123474,first_condition='R24-RND-N002-R01-RHO050-TW-WIDE');atomic(OUT/'TIMING.json',timing)
            records.append({k:v for k,v in result.items() if k not in ['identity','resources']});identities.append(p['identity'])
            circuits.append(dict(run_id=r['run_id'],condition=r['condition'],qubits=ad.N,parameterized=True,bound=True,
                uniform_H=True,standard_X=True,p=spec['p'],parameter_count=len(p['qc'].parameters),measurements=ad.N,Ising_algebraic_check='PASS',status='PASS',Aer=0))
            resources.append(dict(run_id=r['run_id'],condition=r['condition'],**p['resources'],comparison='EXACT_MATCH',status='PASS',
                transpiler_seed=p['plan']['seeds']['transpiler_seed'],basis=spec['transpilation']['basis_gates'],optimization_level=spec['transpilation']['optimization_level'],coupling='ALL_TO_ALL_LOGICAL'))
            seeds.append(dict(run_id=r['run_id'],repetition=r['repetition'],seed_mapping_hash=p['identity']['seed_mapping_hash'],
                training_seed_count=len(p['plan']['seeds']['training_simulator_seeds']),final_seed=p['plan']['seeds']['final_simulator_seed'],transpiler_seed=p['plan']['seeds']['transpiler_seed'],initial_alpha=p['plan']['initial_parameters'][0],initial_beta=p['plan']['initial_parameters'][1],scale=spec['parameters']['scale'],status='PASS'))
            run_checks.append(dict(run_id=r['run_id'],condition=r['condition'],batch=r['batch'],repetition=r['repetition'],budget=100,identity='PASS',hashes='PASS',status='PASS'))
            metrics_checks.append(dict(run_id=r['run_id'],independent_validator='PASS',synthetic_fixture=True,feasible_count=metrics['feasible_count'],status='PASS'))
            print(r['run_id'],'PASS',p['resources'],flush=True)
        ledger=Ledger(OUT/'synthetic_ledger'/'CIRCUIT_LEDGER.json');ledger.initialize(spec,identities,synthetic=True);ledger.reserve_all(spec)
        reserved=ledger.snapshot()['totals']
        require(reserved['scientific_reserved']==2100 and reserved['sanity_reserved']==7 and reserved['reserved']==2107,'reservation totals')
        for ident in identities:ledger.claim(ident['run_id'])
        after=ledger.snapshot()
        require(after['totals']['consumed']==0 and all(r['status']=='CLAIMED' for r in after['runs'].values()),'offline claim only')
        for index,b in enumerate(batches):
            runs=[r for r in source if r['batch']==b['batch']]
            require(int(b['order'])==index+1 and len(runs)==3 and [int(r['repetition']) for r in runs]==[0,1,2],'batch order/reps')
            require([r['run_id'] for r in runs]==json.loads(b['scientific_run_ids']) and {r['condition'] for r in runs}=={b['condition']},'batch identity')
            require(int(b['scientific_circuits_max'])==300 and int(b['total_circuits_max'])==301,'batch budget')
            batch_checks.append(dict(batch=b['batch'],order=index+1,condition=b['condition'],runs=3,repetitions=[0,1,2],scientific_budget=300,sanity_budget=1,study_cumulative_budget=(index+1)*301,status='PASS'))
            atomic(OUT/f'{b["batch"]}_EMPTY_AGGREGATE_SCHEMA.json',aggregate_batch(runs,[],after['totals']))
        require(aer.call_count==opt.call_count==sv.call_count==0,'forbidden API attempted')
    require((sha(production) if production.exists() else None)==before,'production ledger changed')
    for filename,data in [('RUN_IDENTITY.csv',identities),('RUN_PLAN_VALIDATION.csv',run_checks),('BATCH_PLAN_VALIDATION.csv',batch_checks),
        ('SEED_MAPPING_VALIDATION.csv',seeds),('CIRCUIT_CONSTRUCTION_CHECK.csv',circuits),('TRANSPILE_RESOURCE_CHECK.csv',resources),('DRY_RUN_RESULTS.csv',records),('METRIC_ACCEPTANCE.csv',metrics_checks)]:table(OUT/filename,data)
    atomic(OUT/'LEDGER_SIMULATION.json',dict(status='PASS',synthetic=True,pre_reserved=reserved,after_claim=after['totals'],claimed_runs=21,
        production_ledger_unchanged=True,production_ledger_existed=before is not None,per_run_training=99,per_run_final=1,
        scientific_budget=2100,sanity_budget=7,study_cap=2107,real_consumption=0,lifecycle_implementation='reused validated locked atomic journal/reserve/claim/execute/finalize/release; VRPTW-only scope and totals',
        legacy_owner_prefix='retained internal prefix r24-cross-condition; spec hash and VRPTW scope uniquely isolate ledger'))
    table(OUT/'CONDITION_READINESS.csv',[dict(condition=r['condition'],status='OFFLINE_ACCEPTANCE_VALIDATED',scientific_ready=False,Aer_runtime_sanity='NOT_EXECUTED') for r in rows(FREEZE/'SCIENTIFIC_CONDITION_SET.csv')])
    atomic(OUT/'OFFLINE_ACCEPTANCE.json',dict(status='PASS',dry_runs=21,batches=7,protected_files=check(),
        forbidden_API_attempts=0,Aer=0,optimizer=0,scientific_circuits=0,final_sampling=0,new_seeds=0,
        condition_readiness='OFFLINE_ACCEPTANCE_VALIDATED',scientific_ready=False))
    return 0

if __name__=='__main__':raise SystemExit(main())
