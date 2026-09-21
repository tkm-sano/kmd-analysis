"""Focused deterministic boundary and supplemental validation tests; no backend."""
import unittest,copy,ast
from .audit import *
class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=[read(OUT/'groups'/f'G{i}.json') for i in (1,2,3)]
        cls.inputs=read(OLD/'conditions'/(cls.r[0]['condition']+'.json'))['inputs']
    def test_normalization(self):
        for r in self.r:self.assertTrue(validate_state(r['state']));self.assertAlmostEqual(len(r['state']['support'])*r['state']['amplitude']**2,1)
    def test_variable_order_negative(self):
        x=copy.deepcopy(self.inputs);x['variable_order'][0],x['variable_order'][1]=x['variable_order'][1],x['variable_order'][0]
        with self.assertRaises(ValueError):construct(x)
    def test_support_uniqueness(self):
        for r in self.r:self.assertEqual(len(r['state']['support']),len(set(r['state']['support'])))
        s=copy.deepcopy(self.r[0]['state']);s['support'][1]=s['support'][0]
        with self.assertRaises(ValueError):validate_state(s)
    def test_deterministic(self):self.assertEqual(construct(self.inputs),construct(copy.deepcopy(self.inputs)))
    def test_leakage_inputs_rejected(self):
        for k in ['optimal_route','optimal_bitstring','feasible_states','cost','demand','time_window']:
            with self.assertRaises(ValueError):construct(dict(self.inputs,**{k:[]}))
    def test_constructor_dependency_boundary(self):
        path=ROOT/'05_src/traffic_simulation/r24_vrptw_structured_initial_state/construction.py';tree=ast.parse(path.read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='construct')
        forbidden={'open','read','Adapter','load','eval','exec','__import__'}
        self.assertFalse(any(isinstance(n,ast.Name) and n.id in forbidden for n in ast.walk(fn)))
    def test_fidelity_records(self):
        for r in self.r:self.assertAlmostEqual(r['fidelity']['fidelity'],1);self.assertLess(r['fidelity']['max_amplitude_difference'],1e-12)
    def test_fidelity_negative(self):
        a=np.array([1.,0.],complex)
        for b in [np.array([0.,1.]),np.array([np.nan,0]),np.array([.5,0]),np.array([1.])]:
            with self.assertRaises(ValueError):fidelity_check(b,a)
    def test_same_qubo_controls(self):
        for row in rows(OUT/'QUBO_GROUPS.csv'):
            old=read(OLD/'conditions'/(row['condition']+'.json'));r=next(x for x in self.r if x['group']==row['group']);self.assertEqual(construct(old['inputs']),r['state'])
    def test_unexpected_ancilla(self):
        x=copy.deepcopy(self.inputs);x['variable_order'].append('temporal_ancilla')
        with self.assertRaises(ValueError):construct(x)
    def test_malformed_amplitude(self):
        for a in [float('nan'),float('inf'),0]:
            s=copy.deepcopy(self.r[0]['state']);s['amplitude']=a
            with self.assertRaises(ValueError):validate_state(s)
    def test_energy_degeneracy(self):
        self.assertTrue(moments([1,1,1])['eigenstate']);self.assertFalse(moments([0,2])['eigenstate'])
        with self.assertRaises(ValueError):moments([float('nan')])
        for r in self.r:self.assertFalse(r['initial_energy']['eigenstate'])
    def test_slack_factor(self):
        p=slack_distribution([0.,0.],1e-5,.37);np.testing.assert_allclose(p,[.5,.5])
        with self.assertRaises(ValueError):slack_distribution([0,1,2],1,.37)
        for r in self.r:self.assertGreater(r['gamma_diagnostic']['total_variation'],1e-12)
    def test_active_temporal_limitation(self):
        s=self.r[2]['metrics'][1]
        for k in ['temporal_mass','overall_feasible_mass','optimal_mass','no_good_mass']:self.assertEqual(s[k],0)
        self.assertEqual(s['no_good_violated_mass'],1)
    def test_frozen_comparison_and_budget(self):
        receipt=read(OUT/'COMPARISON_REUSE_RECEIPT.json')
        for name,h in receipt['byte_identical_files'].items():self.assertEqual(sha(OUT/name),sha(SPEC/name));self.assertEqual(sha(OUT/name),h)
        self.assertEqual(sha(OUT/'SCIENTIFIC_RUN_PLAN.csv'),sha(SPEC/'RUN_PLAN.csv'))
        self.assertEqual(3*3*(99+1),900);self.assertEqual(900*2048,1843200)
    def test_no_execution_calls(self):
        for filename in ['audit.py','publish.py']:
            tree=ast.parse((Path(__file__).parent/filename).read_text())
            for n in ast.walk(tree):
                if isinstance(n,ast.Call):
                    name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else ''
                    self.assertNotIn(name,['minimize','AerSimulator','sample_counts','sample_memory','Sampler','reserve','claim'])
    def test_wide_regression_record(self):
        for g in ['G1','G2']:self.assertEqual(read(OUT/'regression'/(g+'.json'))['status'],'PASS')
    def test_resource_and_gate(self):
        for r in self.r:
            self.assertEqual(r['resources']['theoretical_statevector_bytes'],16*2**r['state']['qubits'])
            self.assertEqual(r['resources']['preparation']['CX'],0)
        self.assertEqual(read(OUT/'RESOURCE_GATE_SUMMARY.json')['stops'],0)

if __name__=='__main__':
    import io
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests))
    log=stream.getvalue();(OUT/'TEST_LOG.txt').write_text(log);print(log)
    dump('TEST_RESULTS.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),status='PASS' if result.wasSuccessful() else 'FAIL',scientific_execution=0))
    raise SystemExit(not result.wasSuccessful())
