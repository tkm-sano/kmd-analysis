#!/usr/bin/env python3
"""Truncation ledger check and fixed-angle, tighter-MPS D3 witness comparison."""
import argparse
from collections import Counter
import csv
import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'):
    os.environ[name]='1'

import numpy as np
from kmd_toc.iterative_d3.revision import ROOT
from kmd_toc.iterative_v3.io import dump,read,sha
from kmd_toc.iterative_v3.order import OrderProblem,cost
from kmd_toc.iterative_v3.quantum import evolve

EPS=float(np.finfo(float).eps)
TOL=1e-6


def overlap(left,right):
    """Contract a pair of MPS states directly by independent charge environments."""
    matrices={0:np.ones((1,1),complex)}
    for i,(a,b) in enumerate(zip(left['tensors'],right['tensors'])):
        edges={}
        for mask,tensor in matrices.items():
            li=np.flatnonzero(left['charges'][i]==mask)
            ri=np.flatnonzero(right['charges'][i]==mask)
            for label in range(a.shape[1]):
                if mask&(1<<label):
                    continue
                target=mask|(1<<label)
                lj=np.flatnonzero(left['charges'][i+1]==target)
                rj=np.flatnonzero(right['charges'][i+1]==target)
                if lj.size and rj.size:
                    l=a[:,label][np.ix_(li,lj)]
                    r=b[:,label][np.ix_(ri,rj)]
                    term=l.conj().T@tensor@r
                    edges[target]=edges.get(target,0)+term
        matrices=edges
    return next(iter(matrices.values())).item()


