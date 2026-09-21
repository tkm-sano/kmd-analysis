"""Final evidence cross-check and provenance (no execution)."""
import time
import subprocess
from .contract import *
from .ledger import atomic
from .provenance import check,DOCS
from .worker import prepare
from .results import schemas

def main():
    spec=load();unit=read(OUT/'UNIT_TEST_RESULTS.json');regression=read(OUT/'REGRESSION_TEST_RESULTS.json');acceptance=read(OUT/'OFFLINE_ACCEPTANCE.json')
    require(unit['status']==regression['status']==acceptance['status']=='PASS','acceptance/test status')
    for result in [unit,*regression['suites']]:
        require(result['forbidden_call_attempts']==dict(Aer=0,optimizer=0,state_evolution=0),'forbidden execution')
    expected=rows(FREEZE/'RUN_PLAN.csv');dry=rows(OUT/'DRY_RUN_RESULTS.csv');ids=rows(OUT/'RUN_IDENTITY.csv')
    require([r['run_id'] for r in expected]==[r['run_id'] for r in dry]==[r['run_id'] for r in ids],'run order')
    require(len(expected)==21 and len(rows(OUT/'BATCH_PLAN_VALIDATION.csv'))==7,'full coverage')
    for r in dry:require(r['status']=='PASS' and all(int(r[k])==0 for k in ['scientific_circuits','Aer','optimizer','final_sampling']),'dry-run zero execution')
    # Recheck final source revision, without simulation, against recorded identities/resources.
    from qiskit_aer import AerSimulator
    from unittest.mock import patch
    checks=[]
    with patch.object(AerSimulator,'run',side_effect=AssertionError('AER_FORBIDDEN')) as a,patch('scipy.optimize.minimize',side_effect=AssertionError('OPTIMIZER_FORBIDDEN')) as o:
        for r in expected:
            p=prepare(r['run_id']);saved=read(OUT/'dry_runs'/r['run_id']/'DRY_RUN.json')
            require(p['identity']==saved['identity'] and p['resources']==saved['resources'],'final-source recheck')
            checks.append(dict(run_id=r['run_id'],status='PASS'))
        require(a.call_count==o.call_count==0,'forbidden invocation')
    table(OUT/'FINAL_SOURCE_RECHECK.csv',checks)
    document_checks={}
    for name,before in read(OUT/'DOCUMENT_PREFIXES_BEFORE.json').items():
        data=(ROOT/name).read_bytes();prefix=hashlib.sha256(data[:before['bytes']]).hexdigest()
        require(prefix==before['sha256'] and len(data)>before['bytes'],'documentation not append only')
        document_checks[name]=dict(status='PASS',old_bytes=before['bytes'],appended_bytes=len(data)-before['bytes'],sha256=sha(ROOT/name))
    atomic(OUT/'DOCUMENT_PREFIX_VALIDATION.json',document_checks)
    n=check();atomic(OUT/'PROTECTED_AFTER.json',read(OUT/'PROTECTED_BEFORE.json'))
    source={str(p.relative_to(ROOT)):sha(p) for p in Path(__file__).parent.glob('*.py')}
    atomic(OUT/'SOURCE_SHA256.json',source)
    worker=read(OUT/'WORKER_SPEC.json');worker.update(status='VRPTW_QAOA_WORKER_OFFLINE_ACCEPTANCE_VALIDATED',
        modules=list(source),source_hash_manifest='SOURCE_SHA256.json',future_schemas=schemas(),
        scientific_entry='execution.supervised_run requires explicit separate authorization, real sanity receipt, monitored child and global exclusive worker lock',
        default_entry='worker.prepare / offline CLI only',current_condition_readiness='OFFLINE_ACCEPTANCE_VALIDATED',
        inherited_gate='r24_qaoa_resource_gate_redesign.gates.GateEngine with frozen VRPTW config; no physical threshold changes',
        automatic_retry=False,production_ledger_consumption=0,structured_initial_state='DEFERRED',hybrid_mixer='EXCLUDED',
        limitations=['No actual Aer/runtime sanity or optimizer has been validated by this offline task','23-bit conditions excluded by frozen plan'])
    atomic(OUT/'WORKER_SPEC.json',worker)
    timing=read(OUT/'TIMING.json');timing.update(end_epoch=time.time(),actual_runtime_seconds=time.time()-timing['start_epoch']);atomic(OUT/'TIMING.json',timing)
    summary=dict(status=worker['status'],source_execution_spec=str(FREEZE.relative_to(ROOT)),source_manifest_sha256=MANIFEST_SHA256,
        timing=timing,conditions=[r['condition'] for r in rows(FREEZE/'SCIENTIFIC_CONDITION_SET.csv')],planned_runs=21,planned_batches=7,
        implemented='identity/QUBO adapter, Standard circuit, decoder/independent validation, metrics, artifacts, VRPTW ledger, future supervised executor',
        run_identity='21/21 PASS',QUBO_hash='21/21 PASS',variable_order='21/21 PASS',encoding='COMPILED_TEMPORAL_NOGOODS unchanged',
        seeds='all99 training plus final per repetition inherited, transpiler170917; no new seeds',
        initial_parameters=spec['parameters'],QAOA_definition='Uniform H on every qubit + Standard X; p=1',optimizer=spec['optimizer'],shots=spec['shots'],
        construction='21/21 PASS',binding='21/21 PASS',transpilation='21/21 PASS',resource_snapshot='exact match; tolerance not relaxed',
        condition_resources=rows(FREEZE/'RESOURCE_SNAPSHOT.csv'),decoder='raw/no repair; all exact feasible authority states and invalid fixtures checked',
        temporal_replay='existing independent exact-rational validator; waiting/service/start/end/return; structural failures NOT_EVALUABLE',
        violations='visit/route/capacity/TW/depot separate; independent early-service and precedence not encoded => null, replay invariants separate',
        penalties='base objective + existing CVRP + temporal/depot no-good + quadratization; coefficient identity tolerance1e-6',
        ledger_cap=2107,training_cap_per_run=99,final_cap_per_run=1,per_run_cap=100,scientific_budget=2100,sanity_budget=7,
        reservation_simulation='2107 reserved,21 claimed,0 consumed; production ledger unchanged',duplicate_protection='exclusive claims and pinned completed result/manifest idempotency',
        automatic_retry=False,zero_feasible_is_stop=False,dry_runs_pass=21,batch_dry_runs_pass=7,
        unit_tests=unit['tests_run'],regression_tests=regression['tests_run'],unit_status=unit['status'],regression_status=regression['status'],
        scientific_Aer_executions=0,optimizer_executions=0,scientific_circuits_consumed=0,final_sampling=0,new_seeds=0,
        resource_warnings='No static resource discrepancies; live Aer memory/PSI behavior not exercised',
        test_fixture_issue='Initial existing CVRP fresh-run test saw completed artifact; output lookup isolated, original assertions retained; history preserved',
        protected_hash_validation=dict(status='PASS',files=n),condition_readiness='OFFLINE_ACCEPTANCE_VALIDATED',scientific_ready=False,
        notebook_updates=0,integrated_docs=DOCS,
        unresolved_issues=['Aer runtime readiness remains unmeasured; actual backend/process-supervisor integration is not proven by synthetic execution'],
        next_task='Separate authorized fixed-parameter non-sampling Aer runtime sanity for the seven frozen conditions')
    atomic(OUT/'EXECUTION_SUMMARY.json',summary)
    atomic(OUT/'VALIDATION.json',dict(status='PASS',worker_status=worker['status'],dry_runs='21/21',batches='7/7',
        hashes='PASS',seeds='PASS',construction='PASS',transpilation='PASS',resources='PASS',ledger_simulation='PASS',
        unit_tests=unit['tests_run'],regression_tests=regression['tests_run'],scientific_executions=0,protected_files=n,
        frozen_spec_changed=False,scientific_ready=False,condition_readiness='OFFLINE_ACCEPTANCE_VALIDATED'))
    for filename,args in [('GIT_STATUS_AFTER.txt',['git','status','--short']),('GIT_DIFF_STAT.txt',['git','diff','--stat'])]:
        output=subprocess.check_output(args,cwd=ROOT,text=True);(OUT/filename).write_text(output);print(' '.join(args)+'\n'+output)
    manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='FINAL_ARTIFACT_MANIFEST.json'}
    atomic(OUT/'FINAL_ARTIFACT_MANIFEST.json',manifest)
    print(json.dumps(dict(status=worker['status'],actual_runtime_seconds=timing['actual_runtime_seconds'],protected_files=n,unit_tests=unit['tests_run'],regression_tests=regression['tests_run'],outputs=len(manifest)),indent=2))

if __name__=='__main__':main()
