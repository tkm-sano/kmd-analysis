#!/usr/bin/env python3
"""Attach the R08 Baseline service-time assumption to R07 customers."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / 'reproducibility/config/traffic_simulation/evrp_r08_service_time_v1.yml'

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def read(path):
    with path.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',type=Path,default=DEFAULT_CONFIG); ap.add_argument('--run-id',required=True); a=ap.parse_args()
    cp=a.config.resolve(); cfg=yaml.safe_load(cp.read_text(encoding='utf-8'))
    r07=(ROOT/cfg['inputs']['r07_time_windows']).resolve(); r07m=(ROOT/cfg['inputs']['r07_manifest']).resolve()
    out=(ROOT/cfg['output_root']/a.run_id).resolve(); out.mkdir(parents=True,exist_ok=False)
    src=read(r07); ids=[r['stop_id'] for r in src]
    if not src or any(not x for x in ids) or len(ids)!=len(set(ids)): raise ValueError('R07 customer IDs missing or duplicated')
    s=float(cfg['baseline']['service_time_minutes_per_customer'])
    if not math.isfinite(s) or s<0: raise ValueError('service time must be finite and non-negative')
    result=[]
    for order,row in enumerate(src,1):
        x=dict(row); x.update({'s_i':s,'s_i_unit':'minutes/customer','s_i_classification':'ASSUMED (external empirical reference)','s_i_source':'Schrader et al. (2024), Urban context and delivery performance: Modelling service time for cargo bikes and vans across diverse urban environments','s_i_source_scope':'urban parcel delivery; city-context service time reference; not Ota-ku observation','s_i_transformation':'apply fixed Baseline model assumption s_i=2.5 minutes/customer to every R07 customer','s_i_assumption_reason':'External empirical reference is used to set an explicit Baseline assumption; no Ota-ku stop-level measurement is claimed','service_time_excludes':'travel time; waiting time; charging time','sensitivity_candidate_range_minutes_per_customer':'4-15 (not executed)','service_time_seed':'not_applicable_deterministic'})
        result.append(x)
    fields=list(result[0])
    with (out/'customer_service_times.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(result)
    validation={'customer_count':len(result),'service_time_minutes_per_customer':s,'all_s_i_equal_baseline':all(float(x['s_i'])==s for x in result),'sensitivity_analysis_executed':False,'travel_waiting_charging_separate':True}
    (out/'r08_service_time_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'schema_version':'evrp-r08-service-time-v1','run_id':a.run_id,'created_at':datetime.now(timezone.utc).isoformat(),'fixture':{'n':len(result),'is_production_problem_size':False},'baseline':{'s_i':s,'unit':'minutes/customer','classification':'ASSUMED (external empirical reference)','sensitivity_candidate_range':'4-15 minutes/customer; not executed'},'source':{'title':'Urban context and delivery performance: Modelling service time for cargo bikes and vans across diverse urban environments','authors':'Schrader et al.','year':2024,'url':'https://arxiv.org/abs/2409.06730','scope':'urban parcel delivery service time reference; not Ota-ku observed data'},'transformation':'fixed 2.5 minutes/customer applied to every R07 customer; service time excludes travel/waiting/charging','inputs':{'r07_time_windows':{'path':str(r07.relative_to(ROOT)),'sha256':sha256(r07)},'r07_manifest':{'path':str(r07m.relative_to(ROOT)),'sha256':sha256(r07m)}},'config':{'path':str(cp.relative_to(ROOT)),'sha256':sha256(cp)},'code':{'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha256(Path(__file__))},'outputs':{}}
    for p in sorted(out.iterdir()):
        if p.name!='r08_service_time_manifest.json': manifest['outputs'][p.name]={'path':str(p.relative_to(ROOT)),'sha256':sha256(p)}
    (out/'r08_service_time_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'run_id':a.run_id,'customer_count':len(result),'s_i':s,'output':str(out.relative_to(ROOT))},ensure_ascii=False))
if __name__=='__main__': main()
