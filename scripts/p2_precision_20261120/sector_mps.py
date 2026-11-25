"""Permutation-charge MPS: the unchanged forward-v5 unitary, block QR/SVD.

Bond charge is the SET of labels to its left (a bitmask). All v5 gates
conserve the total label multiset. No state is chosen by classical cost.
"""
from collections import Counter, defaultdict
import math
import resource
import time

import numpy as np
from scipy.linalg import qr, svd


def groups(charges):
    return {int(m): np.flatnonzero(charges == m) for m in np.unique(charges)}


def gamma(k):
    u=np.finfo(float).eps/2
    return k*u/(1-k*u) if k*u<1 else float('inf')


class SectorMPS:
    def __init__(self, labels, dimension, max_bond=512, threshold=1e-18, emit=None):
        self.d=dimension;self.n=len(labels);self.center=0;self.cap=max_bond;self.cutoff=threshold
        self.A=[];self.charges=[np.array([0],dtype=np.int64)];mask=0
        for label in labels:
            a=np.zeros((1,dimension,1),complex);a[0,label,0]=1;self.A.append(a)
            mask|=1<<label;self.charges.append(np.array([mask],dtype=np.int64))
        self.logs=[];self.emit=emit;self.trunc_bound=0.;self.residual_bound=0.;self.roundoff_allowance=0.
        self.layer=0;self.stage='initial';self.logical_gate=0;self.peak_bond=1

    def _record(self, row):
        row.update(update=len(self.logs),logical_gate=self.logical_gate,layer=self.layer,stage=self.stage,
                   truncation_trace_bound=self.trunc_bound,
                   decomposition_residual_accumulated=self.residual_bound,
                   arithmetic_allowance_accumulated=self.roundoff_allowance,
                   combined_error_estimate=min(1.,self.trunc_bound+self.residual_bound+self.roundoff_allowance),
                   RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        self.logs.append(row)
        if self.emit:self.emit(row)

    def move(self,target):
        while self.center<target:self._qr(self.center,1)
        while self.center>target:self._qr(self.center,-1)

    def _qr(self,i,direction):
        begin=time.perf_counter();A=self.A[i];l,d,r=A.shape
        if direction==1:
            blocks=[]
            for mask,cols in groups(self.charges[i+1]).items():
                rows=[(j,a) for j,m in enumerate(self.charges[i]) for a in range(d)
                      if not int(m)&(1<<a) and int(m)|(1<<a)==mask]
                if not rows:continue
                ix=np.array([j*d+a for j,a in rows]);M=A.reshape(l*d,r)[np.ix_(ix,cols)]
                Q,R=qr(M,mode='economic',check_finite=False)
                blocks.append((mask,ix,cols,Q,R,float(np.linalg.norm(M-Q@R))))
            size=sum(b[3].shape[1] for b in blocks)
            new=np.zeros((l*d,size),complex);transfer=np.zeros((size,r),complex);charges=[];offset=0
            for mask,ix,cols,Q,R,res in blocks:
                z=np.arange(offset,offset+Q.shape[1]);new[np.ix_(ix,z)]=Q;transfer[np.ix_(z,cols)]=R
                charges.extend([mask]*len(z));offset+=len(z)
            self.A[i]=new.reshape(l,d,size)
            self.A[i+1]=np.tensordot(transfer,self.A[i+1],axes=(1,0))
            self.charges[i+1]=np.array(charges,dtype=np.int64);self.center=i+1
        else:
            blocks=[]
            for mask,rows in groups(self.charges[i]).items():
                cols=[(a,j) for a in range(d) for j,m in enumerate(self.charges[i+1])
                      if not mask&(1<<a) and mask|(1<<a)==int(m)]
                if not cols:continue
                ix=np.array([a*r+j for a,j in cols]);M=A.reshape(l,d*r)[np.ix_(rows,ix)]
                Q,R=qr(M.T,mode='economic',check_finite=False)
                blocks.append((mask,rows,ix,Q,R,float(np.linalg.norm(M.T-Q@R))))
            size=sum(b[3].shape[1] for b in blocks)
            new=np.zeros((size,d*r),complex);transfer=np.zeros((l,size),complex);charges=[];offset=0
            for mask,rows,ix,Q,R,res in blocks:
                z=np.arange(offset,offset+Q.shape[1]);new[np.ix_(z,ix)]=Q.T;transfer[np.ix_(rows,z)]=R.T
                charges.extend([mask]*len(z));offset+=len(z)
            self.A[i]=new.reshape(size,d,r)
            self.A[i-1]=np.tensordot(self.A[i-1],transfer,axes=(2,0))
            self.charges[i]=np.array(charges,dtype=np.int64);self.center=i-1
        residual=math.sqrt(sum(b[-1]**2 for b in blocks));self.residual_bound+=2*residual
        # Complex dot products: conservative operation-count allowance. Not interval certification.
        allowance=32*gamma(max(l*d,r*d,1))*max(1.,float(np.linalg.norm(A)))
        self.roundoff_allowance+=allowance
        self._record({'kind':'QR_MOVE','sites':[i,self.center],'qubits':self._qubits([i]),
                      'bond_before':max(l,r),'bond_after':size,'singular_values':[],
                      'discarded_weight':0.,'local_trace_error':0.,'decomposition_residual':residual,
                      'arithmetic_allowance':allowance,'wall_s':time.perf_counter()-begin,
                      'state_norm_squared_center':float(np.linalg.norm(self.A[self.center])**2),
                      'canonical_residual':self.canonical_residual()})

    def _qubits(self,sites):
        width=(self.d-1).bit_length()
        return [b for i in sites for b in range(i*width,(i+1)*width)]

    def pair(self,i,phase=None,beta=None):
        self.logical_gate+=1;self.move(i);begin=time.perf_counter()
        A,B=self.A[i],self.A[i+1];l,d,m=A.shape;r=B.shape[2]
        left=groups(self.charges[i]);middle=groups(self.charges[i+1]);right=groups(self.charges[i+2])
        rowsets=defaultdict(list);colsets=defaultdict(list)
        for mask,inds in left.items():
            for a in range(d):
                if not mask&(1<<a):
                    for j in inds:rowsets[mask|(1<<a)].append((int(j),a))
        for mask,inds in right.items():
            for b in range(d):
                if mask&(1<<b):
                    for j in inds:colsets[mask^(1<<b)].append((b,int(j)))
        blocks=[];svd_s=0.
        for mask in sorted(rowsets.keys() & colsets.keys()):
            rows=rowsets[mask];cols=colsets[mask]
            ri=np.array([x[0] for x in rows]);ra=np.array([x[1] for x in rows])
            cb=np.array([x[0] for x in cols]);ci=np.array([x[1] for x in cols])
            M=np.zeros((len(rows),len(cols)),complex)
            mid=middle.get(mask)
            if mid is not None:
                M=A[ri,ra][:,mid] @ B[mid][:,cb,ci]
            if beta is not None:
                M*=math.cos(beta)
                for a in np.unique(ra):
                    rr=np.flatnonzero(ra==a);Lmask=mask^(1<<int(a))
                    for b in np.unique(cb):
                        if Lmask&(1<<int(b)):continue
                        kk=middle.get(Lmask|(1<<int(b)))
                        if kk is None:continue
                        cc=np.flatnonzero(cb==b)
                        M[np.ix_(rr,cc)]+=-1j*math.sin(beta)*(A[ri[rr],int(b)][:,kk] @ B[kk][:,int(a),ci[cc]])
            if phase is not None:M*=phase[ra[:,None],cb[None,:]]
            if not np.any(M):continue
            t=time.perf_counter();U,s,V=svd(M,full_matrices=False,check_finite=False,lapack_driver='gesdd');svd_s+=time.perf_counter()-t
            reconstruction=(U*s)@V
            residual=float(np.linalg.norm(M-reconstruction))
            blocks.append({'mask':mask,'ri':ri,'ra':ra,'cb':cb,'ci':ci,'U':U,'s':s,'V':V,'residual':residual,
                           'rows':len(rows),'cols':len(cols)})
        spectrum=sorted([(float(v),bi,j) for bi,b in enumerate(blocks) for j,v in enumerate(b['s'])],reverse=True)
        values=np.array([v for v,_,_ in spectrum]);total=float(values@values)
        tails=np.cumsum(values[::-1]**2);discard=int(np.searchsorted(tails,self.cutoff*total,side='right'))
        keep=max(1,len(values)-discard)
        if self.cap is not None:keep=min(keep,self.cap)
        selected=defaultdict(list)
        for v,bi,j in spectrum[:keep]:selected[bi].append(j)
        weight=float(values[keep:]@values[keep:])/total
        retained_norm=math.sqrt(float(values[:keep]@values[:keep]))
        newA=np.zeros((l,d,keep),complex);newB=np.zeros((keep,d,r),complex);charges=[];offset=0
        for bi,indices in sorted(selected.items()):
            b=blocks[bi];indices=sorted(indices);z=np.arange(offset,offset+len(indices))
            newA[b['ri'][:,None],b['ra'][:,None],z[None,:]]=b['U'][:,indices]
            newB[z[:,None],b['cb'][None,:],b['ci'][None,:]]=(b['s'][indices,None]*b['V'][indices,:])/retained_norm
            charges.extend([b['mask']]*len(z));offset+=len(z)
        self.A[i],self.A[i+1]=newA,newB;self.charges[i+1]=np.array(charges,dtype=np.int64);self.center=i+1
        self.peak_bond=max(self.peak_bond,keep)
        self.trunc_bound+=math.sqrt(weight)
        residual=math.sqrt(sum(b['residual']**2 for b in blocks));self.residual_bound+=2*residual
        allowance=64*gamma(max(l*d,r*d,m,1))*max(1.,math.sqrt(total));self.roundoff_allowance+=allowance
        self._record({'kind':'DISTANCE_PHASE' if phase is not None else 'PARTIAL_SWAP','sites':[i,i+1],
             'qubits':self._qubits([i,i+1]),'bond_before':m,'bond_after':keep,
             'singular_values':values.tolist(),'sector_dimensions':[(b['mask'],b['rows'],b['cols']) for b in blocks],
             'discarded_squared_sum':float(values[keep:]@values[keep:]),'total_squared_sum':total,
             'discarded_weight':weight,'local_trace_error':math.sqrt(weight),
             'normalized_state_L2_error':math.sqrt(max(0.,2*weight/(1+math.sqrt(max(0.,1-weight))))),
             'decomposition_residual':residual,'arithmetic_allowance':allowance,
             'state_norm_squared_center':float(np.linalg.norm(newB)**2),'canonical_residual':self.canonical_residual(),
             'svd_s':svd_s,'wall_s':time.perf_counter()-begin,'cap_active':keep==self.cap,
             'discarded_due_to_cap':keep<max(1,len(values)-discard)})

    def single_phase(self,i,values):
        self.logical_gate+=1;begin=time.perf_counter()
        self.A[i]*=values[None,:,None]
        allowance=16*gamma(8);self.roundoff_allowance+=allowance
        self._record({'kind':'SINGLE_PHASE','sites':[i],'qubits':self._qubits([i]),'bond_before':self.A[i].shape[2],
             'bond_after':self.A[i].shape[2],'singular_values':[],'discarded_weight':0.,'local_trace_error':0.,
             'decomposition_residual':0.,'arithmetic_allowance':allowance,
             'state_norm_squared_center':float(np.linalg.norm(self.A[self.center])**2),
             'canonical_residual':self.canonical_residual(),'wall_s':time.perf_counter()-begin})

    def canonical_residual(self):
        largest=0.
        for i,A in enumerate(self.A):
            if i<self.center:
                for mask,indices in groups(self.charges[i+1]).items():
                    M=A.reshape(-1,A.shape[2])[:,indices]
                    largest=max(largest,float(np.linalg.norm(M.conj().T@M-np.eye(len(indices)))))
            elif i>self.center:
                for mask,indices in groups(self.charges[i]).items():
                    M=A[indices].reshape(len(indices),-1)
                    largest=max(largest,float(np.linalg.norm(M@M.conj().T-np.eye(len(indices)))))
        return largest

    def prepare_sweep(self):
        self.layer=0;self.stage='preparation'
        for i in range(self.n-1):self.pair(i,beta=math.pi/4)

    def phase(self,lookup,gamma_value,bound):
        self.stage='oracle';edge=np.zeros((self.d,self.d));n=len(lookup['first'])
        edge[:n,:n]=np.asarray(lookup['edge'])/bound
        first=np.zeros(self.d);last=np.zeros(self.d)
        first[:n]=np.asarray(lookup['first'])/bound;last[:n]=np.asarray(lookup['last'])/bound
        self.single_phase(0,np.exp(-1j*gamma_value*first))
        for i in range(self.n-1):self.pair(i,phase=np.exp(-1j*gamma_value*edge))
        self.single_phase(self.n-1,np.exp(-1j*gamma_value*last))

    def mixer(self,beta):
        self.stage='mixer'
        for parity in (0,1):
            for i in range(parity,self.n-1,2):self.pair(i,beta=beta)

    def state(self):
        return {'format':'permutation_charge_MPS_v1','tensors':self.A,'charges':self.charges,'dimension':self.d,
                'center':self.center,'max_bond':self.peak_bond,'configured_max_bond':self.cap,'threshold':self.cutoff,
                'discarded_weights':[r['discarded_weight'] for r in self.logs],
                'trace_distance_error_bound':min(1.,self.trunc_bound),
                'combined_error_estimate':min(1.,self.trunc_bound+self.residual_bound+self.roundoff_allowance),
                'decomposition_residual_accumulated':self.residual_bound,
                'arithmetic_allowance_accumulated':self.roundoff_allowance,
                'canonical_residual':self.canonical_residual(),
                'roundoff_certification':'a posteriori residual + operation-count allowance; conditional on IEEE model, not interval-certified'}


def right_environments(state):
    A=state['tensors'];charges=state['charges'];n=len(A);d=state['dimension'];env=[None]*(n+1)
    env[-1]={int(charges[-1][0]):np.ones((1,1),complex)}
    for i in range(n-1,-1,-1):
        env[i]={};left=groups(charges[i]);right=groups(charges[i+1])
        for mask,ix in left.items():
            R=np.zeros((len(ix),len(ix)),complex)
            for a in range(d):
                if mask&(1<<a):continue
                m=mask|(1<<a)
                if m not in right:continue
                M=A[i][ix,a][:,right[m]]
                R+=M@env[i+1][m]@M.conj().T
            env[i][mask]=R
    return env


def sample(state,shots,seed,width,qubits):
    A=state['tensors'];charges=state['charges'];d=state['dimension'];right=right_environments(state)
    uniforms=np.random.default_rng(seed).random((len(A),shots))
    active={0:(np.arange(shots),np.ones((shots,1),complex))};bits=np.zeros(shots,np.uint64)
    for i in range(len(A)):
        nxt=defaultdict(list);left=groups(charges[i]);right_ids=groups(charges[i+1])
        for mask,(indices,prefix) in active.items():
            p=np.zeros((len(indices),d));vectors={}
            for label in range(d):
                if mask&(1<<label):continue
                m=mask|(1<<label)
                if m not in right_ids:continue
                U=prefix@A[i][left[mask],label][:,right_ids[m]];vectors[label]=U
                p[:,label]=np.maximum(0.,np.einsum('bi,ij,bj->b',U,right[i+1][m],U.conj(),optimize=True).real)
            total=p.sum(axis=1)
            if np.any(total<=0):raise ValueError('ZERO_NORM')
            cdf=np.cumsum(p/total[:,None],axis=1);cdf[:,-1]=1
            labels=(uniforms[i,indices,None]>cdf).sum(axis=1)
            for label,U in vectors.items():
                take=labels==label
                if not take.any():continue
                nxt[mask|(1<<label)].append((indices[take],U[take]/np.sqrt(p[take,label,None])))
                bits[indices[take]]|=np.uint64(label)<<np.uint64(i*width)
        active={m:(np.concatenate([x[0] for x in g]),np.concatenate([x[1] for x in g])) for m,g in nxt.items()}
    return dict(Counter(format(int(b),f'0{qubits}b') for b in bits))


def expectation(state,lookup):
    A=state['tensors'];charges=state['charges'];d=state['dimension']
    active={(0,None):(np.ones((1,1),complex),np.zeros((1,1),complex))}
    for i in range(len(A)):
        nxt={};left=groups(charges[i]);right=groups(charges[i+1])
        for (mask,last),(N,F) in active.items():
            for a in range(len(lookup['first'])):
                if mask&(1<<a):continue
                m=mask|(1<<a)
                if m not in right:continue
                M=A[i][left[mask],a][:,right[m]]
                if not np.any(M):continue
                cost=lookup['first'][a] if last is None else lookup['edge'][last][a]
                if i==len(A)-1:cost+=lookup['last'][a]
                n=M.T@N@M.conj();f=M.T@(F+cost*N)@M.conj()
                if (m,a) in nxt:
                    n0,f0=nxt[m,a];nxt[m,a]=(n0+n,f0+f)
                else:nxt[m,a]=(n,f)
        active=nxt
    norm=sum(float(np.trace(N).real) for N,F in active.values())
    return sum(float(np.trace(F).real) for N,F in active.values())/norm/lookup['bound_m'],norm


def overlap(a,b):
    """Cross-MPS contraction sector by sector (no squared-fidelity cancellation)."""
    env={0:np.ones((1,1),complex)}
    for i,(A,B) in enumerate(zip(a['tensors'],b['tensors'])):
        la,lb=groups(a['charges'][i]),groups(b['charges'][i])
        ra,rb=groups(a['charges'][i+1]),groups(b['charges'][i+1]);nxt={}
        for mask,E in env.items():
            for v in range(a['dimension']):
                if mask&(1<<v):continue
                m=mask|(1<<v)
                if m not in ra or m not in rb:continue
                X=A[la[mask],v][:,ra[m]];Y=B[lb[mask],v][:,rb[m]]
                value=X.conj().T@E@Y
                nxt[m]=nxt.get(m,0)+value
        env=nxt
    return complex(sum(np.trace(x) for x in env.values()))
