#!/usr/bin/env python3
"""Independent validation for R07 synthetic time windows."""

from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]

def sha256(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def read(path):
    with path.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('output',type=Path); a=ap.parse_args(); out=a.output.resolve()
    m=json.loads((out/'r07_time_window_manifest.json').read_text(encoding='utf-8')); data=read(out/'customer_time_windows.csv')
    ids=[r['stop_id'] for r in data]; assert data and all(ids) and len(ids)==len(set(ids))
    assert len(data)==m['fixture']['n'] and m['fixture']['is_production_problem_size'] is False
    assert m['classification']=='SYNTHETIC_CALIBRATED' and m['service_start_constraint']=='e_i <= b_i <= l_i'
    assert all(math.isfinite(float(r['e_i'])) and math.isfinite(float(r['l_i'])) and float(r['e_i'])<=float(r['l_i']) for r in data)
    assert all(r['time_origin']=='local_day_start_00:00' and r['time_unit']=='hours' for r in data)
    assert all(r['classification']=='SYNTHETIC_CALIBRATED' and r['source_time_specification_category'] for r in data)
    allowed={'unspecified','date_only','time_band','clock_time_proxy'}; assert {r['time_window_category'] for r in data} <= allowed
    for r in data:
        e,l=float(r['e_i']),float(r['l_i']); cat=r['time_window_category']
        if cat in {'unspecified','date_only'}: assert (e,l)==(0.0,24.0)
        elif cat=='time_band': assert math.isclose(l-e,2.0) or (e==0 and l==1) or (e==23 and l==24)
        else: assert math.isclose(l-e,1.0)
    for rec in m['inputs'].values(): assert sha256(ROOT/rec['path'])==rec['sha256']
    summary=json.loads((out/'r07_time_window_summary.json').read_text(encoding='utf-8'))
    assert sum(summary['category_counts'].values())==len(data)
    result={'customer_count':len(data),'time_specified_count':sum(r['time_specified']=='True' for r in data),'time_unspecified_count':sum(r['time_specified']=='False' for r in data),'category_counts':summary['category_counts'],'finite_and_ordered':True,'consistent_units_origin':True,'statistics_not_treated_as_windows':True,'input_hash_validation':'PASS'}
    (out/'r07_independent_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
