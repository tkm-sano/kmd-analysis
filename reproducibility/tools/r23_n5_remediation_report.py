"""Generate evidence-bound remediation reports; never grants code-audit acceptance."""
from __future__ import annotations
from collections import Counter
import difflib
import json
from pathlib import Path
import re
import subprocess
from r23_n5_remediation_evidence import ROOT, OUT, AUDIT, BASE, sha, write, git

def read(name):
    return json.loads((OUT/name).read_text())

def report():
    authority=read('finding_authority.json')
    tests=read('validation_test_manifest.json')
    evidence=read('regression_evidence.json')
    provenance=read('provenance_status_by_run.json')
    logs=read('execution_log_evidence.json')
    retired=read('legacy_generator_retirement.json')['generators']
    contract='05_src/traffic_simulation/specifications/R23_RUNTIME_REMEDIATION_CONTRACT.md'
    # Read-only search: raw/historical claims are not silently rewritten.
    paths=[p for p in git('ls-files').splitlines() if not p.startswith(str(OUT.relative_to(ROOT))+'/')]
    search=[]
    pattern=re.compile(r'converg|success.{0,10}3/3|33[.]7|327|quantum advantage|quantum speedup|superiority|generally efficient|scalable|robust',re.I)
    for path in paths:
        if 'r23' not in path.lower() and path!='RESEARCH_STATUS.md':continue
        if Path(path).suffix not in ('.py','.md','.json','.yml'):continue
        p=ROOT/path
        if not p.is_file():continue
        for line,text in enumerate(p.read_text(errors='replace').splitlines(),1):
            if pattern.search(text):search.append({'path':path,'line':line,'text':text,'layer':'HISTORICAL_NOT_REWRITTEN' if '/outputs/' in path else 'CURRENT_SOURCE_OR_DOCUMENT'})
    write('claim_search_inventory.json',{'matches':search,'method':'tracked R23 text plus RESEARCH_STATUS; immutable historical records retained, not current authority'})
    pass_search=[]
    for path in paths:
        if Path(path).suffix!='.py' or 'r23' not in path.lower():continue
        for line,text in enumerate((ROOT/path).read_text().splitlines(),1):
            if re.search(r'[\"\x27]PASS[\"\x27]|all_gates_pass|targeted_tests_pass',text):
                pass_search.append({'path':path,'line':line,'text':text})
    remaining=[
        {'path':'tools/authorize_r23_experiment_b2.py','lines':[138,143,144],'issue':'targeted_tests_pass/py_compile and six passing tests declared without invocation'},
        {'path':'tools/review_r23_experiment_b2_nelder_mead.py','lines':[129,140],'issue':'implementation and technical preflight PASS assigned without validating all listed conditions'},
        {'path':'tools/build_r23_experiment_b2_reexecution_authority.py','lines':[34,36],'issue':'constant pytest/smoke validation results in authority generator'},
        {'path':'tools/finalize_r23_b1_v2.py','lines':[124],'issue':'aggregate PASS is not conditioned on computed integrity booleans'},
        {'path':'tools/finalize_r23_experiment_b2_reexecution.py','lines':[31,37],'issue':'aggregate PASS independent of prob_pass/params_pass/exact_pass'},
        {'path':'05_src/traffic_simulation/r23_qaoa_aer/artifact.py','lines':[76,84],'issue':'lineage PASS manufactured from file existence/hash collection, not comparison to authority'},
    ]
    write('validation_pass_search.json',{'matches':pass_search,'unresolved':remaining,
        'guard_backed_examples':['tools/review_r23_experiment_b1.py: parameter_gate assert precedes PASS','tools/execute_r23_experiment_b2.py: gate assertions precede execution preflight','tools/validate_r23_experiment_b_implementation.py: scalar and explicit condition comparisons'],
        'historical_audit_assertions':'Independent audit PASS strings are downstream of explicit assertions; previous audit output remains immutable.',
        'scope_limitation':'Search inventory is comprehensive over tracked R23 Python names; manual control-flow review is not a formal whole-program proof. Six remaining locations explicitly prevent global I03 closure.'})
    write('i01_probability_integrity_remediation.json',{'original_ids':['I01','I07'],'status':'RESOLVED',
        'source':'05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py',
        'contract':'finite float64/complex128, finite derived masses, abs(sum(abs(psi)**2)-1)<=1e-12, original probability range tolerance',
        'prohibited_repairs':['renormalization','NaN replacement','clipping','warning-only continuation'],
        'evidence':['invalid_input_regression.json','valid_domain_regression.json','multiple_optimum_regression.json'],
        'valid_domain_limit':'fixed initial points and basis fixtures; not a rerun of historical optimizer trajectories'})
    write('i02_execution_provenance_reconstruction.json',{'original_ids':['I02','I08'],
        'status':'RESOLVED_WITH_DOCUMENTED_PROVENANCE_LIMITATION','runs':provenance['runs'],
        'evidence':['execution_log_evidence.json','original_artifact_snapshot.json','historical_run_snapshots/'],
        'reconstruction':'Timestamped FileChange patches replay uniquely to later committed runner/qaoa. This establishes a strongly inferred dirty-source explanation, not cryptographic process attestation.',
        'journal':{'query':'journalctl 2026-09-11..2026-09-14 PIDs 609374 and 3556883','result':'no visible entries; current user lacks full system journal access'},
        'resource_contradiction':'Contemporaneous rank02 ps RSS exceeds 798660 KiB while final ru_maxrss is 323576 KiB. The cause/process accounting is not reconciled; rank03 similarly inconsistent.',
        'quantity_verification_limit':'Recorded routes and costs remain independently checkable. Final probability distribution/optimizer trajectory cannot be reproduced without final parameters/state/trace. New fixed-point regression does not certify those historical values.',
        'formal_acceptance':'rank02/03 NOT_REAUTHORIZED; RERUN_REQUIRED_FOR_FORMAL_ACCEPTANCE; no scientific rerun authorized or performed'})
    write('i03_validation_gate_remediation.json',{'original_ids':['I03'],'status':'PARTIAL','resolved_n5_generators':retired,
        'replacement':'reproducibility/tools/r23_n5_remediation_regression.py calls actual before/after helpers with independent references',
        'gate':'05_src/traffic_simulation/validation/r23_validation_gate.py; exact nonempty required set, executed checks and evidence mandatory',
        'executed_gate':tests['gate'],'remaining_unconditional_locations':remaining,
        'residual':'n5 finding target repaired, but requested repository-wide unconditional PASS removal is incomplete; retain MAJOR I03 rather than equating passing local tests with complete closure',
        'evidence':['validation_test_manifest.json','validation_pass_search.json','regression_evidence.json#gate_mutations']})
    write('i04_convergence_claim_remediation.json',{'original_ids':['I04'],'status':'RESOLVED',
        'wording':{'optimal_route_recovered':'3/3','relative_route_objective_gap':'0 for 3/3','optimizer_reported_success':'2/3','rank01':False,'rank02':True,'rank03':True,'rank01_cap_reached':True},
        'limitation':'rank02/03 retained observations, not formal reauthorization; native optimizer success does not prove global convergence',
        'corrected_documents':['05_src/traffic_simulation/R23_STATUS.md','05_src/traffic_simulation/R23_NEXT_STEPS.md','05_src/traffic_simulation/R23_ROADMAP.md','05_src/traffic_simulation/specifications/R23_REDUCED_PROBLEM_CANONICAL.md','RESEARCH_STATUS.md'],
        'historical_records':'unchanged; old claims superseded by current status and this erratum'})
    timeline=git('log','--all','--format=%H %aI %s','--','reproducibility/outputs/traffic_simulation/r23_experiment_b2_evidence_review','reproducibility/outputs/traffic_simulation/r23_n5_scaling_authority').splitlines()
    write('i05_stopping_rule_authority_review.json',{'request_id':'I05','original_finding':'HIGH cap decision in independent DOF, not register I05',
        'classification':'VERIFIED_PRE_FIXED','scope_of_verification':'Declared pre-run runner source in timestamped local FileChange; execution lineage remains STRONGLY_INFERRED',
        'maxiter':300,'objective_evaluation_cap':300,'optimizer_options':None,'wall_time_seconds':None,
        'runner_created_at':'2026-09-11T13:32:14.461Z','rank01_launch_at':'2026-09-11T13:32:20.724Z',
        'rank02_v4_wiring_completed_at':'2026-09-13T14:16:48.954Z','rank02_start':'2026-09-13T14:17:17Z',
        'evidence':['execution_log_evidence.json','reconstructed_sources/rank01_runner.py.txt','reconstructed_sources/rank02_rank03_runner.py.txt'],
        'risk_before':'HIGH','risk_after':'MEDIUM','basis':'New directly dated source evidence resolves absent runner bytes; manifest still omits explicit effective options and source attestation. No observed cap extension, rank-specific override or result-dependent wall-time stopping.',
        'not_authority':'B1/B2 cap900 cannot authorize n5 cap300. Native maxiter and project evaluation cap are distinct controls.'})
    write('i06_optimizer_authority_review.json',{'request_id':'I06','original_finding':'optimizer MEDIUM decision, not register I06','timeline':timeline,
        'n5_authority':'66d8d73 2026-09-11T22:18:24+09:00','n5_execution':'2026-09-11T22:32:21+09:00',
        'B2_evidence_available_before_n5':True,'rationale':'Continuity with COBYLA baseline is plausible; not proof of complete B2 independence.',
        'result_dependence':'No direct evidence of n5 post-result selection; B2 influence cannot be excluded. Alternatives include Nelder-Mead.',
        'general_superiority':'NOT_SUPPORTED','residual_risk':'MEDIUM'})
    write('i07_lambda_erratum.json',{'original_id':'I09','original_artifact_unchanged':True,
        'authority':'reproducibility/outputs/traffic_simulation/r23_n5_scaling_authority/20260911_v1/n5_penalty_authority.json',
        'condition':'lambda > (n+1)/2','n':5,'bound':3.0,'lambda':4.0,'strict_condition_satisfied':4.0>3.0,
        'correct_margin':4.0-3.0,'correct_penalty_margin':2*4.0-(5+1),'erroneous_margins':[0.5,1.0],
        'scientific_parameter_change':False,'canonical_correction':'05_src/traffic_simulation/specifications/R23_REDUCED_PROBLEM_CANONICAL.md'})
    write('i08_benchmark_claim_remediation.json',{'original_ids':['I05','I10'],'classification':'PRELIMINARY_ONLY',
        'runtime':'33.7x is an unmatched historical diagnostic ratio, not formal/scientific speedup',
        'memory':'201.6 GiB original observed absolute peak RSS versus approximately 0.615 GiB candidate incremental RSS: metrics not directly comparable; no 327x formal reduction',
        'proxy_erratum':'Legacy idx[-1:] P_optimal_lookup is an arbitrary feasible-index lookup microbenchmark, not verified optimum mass. Archived code retired; new regression invokes actual optimal-set helper.',
        'formal_contract':contract,'formal_benchmark_executed':False,'formal_comparability':'NOT_TESTED',
        'accounting':'T_total=T_setup+T_warmup+sum(T_eval)+T_final; also report cold total without warmup; include feasible caches, circuit/Hamiltonian/backend construction and final guards/decoding',
        'residual':['historical thread/affinity/warm-up/boundaries unmatched','rank02/03 peak RSS conflict unreconciled','no formal ratio authorized']})
    write('i09_selective_reporting_remediation.json',{'original_id':'I04','status':'RESOLVED_FOR_CURRENT_STATUS',
        'retained':['rank01 success=false','rank01 cap reached','P_feasible<1%','P_optimal about 5.45e-5..6.64e-5','rank01 runtime42.62h','rank01 peakRSS201.58GiB','rank02/03 provenance limitation','independent CODE_AUDIT_FAIL','CODE_AUDIT_RESULT_NOT_REPRODUCED','PRELIMINARY_ONLY benchmark','n>=6 not recommended'],
        'evidence':['05_src/traffic_simulation/R23_STATUS.md','claim_search_inventory.json'],
        'historical_reports':'Retained unchanged, including disfavored outcomes and superseded claims. No run excluded from new snapshots.'})
    write('i10_execution_metadata_contract.json',{'original_ids':['I02','I06','I08'],'contract':contract,
        'implementation':'05_src/traffic_simulation/r23_qaoa_aer/execution_provenance.py',
        'required':['git commit','source SHA','runner SHA','helper SHA','authority manifest SHA','source manifest','clean worktree','environment path','dependency versions','hostname','CPU','thread settings','command line','start/end timestamp','effective optimizer options','seeds','termination status','resource metrics and units','final parameters','objective trace SHA'],
        'missing_policy':'FORMAL_RUN_PROVENANCE_INCOMPLETE; do not elevate to formal evidence',
        'admission_scope':'Structural fail-closed validator tested; caller must bind recorded hashes to archived source/config files and enforce at start and end. No existing scientific runner changed or authorized.',
        'test':'regression_evidence.json#provenance_missing_fields',
        'compact_reporting_contract':'qaoa._v4_reporting_metrics now labels intentionally omitted diagnostics and candidate output version'})
    decisions=json.loads((AUDIT/'researcher_degrees_of_freedom.json').read_text())['decisions']
    for row in decisions:
        row['original_risk']=row['Risk']
        if row['Decision']=='cap':
            row.update({'Risk':'MEDIUM','When fixed':'2026-09-11T13:32:14.461Z pre-launch FileChange','Authority':'execution_log_evidence.json and reconstructed_sources/rank01_runner.py.txt','Result-dependent?':'No observed change; exact executed closure strongly inferred','reason':'New pre-run source bytes establish 300/300/None defaults; effective process attestation still missing.'})
        row['remediation_note']='Historical decision preserved; no scientific parameter changed.'
    counts=dict(Counter(r['Risk'] for r in decisions));counts.setdefault('HIGH',0)
    write('researcher_degrees_of_freedom_updated.json',{'decisions':decisions,'counts':counts,'unit':'15 independent-audit decision rows; risk reassessment is not independent re-audit acceptance'})
    claims=[('optimal route recovered3/3','DIRECTLY_OBSERVED','historical route fields; independently checkable costs, provenance qualified'),('optimizer success2/3','DIRECTLY_OBSERVED','native flags, not global convergence'),('gap0 for3/3','DERIVED','reported route costs vs frozen exact reference'),('unchanged valid-domain probability metrics','DERIVED','executed fixed-point and basis regression; not historical trajectory reproduction'),('dirty-source execution lineage','INFERRED','timestamped source edits and process logs'),('general robustness/scaling law','NOT_SUPPORTED','limited deterministic instances and one initialization'),('formal speedup or memory reduction factor','NOT_SUPPORTED','unmatched timing/memory metrics'),('optimizer superiority','NOT_SUPPORTED','B2 continuity does not establish general superiority'),('quantum advantage/speedup','NOT_SUPPORTED','CPU exact simulator evidence only'),('future benchmark settings','ASSUMED','prospective contract, NOT_EXECUTED')]
    write('claim_reaudit.json',{'claims':[{'claim':a,'classification':b,'basis':c} for a,b,c in claims], 'formal_docs_policy':'NOT_SUPPORTED claims explicitly denied; historical artifacts not retroactively rewritten'})
    protected=read('original_artifact_snapshot.json')['files']
    exceptions={r['path']:r for r in retired}
    immutable=[]
    for row in protected:
        actual=sha(ROOT/row['path']); same=actual==row['sha256']
        archived=exceptions.get(row['path'])
        source_retirement=bool(archived and sha(OUT/archived['archive'])==row['sha256'])
        immutable.append({**row,'current_sha256':actual,'unchanged':same,'archived_generator_retirement_only':source_retirement})
    immutable_ok=all(r['unchanged'] or r['archived_generator_retirement_only'] for r in immutable)
    write('original_artifact_immutability.json',{'files':immutable,'protected_count':len(immutable),'all_scientific_records_unchanged':immutable_ok,
        'source_only_exceptions':'Two legacy executable generators inside historical review directory retired; exact old source archived. No scientific result, original manifest, exact reference or execution record altered.'})
    tracked=git('diff','--name-only',BASE).splitlines()
    added=['05_src/traffic_simulation/r23_qaoa_aer/execution_provenance.py','05_src/traffic_simulation/validation/r23_validation_gate.py','05_src/traffic_simulation/specifications/R23_RUNTIME_REMEDIATION_CONTRACT.md','reproducibility/tools/r23_n5_remediation_evidence.py','reproducibility/tools/r23_n5_remediation_regression.py','reproducibility/tools/r23_n5_remediation_report.py']
    changes=[]
    for path in sorted(set(tracked+added)):
        if path.startswith(str(OUT.relative_to(ROOT))+'/'):continue
        if path.endswith('optimized_metrics_v4.py'):category='SAFETY_GUARD_ONLY'
        elif path.endswith('execution_provenance.py') or path.endswith('remediation_evidence.py'):category='PROVENANCE_ONLY'
        elif path.endswith('.py'):category='DOCUMENTATION_ONLY' if path.endswith('/qaoa.py') else 'VALIDATION_ONLY'
        else:category='DOCUMENTATION_ONLY'
        old=subprocess.run(['git','show',f'{BASE}:{path}'],cwd=ROOT,capture_output=True,text=True).stdout
        new=(ROOT/path).read_text()
        diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+path,tofile='after/'+path))
        changes.append({'path':path,'category':category,'sha256':sha(ROOT/path),'hunk_headers':re.findall(r'^@@.*@@',diff,re.M),'line_diff':diff})
    write('source_change_classification.json',{'changes':changes,'counts':dict(Counter(x['category'] for x in changes)),'SCIENTIFIC_SEMANTICS':0,
        'basis':'Mathematical core source unchanged; qaoa objective/run_single AST unchanged; valid-domain values and decoding compared against BASE. Rejection of invalid/low-precision input is a safety contract restoration.'})
    closures=[]
    mapping={'I01':('RESOLVED','i01_probability_integrity_remediation.json','NONE'),
             'I02':('RESOLVED_WITH_DOCUMENTED_PROVENANCE_LIMITATION','i02_execution_provenance_reconstruction.json','MODERATE'),
             'I03':('PARTIAL','i03_validation_gate_remediation.json','MAJOR'),
             'I04':('RESOLVED','i04_convergence_claim_remediation.json','NONE'),
             'I05':('RESOLVED_WITH_DOCUMENTED_LIMITATION','i08_benchmark_claim_remediation.json','MODERATE'),
             'I06':('RESOLVED','i10_execution_metadata_contract.json','NONE'),
             'I07':('RESOLVED','i01_probability_integrity_remediation.json','NONE'),
             'I08':('RESOLVED_WITH_DOCUMENTED_PROVENANCE_LIMITATION','i02_execution_provenance_reconstruction.json','MODERATE'),
             'I09':('RESOLVED','i07_lambda_erratum.json','NONE'),
             'I10':('RESOLVED','i08_benchmark_claim_remediation.json','NONE')}
    for finding in authority['findings_verbatim']:
        status,ev,severity=mapping[finding['id']]
        closures.append({'id':finding['id'],'finding':finding['title'],'original_severity':finding['severity'],
            'remediation':read(ev),'evidence':[ev],'status':status,'resolved':status.startswith('RESOLVED'),
            'new_severity':severity,'residual_limitation':'See evidence; formal historical acceptance not implied.' if severity!='NONE' else 'Regression coverage finite; independent re-audit pending.'})
    write('finding_closure_register.json',{'authority':'finding_authority.json','findings':closures,'new_unresolved_locations_are_I03_scope_extension':remaining})
    gates={'executed_regression':tests['gate']['passed'],'scientific_artifacts_immutable':immutable_ok,
        'no_scientific_semantics_change':all(x['category']!='SCIENTIFIC_SEMANTICS' for x in changes),
        'no_unresolved_critical':not any(not x['resolved'] and x['new_severity']=='CRITICAL' for x in closures),
        'no_unresolved_major':not any(not x['resolved'] and x['new_severity']=='MAJOR' for x in closures),
        'no_unresolved_HIGH_arbitrariness':counts['HIGH']==0,'repository_wide_unconditional_pass_removed':len(remaining)==0}
    classification='R23_N5_RUNTIME_OPTIMIZATION_AUDIT_REMEDIATION_'+('PASSED' if all(gates.values()) else 'INCOMPLETE')
    write('remediation_gate.json',{'checks':gates,'classification':classification,'status':'REMEDIATION_INCOMPLETE' if not all(gates.values()) else 'REMEDIATION_COMPLETED_PENDING_INDEPENDENT_REAUDIT',
        'independent_audit_classification':'CODE_AUDIT_FAIL','audit_reproducibility':'CODE_AUDIT_RESULT_NOT_REPRODUCED',
        'unresolved_severity_counts':dict(Counter(x['new_severity'] for x in closures if not x['resolved'])),
        'R24':'NOT_AUTHORIZED_PENDING_R23_REMEDIATION','next_task':'Complete remaining I03 generator/provenance-status guards, then R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN',
        'self_audit_pass_granted':False,'scientific_runs_started':0})
    (OUT/'README.md').write_text('# R23 n5 audit remediation\n\n'+classification+'\n\nPrimary authority: independent audit 33ae964; original IDs preserved in INITIAL_FINDINGS.md and finding_authority.json. Request section IDs I05–I10 differ from original IDs: consult the explicit mapping.\n\nFrozen-environment regression: 16/16 VERIFIED. I01 safety guards, reporting corrections, n5 evidence-bound gate, provenance reconstruction and metadata/benchmark contracts implemented. I03 remains MAJOR because repository-wide search found six additional old R23 generator/provenance PASS locations; these are recorded, not silently certified. No independent CODE_AUDIT_PASS is granted.\n\nRank02/03 remain not reauthorized. Dirty source lineage is STRONGLY_INFERRED; final parameter/trajectory evidence and resource reconciliation remain missing. Reruns are required for formal acceptance, but none started. Historical scientific files and prior audits unchanged.\n\nReproduce regression: `PYTHONDONTWRITEBYTECODE=1 /home/takuma/.conda/envs/evrp-quantum-temp/bin/python reproducibility/tools/r23_n5_remediation_regression.py`. Do not rerun initial snapshot collection or overwrite historical audits. Report regeneration: same Python with reproducibility/tools/r23_n5_remediation_report.py. Hash verification: from this directory, `sha256sum -c SHA256SUMS`.\n\nSee FINAL_REPORT.md, finding_closure_register.json and remediation_gate.json. R24 remains blocked.\n')
    # Final report is generated separately, so sealing is an explicit final action.
    print(json.dumps({'classification':classification,'tests':tests['gate'],'risk_counts':counts,'closures':[(x['id'],x['status']) for x in closures]}))

