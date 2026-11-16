"""Independent validation of display data, raw events, geometry and preservation.

Does not import the builder or the routing/optimization implementations.
"""
import csv
import gzip
import hashlib
import json
import math
import subprocess
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path
import numpy as np
import osmium

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];OLD=REPO/'output/toc_delivery/ad_pipeline_20261112_route_v2'
CHECKS=[]


def check(name,ok):CHECKS.append({'check':name,'passed':bool(ok)})


def main():
    start=time.perf_counter();data=json.loads((ROOT/'data/dashboard.json').read_text());nodes_to_check={}
    for case,n in [('S1',1000),('S2',2000),('S3',4000)]:
        inp=json.loads((OLD/'roads/inputs'/case/'input.json').read_text());display=data['scenarios'][case]
        check(case+':all delivery stops',len(display['points'])==n+1 and len(inp['stops'])==n)
        check(case+':depot exact coordinate', (display['points'][0]['lon'],display['points'][0]['lat'])==(inp['depot']['longitude'],inp['depot']['latitude']))
        frozen=REPO/'03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1'/f'{case}.csv'
        with frozen.open() as f:raw=list(csv.DictReader(f))
        check(case+':frozen point ID set',{x['id'] for x in display['points'][1:]}=={x['stop_id'] for x in raw})
        original={x['stop_id']:x for x in raw}
        check(case+':frozen demand coordinates and units',all(p['lon']==float(original[p['id']]['longitude']) and p['lat']==float(original[p['id']]['latitude']) and p['demand']==int(original[p['id']]['parcel_count']) for p in display['points'][1:]))
        for p,s in zip(display['points'],[inp['depot'],*inp['stops']]):
            check(case+':point/snap identity:'+p['id'],p['lon']==s['longitude'] and p['lat']==s['latitude'] and
                  p['snap_lon']==s['snap']['longitude'] and p['snap_lat']==s['snap']['latitude'] and p['node_ids']==s['snap']['node_ids'])
            for nid,c in zip(p['node_ids'],p['node_coordinates']):
                if nid==0:check(case+':unspecified node not invented:'+p['id'],c is None)
                else:nodes_to_check[nid]=c
        manifest=json.loads((OLD/'roads/inputs'/case/'od/manifest.json').read_text())
        check(case+':Route only road version',manifest['metadata']['table_distances_used'] is False and display['road_version']==manifest['metadata']['road_version'])
        check(case+':OD hash agreement',display['OD_hash']==inp['od_hash']==manifest['od_hash'])
        for fname,entry in manifest['files'].items():
            p=OLD/'roads/inputs'/case/'od'/fname
            expected=entry if isinstance(entry,str) else entry['sha256']
            check(case+':OD file hash:'+fname,hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==expected)
        for name in ['distance_m','duration_s','reachable']:
            a=np.load(OLD/'roads/inputs'/case/'od'/(name+'.npy'),mmap_mode='r')
            check(case+':matrix dimensions:'+name,a.shape==(n+1,n+1))
            if name!='reachable':check(case+':all finite/nonnegative:'+name,np.isfinite(a).all() and (a>=0).all() and not np.any(a.diagonal()))
            else:check(case+':reachability',a.all())
        q=data['stats'][case]
        check(case+':all distances histogram population',sum(q['distance_km']['hist']['counts'])==n*(n+1))
        check(case+':all time histogram population',sum(q['duration_min']['hist']['counts'])==n*(n+1))
        check(case+':asymmetry undirected pair count',sum(q['signed_asymmetry_km']['hist']['counts'])==n*(n+1)//2)
        check(case+':sample count explicit',len(q['scatter'])==2500)
        check(case+':no invented large-scale plan',display['has_delivery_plans']==(case=='S1'))
    d=np.load(OLD/'roads/inputs/S1/od/distance_m.npy',mmap_mode='r');t=np.load(OLD/'roads/inputs/S1/od/duration_s.npy',mmap_mode='r')
    inp=json.loads((OLD/'roads/inputs/S1/input.json').read_text());pos={p['id']:i for i,p in enumerate(data['scenarios']['S1']['points'])}
    raw_signatures={}
    for m in ['B','C','D']:
        saved=json.loads((OLD/'experiments/S1'/f'{m}_primaryD_epsW_1/result.json').read_text());display=data['plans'][m];plan=saved['plan'];seen=[];distance=Decimal(0);waiting=0;vehicle_count=Counter();berth_events={};previous={}
        check(m+':trip count identity',len(display['trips'])==len(plan['trips'])==17)
        check(m+':displayed T exact saved value',display['T_program_s']==saved['T_program_s'])
        check(m+':identical common input',plan['problem_hash']==display['input_hash']==inp['problem_hash'] and plan['od_hash']==display['OD_hash']==inp['od_hash'])
        raw_signatures[m]={}
        for raw,draw in zip(plan['trips'],display['trips']):
            label=f"{m}:{raw['vehicle_id']}:{raw['trip_no']}";ids=[v['stop_id'] for v in raw['visits']];seen+=ids;vehicle_count[raw['vehicle_id']]+=1
            check(label+':saved fields unchanged',all(draw[k]==v for k,v in raw.items()))
            indices=[0,*[pos[s] for s in ids],0];tripdist=sum((Decimal(str(float(d[a,b]))) for a,b in zip(indices,indices[1:])),Decimal(0));distance+=tripdist
            wait=raw['load_start_s']-raw['ready_s'];waiting+=wait
            check(label+':nonnegative wait',wait>=0)
            check(label+':plotted D and W independently',abs(draw['D_km_recomputed']-float(tripdist/1000))<1e-9 and draw['W_min_recomputed']==wait/60)
            check(label+':capacity',len(ids)<=60 and draw['load_units']==len(ids))
            ready=next(v['first_ready_s'] for v in inp['vehicles'] if v['vehicle_id']==raw['vehicle_id']) if raw['trip_no']==1 else previous[raw['vehicle_id']]
            check(label+':ready and second-trip linkage',ready==raw['ready_s'])
            check(label+':loading and departure',raw['load_start_s']>=28800 and raw['load_end_s']-raw['load_start_s']==1800 and raw['departure_s']>=raw['load_end_s'])
            clock=raw['departure_s']
            for k,(a,b) in enumerate(zip(indices,indices[1:])):
                clock+=math.ceil(float(t[a,b]))
                if k<len(raw['visits']):
                    v=raw['visits'][k];check(label+':arrival/service:'+str(k),v['arrival_s']==v['service_start_s']==clock and v['service_end_s']==clock+120);clock+=120
            check(label+':return/shift',clock==raw['return_s'] and clock<=72000);previous[raw['vehicle_id']]=clock
            berth_events.setdefault(raw['berth_id'],[]).extend([(raw['load_start_s'],1),(raw['load_end_s'],-1)])
            check(label+':validated geometry exists',draw['geometry_status']=='GO' and draw['geometry'] is not None)
            first=data['scenarios']['S1']['points'][0];check(label+':geometry depot endpoints',draw['geometry'][0]==draw['geometry'][-1]==[first['snap_lon'],first['snap_lat']])
            raw_signatures[m][tuple(ids)]={'vehicle':raw['vehicle_id'],'trip':raw['trip_no'],'berth':raw['berth_id'],'start':raw['load_start_s'],'return':raw['return_s']}
        check(m+':exact coverage',Counter(seen)==Counter(x['stop_id'] for x in inp['stops']))
        check(m+':physical vehicles/two trips',set(vehicle_count)<=set(v['vehicle_id'] for v in inp['vehicles']) and max(vehicle_count.values())<=2)
        for berth,events in berth_events.items():
            occupancy=0;valid=True
            for _,delta in sorted(events,key=lambda x:(x[0],x[1])):occupancy+=delta;valid=valid and 0<=occupancy<=1
            check(m+':independent half-open berth sweep:'+berth,valid and occupancy==0)
        check(m+':D before rounding',abs(float(distance/1000)-saved['D_km'])<1e-9 and display['D_km']==saved['D_km'])
        check(m+':W before rounding',waiting/60==saved['W_min']==display['W_min'])
    check('B/D route sets equal independent canonical key',raw_signatures['B'].keys()==raw_signatures['D'].keys())
    days=lambda m:Counter(tuple(tuple(v['stop_id'] for v in t['visits']) for t in sorted([t for t in data['plans'][m]['trips'] if t['vehicle_id']==f'v{i}'],key=lambda x:x['trip_no'])) for i in range(10))
    canonical_equal=days('B')==days('D')
    check('BD equivalence independent of Hungarian matching',canonical_equal==data['BD_comparison']['same_vehicle_days_up_to_relabelling'])
    check('BD physical plan inequality documented',not canonical_equal and not data['BD_comparison']['same_all_schedules_after_matching'])
    # Read the PBF again through the C++ ID filter, independently of the extraction handler.
    ids=sorted(nodes_to_check);sample=[ids[i] for i in np.linspace(0,len(ids)-1,120,dtype=int)];found={}
    pbf=REPO/'03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf'
    for n in osmium.FileProcessor(str(pbf),entities=osmium.osm.NODE).with_filter(osmium.filter.IdFilter(sample)):
        found[n.id]=[n.location.lon,n.location.lat]
    check('120 road-node coordinates independently reread from PBF',len(found)==120)
    for nid,c in found.items():check('raw PBF node coordinate:'+str(nid),np.allclose(c,nodes_to_check[nid],atol=1e-8,rtol=0))
    with (ROOT/'ARC_VALIDATION.csv').open() as f:arcs=list(csv.DictReader(f))
    check('all 3051 arcs have Route/OD and shape verification',len(arcs)==3051 and all(x['geometry_passed']=='True' and x['OD_passed']=='True' for x in arcs))
    for name in ['01_S1_S3_demand_roads','02_S1_BCD_road_routes','03_S1_BCD_berth_gantt','04_S1_BCD_metrics','05_all_OD_quality_distributions']:
        for ext in ['png','svg','pdf']:check('figure exists:'+name+ext,(ROOT/'figures'/(name+'.'+ext)).stat().st_size>10000)
    baseline=json.loads((ROOT/'PRESERVATION_BEFORE.json').read_text());changed=[]
    for rel,h in baseline['files'].items():
        p=REPO/rel;ok=p.exists() and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==h
        if not ok:changed.append(rel)
    check('88 protected existing files unchanged',len(baseline['files'])==88 and not changed)
    check('tracked user changes preserved',subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=REPO,text=True)==baseline['tracked_status'])
    summary={'checks':len(CHECKS),'passed':sum(x['passed'] for x in CHECKS),'failed':[x for x in CHECKS if not x['passed']],
             'details':CHECKS,'elapsed_s':time.perf_counter()-start,'changed_existing_files':changed,'independent_PBF_nodes':len(found),
             'scope':'raw JSON/Decimal/events/canonical vehicle-day signatures/C++-filtered PBF; no builder or optimizer import'}
    (ROOT/'INDEPENDENT_VALIDATION.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='details'},ensure_ascii=False,indent=2));assert not summary['failed']


if __name__=='__main__':main()
