"""Artificial directed network witnesses. Never substitute these for frozen OD."""
import math
import numpy as np
from kmd_toc.common.config import load_conditions, ready_s, CONFIG_SHA256
from kmd_toc.common.models import Snap, Stop, Depot, Vehicle, Berth, Experiment, Problem
from kmd_toc.common.od import OD


def artificial_problem(n=6, vehicles=2, berths=1):
    if not all(type(x) is int and x>0 for x in [n,vehicles,berths]):raise ValueError('FIXTURE_COUNTS')
    size=n+1; width=math.ceil(math.sqrt(size)); ids=('DEPOT',*(f'c{i:04}' for i in range(1,size)))
    duration=np.full((size,size),np.inf); distance=np.full((size,size),np.inf)
    np.fill_diagonal(duration,0);np.fill_diagonal(distance,0)
    for i in range(size):
        neighbors = {i-1,i+1,i-width,i+width}
        for j in sorted(neighbors):
            if 0<=j<size:
                duration[i,j]=20+(i*7+j*3)%11
                distance[i,j]=90+(i*13+j*7)%29
    # Floyd-Warshall on duration; retain distance on precisely the selected path.
    for k in range(size):
        candidate=duration[:,k,None]+duration[None,k,:]
        mask=candidate<duration
        candidate_d=distance[:,k,None]+distance[None,k,:]
        duration[mask]=candidate[mask];distance[mask]=candidate_d[mask]
    metadata={'kind':'synthetic','road_version':'artificial-directed-fastest-path-v1',
              'graph_id':f'artificial-grid-{n}-v1','units':{'distance':'m','duration':'s'},
              'warning':'test edge weights; not real roads or real-demand distance estimates'}
    od=OD(ids,distance,duration,np.ones((size,size),dtype='bool'),metadata)
    def location(i):return 139.7+(i%width)*0.0001,35.58+(i//width)*0.0001
    def snap(i):
        x,y=location(i);return Snap(x,y,0,'artificial',(i,),metadata['graph_id'],True,'artificial network witness')
    stops=tuple(Stop(ids[i],*location(i),1,snap(i),{'kind':'synthetic_fixture','source':'baseline_a/fixtures.py',
                      'generation':'directed_graph_fastest_path_v1','sha256':'a'*64}) for i in range(1,size))
    c=load_conditions();o=c['operations']
    return Problem(stops,tuple(Vehicle(f'v{i}',60,2,ready_s(i,vehicles),72000) for i in range(vehicles)),
        Depot('DEPOT',*location(0),snap(0),True,'artificial entrance only'),
        tuple(Berth(f'b{i}','DEPOT',28800,72000,1800,0) for i in range(berths)),od,
        Experiment(f'ART_N{n}',c['conditions_version'],CONFIG_SHA256,None,{'od':od.fingerprint},
                   {'fixture':True},{},'synthetic_validation')).validate()
