"""Finite-shot objective and actual operation ledger, without changing the AOA circuit."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter
from importlib.metadata import version
import numpy as np
from scipy.optimize import minimize
from qiskit import transpile
from kmd_toc.column_generation.aoa import PricingAOA
from kmd_toc.column_generation.models import reduced_cost
from kmd_toc.column_generation.backends import circuit_metadata
from .work import WorkLimit

def measured_minimize(objective,initial,config,ledger,call_id,restart):
    """Observe SciPy's actual last-x cache without altering its behavior."""
    from scipy.optimize import _cobyla_py
    from unittest.mock import patch
    original=_cobyla_py._prepare_scalar_function
    def prepare(*args,**kwargs):
        sf=original(*args,**kwargs) # initial evaluation occurs here and is counted by objective
        ledger.count('quantum_optimizer_initial_preparations')
        original_fun=sf.fun
        def fun(x):
            before=sf.nfev
            ledger.count('quantum_optimizer_value_requests')
            value=original_fun(x)
            if sf.nfev==before:
                ledger.count('quantum_optimizer_cache_hits')
                ledger.emit('optimizer_cache_hit',call_id=call_id,restart=restart,
                            consumed_training_shots=0,scope='SciPy ScalarFunction last-x cache, not a sampled evaluation')
            return value
        sf.fun=fun
        return sf
    with patch.object(_cobyla_py,'_prepare_scalar_function',prepare):
        return minimize(objective,initial,method='COBYLA',
                        options={'maxiter':config.max_evaluations,'tol':config.tolerance})

