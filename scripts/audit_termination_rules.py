#!/usr/bin/env python3
"""Audit every registered attempt and branch; never fabricate missing outcomes."""
import argparse
from collections import Counter
import csv
import json
import hashlib
import tarfile
from pathlib import Path
from kmd_toc.comparison_v1.contract import ROOT,read,digest,atomic
from kmd_toc.termination_v1.runner import aggregate


def audit(root):
    root=Path(root).resolve();manifest=read(root/'REGISTERED.json');rows=aggregate(root);checks=[];telemetry=[]
    def check(name,condition,detail=None):checks.append({'check':name,'pass':bool(condition),'detail':detail})
    check('all_registered_attempts_recorded',len(rows)==len(manifest['runs']))
    check('all_registered_attempts_finished',all(r['execution_state'] not in ('NOT_STARTED','USER_CANCELLED','EXTERNAL_INTERRUPTION') for r in rows))
    for r in rows:
        check(r['run_id']+':all_branch_states_recovered',len(r['branches'])==len(next(x for x in manifest['runs'] if x['run_id']==r['run_id'])['branches']))
        if r.get('adoptable'):
            check(r['run_id']+':physical_adoption',r['plan_state']=='VALID' and r['validation_state']=='VALIDATED' and all(r.get(k) is not None for k in ('D','W','T_program')))
            check(r['run_id']+':plan_bytes',digest(root/'runs'/r['run_id']/'plan.json')==r['plan_sha256'])
        else:check(r['run_id']+':failed_values_preserved',all(r.get(k) is None for k in ('D','W','T_program')))
        for b in r['branches']:
            path=root/'runs'/r['run_id']/f"branch_{b['branch_id']:02d}"/'stages'/'work.jsonl'
            events=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
            starts=[e for e in events if e['event']=='training_evaluation_start'];ends=[e for e in events if e['event']=='training_evaluation_end']
            failures=[e for e in events if e['event']=='training_evaluation_failed']
            final_start=[e for e in events if e['event']=='final_sample_start'];final=[e for e in events if e['event']=='final_sample_end']
            qcalls=[e for e in events if e['event']=='quantum_call_start']
            per_call=Counter((e['call_id'],e['restart']) for e in starts)
            record={'run_id':r['run_id'],'method':r['method'],'scale':r['scale'],'branch_id':b['branch_id'],
                'execution_state':b['execution_state'],'algorithm_termination':b.get('algorithm_termination'),'plan_state':b['plan_state'],
                'counts':b.get('counts'),'quantum_call_attempts':len(qcalls),'training_attempts':len(starts),
                'training_successes':len(ends),'training_failures':len(failures),
                'observed_training_shots':sum(e['actual_shots'] for e in ends),'final_sampling_started':len(final_start),
                'final_sampling_completed':len(final),'observed_final_shots':sum(e['actual_shots'] for e in final),
                'incomplete_training_evaluations':len(starts)-len(ends)-len(failures),
                'shots_accounting_complete':len(starts)==len(ends) and len(final_start)==len(final),
                'max_attempted_evaluations_per_call_start':max(per_call.values(),default=0),
                'stage_terminations':[e for e in events if e['event'] in ('A_complete','Routing_end','CP_end','LP_end','IP_end','catalogue_complete')],
                'quantum_qubits':sorted({e['qubits'] for e in events if e['event']=='quantum_problem'})}
            telemetry.append(record)
            if b.get('execution_state')=='NORMAL':
                check(r['run_id']+f":branch{b['branch_id']}:native_threads",b.get('observed_threads')==1)
                check(r['run_id']+f":branch{b['branch_id']}:affinity",len(b.get('cpu_affinity',[]))==1)
                check(r['run_id']+f":branch{b['branch_id']}:shots",all(e['actual_shots']==10000 for e in ends+final))
                check(r['run_id']+f":branch{b['branch_id']}:evaluation_bound",max(per_call.values(),default=0)<=80)
                if r['method']=='D':
                    cw=next(e for e in events if e['event']=='CW_complete')['routes']
                    check(r['run_id']+f":branch{b['branch_id']}:all_pricing_calls",len(qcalls)==2*cw)
                    check(r['run_id']+f":branch{b['branch_id']}:complete_shot_accounting",record['shots_accounting_complete'])
                    counts=b['counts'];check(r['run_id']+f":branch{b['branch_id']}:counter_reconciliation",
                        counts.get('quantum_training_shots',0)==record['observed_training_shots'] and counts.get('quantum_final_shots',0)==record['observed_final_shots'])
    with tarfile.open(root/'SOURCE_SNAPSHOT.tar.gz') as snapshot:
        for name,h in manifest['source_hashes'].items():
            check('registered_snapshot_source:'+name,hashlib.sha256(snapshot.extractfile(name).read()).hexdigest()==h)
    current_source_matches=all(digest(ROOT/name)==h for name,h in manifest['source_hashes'].items())
    for case in manifest['cases']:
        for name,h in case['input']['files'].items():check('frozen_input:'+case['case_id']+':'+name,digest(Path(case['input']['directory'])/name)==h)
    report={'current_source_matches':current_source_matches,'pass':all(c['pass'] for c in checks),'registered_trials':len(rows),'executed_trials':sum(r['execution_state']!='NOT_STARTED' for r in rows),
        'adoptable':sum(r.get('adoptable',False) for r in rows),'execution_states':dict(Counter(r['execution_state'] for r in rows)),
        'functional_checks_complete':all(r['execution_state'] not in ('NOT_STARTED','USER_CANCELLED','EXTERNAL_INTERRUPTION') for r in rows),
        'main_start_allowed':False,'main_reason':'new-setting variance/R/precision/analysis registration remain outside this task',
        'checks':checks}
    atomic(root/'TELEMETRY.json',telemetry);atomic(root/'FINAL_AUDIT.json',report)
    fields=['scale','method','execution_state','algorithm_termination','plan_state','adoptable','D','W','T_program','T_attempt','J','J_reason','CPU_s_branches','sampled_tree_peak_RSS_KiB','final_candidate_source']
    with (root/'RESULTS.csv').open('w') as f:
        writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in report.items() if k!='checks'}),flush=True)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root');audit(parser.parse_args().root)
