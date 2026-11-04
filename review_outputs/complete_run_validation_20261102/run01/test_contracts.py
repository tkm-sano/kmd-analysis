"""Meaningful contract tests, independent scalar vs pinned scientific implementation."""
import unittest,copy,sys,importlib.util,math
from pathlib import Path
from decimal import Decimal as D
import numpy as np
from common import *
from contracts import *
sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate
from kmd_quantitative.simulation.trajectory_io import validate_dc_input,read_dc_input

MODEL=read(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json')
for rel in ['src/kmd_quantitative/energy/controlled_dc.py','src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py','src/kmd_quantitative/simulation/trajectory_io.py','src/kmd_quantitative/simulation/frozen_sources/apply_r0_method_battery.py']:use(R/rel)
class Events(unittest.TestCase):
 def event(self,**kw):
  args=dict(stop_start=20,stop_end=222,ready=120,service=102,deadline=222);args.update(kw);return delivery_event(**args)
 def test_early_wait_and_equal_deadline(self):
  x=self.event();self.assertEqual((x['work_start_model_s'],x['work_complete_model_s'],x['outcome']),(120,222,'ON_TIME'));self.assertIsNone(x['physical_arrival_s']);self.assertEqual(x['formal_outcome'],'HOLD')
 def test_stop_end_is_not_work_completion(self):
  x=self.event(stop_end=600);self.assertEqual(x['work_complete_model_s'],222);self.assertEqual(x['extra_hold_s'],378)
 def test_late_and_exact_decimal_boundary(self):
  self.assertEqual(self.event(stop_start=121,stop_end=223)['outcome'],'LATE');self.assertEqual(self.event(deadline=221)['outcome'],'LATE')
  self.assertEqual(self.event(stop_start=.1,ready=.1,stop_end=102.1,deadline=102.1)['outcome'],'ON_TIME')
 def test_unfinished_and_missing_are_different(self):
  self.assertEqual(self.event(stop_start=None,stop_end=None)['outcome'],'NOT_COMPLETED');self.assertEqual(self.event(stop_start=None,stop_end=None,observation_complete=False)['outcome'],'INDETERMINATE')
 def test_missing_end_not_completed_by_inference(self):self.assertEqual(self.event(stop_end=None,observation_complete=False)['outcome'],'INDETERMINATE')
 def test_impossible_hold_rejected(self):
  with self.assertRaises(ValueError):self.event(stop_end=221)
  with self.assertRaises(ValueError):self.event(resume=221)
 def test_B_no_customer_deadline(self):self.assertEqual(self.event(ready=None,deadline=None)['outcome'],'COMPLETED_NO_CUSTOMER_DEADLINE')
 def test_fixed_denominator(self):
  x=rates([{'q_PE':2,'outcome':'ON_TIME'},{'q_PE':3,'outcome':'NOT_COMPLETED'},{'q_PE':5,'outcome':'INDETERMINATE'}]);self.assertEqual(x['demand_PE'],10);self.assertIsNone(x['F_PE']);self.assertEqual((x['F_PE_lower'],x['F_PE_upper']),(.2,.7))
class Policy(unittest.TestCase):
 def test_equal_cutoff_quantum_adopted(self):self.assertEqual(operation_policy(900,900,0,True)['method'],'QUANTUM')
 def test_unacquired_switch_at_first_event(self):
  x=operation_policy(900,60,0,False);self.assertEqual(x['method'],'CLASSICAL');self.assertEqual(x['switch_s'],-840);self.assertEqual(x['departure_s'],0)
 def test_success_after_cutoff_switch(self):self.assertEqual(operation_policy(900,3600,0,True)['departure_s'],720)
 def test_all_2808_saved_decisions(self):
  for x in rows(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv'):
   y=operation_policy(x['L'],x['T_Q'],x['B'],x['quantum_acquired']=='True')
   with self.subTest(scenario=x['scenario_id'],PID=x['PID']):self.assertEqual((y['method'],y['departure_s']),(x['adopted_method'],D(x['t_depart'])))
class Identity(unittest.TestCase):
 def setUp(self):
  with (O/'RUN_INPUTS.jsonl').open() as h:self.p=json.loads(next(h))['payload']
 def test_canonical_order_independent(self):self.assertEqual(complete_id(self.p),complete_id(dict(reversed(list(self.p.items())))))
 def test_every_physical_dimension_changes_identity(self):
  for key in ['road_sha256','vtype_sha256','environment_sha256','generator_sha256','input_sha256']:
   p=copy.deepcopy(self.p);p[key]='different'
   with self.subTest(key=key):self.assertNotEqual(complete_id(p)[0],complete_id(self.p)[0])
  for key,sub,value in [('vehicle','depart','120'),('traffic','seed',43),('simulation','step_s',.5)]:
   p=copy.deepcopy(self.p);p[key][sub]=value
   with self.subTest(key=key):self.assertNotEqual(complete_id(p)[0],complete_id(self.p)[0])
  p=copy.deepcopy(self.p);p['stops'][0]['duration']='103';self.assertNotEqual(complete_id(p)[0],complete_id(self.p)[0])
 def test_partial_input_cannot_get_full_run_id(self):
  p=copy.deepcopy(self.p);p['road_edges']=None;self.assertIsNone(complete_id(p)[0]);p=copy.deepcopy(self.p);p['unbound']=['unknown traffic'];self.assertIsNone(complete_id(p)[0])
 def test_manifest_reference_coverage_and_unique_keys(self):
  a=rows(O/'A_OPERATION_RUN_LINKS.csv');b=rows(O/'B_PLAN_RUN_LINKS.csv');self.assertEqual(len(a),2808);self.assertEqual(len({(x['scenario_id'],x['PID']) for x in a}),2808);self.assertEqual(len(b),36800);self.assertEqual(len({(x['family'],x['config_id'],x['problem_id'],x['rep']) for x in b}),36800)
  for x in b:self.assertTrue(x['run_id'] or x['input_status']=='UNBOUND')
 def test_stop_behind_on_same_edge_requires_loop(self):
  from build_run_ledger import static_check
  p={'road_edges':['e'],'stops':[{'lane':'e_0','endPos':'100','actType':'a'},{'lane':'e_0','endPos':'50','actType':'b'}]};lanes={'e_0':{'length':200,'allow':'delivery','disallow':''}}
  self.assertTrue(static_check(p,lanes,set()));p['road_edges']=['e','loop','e'];self.assertFalse(static_check(p,lanes,{('e','loop'),('loop','e')}))
 def test_route_vehicle_class_permission(self):
  from build_run_ledger import static_check
  p={'road_edges':['e'],'stops':[]};self.assertTrue(static_check(p,{},set(),{'e':False}));self.assertFalse(static_check(p,{},set(),{'e':True}))
 def test_missing_leg_is_unknown_not_false_connectivity_failure(self):
  from build_run_ledger import stitch_segments
  self.assertEqual(stitch_segments([['a','b'],None,['x','y']]),(None,[]));self.assertEqual(stitch_segments([['a','b'],['x','y']]),(None,['LEG_STITCH_MISMATCH']));self.assertEqual(stitch_segments([['a','b'],['b','c']]),(['a','b','c'],[]))
class DC(unittest.TestCase):
 def compare(self,t,v,m=1200,p=4.5):
  t,v=validate_trace(t,v,m,p);validate_dc_input(t,v);expected=scalar_dc(t,v,m,p);actual,parts=evaluate(t,v,MODEL,p,{'running_mass_kg':m});self.assertAlmostEqual(expected['DC_Wh'],actual['net_DC_Wh'],delta=1e-7);self.assertAlmostEqual(expected['observed_distance_m'],actual['observed_distance_m'],delta=1e-7)
  self.assertEqual(expected,scalar_dc(t,v,m,p));return expected,actual,parts
 def test_stop_accelerate_cruise_decelerate(self):
  x,_,_=self.compare([0,1,2,3],[0,10,10,0]);self.assertAlmostEqual(x['DC_Wh'],20.4410590184856,delta=1e-10)
 def test_rest_and_constant_speed(self):
  self.assertEqual(self.compare([0,1,2],[0,0,0])[0]['DC_Wh'],0);self.compare([0,1,2],[10,10,10])
 def test_sum_before_positive_part(self):
  x,_,parts=self.compare([0,1],[10,0]);self.assertEqual(x['DC_Wh'],0);self.assertLess(x['W3_Wh'],0)
  _,_,parts=self.compare([0,1],[10,9]);wrong=sum(max(float(a[0]),0) for k,a in parts.items() if k in ['roll','translational','rotational','aero'])/.9;self.assertGreater(wrong,0);self.assertEqual(float(parts['dc'][0]),0)
 def test_missing_duplicate_negative_nonfinite_rejected(self):
  for t,v in [([0,2],[0,1]),([0,0],[0,1]),([0,1],[0,-1]),([0,1],[0,float('nan')]),([0],[0]),([0,1],[0])]:
   with self.subTest(t=t,v=v):
    with self.assertRaises(ValueError):scalar_dc(t,v,1200,4.5)
 def test_mass_and_terminal_contract(self):
  for m in [0,-1,float('nan')]:
   with self.assertRaises(ValueError):scalar_dc([0,1],[0,1],m,4.5)
  x=scalar_dc([0,1],[0,1],1200,4.5,arrival=2);self.assertEqual(x['terminal_gap_s'],1);self.assertIsNone(x['terminal_gap_energy_Wh'])
 def test_material_mass_and_pressure_keep_kernel(self):
  for mass in [1140.0345436876048,1134.586246272528,1200,1400]:
   for pressure in [2.6,4.5]:self.compare([0,1,2,3],[0,10,10,0],mass,pressure)
 def test_csv_reader_hash_and_gap_rejection(self):
  f=O/'unit_trace.csv';f.write_text('timestamp_s,speed_m_s\n0,0\n1,10\n2,0\n');t,v=read_dc_input(f,expected_sha256=sha(f));self.assertEqual(len(t),3)
  with self.assertRaises(ValueError):read_dc_input(f,expected_sha256='0'*64)
  g=O/'unit_trace_missing.csv';g.write_text('timestamp_s,speed_m_s\n0,0\n2,10\n')
  with self.assertRaises(ValueError):read_dc_input(g)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]);result=unittest.TextTestRunner(verbosity=2).run(suite)
 write('UNIT_TEST_RESULTS.json',{'test_methods':result.testsRun,'failures':[(str(t),s) for t,s in result.failures],'errors':[(str(t),s) for t,s in result.errors],'successful':result.wasSuccessful(),'scope':'pure event/policy/identity plus pinned kernel and reader comparison; not regional native acceptance'})
 save_sources('UNIT_SOURCE_FILES.json');sys.exit(not result.wasSuccessful())
