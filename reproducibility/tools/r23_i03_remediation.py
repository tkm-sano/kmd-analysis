"""Collect and verify I03-only remediation evidence; no scientific execution."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_i03_validation_gate_remediation/20260913_v1'
PREV=ROOT/'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_audit_remediation/20260913_v1'
BASE='9cce6ebacfb180b0df84874d9b3648b8935eefe0'
ORIGINAL=[
 'tools/authorize_r23_experiment_b2.py','tools/review_r23_experiment_b2_nelder_mead.py',
 'tools/build_r23_experiment_b2_reexecution_authority.py','tools/finalize_r23_b1_v2.py',
 'tools/finalize_r23_experiment_b2_reexecution.py','05_src/traffic_simulation/r23_qaoa_aer/artifact.py']
ADDITIONAL=['tools/finalize_r23_experiment_b2_failure.py','reproducibility/tools/r23_b2_evidence_review.py','tools/build_r23_experiment_b1_fix_authority.py','tools/execute_r23_experiment_b2.py','tools/execute_r23_experiment_b2_reexecution.py']
ADDITIONAL += ['tools/build_r23_experiment_b_authority.py','05_src/traffic_simulation/r20_route_ordering/resolve_r23_design_authority.py','05_src/traffic_simulation/r20_route_ordering/freeze_r23_instance_authority.py']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def write(name,obj):
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def initialize():
 if (OUT/'start_state.json').exists():raise RuntimeError('Initial snapshot already frozen')
 write('start_state.json',{'HEAD':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),
  'git_status':git('status','--short'),'hostname':platform.node(),'python':subprocess.check_output(['which','python'],text=True).strip(),
  'collector_python':sys.executable,'environment':{k:os.environ.get(k) for k in ('CONDA_PREFIX','CONDA_DEFAULT_ENV','VIRTUAL_ENV')},'timestamp':dt.datetime.now(dt.timezone.utc).isoformat()})
 # Include all tracked historical R23 outputs and configs, not only successful runs.
 protected=[p for p in git('ls-files').splitlines() if ('/outputs/traffic_simulation/r23_' in p or '/config/traffic_simulation/r23_' in p)]
 write('initial_artifact_snapshot.json',{'files':[{'path':p,'sha256':sha(ROOT/p)} for p in protected]})
 old=json.loads((PREV/'i03_validation_gate_remediation.json').read_text())['remaining_unconditional_locations']
 rows=[];folder=OUT/'historical_source_snapshots';folder.mkdir()
 for i,path in enumerate(ORIGINAL+ADDITIONAL,1):
  text=(ROOT/path).read_text();matches=[{'line':n,'text':t} for n,t in enumerate(text.splitlines(),1) if 'PASS' in t or ('True' in t and ('check' in t or 'validation' in t))]
  name=f'{i:02d}_{Path(path).name}.txt';(folder/name).write_text(text)
  rows.append({'id':f'G{i:02d}','file':path,'function':'build_provenance_lineage' if path.endswith('/artifact.py') else 'main / module-level summary generation',
   'experiment':'R21/R22 lineage' if path.endswith('/artifact.py') else ('B1' if 'b1' in path else 'B2'),
   'current_behavior':'Outputs success summaries without computing every represented validation condition',
   'why_invalid':old[i-1]['issue'] if i<=6 else 'Constant scientific integrity/baseline success, gap zeros or preflight claims without checking represented contents',
   'matched_lines':matches,'sha256':sha(ROOT/path),'source_archive':'historical_source_snapshots/'+name,'previously_reported':i<=6})
 write('residual_unconditional_pass_inventory.json',{'previous_file_count':6,'confirmed_original_file_count':sum((ROOT/p).exists() for p in ORIGINAL),
  'actual_file_count':len(rows),'unit':'affected file/function clusters, not literal PASS occurrences','additional_file_count':len(ADDITIONAL),'locations':rows})
 print(json.dumps({'protected_files':len(protected),'residual_file_clusters':len(rows)}))

def extend_inventory():
 p=OUT/'residual_unconditional_pass_inventory.json';d=json.loads(p.read_text());known={r['file'] for r in d['locations']}
 for path in ADDITIONAL:
  if path in known:continue
  source=git('show',BASE+':'+path)+'\n';name=f"{len(d['locations'])+1:02d}_{Path(path).name}.txt"
  (OUT/'historical_source_snapshots'/name).write_text(source)
  d['locations'].append({'id':f"G{len(d['locations'])+1:02d}",'file':path,'function':'main / preflight checks','experiment':'B1' if 'b1' in path else 'B2',
   'current_behavior':'constant validation booleans or unexecuted pytest/compile success','why_invalid':'individual reported validation claims exceed executed conditions; top-level guards do not validate every named check',
   'matched_lines':[{'line':n,'text':t} for n,t in enumerate(source.splitlines(),1) if 'PASS' in t],
   'sha256':hashlib.sha256(source.encode()).hexdigest(),'source_archive':'historical_source_snapshots/'+name,'previously_reported':False})
 d['actual_file_count']=len(d['locations']);d['additional_file_count']=len(d['locations'])-6
 write(p.name,d)

if __name__=='__main__':
 extend_inventory() if '--extend' in sys.argv else initialize()
