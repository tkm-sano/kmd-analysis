# Hamiltonian verification

`r22_ising_conversion.converter` is the authority used to derive Ising constant, linear and quadratic terms; `hamiltonian.py` preserves indexed coefficients and Qiskit’s reversed label convention. The conversion includes the constant only when requested by the operator builder, while expectation evaluation starts from the stored constant. The three n=5 instances use 25 logical qubits and the same p=1 circuit path. No new Aer execution was performed, so numerical three-instance expectation equivalence is retained as evidence-limited rather than freshly reproduced.
