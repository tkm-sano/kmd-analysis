from pathlib import Path
import subprocess,hashlib,json,datetime
O=Path(__file__).resolve().parents[1];R=O.parents[1]
assert not (O/'evidence/START.json').exists(),'Run only in a fresh trial; never reset an existing baseline'
for x in ['evidence','data','logs','render','PATH1_FIGURES','PATH2_FIGURES','CROSS_PATH_FIGURES']:(O/x).mkdir(exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
(O/'evidence/START.json').write_text(json.dumps(dict(trial=str(O),head=head,created=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2))
(O/'evidence/GIT_STATUS_START.txt').write_bytes(subprocess.check_output(['git','status','--short','--untracked-files=all'],cwd=R))
(O/'evidence/GIT_DIFF_START.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=R))
files=subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0');rows=[]
for name in files:
 p=R/name
 if name and p.is_file():rows.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'evidence/TRACKED_BASELINE.json').write_text(json.dumps(rows))
