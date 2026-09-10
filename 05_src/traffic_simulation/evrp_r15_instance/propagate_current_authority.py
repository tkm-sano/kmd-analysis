#!/usr/bin/env python3
"""Copy the validated R15 fixture while changing authority references only."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True); ap.add_argument('--output',required=True); ap.add_argument('--r09',required=True); ap.add_argument('--r16',required=True); ap.add_argument('--instance-id',required=True); a=ap.parse_args()
    src=Path(a.source); out=Path(a.output); out.mkdir(parents=True,exist_ok=False); shutil.copytree(src,out,dirs_exist_ok=True)
    r09=Path(a.r09); r16=Path(a.r16)
    x=json.loads((out/'common_instance.json').read_text()); x['instance_id']=a.instance_id; x['constraint_version']=json.loads((r16/'constraint_spec.json').read_text())['constraint_version']; x['depot']['mapped_edge_id']='617631294'; x['depot']['edge_offset_m']=12.507432581420328; x['depot']['mapping_distance_m']=1.4616751655855091; x['routing']['network_authority']='CURRENT-NETWORK-COMPLETION-AUTHORITY-V18-GEOMETRY-REACCEPTED'; x['routing']['network_hash']='460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2'
    ref=x['source_hashes']['r09_depot']; p=r09/'depot_definition.csv'; ref.update(path=str(p),sha256=sha(p),classification='PROXY',unit='coordinates and edge mapping',transformation='R09 V18 selected proxy',assumption_reason='')
    (out/'common_instance.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
    ledger=json.loads((out/'provenance_ledger.json').read_text()); ledger['r09_depot']=ref; (out/'provenance_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
    cfg=json.loads((out/'r15_config.json').read_text()); cfg['instance_id']=a.instance_id; cfg['source_run_ids']['R09']=r09.name; cfg['source_run_ids']['R16']=r16.name; (out/'r15_config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    manifest={'run_id':out.name,'instance_id':a.instance_id,'current_authorities':{'r09_run_id':r09.name,'r16_run_id':r16.name,'network_hash':x['routing']['network_hash'],'constraint_version':x['constraint_version']},'outputs':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='r15_manifest.json'}}; (out/'r15_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': main()
