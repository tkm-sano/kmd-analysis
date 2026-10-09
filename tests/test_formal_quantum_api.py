"""No quantum experiment: frozen statement identity plus synthetic result contracts."""
from pathlib import Path
import ast, copy, importlib.util, sys, unittest
from decimal import Decimal as D
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kmd_quantitative.quantum import formal, builder, qualification_builder, decoder
from kmd_quantitative.routing import independent
from quantum_cases import cases

class FormalQuantumTests(unittest.TestCase):
 def setUp(self):
  self.a=dict(next(cases())[1]);self.model=qualification_builder.build(self.a)
 def test_frozen_r1_statement_identity(self):
  tree=ast.parse((ROOT/'05_src/traffic_simulation/matched_quantum_r1_c_protocol_v2/worker.py').read_text())
  child=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute_child')
  # Independent source interval lookup, not the adapter's slicing helper.
  starts={t.id:i for i,n in enumerate(child.body) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
  for nodes,left,right in [(formal._FEASIBLE,'feasible_routes','exact_optimum'),(formal._FINAL,'routes','best')]:
   original=child.body[starts[left]:starts[right]+1]
   if left=='feasible_routes':
    # R1 is explicitly four-customer; shared R0 source generalizes this argument.
    call=next(x for x in ast.walk(ast.Module(body=original,type_ignores=[])) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='route_code')
    self.assertEqual(ast.dump(call.args[1]),ast.dump(ast.Constant(4)))
    shared_call=next(x for x in ast.walk(ast.Module(body=nodes,type_ignores=[])) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='route_code')
    call.args[1]=copy.deepcopy(shared_call.args[1])
   if left=='routes':
    call=next(x for x in ast.walk(ast.Module(body=original,type_ignores=[])) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='format')
    self.assertEqual(ast.dump(call.args[1]),ast.dump(ast.Constant('016b')))
    shared_call=next(x for x in ast.walk(ast.Module(body=nodes,type_ignores=[])) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='format')
    call.args[1]=copy.deepcopy(shared_call.args[1])
   self.assertEqual(ast.dump(ast.Module(body=original,type_ignores=[])),ast.dump(ast.Module(body=nodes,type_ignores=[])))
  sample=next(n for n in child.body if isinstance(n,ast.FunctionDef) and n.name=='sample')
  for n in formal._COUNTS:
   self.assertTrue(any(ast.dump(n)==ast.dump(x) for x in sample.body))
 def test_all_small_codes_against_qualification(self):
  table,opt=formal.feasible_route_table(self.model,self.a)
  for code in range(512):
   out=formal.evaluate_final_counts(self.model,self.a,{code:1})
   decoded=decoder.decode(self.a,[(code>>i)&1 for i in range(9)],[])
   self.assertEqual(out['final_feasible_count'],int(decoded['valid']))
   if decoded['valid']:
    self.assertEqual(out['best_final_feasible_route']['route_indices'],decoded['route'])
    self.assertEqual(out['best_final_feasible_route']['independent_validation'],independent.validate(self.a,decoded['route']))
 def test_direct_frozen_r1_output(self):
  tree=ast.parse((ROOT/'05_src/traffic_simulation/matched_quantum_r1_c_protocol_v2/worker.py').read_text())
  child=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute_child')
  starts={t.id:i for i,n in enumerate(child.body) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
  for name,a in cases():
   if name!='base4':continue  # frozen R1 table hardcodes n=4
   model=qualification_builder.build(a)
   ns={'a':a,'model':model,'D':D,'ind':independent,'route_code':builder.route_code,'ValidationFailure':formal.ValidationFailure}
   nodes=child.body[starts['feasible_routes']:starts['exact_optimum']+1]
   if name in {'capacity3','return3'}:
    with self.assertRaises(AssertionError):formal.feasible_route_table(model,a)
    continue
   exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-r1-reference','exec'),ns)
   table=ns['feasible_routes'];counts={k:i+1 for i,k in enumerate(table)};counts[0]=7
   ns.update(q=int(model['n'])**2,final={'counts':counts,'feasible_count':sum(v for k,v in counts.items() if k in table)})
   exec(compile(ast.Module(body=child.body[starts['routes']:starts['best']+1],type_ignores=[]),'frozen-r1-reference','exec'),ns)
   actual=formal.evaluate_final_counts(model,a,counts)
   self.assertEqual(actual,{'final_feasible_count':ns['final']['feasible_count'],'sampled_feasible_routes':ns['routes'],'best_final_feasible_route':ns['best']})
 def test_tie_rule_not_frequency(self):
  a=self.a.copy();a['travel']=self.a['travel'].copy();a['travel'][:]=10
  for i in range(4):a['travel'][i,i]=0
  model=qualification_builder.build(a);table,_=formal.feasible_route_table(model,a)
  codes=sorted(table);out=formal.evaluate_final_counts(model,a,{codes[-1]:100,codes[0]:1})
  self.assertEqual(int(out['best_final_feasible_route']['bitstring'],2),codes[0])
  self.assertEqual(D(out['best_final_feasible_route']['road_travel_objective_s']),D(40))
 def test_absent_and_invalid_samples(self):
  for counts in ({},{0:64},{512:1},{511:1}):
   out=formal.evaluate_final_counts(self.model,self.a,counts)
   self.assertIsNone(out['best_final_feasible_route']);self.assertEqual(out['final_feasible_count'],0)
  self.assertEqual(formal.parse_sample_counts({'100 010 001':2},2),{273:2})
  with self.assertRaises(ValueError):formal.parse_sample_counts({'not-binary':1},1)
  with self.assertRaises(formal.ProtocolFailure):formal.parse_sample_counts({'0':1},2)
 def test_independent_recheck_failure(self):
  original=independent.validate;calls=0
  def fail_final(a,route):
   nonlocal calls
   calls+=1
   if calls>6:raise AssertionError('artificial final validation failure')
   return original(a,route)
  with patch.object(independent,'validate',fail_final):
   with self.assertRaisesRegex(formal.ValidationFailure,'FINAL_ROUTE_FAILED'):
    formal.evaluate_final_counts(self.model,self.a,{273:1})
 def test_no_worker_side_effects(self):
  # Import module under another package identity with writes/worker imports prohibited.
  spec=importlib.util.spec_from_file_location('kmd_quantitative.quantum._safe_probe',formal.__file__)
  mod=importlib.util.module_from_spec(spec)
  with patch('subprocess.run',side_effect=AssertionError('worker launch')),patch('pathlib.Path.write_text',side_effect=AssertionError('write')):
   spec.loader.exec_module(mod)
  self.assertFalse(any(k.endswith('.science') for k in sys.modules))

if __name__=='__main__':unittest.main()
