#!/usr/bin/env python3
"""Read-only real-data audit and synthetic validation; no optimization experiments."""
import argparse
from collections import Counter
import csv
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.common.config import load_conditions, digest_file, CONFIG_SHA256
from kmd_toc.common.models import save_problem, load_problem, save_plan
from kmd_toc.common.runtime import run_measured
from kmd_toc.frozen_demand import load_frozen_demand


def write(p,value):
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def demand_audit():
    config=json.loads((ROOT/'configs/toc_delivery/frozen_demand_v1.json').read_text())
    bundle=ROOT/config['bundle_relative_path']
    historical=json.loads((ROOT/'review_outputs/toc_demand_freeze_20261110/FILE_HASHES.json').read_text())
    files=[]
    for p in sorted(bundle.iterdir()):
        rel=str(p.relative_to(ROOT));actual=digest_file(p)
        files.append(dict(path=rel,bytes=p.stat().st_size,sha256=actual,
                          matches_freeze=actual==historical[rel]['sha256']))
    if len(files)!=8 or not all(r['matches_freeze'] for r in files):raise ValueError('FROZEN_HASH_MISMATCH')
    audit_path=ROOT/'review_outputs/toc_stops_full_audit_20261108/run_20261108T091121Z_attempt02/ALL_STOPS_AUDIT.csv'
    with audit_path.open(newline='') as s:
        old={row['stop_id']:row for row in csv.DictReader(s)}
    results,sets={},{}
    for sid,expected in [('S1',(1000,10,2)),('S2',(2000,20,4)),('S3',(4000,40,8))]:
        consumers={m:load_frozen_demand(sid,method_id=m) for m in 'ABCD'}
        frozen=consumers['B']
        with (bundle/(sid+'.csv')).open(newline='') as s:rows=list(csv.DictReader(s))
        ids=[r['stop_id'] for r in rows]
        if len(ids)!=expected[0] or len(set(ids))!=len(ids) or any(not i for i in ids):raise ValueError('DEMAND_IDS')
        if any(r['parcel_count']!='1' for r in rows):raise ValueError('DEMAND_QUANTITY')
        for r in rows:
            lon,lat=Decimal(r['longitude']),Decimal(r['latitude'])
            if not(lon.is_finite() and lat.is_finite() and -180<=lon<=180 and -90<=lat<=90):raise ValueError('DEMAND_COORDS')
        sets[sid]=set(ids)
        status={key:dict(Counter(old[i][key] for i in ids)) for key in
                ('overall_status','road_mapping_status','road_reachability_status','real_access_status','new_study_road_adoption')}
        results[sid]=dict(stops=len(rows),vehicles=frozen.vehicles,berths=frozen.berths,
            demand_units=sum(int(r['parcel_count']) for r in rows),csv_sha256=frozen.csv_sha256,
            source_audit_status=status,all_consumers_same_hash=len({d.csv_sha256 for d in consumers.values()})==1,
            bbox=dict(west=min(float(r['longitude']) for r in rows),east=max(float(r['longitude']) for r in rows),
                      south=min(float(r['latitude']) for r in rows),north=max(float(r['latitude']) for r in rows)))
    return dict(files=files,scenarios=results,strict_nested=sets['S1']<sets['S2']<sets['S3'],
                source_audit_sha256=digest_file(audit_path),runtime_regeneration=False)


def road_audit():
    quality_path=ROOT/'03_data/processed/traffic_simulation/validation/osm_ota_ward_20260716_quality_summary.json'
    q=json.loads(quality_path.read_text())
    files=[]
    for key in ('raw','extract'):
        p=ROOT/q[key+'_path']
        actual=digest_file(p) if p.exists() else None
        files.append(dict(path=str(p.relative_to(ROOT)),present=p.exists(),sha256=actual,
                          expected_sha256=q[key+'_sha256'],matches=actual==q[key+'_sha256'],
                          bytes=p.stat().st_size if p.exists() else None))
    prior=json.loads((ROOT/'review_outputs/toc_demand_map_depot_20261110/BEFORE.json').read_text())['depot_sources']
    sources=[]
    for name,r in prior.items():
        p=Path(r['path'])
        sources.append(dict(name=name,path=str(p),sha256=digest_file(p) if p.exists() else None,
                            matches=p.exists() and digest_file(p)==r['sha256']))
    return dict(files=files,source_url=q['source_url'],source_id=q['source_id'],
                snapshot_date=q['snapshot_date'],osm_timestamp=q['raw_data_timestamp'],
                recorded_local_acquisition_or_processing_at=q['generated_at'],
                download_time_independently_confirmed=False,source_registry_record=quality_path.relative_to(ROOT).as_posix(),
                depot=dict(depot_id='DEP_006',longitude=139.745306,latitude=35.586971,
                           kind='historical_proxy',vehicle_entrance_verified=False,sources=sources),
                osrm_graph_found=False,research_od_available=False,public_osrm_requests=0,
                notes=['SUMO mappings do not certify OSRM snaps',
                       'Exact download timestamp absent; generated_at is processing timestamp',
                       'Local OSRM generation not attempted before entrance and snap review'])


