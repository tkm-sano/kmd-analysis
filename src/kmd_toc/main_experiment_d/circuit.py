"""Inspect the unchanged v5 SDK circuit and the actually executed MPS layers."""
from collections import Counter
import hashlib
import json
import math

from .depth import frozen_config


def build_circuit(local, q):
    """Observe real cost/mixer construction; do not infer depth from a label.

    q is a fresh private module per run_local call. Wrappers are restored even
    on failure. The initial forward sweep is preparation, not a QAOA layer.
    """
    from qiskit.circuit import ParameterVector
    p = frozen_config()['qaoa']['depth_p']
    angles = list(ParameterVector('theta', 2 * p))
    trace = []
    original_phase, original_swap = q.local_phase, q.partial_swap

    def phase(qc, qubits, energy, gamma):
        trace.append(('cost', gamma))
        return original_phase(qc, qubits, energy, gamma)

    def swap(qc, left, right, anc, beta):
        trace.append(('swap', beta))
        return original_swap(qc, left, right, anc, beta)

    q.local_phase, q.partial_swap = phase, swap
    try:
        circuit = q.register_circuit(local, angles)
    finally:
        q.local_phase, q.partial_swap = original_phase, original_swap
    expected = [('swap', math.pi / 4)] * local.n
    for layer in range(p):
        expected += [('cost', angles[2 * layer])] * (local.n + 2)
        expected += [('swap', angles[2 * layer + 1])] * local.n
    if trace != expected or set(circuit.parameters) != set(angles):
        raise ValueError('GENERATED_CIRCUIT_DEPTH_MISMATCH')
    width = q.register_layout(local.n)[0]
    expected_rz = p * (2 * ((1 << width) - 1) + local.n * ((1 << (2 * width)) - 1)) + (p + 1) * local.n
    if circuit.count_ops().get('rz') != expected_rz:
        raise ValueError('GENERATED_CIRCUIT_GATE_STRUCTURE_MISMATCH')
    structure = [(item.operation.name, [str(x) for x in item.operation.params],
                  [circuit.find_bit(bit).index for bit in item.qubits]) for item in circuit.data]
    fingerprint = hashlib.sha256(json.dumps([str(circuit.global_phase), structure]).encode()).hexdigest()
    metadata = {'depth_p': p, 'cost_layers': p, 'mixer_layers': p,
                'angle_parameter_count': len(circuit.parameters),
                'angle_order': [str(x) for x in angles],
                'preparation_partial_swaps': local.n,
                'cost_blocks_per_layer': local.n + 2, 'mixer_partial_swaps_per_layer': local.n,
                'sdk_gate_counts': dict(circuit.count_ops()), 'sdk_qubits': circuit.num_qubits,
                'sdk_circuit_structure_sha256': fingerprint,
                'unit': 'QAOA cost/mixer pairs, not transpiled gate depth'}
    return circuit, metadata


def executed_layers(logs, n):
    """Count fused updates actually emitted by SectorMPS before sampling."""
    p = frozen_config()['qaoa']['depth_p']
    actual = Counter((row['layer'], row['stage'], row['kind'])
                     for row in logs if row['kind'] != 'QR_MOVE')
    expected = Counter({(0, 'preparation', 'PARTIAL_SWAP'): n})
    for layer in range(1, p + 1):
        expected.update({(layer, 'oracle', 'SINGLE_PHASE'): 2,
                         (layer, 'oracle', 'DISTANCE_PHASE'): n,
                         (layer, 'mixer', 'PARTIAL_SWAP'): n})
    if actual != expected:
        raise ValueError('EXECUTED_CIRCUIT_DEPTH_MISMATCH')
    return {'depth_p': p, 'cost_layers': p, 'mixer_layers': p,
            'cost_layer_ids': list(range(1, p + 1)), 'mixer_layer_ids': list(range(1, p + 1))}
