"""Huang eqs. 13/17--20: explicit QUBO, ALiM, exact ring XY, Qiskit check.

Input: small Instance, LP dual, AOAConfig. Output: samples, validated routes,
true reduced costs, circuit/training/time evidence. Only solver_seed is random.
literal penalty and t=0 mixer are separately selectable audit variants.
Training uses an exact one-hot tensor simulator; final states/sampling use Qiskit.
No X mixer, capacity repair, or classical negative-column fallback is used.
Tests compare the tensor evolution, Qiskit circuit, polynomial and direct formulas.
"""
from collections import Counter
from dataclasses import dataclass, asdict
from itertools import product
from time import perf_counter
import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import Statevector
from .models import Route, reduced_cost


@dataclass(frozen=True)
class AOAConfig:
    slots: int = 4
    p: int = 2
    max_evaluations: int = 200
    restarts: int = 3
    train_shots: int = 1000
    final_shots: int = 4096
    solver_seed: int = 1101
    fixed_depot: bool = True
    penalty: str = 'customer_unique'
    lambda_capacity: float = 1.0
    lambda_visit: float = 1.0
    tolerance: float = 1e-3

    def __post_init__(self):
        if self.penalty not in ('customer_unique', 'paper_literal'):
            raise ValueError('Unknown penalty version')
        if any(type(getattr(self, k)) is not int or getattr(self, k) <= 0 for k in
               ('slots', 'p', 'max_evaluations', 'restarts', 'train_shots', 'final_shots')):
            raise ValueError('Positive integer experiment settings required')
        if self.slots < 2 or self.lambda_capacity < 0 or self.lambda_visit < 0:
            raise ValueError('Invalid slots/penalties')


class Polynomial:
    """Multilinear binary degree<=2; x_a squared is x_a, including fixed t=0."""
    def __init__(self):
        self.terms = {}

    def add(self, coefficient, *variables):
        key = tuple(sorted(set(variables)))
        if len(key) > 2:
            raise ValueError('Not quadratic')
        self.terms[key] = self.terms.get(key, 0.0) + float(coefficient)

    def affine(self, terms, coefficient):
        for key, value in terms.items():
            self.add(coefficient * value, *key)

    def multiply(self, left, right, coefficient):
        for a, x in left.items():
            for b, y in right.items():
                self.add(coefficient * x * y, *(a + b))

    def value(self, bitmask):
        return sum(c for ids, c in self.terms.items()
                   if all((int(bitmask) >> i) & 1 for i in ids))

    def ising(self):
        constant, z, zz = 0.0, {}, {}
        for ids, c in self.terms.items():
            if not ids:
                constant += c
            elif len(ids) == 1:
                i = ids[0]
                constant += c / 2
                z[i] = z.get(i, 0) - c / 2
            else:
                i, j = ids
                constant += c / 4
                z[i] = z.get(i, 0) - c / 4
                z[j] = z.get(j, 0) - c / 4
                zz[i, j] = zz.get((i, j), 0) + c / 4
        return constant, z, zz


