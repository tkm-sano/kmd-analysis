"""Run: PYTHONPATH=05_src/traffic_simulation python -m unittest r24_minimal_evrp.test_replay -v"""
import copy
import json
import unittest
from fractions import Fraction as F
from pathlib import Path
from r24_vrptw.instance import InputError
from .replay import replay, distance_km, energy_kwh, battery_after, battery_feasible, parameters
from .independent import validate_saved

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reproducibility/outputs/traffic_simulation'
DESIGN=BASE/'r24_minimal_evrp_design_authority/20260926_v1'
BENCH=BASE/'r24_vrptw_benchmark_spec/20260921_v1'
CID='R24-RND-N002-R01-RHO050-TW-WIDE'
def read(p): return json.loads(p.read_text())

class EnergyRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance=read(BENCH/'instances'/f'{CID}.json')
        cls.authority=read(DESIGN/'MINIMAL_EVRP_AUTHORITY.json')
        cls.reference=read(BENCH/'preflight'/CID/'MILP.json')['audit']
        cls.routes=cls.reference['routes']
        cls.result=replay(cls.instance,cls.routes,cls.authority,source_distance_unit='m')

    def test_distance_energy(self):
        self.assertEqual(energy_kwh(distance_km(1000,'m'),F(127,1000)),F(127,1000))
        self.assertEqual(energy_kwh(distance_km(2500,'m'),F(127,1000)),F('0.3175'))

    def test_battery_propagation_scalar(self):
        battery=F(20); trajectory=[]
        for debit in (F('0.2'),F('0.3'),F('0.4')):
            battery=battery_after(battery,debit);trajectory.append(battery)
        self.assertEqual(trajectory,[F('19.8'),F('19.5'),F('19.1')])

    def test_reserve_boundary_scalar_only(self):
        self.assertTrue(battery_feasible(F(2),F(2),F(20)))
        self.assertFalse(battery_feasible(F(2)-F(1,10**12),F(2),F(20)))
        self.assertFalse(battery_feasible(F(20)+F(1,10**12),F(2),F(20)))

    def test_unit_consistency(self):
        r=parameters(self.authority)[3]
        self.assertEqual(r,F(127)/1000)
        self.assertEqual(distance_km('3588.462631414','m'),F('3.588462631414'))
        with self.assertRaises(InputError): distance_km(1,'km')
        with self.assertRaises(InputError): distance_km(-1,'m')
        with self.assertRaises(InputError): distance_km('NaN','m')

    def test_zero_charging(self):
        for row in self.result['arcs']+self.result['trajectory']:
            self.assertEqual(row['q_chg_kwh'],0);self.assertEqual(row['t_chg_s'],0)
        self.assertEqual(self.result['fleet']['q_chg_kwh'],0)

    def test_full_vrptw_regression(self):
        self.assertEqual(self.result['routes'],self.routes)
        self.assertEqual(self.result['vrptw'],self.reference['replay'])
        self.assertTrue(self.result['combined_feasible'])

    def test_final_depot_reserve(self):
        used=[v for v in self.result['vehicles'] if v['used']]
        self.assertEqual(len(used),1)
        self.assertEqual(used[0]['nodes'][-1],self.instance['depot']['depot_id'])
        self.assertGreaterEqual(F(used[0]['final_battery_kwh']),F(2))
        self.assertEqual(F(used[0]['final_battery_kwh']),F('18.477857385541'))

    def test_independent_agreement(self):
        saved=json.loads(json.dumps(self.result))
        self.assertEqual(validate_saved(self.instance,self.authority,self.routes,saved)['status'],'PASS')

    def test_independent_detects_corruption(self):
        for section,key,value in [('arcs','distance_km','3'),('arcs','energy_kwh','0'),
                                  ('arcs','battery_after_kwh','20'),('arcs','soc_after_pct','100'),
                                  ('trajectory','q_chg_kwh','1')]:
            with self.subTest(key=key):
                bad=copy.deepcopy(self.result);bad[section][0][key]=value
                self.assertEqual(validate_saved(self.instance,self.authority,self.routes,bad)['status'],'FAIL')
        bad=copy.deepcopy(self.result);bad['vehicles'][0]['final_battery_kwh']='20'
        self.assertEqual(validate_saved(self.instance,self.authority,self.routes,bad)['status'],'FAIL')

    def test_all_saved_optimal_witnesses(self):
        exact=read(BENCH/'preflight'/CID/'EXACT.json')
        self.assertEqual(len(exact['optimal_route_set']),2)
        for witness in exact['optimal_route_set']:
            result=replay(self.instance,witness['routes'],self.authority,source_distance_unit='m')
            self.assertTrue(result['combined_feasible'])
            self.assertEqual(result['vrptw']['routing_objective_seconds'],exact['best_objective'])
            self.assertEqual(validate_saved(self.instance,self.authority,witness['routes'],result)['status'],'PASS')

    def test_missing_distance_rejected(self):
        broken=copy.deepcopy(self.instance)
        for edge in broken['travel']: edge.pop('travel_distance')
        with self.assertRaises(InputError): replay(broken,self.routes,self.authority,source_distance_unit='m')

    def test_unreplayable_and_unused_preserved(self):
        bad=copy.deepcopy(self.routes);bad[0]['stops']=bad[0]['stops'][1:]
        result=replay(self.instance,bad,self.authority,source_distance_unit='m')
        self.assertIsNone(result['vrptw']['temporal_feasible'])
        self.assertIsNone(result['vehicles'][0]['ev_feasible'])
        self.assertFalse(result['combined_feasible'])
        self.assertIsNone(self.result['vehicles'][1]['ev_feasible'])
        self.assertEqual(self.result['vehicles'][1]['nodes'],[])

if __name__=='__main__': unittest.main()
