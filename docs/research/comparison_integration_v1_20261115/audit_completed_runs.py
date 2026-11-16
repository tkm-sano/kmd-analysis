"""Read-only final checks of saved actual paths, plans, histories and frozen assets."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median
import tarfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
PREFIX='output/toc_delivery/comparison_integration_v1_20261115_'
ROOTS=['A_checks01','small01','A_checks02','small02','small03']


def read(p):return json.loads(Path(p).read_text())


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def save(name,value):
    with (HERE/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def main():
    checks=[];history=[]
    def check(name,value):checks.append({'check':name,'pass':bool(value)})
    for name in ROOTS:
        root=ROOT/(PREFIX+name);manifest=read(root/'REGISTERED.json')
        table_name={'A_checks01':'A_tables01','small01':'small_tables01','A_checks02':'A_tables02',
                    'small02':'small_tables02_not_executed','small03':'small_tables03'}[name]
        scored={r['run_id']:r for r in read(ROOT/(PREFIX+table_name)/'ALL_ATTEMPTS.json')['rows']}
        # Archive validates each historical code version; current adapter may
        # intentionally differ after a documented diagnostic correction.
        with tarfile.open(root/'SOURCE_SNAPSHOT.tar.gz') as archive:
            check(name+':snapshot_pins',all(hashlib.sha256(archive.extractfile(p).read()).hexdigest()==h
                  for p,h in manifest['source_hashes'].items()))
        end=None
        for run in manifest['runs']:
            directory=root/'runs'/run['run_id'];path=directory/'result.json'
            if not path.exists():
                history.append({'registration':str(root.relative_to(ROOT)),'run_id':run['run_id'],
                    'method':run['method'],'executed':False,'reason':'REGISTERED_R2_SUPERSEDED_BEFORE_EXECUTION_BY_RESOURCE_LOGGING_FIX'})
                check(name+':only_intentional_not_run',name=='small02')
                continue
            r=read(path);history.append({**r,'J':scored[r['run_id']]['J'],'J_reason':scored[r['run_id']]['J_reason'],
                'registration':str(root.relative_to(ROOT)),'executed':True})
            hashes=read(directory/'OUTPUT_HASHES.json')
            check(run['run_id']+':output_hashes',all(digest(directory/p)==h for p,h in hashes.items()))
            check(run['run_id']+':common_deadline',r['T_program'] is None or r['T_program']<=r['budget_wall_s'])
            check(run['run_id']+':children_reaped',r['process_control']['cleanup']['session_empty'])
            start=read(directory/'job.json')['deadline_perf_counter']-r['budget_wall_s']
            if end is not None:check(run['run_id']+':sequential',start>=end)
            end=start+r['T_attempt']
            if r['adoptable']:
                validation=read(directory/'validation.json')
                check(run['run_id']+':two_physical_checks',validation['common_physical']['feasible'] and
                      validation['independent_physical']['feasible'])
                check(run['run_id']+':wait_split',abs(r['W']-r['W_first']-r['W_reload'])<1e-9)
                check(run['run_id']+':raw_bytes_preserved',digest(directory/'candidate_plan.json')==digest(directory/'plan.json'))
            else:
                check(run['run_id']+':failed_null',all(r[k] is None for k in ('D','W','W_first','W_reload','T_program')))
    identities=[]
    for revision in ['A_checks01','A_checks02']:
        root=ROOT/(PREFIX+revision)
        for run in read(root/'REGISTERED.json')['runs']:
            new=root/'runs'/run['run_id'];r=read(new/'result.json');scale=r['scale']
            b={'S1':2,'S2':4,'S3':8}[scale]
            original=ROOT/f'output/toc_delivery/a_rule_v1_20261115_checks01/a_rule_v1_20261115_checks01_{scale}_b{b}_r1'
            old_metrics=read(original/'metrics.json')
            entry={'run_id':run['run_id'],'scale':scale,'original_sha256':digest(original/'plan.json'),
                'integrated_sha256':digest(new/'plan.json'),'same_bytes':(original/'plan.json').read_bytes()==(new/'plan.json').read_bytes(),
                'same_semantic_plan':read(original/'plan.json')==read(new/'plan.json'),
                'same_D_W_parts':all(old_metrics[k]==r[k] for k in ('D','W','W_first','W_reload')),
                'same_input_hash':old_metrics['input_hash']==r['input_hash'],
                'native_time_not_reused':r['T_kind']!='program_wall','T_program':r['T_program']}
            identities.append(entry)
            check(run['run_id']+':identity',all(entry[k] for k in ('same_bytes','same_semantic_plan','same_D_W_parts','same_input_hash')))
    standalone=ROOT/(PREFIX+'standalone_S2_01')
    expected='64114d3fed738a14198c0958a4c3cdd6bafb9c9d81926bdaf276250bd651f4d9'
    check('new_standalone_S2_exact_hash',digest(standalone/'plan.json')==expected)
    check('original_S2_expected_hash_not_changed',all(x['original_sha256']==expected and x['integrated_sha256']==expected for x in identities if x['scale']=='S2'))
    save('A_IDENTITY_VALIDATION.json',{'integrated_runs':identities,'new_standalone_S2':{
        'sha256':digest(standalone/'plan.json'),'PROCESS':read(standalone/'PROCESS.json'),
        'native_metrics':read(standalone/'metrics.json')},'T_equality_required':False})
    final=ROOT/(PREFIX+'small03');paths=[]
    for run in read(final/'REGISTERED.json')['runs']:
        directory=final/'runs'/run['run_id'];r=read(directory/'result.json')
        trace=[json.loads(s) for p in directory.glob('path_*.jsonl') for s in p.read_text().splitlines()]
        events=Counter(t['event'] for t in trace)
        required={'A':['frozen_A_rule_v1.generate'],'B':['existing_dwt.execute_parallel','directed_CW','shared_CP_completion'],
            'C':['existing_dwt.execute_parallel','directed_CW','OR_Routing','shared_CP_completion'],
            'D':['existing_dwt.execute_parallel','directed_CW','Huang_hybrid','shared_CP_completion','AOA_statevector_run']}[run['method']]
        check(run['method']+':actual_call_path',all(events[e]>0 for e in required))
        if run['method']=='A':check('A_never_enters_completion',events['shared_CP_completion']==0)
        native=read(directory/'native_result.json')
        detail={'method':run['method'],'run_id':run['run_id'],'events':dict(events),
                'adoptable':r['adoptable'],'termination_reason':r['termination_reason']}
        if run['method']!='A':
            branches=native['parallel_branches'];detail['branches']=branches
            check(run['method']+':four_branch_pids',len(branches)==4 and len({b['pid'] for b in branches})==4)
            check(run['method']+':four_distinct_cores',len({tuple(b['cpu_affinity']) for b in branches})==4 and
                  all(len(b['cpu_affinity'])==1 for b in branches))
            if run['method']=='D':
                detail['backend']=native['quantum_backend_environment']
                detail['completed_quantum_calls']=native['completed_quantum_call_observations']
                check('D_observed_simulator_calls',native['completed_quantum_call_observations']>0 and
                    native['quantum_backend_environment']['statevector_backend']=='qiskit' and
                    any('qiskit' in b['statevector_backends_observed'] for b in branches))
            if r['adoptable']:
                p=read(directory/'plan.json');meta=p['method_settings']
                pool={tuple(x) for x in meta['completion_input_routes']}
                ids=read(Path(read(final/'REGISTERED.json')['cases'][0]['input']['directory'])/'od/manifest.json')['ids']
                position={s:i for i,s in enumerate(ids)}
                check(run['method']+':completion_preserves_internal_order',all(tuple(position[s['stop_id']] for s in t['visits']) in pool for t in p['trips']))
        paths.append(detail)
    save('ACTUAL_PATH_VALIDATION.json',paths)
    tables=ROOT/(PREFIX+'small_tables03')
    scored=read(tables/'ALL_ATTEMPTS.json')['rows']
    references=read(tables/'A_REFERENCES.json')
    reference=next(iter(references['groups'].values()))
    members=[r for r in scored if r['run_id'] in reference['run_ids']]
    check('contract_check_reference_not_formal',not references['formal_T_A_ref_registered'] and
          reference['purpose']=='contract_check')
    check('reference_all_prespecified_members',len(members)==reference['required_count'])
    if reference['established']:
        check('reference_median',reference['T_A_ref']==median(r['T_program'] for r in members))
        for r in scored:
            if r['adoptable']:
                expected=(r['D']/reference['D_A']+r['W']/reference['W_A']+r['T_program']/reference['T_A_ref'])/3
                check(r['method']+':J_formula',abs(r['J']-expected)<1e-12)
    old_counts=read(ROOT/(PREFIX+'small_tables01')/'ATTEMPT_COUNTS.json')['rows']
    check('old_timeouts_kept_in_denominator',all(r['valid_input_executed']==1 and r['success_rate']==0 and
          r['limit_stop_count']==1 for r in old_counts if r['method'] in 'BCD'))
    unrun=read(ROOT/(PREFIX+'small_tables02_not_executed')/'ALL_ATTEMPTS.json')['rows']
    check('superseded_registration_stays_unexecuted',len(unrun)==4 and all(r['termination_reason']=='NOT_STARTED' for r in unrun))
    protected=read(HERE/'PRESERVATION_BEFORE.json')['files']
    changed=[p for p,h in protected.items() if digest(ROOT/p)!=h]
    check('protected_assets_unchanged',not changed)
    save('PRESERVATION_AFTER.json',{'checked':len(protected),'changed':changed})
    save('ALL_EXECUTION_HISTORY.json',{'comparison_planned':len(history),
        'comparison_executed':sum(h['executed'] for h in history),
        'registered_not_executed':sum(not h['executed'] for h in history),
        'new_standalone_executions':1,'rows':history,
        'technical_revisions_are_not_independent_samples':True})
    save('FINAL_AUDIT.json',{'pass':all(c['pass'] for c in checks),'checks':checks,
        'check_count':len(checks),'protected_count':len(protected),
        'new_small_all_adoptable':all(p['adoptable'] for p in paths)})
    print(json.dumps({'pass':all(c['pass'] for c in checks),'checks':len(checks),'changed':changed}))


if __name__=='__main__':main()
