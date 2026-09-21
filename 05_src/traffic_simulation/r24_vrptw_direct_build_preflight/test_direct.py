"""Direct path negative tests and complete affected legacy suites, zero backend."""
import unittest,io,ast,inspect,copy
from unittest.mock import patch
from contextlib import ExitStack
from .audit import *
from traffic_simulation.r24_vrptw_structured_worker import execution
from traffic_simulation.r24_vrptw_structured_worker.preflight import manifest_entry
from traffic_simulation.r24_vrptw_structured_initial_state.construction import construct
from traffic_simulation.r24_vrptw_qaoa_worker import contract as uc
from traffic_simulation.r24_vrptw_qaoa_worker.adapter import Adapter

class DirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plans=rows(SPEC/'RUN_PLAN.csv');cls.p=prepare(cls.plans[0]['run_id'])
    def test_no_uniform_factories(self):
        with NoUniform() as g:
            for r in self.plans:prepare(r['run_id'])
            self.assertEqual(g.full.call_count,0);self.assertEqual(g.initial.call_count,0)
    def test_no_uniform_import_or_call(self):
        from traffic_simulation.r24_vrptw_structured_worker import worker
        s=inspect.getsource(worker)
        self.assertNotIn('uniform_prepare',s);self.assertNotIn("r24_vrptw_qaoa_worker.worker",s)
        self.assertNotIn('build_uniform_initial_state',s)
    def test_shared_body_single_implementation(self):
        from traffic_simulation.r24_vrptw_structured_worker import worker
        self.assertIs(worker.shared,uniform.shared);self.assertIs(worker.shared.build_body,shared.build_body)
        for module in [worker,uniform]:
            code=next(n for n in ast.parse(Path(module.__file__).read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='prepare');calls=[n.func.attr for n in ast.walk(code) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
            self.assertEqual(calls.count('build_body'),1);self.assertFalse({'rz','cx','rx'}&set(calls))
    def test_all_body_DAGs(self):
        for r in rows(SPEC/'RUN_PLAN.csv'):
            a=body_audit(prepare(r['run_id']));self.assertTrue(a['body_DAG_equivalence'])
    def test_parameter_order(self):
        self.assertEqual([p.name for p in self.p['qc'].parameters],['beta','gamma'])
        self.assertEqual(self.p['plan']['initial_parameters'],[.5262887849165184,.37])
    def test_measurement(self):self.assertEqual(self.p['injection_audit']['measurement'],[(i,i) for i in range(self.p['adapter'].N)])
    def test_registers(self):
        s=self.p['state'];self.assertEqual(s['h_qubits'],list(range(s['route_qubits'],s['qubits'])))
    def test_candidate_inputs(self):
        self.assertEqual(set(self.p['construction_inputs']),{'n','m','variable_order'})
        for key in ['no_good','temporal','Uniform_results','feasible','optimal','energy']:
            with self.assertRaises(ValueError):construct(dict(self.p['construction_inputs'],**{key:1}))
    def test_reproduction(self):
        for r in rows(OUT/'STATE_REPRODUCTION_AUDIT.csv'):
            self.assertAlmostEqual(float(r['fidelity']),1);self.assertLessEqual(float(r['max_amplitude_difference']),1e-12);self.assertLess(float(r['probability_max_error']),1e-12)
    def test_support_uniqueness(self):
        for r in rows(OUT/'STATE_REPRODUCTION_AUDIT.csv'):self.assertEqual(int(r['duplicate_support']),0);self.assertEqual(int(r['support_mismatch']),0)
    def test_active_TW(self):
        r=next(r for r in rows(OUT/'STATE_REPRODUCTION_AUDIT.csv') if r['group']=='G3')
        self.assertEqual(float(r['temporal_valid_mass']),0);self.assertEqual(float(r['no_good_violation_mass']),1);self.assertEqual(float(r['initial_feasible_mass']),0)
    def test_same_QUBO(self):self.assertTrue(all(r['status']=='PASS' for r in rows(OUT/'WAITING_CONTROL_VALIDATION.csv')))
    def test_frozen_config(self):
        c,s=frozen();self.assertEqual(c['inherited_settings'],{k:s[k] for k in c['inherited_settings']})
    def test_projection(self):
        p=projection();self.assertEqual(p['new_max_circuits'],900);self.assertEqual(p['new_max_shots'],1843200);self.assertEqual(p['projected_scientific'],1263)
    def test_manifest_determinism(self):
        m=read(OUT/'PREFLIGHT_MANIFEST.json')
        for r in m['runs']:self.assertEqual(manifest_entry(prepare(r['run_id'])),r)
    def test_default_execution_block(self):
        from traffic_simulation.r24_vrptw_structured_worker.guard import ExecutionForbidden
        with self.assertRaises(ExecutionForbidden):execution.supervised_run(self.plans[0]['run_id'])
    def test_zero_counters(self):
        c=read(OUT/'EXECUTION_COUNTS.json')
        for k in ['Uniform_full_factory','Uniform_initial_factory','backend','sampler','optimizer_evaluations','scientific_circuits','scientific_shots','Aer_sampling','ledger_increment','reservations']:self.assertEqual(c[k],0)
    def test_bad_order_rejected(self):
        d=copy.deepcopy(self.p['construction_inputs']);d['variable_order'].reverse()
        with self.assertRaises(ValueError):construct(d)
    def test_initial_state_has_no_reference_dependency(self):
        d=self.p['construction_inputs']
        with patch('builtins.open',side_effect=AssertionError('construction I/O')),patch.object(Path,'read_text',side_effect=AssertionError('construction I/O')):
            self.assertEqual(initial_state(**d)[0],self.p['state'])
    def test_shared_body_no_initial_operations(self):
        body,*_=shared.build_body(self.p['adapter'].model)
        self.assertFalse({'h','x','initialize','state_preparation'}&set(body.count_ops()))
    def test_no_pending_output(self):
        for r in self.plans:self.assertFalse((ROOT/r['future_output']).exists())
    def test_active_gate_supersession(self):self.assertEqual(execution.ACTIVE_PREFLIGHT,OUT)


def archived_uniform_fixture(run_id,spec=None,check_environment=True):
    """Legacy tests get archived circuits, not a regenerated Uniform factory.
    Synthetic callbacks only inspect/bind; their 'measured' input needs no physical
    measurement because no backend exists. Scientific measurement is audited separately.
    """
    spec=uc.load() if spec is None else spec;run=uc.plan(spec,run_id);ad=Adapter(run['condition']);qc=load_archive(run_id);bound=load_archive(run_id,'fixed_parameters.qpy')
    gamma=next(x for x in qc.parameters if x.name=='gamma');beta=next(x for x in qc.parameters if x.name=='beta')
    actual=dict(qubits=ad.N,interactions=int(np.count_nonzero(ad.model['J'])),expected_CX=int(qc.count_ops().get('cx',0)),expected_depth=qc.depth(),raw_statevector_bytes=16*2**ad.N,planned_memory_bytes=64*2**ad.N)
    expected=next(x for x in uniform.rows(uc.FREEZE/'RESOURCE_SNAPSHOT.csv') if x['condition']==run['condition'])
    for k,f in {'qubits':'qubits','interactions':'interactions','expected_CX':'estimated_CX','expected_depth':'estimated_depth','raw_statevector_bytes':'raw_statevector_bytes','planned_memory_bytes':'planned_memory_bytes'}.items():uc.require(actual[k]==int(expected[f]),k,'CIRCUIT_RESOURCE_MISMATCH')
    return dict(spec=spec,plan=run,identity=uc.identity(spec,run),adapter=ad,logical=qc,qc=qc,measured=qc,bound=bound,gamma=gamma,beta=beta,resources=actual,status='OFFLINE_ACCEPTANCE_VALIDATED',scientific_ready=False)


def main():
    from traffic_simulation.r24_vrptw_structured_worker.test_preflight import PreflightTests
    from traffic_simulation.r24_vrptw_structured_initial_state.test_design import DesignTests
    from traffic_simulation.r24_vrptw_structured_initial_state_audit.tests import AuditTests
    from traffic_simulation.r24_vrptw_qaoa_worker import test_worker as legacy_tests
    reports=[];stream=io.StringIO()
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(t) for t in [DirectTests,PreflightTests,DesignTests,AuditTests])
    with ZeroShotGuard() as guard,NoUniform() as nou:
        r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        reports.append(dict(suite='direct plus complete Structured v1/v2/v3 suites',tests=r.testsRun,status='PASS' if r.wasSuccessful() else 'FAIL',failures=[str(x) for x in r.failures+r.errors],Uniform_full=nou.full.call_count,Uniform_initial=nou.initial.call_count,expected_guard_negative_rejections=len(guard.attempts)))
    # All56 Standard tests unchanged; isolate synthetic fixtures from scientific sources.
    from qiskit_aer import AerSimulator,Aer
    from qiskit.primitives import StatevectorSampler
    from qiskit_aer.primitives import Sampler,SamplerV2
    import scipy.optimize
    from qiskit.quantum_info import Statevector
    with ExitStack() as stack,NoUniform() as nou:
        denied=[]
        for obj,name in [(AerSimulator,'run'),(StatevectorSampler,'run'),(Sampler,'run'),(SamplerV2,'run'),(scipy.optimize,'minimize'),(Statevector,'from_instruction')]:denied.append(stack.enter_context(patch.object(obj,name,side_effect=AssertionError('SCIENTIFIC_API_FORBIDDEN'))))
        stack.enter_context(patch.object(legacy_tests,'prepare',side_effect=archived_uniform_fixture))
        r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(legacy_tests.WorkerTests))
        reports.append(dict(suite='complete Standard worker suite; archived-QPY fixture',tests=r.testsRun,status='PASS' if r.wasSuccessful() and all(x.call_count==0 for x in denied) else 'FAIL',failures=[str(x) for x in r.failures+r.errors],Uniform_full=nou.full.call_count,Uniform_initial=nou.initial.call_count,real_backend_optimizer_calls=sum(x.call_count for x in denied),fixture='Saved Uniform QPY loaded without reconstruction; synthetic callbacks and temporary synthetic ledgers only. No actual reservation/consumption.'))
    (OUT/'TEST_RESULTS.txt').write_text(stream.getvalue());print(stream.getvalue())
    dump('TEST_RESULTS.json',dict(status='PASS' if all(x['status']=='PASS' and x['Uniform_full']==x['Uniform_initial']==0 for x in reports) else 'FAIL',tests=sum(x['tests'] for x in reports),suites=reports,skipped=0,scientific_circuits=0,scientific_shots=0,Uniform_factories=0))
    if read(OUT/'TEST_RESULTS.json')['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
