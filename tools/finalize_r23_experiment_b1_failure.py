"""Finalize the B1 terminal-failure record set without rerunning any condition."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b1/20260911_v1'
AUTH=ROOT/'reproducibility/outputs/traffic_simulation/r23_experiment_b_authority/20260911_v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):
 p=OUT/name; p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); return p
files=sorted((OUT/'runs').glob('*.json'))
records=[json.loads(p.read_text()) for p in files]
failure_counts={}
for r in records: failure_counts[r.get('exception',r.get('terminal_outcome','UNKNOWN'))]=failure_counts.get(r.get('exception',r.get('terminal_outcome','UNKNOWN')),0)+1
summary=dump('b1_summary.json',{'schema_version':'r23-experiment-b1-summary-v1','classification':'EXPERIMENT_B1_FAILED_IMPLEMENTATION_FIX_REQUIRED','planned_runs':36,'terminal_records':len(records),'successful_runs':0,'failed_runs':len(records),'research_metrics_available':False,'failure_counts':failure_counts,'root_cause':'R23SchemaError: R22 instance selection is not unique; runner used central R22 conversion artifact rather than the frozen per-instance R22 authority paths.','qaoa_or_aer_objective_evaluations':0,'retry_performed':False})
robust=dump('initialization_robustness_summary.json',{'schema_version':'r23-experiment-b1-initialization-summary-v1','classification':'NOT_AVAILABLE_IMPLEMENTATION_FAILURE','cells':[],'interpretation':'No P_feasible/P_optimal/gap robustness inference is valid because all 36 conditions failed before R22 instance loading.'})
integrity=dump('integrity.json',{'schema_version':'r23-experiment-b1-integrity-v1','classification':'FAIL','planned_count':36,'terminal_count':len(records),'unique_run_ids':len({r['run_id'] for r in records})==36,'all_authorized_conditions_accounted_for':len(records)==36,'all_records_are_terminal':all(r.get('classification')=='RESEARCH_TERMINAL_RECORD' for r in records),'all_runs_failed_before_qaoa':all(r.get('terminal_outcome')=='IMPLEMENTATION_EXCEPTION' for r in records),'failure_reason_consistent':len(failure_counts)==1,'metrics_integrity':'NOT_APPLICABLE','authority_drift_after_execution':'NOT_ASSESSED_BY_EXECUTION; source artifacts unchanged','formal_a_artifacts_modified':False,'b2_executed':False,'n5_executed':False,'experiment_c_executed':False})
index=json.loads((OUT/'terminal_records.json').read_text())
manifest=dump('manifest.json',{'schema_version':'r23-experiment-b1-manifest-v1','classification':'EXPERIMENT_B1_FAILED_IMPLEMENTATION_FIX_REQUIRED','execution_performed':False,'execution_attempts':36,'qaoa_formal_evaluations':0,'files':{'execution_preflight.json':sha(OUT/'execution_preflight.json'),'terminal_records.json':sha(OUT/'terminal_records.json'),'b1_summary.json':sha(summary),'initialization_robustness_summary.json':sha(robust),'integrity.json':sha(integrity)},'run_record_count':len(index['records']),'no_retry':True,'no_adaptive_tuning':True})
print(json.dumps({'summary_sha256':sha(summary),'robustness_sha256':sha(robust),'integrity_sha256':sha(integrity),'manifest_sha256':sha(manifest),'terminal_count':len(records),'qaoa_evaluations':0},indent=2))
