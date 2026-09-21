"""Materialize only the previously frozen hand-crafted software test oracles."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ORACLE = ROOT / 'reproducibility/outputs/traffic_simulation/r24_vrptw_formulation_validation_design/20260921_v1/HANDCRAFTED_CASE_EXPECTATIONS.json'


def saved_cases():
    return json.loads(ORACLE.read_text())['cases']


def inputs(case):
    nodes = ['DEP_006', '1', '2']
    data = dict(schema_version='1.0', time_unit='seconds',
        metadata={'scenario': 'ABSTRACT_HANDCRAFTED', 'case': case['case'], 'source': str(ORACLE.relative_to(ROOT))},
        depot=dict(depot_id='DEP_006', opening_time=case['depot_window_s'][0], closing_time=case['depot_window_s'][1]),
        customers=[dict(customer_id=str(i+1), demand=case['demands'][i],
            earliest_service_time=case['windows_s_by_customer'][i][0],
            latest_service_time=case['windows_s_by_customer'][i][1],
            service_duration=case['duration_s_by_customer'][i]) for i in range(2)],
        vehicles=[dict(vehicle_id=f'vehicle_{k}', capacity=case['Q']) for k in range(case['m'])],
        travel=[dict(origin=i, destination=j, travel_time_seconds=case['all_nonself_directed_travel_s'],
            travel_distance=case['all_nonself_directed_distance_m']) for i in nodes for j in nodes if i != j])
    routes=[dict(vehicle_id=f'vehicle_{k}', stops=['DEP_006', *map(str,route), 'DEP_006'])
            for k,route in enumerate(case['abstract_routes_customers_only'])]
    return data,routes
