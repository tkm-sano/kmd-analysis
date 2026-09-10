#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();o=a.output.resolve()
    m=json.loads((o/'r08_service_time_manifest.json').read_text(encoding='utf-8'));d=read(o/'customer_service_times.csv')
    ids=[x['stop_id'] for x in d];assert d and all(ids) and len(ids)==len(set(ids))
    assert len(d)==m['fixture']['n'] and m['fixture']['is_production_problem_size'] is False
    assert all(math.isfinite(float(x['s_i'])) and float(x['s_i'])>=0 and float(x['s_i'])==2.5 for x in d)
    assert all(x['s_i_unit']=='minutes/customer' and x['s_i_classification']=='ASSUMED (external empirical reference)' for x in d)
    assert all('travel time' in x['service_time_excludes'] and 'waiting time' in x['service_time_excludes'] and 'charging time' in x['service_time_excludes'] for x in d)
    assert all(x['s_i_source'] and x['s_i_assumption_reason'] for x in d)
    for rec in m['inputs'].values():assert sha256(ROOT/rec['path'])==rec['sha256']
    r={'customer_count':len(d),'all_s_i_equal_2_5':True,'finite_nonnegative':True,'unit_consistent':True,'travel_waiting_charging_separate':True,'classification_and_reason_complete':True,'external_reference_provenance_complete':True,'sensitivity_range_recorded':'4-15 minutes/customer; not executed','input_hash_validation':'PASS'}
    (o/'r08_independent_validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
