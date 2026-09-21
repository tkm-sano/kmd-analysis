"""Deterministic software tests, no solver/quantum experiments."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from traffic_simulation.r24_vrptw import InputError, validate_input, validate_routes
from traffic_simulation.r24_vrptw.cases import inputs, saved_cases


def base():
    return inputs(saved_cases()[0])


class FrozenCases(unittest.TestCase):
    def test_all_ten_alternatives_exact_times_and_axes(self):
        for case in saved_cases():
            with self.subTest(case=case['case']):
                data,routes=inputs(case); result=validate_routes(data,routes)
                expected=[x for route in case['expected_arrival_start_wait_departure_by_route'] for x in route]
                self.assertEqual([[r[k] for k in ['arrival_time','service_start_time','waiting_time','service_end_time']] for r in result['customers']],expected)
                self.assertEqual([r['return_time'] for r in result['vehicles'] if r['used']],case['expected_depot_return_s'])
                self.assertEqual([r['late_amount'] for r in result['customers']],case['expected_lateness_route_flat_order'])
                for axis,status in case['expected_axes'].items():
                    self.assertEqual(result[f'{axis}_feasible'],status=='PASS')
                self.assertEqual(result['status'],case['expected_validation'])
                self.assertEqual(result['overall_feasible'],case['expected_validation']=='VALID_SOLUTION')
                for row in result['customers']:
                    self.assertEqual(row['early_amount'],row['waiting_time'])
                    self.assertEqual(row['departure_time'],row['service_end_time'])
                    self.assertEqual(row['temporal_feasible'],row['late_amount']==0)
                for vr in result['vehicles']:
                    if vr['used']:
                        self.assertEqual(vr['travel_time_seconds']+vr['waiting_time']+vr['service_time'],vr['elapsed_time'])
    def test_replay_does_not_mutate_inputs(self):
        data,routes=base();old=copy.deepcopy((data,routes));validate_routes(data,routes)
        self.assertEqual((data,routes),old)


class InvalidInputs(unittest.TestCase):
    def reject(self, change, message=None):
        data,routes=base();change(data,routes)
        with self.assertRaises(InputError) as cm:validate_routes(data,routes)
        if message:self.assertIn(message,str(cm.exception))
    def test_earliest_after_latest(self):self.reject(lambda d,r:d['customers'][0].update(earliest_service_time=70))
    def test_negative_service(self):self.reject(lambda d,r:d['customers'][0].update(service_duration=-1))
    def test_negative_travel(self):self.reject(lambda d,r:d['travel'][0].update(travel_time_seconds=-1))
    def test_missing_arc(self):self.reject(lambda d,r:d['travel'].pop(),'missing travel arcs')
    def test_duplicate_customer(self):self.reject(lambda d,r:d['customers'].append(d['customers'][0]))
    def test_unknown_customer_route(self):self.reject(lambda d,r:r[0]['stops'].insert(1,'UNKNOWN'),'unknown customer')
    def test_duplicate_vehicle(self):self.reject(lambda d,r:d['vehicles'].append(d['vehicles'][0]))
    def test_zero_capacity(self):self.reject(lambda d,r:d['vehicles'][0].update(capacity=0))
    def test_negative_demand(self):self.reject(lambda d,r:d['customers'][0].update(demand=-1))
    def test_inverted_depot(self):self.reject(lambda d,r:d['depot'].update(opening_time=101))
    def test_window_outside_depot(self):self.reject(lambda d,r:d['customers'][0].update(latest_service_time=101))
    def test_duplicate_arc(self):self.reject(lambda d,r:d['travel'].append(d['travel'][0]))
    def test_unknown_arc(self):self.reject(lambda d,r:d['travel'][0].update(origin='UNKNOWN'))
    def test_self_arc(self):self.reject(lambda d,r:d['travel'][0].update(destination=d['travel'][0]['origin']))
    def test_unknown_route_vehicle(self):self.reject(lambda d,r:r[0].update(vehicle_id='UNKNOWN'))
    def test_duplicate_route_vehicle(self):self.reject(lambda d,r:r.append(r[0]))
    def test_boolean_quantity(self):self.reject(lambda d,r:d['customers'][0].update(demand=True))
    def test_nonfinite(self):
        for val in [float('nan'),float('inf'),'-Infinity','NaN']:
            with self.subTest(value=val):self.reject(lambda d,r:d['travel'][0].update(travel_time_seconds=val))
    def test_invalid_decimal_strings(self):
        for val in [' 1 ', '1_0', '1/2']:
            with self.subTest(value=val):self.reject(lambda d,r:d['travel'][0].update(travel_time_seconds=val))
    def test_units(self):self.reject(lambda d,r:d.update(time_unit='minutes'))
    def test_typo_field(self):self.reject(lambda d,r:d['customers'][0].update(duraton=0))
    def test_no_solver_certificate_input(self):self.reject(lambda d,r:r[0].update(service_start_time=0,feasible=True))
    def test_bad_coordinates(self):self.reject(lambda d,r:d['customers'][0].update(coordinates=[1]))
    def test_bad_stops_type(self):self.reject(lambda d,r:r[0].update(stops='DEP_006,1,2,DEP_006'))


class BoundariesAndStructure(unittest.TestCase):
    def test_nonzero_origin(self):
        d,r=base();d['depot'].update(opening_time=3600,closing_time=3700)
        for c in d['customers']:c['earliest_service_time']+=3600;c['latest_service_time']+=3600
        result=validate_routes(d,r);self.assertEqual([x['arrival_time'] for x in result['customers']],[3610,3625]);self.assertEqual(result['vehicles'][0]['return_time'],3640)
    def test_exact_latest_and_return_boundary(self):
        d,r=base();d['customers'][0]['latest_service_time']=10;d['customers'][1]['latest_service_time']=25;d['depot']['closing_time']=40
        self.assertTrue(validate_routes(d,r)['overall_feasible'])
    def test_positive_sub_tolerance_lateness_fails(self):
        d,r=base();d['customers'][0]['latest_service_time']='9.99999999'
        result=validate_routes(d,r);self.assertFalse(result['temporal_feasible']);self.assertEqual(result['customers'][0]['late_amount'],'0.00000001')
    def test_fractional_seconds_exact(self):
        d,r=base()
        for a in d['travel']:a['travel_time_seconds']='0.1'
        for c in d['customers']:c['service_duration']='0.2'
        result=validate_routes(d,r);self.assertEqual(result['vehicles'][0]['return_time'],'0.7');self.assertEqual(result['customers'][1]['arrival_time'],'0.4')
    def test_zero_demand_and_degenerate_window(self):
        d,r=base();d['depot']['closing_time']=0
        for c in d['customers']:c.update(demand=0,earliest_service_time=0,latest_service_time=0,service_duration=0)
        for a in d['travel']:a['travel_time_seconds']=0
        self.assertTrue(validate_routes(d,r)['overall_feasible'])
    def test_duplicate_visit_across_vehicles(self):
        d,r=base();d['vehicles'].append(dict(vehicle_id='v2',capacity=14));r.append(dict(vehicle_id='v2',stops=['DEP_006','1','DEP_006']))
        v=validate_routes(d,r);self.assertFalse(v['visit_feasible']);self.assertTrue(v['route_feasible']);self.assertFalse(v['overall_feasible'])
    def test_missing_customer(self):
        d,r=base();r[0]['stops'].remove('2');v=validate_routes(d,r);self.assertFalse(v['visit_feasible']);self.assertTrue(v['temporal_feasible'])
    def test_invalid_endpoints_not_temporal_pass(self):
        d,r=base();r[0]['stops'].pop();v=validate_routes(d,r);self.assertFalse(v['route_feasible']);self.assertFalse(v['depot_feasible']);self.assertIsNone(v['temporal_feasible'])
    def test_interior_depot(self):
        d,r=base();r[0]['stops'].insert(2,'DEP_006');self.assertFalse(validate_routes(d,r)['route_feasible'])
    def test_repeated_customer_subtour(self):
        d,r=base();r[0]['stops'].insert(-1,'1');v=validate_routes(d,r);self.assertFalse(v['route_feasible']);self.assertIsNone(v['temporal_feasible']);self.assertIsNone(v['depot_feasible'])
    def test_multiple_malformed_routes(self):
        d,r=base();d['vehicles'].append(dict(vehicle_id='v2',capacity=14));r[0]['stops']=['DEP_006','1','1','DEP_006'];r.append(dict(vehicle_id='v2',stops=['2']))
        v=validate_routes(d,r);self.assertFalse(v['depot_feasible']);self.assertFalse(v['overall_feasible'])
    def test_unused_vehicle(self):
        d,r=base();d['vehicles'].append(dict(vehicle_id='v2',capacity=14));v=validate_routes(d,r);self.assertTrue(v['overall_feasible']);self.assertIsNone(v['vehicles'][1]['return_time'])
        r.append(dict(vehicle_id='v2',stops=[]));self.assertEqual(v,validate_routes(d,r))
    def test_optional_distance_unknown_not_zero(self):
        d,r=base();d['travel'][0].pop('travel_distance');v=validate_routes(d,r);self.assertIsNone(v['vehicles'][0]['travel_distance'])
    def test_read_only_parsed_input(self):
        d,r=base();v=validate_input(d)
        with self.assertRaises(TypeError):v['customers']['1']['duration']=0


class RegressionAndIndependence(unittest.TestCase):
    def test_existing_cvrp_route_validator_wide_windows(self):
        # Legacy validator import transitively loads model/highspy, but never solves.
        from traffic_simulation.r24_classical_reference.r24_solution_validator import validate_routes as legacy
        for variant in ['valid','overload','missing','duplicate']:
            with self.subTest(variant=variant):
                d,r=base()
                if variant=='overload':
                    for c in d['customers']:c['demand']=8
                if variant=='missing':r[0]['stops'].remove('2')
                if variant=='duplicate':r[0]['stops'].insert(-1,'1')
                for c in d['customers']:c['latest_service_time']=10000
                d['depot']['closing_time']=10000
                arcmap={(a['origin'],a['destination']):SimpleNamespace(travel_time=a['travel_time_seconds'],distance=a['travel_distance']) for a in d['travel']}
                # A nonconsecutive repeat needs no artificial self arc.
                if variant=='duplicate':
                    r[0]['stops']=['DEP_006','1','2','1','DEP_006']
                old_input=SimpleNamespace(customers=('1','2'),depot='DEP_006',capacity=14,max_vehicles=1,
                    demands={c['customer_id']:c['demand'] for c in d['customers']},arcs=arcmap,nodes=('DEP_006','1','2'))
                stops=r[0]['stops'];objective=sum(arcmap[i,j].travel_time for i,j in zip(stops,stops[1:]))
                old=legacy(old_input,[stops],objective);new=validate_routes(d,r)
                self.assertEqual(new['overall_feasible'],old.status=='VALID_SOLUTION')
                if variant in ('valid','overload','missing'):self.assertEqual(new['routing_objective_seconds'],old.objective)
    def test_no_solver_or_quantum_import_dependency(self):
        code='''import builtins
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in {'highspy','qiskit','qiskit_aer','scipy'}:raise AssertionError(name)
    return original(name,*args,**kwargs)
builtins.__import__=guarded
from traffic_simulation.r24_vrptw import validate_routes
from traffic_simulation.r24_vrptw.cases import inputs,saved_cases
assert validate_routes(*inputs(saved_cases()[0]))['overall_feasible']
'''
        subprocess.run([sys.executable,'-c',code],check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})

if __name__=='__main__':unittest.main()
