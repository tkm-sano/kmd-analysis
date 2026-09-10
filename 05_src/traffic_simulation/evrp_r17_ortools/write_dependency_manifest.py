#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',required=True); ap.add_argument('--r15',required=True); ap.add_argument('--r16',required=True); ap.add_argument('--r09',required=True); a=ap.parse_args(); d=Path(a.run_dir); r15=Path(a.r15); r16=Path(a.r16); r09=Path(a.r09)
    spec=json.loads((d/'ortools_formulation_spec.json').read_text()); out={'run_id':d.name,'instance_id':spec['instance_id'],'dependencies':{'R09_v18_depot':{'run_id':r09.name,'depot_definition_sha256':sha(r09/'depot_definition.csv')},'R15_current':{'run_id':r15.name,'common_instance_sha256':sha(r15/'common_instance.json')},'R16_current':{'run_id':r16.name,'constraint_spec_sha256':sha(r16/'constraint_spec.json')},'R17_formulation':{'formulation_spec_sha256':sha(d/'ortools_formulation_spec.json'),'hc_mapping_sha256':sha(d/'hc_mapping_table.json'),'r18_contract_sha256':sha(d/'r18_execution_contract.json')}},'current_authority':{'network_hash':'460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2','constraint_version':spec['constraint_version']},'r18_execution':'NOT_EXECUTED'}
    (d/'r17_dependency_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': main()