def audit_ledger(rows,n):
    counts=Counter((r['layer'],r['stage'],r['kind']) for r in rows if r['kind']!='QR_MOVE')
    expected=Counter({(0,'preparation','PARTIAL_SWAP'):n-1})
    for l in (1,2):
        expected.update({(l,'oracle','SINGLE_PHASE'):2,(l,'oracle','DISTANCE_PHASE'):n-1,(l,'mixer','PARTIAL_SWAP'):n-1})
    assert counts==expected
    errors=[];res=[];allow=[]
    for r in rows:
        if r['kind'] in ('DISTANCE_PHASE','PARTIAL_SWAP'):
            spectrum=r['singular_values']
            assert spectrum and spectrum==sorted(spectrum,reverse=True)
            total=math.fsum(s*s for s in spectrum)
            discarded=math.fsum(s*s for s in spectrum[r['bond_after']:])
            assert math.isclose(total,r['total_squared_sum'],rel_tol=64*EPS)
            delta=discarded/total
            assert math.isclose(delta,r['discarded_weight'],rel_tol=64*EPS)
            errors.append(math.sqrt(delta))
        else:
            assert r['discarded_weight']==0
        assert math.isclose(math.fsum(errors),r['truncation_trace_bound'],rel_tol=512*EPS)
        assert abs(r['state_norm_squared_center']-1) <= TOL
        assert r['canonical_residual'] <= TOL
        res.append(r['decomposition_residual'])
        allow.append(r['arithmetic_allowance'])
    trunc=math.fsum(errors)
    combined=trunc+2*math.fsum(res)+math.fsum(allow)
    assert trunc<=TOL and combined<=TOL
    assert math.isclose(combined,rows[-1]['combined_error_estimate'],rel_tol=512*EPS)
    return dict(truncation=trunc,normalized_residual_estimate=2*math.fsum(res),
                arithmetic_allowance=math.fsum(allow),combined_estimate=combined,updates=len(rows),
                max_canonical_residual=max(r['canonical_residual'] for r in rows))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--audit',required=True,type=Path)
    p.add_argument('--repository',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    with (args.audit/'SELECTOR_RECHECK.csv').open() as f:
        all_rows=list(csv.DictReader(f))
    rule=dict(selection='each scale: maximum recorded TV bound and maximum peak bond, then lexicographic path; worst sample within call by same criterion; deduplicate',
        base={'mps_bond':1280,'mps_cutoff':1e-18,'TV_bound_max':1e-6},strict={'mps_bond':2560,'mps_cutoff':1e-22,'TV_bound_max':1e-6})
    selectors={}
    for scale in ('S1','S2','S3'):
        rows=[r for r in all_rows if f'/pilot_v2/{scale}/D3/' in r['directory']]
        paths=[(Path(r['directory']),r) for r in rows]
        def peak(item):
            return read(args.repository/item[0]/'local_000/solver/RESULT.json')['peak_bond']
        for mode,metric in [('TV',lambda item:float(item[1]['max_TV_bound'])),('bond',peak)]:
            path,_=min(paths,key=lambda x:(-metric(x),str(x[0])))
            folder=args.repository/path/'local_000/solver'
            options=[]
            for f in [*folder.glob('EVAL_*.json'),folder/'FINAL_SAMPLE.json']:
                rr=read(f)
                options.append((rr['TV_bound' if mode=='TV' else 'peak_bond'],str(f)))
            f=Path(min(options,key=lambda x:(-x[0],x[1]))[1])
            key=(scale,str(f))
            selectors.setdefault(key,[]).append(mode)
    args.output.mkdir(parents=True,exist_ok=False)
    dump(args.output/'SELECTION.json',rule | {'cases':[dict(scale=s,file=f,reasons=v) for (s,f),v in selectors.items()]})
    results=[]
    for (scale, name), reasons in selectors.items():
        f=Path(name)
        old=read(f)
        case=read(f.parent.parent/'CASE.json')
        pr=OrderProblem(**case['problem'])
        assert pr.n==12 and len(set(pr.ids))==12
        a,b=rule['base'],rule['strict']
        angles=old['identity']['angles']
        assert len(angles)==4 and case['case_hash']==old['identity']['problem_hash']
        # Directed entry/exit and the original and reversed order are compared
        # by an independent lookup expression, including both boundary arcs.
        for order in (tuple(range(12)),tuple(reversed(range(12)))):
            ref=math.fsum([pr.lookup['first'][order[0]],pr.lookup['last'][order[-1]],
              *(pr.lookup['edge'][i][j] for i,j in zip(order,order[1:]))])
            assert cost(pr,order)==ref
        base,logs=evolve(pr,angles,a)
        high,strict_logs=evolve(pr,angles,b)
        b0=audit_ledger(old['updates'],pr.n)
        b1=audit_ledger(logs,pr.n)
        b2=audit_ledger(strict_logs,pr.n)
        assert math.isclose(b0['truncation'],old['TV_bound'],rel_tol=512*EPS)
        assert math.isclose(b0['truncation'],b1['truncation'],rel_tol=5e-6,abs_tol=1e-12)
        n0=overlap(base,base).real;n1=overlap(high,high).real
        z=abs(overlap(base,high))**2/(n0*n1)
        # This is a numerical cross-check. The floor avoids interpreting
        # cancellation at dot products close to one as accuracy below sqrt(u).
        diagnostic_upper=math.sqrt(max(0.,1.-z)+128*EPS)
        assert diagnostic_upper<TOL
        result=dict(scale=scale,source=name,sha256=sha(f),reasons=reasons,angles=angles,
                    base=b1,strict=b2,stored=b0,norms=[n0,n1],overlap_squared=z,
                    finite_precision_overlap_diagnostic=diagnostic_upper,
                    base_bond=base['max_bond'],strict_bond=high['max_bond'])
        results.append(result)
        dump(args.output/f'WITNESS_{len(results):02d}.json',result)
    dump(args.output/'PRECISION.json',dict(status='PASS',threshold=TOL,source_root=str(ROOT),
        results=results,truncation_proof='ideal canonical MPS, normalized Schmidt projection: overlap sqrt(1-discarded/total); pure-state trace distance sqrt(delta); unitaries preserve it, triangle sums it, measurement TV contracts',
        floating_point_scope='QR/SVD residual and operation allowance are numerical diagnostics under the IEEE model; no interval certificate',
        convergence='not inferred: fixed angles, no optimization or shot-uniform convergence claim',
        backend_sha256=sha(ROOT/'scripts/p2_precision_20261120/sector_mps.py')))
if __name__=='__main__':
    main()
