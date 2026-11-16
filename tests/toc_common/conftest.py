"""Synthetic witnesses only; no geographic demand or optimizer calls."""
from dataclasses import replace
import math
import numpy as np
import pytest
from kmd_toc.common.config import load_conditions, ready_s, CONFIG_SHA256
from kmd_toc.common.models import (Snap, Stop, Vehicle, Depot, Berth, Experiment,
                                   Problem, Visit, Trip, Plan)
from kmd_toc.common.od import OD


def fixture_problem(n=5, vehicles=3, berths=2):
    ids = ('depot',*(f'c{i}' for i in range(1,n+1)))
    d = np.zeros((n+1,n+1),dtype='float64')
    t = np.zeros_like(d)
    for i in range(n+1):
        for j in range(n+1):
            if i!=j:
                d[i,j] = 100+13*i+7*j+(100 if i>j else 0)
                t[i,j] = 60+3*i+5*j+(9 if i>j else 0)+0.2
    od = OD(ids,d,t,np.ones_like(d,dtype='bool'),
            {'kind':'synthetic','road_version':'synthetic-directed-v1',
             'graph_id':'synthetic-graph-v1','units':{'distance':'m','duration':'s'}})
    def snap(i):
        return Snap(139.7+i*.0001,35.58,0.0,'synthetic-hint',(i,),
                    'synthetic-graph-v1',True,'synthetic witness, not actual road')
    stops = tuple(Stop(ids[i],139.7+i*.0001,35.58,1,snap(i),
                       {'kind':'synthetic_fixture','source':'tests/toc_common/conftest.py',
                        'generation':'arithmetic_directed_matrix_v1','sha256':'1'*64}) for i in range(1,n+1))
    c = load_conditions()
    o = c['operations']
    return Problem(stops,tuple(Vehicle(f'v{i}',60,2,ready_s(i,vehicles),72000) for i in range(vehicles)),
                   Depot('depot',139.7,35.58,snap(0),True,'synthetic depot'),
                   tuple(Berth(f'b{i}','depot',28800,72000,1800,o['preparation_s']) for i in range(berths)),od,
                   Experiment(f'TEST_N{n}',c['conditions_version'],CONFIG_SHA256,0,
                              {'od':od.fingerprint},{'fixture':True},{},'synthetic_validation'))


def fixture_plan(p, assignments=None):
    """Build a specified witness by arithmetic. No search or repairs."""
    if assignments is None:
        assignments = [('v0',('c1','c2'),60,'b0'),('v0',('c3','c4'),120,'b0'),
                       ('v1',('c5',),30,'b1')]
    previous, counts, trips = {}, {}, []
    o = load_conditions()['operations']
    for vid, identifiers, delay, berth in assignments:
        counts[vid] = counts.get(vid,0)+1
        ready = (previous[vid]+o['preparation_s'] if vid in previous else
                 next(v.first_ready_s for v in p.vehicles if v.vehicle_id == vid))
        start = ready+delay
        clock = start+o['loading_s']
        visits, distance, node = [],0.0,0
        for identifier in identifiers:
            j=p.od.ids.index(identifier)
            distance += float(p.od.distance_m[node,j])
            clock += math.ceil(float(p.od.duration_s[node,j]))
            visits.append(Visit(identifier,clock,clock,clock+o['service_s']))
            clock+=o['service_s']
            node=j
        distance+=float(p.od.distance_m[node,0])
        clock+=math.ceil(float(p.od.duration_s[node,0]))
        trips.append(Trip(vid,counts[vid],'depot','depot',tuple(visits),ready,berth,
                          start,start+o['loading_s'],start+o['loading_s'],clock,distance,delay))
        previous[vid]=clock
    return Plan('1.0','synthetic-witness','B',p.fingerprint,p.od.fingerprint,tuple(trips),{},'classical')


@pytest.fixture
def problem():
    return fixture_problem()


@pytest.fixture
def plan(problem):
    return fixture_plan(problem)


def rehash_problem(p, **kwargs):
    p=replace(p,**kwargs)
    return replace(p,experiment=replace(p.experiment,data_hashes={**p.experiment.data_hashes,'od':p.od.fingerprint}))
