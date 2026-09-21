"""Pure preparation boundary. No file, instance, solution, cost or outcome access.

Only n, m and the accepted variable order enter this module. No temporal filtering.
This task supports precisely the ancilla-free frozen layouts; unknown auxiliaries STOP.
"""
import math

def construct(inputs):
    if set(inputs)!={'n','m','variable_order'}:
        raise ValueError('LEAKAGE_BOUNDARY: unexpected input')
    n,m=inputs['n'],inputs['m'];order=inputs['variable_order']
    if type(n) is not int or type(m) is not int or n not in (2,3) or m not in (1,2):
        raise ValueError('unsupported frozen dimensions')
    B=m*n*(n+1);N=B+4*m
    if len(order)!=N or len(set(order))!=N:raise ValueError('ancilla/extra variables or malformed order: explicit design required')
    nodes=[name.removeprefix('x_0_0_') for name in order[:n+1]]
    expected=[f'x_{k}_{t}_{node}' for k in range(m) for t in range(n) for node in nodes]
    expected += [f'b_{k}_{l}' for k in range(m) for l in range(4)]
    if list(order)!=expected:raise ValueError('variable-order mismatch')
    # Literal frozen CVRP formula; not a feasible/optimal route search.
    word=sum(1 << (slot*(n+1)+(n-slot if slot<n else 0)) for slot in range(m*n))
    support=[word+(s<<B) for s in range(1<<(4*m))]
    return dict(qubits=N,route_qubits=B,route_word=word,support=support,
        amplitude=2.**(-2*m),x_qubits=[q for q in range(B) if word>>q&1],
        h_qubits=list(range(B,N)),ancilla_count=0,preparation_parameters=[])

def validate_state(state):
    s=state['support'];a=state['amplitude'];N=state['qubits']
    if not s or len(s)!=len(set(s)) or any(type(x)is not int or x<0 or x>=1<<N for x in s):raise ValueError('malformed support')
    if not math.isfinite(a) or not math.isclose(len(s)*a*a,1.,abs_tol=1e-12):raise ValueError('invalid amplitudes/norm')
    return True

def preparation(state):
    from qiskit import QuantumCircuit
    validate_state(state)
    qc=QuantumCircuit(state['qubits'])
    for q in state['x_qubits']:qc.x(q)
    for q in state['h_qubits']:qc.h(q)
    return qc
