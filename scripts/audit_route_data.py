"""Independent audit of EVERY saved Route/ancestor record against OD arrays.

No OD generator function is used. Hashes, pair indexing, same-object D/time,
snaps, node-path evidence, and inheritance identity are checked independently.
"""
import argparse
import gzip
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import time
import numpy as np
from kmd_toc.common.models import load_problem

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112_route_v2'))
PROBLEMS={};HASHES={};CONTEXTS={};DIRECTORIES={};SNAPS={}

def audit_block(job):
    case,entry=job;p=PROBLEMS[case];path=ROOT/'roads'/('route_'+case)/'blocks'/f"{entry['i']}_{entry['j']}.json.gz";payload=path.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=entry['sha256']:raise ValueError('RAW_BLOCK_HASH:'+str(path))
    raw=json.loads(gzip.decompress(payload));context=CONTEXTS[case]
    if raw['context']!=context['hash'] or (raw['i'],raw['j'])!=(entry['i'],entry['j']):raise ValueError('RAW_BLOCK_CONTEXT')
    expected=[(i,j) for i in range(entry['i'],min(len(p.od.ids),entry['i']+context['block_size'])) for j in range(entry['j'],min(len(p.od.ids),entry['j']+context['block_size']))]
    if len(raw['records'])!=len(expected):raise ValueError('RAW_PAIR_COUNT')
    direct=references=0
    for record,(i,j) in zip(raw['records'],expected):
        if (record['i'],record['j'])!=(i,j):raise ValueError('RAW_PAIR_ORDER')
        if 'ancestor' in record:
            a=record['ancestor'];source_case=DIRECTORIES[a['directory']];source=PROBLEMS[source_case];x,y=a['i'],a['j']
            if a['OD_hash']!=HASHES[source_case] or source.od.ids[x]!=p.od.ids[i] or source.od.ids[y]!=p.od.ids[j]:raise ValueError('ANCESTOR_ID_HASH')
            if a['block']!=f'{x//25*25}_{y//25*25}.json.gz':raise ValueError('ANCESTOR_BLOCK_INDEX')
            distance,duration=float(source.od.distance_m[x,y]),float(source.od.duration_s[x,y]);references+=1
        else:
            response=record['response']
            if response['code']!='Ok' or len(response['waypoints'])!=2 or len(response['routes'])!=1:raise ValueError('RAW_ROUTE_RESPONSE')
            route=response['routes'][0];distance,duration=route['distance'],route['duration']
            if len(route['legs'])!=1 or len(route['legs'][0]['annotation']['nodes'])<1:raise ValueError('RAW_PATH_NODES')
            for waypoint,k in zip(response['waypoints'],[i,j]):
                expected_lon,expected_lat=SNAPS[case][k]
                if max(abs(waypoint['location'][0]-expected_lon),abs(waypoint['location'][1]-expected_lat))>1e-6:raise ValueError('RAW_SNAP_IDENTITY')
            direct+=1
        if distance!=record['distance'] or duration!=record['duration'] or distance!=float(p.od.distance_m[i,j]) or duration!=float(p.od.duration_s[i,j]) or not p.od.reachable[i,j]:raise ValueError('RAW_VS_MATRIX_SCALAR')
    return len(expected),direct,references

def ready():
    try:return {'S1','S2','S3'}<={r['id'] for r in json.loads((ROOT/'roads/COMMON_BUNDLES.json').read_text())}
    except (OSError,ValueError):return False

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wait',action='store_true');parser.add_argument('--workers',type=int,default=8);a=parser.parse_args();waiting=time.perf_counter()
    while a.wait and not ready():
        if time.perf_counter()-waiting>7200:raise TimeoutError('ROUTE_INPUTS_NOT_COMPLETE')
        time.sleep(2)
    begin=time.perf_counter();jobs=[]
    for case in ['S1','S2','S3']:
        p=load_problem(ROOT/'roads/inputs'/case);PROBLEMS[case]=p;HASHES[case]=p.od.fingerprint;CONTEXTS[case]=json.loads((ROOT/'roads'/('route_'+case)/'CONTEXT.json').read_text());DIRECTORIES[str(ROOT/'roads'/('route_'+case))]=case
        SNAPS[case]=[(p.depot.snap.longitude,p.depot.snap.latitude)]+[(s.snap.longitude,s.snap.latitude) for s in p.stops]
        for e in json.loads((ROOT/'roads'/('route_'+case)/'BLOCK_MANIFEST.json').read_text()):jobs.append((case,e))
    overlaps=[]
    for small,large in [('S1','S2'),('S2','S3'),('S1','S3')]:
        p,q=PROBLEMS[small],PROBLEMS[large];pos={sid:i for i,sid in enumerate(q.od.ids)};ix=[pos[sid] for sid in p.od.ids]
        for key in ['distance_m','duration_s','reachable']:
            if not np.array_equal(getattr(p.od,key),getattr(q.od,key)[np.ix_(ix,ix)]):raise ValueError('OVERLAP_MATRIX_CHANGED')
        overlaps.append({'subset':small,'superset':large,'all_three_arrays_equal':True,'pairs':len(ix)**2})
    count=direct=references=blocks=0
    with multiprocessing.get_context('fork').Pool(a.workers) as pool:
        for n,d,r in pool.imap_unordered(audit_block,jobs,chunksize=8):
            count+=n;direct+=d;references+=r;blocks+=1
            if blocks%1000==0:print('independent raw Route audit blocks',blocks,'/',len(jobs),flush=True)
    result={'passed':True,'blocks':blocks,'pair_records_audited':count,'direct_annotated_HTTP_paths':direct,'ancestor_records_audited':references,'overlap_checks':overlaps,'OD_hashes':HASHES,'elapsed_s':time.perf_counter()-begin,'workers':a.workers,
            'scope':'all S1/S2/S3 retained records; scalar values from same Route object or recursively audited ancestor; separate from generator'}
    (ROOT/'ALL_ROUTE_DATA_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
