"""Explicit replay entrypoint: creates no destination; requires bootstrap_replay first."""
from pathlib import Path
import sys,subprocess,json,time
O=Path(__file__).resolve().parents[1];R=O.parents[1]
if not (O/'evidence/REPLAY_SOURCE.json').is_file():raise SystemExit('Replay-only entrypoint; first bootstrap a NEW trial directory')
if (O/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv').exists():raise SystemExit('Replay has outputs; refusing to overwrite; use another new directory')
py=R/'.conda/bin/python';log=[]
sequence=[('exact_audit.py',[]),('prepare_exact_models.py',[]),('exact_recheck.py',['--pilot']),('exact_separation.py',['--pilot']),('exact_recheck.py',[]),('resolve_exact_status.py',[]),('exact_features.py',[]),('dp_reference_review.py',[]),('path1_statistics.py',[]),('zero_success_bound.py',[]),('controlled_qaoa.py',['--pilot']),('controlled_qaoa.py',[]),('runtime_analysis.py',[]),('controlled_analysis.py',[]),('control_sd_review.py',[]),('path2_analysis.py',[]),('support_and_verification.py',[]),('refine_figures.py',[]),('reference_strength_sensitivity.py',[]),('write_reports.py',[])]
for index,(name,args) in enumerate(sequence):
 command=[str(py),'-B',str(O/'scripts'/name),*args];start=time.perf_counter()
 with (O/'logs'/f'replay_{index:02d}_{Path(name).stem}.log').open('w') as stream:result=subprocess.run(command,cwd=R,stdout=stream,stderr=subprocess.STDOUT)
 log.append({'command':command,'exitcode':result.returncode,'wall_s':time.perf_counter()-start});(O/'evidence/REPLAY_EXECUTION.json').write_text(json.dumps(log,indent=2))
 if result.returncode:raise SystemExit(f'{name} failed; stop and inspect fresh trial logs; no original files modified')
print('Scientific replay complete. Create fresh start preservation baselines before execution to use final_audit.py; do not reuse original trial baselines.')
