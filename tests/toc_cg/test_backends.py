"""Backend equivalence, sampling parity, optional loading and audit timing."""
from dataclasses import replace
import numpy as np
import pytest
from qiskit.quantum_info import Statevector
from kmd_toc.column_generation.aoa import PricingAOA, AOAConfig
from kmd_toc.column_generation.models import Instance
from kmd_toc.column_generation import backends


def problem(nodes):
    distance = np.array([[0. if i == j else .1 + ((7*i + 3*j) % 11) / 10
                          for j in range(nodes)] for i in range(nodes)])
    return Instance('backend_contract', distance, (0,) + (1,) * (nodes - 1), 2)


@pytest.mark.parametrize('name', ['quri', 'auto', None, False, []])
def test_no_unknown_or_automatic_backend(name):
    with pytest.raises(ValueError, match='statevector_backend'):
        AOAConfig(statevector_backend=name)


def test_qiskit_default_does_not_require_qulacs(monkeypatch):
    original = backends.importlib.import_module
    def load(name, *args):
        if name.startswith('qulacs'):
            raise AssertionError('Default path loaded optional Qulacs')
        return original(name, *args)
    monkeypatch.setattr(backends.importlib, 'import_module', load)
    engine = PricingAOA(problem(3), [.8, 1.1], AOAConfig(slots=3, p=1))
    assert engine.config.statevector_backend == 'qiskit'
    engine.execution_state([.17, .41])


def test_missing_qulacs_is_explicit_without_fallback(monkeypatch):
    original = backends.importlib.import_module
    def load(name, *args):
        if name.startswith('qulacs'):
            raise ImportError('synthetic unavailable optional module')
        return original(name, *args)
    monkeypatch.setattr(backends.importlib, 'import_module', load)
    with pytest.raises(RuntimeError, match='no backend fallback') as exc:
        PricingAOA(problem(3), [.8, 1.1], AOAConfig(statevector_backend='qulacs'))
    assert isinstance(exc.value.__cause__, ImportError)


@pytest.mark.parametrize('nodes,slots,fixed,p', [(2, 2, True, 1), (3, 3, True, 2),
                                                (4, 4, True, 3), (3, 2, False, 2)])
def test_full_state_probabilities_energy_and_bit_order(nodes, slots, fixed, p):
    pytest.importorskip('qulacs')
    cfg = AOAConfig(slots=slots, p=p, fixed_depot=fixed)
    native = PricingAOA(problem(nodes), [i*.37 for i in range(1, nodes)], cfg)
    other = PricingAOA(native.instance, native.dual[1:], replace(cfg, statevector_backend='qulacs'))
    angles = np.random.default_rng(71).uniform(.1, .9, 2*p)
    # The public reference circuit remains Qiskit for either backend.
    expected = Statevector.from_instruction(other.circuit(angles)).data
    actual, circuit, build_s, evolution_s = other.execution_state(angles)
    overlap = np.vdot(expected, actual.data)
    aligned = actual.data * np.conj(overlap / abs(overlap))
    assert abs(1 - abs(overlap)**2) < 1e-10
    assert np.max(np.abs(expected - aligned)) < 1e-10
    assert np.abs(abs(expected)**2 - abs(actual.data)**2).sum() < 1e-10
    energy = np.array([native.polynomial.value(mask) for mask in range(1 << native.q)])
    assert float(abs(expected)**2 @ energy) == pytest.approx(float(abs(actual.data)**2 @ energy), abs=1e-9)
    assert build_s >= 0 and evolution_s >= 0
    assert backends.circuit_metadata(circuit, 'qulacs')[0] == native.circuit(angles).depth()


@pytest.mark.parametrize('restarts', [1, 2])
def test_training_sampling_routes_and_all_restart_accounting(restarts):
    pytest.importorskip('qulacs')
    cfg = AOAConfig(slots=3, p=2, max_evaluations=35, restarts=restarts,
                    train_shots=1000, final_shots=4096, solver_seed=1101)
    reference = PricingAOA(problem(3), [.8, 1.1], cfg).run()
    result = PricingAOA(problem(3), [.8, 1.1], replace(cfg, statevector_backend='qulacs')).run()
    assert result['history'] == reference['history']
    for key in ['routes', 'feasible_shots', 'improving_shots', 'reason_counts', 'logical_depth']:
        assert result[key] == reference[key]
    assert result['measured_shots'] == restarts * 4096
    assert result['statevector_backend'] == 'qulacs'
    assert result['statevector_backend_version']
    assert result['sampling_backend'].endswith('Statevector.sample_counts')
    assert result['qiskit_seconds'] == result['final_processing_seconds']
    assert result['final_processing_seconds'] >= sum(result[k] for k in
        ['circuit_build_seconds', 'statevector_seconds', 'state_validation_seconds', 'sampling_seconds', 'decode_seconds'])
    assert result['total_seconds'] >= result['training_seconds'] + result['final_processing_seconds']


def test_native_depth_is_reference_diagnostic_without_second_simulation(monkeypatch):
    pytest.importorskip('qulacs')
    cfg = AOAConfig(slots=2, p=1, max_evaluations=8, restarts=1,
                    statevector_backend='qulacs', final_shots=64)
    def forbidden(*args, **kwargs):
        raise AssertionError('Qulacs backend executed Qiskit reference statevector')
    monkeypatch.setattr(Statevector, 'from_instruction', forbidden)
    result = PricingAOA(problem(2), [.8], cfg).run(native_depth=True)
    assert result['native_circuit']['basis'] == ['rz', 'sx', 'x', 'cx']
    assert result['native_depth_diagnostic_seconds'] >= 0


def test_observed_timing_missing_is_unknown():
    assert all(v == 0 for v in backends.observed_quantum_timings([]).values())
    assert all(v is None for v in backends.observed_quantum_timings([{}]).values())
