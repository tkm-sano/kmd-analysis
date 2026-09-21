"""Zero-shot integration and negative acceptance tests."""
import unittest,copy,inspect,ast,io
from unittest.mock import patch
from .contract import *
from .worker import prepare,initial_state,state_digest
from .guard import ZeroShotGuard,ExecutionForbidden
from .ledger import projection,DryLedger,Ledger,LedgerError,BudgetBlocked
from .execution import supervised_run,wired,original,ORIGINAL_PERFORM
from .preflight import manifest_entry,dump
from traffic_simulation.r24_vrptw_structured_initial_state.construction import construct

class PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans=rows(SPEC/'RUN_PLAN.csv');cls.p=prepare(cls.plans[0]['run_id']);cls.manifest=read(OUT/'PREFLIGHT_MANIFEST.json')
    def dry(self):
        l=DryLedger();ident=run_identity(self.plans[0]['run_id']);l.reserve_run(ident);return l,ident
    def test_01_Candidate_A_worker(self):
        old=read(DESIGN/'conditions'/(self.p['plan']['condition']+'.json'));self.assertEqual(self.p['state'],old['state'])
    def test_02_input_allowlist(self):
        self.assertEqual(set(self.p['construction_inputs']),{'n','m','variable_order'})
        for name in ['feasible','optimal','energy','temporal_valid','no_good','samples']:
            with self.assertRaises(ValueError):construct(dict(self.p['construction_inputs'],**{name:1}))
    def test_03_variable_order(self):self.assertEqual(self.p['construction_inputs']['variable_order'],self.p['adapter'].order)
    def test_04_QUBO_hash(self):self.assertEqual(self.p['identity']['qubo_hash'],self.plans[0]['QUBO_hash'])
    def test_05_state_fidelity(self):
        for r in rows(OUT/'STATE_REPRODUCTION_AUDIT.csv'):
            self.assertAlmostEqual(float(r['fidelity']),1);self.assertLess(float(r['max_amplitude_difference']),1e-12);self.assertEqual(int(r['support_mismatch']),0)
    def test_06_same_QUBO_state(self):
        for r in rows(OFFLINE/'QUBO_GROUPS.csv'):
            old=read(DESIGN/'conditions'/(r['condition']+'.json'));representative=read(OFFLINE/'groups'/(r['group']+'.json'));self.assertEqual(construct(old['inputs']),representative['state'])
    def test_07_leakage_boundary(self):
        tree=ast.parse(inspect.getsource(initial_state));self.assertEqual({x.id for x in ast.walk(tree) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Load)},{'n','m','variable_order','dict','list','inputs','construct'})
    def test_08_Uniform_execution_blocked(self):
        with self.assertRaises(ExecutionForbidden):original.supervised_run('anything',{})
    def test_09_backend_blocked(self):
        from qiskit_aer import AerSimulator
        with self.assertRaises(ExecutionForbidden):AerSimulator().run(None,shots=2048)
    def test_10_sampler_blocked(self):
        from qiskit.primitives import StatevectorSampler
        with self.assertRaises(ExecutionForbidden):StatevectorSampler().run([])
    def test_11_optimizer_blocked(self):
        from scipy.optimize import minimize
        with self.assertRaises(ExecutionForbidden):minimize(lambda x:0,[0,0],method='COBYLA')
    def test_12_scientific_pipeline_blocked(self):
        with self.assertRaises(ExecutionForbidden):original.perform(None,None,None,None,None)
    def test_13_persistent_ledger_blocked(self):
        from traffic_simulation.r24_qaoa_initial_state_cross_condition_worker.ledger import Ledger as Parent
        with self.assertRaises(ExecutionForbidden):Parent('/unreachable').commit({},'TEST',None,{},'')
    def test_14_projection_deterministic(self):self.assertEqual(projection(),projection())
    def test_15_projected_max(self):
        p=projection();self.assertEqual(p['new_max_circuits'],900);self.assertEqual(p['new_max_shots'],1843200);self.assertEqual(p['projected_scientific'],1263);self.assertLessEqual(p['projected_shots'],p['caps']['shots'])
    def test_16_nine_runs(self):
        runs=self.manifest['runs'];self.assertEqual(len(runs),9);self.assertEqual(len({r['run_id'] for r in runs}),9)
        for group in ['G1','G2','G3']:self.assertEqual([r['repetition'] for r in runs if r['group']==group],[0,1,2])
    def test_17_active_TW_unchanged(self):
        r=read(OFFLINE/'groups/G3.json');self.assertEqual(r['metrics'][1]['temporal_mass'],0);self.assertEqual(r['metrics'][1]['no_good_violated_mass'],1)
        old=read(DESIGN/'conditions'/(r['condition']+'.json'));self.assertEqual(construct(old['inputs']),r['state'])
    def test_18_protected_freeze(self):
        c,s=frozen();self.assertEqual(c['inherited_settings'],{k:s[k] for k in c['inherited_settings']})
    def test_19_manifest_regeneration(self):
        self.assertEqual(manifest_entry(prepare(self.plans[0]['run_id'])),self.manifest['runs'][0])
    def test_20_zero_actual_counts(self):
        r=read(OUT/'PREFLIGHT_EXECUTION_COUNTS.json')
        for k in ['Uniform_execution','scientific_circuits','scientific_shots','optimizer_scientific_evaluations','Aer_sampling_calls','new_seeds','actual_ledger_mutations']:self.assertEqual(r[k],0)
    def test_21_default_launch_guard(self):
        with self.assertRaises(ExecutionForbidden):supervised_run(self.plans[0]['run_id'])
    def test_22_explicit_authorization_required(self):
        with self.assertRaises(Stop):supervised_run(self.plans[0]['run_id'],{},preflight=False)
    def test_23_claim_no_consumption(self):
        l,i=self.dry();r=l.snapshot()['runs'][i['run_id']]['reservation'];l.claim_reservation(r['reservation_id'],r['context']);self.assertEqual(l.snapshot()['totals']['consumed_new'],0)
        with self.assertRaises(LedgerError):l.claim_reservation(r['reservation_id'],r['context'])
    def test_24_duplicate_reservation(self):
        l,i=self.dry()
        with self.assertRaises(LedgerError):l.reserve_run(i)
    def test_25_unknown_counting_model(self):
        l,i=self.dry();rid=i['run_id'];l.claim(rid);l.transition(rid,'training',0,'STARTED');l.transition(rid,'training',0,'UNKNOWN_COUNTED');l.release_training(rid)
        q=l.snapshot()['totals'];self.assertEqual(q['consumed_new'],1);self.assertEqual(q['unknown_counted'],1);self.assertTrue(l.snapshot()['halted'])
        with self.assertRaises(LedgerError):l.transition(rid,'training',0,'STARTED')
    def test_26_projection_exhaustion_negative(self):
        l,i=self.dry();s=l.snapshot();s['historical']['scientific_consumed']=2099;s['historical']['consumed']=2106;s['totals']=Ledger.summary(s)
        with self.assertRaises(BudgetBlocked):Ledger.invariant(s)
    def test_27_future_batch_blocked(self):
        l=DryLedger()
        with self.assertRaises(LedgerError):l.reserve_run(run_identity(self.plans[3]['run_id']))
    def test_28_wrong_seed_negative(self):
        from . import contract
        real=contract.rows
        def wrong(path):
            r=real(path)
            if path==SPEC/'RUN_PLAN.csv':r[0]['seed_mapping_sha256']='tampered'
            return r
        with patch.object(contract,'rows',side_effect=wrong),self.assertRaises(Stop):run_plan(self.plans[0]['run_id'])
    def test_29_state_hash_serialization_authority(self):self.assertEqual(state_digest(self.p['state']),self.plans[0]['preparation_state_hash'])
    def test_30_measurement_endian(self):
        self.assertEqual(self.p['injection_audit']['measurement'],[(i,i) for i in range(self.p['adapter'].N)])
        for i in range(self.p['adapter'].N):self.assertEqual(self.p['adapter'].bits(format(1<<i,f"0{self.p['adapter'].N}b")).tolist(),[int(j==i) for j in range(self.p['adapter'].N)])
    def test_31_supervisor_reuse(self):
        f,source,changes=wired();self.assertEqual(f.__globals__['perform'].__code__,ORIGINAL_PERFORM.__code__);self.assertEqual(len(changes),4)
        self.assertIn('preflight_gate(run_identity(run_id))',source);self.assertIn('from .worker import prepare',source)
    def test_32_binding_offline_identity(self):self.assertFalse(self.p['bound'].parameters);self.assertEqual(self.p['qc'].count_ops().get('cx'),198)
    def test_33_source_code_no_new_optimizer(self):
        tree=ast.parse(inspect.getsource(initial_state));self.assertFalse(any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(tree)))
    def test_34_no_future_output_created(self):
        for r in self.plans:self.assertFalse((ROOT/r['future_output']).exists())


    def test_35_aggregation_reuses_arithmetic(self):
        from .results import aggregate_batch,summarize,save,standard
        self.assertEqual(aggregate_batch.__code__,standard.aggregate_batch.__code__)
        self.assertIs(summarize,standard.summarize);self.assertIs(save,standard.save)
        plans=[run_plan(r['run_id'])[0] for r in self.plans[:3]]
        a=aggregate_batch(plans,[],{});self.assertFalse(a['complete']);self.assertEqual(a['total_circuits'],0)


