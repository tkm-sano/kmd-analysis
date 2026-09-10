#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--spec-dir',required=True); a=ap.parse_args(); d=Path(a.spec_dir); s=json.loads((d/'constraint_spec.json').read_text()); inst=Path(s['input_instance_path']); checks={}
 checks['constraint_count_13']=len(s['constraints'])==13
 checks['unique_ids']=len({x['constraint_id'] for x in s['constraints']})==13
 checks['required_fields']=all(all(k in x for k in ('constraint_id','constraint_name','formal_meaning','applicable_entity','required_inputs','unit','enabled','judgement','tolerance','violation_condition','validator_check','source_rationale','downstream_solver_mapping_placeholder')) for x in s['constraints'])
 checks['instance_exists_and_hash']=inst.exists() and sha(inst)==s['input_instance_hash']
 checks['all_units_defined']=all(x['unit'] and x['tolerance'] for x in s['constraints'])
 checks['objective_separated']=s['objective_separation']['customer_nonvisit_allowed'] and s['objective_separation']['full_customer_service_is_not_hard_constraint']
 checks['validator_contract_complete']=len(s['validator_contract']['must_recompute'])>=13 and 'charging revisit/session semantics' in s['validator_contract']['must_recompute'] and s['validator_contract']['solver_status_not_authoritative'] is True
 checks['same_version_reference']=s['constraint_version'].startswith('evrp-common-hard-constraints-')
 unresolved=['charging_station_revisit_policy'] if s['charging_station_revisit_policy']['status']=='UNRESOLVED' else []
 result={'status':'BLOCKED' if unresolved else ('PASS' if all(checks.values()) else 'FAIL'),'checks':checks,'unresolved_semantics':unresolved,'constraint_version':s['constraint_version'],'input_instance_hash':s['input_instance_hash'],'spec_hash':sha(d/'constraint_spec.json')}
 (d/'r16_validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(result,ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
