"""Create an isolated copy of this trial's analysis code; never overwrite any trial."""
from pathlib import Path
import sys,shutil,subprocess,json,datetime
source=Path(__file__).resolve().parents[1];repo=source.parents[1]
if len(sys.argv)!=2:raise SystemExit('Usage: bootstrap_replay.py /absolute/repo/review_outputs/new_unique_step2_trial')
target=Path(sys.argv[1]).resolve()
if target.parent!=repo/'review_outputs' or target.exists():raise SystemExit('Target must be NEW under repository review_outputs')
target.mkdir();shutil.copytree(source/'scripts',target/'scripts')
for name in ['evidence','logs','experiments','PATH1_STATISTICAL_FIGURES','QAOA_CONTROLLED_EXPERIMENT_FIGURES','PATH1_RUNTIME_FIGURES','PATH2_FIGURES']:(target/name).mkdir()
for name in ['EXACT_RECHECK_PROTOCOL.md','QAOA_CONTROLLED_EXPERIMENT_DESIGN.md','PATH1_RUNTIME_PROTOCOL.md','PATH2_ANALYSIS_PROTOCOL.md','STATISTICAL_METHODS.md']:shutil.copyfile(source/name,target/name)
(target/'evidence/REPLAY_SOURCE.json').write_text(json.dumps({'source_trial':str(source),'created':datetime.datetime.now().astimezone().isoformat(),'purpose':'isolated scientific replay; numerical values compared by key, timing not bitwise'},indent=2));print(target)
