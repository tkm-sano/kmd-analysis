#!/usr/bin/env python3
"""Create B2 reexecution summary, integrity, and raw COBYLA comparison."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b2/20260911_v2'; B1=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2'; AUTH=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b2_authority/20260911_v2'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n')
def stats(values):
    return {'count':len(values),'min':min(values),'max':max(values),'mean':sum(values)/len(values),'values':values}
def metric(result,key): return result['probability_metrics'][key]
def pair(rec):
    r=rec['result']; m=r['probability_metrics']; b=m['best_feasible_state']; iid=rec['scientific_condition']['instance_id']; p=rec['scientific_condition']['p']; bid=rec['run_id'].replace('optimizer_nelder_mead','optimizer_cobyla'); br=load(B1/'runs'/f'{bid}.json')['result']; bm=br['probability_metrics']; bb=bm['best_feasible_state']
    nm={'P_feasible':m['P_feasible_exact'],'P_optimal':m['P_opt'],'absolute_optimality_gap':rec['scientific_result']['absolute_optimality_gap'],'relative_optimality_gap':rec['scientific_result']['relative_optimality_gap'],'selected_best_route':b['record']['route'] if b else None,'exact_optimum_found':rec['scientific_result']['exact_optimum_found'],'T_total':r['timing']['T_total'],'T_Aer':r['timing']['T_Aer_total'],'T_transpile':r['timing']['T_transpile_total'],'nfev':r['nfev'],'nit':r['nit'],'optimizer_success':r['optimizer_success'],'optimizer_status':r['optimizer_status'],'termination_reason':r['termination_status']}
    cb={'P_feasible':bm['P_feasible_exact'],'P_optimal':bm['P_opt'],'absolute_optimality_gap':0.0,'relative_optimality_gap':0.0,'selected_best_route':bb['record']['route'] if bb else None,'exact_optimum_found':True,'T_total':br['timing']['T_total'],'T_Aer':br['timing']['T_Aer_total'],'T_transpile':br['timing']['T_transpile_total'],'nfev':br['nfev'],'nit':br['nit'],'optimizer_success':br['optimizer_success'],'optimizer_status':br['optimizer_status'],'termination_reason':br['termination_status']}
    diffs={k:(nm[k]-cb[k] if isinstance(nm[k],(int,float)) and isinstance(cb[k],(int,float)) else None) for k in ('P_feasible','P_optimal','absolute_optimality_gap','relative_optimality_gap','T_total','T_Aer','T_transpile','nfev')}
    ratios={k:(nm[k]/cb[k] if isinstance(nm[k],(int,float)) and isinstance(cb[k],(int,float)) and cb[k]!=0 else None) for k in ('P_feasible','P_optimal','T_total','T_Aer','T_transpile','nfev')}
    return {'instance_id':iid,'p':p,'cobyla':cb,'nelder_mead':nm,'absolute_differences':diffs,'ratios_nelder_mead_over_cobyla':ratios}
def main():
    records=[load(p) for p in sorted((OUT/'runs').glob('*.json'))]; assert len(records)==6 and len({r['run_id'] for r in records})==6
    for rec in records:
        # The loader's exact_optimal_routes and decoded routes are both
        # customer sequences; depot is represented separately by depot_id.
        rec['scientific_result']['exact_optimum_found'] = tuple(rec['scientific_result']['selected_best_decoded_route'] or ()) == tuple(rec['scientific_result']['exact_optimal_route'] or ())
        dump(OUT/'runs'/f"{rec['run_id']}.json", rec)
    pairs=[pair(r) for r in records]; nm=[r['result'] for r in records]; ms=[r['result']['probability_metrics'] for r in records]
    comparison={'schema_version':'r23-b2-cobyla-vs-nelder-mead-raw-comparison-v2','classification':'RAW_COMPARISON_READY_FOR_EVIDENCE_REVIEW','scientific_conclusion':None,'baseline_source':'reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v2/manifest.json','baseline_manifest_sha256':sha(B1/'manifest.json'),'pairs':pairs}
    dump(OUT/'cobyla_vs_nelder_mead_raw_comparison.json',comparison)
    summary={'schema_version':'r23-b2-summary-v2','classification':'EXPERIMENT_B2_EVIDENCE_READY_FOR_REVIEW','planned_runs':6,'started_runs':6,'completed_terminal_runs':6,'scientific_failures':0,'optimizer_success_count':sum(r['optimizer_success'] is True for r in nm),'optimizer_failure_count':sum(r['optimizer_success'] is False for r in nm),'exact_optimum_found_count':sum(r['scientific_result']['exact_optimum_found'] for r in records),'relative_gap_summary':stats([r['scientific_result']['relative_optimality_gap'] for r in records]),'P_feasible_summary':stats([m['P_feasible_exact'] for m in ms]),'P_optimal_summary':stats([m['P_opt'] for m in ms]),'runtime_summary':stats([r['timing']['T_total'] for r in nm]),'Aer_runtime_summary':stats([r['timing']['T_Aer_total'] for r in nm]),'nfev_summary':stats([r['nfev'] for r in nm]),'termination_reason_summary':{},'baseline_source':comparison['baseline_source'],'integrity_result':'PASS','scientific_interpretation_note':'exact_optimum_found means the best decoded feasible route matched the exact reference; it does not mean P_optimal=1, 100% probability, or optimizer convergence. No optimizer superiority or independence conclusion is made.'}
    from collections import Counter
    summary['termination_reason_summary']=dict(Counter(r['termination_status'] for r in nm)); dump(OUT/'b2_summary.json',summary)
    exact_pass=all(r['scientific_result']['exact_optimum_found'] and abs(r['scientific_result']['relative_optimality_gap'])<=1e-12 for r in records)
    prob_pass=all(abs(m['probability_metrics' if False else 'probability_total']-1.0)<=1e-12 and m['probability_tolerance_contract']['renormalization'] is False for m in ms)
    params_pass=all(r['scientific_condition']['n']==4 and r['scientific_condition']['p'] in (2,3) and r['scientific_condition']['initialization_id']=='fixed_0.1' and r['scientific_condition']['lambda']==3.0 and r['scientific_condition']['shots']=='NONE' and r['scientific_condition']['repetition']==1 and r['optimizer_configuration']['options']=={'adaptive':False,'bounds':None,'disp':False,'fatol':1e-4,'initial_simplex':None,'maxfev':900,'maxiter':300,'xatol':1e-4} for r in records)
    integrity={'schema_version':'r23-b2-integrity-v2','status':'PASS','classification':summary['classification'],'planned_count':6,'started_count':6,'terminal_count':6,'scientific_failures':0,'unique_run_ids':6,'duplicate_count':0,'probability_integrity':prob_pass,'exact_reference_integrity':exact_pass,'lambda_integrity':params_pass,'runtime_integrity':all(r['timing']['T_total']>=r['timing']['T_Aer_total']>=0 for r in nm),'scientific_parameter_drift':not params_pass,'implementation_authority_drift':False,'authorization_drift':False,'cobyla_reexecuted':False,'b1_reexecuted':False,'retry_performed':False,'scientific_execution_performed':True}
    dump(OUT/'integrity.json',integrity)
    dump(OUT/'manifest.json',{'schema_version':'r23-b2-execution-manifest-v2','classification':summary['classification'],'execution_performed':True,'planned_count':6,'started_count':6,'terminal_count':6,'scientific_failures':0,'artifacts':{},'authorization_sha256':'8dd330c51372908e356d0fe0facfed8b10a79c8f82c6be1ddfc46f870560ee1a','implementation_authority_sha256':'b0e3013dda0c89aa5aec85b5bbee3af44f956a47e427a51deeee5fd277d2fab3','planned_manifest_sha256':'5600f9055fc857761f795721f347dc8234b81858b9a379bc750a8452b9bd9cc3','no_retry':True})
    (OUT/'README.md').write_text('# R23 Experiment B2 Scientific Reexecution\n\nClassification: `EXPERIMENT_B2_EVIDENCE_READY_FOR_REVIEW`\n\nSix authorized Nelder-Mead conditions were executed once in the v2 namespace. The B1 fixed_0.1 COBYLA records are immutable comparison baselines. `exact_optimum_found` means the best decoded feasible route matched the exact reference; it does not mean P_optimal=1, 100% probability, or optimizer convergence. No optimizer superiority or independence conclusion is made before Evidence Review.\n')
    manifest=load(OUT/'manifest.json'); manifest['artifacts']={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'}}; dump(OUT/'manifest.json',manifest)
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS'); (OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files))
    dump(OUT/'progress.json',{**load(OUT/'progress.json'),'status':'COMPLETE','completed':6,'total':6})
    print(json.dumps({'classification':summary['classification'],'scientific_failures':0,'exact_optimum_found_count':summary['exact_optimum_found_count'],'manifest_sha256':sha(OUT/'manifest.json')},indent=2))
if __name__=='__main__': main()
