"""Shared frozen p=1 cost/X body, compilation, binding and measurement.

Extracted from the validated Standard worker. No initial state, decoder, optimizer,
backend or results enter build_body. Both preparations use this one implementation.
"""
import numpy as np
from .contract import require,Stop

def build_uniform_initial_state(qubits):
    from qiskit import QuantumCircuit
    qc=QuantumCircuit(qubits);qc.h(range(qubits));return qc

def build_body(model):
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
    m=model;N=m['N'];gamma,beta=Parameter('gamma'),Parameter('beta')
    a=-m['h']/2-(m['J'].sum(axis=0)+m['J'].sum(axis=1))/4
    const=m['offset']+m['h'].sum()/2+m['J'].sum()/4
    body=QuantumCircuit(N);body.global_phase=-gamma*float(const)
    for i,c in enumerate(a):
        if c:body.rz(2*gamma*float(c),i)
    for i,j in zip(*np.nonzero(m['J'])):
        body.cx(int(i),int(j));body.rz(gamma*float(m['J'][i,j])/2,int(j));body.cx(int(i),int(j))
    body.rx(2*beta,range(N))
    require(all(g.operation.params[0]==2*beta for g in body.data if g.operation.name=='rx') and body.count_ops().get('rx')==N,'Standard X')
    return body,gamma,beta,a,const

def compile_and_bind(logical,gamma,beta,spec,run):
    from qiskit import transpile
    trans=spec['transpilation']
    try:
        qc=transpile(logical,basis_gates=trans['basis_gates'],optimization_level=trans['optimization_level'],seed_transpiler=run['seeds']['transpiler_seed'],coupling_map=trans['coupling_map'],num_processes=trans['num_processes'])
    except Exception as e:raise Stop('TRANSPILATION_FAILURE: '+str(e)) from e
    bound=qc.assign_parameters({gamma:run['initial_parameters'][0]/spec['parameters']['scale'],beta:run['initial_parameters'][1]})
    require(not bound.parameters,'initial binding','CIRCUIT_CONSTRUCTION_FAILURE')
    require(qc.layout is None and qc.num_ancillas==0,'layout/ancilla','VARIABLE_ORDER_MISMATCH')
    measured=qc.copy();measured.measure_all()
    mapping=[(measured.find_bit(g.qubits[0]).index,measured.find_bit(g.clbits[0]).index) for g in measured.data if g.operation.name=='measure']
    require(mapping==[(i,i) for i in range(qc.num_qubits)],'measurement ordering','VARIABLE_ORDER_MISMATCH')
    return qc,bound,measured

def check_ising_identity(ad,a,const):
    # Original algebraic check; no state evolution or solution-dependent construction.
    N=ad.N;m=ad.model;words=[0,(1<<N)-1,*[1<<i for i in range(N)]]
    bits=np.array([ad.bits(format(w,f'0{N}b')) for w in words]);z=1-2*bits;energies=const+z@a
    for i,j in zip(*np.nonzero(m['J'])):energies+=m['J'][i,j]/4*z[:,i]*z[:,j]
    from traffic_simulation.r24_vrptw_quantum_encoding_preflight.model import expanded
    require(float(np.max(abs(energies-expanded(m,bits))))<1e-6,'Ising energy','CIRCUIT_CONSTRUCTION_FAILURE')
