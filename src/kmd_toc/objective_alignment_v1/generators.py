"""One local-problem API; only proposal generation differs between controls."""
from dataclasses import dataclass,asdict
from copy import deepcopy
from itertools import permutations
from math import factorial
from pathlib import Path
import hashlib,json,random,time,resource
from kmd_toc.main_experiment_d.quantum import backend_modules
from kmd_toc.nkr_p2_study.model import pick
from kmd_toc.d_local_design.model import Decision
from kmd_toc.measurement_audit_v1.measurement import physical_payload,digest_payload
from kmd_toc.common_initial_v1.plans import dump

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

@dataclass(frozen=True)
class Case:
    local:object
    lookup:dict
    physical_initial_hash:str
    problem_hash:str
    od_hash:str
    case_hash:str

def case_digest(case):
    return digest({'local':case.local.payload(),'lookup':case.lookup,
        'physical_initial_hash':case.physical_initial_hash,'problem_hash':case.problem_hash,'od_hash':case.od_hash})

def prepare(p,plan,n,seed,seen=None):
    if type(seed) is not int or seed<0:raise ValueError('EXPLICIT_NONNEGATIVE_LOCAL_SEED')
    local=pick(p,plan,set() if seen is None else set(seen),n,seed)
    if local is None:raise ValueError('NO_ELIGIBLE_LOCAL_PROBLEM')
    q,_=backend_modules()  # read-only pure oracle/codec; no circuit or SDK execution
    lookup=q.boundary_lookups(p,plan,local);physical=digest_payload(physical_payload(plan))
    value={'local':local.payload(),'lookup':lookup,'physical_initial_hash':physical,
           'problem_hash':p.fingerprint,'od_hash':p.od.fingerprint}
    return Case(local,lookup,physical,p.fingerprint,p.od.fingerprint,digest(value))

def labels(decision,case):
    ids={s:i+1 for i,s in enumerate(case.local.customer_ids)}
    return tuple(ids[s] for s in decision.trip_1)+(0,)+tuple(ids[s] for s in decision.trip_2)

def proxy(decision,case):
    decision.validate(case.local.customer_ids);order=labels(decision,case);c=case.lookup
    import math
    return math.fsum([c['first'][order[0]],c['last'][order[-1]],
                     *(c['edge'][a][b] for a,b in zip(order,order[1:]))])/c['bound_m']

def proposal(decision,case,source,*,count=None,bits=None):
    return {'decision':decision,'proxy':proxy(decision,case),'candidate_id':digest(asdict(decision)),
            'source':source,'sample_count':count,'measured_bits':bits}

def persist(path,items,receipt):
    path=Path(path);path.mkdir(parents=True,exist_ok=False)
    dump(path/'GENERATION.json',{'receipt':receipt,'proposals':[{**r,'decision':asdict(r['decision'])} for r in items]})

