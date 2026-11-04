"""Create a fresh replay trial without overwriting any result."""
from pathlib import Path
import sys,shutil,subprocess,json,hashlib,datetime
source=Path(__file__).resolve().parents[1];repo=source.parents[1]
if len(sys.argv)!=2:raise SystemExit('Usage: python -B bootstrap_replay.py /absolute/repository/review_outputs/unique_new_trial')
target=Path(sys.argv[1]).resolve()
if target.parent != repo/'review_outputs' or target.exists():raise SystemExit('New unique directory under repository/review_outputs required')
status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=repo);diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=repo)
target.mkdir();shutil.copytree(source/'scripts',target/'scripts')
for name in ['sources','logs']:(target/name).mkdir()
(target/'GIT_STATUS_START.txt').write_bytes(status);(target/'GIT_DIFF_START.patch').write_bytes(diff)
tracked=[]
for name in subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode().split('\0'):
 p=repo/name
 if p.is_file():
  with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  tracked.append({'path':name,'sha256':h,'size':p.stat().st_size})
(target/'TRACKED_BASELINE.json').write_text(json.dumps(tracked,indent=2));(target/'START.json').write_text(json.dumps({'trial':str(target),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo).decode().strip(),'created':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2));print(target)
