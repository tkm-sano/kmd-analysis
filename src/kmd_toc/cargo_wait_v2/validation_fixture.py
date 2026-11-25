"""Artificial graph for candidate propagation tests; never a research input."""
from dataclasses import replace


def quantum_connection_witness():
    import numpy as np
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.common.od import OD
    p = artificial_problem(6, 2, 1)
    # Explicit shortest-path seconds of a synthetic directed graph (seed 6).
    # Selected because one legal macro permutation improves the CW seed, so
    # candidate propagation is observable. No A values enter this construction.
    seconds = np.array([
        [0,58,56,40,50,43,69], [40,0,96,26,36,48,69],
        [49,39,0,65,50,21,65], [14,64,70,0,10,24,43],
        [42,54,79,59,0,14,33], [28,59,84,68,48,0,66],
        [40,21,80,26,36,50,0]], dtype=float)
    graph = 'synthetic-candidate-connection-seed6'
    od = OD(p.od.ids, seconds * 10, seconds, p.od.reachable,
            {**p.od.metadata, 'road_version': graph, 'graph_id': graph,
             'warning': 'candidate propagation witness only; invented graph weights'})
    stops = tuple(replace(s, snap=replace(s.snap, graph_id=graph), source={**s.source,
                  'generation': 'synthetic_quantum_candidate_connection_witness'}) for s in p.stops)
    return replace(p, od=od, stops=stops, depot=replace(p.depot, snap=replace(p.depot.snap, graph_id=graph)),
                   experiment=replace(p.experiment, scenario_id='ART_QUANTUM_CONNECTION_N6',
                                      data_hashes={'od': od.fingerprint})).validate()
