"""TEBD on whole binary-labelled registers; exact circuit fusion, explicit SVD error.

The proven clean-ancilla partial-SWAP gadget is executed as cos(beta)I-i sin(beta)S.
This is a quantum-state simulator, not enumeration or a classical optimizer.
"""
import math
from collections import Counter
import numpy as np
from scipy.linalg import svd


class RegisterMPS:
    def __init__(self,labels,dimension,max_bond=128,threshold=1e-18):
        self.d=dimension;self.center=0;self.A=[];self.max_bond=max_bond;self.threshold=threshold
        self.discarded=[]
        for label in labels:
            a=np.zeros((1,dimension,1),dtype=complex);a[0,label,0]=1;self.A.append(a)

    def move(self,target):
        while self.center<target:
            i=self.center;l,d,r=self.A[i].shape
            Q,R=np.linalg.qr(self.A[i].reshape(l*d,r),mode='reduced');new=Q.shape[1]
            self.A[i]=Q.reshape(l,d,new);self.A[i+1]=np.tensordot(R,self.A[i+1],axes=(1,0));self.center+=1
        while self.center>target:
            i=self.center;l,d,r=self.A[i].shape
            Q,R=np.linalg.qr(self.A[i].reshape(l,d*r).T,mode='reduced');new=Q.shape[1]
            self.A[i]=Q.T.reshape(new,d,r);self.A[i-1]=np.tensordot(self.A[i-1],R.T,axes=(2,0));self.center-=1

    def pair(self,i,phase=None,beta=None):
        self.move(i)
        theta=np.tensordot(self.A[i],self.A[i+1],axes=(2,0))
        if phase is not None:theta*=phase[None,:,:,None]
        if beta is not None:theta=math.cos(beta)*theta-1j*math.sin(beta)*theta.transpose(0,2,1,3)
        l,d,_,r=theta.shape
        U,s,V=svd(theta.reshape(l*d,d*r),full_matrices=False,check_finite=False,lapack_driver='gesdd')
        total=float(np.sum(s*s));tails=np.cumsum((s[::-1]*s[::-1]))
        discard=int(np.searchsorted(tails,self.threshold*total,side='right'))
        keep=max(1,len(s)-discard)
        if self.max_bond is not None:keep=min(keep,self.max_bond)
        weight=float(np.sum(s[keep:]**2))/total
        self.discarded.append(weight)
        norm=math.sqrt(float(np.sum(s[:keep]**2)))
        self.A[i]=U[:,:keep].reshape(l,d,keep)
        self.A[i+1]=(s[:keep,None]*V[:keep,:]/norm).reshape(keep,d,r)
        self.center=i+1

    def mixer(self,beta):
        for parity in (0,1):
            for i in range(parity,len(self.A)-1,2):self.pair(i,beta=beta)

    def prepare_sweep(self):
        for i in range(len(self.A)-1):self.pair(i,beta=math.pi/4)

    def phase(self,lookup,gamma,bound):
        edge=np.zeros((self.d,self.d),dtype=float);n=len(lookup['first'])
        edge[:n,:n]=np.asarray(lookup['edge'])/bound
        first=np.zeros(self.d);last=np.zeros(self.d)
        first[:n]=np.asarray(lookup['first'])/bound;last[:n]=np.asarray(lookup['last'])/bound
        self.A[0]*=np.exp(-1j*gamma*first)[None,:,None]
        for i in range(len(self.A)-1):self.pair(i,phase=np.exp(-1j*gamma*edge))
        self.A[-1]*=np.exp(-1j*gamma*last)[None,:,None]

    def state(self):
        return {'format':'grouped_register_MPS_v5','tensors':self.A,'dimension':self.d,
                'discarded_weights':self.discarded,'max_bond':max(max(a.shape[0],a.shape[2]) for a in self.A),
                'trace_distance_error_bound':min(1.,sum(math.sqrt(x) for x in self.discarded)),
                'threshold':self.threshold,'configured_max_bond':self.max_bond}


def sample(state,shots,seed,w,qubits):
    A=state['tensors'];n=len(A);d=state['dimension']
    right=[None]*(n+1);right[n]=np.ones((1,1),dtype=complex)
    for i in range(n-1,-1,-1):
        right[i]=sum(A[i][:,a,:]@right[i+1]@A[i][:,a,:].conj().T for a in range(d))
    prefix=np.ones((shots,1),dtype=complex)
    bits=np.zeros(shots,dtype=np.uint64 if qubits<=64 else object)
    rng=np.random.default_rng(seed)
    for i in range(n):
        p=np.empty((shots,d))
        for label in range(d):
            u=prefix@A[i][:,label,:]
            p[:,label]=np.maximum(0.,np.einsum('bi,ij,bj->b',u,right[i+1],u.conj(),optimize=True).real)
        total=p.sum(axis=1)
        if np.any(total<1e-200):raise ValueError('ZERO_GROUPED_MPS_NORM')
        cdf=np.cumsum(p/total[:,None],axis=1);cdf[:,-1]=1.
        labels=(rng.random(shots)[:,None]>cdf).sum(axis=1)
        new=np.empty((shots,A[i].shape[2]),dtype=complex)
        for label in range(d):
            mask=labels==label
            if mask.any():new[mask]=prefix[mask]@A[i][:,label,:]
        new/=np.sqrt(np.maximum(p[np.arange(shots),labels],1e-300))[:,None]
        prefix=new
        if qubits<=64:bits|=labels.astype(np.uint64)<<np.uint64(i*w)
        else:bits|=labels.astype(object)*(1<<(i*w))
    return dict(Counter(format(int(x),f'0{qubits}b') for x in bits))


def overlap(a,b):
    env=np.ones((1,1),dtype=complex)
    for x,y in zip(a['tensors'],b['tensors']):env=sum(x[:,v,:].conj().T@env@y[:,v,:] for v in range(a['dimension']))
    return complex(env[0,0])
