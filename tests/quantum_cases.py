"""Synthetic inputs and output serialization for migration tests; no optimizer."""
from pathlib import Path
import hashlib,itertools,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def cases():
 data=json.loads((ROOT/'notebooks/fixtures/three_customers.json').read_text())
 a={k:np.array(data[k]) for k in ('nodes','travel','distance','partition','ready','due','service','demand')}
 a['nodes']=np.array(['DEP_006','A','B','C'])
 yield 'base3',a
 for name,change in [('time_window3',lambda b:b['due'].__setitem__(2,120)),('capacity3',lambda b:b['demand'].__setitem__(1,217)),('return3',lambda b:b['travel'].__setitem__(slice(None),10000))]:
  b={k:v.copy() for k,v in a.items()};change(b);yield name,b
 n=5;t=np.full((n,n),10);np.fill_diagonal(t,0)
 yield 'base4',dict(nodes=np.array(['DEP_006','A','B','C','D']),travel=t,distance=t*10,partition=np.zeros((n,n),int),ready=np.zeros(n,int),due=np.full(n,32400),service=np.array([0,102,102,102,102]),demand=np.array([0,1,1,1,1]))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def snapshot(builder,decoder,qualification):
 out={}
 for name,a in cases():
  model=qualification.build(a);q,poly=builder.build_C(model,a)
  terms=[[list(k),str(v)] for k,v in sorted(poly.items())]
  orders=list(itertools.permutations(range(1,len(a['nodes']))))
  codes=[builder.route_code(p,model['n']) for p in orders]
  rawcodes=range(1<<q) if q==9 else codes+[0,(1<<q)-1]
  decoded=[decoder.decode(a,[(code>>i)&1 for i in range(q)],[]) for code in rawcodes]
  witnesses=[decoder.decode(a,qualification.witness(model,p),model['ands']) for p in orders]
  out[name]={'qubits':q,'terms':terms,'route_codes':codes,'qualification_model_sha256':digest(model),'decoded_sha256':digest(decoded),'states_checked':len(decoded),'valid_states':sum(d['valid'] for d in decoded),'ancilla_witness_sha256':digest(witnesses)}
 return out
