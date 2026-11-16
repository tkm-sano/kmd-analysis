"""Authoritative same-path Route OD, retaining annotated paths for EVERY pair.

Table annotations are excluded after a cross-service distance mismatch. All
requests are loopback, no speed/distance estimation. S1 is built first and its
hash-bound paths are referenced when expanding S2/S3. Raw Table results remain.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import replace
from datetime import datetime,timezone
import gzip
import http.client
import json
import math
from pathlib import Path
import time
from urllib.parse import urlencode
import numpy as np
from kmd_toc.common.config import digest_file,fingerprint
from kmd_toc.common.models import load_problem,save_problem
from kmd_toc.common.od import OD
from .roads import dump


def build_route_matrix(p,meta,directory,ancestor=None,block_size=25,workers=4,port=5000,process_workers=0):
    root=Path(directory);root.mkdir(parents=True,exist_ok=True);cache=root/'blocks';cache.mkdir(exist_ok=True)
    points=[(p.depot.longitude,p.depot.latitude,p.depot.snap)]+[(s.longitude,s.latitude,s.snap) for s in p.stops]
    n=len(points);context=fingerprint({'ids':p.od.ids,'points':[(x,y,s.hint) for x,y,s in points],'metadata':meta,'block_size':block_size,'ancestor':ancestor['hash'] if ancestor else None})
    cp=root/'CONTEXT.json'
    if cp.exists() and json.loads(cp.read_text())['hash']!=context:raise ValueError('ROUTE_OD_CONTEXT_CHANGED')
    dump(cp,{'hash':context,'points':n,'block_size':block_size,'service':'Route with annotated nodes; no Table distances'})
    arrays=[]
    for name,dtype in [('distance_m','float64'),('duration_s','float64'),('reachable','bool')]:
        f=root/(name+'.npy');arrays.append(np.lib.format.open_memmap(f,mode='r+' if f.exists() else 'w+',shape=(n,n),dtype=dtype))
    if (root/'CHECKPOINT.json').exists():
        previous=json.loads((root/'CHECKPOINT.json').read_text())
        if previous.get('status')=='COMPLETE':
            entries=json.loads((root/'BLOCK_MANIFEST.json').read_text())
            for entry in entries:
                f=cache/f"{entry['i']}_{entry['j']}.json.gz"
                if digest_file(f)!=entry['sha256']:raise ValueError('ROUTE_OD_CACHE_HASH')
            od=OD(p.od.ids,*arrays,meta);od.audit()
            if od.fingerprint!=previous['OD_hash']:raise ValueError('ROUTE_OD_COMPLETE_ARRAY_HASH')
            print(p.experiment.scenario_id,'COMPLETE Route OD reused after all block/array hash checks',flush=True)
            return od
    prior_index={sid:i for i,sid in enumerate(ancestor['od'].ids)} if ancestor else {};start=time.perf_counter();entries=[]
    dump(root/'CHECKPOINT.json',{'status':'INCOMPLETE','context':context,'completed':0,'total':math.ceil(n/block_size)**2})
    def one(job):
        i,j=job;src=range(i,min(n,i+block_size));dst=range(j,min(n,j+block_size));file=cache/f'{i}_{j}.json.gz';side=file.with_name(file.name+'.sha256')
        if file.exists():
            if not side.exists() or digest_file(file)!=side.read_text().strip():raise ValueError('ROUTE_OD_CACHE_HASH')
            raw=json.loads(gzip.decompress(file.read_bytes()));reused=True
        else:
            records=[];connection=http.client.HTTPConnection('127.0.0.1',port,timeout=60)
            for a in src:
                for b in dst:
                    sid,tid=p.od.ids[a],p.od.ids[b]
                    if sid in prior_index and tid in prior_index:
                        x,y=prior_index[sid],prior_index[tid];old=ancestor['od'];records.append({'i':a,'j':b,'distance':float(old.distance_m[x,y]),'duration':float(old.duration_s[x,y]),
                            'ancestor':{'directory':ancestor['directory'],'OD_hash':ancestor['hash'],'i':x,'j':y,'block':f'{x//block_size*block_size}_{y//block_size*block_size}.json.gz'}});continue
                    x,y=points[a],points[b];coords=f'{x[0]},{x[1]};{y[0]},{y[1]}'
                    query=urlencode({'hints':x[2].hint+';'+y[2].hint,'overview':'false','annotations':'nodes','continue_straight':'false'})
                    # Persistent OSRM HTTP has a measured 40ms response delay
                    # here. Explicit close removes it; benchmark is retained.
                    connection.request('GET','/route/v1/driving/'+coords+'?'+query,headers={'Connection':'close'})
                    response=connection.getresponse();payload=json.loads(response.read())
                    if response.status!=200 or payload.get('code')!='Ok' or len(payload.get('routes',[]))!=1:raise ValueError('ROUTE_OD_UNREACHABLE_OR_ERROR:'+sid+'->'+tid)
                    for waypoint,expected in zip(payload['waypoints'],[x[2],y[2]]):
                        loc=waypoint['location']
                        if max(abs(loc[0]-expected.longitude),abs(loc[1]-expected.latitude))>1e-6:raise ValueError('ROUTE_OD_SNAP_DRIFT')
                    route=payload['routes'][0]
                    if not math.isfinite(route['distance']) or not math.isfinite(route['duration']) or min(route['distance'],route['duration'])<0:raise ValueError('ROUTE_OD_BAD_VALUE')
                    if len(route['legs'])!=1 or 'nodes' not in route['legs'][0].get('annotation',{}):raise ValueError('ROUTE_OD_NO_PATH_EVIDENCE')
                    records.append({'i':a,'j':b,'distance':route['distance'],'duration':route['duration'],'response':payload})
            connection.close();raw={'context':context,'i':i,'j':j,'records':records};temporary=file.with_suffix('.partial');temporary.write_bytes(gzip.compress(json.dumps(raw,separators=(',',':')).encode(),compresslevel=1,mtime=0));temporary.replace(file);side.write_text(digest_file(file)+'\n');reused=False
        if raw['context']!=context or raw['i']!=i or raw['j']!=j or len(raw['records'])!=len(src)*len(dst):raise ValueError('ROUTE_OD_CACHE_CONTENT')
        return i,j,raw,{'i':i,'j':j,'sha256':side.read_text().strip(),'reused':reused}
    jobs=[(i,j) for i in range(0,n,block_size) for j in range(0,n,block_size)]
    def consume(i,j,distances,durations,entry):
        shape=(min(block_size,n-i),min(block_size,n-j))
        arrays[0][i:i+shape[0],j:j+shape[1]]=np.asarray(distances).reshape(shape)
        arrays[1][i:i+shape[0],j:j+shape[1]]=np.asarray(durations).reshape(shape)
        arrays[2][i:i+shape[0],j:j+shape[1]]=True
        entries.append(entry)
        if len(entries)%25==0:
            for a in arrays:a.flush()
            dump(root/'CHECKPOINT.json',{'status':'INCOMPLETE','context':context,'completed':len(entries),'total':len(jobs),'elapsed_s':time.perf_counter()-start})
            print(p.experiment.scenario_id,'Route blocks',len(entries),'/',len(jobs),flush=True)
    if process_workers:
        # Linux fork shares read-only input/mmap pages. Return only two small
        # scalar arrays; annotated path evidence stays in each worker's cache.
        import multiprocessing
        import queue
        ctx=multiprocessing.get_context('fork');tasks=ctx.Queue();results=ctx.Queue()
        def work():
            while True:
                job=tasks.get()
                if job is None:return
                try:
                    i,j,raw,entry=one(job)
                    results.put((True,i,j,[r['distance'] for r in raw['records']],[r['duration'] for r in raw['records']],entry))
                except Exception as error:
                    results.put((False,type(error).__name__,str(error)));return
        children=[ctx.Process(target=work) for _ in range(process_workers)]
        for child in children:child.start()
        for job in jobs:tasks.put(job)
        for child in children:tasks.put(None)
        try:
            for _ in jobs:
                try:result=results.get(timeout=90)
                except queue.Empty:raise RuntimeError('ROUTE_OD_WORKER_STALLED')
                if not result[0]:raise ValueError('ROUTE_OD_WORKER:'+str(result[1:]))
                consume(*result[1:])
        finally:
            for child in children:
                child.join(timeout=2)
                if child.is_alive():child.terminate();child.join()
            tasks.cancel_join_thread();results.cancel_join_thread();tasks.close();results.close()
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending={pool.submit(one,job) for job in jobs}
            for task in as_completed(pending):
                i,j,raw,entry=task.result();pending.remove(task)
                consume(i,j,[r['distance'] for r in raw['records']],[r['duration'] for r in raw['records']],entry)
    for a in arrays:a.flush()
    od=OD(p.od.ids,*arrays,meta);audit=od.audit();h=od.fingerprint
    dump(root/'BLOCK_MANIFEST.json',sorted(entries,key=lambda e:(e['i'],e['j'])))
    dump(root/'CHECKPOINT.json',{'status':'COMPLETE','context':context,'completed':len(entries),'total':len(jobs),'elapsed_s':time.perf_counter()-start,'audit':audit,'OD_hash':h,'service':'Route','ancestor_OD_hash':ancestor['hash'] if ancestor else None})
    return od


def build_pipeline(old_root,new_root,scenarios=('S1','S2','S3'),process_workers=0,port=5000):
    old,new=Path(old_root),Path(new_root);roads=new/'roads';roads.mkdir(parents=True,exist_ok=True)
    meta=json.loads((old/'roads/ROAD_METADATA.json').read_text())
    meta.update(generated_at=datetime.now(timezone.utc).isoformat(),matrix_service='Route per ordered pair with annotated node path; distance and duration from same Route object',
                table_distances_used=False,service_consistency_basis='full-tour Route vs pair Route; Table distance mismatch rejected',
                parent_table_result=str(old/'FULL_TOUR_ROUTE_AUDIT/SUMMARY.json'))
    if (roads/'ROAD_METADATA.json').exists():meta=json.loads((roads/'ROAD_METADATA.json').read_text())
    else:dump(roads/'ROAD_METADATA.json',meta)
    ancestor=None;bundles=[]
    for scenario in scenarios:
        p=load_problem(old/'roads/inputs'/scenario);od=build_route_matrix(p,meta,roads/('route_'+scenario),ancestor=ancestor,process_workers=process_workers,port=port)
        e=replace(p.experiment,data_hashes={**p.experiment.data_hashes,'od':od.fingerprint},environment={**p.experiment.environment,'OD_service':'Route per pair; annotated nodes retained'})
        q=replace(p,od=od,experiment=e).validate();dest=roads/'inputs'/scenario
        if not dest.exists():save_problem(q,dest)
        bundles.append({'id':scenario,'path':str(dest),'N':len(q.stops),'V':len(q.vehicles),'B':len(q.berths),'input_hash':q.fingerprint,'OD_hash':od.fingerprint,'kind':e.kind})
        if scenario=='S1':
            for case in ['ROAD_N6','ROAD_N20','ROAD_N120','ROAD_N240']:
                small=load_problem(old/'roads/inputs'/case);ix=[p.od.ids.index(s) for s in small.od.ids];sub=OD(small.od.ids,*(np.array(a[np.ix_(ix,ix)]) for a in [od.distance_m,od.duration_s,od.reachable]),meta)
                se=replace(small.experiment,data_hashes={**small.experiment.data_hashes,'od':sub.fingerprint},environment={**small.experiment.environment,'OD_service':'Route per pair; annotated nodes retained'})
                sq=replace(small,od=sub,experiment=se).validate();d=roads/'inputs'/case
                if not d.exists():save_problem(sq,d)
                bundles.append({'id':case,'path':str(d),'N':len(sq.stops),'V':len(sq.vehicles),'B':len(sq.berths),'input_hash':sq.fingerprint,'OD_hash':sub.fingerprint,'kind':se.kind})
        dump(roads/'COMMON_BUNDLES.json',bundles);print('VERIFIED ROUTE INPUT SAVED',scenario,flush=True)
        ancestor={'od':od,'hash':od.fingerprint,'directory':str(roads/('route_'+scenario))}
    return bundles