class FinitePricingAOA(PricingAOA):
    def __init__(self,instance,dual,config,ledger,call_id):
        self.ledger=ledger;self.call_id=call_id
        super().__init__(instance,dual,config)

    def run(self, native_depth=False):
        begin = perf_counter()
        c = self.config
        seed_stream = np.random.SeedSequence(c.solver_seed).spawn(c.restarts)
        histories, all_counts, routes = [], Counter(), set()
        feasible = improving = measured = 0
        reasons = Counter()
        max_infidelity = max_leakage = 0.0
        training_seconds = final_seconds = 0.0
        circuit_seconds = statevector_seconds = validation_seconds = sampling_seconds = decode_seconds = 0.0
        for restart, seed in enumerate(seed_stream):
            rng = np.random.default_rng(seed)
            initial = np.array([a for layer in range(1, c.p + 1)
                                for a in (.1 * layer / c.p, np.pi / 4 * (1 - layer / (c.p + 1)))])
            if restart:
                initial = rng.uniform(0, 1, 2 * c.p) * np.tile([2 * np.pi, np.pi], c.p)
            evaluations = []

            requested=0
            def objective(angles):
                nonlocal requested
                requested+=1
                self.ledger.count('quantum_objective_requests')
                if len(evaluations)>=c.max_evaluations:
                    self.ledger.emit('quantum_guard',call_id=self.call_id,restart=restart,requested=requested)
                    raise WorkLimit('AOA_EVALUATION_BUDGET')
                number=len(evaluations)+1
                record={'evaluation':number,'angles':np.asarray(angles).tolist(),'status':'STARTED'}
                evaluations.append(record)
                self.ledger.count('quantum_training_attempts')
                self.ledger.emit('training_evaluation_start',call_id=self.call_id,restart=restart,evaluation=number,
                                 planned_shots=c.train_shots,cache_hit=False)
                try:
                    self.ledger.count('quantum_training_tensor_calls')
                    probabilities=np.abs(self.tensor_state(angles))**2
                    probabilities/=probabilities.sum()
                    self.ledger.count('quantum_training_sampling_calls')
                    counts=rng.multinomial(c.train_shots,probabilities)
                    actual=int(counts.sum())
                    if actual!=c.train_shots:raise RuntimeError('TRAIN_SHOTS_MISMATCH')
                    self.ledger.count('quantum_training_shots',actual)
                    value=float(counts@self.energy/actual)
                    record.update(status='COMPLETE',sample_mean=value,actual_shots=actual)
                    self.ledger.count('quantum_training_successes')
                    self.ledger.emit('training_evaluation_end',call_id=self.call_id,restart=restart,
                                     evaluation=number,actual_shots=actual,sample_mean=value)
                    return value
                except BaseException as e:
                    self.ledger.count('quantum_training_failures');record.update(status='FAILED',error=str(e))
                    self.ledger.emit('training_evaluation_failed',call_id=self.call_id,restart=restart,
                                     evaluation=number,error=repr(e),actual_shots=record.get('actual_shots'))
                    raise

            started = perf_counter()
            try:
                optimization = measured_minimize(objective,initial,c,self.ledger,self.call_id,restart)
            except WorkLimit:
                # Defensive guard: preserve the best successfully evaluated angles.
                from types import SimpleNamespace
                completed=[e for e in evaluations if e['status']=='COMPLETE']
                if not completed:raise
                best=min(completed,key=lambda e:e['sample_mean'])
                optimization=SimpleNamespace(x=np.asarray(best['angles']),nfev=len(evaluations),success=False,
                                             message='WORK_BUDGET_REACHED: defensive objective guard')
            training_seconds += perf_counter() - started
            angles = optimization.x
            started = perf_counter()
            self.ledger.count('quantum_final_circuit_calls')
            self.ledger.emit('final_state_start',call_id=self.call_id,restart=restart)
            state, qc, construction, evolution = self.execution_state(angles)
            self.ledger.count('quantum_final_state_successes')
            circuit_seconds += construction
            statevector_seconds += evolution
            phase_start = perf_counter()
            self.ledger.count('quantum_validation_tensor_calls')
            tensor = self.tensor_state(angles)
            embedded = state.data[self.indices]
            fidelity = float(abs(np.vdot(tensor, embedded)) ** 2)
            leakage = max(0.0, float(1 - np.vdot(embedded, embedded).real))
            if abs(1 - fidelity) > 1e-8 or leakage > 1e-8:
                raise RuntimeError(f'{c.statevector_backend} / one-hot tensor evolution mismatch')
            max_infidelity = max(max_infidelity, abs(1 - fidelity))
            max_leakage = max(max_leakage, leakage)
            validation_seconds += perf_counter() - phase_start
            phase_start = perf_counter()
            state.seed(int(rng.integers(0, 2 ** 31)))
            self.ledger.count('quantum_final_sampling_calls')
            self.ledger.emit('final_sample_start',call_id=self.call_id,restart=restart,planned_shots=c.final_shots)
            counts = state.sample_counts(c.final_shots)
            actual=int(sum(counts.values()))
            if actual!=c.final_shots:raise RuntimeError('FINAL_SHOTS_MISMATCH')
            self.ledger.count('quantum_final_shots',actual)
            self.ledger.emit('final_sample_end',call_id=self.call_id,restart=restart,actual_shots=actual)
            sampling_seconds += perf_counter() - phase_start
            phase_start = perf_counter()
            for bits, count in counts.items():
                mask = int(bits, 2)
                all_counts[bits] += int(count)
                measured += int(count)
                if mask not in self.index_to_sequence:
                    reasons['ONE_HOT_VIOLATION'] += int(count)
                    continue
                candidates, reason = self.decode(self.index_to_sequence[mask])
                reasons[reason] += int(count)
                if reason == 'VALID':
                    feasible += int(count)
                    if any(reduced_cost(self.instance, r, self.dual[1:]) < -1e-7 for r in candidates):
                        improving += int(count)
                    routes.update(candidates)
            decode_seconds += perf_counter() - phase_start
            final_seconds += perf_counter() - started
            histories.append({'restart': restart, 'initial_angles': initial.tolist(),
                              'optimized_angles': angles.tolist(), 'nfev': int(optimization.nfev), 'objective_requests':requested, 'objective_callback_cache_hits':0, 'optimizer_wrapper_cache':'SciPy ScalarFunction last-x memoization; measured in ledger separately from objective callbacks and optimizer nfev', 'training_initial_evaluation_included':True, 'gradient_evaluations':0,
                              'optimizer_success': bool(optimization.success),
                              'optimizer_message': str(optimization.message),
                              'evaluations': evaluations, 'qiskit_counts': dict(counts)})
        depth, gates = circuit_metadata(qc, c.statevector_backend)
        native = None
        diagnostic_seconds = 0.0
        if native_depth:
            diagnostic_start = perf_counter()
            reference = qc if c.statevector_backend == 'qiskit' else self.circuit(angles)
            native_qc = transpile(reference, basis_gates=['rz', 'sx', 'x', 'cx'],
                                  optimization_level=0, seed_transpiler=c.solver_seed)
            native = {'depth': native_qc.depth(), 'gates': dict(native_qc.count_ops()),
                      'basis': ['rz', 'sx', 'x', 'cx'], 'connectivity': 'all_to_all_no_hardware'}
            diagnostic_seconds = perf_counter() - diagnostic_start
        return {'routes': [list(r.customers) for r in sorted(routes)],
                'config': asdict(c), 'qubits': self.q, 'logical_depth': depth,
                'logical_gates': gates, 'logical_gate_names_backend': c.statevector_backend,
                'logical_depth_scope': 'exact dense XY block counts as one logical gate',
                'native_circuit': native, 'native_depth_diagnostic_seconds': diagnostic_seconds,
                'raw_statevector_bytes': 16 * (1 << self.q),
                'one_hot_basis_states': len(self.assignments),
                'measured_shots': measured, 'feasible_shots': feasible,
                'improving_shots': improving, 'feasible_rate': feasible / measured,
                'improving_rate': improving / measured, 'reason_counts': dict(reasons),
                'qiskit_tensor_max_infidelity': max_infidelity,
                'qiskit_one_hot_max_leakage': max_leakage,
                'training_seconds': training_seconds, 'final_processing_seconds': final_seconds,
                'circuit_build_seconds': circuit_seconds, 'statevector_seconds': statevector_seconds,
                'state_validation_seconds': validation_seconds, 'sampling_seconds': sampling_seconds,
                'decode_seconds': decode_seconds,
                'qiskit_seconds': final_seconds,
                'qiskit_seconds_scope': 'legacy alias of final_processing_seconds; see statevector_backend',
                'total_seconds': perf_counter() - begin, 'history': histories,
                'statevector_backend': c.statevector_backend,
                'statevector_backend_version': version(c.statevector_backend),
                'sampling_backend': 'qiskit.quantum_info.Statevector.sample_counts',
                'sampling_backend_version': version('qiskit'),
                'backend': ('Qiskit Statevector final; exact one-hot tensor + finite-shot training'
                            if c.statevector_backend == 'qiskit' else
                            'Qulacs Statevector final; Qiskit sampling; exact one-hot tensor + finite-shot training'),
                'internal_depot_handling': 'split at depot; free-fleet reference only'}
