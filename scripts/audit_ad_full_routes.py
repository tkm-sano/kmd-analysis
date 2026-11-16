"""Check concatenated real-road tours against local OSRM Route, independently.

Explicitly allow reorientation at service waypoints (continue_straight=false),
as assumed by the common pairwise OD model. No result or schedule is repaired.
"""
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
import os
import argparse
from pathlib import Path
from urllib.parse import urlencode
from kmd_toc.common.models import load_problem
from kmd_toc.pipeline.roads import get

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',default='S1');parser.add_argument('--all-feasible',action='store_true');args=parser.parse_args();case=args.case
    p=load_problem(ROOT/'roads/inputs'/case);out=ROOT/('FULL_TOUR_ROUTE_AUDIT' if case=='S1' else 'FULL_TOUR_ROUTE_AUDIT_'+case);out.mkdir(exist_ok=True);ids={s:i for i,s in enumerate(p.od.ids)}
    items={s.stop_id:(s.longitude,s.latitude,s.snap) for s in p.stops};items[p.depot.depot_id]=(p.depot.longitude,p.depot.latitude,p.depot.snap)
    jobs=[]
    conditions=sorted(p.parent.name for p in (ROOT/'experiments'/case).glob('*/result.json')) if args.all_feasible else ['A2_angle0','A3_angle0','B_primaryD_epsW_1','C_primaryD_epsW_1','D_primaryD_epsW_1']
    checked=[]
    for condition in conditions:
        result=json.loads((ROOT/'experiments'/case/condition/'result.json').read_text())
        if result['status']!='FEASIBLE':continue
        checked.append(condition)
        for trip in result['plan']['trips']:jobs.append((condition,trip))
    def one(job):
        condition,t=job;sequence=[p.depot.depot_id,*[v['stop_id'] for v in t['visits']],p.depot.depot_id]
        coords=';'.join(f'{items[s][0]},{items[s][1]}' for s in sequence)
        query=urlencode({'hints':';'.join(items[s][2].hint for s in sequence),'overview':'false','steps':'false','annotations':'nodes','continue_straight':'false'})
        raw=get('http://127.0.0.1:5000/route/v1/driving/'+coords+'?'+query)
        name=condition+'_'+t['vehicle_id']+'_'+str(t['trip_no'])+'.json.gz';(out/name).write_bytes(gzip.compress(json.dumps(raw).encode(),mtime=0))
        if raw.get('code')!='Ok':return {'condition':condition,'vehicle':t['vehicle_id'],'trip':t['trip_no'],'passed':False,'error':raw.get('code')}
        legs=raw['routes'][0]['legs'];errors=[];deltas=[]
        if len(legs)!=len(sequence)-1:errors.append('LEG_COUNT')
        for waypoint,s in zip(raw['waypoints'],sequence):
            if max(abs(waypoint['location'][0]-items[s][2].longitude),abs(waypoint['location'][1]-items[s][2].latitude))>1e-6:errors.append('SNAP_DRIFT')
        for k,(a,b) in enumerate(zip(sequence,sequence[1:])):
            dd=legs[k]['distance']-float(p.od.distance_m[ids[a],ids[b]]);dt=legs[k]['duration']-float(p.od.duration_s[ids[a],ids[b]])
            deltas.append({'from':a,'to':b,'delta_m':dd,'delta_s':dt})
            if abs(dd)>.25 or abs(dt)>.25:errors.append('CONCATENATED_PATH_DIFFERS_FROM_PAIRWISE_OD')
        return {'condition':condition,'vehicle':t['vehicle_id'],'trip':t['trip_no'],'passed':not errors,'errors':sorted(set(errors)),'legs':len(legs),'full_route_distance_m':raw['routes'][0]['distance'],
                'OD_route_distance_m':t['distance_m'],'max_distance_delta_m':max(abs(d['delta_m']) for d in deltas),'max_duration_delta_s':max(abs(d['delta_s']) for d in deltas),'deltas':deltas,'raw':name}
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(one,jobs))
    summary={'scope':case+': '+('all saved feasible plans' if args.all_feasible else 'five representative plans')+'; service-waypoint reorientation allowed, not field validation','conditions_checked':checked,'tours':len(results),'passed':sum(r['passed'] for r in results),'all_passed':all(r['passed'] for r in results),'records':results}
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print('full tour Route audit',summary['passed'],'/',summary['tours'],flush=True)

if __name__=='__main__':main()
