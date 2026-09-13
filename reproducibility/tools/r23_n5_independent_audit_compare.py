"""Post-seal comparison only. Never changes independent findings or acceptance."""
from __future__ import annotations
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_code_audit'
OUT=PARENT/'20260913_v2_independent'
PREV=PARENT/'20260913_v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def verify_seal():
    seal=load(OUT/'independent_seal.json')
    assert all(sha(OUT/name)==expected for name,expected in seal['files'].items())
    return seal
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()

def main():
    seal=verify_seal()
    assert seal['classification']=='CODE_AUDIT_FAIL'
    previous={p.name:load(p) for p in PREV.glob('*.json')}
    gate=load(OUT/'acceptance_gate.json'); findings=load(OUT/'finding_register.json')
    prior_f=previous['finding_register.json']['findings']; prior_g=previous['acceptance_gate.json']
    prior_d=previous['researcher_degrees_of_freedom.json']
    observed_counts=dict(Counter(r['arbitrariness_risk'] for r in prior_d['decisions']))
    prior_sev=dict(Counter(r['severity'] for r in prior_f))
    for key in ('CRITICAL','MAJOR','MODERATE','MINOR'):prior_sev.setdefault(key,0)
    correspondence=[
        {'previous':'AUD-M-001','current':['I05'],'finding_agreement':'substantially same','severity_agreement':True,'note':'Both reject formal runtime/memory multiplier; current adds actual timer exclusions and sub-raw-state RSS anomaly.'},
        {'previous':'AUD-M-002','current':['I01','I07'],'finding_agreement':'same topic, materially different failure conclusion','severity_agreement':False,
         'note':'Previous MODERATE assumes malformed paths fail closed. Independent probes demonstrate accepted zero/scaled norm and output inf/nan; I01 MAJOR. Current explicit dimension/finiteness guards are newer than previous source.'},
        {'previous':'AUD-M-003','current':[],'current_decision':'optimizer MEDIUM in optimizer_selection_audit.json and degrees-of-freedom',
         'finding_agreement':'rationale risk retained as a decision, not a standalone finding','severity_agreement':'no one-to-one severity','note':'Same MEDIUM optimizer risk; current does not infer B2-independent preference from pre-n5 timestamp alone.'},
    ]
    names={'instance':'instance selection','n':'n','p':'p','lambda':'lambda','optimizer':'optimizer','initialization':'initialization','cap':'cap','seed':'seed',
           'tolerance':'tolerance','denominator':'denominator','benchmark metric':'runtime measurement','memory metric':'memory measurement',
           'optimization approach':'optimization candidate','validation cases':'validation cases','continuation rule':'continuation rule'}
    risk_map={r['decision']:r['arbitrariness_risk'] for r in prior_d['decisions']}
    risks=[{'decision':r['Decision'],'previous_decision':names[r['Decision']],'previous':risk_map[names[r['Decision']]],'current':r['Risk'],
            'agreement':risk_map[names[r['Decision']]]==r['Risk']} for r in load(OUT/'researcher_degrees_of_freedom.json')['decisions']]
    # Distinguish source drift from previously existing errors using historical helper probes.
    sys.path.insert(0,str(ROOT/'05_src'))
    import numpy as np
    old_source=git('show','ff1d579:05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py')+'\n'
    old=types.ModuleType('audit_prior_helper');exec(compile(old_source,'historical_helper','exec'),old.__dict__)
    historical_probes=[]
    data=np.zeros(16,dtype=np.complex128);data[9]=2.
    for name,state,opt in [('norm_four',data,((1,0,0,1),)),('zero_norm',np.zeros_like(data),((1,0,0,1),)),('empty_optimum',data/2,())]:
        try:
            r=old.indexed_probability_metrics(state,('A','B'),opt,2)
            historical_probes.append({'case':name,'result':'ACCEPTED','total':r['probability_total'],'P_opt':r['P_opt']})
        except Exception as exc:historical_probes.append({'case':name,'result':'REJECTED','exception':type(exc).__name__})
    comparison={'comparison_recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'previous_first_content_read':'after independent seal; first explicit read was previous acceptance/finding/DOF files',
        'independent_seal_sha256':sha(OUT/'independent_seal.json'),'independent_files_unchanged':True,
        'previous_classification':prior_g['status'],'independent_classification':gate['classification'],'classification_agreement':False,
        'previous_finding_count':len(prior_f),'independent_finding_count':findings['count'],
        'previous_severity_counts':prior_sev,'independent_severity_counts':findings['severity_counts'],
        'previous_HIGH':prior_g['high_arbitrariness'],'independent_HIGH':gate['arbitrariness_counts']['HIGH'],
        'previous_CRITICAL_MAJOR':prior_sev['CRITICAL']+prior_sev['MAJOR'],'independent_CRITICAL_MAJOR':findings['severity_counts']['CRITICAL']+findings['severity_counts']['MAJOR'],
        'correspondence':correspondence,'new_independent_findings':['I02','I03','I04','I06','I08','I09','I10'],
        'prior_only_register_finding':'AUD-M-003 is represented in the current optimizer risk decision; not silently discarded',
        'arbitrariness_comparison':risks,'unmapped_previous_decision':'metric (generic; prior has 16 decisions, current has 15)',
        'previous_declared_risk_counts':prior_d['counts'],'previous_recomputed_risk_counts':observed_counts,
        'previous_count_inconsistency':'Previous declares LOW11/MEDIUM5 but its 16 rows count LOW9/MEDIUM7. This comparison-only observation is not added to sealed independent findings.',
        'current_risk_counts':gate['arbitrariness_counts'],
        'agreements':['normalized mathematical equivalence','canonical Hamiltonian/QUBO unchanged','bit ordering','no production exact-optimum leakage','raw denominator','no observed result hardcoding','no formal runtime multiplier','optimizer rationale MEDIUM'],
        'disagreements':['failure safety/severity','validation acceptance sensitivity','execution source authority completeness','historical immutability certainty','current convergence claim','cap pre-run authority/HIGH risk'],
        'source_drift':{'previous_helper_sha256':hashlib.sha256(old_source.encode()).hexdigest(),
            'current_helper_sha256':sha(ROOT/'05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py'),
            'change':'d4a8d78 adds explicit guards and label sort, 66 insertions/5 deletions; model and qaoa source unchanged since previous audit',
            'historical_failure_probes':historical_probes,
            'conclusion':'Added guards explain improvements in NaN/dimension rejection, but norm acceptance, missing entrypoint commits, unconditional report PASS and convergence 3/3 already existed. Source drift alone does not explain audit disagreement.'},
        'result':'CODE_AUDIT_RESULT_NOT_REPRODUCED',
        'causes':['Previous treats current snapshot hash as execution-time authority without reconstructing wrapper/wiring.',
                  'Previous accepts generated PASS summaries without checking whether assertions drive them or actual helper is exercised.',
                  'Previous assumes malformed input fails closed; independent counterexamples refute it even on the historical helper.',
                  'Previous retained-facts check does not detect contradictory current convergence claim.',
                  'Current differentiates absence of observed tuning from evidence that run options were fixed before results.'],
        'no_reclassification_after_comparison':True,
        'LLM_identity_limit':'Previous artifact does not certify auditor model identity; this is independent source/model-condition reassessment, not verified same-LLM experiment.'}
    write('previous_audit_comparison.json',comparison)
    write('previous_audit_read_log.json',{'phase':'post-independent-seal only','seal_timestamp':seal['sealed_at_utc'],
        'previous_files':{p.name:sha(p) for p in sorted(PREV.iterdir()) if p.is_file()},'prior_artifacts_changed':False})
    # Supplementary coverage records do not alter sealed scope or scientific classifications.
    write('post_seal_scope_verification.json',{'status_documents':[{ 'path':p,'sha256':sha(ROOT/p),'content_review_phase':'scientific claim lines before seal; full content after seal'} for p in ['05_src/traffic_simulation/R23_STATUS.md','05_src/traffic_simulation/R23_NEXT_STEPS.md','05_src/traffic_simulation/R23_ROADMAP.md','RESEARCH_STATUS.md']],
        'scope_file_count':len(load(OUT/'audit_scope.json')['files']),'comparison_script_sha256':sha(Path(__file__)),
        'independent_scope_not_rewritten':True})
    current_files=load(OUT/'audit_scope.json')['files']
    drift=[r['path'] for r in current_files if sha(ROOT/r['path'])!=r['sha256']]
    assert not drift,drift
    assert git('diff','--name-only','d4a8d78','--','05_src')==''
    verify_seal()
    write('verification.json',{'independent_seal':'PASS','source_and_scoped_artifact_hashes':'PASS','scoped_file_count':len(current_files),
        'scientific_source_diff':'EMPTY','previous_artifacts':'read only','scientific_runs_started_by_audit':0,
        'audit_tests':'direct assertions passed; expected failure-contract counterexamples recorded','pytest':'not installed in frozen environment; no installation or environment change performed',
        'unrelated_untracked_files':'left unchanged','SHA256SUMS':'generated after report generation; verify externally with sha256sum -c'})
    covered=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
    covered.extend(ROOT/'reproducibility/tools'/name for name in [
        'r23_n5_independent_audit.py','r23_n5_independent_audit_report.py',
        'r23_n5_independent_audit_contracts.py','r23_n5_independent_audit_compare.py'])
    (OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {os.path.relpath(p,OUT)}\n' for p in covered))
    print(json.dumps({'result':comparison['result'],'previous':prior_g['status'],'current':gate['classification'],'scoped_files':len(current_files),'seal_unchanged':True}))

if __name__=='__main__':main()
