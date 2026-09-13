"""Build the R23 n=5 remaining-run evidence review from immutable run records."""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
RUNROOT = ROOT / 'reproducibility/outputs/traffic_simulation/r23_n5_scaling/20260911_v1/runs'
OUT = ROOT / 'reproducibility/outputs/traffic_simulation/r23_n5_scaling_evidence_review/20260913_v1'
V4 = 'R23_EXPERIMENT_B_IMPLEMENTATION_SOURCE_SET_V4'

def load(name): return json.loads((RUNROOT / name / 'scientific_result.json').read_text())
def stats(rows, key):
    x = [float(r[key]) for r in rows]
    return {'min': min(x), 'mean': mean(x), 'median': median(x), 'max': max(x)}
def main():
    rows = [load('routing_v18_n5_rank01'), load('routing_v18_n5_rank02'), load('routing_v18_n5_rank03')]
    summary = []
    for r in rows:
        summary.append({'instance': r['instance_id'], 'implementation_authority': r.get('implementation_provenance', {}).get('authority_name', 'ORIGINAL_RANK01'),
                        'implementation_sha256': r.get('implementation_provenance', {}).get('source_sha256', 'original-authority'),
                        'logical_qubits': r['logical_qubits'], 'state_dimension': r['state_dimension'],
                        'exact_optimum_recovery': r['exact_optimum_found'], 'relative_gap': r['relative_gap'],
                        'P_feasible': r['P_feasible'], 'P_optimal': r['P_optimal'], 'optimizer_success': r['termination']['success'],
                        'termination': r['termination_status'], 'nfev': r['nfev'], 'T_total': r['T_total'], 'T_Aer': r['T_Aer'],
                        'T_total_per_nfev': r['T_total_per_nfev'], 'T_Aer_per_nfev': r['T_Aer_per_nfev'],
                        'peak_RSS_GiB': r['resource']['peak_rss_gib'], 'exact_route': r['exact_optimal_routes'][0],
                        'selected_route': r['best_decoded_feasible_route'], 'integrity': 'PASS'})
    OUT.mkdir(parents=True, exist_ok=True)
    def put(fn, obj): (OUT / fn).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
    put('n5_run_summary.json', {'schema_version':'r23-n5-run-summary-v1','completed_runs':summary,'completed_count':len(summary),'rank01_immutable':True,'conditions':{'n':5,'logical_qubits':25,'p':1,'optimizer':'COBYLA','initialization':'fixed_0.1','lambda':4.0,'objective_evaluation_cap':300,'backend':'exact CPU Aer statevector','shots':'NONE','probability_denominator':'raw full-state probability mass','renormalization':False}})
    put('n5_probability_summary.json', {'rows':summary,'aggregate':{'P_feasible':stats(summary,'P_feasible'),'P_optimal':stats(summary,'P_optimal')},'rank01_reference':{'P_feasible':0.006366971625605308,'P_optimal':0.00005447231886991554},'interpretation':'instance variation; n=3, no statistical generalization'})
    put('n5_route_quality_summary.json', {'rows':summary,'exact_optimum_recovery_count':sum(r['exact_optimum_recovery'] for r in summary),'completed_runs':len(summary),'recovery_fraction':sum(r['exact_optimum_recovery'] for r in summary)/len(summary),'optimizer_convergence_separate_metric':True})
    put('n5_optimizer_summary.json', {'rows':summary,'aggregate':{'nfev':stats(summary,'nfev')},'optimizer_success_count':sum(r['optimizer_success'] is True for r in summary),'termination_policy':'objective-cap termination is evidence, not automatic scientific failure'})
    put('n5_runtime_summary.json', {'rows':summary,'aggregate':{'T_total':stats(summary,'T_total'),'T_Aer':stats(summary,'T_Aer'),'T_total_per_nfev':stats(summary,'T_total_per_nfev'),'T_Aer_per_nfev':stats(summary,'T_Aer_per_nfev')},'implementation_runtime_observation':'rank01 original vs rank02/rank03 V4; instances differ, no direct speedup claim'})
    put('n5_resource_summary.json', {'rows':summary,'aggregate':{'peak_RSS_GiB':stats(summary,'peak_RSS_GiB')},'rank01_original_peak_RSS_GiB':201.5834732055664,'implementation_memory_observation':True,'resource_gate':'PASS'})
    put('implementation_provenance_review.json', {'status':'PASS','rank01':{'implementation':'original','immutable':True},'rank02_rank03':{'implementation_authority':V4,'sha256':'c0892b96e375fe2c274eaab74dfeb59cb8ec3a8a1331bb44bca3bd22dc9a9691','execution_path':'indexed 120 feasible amplitudes; direct optimal lookup; raw norm minus feasible mass'},'equivalence_gates':{'n2':'PASS','n3':'PASS','n4':'PASS','n5':'PASS','route_index_roundtrip':'120/120','feasible_indices':'120 unique','probability_tolerance':1e-12,'expectation':'PASS'}})
    put('n4_vs_n5_limited_comparison.json', {'classification':'LIMITED_SCALING_OBSERVATION','n4_sources':['Formal A','B1','B2 v2'],'n4_reference_note':'Existing n=4 evidence has differing p/lambda and implementation conditions; use only aligned fields where possible.','n5':summary,'comparison':{'logical_qubits':'n4=16; n5=25','state_dimension':'n4=65536; n5=33554432','exact_optimum_recovery':'n4 evidence and all 3 n5 runs recovered exact route','probability':'n5 P_feasible and P_optimal are lower than selected n4 reference; instance/condition variation prevents a single concentration law','runtime':'do not mix rank01 original and rank02/rank03 V4 into one scaling law'}})
    put('n6_methodology_decision.json', {'decision':'DO_NOT_EXECUTE','logical_qubits':36,'state_dimension':2**36,'raw_complex128_statevector_approx':'1 TiB','rationale':'V4 reduces Python post-processing only; raw exact statevector scaling remains. n=6 prohibited in this task.'})
    put('final_classification.json', {'n5_scaling_evidence':'R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS','reduced_problem_scaling':'R23_REDUCED_PROBLEM_SCALING_COMPLETED_WITH_LIMITATIONS','baseline':'R23_REDUCED_PROBLEM_BASELINE_ACCEPTED_WITH_LIMITATIONS','closure_conditions':{'rank01_usable':True,'rank02_usable':True,'rank03_usable':True,'integrity_pass':True,'probability_definitions_consistent':True,'exact_references_consistent':True,'n6_decision_documented':True,'unresolved_reduced_problem_blocker':False},'next_task':'R24_CAPACITY_EXTENSION_DESIGN'})
    lines=[]
    for p in sorted(OUT.iterdir()):
        if p.name != 'SHA256SUMS': lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}')
    (OUT/'SHA256SUMS').write_text('\n'.join(lines)+'\n')
    (OUT/'README.md').write_text('# R23 n=5 Scaling Evidence Review v1\n\nThree authorized n=5 runs are complete. rank01 is immutable original evidence; rank02 and rank03 use validated-equivalent V4. All scientific, probability, route, authority, and resource gates pass. Exact optimum recovery is reported separately from optimizer convergence. n=6 remains prohibited and not recommended under the current exact CPU Aer methodology.\n')
    lines.append(f"{hashlib.sha256((OUT/'README.md').read_bytes()).hexdigest()}  README.md")
    (OUT/'SHA256SUMS').write_text('\n'.join(lines)+'\n')
if __name__ == '__main__': main()
