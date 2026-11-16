"""Read-only access to retained Route records and OSM node coordinates."""
import functools
import gzip
import hashlib
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE = REPO/'output/toc_delivery/ad_pipeline_20261112_route_v2'


def read_json(p): return json.loads(Path(p).read_text())


class SavedRoads:
    def __init__(self):
        self.node_ids = np.load(ROOT/'data/osm_node_ids.npy',mmap_mode='r')
        self.node_xy = np.load(ROOT/'data/osm_node_xy_e7.npy',mmap_mode='r')
        self.inputs = {s:read_json(SOURCE/'roads/inputs'/s/'input.json') for s in ['S1','S2','S3']}
        self.ods = {s:{k:np.load(SOURCE/'roads/inputs'/s/'od'/(k+'.npy'),mmap_mode='r') for k in ['distance_m','duration_s','reachable']} for s in self.inputs}
        self.manifests = {s:{(x['i'],x['j']):x for x in read_json(SOURCE/'roads'/('route_'+s)/'BLOCK_MANIFEST.json')} for s in self.inputs}
        self.used_blocks = {}

    def node_coordinates(self, ids):
        a=np.asarray(ids,dtype=np.int64); ix=np.searchsorted(self.node_ids,a)
        if (ix>=len(self.node_ids)).any() or (self.node_ids[ix]!=a).any(): raise ValueError('OSM_NODE_COORDINATE_MISSING')
        return self.node_xy[ix].astype(float)/1e7

    @functools.lru_cache(maxsize=4)
    def block(self, case, row, col):
        file=SOURCE/'roads'/('route_'+case)/'blocks'/f'{row}_{col}.json.gz'
        raw=file.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
        if digest!=self.manifests[case][row,col]['sha256']:raise ValueError('ROUTE_BLOCK_HASH')
        self.used_blocks[str(file.relative_to(REPO))]=digest
        return json.loads(gzip.decompress(raw))

    def pair_record(self, case, i, j):
        n=len(self.inputs[case]['stops'])+1
        if not (0<=i<n and 0<=j<n):raise ValueError('OD_INDEX_OUT_OF_RANGE')
        a,b=i//25*25,j//25*25
        rec=self.block(case,a,b)['records'][(i-a)*min(25,n-b)+j-b]
        if (rec['i'],rec['j'])!=(i,j):raise ValueError('OD_RECORD_INDEX')
        if 'ancestor' in rec:
            old=rec['ancestor']; parent=Path(old['directory']).name.replace('route_','')
            direct=self.pair_record(parent,old['i'],old['j'])
            if rec['distance']!=direct['distance'] or rec['duration']!=direct['duration']:raise ValueError('ANCESTOR_VALUES')
            return direct
        return rec

    def pair(self,case,i,j):
        rec=self.pair_record(case,i,j);route=rec['response']['routes'][0]
        if route['distance']!=float(self.ods[case]['distance_m'][i,j]) or route['duration']!=float(self.ods[case]['duration_s'][i,j]):
            raise ValueError('ROUTE_MATRIX_MISMATCH')
        response=rec['response'];coords,metric=self.shape(response['routes'][0]['legs'][0]['annotation']['nodes'],
                                                   response['waypoints'][0]['location'],response['waypoints'][1]['location'],route['distance'])
        pts=[self.inputs[case]['depot'],*self.inputs[case]['stops']]
        return {'case':case,'i':i,'j':j,'from_id':pts[i].get('stop_id',pts[i].get('depot_id')),
                'to_id':pts[j].get('stop_id',pts[j].get('depot_id')),'distance_m':route['distance'],
                'duration_s':route['duration'],'coordinates':coords,'geometry_check':metric,
                'node_ids':route['legs'][0]['annotation']['nodes'],'source':'saved Route response; no new routing request'}

    def shape(self, node_ids, start, end, saved_distance):
        nodes=self.node_coordinates(node_ids).tolist()
        # Clip only endpoint portions when a retained node segment contains the
        # phantom snap; retain all intermediate road vertices and their order.
        if saved_distance==0:
            if planar_distance(start,end)>.35:raise ValueError('ZERO_OD_WITH_DISTINCT_SNAPS')
            return [list(start)],{'length_m':0.,'delta_m':0.,'passed':True,'clipping':'stationary'}
        if not nodes:raise ValueError('EMPTY_ROAD_PATH')
        path=[list(start),*nodes,list(end)]
        if len(nodes)>1:
            candidates=[(point_segment(start,nodes[k],nodes[k+1])[0],k) for k in range(min(3,len(nodes)-1))]
            error,k=min(candidates)
            if error<=.35:path=[list(start),*nodes[k+1:],list(end)]
            # Destination projection is restricted to the final road segments.
            candidates=[(point_segment(end,path[k],path[k+1])[0],k) for k in range(max(0,len(path)-5),len(path)-2)]
            if candidates:
                error,k=min(candidates,key=lambda x:(x[0],-x[1]))
                if error<=.35:path=[*path[:k+1],list(end)]
        clean=[path[0]]
        for point in path[1:]:
            if point!=clean[-1]:clean.append(point)
        length=cheap_length(clean)
        delta=length-saved_distance
        return clean,{'length_m':length,'delta_m':delta,'passed':abs(delta)<=.35,
                      'clipping':'source/destination phantom snap on first/last retained road segments',
                      'metric':'OSRM5.27.1 bucketed WGS84 CheapRuler, coordinate precision 1e-6 degrees',
                      'tolerance_m':.35}


def planar_distance(a,b):
    return math.hypot((a[0]-b[0])*111320*math.cos(math.radians((a[1]+b[1])/2)),(a[1]-b[1])*111320)


def point_segment(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    f=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0.
    q=[a[0]+f*dx,a[1]+f*dy]
    return planar_distance(p,q),f


def cheap_length(coords):
    """Independent port of OSRM 5.27.1 coordinate_calculation + CheapRuler."""
    if len(coords)<2:return 0.
    c=np.floor(np.asarray(coords)*1e6+.5)/1e6
    # C++ fixed-latitude average is integer division before the 0.05deg bucket.
    avg=np.floor((np.floor(c[:-1,1]*1e6+.5)+np.floor(c[1:,1]*1e6+.5))/2)
    bucket=np.floor((np.abs(avg)-1)/50000)
    lat=np.radians((bucket+.5)*.05)
    e2=(1/298.257223563)*(2-1/298.257223563)
    w=np.sqrt(1-e2*np.sin(lat)**2)
    kx=np.pi/180*6378137*np.cos(lat)/w
    ky=np.pi/180*6378137*(1-e2)/(w**3)
    d=np.diff(c,axis=0)
    return float(np.sum(np.hypot(d[:,0]*kx,d[:,1]*ky)))
