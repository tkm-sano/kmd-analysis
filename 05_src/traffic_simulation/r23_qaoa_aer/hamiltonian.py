"""Qiskit operator and circuit construction with explicit qubit ordering."""

from __future__ import annotations

from typing import Sequence

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp

from .schema import R23Input


def _label(n: int, terms: dict[int, str]) -> str:
    chars = ["I"] * n
    for index, value in terms.items():
        chars[index] = value
    return "".join(reversed(chars))  # Qiskit labels are q[n-1]...q[0].


def build_cost_operator(input_data: R23Input, *, include_constant: bool = False) -> SparsePauliOp:
    terms: list[tuple[str, complex]] = []
    if include_constant:
        terms.append(("I" * input_data.n_logical, input_data.ising_constant))
    for index, value in sorted(input_data.ising_linear.items()):
        terms.append((_label(input_data.n_logical, {index: "Z"}), value))
    for (left, right), value in sorted(input_data.ising_quadratic.items()):
        terms.append((_label(input_data.n_logical, {left: "Z", right: "Z"}), value))
    return SparsePauliOp.from_list(terms, num_qubits=input_data.n_logical)


def build_qaoa_circuit(input_data: R23Input, p: int, gamma: Sequence[float], beta: Sequence[float]) -> QuantumCircuit:
    if len(gamma) != p or len(beta) != p:
        raise ValueError("gamma and beta must each have length p")
    qc = QuantumCircuit(input_data.n_logical)
    qc.h(range(input_data.n_logical))
    for layer in range(p):
        for index, coefficient in sorted(input_data.ising_linear.items()):
            qc.rz(2.0 * float(gamma[layer]) * coefficient, index)
        for (left, right), coefficient in sorted(input_data.ising_quadratic.items()):
            qc.cx(left, right)
            qc.rz(2.0 * float(gamma[layer]) * coefficient, right)
            qc.cx(left, right)
        for index in range(input_data.n_logical):
            # H_M=-sum X; exp(-i beta H_M)=RX(-2 beta).
            qc.rx(-2.0 * float(beta[layer]), index)
    return qc


def repository_parameters(values: Sequence[float], p: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if len(values) != 2 * p:
        raise ValueError("repository parameter vector must have length 2p")
    return tuple(float(v) for v in values[:p]), tuple(float(v) for v in values[p:])
