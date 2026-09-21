"""Circuit construction and offline preparation; no simulation or optimizer calls."""
import time
import numpy as np
from .contract import *
from .adapter import Adapter
from . import circuit as shared

def prepare(run_id,spec=None,check_environment=True):
    started=time.monotonic();spec=load() if spec is None else spec;run=plan(spec,run_id)
    ident=identity(spec,run)
    env=environment() if check_environment else dict(status='NOT_CHECKED_TEST_ONLY')
    ad=Adapter(run['condition']);m=ad.model;N=ad.N
    body,gamma,beta,a,const=shared.build_body(m)
    logical=shared.build_uniform_initial_state(N).compose(body)
    qc,bound,measured=shared.compile_and_bind(logical,gamma,beta,spec,run)
    require([logical.find_bit(g.qubits[0]).index for g in logical.data if g.operation.name=='h']==list(range(N)),'uniform H initialization')
    expected=next(r for r in rows(FREEZE/'RESOURCE_SNAPSHOT.csv') if r['condition']==run['condition'])
    actual=dict(qubits=N,interactions=int(np.count_nonzero(m['J'])),expected_CX=int(qc.count_ops().get('cx',0)),
        expected_depth=qc.depth(),raw_statevector_bytes=16*2**N,planned_memory_bytes=64*2**N)
    mapping={'qubits':'qubits','interactions':'interactions','expected_CX':'estimated_CX','expected_depth':'estimated_depth',
        'raw_statevector_bytes':'raw_statevector_bytes','planned_memory_bytes':'planned_memory_bytes'}
    for key,field in mapping.items():require(actual[key]==int(expected[field]),(key,actual[key],expected[field]),'CIRCUIT_RESOURCE_MISMATCH')
    shared.check_ising_identity(ad,a,const)
    path=ROOT/run['planned_output_path']
    require(path.is_relative_to(BASE/'r24_vrptw_qaoa_scientific/20260921_v1/runs'),'output path')
    return dict(spec=spec,plan=run,identity=ident,adapter=ad,logical=logical,qc=qc,measured=measured,bound=bound,
        gamma=gamma,beta=beta,environment=env,resources=actual,construction_seconds=time.monotonic()-started,
        status='OFFLINE_ACCEPTANCE_VALIDATED',scientific_ready=False)

def public_result(p):
    return dict(run_id=p['plan']['run_id'],condition=p['plan']['condition'],repetition=p['plan']['repetition'],
        status='PASS',identity=p['identity'],resources=p['resources'],construction_seconds=p['construction_seconds'],
        output_path=p['plan']['planned_output_path'],parameter_binding='PASS',seeds='PASS',
        resource_difference='NONE_EXACT_MATCH',scientific_circuits=0,Aer=0,optimizer=0,final_sampling=0)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('run_id');args=parser.parse_args()
    print(json.dumps(public_result(prepare(args.run_id)),indent=2))
