"""Local OSRM, map-based snapping review and hash-bound resumable OD blocks."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.request import urlopen
from urllib.parse import urlencode
import numpy as np
from kmd_toc.common.config import load_conditions, ready_s, CONFIG_SHA256, fingerprint, digest_file
from kmd_toc.common.od import OD, LocalOSRM, save_od
from kmd_toc.common.models import Snap, Stop, Vehicle, Depot, Berth, Experiment, Problem, save_problem
from kmd_toc.frozen_demand import load_frozen_demand


def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def get(url):
    with urlopen(url,timeout=120) as r:return json.load(r)


class FixedSnapOSRM(LocalOSRM):
    """OSRM hints are bound to the ORIGINAL query coordinate, not rounded snap.

    Send that coordinate with the reviewed candidate hint and still reject any
    resulting waypoint drift. Replacing query coordinates silently invalidates
    some hints, particularly for a deliberately selected second road candidate.
    """
    def __init__(self, originals, **kwargs):
        super().__init__(**kwargs);self.originals=originals

    def table(self, origins, destinations, snaps):
        ids=tuple(dict.fromkeys((*origins,*destinations)))
        # OSRM requires at least two coordinates even for the final 1x1
        # diagonal block. Repeat the same reviewed point; indexes stay zero.
        if len(ids)==1:ids=ids+ids
        coords=';'.join(f'{self.originals[i][0]},{self.originals[i][1]}' for i in ids)
        query=urlencode({'sources':';'.join(str(ids.index(i)) for i in origins),
                         'destinations':';'.join(str(ids.index(i)) for i in destinations),
                         'hints':';'.join(snaps[i].hint for i in ids),'annotations':'distance,duration'})
        raw=self.transport(f'{self.endpoint}/table/v1/driving/{coords}?{query}')
        if raw.get('code')!='Ok' or raw.get('fallback_speed_cells'):raise ValueError('FIXED_SNAP_TABLE_RESPONSE')
        for key,group in [('sources',origins),('destinations',destinations)]:
            if len(raw.get(key,[]))!=len(group):raise ValueError('FIXED_SNAP_WAYPOINT_COUNT')
            for w,sid in zip(raw[key],group):
                expected=snaps[sid];actual=w.get('location',[])
                if len(actual)!=2 or max(abs(actual[0]-expected.longitude),abs(actual[1]-expected.latitude))>1e-6:
                    raise ValueError('FIXED_SNAP_DRIFT:'+sid)
        d,t=np.array(raw.get('distances'),dtype='float64'),np.array(raw.get('durations'),dtype='float64')
        if d.shape!=(len(origins),len(destinations)) or t.shape!=d.shape or not np.array_equal(np.isnan(d),np.isnan(t)):raise ValueError('FIXED_SNAP_MATRIX_SHAPE')
        return d,t,np.isfinite(d)&np.isfinite(t),raw


def graph_metadata(graph_dir, rootfs, output):
    graph_dir,rootfs=Path(graph_dir),Path(rootfs);out=Path(output)
    path=out/'ROAD_METADATA.json'
    if path.exists():return json.loads(path.read_text())
    files={p.name:digest_file(p) for p in sorted(graph_dir.glob('kanto.osrm*')) if p.is_file()}
    raw=Path('03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf')
    meta={'kind':'osm_osrm','units':{'distance':'m','duration':'s'},
          'source_url':'https://download.geofabrik.de/asia/japan/kanto-260716.osm.pbf',
          'acquired_at':'2026-07-17 local retained file; exact original download log unavailable',
          'osm_timestamp':'2026-07-16T20:21:30Z','road_version':'geofabrik-kanto-20260716-osrm5.27.1-car-MLD',
          'graph_id':fingerprint(files),'osrm_version':'5.27.1','profile':'standard car.lua; static speed assumptions from pinned OSRM profile',
          'profile_sha256':digest_file(rootfs/'opt/car.lua'),'raw_sha256':digest_file(raw),
          'graph_artifacts':files,'build_commands':['osrm-extract -p car.lua -t 4 kanto.osm.pbf','osrm-partition -t 4 kanto.osrm','osrm-customize -t 4 kanto.osrm'],
          'generated_at':datetime.now(timezone.utc).isoformat(),'route_policy':'fastest_same_route','fallback_speed_allowed':False,
          'directed':True,'traffic_time_dependence':False,'crs':'EPSG:4326 longitude latitude; distances m and durations s',
          'source_date_basis':'PBF header generator=osmium/1.16.0; replication timestamp and base_url',
          'scope':'full Kanto PBF; not clipped to Ota ward','runtime_manifest':'sources/OSRM_RUNTIME_MANIFEST.json'}
    dump(path,meta);return meta


def nearest_all(points, output, endpoint='http://127.0.0.1:5000'):
    p=Path(output)/'nearest';p.mkdir(exist_ok=True)
    def one(item):
        sid,lon,lat=item;f=p/(sid+'.json')
        expanded=p/(sid+'.expanded.json')
        if expanded.exists():d=json.loads(expanded.read_text())
        elif f.exists():d=json.loads(f.read_text())
        else:
            d=get(f'{endpoint}/nearest/v1/driving/{lon},{lat}?number=5');dump(f,d)
        if d.get('code')!='Ok':raise ValueError('OSRM_NEAREST:'+sid)
        return sid,d
    result={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for k,(sid,d) in enumerate(pool.map(one,points)):
            result[sid]=d
            if (k+1)%500==0:print('nearest',k+1,flush=True)
    return result


def road_nodes_for_candidates(nearest, output):
    """Inspect source ways for candidate OSM node pairs; never infer road class by distance."""
    import osmium
    p=Path(output)/'SNAP_ROAD_WAYS.json'
    if p.exists():return json.loads(p.read_text())
    wanted={int(n) for r in nearest.values() for w in r['waypoints'] for n in w.get('nodes',[]) if n}
    class Ways(osmium.SimpleHandler):
        def __init__(self):super().__init__();self.items=[]
        def way(self,w):
            if not w.tags.get('highway'):return
            hit=[n.ref for n in w.nodes if n.ref in wanted]
            if hit:self.items.append({'way_id':w.id,'matched_nodes':hit,'tags':dict(w.tags)})
    h=Ways();h.apply_file('03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf')
    dump(p,h.items);return h.items


def review_snaps(points, nearest, ways, metadata, output):
    nodeways=defaultdict(list)
    for w in ways:
        for n in w['matched_nodes']:nodeways[n].append(w)
    exception_path=Path(output)/'SNAP_EXCEPTION_REVIEW.json'
    exceptions=set(json.loads(exception_path.read_text())['reviewed_way_ids']) if exception_path.exists() else set()
    cp=Path(output)/'CONNECTIVITY_REVIEW.json'
    connected=json.loads(cp.read_text())['allowed_hints'] if cp.exists() else {}
    chosen={};review=[];blocked=[]
    for sid,lon,lat in points:
        options=[]
        for candidate in nearest[sid]['waypoints']:
            ns=[n for n in candidate.get('nodes',[]) if n]
            matches={w['way_id']:w for w in nodeways.get(ns[0],[])} if ns else {}
            for n in ns[1:]:matches={i:w for i,w in matches.items() if any(k['way_id']==i for k in nodeways.get(n,[]))}
            allowed=[]
            for w in matches.values():
                t=w['tags']
                if ((t.get('highway') in ['motorway','motorway_link','trunk','trunk_link','footway','cycleway','path','steps','construction','proposed'] and w['way_id'] not in exceptions) or
                        t.get('access') in ['no','private'] or t.get('motor_vehicle') in ['no','private'] or
                        t.get('bridge')=='yes' or int(t.get('layer','0').replace('+','') or 0)>0):continue
                allowed.append(w)
            good=bool(allowed) and candidate['distance']<=100 and (sid not in connected or candidate['hint'] in connected[sid])
            options.append({'candidate':candidate,'matched_ways':list(matches.values()),'allowed_ways':allowed,'map_rules_pass':good})
        accepted=next((o for o in options if o['map_rules_pass']),None)
        if accepted is None:blocked.append(sid)
        else:chosen[sid]=accepted['candidate']
        review.append({'id':sid,'original':[lon,lat],'options':options,'selected':accepted['candidate'] if accepted else None,
                       'review_scope':'map/source-tags/topology/offset review; not field observation or individual access-right confirmation'})
    path=Path(output)/'SNAP_REVIEW.json';dump(path,{'policy':'reject inaccessible/grade-separated/expressway candidates; max 100m; actual source-way match required','records':review,'blocked':blocked})
    if blocked:raise ValueError('SNAP_REVIEW_HOLD:'+str(blocked[:20])+f'; total={len(blocked)}')
    evidence='sha256:'+digest_file(path)
    snaps={sid:Snap(w['location'][0],w['location'][1],w['distance'],w['hint'],tuple(w['nodes']),metadata['graph_id'],True,evidence) for sid,w in chosen.items()}
    return snaps


def resumable_od(ids, snaps, metadata, output, block_size=100, client=None, workers=4):
    """Cache raw blocks keyed by graph+IDs+hints; bad cache is a visible error."""
    p=Path(output);p.mkdir(parents=True,exist_ok=True);cache=p/'blocks';cache.mkdir(exist_ok=True)
    context=fingerprint({'ids':ids,'metadata':metadata,'snaps':{i:asdict(snaps[i]) for i in ids},'block_size':block_size})
    context_path=p/'CONTEXT.json'
    if context_path.exists() and json.loads(context_path.read_text())['hash']!=context:raise ValueError('OD_RESUME_CONTEXT_CHANGED')
    dump(context_path,{'hash':context,'block_size':block_size,'points':len(ids)})
    n=len(ids);arrays=[]
    for name,dtype in [('distance_m','float64'),('duration_s','float64'),('reachable','bool')]:
        path=p/(name+'.npy');a=np.lib.format.open_memmap(path,mode='r+' if path.exists() else 'w+',dtype=dtype,shape=(n,n));arrays.append(a)
    checkpoint=p/'CHECKPOINT.json';dump(checkpoint,{'status':'INCOMPLETE','context':context})
    jobs=[(i,j) for i in range(0,n,block_size) for j in range(0,n,block_size)]
    client=client or LocalOSRM();started=time.perf_counter();entries=[]
    def one(job):
        i,j=job;src,dst=ids[i:i+block_size],ids[j:j+block_size];path=cache/f'{i}_{j}.json.gz';side=cache/f'{i}_{j}.sha256'
        if path.exists():
            if not side.exists() or digest_file(path)!=side.read_text().strip():raise ValueError('OD_BLOCK_HASH:'+str(job))
            raw=json.loads(gzip.decompress(path.read_bytes()));d=np.array(raw['distances'],dtype='float64');t=np.array(raw['durations'],dtype='float64')
            if d.shape!=(len(src),len(dst)) or t.shape!=d.shape:raise ValueError('OD_CACHED_SHAPE')
            reused=True
        else:
            d,t,reachable,raw=client.table(src,dst,snaps)
            payload=gzip.compress(json.dumps(raw,separators=(',',':')).encode(),mtime=0);temp=path.with_suffix('.partial');temp.write_bytes(payload);temp.replace(path);side.write_text(digest_file(path)+'\n');reused=False
        if not np.array_equal(np.isnan(d),np.isnan(t)):raise ValueError('OD_BLOCK_MISSING_PAIR')
        return i,j,d,t,{'i':i,'j':j,'sha256':side.read_text().strip(),'reused':reused}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for k,(i,j,d,t,entry) in enumerate(pool.map(one,jobs)):
            arrays[0][i:i+d.shape[0],j:j+d.shape[1]]=d;arrays[1][i:i+d.shape[0],j:j+d.shape[1]]=t;arrays[2][i:i+d.shape[0],j:j+d.shape[1]]=np.isfinite(d)&np.isfinite(t)
            entries.append(entry)
            if (k+1)%50==0:
                for a in arrays:a.flush()
                dump(checkpoint,{'status':'INCOMPLETE','context':context,'completed':len(entries),'total':len(jobs),'elapsed_s':time.perf_counter()-started})
                print('OD blocks',len(entries),'/',len(jobs),flush=True)
    for a in arrays:a.flush()
    # MLD Table 5.27 can report small negative distance offsets. Requery both
    # measures with Route on the identical reviewed hints; retain raw before/
    # after evidence. Never clamp, estimate, or label a negative value valid.
    corrections=[]
    for i,j in np.argwhere((arrays[0]<0)|(arrays[1]<0)):
        a,b=ids[i],ids[j];coords=';'.join(','.join(map(str,client.originals[k])) for k in [a,b])
        raw=get(f'{client.endpoint}/route/v1/driving/{coords}?'+urlencode({'hints':snaps[a].hint+';'+snaps[b].hint,'overview':'false','annotations':'distance,duration,nodes'}))
        route=raw['routes'][0]
        if route['distance']<0 or route['duration']<0:raise ValueError('ROUTE_REQUERY_NEGATIVE')
        corrections.append({'i':int(i),'j':int(j),'before_distance_m':float(arrays[0][i,j]),'before_duration_s':float(arrays[1][i,j]),'response':raw})
        arrays[0][i,j]=route['distance'];arrays[1][i,j]=route['duration']
    dump(p/'ROUTE_REQUERY_CORRECTIONS.json',corrections)
    for a in arrays:a.flush()
    od=OD(tuple(ids),*arrays,metadata);audit=od.audit()
    dump(checkpoint,{'status':'COMPLETE','context':context,'completed':len(entries),'total':len(jobs),'elapsed_s':time.perf_counter()-started,'audit':audit,'reused_blocks':sum(r['reused'] for r in entries)})
    dump(p/'BLOCK_MANIFEST.json',entries)
    return od


def independent_route_check(od, snaps, output, endpoint='http://127.0.0.1:5000', originals=None):
    pairs=[(0,1),(1,0),(0,len(od.ids)-1),(len(od.ids)-1,0)]
    pairs.extend((1+i*max(1,(len(od.ids)-2)//8),min(len(od.ids)-1,2+i*max(1,(len(od.ids)-2)//8))) for i in range(8))
    results=[]
    for i,j in pairs:
        if i>=len(od.ids) or i==j:continue
        a,b=snaps[od.ids[i]],snaps[od.ids[j]]
        ca=originals[od.ids[i]] if originals else (a.longitude,a.latitude)
        cb=originals[od.ids[j]] if originals else (b.longitude,b.latitude)
        u=f'{endpoint}/route/v1/driving/{ca[0]},{ca[1]};{cb[0]},{cb[1]}?hints={a.hint};{b.hint}&overview=false&annotations=distance,duration,nodes'
        r=get(u);route=r['routes'][0];ok=abs(route['distance']-float(od.distance_m[i,j]))<=0.2 and abs(route['duration']-float(od.duration_s[i,j]))<=0.2
        results.append({'origin':od.ids[i],'destination':od.ids[j],'table_distance_m':float(od.distance_m[i,j]),'route_distance_m':route['distance'],'table_duration_s':float(od.duration_s[i,j]),'route_duration_s':route['duration'],'match':ok,'response':r})
    dump(Path(output)/'INDEPENDENT_ROUTE_CHECK.json',results)
    if not all(r['match'] for r in results):raise ValueError('OD_ROUTE_TABLE_MISMATCH')


def build_inputs(output, graph_dir='/tmp/kmd-osrm-graph', rootfs='/tmp/kmd-osrm527'):
    out=Path(output);out.mkdir(parents=True,exist_ok=True);meta=graph_metadata(graph_dir,rootfs,out)
    frozen=load_frozen_demand('S3',method_id='A');decision=json.loads(Path('output/toc_delivery/ad_pipeline_20261112/DEPOT_ENTRANCE_DECISION.json').read_text())
    points=[(decision['depot_id'],decision['longitude'],decision['latitude'])]+[(s.stop_id,float(s.longitude),float(s.latitude)) for s in frozen.stops]
    nearest=nearest_all(points,out);ways=road_nodes_for_candidates(nearest,out);snaps=review_snaps(points,nearest,ways,meta,out)
    ids=tuple(sid for sid,x,y in points)
    client=FixedSnapOSRM({sid:(x,y) for sid,x,y in points})
    od=resumable_od(ids,snaps,meta,out/'full_S3',client=client)
    independent_route_check(od,snaps,out,originals={sid:(x,y) for sid,x,y in points})
    entrance_evidence='sha256:'+digest_file(Path('output/toc_delivery/ad_pipeline_20261112/DEPOT_ENTRANCE_DECISION.json'))
    depot=Depot(decision['depot_id'],decision['longitude'],decision['latitude'],snaps[decision['depot_id']],True,entrance_evidence)
    o=load_conditions()['operations'];c=load_conditions();pos={sid:i for i,sid in enumerate(ids)};bundles=[]
    config=json.loads(Path('configs/toc_delivery/ad_pipeline_v1.json').read_text())
    cases=[{'id':sid,'frozen':load_frozen_demand(sid,method_id='A')} for sid in ['S1','S2','S3']]
    for row in config['road_validation_cases']:
        f=load_frozen_demand('S1',method_id='A');indices=np.linspace(0,len(f.stops)-1,row['N'],dtype=int);cases.append({**row,'frozen':f,'subset':indices})
    for case in cases:
        sid=case['id'];f=case['frozen'];is_subset='subset' in case
        selected=tuple(f.stops[i] for i in case['subset']) if is_subset else f.stops
        V,B=(case['V'],case['B']) if is_subset else (f.vehicles,f.berths)
        ix=[0]+[pos[s.stop_id] for s in selected];sub=OD((depot.depot_id,*(s.stop_id for s in selected)),*(np.asarray(a[np.ix_(ix,ix)]) for a in (od.distance_m,od.duration_s,od.reachable)),meta)
        stops=tuple(Stop(s.stop_id,float(s.longitude),float(s.latitude),s.parcel_count,snaps[s.stop_id],{'kind':'frozen_synthetic_demand','source':f.scenario_id+'.csv','generation':'frozen_v1_subset_validation_only' if is_subset else 'frozen_v1_unchanged','sha256':f.csv_sha256}) for s in selected)
        vehicles=tuple(Vehicle(f'v{i}',60,2,ready_s(i,V),72000) for i in range(V));berths=tuple(Berth(f'b{i}',depot.depot_id,28800,72000,1800,0) for i in range(B))
        e=Experiment(sid,c['conditions_version'],CONFIG_SHA256,20261112,{'od':sub.fingerprint,'demand_manifest':f.manifest_sha256,'demand_csv':f.csv_sha256},{'source':'real-road common pipeline','OD_precomputed':True},{},'road_validation' if is_subset else 'frozen_research')
        p=Problem(stops,vehicles,depot,berths,sub,e).validate();dest=out/'inputs'/sid
        if not dest.exists():save_problem(p,dest)
        bundles.append({'id':sid,'path':str(dest),'N':len(stops),'V':V,'B':B,'input_hash':p.fingerprint,'OD_hash':sub.fingerprint,'kind':e.kind})
        print('saved common input',sid,flush=True)
    dump(out/'COMMON_BUNDLES.json',bundles)
    return bundles
