"""Technical preparation state is independent of experimental execution state."""
from pathlib import Path
import xml.etree.ElementTree as ET
from kmd_toc.iterative_v3.io import read,dump,atomic,sha,verify_pins,load_problem,read_initial,load_plan,identity
from kmd_toc.iterative_v3.physical import metrics
from kmd_toc.objective_alignment_v1.objective import measure
from .plan import preflight,VERSION

def freeze(manifest,output):
    preflight(manifest,output);out=Path(output).resolve();m=read(manifest);c=m['configuration']
    record=dict(status='FREEZE',version=VERSION,authority='explicit user instruction: J30, achieved precision, 10 iterations / 70 completions',
        manifest_sha256=sha(manifest),configuration_sha256=m['configuration_sha256'],freeze_spec=c['freeze_spec'],freeze_spec_sha256=c['freeze_spec_sha256'],
        seed_registry_sha256=sha(out/'SEEDS.csv'),git_HEAD=m['git_HEAD'],tracked_diff_sha256=m['tracked_diff_sha256'],
        J_per_scale=30,comparison_cases=90,code_hashes=m['code_hashes'],input_hashes=m['input_hashes'],fixed_initials=m['fixed_initials'],
        search=c['search'],statistics=c['statistics'],precision_policy=c['precision_policy'],counts=m['counts'],
        C_effective={k:m['classical_configuration'][k] for k in ('C','completion')},C_native_threads=1,C_branches=1,
        superseded_for_this_version=['formal J HOLD / proposal only','a priori MCSE target prerequisite','2 iterations / 14 completions as formal budget','all four methods required in one analysis cohort','mean-D/W index as primary estimand'],
        unchanged=['legacy nKR/v2/v3 pilot outputs','physical policy and assumptions','p2 / 1000 / 10000 shots','zero and tie selection'],
        execution_state='NOT_STARTED',legacy_main_entry_disabled=True,explicit_execute_action_required=True)
    dump(out/'FREEZE_RECORD.json',record);(out/'FREEZE_RECORD.json').chmod(0o444);return record