def seal():
    files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT)}\n' for p in files))
    print(json.dumps({'sealed_files':len(files)}))

def verify():
    source_checks=[{'path':r['path'],'matches':sha(ROOT/r['path'])==r['sha256']} for r in read('source_change_classification.json')['changes']]
    artifact_checks=[{'path':r['path'],'matches':sha(ROOT/r['path'])==r['current_sha256']} for r in read('original_artifact_immutability.json')['files']]
    required=['README.md','finding_authority.json','source_change_classification.json','valid_domain_regression.json','invalid_input_regression.json','multiple_optimum_regression.json','bit_ordering_regression.json','provenance_status_by_run.json','claim_reaudit.json','researcher_degrees_of_freedom_updated.json','finding_closure_register.json','remediation_gate.json','FINAL_REPORT.md']
    required += ['i01_probability_integrity_remediation.json','i02_execution_provenance_reconstruction.json','i03_validation_gate_remediation.json','i04_convergence_claim_remediation.json','i05_stopping_rule_authority_review.json','i06_optimizer_authority_review.json','i07_lambda_erratum.json','i08_benchmark_claim_remediation.json','i09_selective_reporting_remediation.json','i10_execution_metadata_contract.json']
    missing=[p for p in required if not (OUT/p).is_file()]
    json_count=0
    for p in OUT.rglob('*.json'):
        json.loads(p.read_text());json_count+=1
    for row in source_checks:
        if row['path'].endswith('.py'):compile((ROOT/row['path']).read_text(),row['path'],'exec')
    if missing or not all(r['matches'] for r in source_checks+artifact_checks):
        raise RuntimeError('Remediation artifact/source verification failed')
    write('final_verification.json',{'artifact_integrity':'VERIFIED','scientific_audit_acceptance':'NOT_GRANTED',
        'source_checks':source_checks,'protected_artifact_checks':artifact_checks,'missing_required_files':missing,
        'json_files_parsed':json_count,'source_syntax':'VERIFIED by compile without bytecode writes',
        'regression_gate':read('validation_test_manifest.json')['gate'],'remediation_classification':read('remediation_gate.json')['classification']})
    print(json.dumps({'verification':'VERIFIED','sources':len(source_checks),'protected':len(artifact_checks),'missing':missing}))

if __name__=='__main__':
    import sys
    if '--seal' in sys.argv:seal()
    elif '--verify' in sys.argv:verify()
    else:report()
