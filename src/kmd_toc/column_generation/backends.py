"""Optional CPU statevector backend; no model, optimizer or sampler changes.

Qulacs is imported only when explicitly selected. Qiskit remains both the
default circuit implementation and the common final finite-shot sampler.
"""
from collections import Counter
import importlib
from importlib.metadata import version


STATEVECTOR_BACKENDS = ('qiskit', 'qulacs')


def validate_backend(name):
    if name not in STATEVECTOR_BACKENDS:
        raise ValueError(f'Unknown statevector_backend {name!r}; choose qiskit or qulacs')
    return name


def configured_backend(config):
    return validate_backend((config or {}).get('D', {}).get('statevector_backend', 'qiskit'))


def require_backend(name):
    """Fail explicitly rather than substitute another execution backend."""
    validate_backend(name)
    try:
        module = importlib.import_module(name)
        version(name)
        if name == 'qulacs':
            importlib.import_module('qulacs.gate')
        return module
    except (ImportError, OSError) as error:
        raise RuntimeError(
            f'Statevector backend {name!r} is unavailable; no backend fallback. '
            'For Qulacs, install reproducibility/environment/dwt_qulacs_v1/'
            'requirements-optional.txt in an isolated environment.'
        ) from error


def backend_environment(config=None):
    name = configured_backend(config)
    require_backend(name)
    return {'statevector_backend': name, 'statevector_version': version(name),
            'sampling_backend': 'qiskit.quantum_info.Statevector.sample_counts',
            'sampling_version': version('qiskit')}


def build_qulacs_circuit(pricing, angles):
    """The same RZ/RZZ and exact position-wise ring XY as PricingAOA.circuit.

    Integer mask bit b denotes qubit b. Qulacs rotations have the opposite
    sign to Qiskit. The omitted cost constant is only a global phase.
    """
    from qulacs import QuantumCircuit
    from qulacs.gate import DenseMatrix, PauliRotation, RZ

    circuit = QuantumCircuit(pricing.q)
    for t in pricing.positions:
        circuit.add_X_gate(pricing.bit[0, t])
    _, z, zz = pricing.ising
    for layer in range(pricing.config.p):
        gamma, beta = angles[2 * layer:2 * layer + 2]
        for i, value in z.items():
            if abs(value) > 1e-14:
                circuit.add_gate(RZ(i, -2 * gamma * value))
        for (i, j), value in zz.items():
            if abs(value) > 1e-14:
                circuit.add_gate(PauliRotation([i, j], [3, 3], -2 * gamma * value))
        matrix = pricing.full_xy_block(beta)
        for t in pricing.positions:
            circuit.add_gate(DenseMatrix([pricing.bit[i, t] for i in range(pricing.n)], matrix))
    return circuit


def qulacs_statevector(circuit, qubits):
    from qulacs import QuantumState

    state = QuantumState(qubits)
    circuit.update_quantum_state(state)
    return state.get_vector()


def circuit_metadata(circuit, backend):
    if backend == 'qiskit':
        return circuit.depth(), dict(circuit.count_ops())
    return circuit.calculate_depth(), dict(Counter(
        circuit.get_gate(i).get_name() for i in range(circuit.get_gate_count())))


QUANTUM_TIMING_FIELDS = ('circuit_build_s', 'statevector_s', 'state_validation_s',
                         'sampling_only_s', 'decode_s', 'training_s', 'final_processing_s')


def observed_quantum_timings(records):
    """Completed-call observations only; the caller carries completeness status."""
    return {key: (sum(r[key] for r in records) if all(r.get(key) is not None for r in records)
                  else None) for key in QUANTUM_TIMING_FIELDS}