def preflight():
    c=load_conditions();o=c['operations'];result={}
    for sid,r in c['scenarios'].items():
        n,v,b=r['stops'],r['vehicles'],r['berths']
        trips=math.ceil(n/o['capacity_per_trip']);pairs=(n+1)**2
        second=max(0,trips-v)
        workload=n*o['service_s']+trips*o['loading_s']+second*o['preparation_s']
        result[sid]=dict(stops=n,vehicles=v,berths=b,max_trips=2*v,total_capacity=120*v,
            spare_capacity=120*v-n,capacity_utilization=n/(120*v),minimum_trips=trips,
            minimum_second_trips=second,minimum_used_vehicles=math.ceil(n/120),
            loading_aggregate_min=trips*30,berth_fluid_lower_bound_min=trips*30/b,
            berth_nonpreemptive_lower_bound_min=math.ceil(trips/b)*30,
            total_service_min=2*n,service_per_vehicle_lower_bound_min=2*n/v,
            vehicle_work_excluding_travel_lower_bound_min=workload/v/60,
            total_minimum_vehicle_work_s=workload,od_points=n+1,od_pairs=pairs,
            od_numeric_bytes=pairs*17,od_numeric_MiB=pairs*17/1024**2,
            od_blocks_100=math.ceil((n+1)/100)**2,
            od_time_estimate_s=None,osrm_build_peak_memory_bytes=None,
            status='HOLD',capacity_necessary_condition_passes=120*v>=n,
            feasibility_proven=False)
    return result


def document_inventory():
    paths=[ROOT/'README.md',ROOT/'research_plan_toc_three_objectives_faceted_20261108.docx',
           ROOT/'docs/research/TOC_DELIVERY_SPEC.md',ROOT/'docs/audits/toc_scope_20261108/REPORT.md',
           ROOT/'docs/research/delivery_planning_desktop_20261111_1230/report.md']
    paths+=sorted((ROOT/'docs/research/toc_delivery_d').glob('*.md'))
    records=[]
    for p in paths:
        data=p.read_bytes()
        records.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                            first_lines=data.decode(errors='replace').splitlines()[:4] if p.suffix=='.md' else []))
    return records


def witnesses(out):
    # New validation fixtures only; no existing A–D generator or optimizer.
    sys.path.insert(0,str(ROOT/'tests/toc_common'))
    from conftest import fixture_problem, fixture_plan
    results=[]
    for n in (4,5,6,20):
        problem=fixture_problem(n)
        p=out/f'N{n}';p.mkdir()
        save_problem(problem,p/'input')
        assignments=None if n==5 else [('v0',tuple(s.stop_id for s in problem.stops),90,'b0')]
        def construct(actual,mark):
            mark('specified_witness_construction_start')
            plan=fixture_plan(actual,assignments)
            return replace(plan,method_settings={'validation_only':True,'optimizer_executed':False})
        result=run_measured(lambda:load_problem(p/'input'),construct)
        write(p/'run_result.json',result)
        # Independent Decimal arc incidence evaluation, no validator imports.
        plan=result['plan'];distance=Decimal(0);waiting=Decimal(0)
        arcs=Counter()
        for trip in plan['trips']:
            ids=[trip['origin_id']]+[v['stop_id'] for v in trip['visits']]+[trip['destination_id']]
            arcs.update(zip(ids,ids[1:]))
            if trip['trip_no']==1:
                ready=next(v.first_ready_s for v in problem.vehicles if v.vehicle_id==trip['vehicle_id'])
            else:
                ready=next(t['return_s'] for t in plan['trips'] if t['vehicle_id']==trip['vehicle_id'] and t['trip_no']==1)
            waiting+=Decimal(trip['load_start_s']-ready)/60
        for (i,j),count in arcs.items():
            distance+=Decimal(str(problem.od.distance_m[problem.od.ids.index(i),problem.od.ids.index(j)]))*count/1000
        match=result['D_km']==float(distance) and result['W_min']==float(waiting)
        if not match or result['status']!='FEASIBLE':raise ValueError('SYNTHETIC_WITNESS_FAILED')
        results.append(dict(N=n,D_km=result['D_km'],W_min=result['W_min'],T_s=result['T_s'],
                            independent_D_km=str(distance),independent_W_min=str(waiting),match=match,
                            input_hash=problem.fingerprint,validation_only=True))
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    write(args.output/'DEMAND_AUDIT.json',demand_audit())
    write(args.output/'ROAD_AUDIT.json',road_audit())
    write(args.output/'SCALE_PREFLIGHT.json',preflight())
    write(args.output/'DOCUMENT_INVENTORY.json',document_inventory())
    write(args.output/'SYNTHETIC_WITNESSES.json',witnesses(args.output))
    record=dict(created_at=datetime.now(timezone.utc).isoformat(),wall_s=time.perf_counter()-start,
                peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                python=sys.version,platform=platform.platform(),logical_cpu_count=os.cpu_count(),
                conditions_sha256=CONFIG_SHA256,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                S1_S2_S3_optimizer_runs=0,public_OSRM_requests=0,quantum_hardware_calls=0)
    write(args.output/'EXECUTION.json',record)
    print(json.dumps(record,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