class PricingAOA:
    def __init__(self, instance, dual, config):
        self.instance, self.config = instance, config
        self.dual = np.r_[0.0, np.asarray(dual, dtype=float)]
        self.n = len(instance.demand)
        if len(self.dual) != self.n or not np.isfinite(self.dual).all():
            raise ValueError('Dual size/nonfinite mismatch')
        self.positions = tuple(range(1 if config.fixed_depot else 0, config.slots))
        self.q = self.n * len(self.positions)
        if self.q > 21 or self.n > 7:
            raise ValueError('Small-reference Qiskit guard: <=21 qubits, <=7 nodes')
        self.bit = {(i, t): b * self.n + i for b, t in enumerate(self.positions)
                    for i in range(self.n)}
        self.assignments = list(product(range(self.n), repeat=len(self.positions)))
        self.polynomial = self._polynomial()
        self.ising = self.polynomial.ising()
        self.sequences = [(0,) + a if config.fixed_depot else a for a in self.assignments]
        self.indices = np.asarray([sum(1 << self.bit[i, t] for i, t in zip(a, self.positions))
                                   for a in self.assignments], dtype=np.int64)
        self.index_to_sequence = dict(zip(self.indices.tolist(), self.sequences))
        self.energy = np.asarray([self.polynomial.value(i) for i in self.indices])
        self.ring = np.zeros((self.n, self.n))
        for i in range(self.n):
            j = (i + 1) % self.n
            self.ring[i, j] += 1
            self.ring[j, i] += 1
        self.eigenvalues, self.eigenvectors = np.linalg.eigh(self.ring)

    def variable(self, i, t):
        if t == 0 and self.config.fixed_depot:
            return {(): 1.0} if i == 0 else {}
        return {(self.bit[i, t],): 1.0}

    def _polynomial(self):
        poly = Polynomial()
        c = self.config
        for t in range(c.slots):
            for i in range(self.n):
                poly.affine(self.variable(i, t), -self.dual[i])
                for j in range(self.n):
                    poly.multiply(self.variable(i, t), self.variable(j, (t + 1) % c.slots),
                                  self.instance.distance[i, j])
        h = {(): -float(self.instance.capacity)}
        for t in range(c.slots):
            for i, demand in enumerate(self.instance.demand):
                for key, value in self.variable(i, t).items():
                    h[key] = h.get(key, 0) + demand * value
        poly.affine(h, c.lambda_capacity)
        poly.multiply(h, h, c.lambda_capacity)
        groups = [[self.variable(i, t) for t in range(c.slots)] for i in range(1, self.n)]
        if c.penalty == 'paper_literal':
            groups = [[self.variable(i, t) for i in range(self.n)] for t in range(c.slots)]
        for group in groups:
            u = {}
            for var in group:
                for key, value in var.items():
                    u[key] = u.get(key, 0) + value
            poly.multiply(u, u, c.lambda_visit)
            poly.affine(u, -c.lambda_visit)
        return poly

    def direct_energy(self, sequence):
        d, c = self.instance.distance, self.config
        travel = sum(d[i, j] for i, j in zip(sequence, sequence[1:] + sequence[:1]))
        h = sum(self.instance.demand[i] for i in sequence) - self.instance.capacity
        unique = sum(sequence.count(i) * (sequence.count(i) - 1) for i in range(1, self.n))
        return float(travel - sum(self.dual[i] for i in sequence) +
                     c.lambda_capacity * (h + h * h) +
                     (c.lambda_visit * unique if c.penalty == 'customer_unique' else 0))

    def tensor_state(self, angles):
        state = np.zeros(len(self.assignments), dtype=complex)
        state[0] = 1.0  # all variable positions initially depot
        shape = (self.n,) * len(self.positions)
        for layer in range(self.config.p):
            gamma, beta = angles[2 * layer:2 * layer + 2]
            state *= np.exp(-1j * gamma * self.energy)
            u = (self.eigenvectors * np.exp(-1j * beta * self.eigenvalues)) @ self.eigenvectors.T
            tensor = state.reshape(shape)
            for axis in range(len(self.positions)):
                tensor = np.moveaxis(np.tensordot(u, tensor, axes=(1, axis)), 0, axis)
            state = tensor.reshape(-1)
        return state

    def full_xy_block(self, beta):
        h = np.zeros((1 << self.n, 1 << self.n))
        for bits in range(1 << self.n):
            for i in range(self.n):
                j = (i + 1) % self.n
                if ((bits >> i) & 1) != ((bits >> j) & 1):
                    h[bits ^ (1 << i) ^ (1 << j), bits] += 1.0
        return expm(-1j * beta * h)

    def circuit(self, angles):
        qc = QuantumCircuit(self.q)
        for t in self.positions:
            qc.x(self.bit[0, t])
        constant, z, zz = self.ising
        for layer in range(self.config.p):
            gamma, beta = angles[2 * layer:2 * layer + 2]
            qc.global_phase -= gamma * constant
            for i, value in z.items():
                if abs(value) > 1e-14:
                    qc.rz(2 * gamma * value, i)
            for (i, j), value in zz.items():
                if abs(value) > 1e-14:
                    qc.rzz(2 * gamma * value, i, j)
            gate = UnitaryGate(self.full_xy_block(beta), label='exact_ring_XY')
            for t in self.positions:
                qc.append(gate, [self.bit[i, t] for i in range(self.n)])
        return qc

    def decode(self, sequence):
        if sequence[0] != 0:
            return [], 'FIXED_DEPOT_VIOLATION'
        ids = [i for i in sequence if i]
        if not ids:
            return [], 'EMPTY_WALK'
        if len(ids) != len(set(ids)):
            return [], 'REPEATED_CUSTOMER'
        if sum(self.instance.demand[i] for i in ids) > self.instance.capacity:
            return [], 'CAPACITY_EXCEEDED'
        # Explicit extension: split depot-separated walks into elementary trip columns.
        # In this free-fleet reference, segment costs and dual rewards add exactly.
        routes, current = [], []
        for i in sequence[1:] + (0,):
            if i:
                current.append(i)
            elif current:
                routes.append(Route(tuple(current)))
                current = []
        return routes, 'VALID'

    def run(self, native_depth=False):
        begin = perf_counter()
        c = self.config
        seed_stream = np.random.SeedSequence(c.solver_seed).spawn(c.restarts)
        histories, all_counts, routes = [], Counter(), set()
        feasible = improving = measured = 0
        reasons = Counter()
        max_infidelity = max_leakage = 0.0
        training_seconds = qiskit_seconds = 0.0
        for restart, seed in enumerate(seed_stream):
            rng = np.random.default_rng(seed)
            initial = np.array([a for layer in range(1, c.p + 1)
                                for a in (.1 * layer / c.p, np.pi / 4 * (1 - layer / (c.p + 1)))])
            if restart:
                initial = rng.uniform(0, 1, 2 * c.p) * np.tile([2 * np.pi, np.pi], c.p)
            evaluations = []

            def objective(angles):
                probabilities = np.abs(self.tensor_state(angles)) ** 2
                probabilities /= probabilities.sum()
                counts = rng.multinomial(c.train_shots, probabilities)
                value = float(counts @ self.energy / c.train_shots)
                evaluations.append({'angles': np.asarray(angles).tolist(), 'sample_mean': value})
                return value

            started = perf_counter()
            optimization = minimize(objective, initial, method='COBYLA',
                                    options={'maxiter': c.max_evaluations, 'tol': c.tolerance})
            training_seconds += perf_counter() - started
            angles = optimization.x
            started = perf_counter()
            qc = self.circuit(angles)
            state = Statevector.from_instruction(qc)
            tensor = self.tensor_state(angles)
            embedded = state.data[self.indices]
            fidelity = float(abs(np.vdot(tensor, embedded)) ** 2)
            leakage = max(0.0, float(1 - np.vdot(embedded, embedded).real))
            if abs(1 - fidelity) > 1e-8 or leakage > 1e-8:
                raise RuntimeError('Qiskit / one-hot tensor evolution mismatch')
            max_infidelity = max(max_infidelity, abs(1 - fidelity))
            max_leakage = max(max_leakage, leakage)
            state.seed(int(rng.integers(0, 2 ** 31)))
            counts = state.sample_counts(c.final_shots)
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
            qiskit_seconds += perf_counter() - started
            histories.append({'restart': restart, 'initial_angles': initial.tolist(),
                              'optimized_angles': angles.tolist(), 'nfev': int(optimization.nfev),
                              'optimizer_success': bool(optimization.success),
                              'optimizer_message': str(optimization.message),
                              'evaluations': evaluations, 'qiskit_counts': dict(counts)})
        depth = qc.depth()
        native = None
        if native_depth:
            native_qc = transpile(qc, basis_gates=['rz', 'sx', 'x', 'cx'],
                                  optimization_level=0, seed_transpiler=c.solver_seed)
            native = {'depth': native_qc.depth(), 'gates': dict(native_qc.count_ops()),
                      'basis': ['rz', 'sx', 'x', 'cx'], 'connectivity': 'all_to_all_no_hardware'}
        return {'routes': [list(r.customers) for r in sorted(routes)],
                'config': asdict(c), 'qubits': self.q, 'logical_depth': depth,
                'logical_gates': dict(qc.count_ops()), 'native_circuit': native,
                'raw_statevector_bytes': 16 * (1 << self.q),
                'one_hot_basis_states': len(self.assignments),
                'measured_shots': measured, 'feasible_shots': feasible,
                'improving_shots': improving, 'feasible_rate': feasible / measured,
                'improving_rate': improving / measured, 'reason_counts': dict(reasons),
                'qiskit_tensor_max_infidelity': max_infidelity,
                'qiskit_one_hot_max_leakage': max_leakage,
                'training_seconds': training_seconds, 'qiskit_seconds': qiskit_seconds,
                'total_seconds': perf_counter() - begin, 'history': histories,
                'backend': 'Qiskit Statevector final; exact one-hot tensor + finite-shot training',
                'internal_depot_handling': 'split at depot; free-fleet reference only'}
