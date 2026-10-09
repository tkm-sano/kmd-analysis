"""Numeric equivalence only, using existing fixtures; no scientific result writes."""
from pathlib import Path
import ast,importlib.util,json,math,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kmd_quantitative.battery import mass,scenarios
from kmd_quantitative.energy import controlled_dc as dc
from kmd_quantitative.simulation import trajectory_io

def old_dc():
 p=ROOT/dc.SOURCE_RELATIVE;s=importlib.util.spec_from_file_location('old_dc_reference',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class BatteryEnergyTests(unittest.TestCase):
 def test_mass_original_ast(self):
  p=ROOT/mass.SOURCE_RELATIVE;tree=ast.parse(p.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  calc=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='calc')
  loop=next(n for n in main.body if isinstance(n,ast.For) and 'masses.append' in ast.get_source_segment(p.read_text(),n))
  ns={'math':math,'stages':[],'masses':[]};exec(compile(ast.Module(body=[calc,loop],type_ignores=[]),str(p),'exec'),ns)
  self.assertEqual(mass.official_mass_stages(),ns['masses'])
 def test_frozen_units_and_stages(self):
  rows=mass.official_mass_stages();stages=scenarios.stage_inputs()
  self.assertEqual([r['e_pack_Wh_kg'] for r in rows],[180,220,250])
  for r,s in zip(rows,stages):
   self.assertEqual(r['E_pack_fixed_Wh'],20000);self.assertEqual(r['E_pack_fixed_kWh'],20)
   # Inherited Notebook freeze/float comparison, not a relaxed new tolerance.
   self.assertTrue(math.isclose(r['m_pack_model_kg'],s['m_pack_kg'],rel_tol=0,abs_tol=1e-10))
   self.assertTrue(math.isclose(r['m_vehicle_model_kg'],s['vehicle_mass_kg'],rel_tol=0,abs_tol=1e-10))
   self.assertEqual(s['running_mass_kg'],s['vehicle_mass_kg']+55)
 def test_custom_and_invalid_specific_energy(self):
  for r in mass.official_mass_stages():
   c=mass.mass_at_specific_energy(r['e_pack_Wh_kg'])
   for k in r:
    if k!='stage_id':self.assertEqual(c[k],r[k])
  for x in (0,-1,float('nan'),float('inf'),'220',None):
   with self.subTest(x=x),self.assertRaises(ValueError):mass.mass_at_specific_energy(x)
 def test_fixture_all_conditions(self):
  old=old_dc();m=scenarios.load_model();t,v=trajectory_io.read_dc_input(ROOT/'notebooks/fixtures/speed.csv');fixture=json.loads((ROOT/'notebooks/fixtures/speed.json').read_text())
  for speed in (v,np.array(fixture['braking_speed_m_s'])):
   for stage in scenarios.stage_inputs():
    for case in m['Crr_model']['cases'].values():
     p=case['p_bar'];new,arr=dc.evaluate(t,speed,m,p,stage);ref,ra=old.evaluate(t,speed,m,p,stage)
     self.assertEqual(new,ref)
     for k in arr:np.testing.assert_array_equal(arr[k],ra[k])
     dc.scalar_check(t,speed,m,p,stage,new)
     self.assertEqual(new['accepted_regen_Wh'],0);self.assertIsNone(new['auxiliary_Wh'])
     self.assertEqual(new['terminal_stock_Wh'],18000-float(np.cumsum(arr['dc'])[-1]))
 def test_invalid_behavior_same(self):
  old=old_dc();m=scenarios.load_model();stage=m['stage_inputs'][0]
  for t,v in [(np.array([0,2]),np.array([1.,1.])),(np.array([0,1]),np.array([-1.,1.])),(np.array([0,1]),np.array([np.nan,1.])),(np.array([0]),np.array([1.]))]:
   errors=[]
   for fn in (old.evaluate,dc.evaluate):
    try:fn(t,v,m,4.5,stage)
    except Exception as e:errors.append((type(e).__name__,str(e)))
    else:errors.append(None)
   self.assertEqual(errors[0],errors[1]);self.assertIsNotNone(errors[0])
 def test_original_broadcast_behavior_retained(self):
  # The low-level frozen kernel does not reject every shape mismatch.
  # Keep that behavior; CSV clients use Simulation's equal-length guard.
  t=np.array([0,1,2]);v=np.array([1.,1.]);m=scenarios.load_model();stage=m['stage_inputs'][0]
  a,x=dc.evaluate(t,v,m,4.5,stage);b,y=old_dc().evaluate(t,v,m,4.5,stage)
  self.assertEqual(a,b)
  for k in x:np.testing.assert_array_equal(x[k],y[k])
  with self.assertRaises(ValueError):trajectory_io.validate_dc_input(t,v)
 def test_fresh_freeze_and_function_alias(self):
  a=scenarios.load_model();a['stage_inputs'][0]['running_mass_kg']=-1
  self.assertEqual(scenarios.stage_inputs()[0]['running_mass_kg'],1155)
  self.assertIs(dc.evaluate,dc._kernel.evaluate);self.assertIs(dc.scalar_check,dc._kernel.scalar_check)
if __name__=='__main__':unittest.main()
