"""Scalar/known-route tests and read-only completed-execution regression checks.

No optimization is executed by this test suite. Full scientific executions live
in run_charging_validation only. Never change frozen fixture values in tests.
"""
import unittest,copy,json,os
from pathlib import Path
from fractions import Fraction as F
from .charging import power_rule,minimal_charges,route_replay,fleet_replay,json_number
from .charging_independent import validate,validate_exhaustive
from .run_charging_validation import load,R

class ChargingUnits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance,cls.od,cls.pre,cls.design,cls.ctx=load();cls.nodes=cls.pre['route']
        cls.q=minimal_charges(cls.ctx,cls.nodes,True)
        cls.r=route_replay(cls.ctx,'V1',cls.nodes,cls.q)
    def test_01_power_rule(self):
        required,p=power_rule(self.pre['q_required_kwh'],self.pre['available_charge_time_s'])
        self.assertEqual(p,10);self.assertGreaterEqual(p,F('1.1')*required);self.assertLess(p-1,F('1.1')*required)
    def test_02_charging_seconds(self):
        self.assertEqual(F(str(self.r['charging_s'])),360*F(self.pre['q_required_kwh']))
    def test_03_zero_charge(self):
        r=route_replay(self.ctx,'V1',self.nodes,{'1':0})
        self.assertEqual(r['charging_s'],0);self.assertFalse(r['battery_feasible']);self.assertTrue(r['temporal_feasible'])
    def test_04_positive_partial_charge(self):
        self.assertEqual(self.q['1'],F(self.pre['q_required_kwh']));self.assertLess(F(str(self.r['events'][0]['departure_battery_kwh'])),20)
    def test_05_battery_upper_bound(self):
        r=route_replay(self.ctx,'V1',self.nodes,{'1':20})
        self.assertFalse(r['battery_feasible']);self.assertGreater(F(str(r['events'][0]['departure_battery_kwh'])),20)
    def test_06_reserve_equal_and_just_below(self):
        self.assertTrue(self.r['battery_feasible']);self.assertEqual(F(str(self.r['final_battery_kwh'])),2)
        r=route_replay(self.ctx,'V1',self.nodes,{'1':self.q['1']-F('1e-12')})
        self.assertFalse(r['battery_feasible'])
    def test_07_energy_conservation(self):
        self.assertEqual(self.ctx['initial']+F(str(self.r['charged_kwh']))-F(str(self.r['energy_kwh'])),F(str(self.r['final_battery_kwh'])))
    def test_08_charger_reachability(self):
        for i,j in zip(self.nodes,self.nodes[1:]):self.assertTrue(self.od[i+'|'+j]['reachable'])
        self.assertGreaterEqual(F(str(self.r['events'][0]['arrival_battery_kwh'])),2)
    def test_09_time_propagation(self):
        t=F(str(self.r['charging_s']))
        for event,base in zip(self.r['events'],self.pre['zero_charge_time_envelope']):
            shift=F(0) if event['position']==1 else t
            self.assertEqual(F(str(event['arrival_time_s'])),F(base['arrival_without_charge_time_s'])+shift)
        self.assertTrue(self.r['temporal_feasible'])
    def test_10_final_depot(self):
        self.assertEqual(self.r['events'][-1]['node'],self.instance['depot']['depot_id'])
        self.assertEqual(F(str(self.r['final_SOC_pct'])),10)
    def test_11_primary_unchanged_by_charging_amount(self):
        zero=route_replay(self.ctx,'V1',self.nodes,{'1':0})
        self.assertEqual(zero['travel_s'],self.r['travel_s']);self.assertEqual(F(str(self.r['travel_s'])),F(self.pre['road_time_with_charger_s']))
    def test_12_secondary_less_charge_preferred(self):
        extra=route_replay(self.ctx,'V1',self.nodes,{'1':self.q['1']+F('.001')})
        self.assertTrue(extra['feasible']);self.assertEqual(extra['travel_s'],self.r['travel_s']);self.assertGreater(F(str(extra['charging_s'])),F(str(self.r['charging_s'])))
    def test_13_no_charge_failure_diagnosis(self):
        r=route_replay(self.ctx,'V1',self.nodes,{'1':0})
        self.assertEqual(r['first_reserve_violation']['destination'],self.nodes[3]);self.assertTrue(r['temporal_feasible'])
    def test_14_enabled_success(self):self.assertTrue(self.r['feasible'])
    def test_15_independent_agreement_and_tamper(self):
        plans=[dict(vehicle_id='V1',nodes=self.nodes,charges={'1':json_number(self.q['1'])}),dict(vehicle_id='V2',nodes=[],charges={})]
        result=fleet_replay(self.ctx,plans)
        self.assertEqual(validate(self.instance,self.od,self.pre,plans,result,True)['status'],'PASS')
        bad=copy.deepcopy(result);bad['routes'][0]['events'][1]['arrival_time_s']='0'
        self.assertEqual(validate(self.instance,self.od,self.pre,plans,bad,True)['status'],'FAIL')
    def test_16_json_charge_serialization(self):
        p={'vehicle_id':'V1','nodes':self.nodes,'charges':self.q}
        saved={**p,'charges':{k:json_number(v) for k,v in p['charges'].items()}}
        self.assertEqual(F(str(json.loads(json.dumps(saved))['charges']['1'])),self.q['1'])
    def test_17_illegal_charging_location(self):
        with self.assertRaises(ValueError):route_replay(self.ctx,'V1',self.nodes,{'2':1})
    def test_18_customer_timing_matches_frozen_validator_without_charger(self):
        from r24_vrptw.validator import validate_routes
        nodes=[x for x in self.nodes if x!=self.ctx['charger']]
        base=validate_routes(self.instance,[{'vehicle_id':'V1','stops':nodes}])
        overlay=route_replay(self.ctx,'V1',nodes,{})
        self.assertEqual([e['arrival_time_s'] for e in overlay['events'][:-1]],[e['arrival_time'] for e in base['customers']])
        self.assertEqual(overlay['return_time_s'],base['vehicles'][0]['return_time'])

