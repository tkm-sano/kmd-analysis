"""Exact synthetic regressions for quantum relocation; no quantum optimization."""
from pathlib import Path
import importlib.util,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'src'))
from kmd_quantitative.quantum import builder,decoder,qualification_builder as qualification
from kmd_quantitative.routing import solver,independent
from quantum_cases import cases,snapshot

class QuantumCoreTests(unittest.TestCase):
 def test_full_pre_migration_snapshot(self):
  golden=json.loads((ROOT/'tests/fixtures/quantum_phase2_golden.json').read_text())
  self.assertEqual(snapshot(builder,decoder,qualification),golden['cases'])
 def test_little_endian_mapping(self):
  self.assertEqual(builder.route_code([1,2,3],3),273)
  self.assertEqual(builder.route_code([3,2,1],3),84)
  a=next(cases())[1]
  self.assertEqual(decoder.decode(a,[(273>>i)&1 for i in range(9)],[])['route'],[0,1,2,3,0])
 def test_invalid_bit_inputs(self):
  a=next(cases())[1]
  for bits in ([0]*8,[0]*9,[2]*9):self.assertFalse(decoder.decode(a,bits,[])['valid'])
 def test_service_and_ancilla_rejection(self):
  a=next(cases())[1];a['service'][1]=101
  self.assertFalse(decoder.decode(a,[(273>>i)&1 for i in range(9)],[])['valid'])
  a=dict(cases())['time_window3'];model=qualification.build(a)
  perm=next(r['order'] for r in model['permutations'] if r['TIME_WINDOW'] and r['RETURN_HORIZON'])
  bits=qualification.witness(model,perm)
  self.assertTrue(decoder.decode(a,bits,model['ands'])['valid'])
  bits[model['ands'][0]['z']]^=1
  self.assertFalse(decoder.decode(a,bits,model['ands'])['valid'])
 def test_routing_import_unaffected(self):
  a=next(cases())[1];route,_=solver.enumerate_exact(a)
  self.assertEqual(independent.validate(a,route)['totals']['road_travel_seconds'],'40')

class LegacyCompatibilityTests(unittest.TestCase):
 def test_qualification_old_paths(self):
  for name,new in [('builder',qualification),('decoder',decoder)]:
   p=ROOT/'05_src/traffic_simulation/matched_quantum_qualification'/(name+'.py')
   self.assertTrue(p.is_symlink());self.assertEqual(p.read_bytes(),Path(new.__file__).read_bytes())
   s=importlib.util.spec_from_file_location('old_'+name,p);old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
   a=next(cases())[1]
   if name=='builder':self.assertEqual(old.build(a),new.build(a))
   else:self.assertEqual(old.decode(a,[(273>>i)&1 for i in range(9)],[]),new.decode(a,[(273>>i)&1 for i in range(9)],[]))

if __name__=='__main__':unittest.main(verbosity=2)
