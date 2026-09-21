"""Direct build: shared Candidate A preparation plus shared p=1 cost/X body.
No optimizer, sampler, backend call, output creation or ledger access here.
"""
import time
import numpy as np
from .contract import *
from traffic_simulation.r24_vrptw_qaoa_worker import circuit as shared
from traffic_simulation.r24_vrptw_qaoa_worker.adapter import Adapter
from traffic_simulation.r24_vrptw_structured_initial_state.construction import construct,preparation
from traffic_simulation.r24_vrptw_structured_initial_state.common import digest as state_digest
from traffic_simulation.r24_vrptw_structured_initial_state.validate import circuit_signature,counts

def initial_state(n,m,variable_order):
    # Explicit allowlist: no adapter, instance, labels, coefficients or results.
    inputs=dict(n=n,m=m,variable_order=list(variable_order))
    return construct(inputs),inputs

def prepare(run_id,check_environment=True):
    from qiskit import qpy
    t=time.monotonic();r,u,s,c=run_plan(run_id)
    env=environment() if check_environment else dict(status='NOT_CHECKED_TEST_ONLY')
    ad=Adapter(r['condition']);N=ad.N
    state,inputs=initial_state(ad.model['n'],ad.model['m'],ad.order)
    require(state_digest(state)==r['preparation_state_hash'],'state hash')
    old=read(DESIGN/'conditions'/(r['condition']+'.json'));require(state==old['state'],'offline support')
    layer,gamma,beta,a,const=shared.build_body(ad.model)
    prep=preparation(state);logical=prep.compose(layer)
    qc,bound,measured=shared.compile_and_bind(logical,gamma,beta,s,r)
    shared.check_ising_identity(ad,a,const)
    require(circuit_signature(qc)==old['circuits']['combined_transpiled']['identity'],'offline full circuit identity')
    mapping=[(measured.find_bit(x.qubits[0]).index,measured.find_bit(x.clbits[0]).index) for x in measured.data if x.operation.name=='measure']
    require(mapping==[(i,i) for i in range(N)],'measurement identity')
    with (DESIGN/'circuits'/r['condition']/'combined_bound.qpy').open('rb') as f:require(bound==qpy.load(f)[0],'bound QPY identity')
    runtime_spec=copy.deepcopy(s)
    # Reporting metadata only; execution-sensitive settings remain exactly inherited.
    runtime_spec.update(configuration_id='STRUCTURED_A',initial_state=c['S']['initial_state'],structured_initial_state=True)
    changed={k for k in s if s[k]!=runtime_spec[k]};require(changed<={'configuration_id','initial_state','structured_initial_state'},'extra configuration difference')
    p=dict(adapter=ad,gamma=gamma,beta=beta,environment=env,spec=runtime_spec,plan=r,identity=run_identity(run_id),logical=logical,qc=qc,measured=measured,bound=bound,preparation=prep,state=state,construction_inputs=inputs,resources=dict(counts(qc),interactions=int(np.count_nonzero(ad.model['J'])),raw_statevector_bytes=16*2**N,planned_memory_bytes=64*2**N),construction_seconds=time.monotonic()-t,status='STRUCTURED_PREPARED_OFFLINE',scientific_ready=False)
    p['injection_audit']=dict(changed='preparation_only',cost_mixer=circuit_signature(layer),Uniform_reference=u['run_id'],measurement=mapping,endian='display key q[N-1]...q[0]; reversed key indexes frozen variable_order; qubit i measured to classical bit i',route_register=list(range(state['route_qubits'])),slack_register=list(range(state['route_qubits'],N)),runtime_metadata_changes=sorted(changed))
    return p
