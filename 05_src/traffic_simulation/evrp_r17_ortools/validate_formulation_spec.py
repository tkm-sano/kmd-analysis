#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--spec-dir',required=True); a=ap.parse_args(); d=Path(a.spec_dir); s=json.loads((d/'ortools_formulation_spec.json').read_text()); m=s['mapping_table']; c=s['charging_model']; p=s['payload_model']; cfg=s['solver_config']; contract=json.loads((d/'r18_execution_contract.json').read_text()); checks={'mapping_count_13':len(m)==13,'unique_constraint_ids':len({x['constraint_id'] for x in m})==13,'instance_hash_present':len(s['instance_hash'])==64,'constraint_version_exact':s['constraint_version']=='evrp-common-hard-constraints-v1','output_schema_present':len(s['r18_output_schema'])>=10,'unserved_explicit':bool(s['unserved']['representation']),'reachability_explicit':bool(s['reachability']),'soc_model_explicit':bool(s['soc_model']),'charging_semantics_recorded':c['revisit'].startswith('multiple'),'charger_bound_fixed':c['copy_count']=='n+1; fixture n=10 => 11','payload_fields_separate':p['delivery_request_count_field']=='delivery_request_count=q_i' and p['payload_mass_field']=='payload_mass_kg=m_i','payload_unit_kg':p['unit']=='kg','solver_config_fixed':cfg['ortools_version']=='9.12.4544' and cfg['first_solution_strategy']=='PATH_CHEAPEST_ARC' and cfg['local_search_metaheuristic']=='GUIDED_LOCAL_SEARCH' and cfg['num_workers']==1 and cfg['deterministic'] is True,'r18_not_executed':contract['status']=='READY_PENDING_R18'}
 result={'status':'PASS' if all(checks.values()) and not s['blockers'] else 'BLOCKED','checks':checks,'blockers':s['blockers'],'formulation_spec_hash':sha(d/'ortools_formulation_spec.json'),'reason':'R17 preparation validated; R18 remains pending and was not executed.'}
 (d/'r17_validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(result,ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
