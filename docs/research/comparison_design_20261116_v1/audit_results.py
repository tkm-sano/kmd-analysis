#!/usr/bin/env python3
"""Read-only audit of frozen pilots; write a separate audit artifact."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import argparse
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.comparison_v1.contract import read,dump,digest,check_freeze,run_identity,check_profile
from kmd_toc.comparison_v1.evaluation import validate_result
from kmd_toc.comparison_v1.design import require_same_settings


def main(output=None):
    root=ROOT/'output/toc_delivery/comparison_design_20261116_v1'
    doc=Path(__file__).resolve().parent
    checks=[]
    def check(name,value,detail=None):
        checks.append({'check':name,'pass':bool(value),'detail':detail})
    baseline=read(doc/'BASELINE_HASHES.json')
    for p in ('README.md','.gitignore','AGENTS.md'):
        check('preserve:'+p,digest(ROOT/p)==baseline[p])
    for p,h in baseline.items():
        if p.startswith('docs/research/comparison_integration_v1_20261115/'):
            check('preserve_prior_report:'+p,digest(ROOT/p)==h)
    check('frozen_A_files',bool(check_freeze()))
    all_rows=[];all_seeds={};manifests={};phase_stats=[];artifact_count=0
    for stage,expected_count in [('selection_lean',15),('selection_retained',15),('variance',45),('confirmation',15)]:
        base=root/stage;m=read(base/'REGISTERED.json');manifests[stage]=m
        check(stage+':registered_count',len(m['runs'])==expected_count)
        check(stage+':physical_cores',len(set(check_profile(m['cpu_profile']['cpu_ids'])))==4)
        with ThreadPoolExecutor(max_workers=8) as pool:
            source_checks=list(pool.map(lambda item:(item[0],digest(ROOT/item[0])==item[1]),m['source_hashes'].items()))
        current_diffs=[name for name,good in source_checks if not good]
        allowed=['scripts/run_comparison_design.py'] if stage=='selection_lean' else []
        check(stage+':source_version',current_diffs==allowed,current_diffs)
        snapshot_good=True
        with tarfile.open(base/'SOURCE_SNAPSHOT.tar.gz','r:gz') as archive:
            for name,h in m['source_hashes'].items():
                stream=archive.extractfile(name)
                snapshot_good=snapshot_good and stream is not None and hashlib.sha256(stream.read()).hexdigest()==h
        check(stage+':snapshot_source_hashes',snapshot_good)
        input_good=True
        for case in m['cases']:
            for name,h in case['input']['files'].items():
                input_good=input_good and digest(Path(case['input']['directory'])/name)==h
        check(stage+':input_OD_preserved',input_good)
        rows=[];output_hash_good=True;validations=True;cleanup=True;branches=True;seed_unique=True
        for run in m['runs']:
            directory=base/'runs'/run['run_id']
            row=validate_result(read(directory/'result.json'),run_identity(m,run))
            rows.append(row)
            if row['adoptable']:
                validations=validations and row['validation_completed_at_s']<=row['budget_wall_s']
                validations=validations and digest(directory/'plan.json')==row['plan_sha256']
                v=read(directory/'validation.json')
                validations=validations and v['common_physical']['feasible'] and v['independent_physical']['feasible']
            else:
                validations=validations and all(row[k] is None for k in ('D','W','W_first','W_reload','T_program'))
            info=row.get('process_control')
            cleanup=cleanup and bool(info and info['cleanup']['session_empty'])
            if row['method']!='A':
                bs=(row.get('native_resources') or {}).get('parallel_branches') or []
                branches=branches and len(bs)==4 and all(b.get('children_joined') for b in bs)
            for stream in ('solver_seed','quantum_seed'):
                seed=run.get(stream)
                if seed is not None:
                    key=(run['method'],stream,seed)
                    if key in all_seeds:seed_unique=False
                    all_seeds[key]=stage+':'+run['run_id']
            inventory=read(directory/'OUTPUT_HASHES.json')
            with ThreadPoolExecutor(max_workers=8) as pool:
                matched=list(pool.map(lambda item:digest(directory/item[0])==item[1],inventory.items()))
            artifact_count+=len(inventory)
            output_hash_good=output_hash_good and all(matched)
            print(stage,run['run_id'],'audited',len(inventory),'files',flush=True)
        check(stage+':result_identity_and_deadline',validations)
        check(stage+':children_reaped',cleanup)
        check(stage+':four_branches_visible_and_joined',branches)
        check(stage+':fresh_method_stream_seeds',seed_unique)
        check(stage+':all_output_hashes',output_hash_good)
        phase_stats.append({'stage':stage,'attempts':len(rows),'adopted':sum(r['adoptable'] for r in rows),
            'T_attempt_sum_s':sum(r['T_attempt'] for r in rows)})
        all_rows.extend(rows)
    check('frozen_variance_and_confirmation_code_settings',bool(require_same_settings([
        manifests['selection_retained'],manifests['variance'],manifests['confirmation']])))
    check('all_90_attempts_preserved',len(all_rows)==90 and len({r['run_id'] for r in all_rows})==90)
    check('planned_pilot_cap',sum(r['budget_wall_s'] for r in all_rows)==19800)
    check('failures_not_zero_imputed',all(all(r[k] is None for k in ('D','W','T_program')) for r in all_rows if not r['adoptable']))
    status=read(root/'design/STATUS.json');pending=read(root/'design/MAIN_MANIFEST.json')
    check('main_not_started_or_falsely_executable',not status['main_started'] and not status['main_start_allowed'] and not pending['executable'])
    check('fixed_demand_scope',status['M_per_scale']==1 and status['independent_demand_families']==1)
    check('main_fixed_count_stop_rule','fixed' in pending['main_stop_rule'])
    audit={'pass':all(c['pass'] for c in checks),'checks':checks,'phases':phase_stats,
        'executed_attempts':len(all_rows),'adopted':sum(r['adoptable'] for r in all_rows),
        'failure_count':sum(not r['adoptable'] for r in all_rows),
        'audited_output_files':artifact_count,'T_attempt_total_s':sum(r['T_attempt'] for r in all_rows),
        'source_audit_script_sha256':digest(__file__),'main_started':False,
        'notes':['lean used prefreeze orchestration revision; only driver changed, recorded in amendment',
                 'quality/status inference remains separate from target attainment',
                 'no statistical pairing inferred from repeat/seed labels']}
    if output is None:
        dump(doc/'FINAL_AUDIT.json',audit)
        dump(root/'DESIGN_FINAL_AUDIT.json',audit)
    else:
        output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
        dump(output,audit)
    print(json.dumps({k:audit[k] for k in ('pass','executed_attempts','adopted','failure_count','audited_output_files')},ensure_ascii=False))
    if not audit['pass']:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',help='New audit JSON path; preserve previous audit artifacts')
    main(parser.parse_args().output)