def main():
    from traffic_simulation.r24_vrptw_structured_initial_state.test_design import DesignTests
    from traffic_simulation.r24_vrptw_qaoa_worker.test_worker import WorkerTests
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(PreflightTests),unittest.defaultTestLoader.loadTestsFromTestCase(DesignTests)])
    safe=['test_correct_spec','test_wrong_config','test_wrong_condition','test_wrong_run','test_wrong_encoding','test_wrong_variable_order','test_wrong_qubo_hash','test_wrong_penalty_rule','test_fixed_parameters','test_seed_mapping_all21','test_circuit_transpiled_exact','test_optimizer_options_inherited','test_physical_gate_thresholds_unchanged']
    # optimizer_options_inherited uses a synthetic perform path; exclude it here.
    safe.remove('test_optimizer_options_inherited')
    suite.addTests(WorkerTests(x) for x in safe)
    stream=io.StringIO()
    with ZeroShotGuard() as guard:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (OUT/'TEST_RESULTS.txt').write_text(stream.getvalue());print(stream.getvalue())
    dump('TEST_RESULTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=[str(x) for x in result.failures+result.errors],guard_expected_negative_rejections=guard.attempts,scientific_calls=0))
    if not result.wasSuccessful():raise SystemExit(1)

if __name__=='__main__':main()