class Classical:
    condition_id='D_classical'
    def __init__(self,method,*,evaluations,seed,enumeration_cap=40320):
        if method not in ('enumerate','random','greedy','local_search'):raise ValueError('CLASSICAL_METHOD')
        if type(evaluations) is not int or evaluations<1:raise ValueError('POSITIVE_GENERATION_EVALUATIONS')
        if type(seed) is not int or seed<0:raise ValueError('EXPLICIT_NONNEGATIVE_CLASSICAL_SEED')
        self.method=method;self.evaluations=evaluations;self.seed=seed;self.enumeration_cap=enumeration_cap

    def generate(self,p,plan,case,output):
        begin=time.perf_counter();cpu=time.process_time();rng=random.Random(self.seed)
        n=case.local.n;universe=factorial(n+1);cache={};count=0;passes=0
        def evaluate(order):
            nonlocal count
            if count>=self.evaluations:return None
            count+=1;split=order.index(0);ids=case.local.customer_ids
            decision=Decision(tuple(ids[i-1] for i in order[:split]),tuple(ids[i-1] for i in order[split+1:]))
            r=proposal(decision,case,'classical_'+self.method)
            cache.setdefault(r['candidate_id'],r);return r
        if self.method=='enumerate':
            if universe>self.enumeration_cap:raise ValueError('ENUMERATION_SCOPE_TOO_LARGE_USE_SAMPLING')
            for order in permutations(range(n+1)):
                if evaluate(order) is None:break
        elif self.method=='random':
            for _ in range(self.evaluations):
                order=list(range(n+1));rng.shuffle(order);evaluate(tuple(order))
        elif self.method=='greedy':
            # Greedy construction of an ordered two-trip separator path.
            remaining=set(range(n+1));order=[];c=case.lookup
            while remaining:
                nxt=min(remaining,key=lambda b:(c['first'][b] if not order else c['edge'][order[-1]][b],b))
                order.append(nxt);remaining.remove(nxt)
            evaluate(tuple(order))
        else:
            order=list(range(n+1));rng.shuffle(order);current=evaluate(tuple(order))
            while count<self.evaluations:
                passes+=1
                improved=False
                for i in range(n):
                    for j in range(i+1,n+1):
                        other=order.copy();other[i],other[j]=other[j],other[i]
                        r=evaluate(tuple(other))
                        if r is None:break
                        if (r['proxy'],r['candidate_id'])<(current['proxy'],current['candidate_id']):
                            order=other;current=r;improved=True
                    if count>=self.evaluations:break
                if not improved:break
        items=sorted(cache.values(),key=lambda r:(r['proxy'],r['candidate_id']))
        receipt={'condition_id':self.condition_id,'algorithm':self.method,'case_hash':case.case_hash,
            'generation_wall_s':time.perf_counter()-begin,'generation_CPU_s':time.process_time()-cpu,
            'objective_evaluations':count,'unique_candidates':len(items),'declared_local_universe':universe,
            'complete_local_enumeration':self.method=='enumerate' and count==universe,
            'quantum_shots':0,'optimization_iterations':passes,'seed':self.seed,
            'iteration_definition':'neighbor-search passes for local_search; no optimizer for other methods',
            'RSS_highwater_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            'quantum_executed':False,'cost_function':'shared boundary_D_v2 distance proxy; no W or LP duals'}
        persist(output,items,receipt);return items,receipt

class Quantum:
    condition_id='D_quantum'
    def __init__(self,protocol,*,tiny_validation=False):
        self.protocol=deepcopy(protocol);self.tiny=tiny_validation

    def generate(self,p,plan,case,output):
        from kmd_toc.nkr_unlimited.kernel import run
        path=Path(output);path.mkdir(parents=True,exist_ok=False)
        if case.local.n not in (10,12):
            if not self.tiny or case.local.n!=2:raise ValueError('RESEARCH_N_NOT_APPROVED; ONLY_EXPLICIT_N2_DIAGNOSTIC')
            if len(p.stops)>8:raise ValueError('TINY_DIAGNOSTIC_SIZE')
            self.protocol['numerical']['bond_by_n']['2']=32
        begin=time.perf_counter();cpu=time.process_time()
        decoded,meta=run(p,plan,case.local,self.protocol,path/'kernel')
        items=[]
        for energy,bits,decision,count in decoded:
            r=proposal(decision,case,'measured_quantum',count=count,bits=bits)
            if abs(r['proxy']-energy)>1e-12:raise ValueError('QUANTUM_CLASSICAL_PROXY_MISMATCH')
            items.append(r)
        items.sort(key=lambda r:(r['proxy'],r['candidate_id']))
        progress=[json.loads(line) for line in (path/'kernel/evaluations.jsonl').read_text().splitlines()]
        proxy_scores=sum(len(r['counts']) for r in progress if r.get('event')=='sampling_completed')
        receipt={'condition_id':self.condition_id,'algorithm':'existing p2 finite-shot MPS kernel',
            'case_hash':case.case_hash,'quantum_executed':True,
            'generation_wall_s':time.perf_counter()-begin,'generation_CPU_s':time.process_time()-cpu,
            'objective_evaluations':proxy_scores,'optimizer_objective_calls':meta['nfev'],
            'sample_level_objective_observations':meta['training_shots_actual']+meta['final_shots_actual'],
            'unique_candidates':len(items),'optimization_iterations':None,
            'optimizer_function_evaluations':meta['nfev'],'iteration_definition':'COBYLA nit unavailable; nfev recorded separately',
            'quantum_shots':meta['training_shots_actual']+meta['final_shots_actual'],
            'RSS_highwater_MiB':meta['RSS_highwater_MiB'],'kernel':meta,
            'cost_function':'same shared boundary_D_v2 distance proxy; no W or LP duals',
            'objective_evaluation_scope':'distinct-bitstring proxy scores per circuit evaluation; sample counts and optimizer calls separately recorded'}
        dump(path/'GENERATION.json',{'receipt':receipt,'proposals':[{**r,'decision':asdict(r['decision'])} for r in items]})
        return items,receipt

class MeasuredReplay:
    """Postprocessing a pinned measured batch for cap diagnostics, not a Q run."""
    condition_id='D_quantum'
    def __init__(self,path,expected_sha256):self.path=Path(path);self.expected=expected_sha256
    def generate(self,p,plan,case,output):
        from kmd_toc.common_initial_v1.plans import sha
        if sha(self.path)!=self.expected:raise ValueError('MEASURED_BATCH_HASH_MISMATCH')
        value=json.loads(self.path.read_text());original=value['receipt']
        if original['case_hash']!=case.case_hash:raise ValueError('REPLAY_NOT_SAME_LOCAL_CASE')
        items=[{**r,'decision':Decision(tuple(r['decision']['trip_1']),tuple(r['decision']['trip_2']))} for r in value['proposals']]
        receipt={**original,'quantum_executed':False,'replay_only':True,'source_generation_sha256':self.expected,
            'original_generation_receipt':original,'generation_wall_s':0.,'generation_CPU_s':0.,
            'objective_evaluations':0,'quantum_shots':0,'optimization_iterations':0,
            'optimizer_function_evaluations':0,'optimizer_objective_calls':0,'sample_level_objective_observations':0}
        persist(output,items,receipt);return items,receipt