def readiness(manifest,output):
    out=Path(output).resolve();checks=[];blockers=[];pending=[]
    try:preflight(manifest,out)
    except Exception as e:
        result=dict(preparation_state='BLOCKED',execution_state='NOT_STARTED',blockers=[repr(e)],workers_submitted=0)
        atomic(out/'READINESS.json',result);return result
    m=read(manifest);c=m['configuration'];fr=out/'FREEZE_RECORD.json'
    if not fr.exists():blockers.append('NEW_FREEZE_RECORD_MISSING')
    elif read(fr)['manifest_sha256']!=sha(manifest) or read(fr)['freeze_spec_sha256']!=c['freeze_spec_sha256']:blockers.append('FREEZE_BINDING_MISMATCH')
    old=Path(c['budget_pilot_evidence']);pm=read(old/'MANIFEST.json')
    # The old CLI executes unchanged engine code. New management/telemetry is
    # verified separately by the instrumented artificial entry and tests.
    for f,h in pm['code_hashes'].items():
        if m['code_hashes'].get(f)!=h:blockers.append('BUDGET_PILOT_ENGINE_SOURCE_CHANGED:'+f)
    if pm['configuration']['search']!=c['search'] or pm['configuration']['rest_options']!=c['rest_options']:blockers.append('BUDGET_PILOT_SETTINGS_MISMATCH')
    for case in pm['cases']:
        folder=old/case['output_subdir'];rpath=folder/'RESULT.json';check=dict(scale=case['scale'],normal=False)
        if not rpath.exists():
            alarms=[str(p) for p in folder.glob('*/executions/*/RESOURCES.json') if read(p).get('reason')]
            if alarms:blockers.append('BUDGET_PILOT_RESOURCE_STOP:'+str(alarms))
            else:pending.append('BUDGET_PILOT_INCOMPLETE:'+case['scale'])
            checks.append(check);continue
        r=read(rpath);p=load_problem(case['input'],c['rest_options']);base=load_plan(r['conditions']['B']['plan']);ref=measure(p,base)
        valid=True;calls=0
        for method in ('D_classical','D_quantum'):
            row=r['conditions'][method]
            if row['status']!='COMPLETE_FOUR_BRANCHES' or metrics(p,load_plan(row['plan']),ref)!=row['metrics']:valid=False
            for b in range(4):
                work=folder/method/f'branch_{b}/work';br=read(work/'RESULT.json')
                if br['status']!='COMPLETE' or br['completed_iterations']!=10 or br['counters']['completion_requests']>70 or br['remaining_completions']!=70-br['counters']['completion_requests']:valid=False
                previous=r['initial_hash']
                for path in sorted(work.glob('iteration_*/COMMIT.json')):
                    commit=read(path);prep=read(path.parent/'PREPARED.json')
                    if commit['input_hash']!=previous or prep['input_hash']!=previous:valid=False
                    if identity(load_plan(commit['adopted_plan_path']))!=commit['adopted_hash']:valid=False
                    previous=commit['adopted_hash']
                for path in work.glob('iteration_*/local_*/DECODED_*.json'):
                    d=read(path)
                    if d['assignment_before']!=d['assignment_after']:valid=False
                if method=='D_quantum':
                    for path in work.glob('iteration_*/local_*/solver/RESULT.json'):
                        q=read(path);h=read(path.parent/'CALL.json');calls+=1
                        if len(h['problem']['ids'])!=12 or q['p']!=2 or q['optimization_shots']!=1000 or q['final_shots']!=10000 or q['max_TV_bound']>1e-6:valid=False
                        if q['training_evaluations']>24 or q['total_shots_actual']!=q['training_evaluations']*1000+10000:valid=False
        if not valid or calls==0:blockers.append('BUDGET_PILOT_TECHNICAL_FAILURE:'+case['scale'])
        check.update(normal=valid,actual_n12_QAOA_calls=calls);checks.append(check)
    tests=[]
    for name in c['validation_xml']:
        file=Path(name)
        if not file.exists():pending.append('VALIDATION_XML_PENDING:'+name);continue
        tree=ET.parse(file);cases=list(tree.iter('testcase'));bad=[x.attrib.get('name') for x in cases if x.find('failure') is not None or x.find('error') is not None]
        if not cases or bad:blockers.append('VALIDATION_FAILED:'+name)
        tests.append(dict(path=name,sha256=sha(file),cases=len(cases),failures=bad))
    probe=Path(c['entry_probe'])/'RESULT.json'
    if not probe.exists():pending.append('INSTRUMENTED_ENTRY_PROBE_PENDING')
    else:
        r=read(probe)
        if r['status']!='COMPLETE':blockers.append('ENTRY_PROBE_NOT_NORMAL')
        if read(probe.parent/'MANIFEST.json')['code_hashes']!=m['code_hashes']:blockers.append('ENTRY_PROBE_SOURCE_VERSION_MISMATCH')
        sample=list(probe.parent.glob('D_quantum/branch_*/work/PHASES_ATTEMPT_*.json'))
        if not sample or not all(read(p)['MPS_sample_calls_this_attempt']>0 for p in sample):blockers.append('ENTRY_TELEMETRY_NOT_EXECUTED')
    diag=Path(c['diagnosis_evidence'])/'DIAGNOSIS.json'
    if not diag.exists():pending.append('PRIOR_LOG_DIAGNOSIS_PENDING')
    elif read(diag)['violations']:blockers.append('PRIOR_LOG_DIAGNOSIS_INCONSISTENCY')
    state='BLOCKED' if blockers else 'VALIDATION_PENDING' if pending else 'EXPERIMENT_READY'
    execution=read(out/'EXECUTION_STATE.json')['state'] if (out/'EXECUTION_STATE.json').exists() else 'NOT_STARTED'
    result=dict(preparation_state=state,EXPERIMENT_READY=state=='EXPERIMENT_READY',execution_state=execution,
        J=30,precision_policy='achieved precision, no a priori numeric target',blockers=blockers,pending=pending,
        scale_checks=checks,tests=tests,counts=m['counts'],workers_submitted=0,
        improvement_required=False,mathematical_convergence_required=False,QPU=False,field_stopping_sites='UNVERIFIED_MODEL_ASSUMPTION',
        old54_restarted=False,explicit_execute_action_required=True)
    atomic(out/'READINESS.json',result);return result
