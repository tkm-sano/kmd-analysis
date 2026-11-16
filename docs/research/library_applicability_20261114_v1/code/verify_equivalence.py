"""Meaningful contract checks for sign, bit ordering, constraint and old-run parity."""
import json,time
from pathlib import Path
import numpy as np
from benchmark import *
from qamomile.optimization.qaoa import QAOAConverter
from qamomile.quri_parts import QuriPartsTranspiler
E=ROOT/'evidence';report={'checks':[]}
for case in ['macro','selection']:
    r=json.loads((E/'measurements'/f'{case}_qiskit_1101.json').read_text())
    p=small_problem(4,2);pool=seed_plan(p);profile=ObjectiveProfile('D');lp=solve_lp(p,pool,profile,'II')
    dom=contract(p.base,lp['dual']['customer'],[(i,) for i in r['subset']],'verification',slots=r['config']['slots'])
    cfg=AOAConfig(**r['config']);e=PricingAOA(dom.pricing,dom.dual,cfg)
    qubo={(ids[0],ids[-1]):v for ids,v in e.polynomial.terms.items() if ids}
    bm=BinaryModel.from_qubo(qubo,e.polynomial.terms.get((),0.));spin=bm.change_vartype(VarType.SPIN)
    error=0.
    for mask in range(1<<e.q):
        bits=[(mask>>i)&1 for i in range(e.q)]
        error=max(error,abs(e.polynomial.value(mask)-bm.calc_energy(bits)),abs(e.polynomial.value(mask)-spin.calc_energy([1-2*b for b in bits])))
    assert error<1e-10
    records=[]
    for angles in [[.17,.41,.23,.31],[0.,.7,.5,.2],[.4,0.,.8,0.],[1.2,.3,.2,.8]]:
        expected=e.tensor_state(angles)
        for backend in ['qiskit','qulacs','quri']:
            c=backend_build(e,angles,backend);v=evolve(c,backend,e.q);w=v[e.indices]
            fidelity=float(abs(np.vdot(expected,w))**2);leak=max(0.,float(1-np.vdot(w,w).real))
            assert abs(1-fidelity)<1e-8 and leak<1e-8
            records.append(dict(backend=backend,angles=angles,fidelity=fidelity,leakage=leak))
    original=e.run();h=original['history'][0]
    assert h['optimized_angles']==r['optimized_angles']
    assert [x['sample_mean'] for x in h['evaluations']]==[x['value'] for x in r['trace']]
    report['checks'].append(dict(case=case,basis_states_checked=1<<e.q,max_energy_error=error,state_checks=records,original_training_history_identical=True,original_run=original))
# Qamomile's standard QAOA: execute, but exclude from equal-ansatz benchmark.
try:
    ts=time.perf_counter();converter=QAOAConverter(bm);t=QuriPartsTranspiler();exe=converter.transpile(t,p=2)
    result=exe.sample(t.executor(seed=1101),shots=4096,bindings={'gammas':[.17,.23],'betas':[.41,.31]}).result()
    counts=[{'bits':list(bits),'count':int(count)} for bits,count in result.results]
    assert sum(x['count'] for x in counts)==4096
    onehot=sum(x['count'] for x in counts if sum((b<<i) for i,b in enumerate(x['bits'])) in e.index_to_sequence)
    report['standard_qamomile_QAOA']={'executed':True,'shots':4096,'p':2,'seed':1101,'counts':counts,'one_hot_shots':onehot,'wall_s':time.perf_counter()-ts,'comparable':False,'reason':'X mixer, plus initial state; no one-hot penalty in unchanged polynomial'}
except Exception as exc:
    import traceback
    report['standard_qamomile_QAOA']={'executed':False,'error':str(exc),'traceback':traceback.format_exc(),'comparable':False}
(E/'equivalence_checks.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
print('All basis energies, 24 state checks and both original training histories match.')
print('Standard Qamomile QAOA:',report['standard_qamomile_QAOA']['executed'])
