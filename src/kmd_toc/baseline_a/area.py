"""Input-derived small areas and bounded same-area preference for A v3.

These are researcher rules, not a claim about any carrier's actual algorithm.
Costs are explicit: public time for calibration, shared road distance for Ota.
"""
import math
import numpy as np


def local_xy(longitudes, latitudes, depot_longitude, depot_latitude):
    lon, lat = np.asarray(longitudes, dtype=float), np.asarray(latitudes, dtype=float)
    if lon.shape != lat.shape or not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ValueError('AREA_COORDINATES')
    radius = 6371008.8
    return np.column_stack((np.radians(lon-depot_longitude)*radius*math.cos(math.radians(depot_latitude)),
                            np.radians(lat-depot_latitude)*radius))


def spatial_labels(nodes, xy, stop_ids, leaf_capacity):
    if type(leaf_capacity) is not int or leaf_capacity < 2:
        raise ValueError('AREA_LEAF_CAPACITY')
    nodes = list(nodes)
    if len(nodes) != len(set(nodes)) or any(j <= 0 or j >= len(stop_ids) for j in nodes):
        raise ValueError('AREA_NODES')
    labels = {}
    def divide(group, prefix):
        if len(group) <= leaf_capacity:
            labels.update((j, prefix) for j in group)
            return
        spans = np.ptp(xy[group], axis=0)
        axis = 0 if spans[0] >= spans[1] else 1
        ordered = sorted(group, key=lambda j: (float(xy[j,axis]), stop_ids[j]))
        cut = len(ordered)//2
        divide(ordered[:cut], prefix+'0')
        divide(ordered[cut:], prefix+'1')
    divide(nodes, 'area')
    return labels


def ordered_nodes(nodes, costs, xy, stop_ids, parameters, supplied_labels=None):
    """Return every given node exactly once, plus a transparent area trace."""
    nodes = list(nodes)
    if not nodes or len(nodes) != len(set(nodes)) or any(j <= 0 or j >= len(stop_ids) for j in nodes):
        raise ValueError('AREA_NODES')
    subset = costs[np.ix_([0,*nodes], [0,*nodes])]
    if not np.isfinite(subset).all() or (subset < 0).any():
        raise ValueError('AREA_UNREACHABLE_OR_NEGATIVE_COST')
    if parameters['kind'] not in ('NN', 'area'):
        raise ValueError('AREA_KIND')
    factor = parameters.get('stay_factor')
    if factor is not None and (type(factor) not in (int,float) or not math.isfinite(factor) or factor < 1):
        raise ValueError('AREA_STAY_FACTOR')
    if parameters['kind'] == 'NN':
        labels = {j: str(j) for j in nodes}
    elif supplied_labels is None:
        labels = spatial_labels(nodes, xy, stop_ids, parameters['leaf_capacity'])
    else:
        labels = {j: supplied_labels.get(j) for j in nodes}
        labels = {j: value if isinstance(value,str) and value else f'unknown:{stop_ids[j]}'
                  for j,value in labels.items()}
    remaining, current, order, trace = set(nodes), 0, [], []
    while remaining:
        key = lambda j: (float(costs[current,j]), stop_ids[j])
        global_next = min(remaining, key=key)
        chosen, preferred = global_next, False
        if parameters['kind'] == 'area' and current != 0:
            same = [j for j in remaining if labels[j] == labels[current]]
            if same:
                local = min(same, key=key)
                if factor is None or float(costs[current,local]) <= factor*float(costs[current,global_next]):
                    chosen, preferred = local, True
        trace.append({'from': current, 'to': chosen, 'area': labels[chosen],
                      'same_area_preference': preferred, 'global_nearest': global_next})
        remaining.remove(chosen)
        order.append(chosen)
        current = chosen
    return order, {'labels': {stop_ids[j]: labels[j] for j in nodes}, 'decisions': trace,
                   'automatic_areas': supplied_labels is None, 'parameters': parameters}
