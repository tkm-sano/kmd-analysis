"""Post-run raw ledger and preservation audit. No solver or quantum execution."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .study import ROOT,OUT,DOC,read,dump
from .model import seed_for
from .analyze import closed_payloads


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()


def main():
    # Read-only historical ledger audit must record drift rather than bypass
    # the execution guard. study.check_pins remains unchanged and rejects runs.
    manifest=read(OUT/'MANIFEST.json');protocol=read(OUT/'PROTOCOL.json')
    pin_drift=[{'path':name,'before_sha256':expected,'current_sha256':current}
        for name,expected in {**manifest['source_hashes'],**manifest['input_hashes']}.items()
        if (current:=sha(ROOT/name))!=expected]
    if pin_drift:
        dump(DOC/'SOURCE_PIN_ALERT.json',{'status':'EXECUTION_GUARD_REJECTS_CURRENT_TREE','changes':pin_drift,
            'historical_ledger_audit_only':True,'execution_guard_not_relaxed':True,'new_execution_permitted':False})
    checks=[];counts={'optimization':0,'final_extraction':0};states=0;calls=0;incomplete=[]
    call_dirs=sorted(p.parent for p in (OUT/'groups').glob('*/branch_*/calls/*/CALL.json'))
    job_cache={}
    for folder,payload in closed_payloads(call_dirs):
        assert payload is not None
        meta=payload['metadata'];job_path=folder.parent.parent/'JOB.json'
        if job_path not in job_cache:job_cache[job_path]=read(job_path)
        job=job_cache[job_path]
        r,k=[int(x[1:]) for x in folder.name.split('_')]
        assert 1<=r<=job['R'] and 1<=k<=job['K']
        assert meta['seed']==seed_for(job['outer_seed'],job['branch'],r,k)
        assert meta['depth_p']==2 and meta['optimization_shots']==1000 and meta['final_extraction_shots']==10000
        assert meta['n']==job['n']==len(set(meta['local']['customer_ids']))
        assert meta['bond']=={10:1024,12:1280}[job['n']] and meta['cutoff']==1e-18 and meta['TV_threshold']==1e-6
        assert meta['settings']==protocol['optimizer_pilot_only']
        assert meta['oracle']['version']=='boundary_D_v2' and meta['circuit']['angle_parameter_count']==4
        assert meta['circuit']['cost_layers']==meta['circuit']['mixer_layers']==2
        raw=payload['progress'];completed=[e for e in raw if e['event']=='sampling_completed']
        started=[e for e in raw if e['event']=='sampling_started']
        for e in completed:
            assert e['depth_p']==2 and e['cost_layer_ids']==e['mixer_layer_ids']==[1,2]
            assert 0<=e['TV_bound']<=1e-6
            expected=1000 if e['phase']=='optimization' else 10000
            assert e['requested_shots']==e['actual_shots']==sum(e['counts'].values())==expected
            assert e['seed']==meta['seed']+(e['evaluation']-1 if e['phase']=='optimization' else 100000)
            assert len(e['angles'])==4
            counts[e['phase']]+=e['actual_shots'];states+=1
        optimization=[e for e in completed if e['phase']=='optimization']
        final=[e for e in completed if e['phase']=='final_extraction']
        result_path=folder/'RESULT.json';result=payload['quantum']
        if result is not None:
            calls+=1
            assert len(started)==len(completed)
            assert result['nfev']==result['scipy_nfev']==len(optimization)<=8
            assert len(final)==1
            assert result['training_shots_actual']==len(optimization)*1000 and result['final_shots_actual']==10000
            assert result['max_TV_bound']==max(e['TV_bound'] for e in completed)
            assessment=payload['assessment']
            if assessment:
                assert assessment['assessment']['checked']<=3
                for candidate in assessment['assessment']['ledger']:
                    if 'metrics' not in candidate:continue
                    bits=format(candidate['bits'],f"0{meta['circuit']['sdk_qubits']}b")
                    assert bits in final[0]['counts']
                    assert candidate['count']==final[0]['counts'][bits]
                    assert (OUT/candidate['plan']).is_file()
                    assert candidate['metrics']['evaluation_version']=='ota-toc-cargo-wait-20261119-v2'
        else:
            incomplete.append({'call':str(folder.relative_to(OUT)),'completed_states':len(completed),
                               'inflight_shots':None if len(started)!=len(completed) else 0,
                               'failure':payload['failure']})
        checks.append({'call':str(folder.relative_to(OUT)),'n':job['n'],'states_checked':len(completed),'complete':result is not None})
    before=read(DOC/'PRESERVATION_BEFORE.json')
    changed=[name for name,h in before['files'].items() if sha(ROOT/name)!=h]
    drift=[{'path':name,'before_sha256':before['files'][name],'current_sha256':sha(ROOT/name)} for name in changed]
    if changed:
        dump(DOC/'PRESERVATION_ALERT.json',{'status':'CHANGED_DO_NOT_RESTORE_OTHER_WORK','changes':drift,
            'scope':'detected outside new pilot directories; do not claim blanket preservation PASS; baseline hashes remain unchanged'})
    summary=read(OUT/'SUMMARY.json')
    assert summary['actual_quantum_calls_complete']==calls
    assert summary['actual_optimization_shots']==counts['optimization'] and summary['actual_final_shots']==counts['final_extraction']
    tests=set();test_sources=[]
    for file in [DOC/'TESTS_FINAL.xml',DOC/'TESTS_SCHEDULE.xml',DOC/'TESTS_SAVED_DATA.xml']:
        if not file.exists():continue
        tree=ET.parse(file)
        for suite in tree.iter('testsuite'):
            assert int(suite.attrib.get('failures',0))==int(suite.attrib.get('errors',0))==0
        for case in tree.iter('testcase'):
            if case.find('skipped') is None:tests.add((case.attrib['classname'],case.attrib['name']))
        test_sources.append(str(file.relative_to(ROOT)))
    result={'status':'PASS_LEDGER_PRESERVATION' if not changed and not pin_drift else 'CONDITIONAL_LEDGER_PASS_WORKSPACE_DRIFT',
        'ledger_status':'PASS','preservation_status':'UNCHANGED' if not changed else 'DRIFT_DETECTED',
        'source_pin_status':'PASS' if not pin_drift else 'CURRENT_EXECUTION_GUARD_REJECTS',
        'source_pin_drift':pin_drift,'current_tree_run_authorized':False,
        'complete_quantum_calls':calls,'completed_states_checked':states,
        'shots_recalculated':counts,'incomplete_calls':incomplete,'checked_existing_files':len(before['files']),
        'preserved_existing_files':len(before['files'])-len(changed),
        'changed_existing_files':changed,'preservation_drift':drift,'distinct_tests_passed':len(tests),'test_xml':test_sources,
        'runtime_all_updates_guard':'all states monitored at runtime using unchanged sector core; raw updates compressed per call',
        'posthoc_scope':'all completed states/shot counts and all checked candidate membership; independent final-plan arithmetic in saved-data tests',
        'checks':checks,'main_experiment':False}
    dump(OUT/'VERIFICATION.json',result)
    dump(DOC/'PRESERVATION_AFTER.json',{'unchanged':not changed,'checked_existing_files':len(before['files']),
        'changed':changed,'HEAD':manifest['HEAD'],'main_experiment':False,'commit_push':False})
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))


if __name__=='__main__':main()
