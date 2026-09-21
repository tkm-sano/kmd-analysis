"""Offline-only tests. Synthetic callbacks are not optimizers or simulators."""
import copy
import tempfile
import unittest
from unittest.mock import patch
from .contract import *
from .worker import prepare
from .adapter import Adapter
from .ledger import Ledger,LedgerError,DuplicateRun,BudgetBlocked,atomic
from .results import summarize,schemas,aggregate_batch
from .execution import perform,supervised_run

class WorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=load();cls.runs=rows(FREEZE/'RUN_PLAN.csv');cls.prepared={r['condition']:prepare(r['run_id']) for r in cls.runs if r['repetition']=='0'}
        cls.p=cls.prepared[cls.runs[0]['condition']];cls.ids=[identity(cls.spec,plan(cls.spec,r['run_id'])) for r in cls.runs]
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)
    def ledger(self):
        l=Ledger(self.path/'ledger.json');l.initialize(self.spec,self.ids,synthetic=True);return l
    def ready(self):
        l=self.ledger();l.reserve_all(self.spec);cid=self.p['identity']['condition'];p=self.path/'sanity.json'
        atomic(p,dict(condition=cid,spec_hash=MANIFEST_SHA256,status='PASS',synthetic=True))
        l.transition_sanity(cid,'STARTED');l.transition_sanity(cid,'SUCCEEDED',dict(path=str(p),sha256=sha(p)));return l
    def callback(self,zero=False):
        self.calls=[]
        def backend(qc,shots,seed):
            self.calls.append(dict(qubits=qc.num_qubits,shots=shots,seed=seed));return {('0'*self.p['adapter'].N if zero else sorted(self.p['adapter'].optimal)[0]):shots}
        return backend
    @staticmethod
    def stub_optimizer(fun,x,**kw):fun(x);fun(x) # synthetic deterministic calls, no optimization

    def test_correct_spec(self):self.assertEqual(self.spec,load())
    def test_wrong_spec_hash(self):
        with patch('traffic_simulation.r24_vrptw_qaoa_worker.contract.sha',return_value='wrong'),self.assertRaises(Stop):load()
    def test_wrong_config(self):
        x=copy.deepcopy(self.spec);x['p']=2
        with self.assertRaises(Stop):validate(x)
    def test_wrong_condition(self):
        with self.assertRaises(Stop):Adapter('wrong')
    def test_wrong_run(self):
        with self.assertRaises(Stop):plan(self.spec,'wrong')
    def test_wrong_encoding(self):
        from . import adapter
        original=adapter.read
        def changed(p):
            x=original(p)
            if p.name=='SELECTED_ENCODING_SPEC.json':x['candidate']='wrong'
            return x
        with patch.object(adapter,'read',side_effect=changed),self.assertRaises(Stop):Adapter(self.p['identity']['condition'])
    def test_wrong_variable_order(self):
        from . import adapter
        original=adapter.build
        def changed(d):
            m=original(d);m['names']=m['names'][::-1];return m
        with patch.object(adapter,'build',side_effect=changed),self.assertRaisesRegex(Stop,'VARIABLE_ORDER'):Adapter(self.p['identity']['condition'])
    def test_wrong_qubo_hash(self):
        from . import adapter
        original=adapter.build
        def changed(d):
            m=original(d);m['h'][0]+=1;return m
        with patch.object(adapter,'build',side_effect=changed),self.assertRaisesRegex(Stop,'QUBO_HASH'):Adapter(self.p['identity']['condition'])
    def test_wrong_penalty_rule(self):
        from . import adapter
        original=adapter.build
        def changed(d):
            m=original(d);m['A']+=1;return m
        with patch.object(adapter,'build',side_effect=changed),self.assertRaises(Stop):Adapter(self.p['identity']['condition'])
    def test_identity_rejects_changed_repetition(self):
        r=plan(self.spec,self.runs[0]['run_id']);r['repetition']=2
        with self.assertRaises(Stop):identity(self.spec,r)
    def test_uniform_all_qubits(self):
        for p in self.prepared.values():self.assertEqual(p['logical'].count_ops()['h'],p['adapter'].N)
    def test_standard_x(self):
        for p in self.prepared.values():self.assertEqual(p['logical'].count_ops()['rx'],p['adapter'].N)
    def test_depth_p_one(self):self.assertEqual(self.spec['p'],1)
    def test_fixed_parameters(self):
        for p in self.prepared.values():self.assertEqual(p['plan']['initial_parameters'],[self.spec['parameters']['initial_alpha'],self.spec['parameters']['initial_beta']]);self.assertFalse(p['bound'].parameters)
    def test_seed_mapping_all21(self):
        for r in self.runs:self.assertEqual(plan(self.spec,r['run_id'])['seeds'],self.spec['seed_mapping'][int(r['repetition'])])
    def test_two_bit_classes(self):self.assertEqual({p['adapter'].N for p in self.prepared.values()},{16,20})
    def test_circuit_transpiled_exact(self):
        for p in self.prepared.values():self.assertEqual(p['resources']['expected_CX'],p['qc'].count_ops()['cx']);self.assertEqual(p['resources']['expected_depth'],p['qc'].depth())
    def test_valid_route_all_exact_authority_states(self):
        for p in self.prepared.values():
            for k in p['adapter'].feasible:self.assertTrue(p['adapter'].inspect(k)['overall_feasible'])
    def test_invalid_route(self):self.assertFalse(self.p['adapter'].inspect('1'*20)['overall_feasible'])
    def test_not_evaluable(self):self.assertEqual(self.p['adapter'].inspect('1'*20)['temporal_evaluability'],'NOT_EVALUABLE')
    def test_waiting(self):
        for p in self.prepared.values():
            if p['adapter'].condition['waiting_required']=='True':
                for k in p['adapter'].feasible:self.assertGreater(Fraction(p['adapter'].inspect(k)['waiting_seconds']),0)
    def test_hard_lateness(self):
        wide=self.p['adapter'];active=next(p['adapter'] for p in self.prepared.values() if p['adapter'].condition['TW_regime']=='MODERATE')
        rejected=wide.feasible-active.feasible;self.assertTrue(rejected)
        for k in rejected:self.assertFalse(active.inspect(k)['temporal']);self.assertFalse(active.inspect(k)['overall_feasible'])
    def test_depot_return_independent_validator(self):
        from traffic_simulation.validation.test_r24_vrptw import FrozenCases
        FrozenCases('test_all_ten_alternatives_exact_times_and_axes').test_all_ten_alternatives_exact_times_and_axes()
    def test_bitstring_length(self):
        with self.assertRaises(Stop):self.p['adapter'].inspect('0')
    def test_bitstring_nonbinary(self):
        with self.assertRaises(Stop):self.p['adapter'].inspect('x'*20)
    def test_frequency_not_unique_weighting(self):
        a=self.p['adapter'];m,_=summarize(a,{sorted(a.feasible)[0]:1,'0'*a.N:2047},2048);self.assertEqual(m['feasible_sample_rate'],1/2048)
    def test_zero_feasible_valid_result(self):
        a=self.p['adapter'];m,_=summarize(a,{'0'*a.N:2048},2048);self.assertEqual(m['feasible_count'],0);self.assertIsNone(m['feasible_waiting']['mean_seconds'])
    def test_wrong_shot_count(self):
        with self.assertRaises(Stop):summarize(self.p['adapter'],{'0'*20:1},2048)
    def test_nearest_full_bits(self):
        a=self.p['adapter'];k=sorted(a.feasible)[0];d=a.inspect(k);self.assertEqual(d['nearest_feasible_distance_or_null'],0)
    def test_energy_decomposition(self):
        for p in self.prepared.values():
            for k in ['0'*p['adapter'].N,'1'*p['adapter'].N,*sorted(p['adapter'].feasible)]:
                d=p['adapter'].inspect(k);self.assertAlmostEqual(d['base_objective']+sum(d['penalty_contributions'].values()),d['coefficient_energy'],places=5)
    def test_all_output_schemas(self):self.assertEqual(len(schemas()['csv']),6)
    def test_cap_2107(self):self.assertEqual(self.ledger().snapshot()['cap_total'],2107)
    def test_100_per_run(self):
        l=self.ledger();l.reserve_run(self.ids[0]);self.assertEqual(len(l.snapshot()['runs'][self.ids[0]['run_id']]['circuits']),100)
    def test_2100_scientific_7_sanity(self):
        l=self.ledger();l.reserve_all(self.spec);q=l.snapshot()['totals'];self.assertEqual((q['scientific_reserved'],q['sanity_reserved'],q['remaining_unallocated']),(2100,7,0))
    def test_duplicate_reservation(self):
        l=self.ledger();l.reserve_run(self.ids[0])
        with self.assertRaises(DuplicateRun):l.reserve_run(self.ids[0])
    def test_duplicate_claim(self):
        l=self.ledger();rid=self.ids[0]['run_id'];l.reserve_run(self.ids[0]);l.claim(rid)
        with self.assertRaises(DuplicateRun):l.claim(rid)
    def test_release_unused(self):
        l=self.ledger();rid=self.ids[0]['run_id'];l.reserve_run(self.ids[0]);l.claim(rid);l.release_training(rid);self.assertEqual(l.snapshot()['totals']['reserved'],1)
    def test_no_sanity_no_science(self):
        l=self.ledger();l.reserve_all(self.spec)
        with self.assertRaisesRegex(LedgerError,'SANITY'):l.order_gate(self.ids[0])
    def test_order_gate(self):
        l=self.ready()
        with self.assertRaisesRegex(LedgerError,'OUT_OF_ORDER'):l.order_gate(self.ids[1])
    def test_synthetic_end_to_end_idempotent(self):
        l=self.ready();backend=self.callback();r=perform(self.p,l,self.path/'run',backend,self.stub_optimizer,synthetic=True)
        self.assertTrue(r['synthetic']);self.assertEqual(len(self.calls),3)
        self.assertEqual(perform(self.p,l,self.path/'run',backend,self.stub_optimizer,synthetic=True),r);self.assertEqual(len(self.calls),3)
    def test_completed_tamper_no_resend(self):
        l=self.ready();backend=self.callback();perform(self.p,l,self.path/'run',backend,self.stub_optimizer,synthetic=True)
        atomic(self.path/'run'/'FINAL_RAW_COUNTS.json',{})
        with self.assertRaises(LedgerError):perform(self.p,l,self.path/'run',backend,self.stub_optimizer,synthetic=True)
        self.assertEqual(len(self.calls),3)
    def test_unknown_completion_no_retry(self):
        l=self.ready()
        def fail(*args):raise TimeoutError('synthetic unknown')
        with self.assertRaises(TimeoutError):perform(self.p,l,self.path/'run',fail,self.stub_optimizer,synthetic=True)
        self.assertEqual(l.snapshot()['totals']['unknown_counted'],1);self.assertTrue(l.snapshot()['halted'])
        with self.assertRaises((Stop,LedgerError)):perform(self.p,l,self.path/'run2',fail,self.stub_optimizer,synthetic=True)
    def test_external_99_cap(self):
        l=self.ready();backend=self.callback()
        def many(fun,x,**kw):
            for _ in range(105):fun(x)
        r=perform(self.p,l,self.path/'run',backend,many,synthetic=True);self.assertEqual(r['training_circuits'],99);self.assertEqual(len(self.calls),100)
    def test_exact_seed_sequence(self):
        l=self.ready();backend=self.callback();perform(self.p,l,self.path/'run',backend,self.stub_optimizer,synthetic=True)
        s=self.p['plan']['seeds'];self.assertEqual([c['seed'] for c in self.calls],s['training_simulator_seeds'][:2]+[s['final_simulator_seed']])
    def test_no_authorization(self):
        with self.assertRaises(Stop):supervised_run(self.runs[0]['run_id'],None)
    def test_no_auto_promotion(self):
        for p in self.prepared.values():self.assertFalse(p['scientific_ready']);self.assertEqual(p['status'],'OFFLINE_ACCEPTANCE_VALIDATED')
    def test_batch_empty_schema(self):
        r=aggregate_batch(self.runs[:3],[],{});self.assertFalse(r['complete']);self.assertEqual(len(r['missing']),3)
    def test_all21_offline_records(self):
        records=rows(OUT/'DRY_RUN_RESULTS.csv');self.assertEqual([r['run_id'] for r in records],[r['run_id'] for r in self.runs])
        self.assertTrue(all(r['status']=='PASS' and int(r['scientific_circuits'])==int(r['Aer'])==int(r['optimizer'])==0 for r in records))
    def test_all7_batch_records(self):
        records=rows(OUT/'BATCH_PLAN_VALIDATION.csv');self.assertEqual(len(records),7);self.assertTrue(all(r['status']=='PASS' and int(r['runs'])==3 for r in records))
    def test_no_live_ledger_consumption(self):
        evidence=read(OUT/'LEDGER_SIMULATION.json');self.assertTrue(evidence['production_ledger_unchanged']);self.assertEqual(evidence['real_consumption'],0)
    def test_manifest_tamper_no_resend(self):
        l=self.ready();backend=self.callback();perform(self.p,l,self.path/'run',backend,self.stub_optimizer,synthetic=True)
        atomic(self.path/'run'/'ARTIFACT_SHA256.json',{})
        with self.assertRaises(LedgerError):perform(self.p,l,self.path/'run',backend,self.stub_optimizer,synthetic=True)
        self.assertEqual(len(self.calls),3)
    def test_zero_feasible_pipeline_not_stop(self):
        l=self.ready();r=perform(self.p,l,self.path/'run',self.callback(zero=True),self.stub_optimizer,synthetic=True)
        self.assertEqual(r['metrics']['feasible_count'],0);self.assertEqual(r['status'],'SUCCEEDED');self.assertFalse(l.snapshot()['halted'])
    def test_optimizer_options_inherited(self):
        l=self.ready()
        def check(fun,x,**kw):
            self.assertEqual(kw,dict(method=self.spec['optimizer']['name'],options=self.spec['optimizer']['options']))
            self.assertEqual(x,self.p['plan']['initial_parameters']);fun(x)
        perform(self.p,l,self.path/'run',self.callback(),check,synthetic=True)
    def test_physical_gate_thresholds_unchanged(self):
        from traffic_simulation.r24_qaoa_resource_gate_redesign.gates import SPEC
        for k in ['process','psi','system_poll_seconds','process_poll_seconds','cgroup_headroom_bytes','host_available_min_bytes','cgroup_event_names']:
            self.assertEqual(self.spec['resource_gate'][k],SPEC[k])
    def test_resource_mismatch_stops(self):
        from . import worker
        original=worker.rows
        def changed(path):
            values=original(path)
            if path.name=='RESOURCE_SNAPSHOT.csv':
                for r in values:r['estimated_depth']='-1'
            return values
        with patch.object(worker,'rows',side_effect=changed),self.assertRaisesRegex(Stop,'CIRCUIT_RESOURCE'):prepare(self.runs[0]['run_id'])
    def test_ledger_cap_violation(self):
        l=self.ledger();s=l.snapshot();s['cap_total']=-1;s['totals']=l.summary(s)
        with self.assertRaises(BudgetBlocked):l.invariant(s)

from fractions import Fraction
