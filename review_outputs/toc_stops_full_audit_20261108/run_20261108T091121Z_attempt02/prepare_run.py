"""Prepare a NEW audit directory; copy audit tools and snapshot repository state."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path('/home/takuma/kmd-analysis')
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve()
    assert out.is_relative_to(ROOT/'review_outputs/toc_stops_full_audit_20261108')
    assert not out.exists(),'New directory required; do not overwrite audit artifacts'
    status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=ROOT).decode()
    files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    tracked={}
    for name in files:
        f=ROOT/name
        if name and f.is_file():
            with f.open('rb') as stream:tracked[name]=hashlib.file_digest(stream,'sha256').hexdigest()
    out.mkdir(parents=True,exist_ok=False)
    for name in ['AUDIT_PROTOCOL.json','audit_stops.py','validate_audit.py','build_report.py','prepare_run.py','finalize_delivery.py','REPRODUCE.md']:
        with (out/name).open('xb') as f:f.write((HERE/name).read_bytes())
    state={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),'status_porcelain_z':status,'tracked_sha256':tracked,'python':sys.executable}
    with (out/'REPOSITORY_BEFORE.json').open('x') as f:json.dump(state,f,ensure_ascii=False,indent=2)
    print(out)
if __name__=='__main__':main()
