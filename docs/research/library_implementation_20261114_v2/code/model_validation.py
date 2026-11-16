"""Direct Qamomile construction compared with native QUBO, Ising and decoding."""
import json,time,sys,itertools,os
from pathlib import Path
from adapters import *
from backend_bench import instance

def terms_error(a,b):return max((abs(a.get(k,0)-b.get(k,0)) for k in set(a)|set(b)),default=0.)

def run():
    results=[]
    for nodes,slots in [(3,3),(4,3),(4,4)]:
        for penalty in ['customer_unique','paper_literal']:
            for lc,lv in [(1.,1.),(.7,2.3)]:
                cfg=AOAConfig(slots=slots,p=2,restarts=1,penalty=penalty,lambda_capacity=lc,lambda_visit=lv)
                # Weighted demand makes capacity violations distinct from duplicates.
                base=instance(nodes);base=Instance(base.name,base.distance,(0,)+tuple(range(1,nodes)),3)
                e=OriginalAOA(base,[.9+i*.31 for i in range(nodes-1)],cfg);qm=QamomilePolynomial(e)
                native=e.polynomial;nc,nz,nzz=e.ising;qc,qz,qzz=qm.ising()
                coeff_err=terms_error(native.terms,qm.terms);ising_err=max(abs(nc-qc),terms_error(nz,qz),terms_error(nzz,qzz))
                maximum=0.;categories=Counter();examples={};decode_errors=0
                for mask in range(1<<e.q):
                    binary_energy=qm.value(mask);spins=[1-2*((mask>>i)&1) for i in range(e.q)]
                    maximum=max(maximum,abs(binary_energy-native.value(mask)),abs(qm.spin.calc_energy(spins)-native.value(mask)))
                    if mask in e.index_to_sequence:
                        seq=e.index_to_sequence[mask];routes,reason=e.decode(seq);categories[reason]+=1
                        # Direct independent decode: depot zeros are separators, never 'missing customers'.
                        ids=[i for i in seq if i];expected=('EMPTY_WALK' if not ids else 'REPEATED_CUSTOMER' if len(ids)!=len(set(ids)) else 'CAPACITY_EXCEEDED' if sum(base.demand[i] for i in ids)>base.capacity else 'VALID')
                        decode_errors+=reason!=expected
                        h=sum(base.demand[i] for i in seq)-base.capacity
                        examples.setdefault(reason,dict(mask=mask,sequence=seq,energy=binary_energy,capacity_residual=h,ALiM=lc*(h+h*h),decoded=[r.customers for r in routes],missing_from_domain=sorted(set(base.customers)-set(ids))))
                assert coeff_err<1e-10 and ising_err<1e-10 and maximum<1e-9 and decode_errors==0
                timings=[]
                for rep in range(-1,7):
                    ts=time.perf_counter();p0=OriginalAOA._polynomial(e);nt=time.perf_counter()-ts
                    ts=time.perf_counter();p0.ising();ncvt=time.perf_counter()-ts
                    ts=time.perf_counter();q0=QamomilePolynomial(e);qt=time.perf_counter()-ts
                    masks=e.indices.tolist()
                    ts=time.perf_counter();en=[p0.value(m) for m in masks];ne=time.perf_counter()-ts
                    ts=time.perf_counter();qe=[q0.value(m) for m in masks];qeval=time.perf_counter()-ts
                    assert np.allclose(en,qe,atol=1e-10,rtol=0)
                    timings.append(dict(repetition=rep,warmup=rep==-1,native_build_s=nt,native_conversion_s=ncvt,
                                        qamomile_build_s=q0.build_s,qamomile_conversion_s=q0.conversion_s,qamomile_total_s=qt,native_energy_s=ne,qamomile_energy_s=qeval,evaluated_states=len(masks)))
                results.append(dict(nodes=nodes,slots=slots,q=e.q,penalty=penalty,lambda_capacity=lc,lambda_visit=lv,
                                    variable_mapping=[dict(customer=i,position=t,qubit=b) for (i,t),b in e.bit.items()],
                                    QUBO_term_max_abs=coeff_err,Ising_term_max_abs=ising_err,energy_max_abs=maximum,basis_states_checked=1<<e.q,
                                    native_terms=sum(abs(v)>1e-14 for v in native.terms.values()),qamomile_terms=sum(abs(v)>1e-14 for v in qm.terms.values()),
                                    ising_terms=len(qz)+len(qzz)+1,constant_native=nc,constant_qamomile=qc,decode_errors=decode_errors,
                                    classifications=categories,examples=examples,timings=timings))
    return {'results':results,'memory':memory(),'ALiM_policy':'explicit lambda*(h+h*h) via BinaryExpr; no automatic OMMX penalty/slack conversion',
            'source_change':'independent code only; production files unchanged'}

if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(run(),indent=2))
