#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',required=True); ap.add_argument('--config',required=True); a=ap.parse_args(); d=Path(a.run_dir); c=Path(a.config); shutil.copy2(c,d/'r09_v18_config.yml'); m=json.loads((d/'r09_depot_manifest.json').read_text()); m['outputs'].update({'r09_v18_validation_report.json':{'path':str((d/'r09_v18_validation_report.json').as_posix()),'sha256':sha(d/'r09_v18_validation_report.json')},'r09_v18_config.yml':{'path':str((d/'r09_v18_config.yml').as_posix()),'sha256':sha(d/'r09_v18_config.yml')}}); (d/'r09_depot_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': main()
