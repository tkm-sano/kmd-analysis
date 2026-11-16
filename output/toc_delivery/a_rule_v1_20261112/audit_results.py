"""Re-read saved results, independently check estimates/ranges and preservation."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import csv
import difflib
import hashlib
import json
import statistics
import subprocess
import time
from kmd_toc.baseline_a.config import load_settings, settings_block, SHA256
from kmd_toc.baseline_a.independent import recompute
from kmd_toc.common.models import load_problem, load_plan
from kmd_toc.common.validation import validate_plan

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DOCS=ROOT/'docs/research/toc_delivery_a'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as s:
        for b in iter(lambda:s.read(1048576),b''):h.update(b)
    return h.hexdigest()


def csv_rows(p):
    with p.open() as f:return list(csv.DictReader(f))


def main():
    start=time.perf_counter();checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    cfg=load_settings();reg=json.loads((HERE/'PREREGISTRATION.json').read_text())
    check('no_BD_result_based_parameter_selection',reg['BD_performance_results_used'] is False)
    for name,h in reg['files'].items():check('preregistered_'+name,sha(ROOT/name)==h)
    implementation=json.loads((HERE/'IMPLEMENTATION_HASHES.json').read_text())
    for name,h in implementation.items():check('implementation_'+name,sha(ROOT/name)==h)
    text=(DOCS/'A_RULE_BASELINE_SPEC.md').read_text()
    check('doc_settings_match',text.split('<!-- BEGIN GENERATED A RULE SETTINGS -->\n')[1].split('\n<!-- END GENERATED A RULE SETTINGS -->')[0]==settings_block())
    for source in json.loads((HERE/'SOURCE_MANIFEST.json').read_text()):check('primary_'+source['id'],sha(ROOT/source['path'])==source['sha256'])
    inventory=json.loads((HERE/'OD_INVENTORY.json').read_text())
    check('real_input_HOLD_based_on_inventory',len(inventory['available_bundles'])==12 and all(r['kind']=='synthetic' for r in inventory['available_bundles']))
    data=json.loads((HERE/'results/SUMMARY.json').read_text());raw=csv_rows(HERE/'results/CONDITIONAL_RESULTS.csv')
    check('36_test_plus_27_input_hold_rows',len(raw)==len(data['rows'])==63)
    check('same_registered_settings',all(r['settings_sha256']==SHA256 for r in raw))
    problems={};plans={};overheads={}
    for row in data['rows']:
        sid=row['scenario_id'];name=row['run_id']
        if sid in ['S1','S2','S3']:
            check(name+'_not_run',row['status']=='INPUT_HOLD' and all(row[k] is None for k in ['D_km','W_min','T_program_s','T_human_min_s','T_human_max_s']))
            continue
        if sid not in problems:problems[sid]=load_problem(HERE/'results/inputs'/sid)
        p=problems[sid];plan=load_plan(HERE/'results/runs'/(name+'.plan.json'));plans[name]=plan
        common=validate_plan(p,plan);other=recompute(p,plan)
        check(name+'_feasible',common.feasible and other['feasible'] and row['status']=='FEASIBLE')
        for key in ['D_km','W_min']:
            check(name+'_'+key,abs(float(other[key])-row[key])<1e-8 and abs(getattr(common,key)-row[key])<1e-8)
        runtime=json.loads((HERE/'results/runs'/(name+'.runtime.json')).read_text());ev={e['name']:e['elapsed_s'] for e in runtime['timing_events']}
        check(name+'_timing_boundary',runtime['timing_events'][0]['name']=='input_load_start' and runtime['timing_events'][-1]['name']=='independent_validation_end' and runtime['T_program_s']==row['T_program_s']==ev['independent_validation_end'])
        check(name+'_program_not_human',runtime['T_semantics'].startswith('program wall') and 'T_s' not in runtime)
        overheads[name]=ev['input_load_end']+ev['independent_validation_end']-ev['independent_validation_start']
        check(name+'_A_model_metadata',plan.method_id=='A' and not plan.method_settings['Sagawa_actual'] and not plan.method_settings['automatic_repair'])
    for aggregate in data['ranges']:
        subset=[r for r in raw if r['scenario_id']==aggregate['scenario_id'] and (aggregate['condition']=='ALL' or r['condition']==aggregate['condition'])]
        good=[r for r in subset if r['status']=='FEASIBLE'];attempted=[r for r in subset if r['status'] not in ['INPUT_HOLD','NOT_RUN']]
        key=aggregate['scenario_id']+'_'+aggregate['condition']
        check(key+'_rate',aggregate['attempted_plans']==len(attempted) and aggregate['feasible_rate']==(len(good)/len(attempted) if attempted else None))
        for metric in ['D_km','W_min','T_program_s']:
            vals=[Decimal(r[metric]) for r in good]
            for tag,fn in [('min',min),('max',max),('median',statistics.median)]:
                expected=fn(vals) if vals else None;observed=aggregate[metric+'_'+tag]
                check(key+'_'+metric+'_'+tag,(expected is None and observed is None) or (expected is not None and abs(expected-Decimal(str(observed)))<Decimal('0.00000001')))

    human=csv_rows(HERE/'results/HUMAN_TIME_BY_PLAN.csv')
    structural=csv_rows(HERE/'results/HUMAN_TIME_STRUCTURAL_SENSITIVITY.csv')
    check('human_rows_324',len(human)==324);check('structural_rows_27',len(structural)==27)
    for index,row in enumerate(human+structural):
        q=cfg['human_time']['profiles'][row['profile']];assignments=json.loads(row['assignments']);workers=int(row['workers'])
        loads=[0]*workers
        for job in assignments:loads[job['worker_index']]+=job['job_s']
        serial=q['setup_s']+q['assignment_s_per_stop']*int(row['N'])+q['coordination_s_per_used_vehicle']*int(row['used_vehicles'])
        check(f'human_{index}_person_vs_elapsed',serial+sum(j['job_s'] for j in assignments)==int(row['person_seconds']) and serial+max(loads)==int(row['workflow_elapsed_s']))
        if row.get('run_id'):
            plan=plans[row['run_id']];counts=Counter()
            for t in plan.trips:counts[t.vehicle_id]+=len(t.visits)
            by_index={i:counts[v.vehicle_id] for i,v in enumerate(problems[row['scenario_id']].vehicles)}
            for job in assignments:
                expected=q['vehicle_setup_s']+sum(q[k] for k in ['lookup_s_per_stop','ordering_s_per_stop','review_s_per_stop'])*by_index[job['vehicle_index']]
                check(f'human_{index}_vehicle_{job["vehicle_index"]}',expected==job['job_s'])
            check(f'human_{index}_measured_overhead',abs(float(row['measured_io_validation_s'])-overheads[row['run_id']])<1e-8)
            check(f'human_{index}_not_rule_program_time',abs(float(row['T_human_estimate_s'])-(int(row['workflow_elapsed_s'])+overheads[row['run_id']]))<1e-8)
        else:
            check(f'human_{index}_structural_not_full_T',row['T_human_estimate_s']==row['measured_io_validation_s']=='' and row['scope']=='structural_sensitivity_only_NOT_experiment')
    adopted=csv_rows(HERE/'ADOPTION_RANGES.csv')
    check('nine_unadopted_research_metrics',len(adopted)==9 and all(r['status']=='HOLD' and r['adopted_min']==r['adopted_max']==r['adopted_median']=='' for r in adopted))
    check('52_new_plus_136_existing_tests','188 passed' in (HERE/'TEST_REGRESSION.txt').read_text())
    rejects=json.loads((HERE/'REJECTION_WITNESSES.json').read_text())
    check('failure_records_not_corrected',all(not r['feasible'] and r['D_km'] is None and r['W_min'] is None for r in rejects.values()))
    distinct=json.loads((HERE/'EFFECTIVE_DISTINCT_PLANS.json').read_text())
    check('duplicate_conditions_reported',all(v['registered_conditions']==9 and v['distinct_plans']==3 for v in distinct.values()))

    before=json.loads((HERE/'PRESERVATION_BEFORE.json').read_text())
    entries=['A_BASELINE_DECISION.md','A_PUBLIC_ONLY_PLAN.md','A_SAGAWA_FINAL_DECISION.md']
    intended={'src/kmd_toc/common/validation.py',*('docs/research/toc_delivery_a/'+s for s in entries)}
    changed=[];missing=[]
    for path,h in before['files'].items():
        p=ROOT/path
        if not p.exists():missing.append(path)
        elif sha(p)!=h:changed.append(path)
    check('only_four_intended_existing_files_changed',set(changed)==intended and not missing)
    for name in entries:
        check(name+'_old_body_intact',(DOCS/name).read_bytes().endswith((HERE/'SOURCE_BEFORE'/name).read_bytes()))
    frozen={p:h for p,h in before['files'].items() if p.startswith('03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/')}
    check('eight_frozen_files_unchanged',len(frozen)==8 and all(sha(ROOT/p)==h for p,h in frozen.items()))
    current=(ROOT/'src/kmd_toc/common/validation.py').read_text();old=(HERE/'SOURCE_BEFORE/common_validation.py').read_text()
    check('one_method_registry_extension_only',current.replace("plan.method_id not in ('A','B','C','D')","plan.method_id not in ('B','C','D')")==old)
    check('no_commit',subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['head'])
    docs=['A_RULE_BASELINE_SPEC.md','A_RULE_IMPLEMENTATION_PLAN.md','A_RULE_VALIDATION_REPORT.md','A_RULE_COMPARABILITY.md','A_RULE_FINAL_DECISION.md']
    for name in docs:
        text=(DOCS/name).read_text();check(name+'_no_trailing_whitespace',all(line==line.rstrip() for line in text.splitlines()))
    check('study_resources_measured','Maximum resident set size (kbytes): 43008' in (HERE/'RUN_RESOURCES.txt').read_text())
    preservation={'checked_files':len(before['files']),'unchanged_files':len(before['files'])-len(changed),'intended_changed_files':changed,'unexpected_changes':[],'missing_files':missing,'frozen_unchanged':8,'head_unchanged':True,'excluded_dirs':before['excluded_dirs']}
    (HERE/'PRESERVATION_RESULT.json').write_text(json.dumps(preservation,ensure_ascii=False,indent=2)+'\n')
    result={'passed':len(checks),'failed':0,'elapsed_wall_s':time.perf_counter()-start,'checks':checks,'scope':'software, artificial outcomes, model arithmetic, metadata and preservation; NOT human validation or S1-S3 performance'}
    (HERE/'INDEPENDENT_AUDIT_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    patch=[]
    pairs=[(HERE/'SOURCE_BEFORE/common_validation.py',ROOT/'src/kmd_toc/common/validation.py')]+[(HERE/'SOURCE_BEFORE'/s,DOCS/s) for s in entries]
    for oldp,newp in pairs:patch.extend(difflib.unified_diff(oldp.read_text().splitlines(keepends=True),newp.read_text().splitlines(keepends=True),fromfile=str(oldp),tofile=str(newp)))
    (HERE/'EXISTING_FILE_CHANGES.patch').write_text(''.join(patch))
    (HERE/'GIT_STATUS_AFTER.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True))
    print(f'{len(checks)} independent audit checks passed; {len(before["files"])} old files checked; 8 frozen files unchanged')


if __name__=='__main__':main()
