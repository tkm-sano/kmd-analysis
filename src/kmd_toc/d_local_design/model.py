"""Two labelled trips: bijections, independent directed cost and input contract."""
from dataclasses import dataclass, asdict
from collections import Counter
from itertools import permutations
import math
import numpy as np


def candidate_count(n, allow_empty=True):
    if type(n) is not int or n < 1:
        raise ValueError('POSITIVE_N')
    return (n + 1 if allow_empty else n - 1) * math.factorial(n)


@dataclass(frozen=True)
class Decision:
    trip_1: tuple[str, ...]
    trip_2: tuple[str, ...]

    def validate(self, ids, allow_empty=True):
        if Counter(self.trip_1 + self.trip_2) != Counter(ids) or len(set(ids)) != len(ids):
            raise ValueError('MISSING_DUPLICATE_OR_UNKNOWN_CUSTOMER')
        if not allow_empty and (not self.trip_1 or not self.trip_2):
            raise ValueError('EMPTY_LOCAL_PART')
        return self


@dataclass(frozen=True)
class LocalProblem:
    problem_id: str
    trip_ids: tuple[tuple[str, int], tuple[str, int]]
    customer_ids: tuple[str, ...]
    demand: tuple[int, ...]
    distance_m: tuple[tuple[float, ...], ...]  # depot at index zero
    duration_s: tuple[tuple[float, ...], ...]
    plan_reference: dict
    outside_routes: tuple[dict, ...]
    seed: int

    @property
    def n(self):
        return len(self.customer_ids)

    @property
    def same_vehicle(self):
        return self.trip_ids[0][0] == self.trip_ids[1][0]

    def validate(self):
        if len(self.trip_ids) != 2 or len(set(self.trip_ids)) != 2:
            raise ValueError('TWO_DISTINCT_TRIPS')
        if not self.customer_ids or len(set(self.customer_ids)) != self.n:
            raise ValueError('CUSTOMER_IDS')
        if len(self.demand) != self.n or any(type(d) is not int or d < 1 for d in self.demand):
            raise ValueError('DEMAND')
        for matrix in (self.distance_m, self.duration_s):
            a = np.asarray(matrix)
            if a.shape != (self.n + 1, self.n + 1) or not np.isfinite(a).all() or (a < 0).any():
                raise ValueError('DIRECTED_OD')
        if not self.plan_reference or len({s for r in self.outside_routes for s in r['customers']} & set(self.customer_ids)):
            raise ValueError('PLAN_REFERENCE_OR_OUTSIDE_OVERLAP')
        return self

    def payload(self):
        return {**asdict(self), 'n': self.n, 'same_vehicle': self.same_vehicle}


def route_cost(ids, order, distance):
    index = {s: i + 1 for i, s in enumerate(ids)}
    nodes = (0, *(index[s] for s in order), 0)
    return math.fsum(float(distance[a][b]) for a, b in zip(nodes, nodes[1:]))


def direct_cost(problem, decision):
    decision.validate(problem.customer_ids)
    return math.fsum(route_cost(problem.customer_ids, r, problem.distance_m)
                     for r in (decision.trip_1, decision.trip_2))


def enumerate_decisions(ids, allow_empty=True):
    for order in permutations(ids):
        for split in range(0 if allow_empty else 1, len(ids) + (1 if allow_empty else 0)):
            yield Decision(order[:split], order[split:])


def rank_permutation(order, ids):
    remaining = list(ids)
    result = 0
    for i, item in enumerate(order):
        digit = remaining.index(item)
        result += digit * math.factorial(len(ids) - i - 1)
        remaining.pop(digit)
    if remaining:
        raise ValueError('INCOMPLETE_PERMUTATION')
    return result


def unrank_permutation(rank, ids):
    if not 0 <= rank < math.factorial(len(ids)):
        raise ValueError('INVALID_PERMUTATION_RANK')
    remaining = list(ids)
    order = []
    for width in range(len(ids), 0, -1):
        digit, rank = divmod(rank, math.factorial(width - 1))
        order.append(remaining.pop(digit))
    return tuple(order)


class Encoding:
    """Ancilla-free representations; invalid bit strings are never repaired."""
    names = ('one_hot_separator', 'binary_slots_split', 'compact_rank_split')

    def __init__(self, name, ids):
        if name not in self.names:
            raise ValueError('ENCODING')
        self.name, self.ids, self.n = name, tuple(ids), len(ids)
        self.label_bits = max(1, (self.n - 1).bit_length())
        self.split_bits = self.n.bit_length()
        self.q = ((self.n + 1) ** 2 if name == self.names[0] else
                  self.n * self.label_bits + self.split_bits if name == self.names[1] else
                  (candidate_count(self.n) - 1).bit_length())

    def encode(self, decision):
        decision.validate(self.ids)
        order = decision.trip_1 + decision.trip_2
        split = len(decision.trip_1)
        if self.name == self.names[2]:
            return rank_permutation(order, self.ids) * (self.n + 1) + split
        if self.name == self.names[1]:
            return sum(self.ids.index(s) << (i * self.label_bits) for i, s in enumerate(order)) | (split << (self.n * self.label_bits))
        labels = tuple(self.ids.index(s) for s in decision.trip_1) + (self.n,) + tuple(self.ids.index(s) for s in decision.trip_2)
        return sum(1 << (t * (self.n + 1) + label) for t, label in enumerate(labels))

    def decode(self, bits, allow_empty=True):
        if type(bits) is not int or not 0 <= bits < 1 << self.q:
            raise ValueError('BIT_RANGE')
        if self.name == self.names[2]:
            rank, split = divmod(bits, self.n + 1)
            order = unrank_permutation(rank, self.ids)
        elif self.name == self.names[1]:
            split = bits >> (self.n * self.label_bits)
            if split > self.n:
                raise ValueError('SPLIT_RANGE')
            labels = [(bits >> (t * self.label_bits)) & ((1 << self.label_bits) - 1) for t in range(self.n)]
            if any(j >= self.n for j in labels) or len(set(labels)) != self.n:
                raise ValueError('INVALID_PERMUTATION')
            order = tuple(self.ids[j] for j in labels)
        else:
            labels = []
            for t in range(self.n + 1):
                mask = (bits >> (t * (self.n + 1))) & ((1 << (self.n + 1)) - 1)
                if mask.bit_count() != 1:
                    raise ValueError('POSITION_ONE_HOT')
                labels.append(mask.bit_length() - 1)
            if len(set(labels)) != self.n + 1:
                raise ValueError('LABEL_EXACTLY_ONCE')
            split = labels.index(self.n)
            order = tuple(self.ids[j] for j in labels if j != self.n)
        return Decision(order[:split], order[split:]).validate(self.ids, allow_empty)

    def resources(self):
        valid = candidate_count(self.n)
        return {'encoding': self.name, 'n': self.n, 'logical_qubits': self.q, 'ancillas': 0,
                'total_qubits': self.q, 'states': 1 << self.q, 'valid_states': valid,
                'nonempty_local_states': candidate_count(self.n, False),
                'invalid_states': (1 << self.q) - valid, 'invalid_fraction': 1 - valid / (1 << self.q),
                'statevector_bytes': 16 * (1 << self.q),
                'encode_decode_complexity': 'O(n^2)' if self.name == self.names[2] else 'O(n^2) bit checks' if self.name == self.names[0] else 'O(n) labels; O(n^2) naive encode lookup'}