@unittest.skipUnless(os.environ.get('EVRP_RESULT_DIR'),'Saved execution not requested')
class SavedCrossValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o=Path(os.environ['EVRP_RESULT_DIR']);cls.i,cls.od,cls.p,_,_=load()
        cls.refs=json.loads((cls.o/'CHARGING_EXACT_REFERENCE.json').read_text());cls.m=json.loads((cls.o/'CHARGING_MILP_RESULT.json').read_text())
    def test_19_exact_milp_agreement(self):
        cross=json.loads((self.o/'CROSS_VALIDATION.json').read_text());self.assertTrue(all(cross.values()))
        for name in ['disabled','enabled']:self.assertEqual(self.refs[name]['status'],self.m[name]['status'])
    def test_20_all_structures_independently_checked(self):
        for name,ref in self.refs.items():self.assertEqual(validate_exhaustive(self.i,self.od,self.p,ref)['status'],'PASS')
    def test_21_milp_saved_fields(self):
        m=self.m['enabled'];self.assertEqual(validate(self.i,self.od,self.p,m['plans'],m['replay'],True,floating=True)['status'],'PASS')
    def test_22_global_lexicographic_minimum(self):
        ref=self.refs['enabled'];objectives=[(F(str(x['result']['primary_travel_s'])),F(str(x['result']['secondary_charging_s']))) for x in ref['candidates'] if x['result']['feasible']]
        self.assertEqual(min(objectives),tuple(F(str(x)) for x in ref['objective']))

@unittest.skipUnless(os.environ.get('EVRP_RESULT_DIR'),'Saved execution not requested')
class RawCertificate(unittest.TestCase):
    def test_23_raw_milp_certificate(self):
        from .charging_independent import validate_raw_milp
        i,od,p,_,_=load();m=json.loads((Path(os.environ['EVRP_RESULT_DIR'])/'CHARGING_MILP_RESULT.json').read_text())['enabled']
        self.assertEqual(validate_raw_milp(i,od,p,m)['status'],'PASS')
        bad=copy.deepcopy(m);bad['raw_schedule'][-1]['battery_arrival_kwh']=0
        self.assertEqual(validate_raw_milp(i,od,p,bad)['status'],'FAIL')

if __name__=='__main__':unittest.main()
