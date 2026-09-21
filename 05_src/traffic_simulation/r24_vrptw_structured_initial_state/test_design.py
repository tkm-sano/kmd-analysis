"""Deterministic structural/negative tests; no scientific execution."""
import ast, copy, inspect, unittest
from unittest.mock import patch
from .construction import construct,validate_state,preparation
from .common import *
from .validate import circuit_signature
from traffic_simulation.r24_qaoa_initial_state_cross_condition_reproducibility_spec.design import structured,route_words

class DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=[read(OUT/'conditions'/(r['condition']+'.json')) for r in rows(FREEZE/'SCIENTIFIC_CONDITION_SET.csv')]
    def test_WIDE_CVRP_regression(self):
        for r in self.records[:2]:
            self.assertEqual(r['wide_regression']['status'],'PASS')
            self.assertEqual(min(route_words(r['inputs']['n'],r['inputs']['m'])),r['state']['route_word'])
            self.assertEqual(structured(r['inputs']['n'],r['inputs']['m']),(r['state']['route_qubits'],r['state']['route_word']))
    def test_active_variable_order(self):
        r=self.records[2];self.assertEqual(construct(r['inputs']),r['state'])
        bad=copy.deepcopy(r['inputs']);bad['variable_order'][0],bad['variable_order'][1]=bad['variable_order'][1],bad['variable_order'][0]
        with self.assertRaises(ValueError):construct(bad)
    def test_normalization(self):
        for r in self.records:self.assertTrue(validate_state(r['state']))
    def test_deterministic_regeneration(self):
        for r in self.records:
            self.assertEqual(construct(r['inputs']),construct(r['inputs']))
            self.assertEqual(circuit_signature(preparation(construct(r['inputs']))),circuit_signature(preparation(r['state'])))
    def test_leakage_negative_boundary(self):
        for key in ['optimal_bitstring','feasible_states','exact_routes','MILP','demands','costs','QAOA_outcomes','road_routes','waiting_label']:
            with self.assertRaises(ValueError):construct({**self.records[0]['inputs'],key:[]})
    def test_construction_has_no_file_access(self):
        with patch('builtins.open',side_effect=AssertionError('file read in generation')),patch.object(Path,'read_text',side_effect=AssertionError('file read in generation')):
            self.assertEqual(construct(self.records[0]['inputs']),self.records[0]['state'])
    def test_same_QUBO_controls(self):
        for group in [(0,5),(1,6),(2,3,4)]:
            a=self.records[group[0]]
            for i in group[1:]:
                b=self.records[i];self.assertEqual(a['state'],b['state']);self.assertEqual(a['variable_order_hash'],b['variable_order_hash'])
                self.assertEqual(circuit_signature(preparation(a['state'])),circuit_signature(preparation(b['state'])))
    def test_temporal_ancilla_handling(self):
        for r in self.records:self.assertEqual(r['temporal_ancillas'],0)
        inp=copy.deepcopy(self.records[0]['inputs']);inp['variable_order'].append('and_0_0_1')
        with self.assertRaises(ValueError):construct(inp)
    def test_malformed_state_negative(self):
        for change in [dict(amplitude=float('nan')),dict(amplitude=float('inf')),dict(amplitude=1.),dict(support=[1,1]),dict(support=[-1]),dict(support=[1<<20])]:
            with self.assertRaises(ValueError):validate_state({**self.records[0]['state'],**change})
    def test_temporal_violation_not_filtered(self):
        r=self.records[2];s=r['metrics'][1]
        self.assertEqual(s['no_good_violated_mass'],1.)
        self.assertEqual(s['overall_feasible_mass'],0.)
        self.assertEqual(r['state']['route_word'],self.records[0]['state']['route_word'])
    def test_probabilities_and_distance_denominators(self):
        for r in self.records:
            for m in r['metrics']:
                self.assertEqual(sum(m['distance_histogram']),m['support_size'])
                self.assertAlmostEqual(m['evaluable_mass']+m['NOT_EVALUABLE_mass'],1.)
                self.assertAlmostEqual(m['no_good_mass']+m['no_good_violated_mass'],1.)
                self.assertAlmostEqual(m['distance_le_0_mass'],m['overall_feasible_mass'])
                self.assertLessEqual(m['optimal_mass'],m['overall_feasible_mass'])
    def test_saved_statevector_and_QAOA_layers(self):
        for r in self.records[:3]:
            c=r['circuits'];self.assertEqual(c['cost_mixer_identity'],'PASS')
            for sv in c['sanity']:
                self.assertEqual(sv['shots'],0);self.assertEqual(sv['Aer_calls'],0);self.assertAlmostEqual(sv['norm'],1.)
    def test_no_scientific_API(self):
        module=Path(__file__).with_name('validate.py');tree=ast.parse(module.read_text())
        forbidden={'sample_counts','sample_memory','measure','measure_all','minimize','AerSimulator','COBYLA','Sampler'}
        called=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
                called.append(name)
        self.assertFalse(forbidden&set(called))

def main():
    import io,time
    start=time.monotonic();stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DesignTests))
    (OUT/'TEST_LOG.txt').write_text(stream.getvalue())
    dump('TEST_RESULTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests_run=result.testsRun,seconds=time.monotonic()-start,failures=[str(x) for x in result.failures+result.errors],scientific_executions=0))
    print(stream.getvalue());assert result.wasSuccessful()
if __name__=='__main__':main()
