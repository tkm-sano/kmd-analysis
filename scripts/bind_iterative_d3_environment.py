#!/usr/bin/env python3
"""Bind a staged formal registration to byte-identical, equal pilot environment evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


def read(p):
    return json.loads(p.read_bytes())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def replace(path,data):
    tmp=path.with_suffix(path.suffix+'.binding.tmp')
    with tmp.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    tmp.chmod(0o444)
    tmp.replace(path)
    directory=os.open(path.parent,os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--formal',type=Path,required=True)
    p.add_argument('--pilot',type=Path,required=True)
    p.add_argument('--backup',type=Path,required=True)
    args=p.parse_args()
    formal=args.formal.resolve()
    pilot=args.pilot.resolve()
    if any((formal/k).exists() for k in ('FREEZE_RECORD.json','EXECUTION_STATE.json','EXECUTION.lock','trials')):
        raise ValueError('ONLY_UNFROZEN_NOT_STARTED_REGISTRATION')
    m=read(formal/'MANIFEST.json')
    pm=read(pilot/'MANIFEST.json')
    registration=read(formal/'REGISTRATION.json')
    past=formal/'ENVIRONMENT.json'
    actual=pilot/'ENVIRONMENT.json'
    if not (m['output']==str(formal) and m['stage']=='formal' and pm['stage']=='pilot' and
            m['version']==pm['version']=='iterative-d3-v2' and m['code_hashes']==pm['code_hashes'] and
            m['seed_sha256']==pm['seed_sha256'] and m['counts']['comparison_cases']==90 and pm['counts']['comparison_cases']==3 and
            sha(formal/'MANIFEST.json')==registration['manifest_sha256'] and
            sha(pilot/'MANIFEST.json')==read(pilot/'REGISTRATION.json')['manifest_sha256'] and
            sha(past)==m['environment_sha256'] and sha(actual)==pm['environment_sha256'] and read(past)==read(actual)):
        raise ValueError('PILOT_AND_FORMAL_ENVIRONMENT_NOT_EQUIVALENT')
    args.backup.mkdir(parents=True,exist_ok=False)
    files=('ENVIRONMENT.json','MANIFEST.json','REGISTRATION.json')
    for name in files:
        shutil.copy2(formal/name,args.backup/name)
    m['environment_sha256']=pm['environment_sha256']
    replace(past,actual.read_bytes())
    replace(formal/'MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2,allow_nan=False).encode())
    replace(formal/'REGISTRATION.json',json.dumps(registration | {'manifest_sha256':sha(formal/'MANIFEST.json')},
            ensure_ascii=False,indent=2,allow_nan=False).encode())
    before=read(args.backup/'MANIFEST.json')
    assert read(formal/'MANIFEST.json')==(before|{'environment_sha256':pm['environment_sha256']})
    record=dict(equal_parsed_environment=True,changed_manifest_fields=['environment_sha256'],
      before={k:sha(args.backup/k) for k in files},after={k:sha(formal/k) for k in files},formal_workers_submitted=0)
    (args.backup/'BINDING.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))
if __name__=='__main__':
    main()
