"""Actual QAOA phase-oracle circuits and independent CPU state evolution.

Diagonal synthesis is explicit (Pauli Z parity rotations), not a promise of a
polynomial-cost quantum oracle. Aer executes the identical diagonal natively.
"""
from itertools import permutations, islice
from functools import lru_cache
from time import perf_counter
import math
import numpy as np
from .model import Encoding, candidate_count, direct_cost


def preflight(encoding, safety, method='statevector', available_bytes=None):
    q = encoding.q
    working = safety['dense_working_arrays'] * 16 * (1 << q) + safety.get('baseline_reserve_MiB', 0) * 1024 ** 2
    budget = safety['worker_RSS_MiB'] * 1024 ** 2
    if available_bytes is not None:
        budget = min(budget, available_bytes // 4)
    reason = None
    mps_limit = safety.get('max_MPS_QUBO_qubits', 8) if encoding.name == 'one_hot_separator' else safety['max_MPS_oracle_qubits']
    if method == 'matrix_product_state' and q > mps_limit:
        reason = 'UNBOUNDED_EXACT_MPS_BOND_OR_WIDE_ORACLE; small equivalent circuit only'
    elif working > budget:
        reason = 'CONSERVATIVE_WORKING_MEMORY_EXCEEDS_SAFETY_CAP'
    elif 1 << q > safety['max_diagonal_entries']:
        reason = 'DIAGONAL_TABLE_WORK_LIMIT'
    return {'safe': reason is None, 'reason': reason, 'estimated_working_bytes': working,
            'effective_worker_budget_bytes': budget, 'method': method,
            'safety_limit_is_production_budget': False}


def compact_cost_table(problem):
    """Tabulate lexicographic ranks in vectorized batches; no quantum results.

    D is a depot-return surrogate for the selected customers. Boundary insertion,
    capacity, travel, berth and W are checked on the complete plan separately.
    This distinction is persisted in all reports.
    """
    n = problem.n
    e = Encoding('compact_rank_split', problem.customer_ids)
    distance = np.asarray(problem.distance_m)
    bound = max(1., (n + 2) * float(distance.max()))
    energy = np.full(1 << e.q, 2., dtype=np.float64)
    iterator = permutations(range(1, n + 1))
    offset = 0
    while rows := list(islice(iterator, 8192)):
        a = np.asarray(rows, dtype=np.int64)
        edges = distance[a[:, :-1], a[:, 1:]]
        prefix = np.concatenate([np.zeros((len(a), 1)), np.cumsum(edges, axis=1)], axis=1)
        values = np.empty((len(a), n + 1))
        values[:, 0] = distance[0, a[:, 0]] + prefix[:, -1] + distance[a[:, -1], 0]
        values[:, -1] = values[:, 0]
        for split in range(1, n):
            values[:, split] = (distance[0, a[:, 0]] + prefix[:, split - 1] + distance[a[:, split - 1], 0]
                                + distance[0, a[:, split]] + prefix[:, -1] - prefix[:, split] + distance[a[:, -1], 0])
        size = values.size
        energy[offset:offset + size] = values.reshape(-1) / bound
        offset += size
    assert offset == candidate_count(n)
    return energy, bound


def one_hot_polynomial(problem):
    """n customers plus one depot separator in n+1 positions, row/column QUBO.

    F has nonnegative directed arc and endpoint terms, each <= max OD.
    Every valid state has F <= (n+2)*max OD. A=bound+1 therefore separates
    EVERY invalid state from EVERY valid state; P is an integer >=1 there.
    """
    n, width = problem.n, problem.n + 1
    d = np.asarray(problem.distance_m)
    bound = max(1., (n + 2) * float(d.max()))
    penalty = bound + 1
    terms = {}
    def add(c, *bits):
        key = tuple(sorted(set(bits)))
        terms[key] = terms.get(key, 0.) + float(c)
    def bit(t, label):
        return t * width + label
    def node(label):
        return 0 if label == n else label + 1
    for label in range(width):
        add(d[0, node(label)], bit(0, label))
        add(d[node(label), 0], bit(n, label))
    for t in range(n):
        for a in range(width):
            for b in range(width):
                add(d[node(a), node(b)], bit(t, a), bit(t + 1, b))
    groups = [[bit(t, label) for label in range(width)] for t in range(width)]
    groups += [[bit(t, label) for t in range(width)] for label in range(width)]
    for group in groups:
        add(penalty)
        for b in group:
            add(-penalty, b)
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                add(2 * penalty, a, b)
    return terms, penalty


def polynomial_value(terms, bits):
    return math.fsum(c for key, c in terms.items() if all((bits >> b) & 1 for b in key))


def one_hot_circuit(problem, angles):
    """Quadratic Ising circuit; scalable construction even if simulation is not."""
    from qiskit import QuantumCircuit
    e = Encoding('one_hot_separator', problem.customer_ids)
    terms, _ = one_hot_polynomial(problem)
    bound = max(1., (problem.n + 2) * float(np.max(problem.distance_m)))
    constant = 0.
    z, zz = {}, {}
    for key, value in terms.items():
        value /= bound
        if not key:
            constant += value
        elif len(key) == 1:
            constant += value / 2
            z[key[0]] = z.get(key[0], 0.) - value / 2
        else:
            a, b = key
            constant += value / 4
            z[a] = z.get(a, 0.) - value / 4
            z[b] = z.get(b, 0.) - value / 4
            zz[a,b] = zz.get((a,b), 0.) + value / 4
    qc = QuantumCircuit(e.q)
    qc.h(range(e.q))
    for gamma, beta in np.asarray(angles).reshape(-1, 2):
        qc.global_phase -= float(gamma * constant)
        for a, value in sorted(z.items()):
            if value:
                qc.rz(float(2 * gamma * value), a)
        for (a,b), value in sorted(zz.items()):
            if value:
                qc.cx(a,b)
                qc.rz(float(2 * gamma * value),b)
                qc.cx(a,b)
        qc.rx(float(2 * beta),range(e.q))
    return qc


def encoding_gate_resources(problem, name, p=1):
    e = Encoding(name, problem.customer_ids)
    if name == 'one_hot_separator':
        qc = one_hot_circuit(problem, [.3,.2] * p)
        counts = qc.count_ops()
        return {'one_qubit_gates': sum(counts.get(g,0) for g in ('h','rz','rx')),
                'two_qubit_gates': counts.get('cx',0), 'depth': qc.depth(),
                'count_kind': 'exact QUBO Ising construction; all-to-all topology',
                'cost_operator': 'F+AP quadratic Ising RZ and RZZ decomposed into CX/RZ',
                'mixer': 'X; invalid states rejected after measurement', 'ancillas': 0}
    if e.q <= 22:
        result = synthesis_resources(e.q,p)
    else:
        cx = p * (e.q * (1 << e.q) - 2 * ((1 << e.q) - 1))
        single = e.q + p * ((1 << e.q) - 1 + e.q)
        result = {'one_qubit_gates': single, 'two_qubit_gates': cx, 'depth': None,
                  'depth_serial_upper_bound': single + cx,
                  'count_kind': 'analytic unpruned parity synthesis; depth not scheduled at unsafe work size'}
    return {**result, 'cost_operator': 'valid normalized directed D surrogate; invalid energy2; Walsh Z-parity synthesis',
            'mixer': 'X; invalid states rejected after measurement', 'ancillas': 0}


def table(problem, encoding):
    if encoding.name == 'compact_rank_split':
        return compact_cost_table(problem)
    bound = max(1., (problem.n + 2) * float(np.max(problem.distance_m)))
    if encoding.name == 'one_hot_separator':
        poly, penalty = one_hot_polynomial(problem)
        energy = np.array([polynomial_value(poly, i) / bound for i in range(1 << encoding.q)])
    else:
        energy = np.full(1 << encoding.q, 2.)
        from .model import enumerate_decisions
        for decision in enumerate_decisions(problem.customer_ids):
            energy[encoding.encode(decision)] = direct_cost(problem, decision) / bound
    return energy, bound


def walsh(energy):
    result = np.array(energy, dtype=float, copy=True)
    width = 1
    while width < len(result):
        view = result.reshape(-1, 2 * width)
        left = view[:, :width].copy()
        right = view[:, width:].copy()
        view[:, :width], view[:, width:] = left + right, left - right
        width *= 2
    return result / len(result)


@lru_cache(maxsize=32)
def synthesis_resources(q, p=1):
    """Exact counts/depth of our unpruned serialized parity synthesis.

    Include zero-angle rotations: no tolerance based approximation is hidden.
    Each nonempty mask uses a highest-bit target and ascending controls, then
    reversed uncompute. O(q*2^q), no ancillas. Depth computed by wire scheduling.
    """
    levels = [1] * q  # H layer
    cx = 0
    for _ in range(p):
        for mask in range(1, 1 << q):
            target = mask.bit_length() - 1
            controls = [b for b in range(target) if mask & (1 << b)]
            for b in controls:
                level = max(levels[b], levels[target]) + 1
                levels[b] = levels[target] = level
                cx += 1
            levels[target] += 1
            for b in reversed(controls):
                level = max(levels[b], levels[target]) + 1
                levels[b] = levels[target] = level
                cx += 1
        levels = [level + 1 for level in levels]  # RX mixer
    assert cx == p * (q * (1 << q) - 2 * ((1 << q) - 1))
    return {'decomposition': 'unpruned Walsh Z-parity synthesis; no topology routing',
            'one_qubit_gates': q + p * ((1 << q) - 1 + q), 'two_qubit_gates': cx,
            'depth': max(levels), 'count_kind': 'exact constructed schedule; not hardware transpilation',
            'native_oracle_depth': 1 + 2 * p,
            'native_oracle_is_one_or_two_qubit_gate': False}


def circuit(energy, angles, decomposed=False):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import DiagonalGate
    q = (len(energy) - 1).bit_length()
    qc = QuantumCircuit(q)
    qc.h(range(q))
    coeff = walsh(energy) if decomposed else None
    for gamma, beta in np.asarray(angles).reshape(-1, 2):
        if decomposed:
            qc.global_phase -= float(gamma * coeff[0])
            for mask in range(1, 1 << q):
                target = mask.bit_length() - 1
                controls = [b for b in range(target) if mask & (1 << b)]
                for b in controls:
                    qc.cx(b, target)
                qc.rz(float(2 * gamma * coeff[mask]), target)
                for b in reversed(controls):
                    qc.cx(b, target)
        else:
            qc.append(DiagonalGate(np.exp(-1j * gamma * energy)), range(q))
        qc.rx(float(2 * beta), range(q))
    return qc


def numpy_state(energy, angles):
    q = (len(energy) - 1).bit_length()
    state = np.full(len(energy), 1 / math.sqrt(len(energy)), dtype=complex)
    for gamma, beta in np.asarray(angles).reshape(-1, 2):
        state *= np.exp(-1j * gamma * energy)
        for b in range(q):
            view = state.reshape(-1, 2, 1 << b)
            a, c = view[:, 0].copy(), view[:, 1].copy()
            view[:, 0] = math.cos(beta) * a - 1j * math.sin(beta) * c
            view[:, 1] = math.cos(beta) * c - 1j * math.sin(beta) * a
    return state


def run_kernel(problem, encoding_name, settings, method='statevector', progress=None):
    from scipy.optimize import minimize
    from qiskit_aer import AerSimulator
    import resource, os
    encoding = Encoding(encoding_name, problem.customer_ids)
    kernel_start = perf_counter()
    start = perf_counter()
    energy, bound = table(problem, encoding)
    preparation_s = perf_counter() - start
    backend = AerSimulator(method=method, max_parallel_threads=1, max_parallel_experiments=1,
                           max_memory_mb=1536, seed_simulator=problem.seed)
    history = []
    simulator_s = circuit_s = 0.
    def execute(angles, shots, seed):
        nonlocal simulator_s, circuit_s
        begin = perf_counter()
        # Small MPS uses an explicit 1q/2q synthesis, avoiding a wide MPS oracle.
        qc = (one_hot_circuit(problem, angles) if encoding_name == 'one_hot_separator' else
              circuit(energy, angles, decomposed=(method == 'matrix_product_state')))
        qc.measure_all()
        circuit_s += perf_counter() - begin
        begin = perf_counter()
        result = backend.run(qc, shots=shots, seed_simulator=seed).result()
        simulator_s += perf_counter() - begin
        if not result.success:
            raise RuntimeError(result.status)
        return result.get_counts()
    def objective(angles):
        counts = execute(angles, settings['training_shots'], problem.seed + len(history))
        value = math.fsum(energy[int(bits.replace(' ', ''), 2)] * count for bits, count in counts.items()) / settings['training_shots']
        history.append({'angles': list(map(float, angles)), 'objective': value, 'counts': counts})
        if progress is not None:
            progress({'phase': 'training_complete', 'evaluation': len(history), 'training_shots': settings['training_shots'],
                      'angles': list(map(float, angles)), 'objective': value, 'counts': counts})
        return value
    start = perf_counter()
    fit = minimize(objective, settings['initial_angles'] * settings['p'], method='COBYLA',
                   options={'maxiter': settings['max_evaluations'], 'rhobeg': .1, 'tol': .01})
    optimizer_s = perf_counter() - start
    counts = execute(fit.x, settings['final_shots'], problem.seed + 100000)
    if progress is not None:
        progress({'phase': 'final_measurement_complete', 'final_shots': settings['final_shots'], 'counts': counts})
    decoded = []
    invalid = {}
    good = 0
    nonempty = 0
    for bits, count in counts.items():
        try:
            decision = encoding.decode(int(bits.replace(' ', ''), 2))
            decoded.append({'trip_1': decision.trip_1, 'trip_2': decision.trip_2, 'count': count,
                            'distance_surrogate_m': direct_cost(problem, decision)})
            good += count
            nonempty += count if decision.trip_1 and decision.trip_2 else 0
        except ValueError as e:
            invalid[str(e)] = invalid.get(str(e), 0) + count
    return {'status': 'MEASURED', 'scope': 'single_local_fixture_resource_validation_not_performance',
            **encoding.resources(), 'method': method, 'preparation_s': preparation_s,
            'optimizer_wall_s': optimizer_s, 'circuit_preparation_s': circuit_s, 'simulator_s': simulator_s,
            'nfev': len(history), 'training_shots': len(history) * settings['training_shots'],
            'final_shots': settings['final_shots'], 'history': history, 'counts': counts,
            'decoded': decoded, 'invalid_reasons': invalid, 'decode_success_rate': good / settings['final_shots'],
            'nonempty_local_fraction': nonempty / settings['final_shots'],
            'physical_feasible_rate': None, 'physical_feasible_rate_reason': 'measured by separate full completion stage',
            'normalization_bound_m': bound, 'optimizer_message': str(fit.message),
            'kernel_wall_s': perf_counter() - kernel_start,
            'peak_RSS_MiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            'pid': os.getpid(), 'affinity': sorted(os.sched_getaffinity(0)),
            'settings': settings, 'seed': problem.seed, 'quantum_optimization_calls': 1}
