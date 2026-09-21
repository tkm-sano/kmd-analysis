"""Supplemental v2 offline audit. Existing v1/spec/scientific files stay read-only."""
from pathlib import Path
import csv,hashlib,json,os,subprocess,threading,time,types
import numpy as np
from traffic_simulation.r24_vrptw_structured_initial_state.construction import construct,validate_state,preparation
from traffic_simulation.r24_vrptw_structured_initial_state import validate as legacy
from traffic_simulation.r24_vrptw_qaoa_worker.adapter import Adapter
from traffic_simulation.r24_vrptw_qaoa_worker.contract import load,environment
from traffic_simulation.r24_vrptw_quantum_encoding_preflight.model import factorized,expanded
from traffic_simulation.r24_qaoa_resource_gate_redesign.gates import GateEngine,snapshot,process_memory
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reproducibility/outputs/traffic_simulation'
OUT=BASE/'r24_vrptw_structured_initial_state/20260922_v2'
OLD=BASE/'r24_vrptw_structured_initial_state/20260922_v1'
SPEC=BASE/'r24_vrptw_uniform_vs_structured_comparison_spec/20260922_v1'
FREEZE=BASE/'r24_vrptw_qaoa_execution_spec/20260921_v1'
STUDY=BASE/'r24_vrptw_qaoa_execution/20260921_v1'
CV=BASE/'r24_qaoa_initial_state_cross_condition_reproducibility/20260920_v1/final_cross_condition_audit'
DOCS=['05_src/traffic_simulation/CURRENT_RESEARCH_DESIGN.md','docs/ja/R24_VALIDATION_AND_QAOA_REPORT.md','docs/ja/R24_PROBLEM_SOLUTION_DECISION_RECORD.md','05_src/traffic_simulation/RESEARCH_PROGRESS_AND_DECISION_RECORD.md']
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
def dump(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def rows(p):
    with Path(p).open() as f:return list(csv.DictReader(f))
def table(name,rr):
    fields=list(dict.fromkeys(k for r in rr for k in r))
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rr:w.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()})

class Guard:
    def __enter__(self):
        self.done=threading.Event();self.trace=[];self.peak=0;self.start=time.monotonic();self.engine=GateEngine(snapshot(os.getpid(),process_memory(os.getpid()),{}),load()['resource_gate'])
        self.poll();self.t=threading.Thread(target=self.loop,daemon=True);self.t.start();time.sleep(1.25);return self
    def poll(self):
        p=process_memory(os.getpid(),self.peak);self.peak=p['peak_rss_bytes'];s=snapshot(os.getpid(),p,dict(phase='offline_validation'));d=self.engine.evaluate(s)
        if time.monotonic()-self.start>900:d['stop']=True;d['stop_reasons'].append('OFFLINE_WALL_LIMIT')
        self.trace.append(dict(snapshot=s,decision=d))
        if d['stop']:
            dump('STOP_SNAPSHOT.json',self.trace[-1]);os._exit(75)
    def loop(self):
        while not self.done.wait(.25):self.poll()
    def __exit__(self,*args):
        self.done.set();self.t.join();self.poll();dump('resource/'+str(time.time_ns())+'.json',self.trace)

def fidelity_check(actual,target):
    if actual.shape!=target.shape or not np.isfinite(actual).all() or not np.isfinite(target).all():raise ValueError('malformed amplitude vector')
    n=float(np.vdot(actual,actual).real);nt=float(np.vdot(target,target).real)
    if abs(n-1)>1e-10 or abs(nt-1)>1e-10:raise ValueError('non-normalized vector')
    fidelity=float(abs(np.vdot(target,actual))**2);err=float(np.max(abs(actual-target)))
    if abs(fidelity-1)>1e-10 or err>1e-12:raise ValueError('preparation fidelity mismatch')
    return dict(norm=n,target_norm=nt,fidelity=fidelity,max_amplitude_difference=err,negative_probabilities=False,NaN_inf=False,status='PASS')

def moments(energies):
    e=np.asarray(energies,dtype=np.longdouble)
    if not len(e) or not np.isfinite(e).all():raise ValueError('invalid energies')
    mean=np.mean(e);variance=np.mean((e-mean)**2)
    # Existing CVRP ablation classification threshold, not retuned after observation.
    eigenstate=bool(variance<=1e-12)
    return dict(mean_energy=float(mean),energy_variance=float(variance),energy_std=float(np.sqrt(variance)),eigenstate=eigenstate,variance_zero_threshold=1e-12)

def slack_distribution(energies,gamma,beta):
    """Exact factor calculation, not full QAOA simulation or sampling.
    Fixed route makes diagonal cost factor into a route phase and a slack vector.
    Standard X factorizes; joint-probability TV equals slack-probability TV.
    """
    v=np.exp(-1j*gamma*np.asarray(energies))/np.sqrt(len(energies));n=(len(v)-1).bit_length()
    if 1<<n != len(v):raise ValueError('power-of-two support required')
    for q in range(n):
        x=v.reshape(-1,2,1<<q).copy();v=(np.cos(beta)*x-1j*np.sin(beta)*x[:,::-1,:]).reshape(-1)
    p=abs(v)**2
    if not np.isfinite(p).all() or abs(p.sum()-1)>1e-10 or (p<0).any():raise ValueError('invalid analytic probabilities')
    return p

def initialize():
    assert not (OUT/'PROTECTED_BEFORE.json').exists()
    protected=read(SPEC/'PROTECTED_ARTIFACTS.json')
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    for root in [OLD,SPEC]:
        for p in root.rglob('*'):
            if p.is_file():protected[str(p.relative_to(ROOT))]=sha(p)
    # Include existing notebooks; create a new supplemental notebook instead of rewriting them.
    for p in (ROOT/'notebooks/traffic_simulation').glob('R24_VRPTW*'):protected[str(p.relative_to(ROOT))]=sha(p)
    dump('PROTECTED_BEFORE.json',protected)
    for p,h in read(SPEC/'FINAL_FREEZE_MANIFEST.json')['artifacts'].items():assert sha(SPEC/p)==h
    dump('DOCUMENTS_BEFORE.json',{p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in DOCS})
    groups=rows(STUDY/'study_synthesis/INDEPENDENT_EVIDENCE_GROUPS.csv');conditions=rows(FREEZE/'SCIENTIFIC_CONDITION_SET.csv');mapping=[]
    for g in groups:
        for b in json.loads(g['members']):
            c=conditions[int(b[1:])-1];mapping.append(dict(group=g['group'],representative=conditions[int(g['representative'][1:])-1]['condition'],batch=b,condition=c['condition'],QUBO_hash=g['QUBO_hash'],role='REPRESENTATIVE' if b==g['representative'] else 'SEMANTIC_CONTROL',TW_regime=c['TW_regime']))
    table('QUBO_GROUPS.csv',mapping)
    dump('DIAGNOSTIC_PLAN.json',dict(candidate='A',new_candidates=0,construction='Unchanged CVRP-derived structural rule; no temporal-aware extension',representative_order=[g['representative'] for g in groups],preparation_evolutions=3,Aer_calls=0,full_p1_statevector_evolutions=0,
       gamma_diagnostic=dict(points=[0,load()['parameters']['initial_gamma']],beta=load()['parameters']['initial_beta'],method='exact slack-register factor calculation only',no_selection_or_tuning=True,reason='Two predetermined points test probability sensitivity; variance separately tests non-eigenstate. No sweep.'),
       numerical_tolerances=dict(norm=1e-10,fidelity=1e-10,amplitude=1e-12,variance_zero=1e-12),variance_tolerance_source='existing CVRP ablation audit.py eigenstate classification1e-12',source_spec_sha256=sha(SPEC/'FINAL_FREEZE_MANIFEST.json')))
    dump('CVRP_SOURCE_FINDINGS.json',dict(source=str(CV.relative_to(ROOT)),records=rows(CV/'CROSS_BASE_DIRECTION_CONSISTENCY.csv'),interpretation='Feasibility/distance/visit/slot improved3/3 bases; optimality improved2/3 and worsened1/3. No claim of uniform optimality benefit. These are prior CVRP findings, not new VRPTW outcomes.'))
    print(json.dumps(dict(protected=len(protected),groups=3,conditions=7)),flush=True)

def one(group):
    from qiskit import QuantumCircuit,transpile,qpy
    from qiskit.circuit import Parameter
    from qiskit.quantum_info import Statevector
    mapping=rows(OUT/'QUBO_GROUPS.csv');cid=next(r['representative'] for r in mapping if r['group']==group);old=read(OLD/'conditions'/f'{cid}.json');start=time.monotonic()
    # Pure construction occurs before new reference/Adapter access.
    state=construct(old['inputs']);validate_state(state);assert state==old['state']==construct(old['inputs'])
    with Guard() as guard:
        ad=Adapter(cid);assert ad.order==old['inputs']['variable_order'] and ad.N==state['qubits'];m=ad.model;assert not m['chains']
        support=np.array(state['support'],dtype=np.int64);bits=(support[:,None]>>np.arange(ad.N))&1
        energy=expanded(m,bits);factor_energy=factorized(m,bits)[2];assert np.max(abs(energy-factor_energy))<1e-6
        moment=moments(energy)
        if moment['eigenstate']:raise RuntimeError('INITIAL_STATE_DESIGN_BLOCKED_EIGENSTATE')
        # Reuse audited full-space calculation with an isolated output sink. Original
        # function/source globals are not modified; its replay writes only into v2.
        audit_fn=types.FunctionType(legacy.masks_and_metrics.__code__,{**legacy.masks_and_metrics.__globals__,'dump':dump},'v2_support_audit')
        metrics,waiting=audit_fn(ad,state)
        assert metrics==old['metrics'],'fresh full-support audit differs from validated v1'
        for k in ['norm','support_size','visit_mass','route_mass','capacity_encoding_mass','no_good_mass','overall_feasible_mass','optimal_mass','nearest_mean']:
            assert metrics[1][k]==old['metrics'][1][k]
        cfg=load();settings={k:cfg['transpilation'][k] for k in ['basis_gates','optimization_level','seed_transpiler','coupling_map','num_processes']}
        t=time.monotonic();prep=preparation(state);prep2=preparation(construct(old['inputs']));assert prep==prep2
        pt=transpile(prep,**settings);prep_seconds=time.monotonic()-t
        t=time.monotonic();v=Statevector.from_instruction(pt).data;sv_seconds=time.monotonic()-t
        target=np.zeros(2**ad.N,complex);target[support]=state['amplitude'];fid=fidelity_check(v,target)
        # Physical probabilities follow directly from the independently audited target.
        fid.update(structured_support_mass=float(np.sum(abs(v[support])**2)),outside_support_mass=float(np.sum(abs(np.delete(v,support))**2)),seconds=sv_seconds)
        gamma,beta=Parameter('gamma'),Parameter('beta');layer=QuantumCircuit(ad.N)
        a=-m['h']/2-(m['J'].sum(axis=0)+m['J'].sum(axis=1))/4;const=m['offset']+m['h'].sum()/2+m['J'].sum()/4
        layer.global_phase=-gamma*float(const)
        for i,c in enumerate(a):
            if c:layer.rz(2*gamma*float(c),i)
        for i,j in zip(*np.nonzero(m['J'])):
            layer.cx(int(i),int(j));layer.rz(gamma*float(m['J'][i,j])/2,int(j));layer.cx(int(i),int(j))
        layer.rx(2*beta,range(ad.N));t=time.monotonic();combined=transpile(prep.compose(layer),**settings);full_seconds=time.monotonic()-t
        assert legacy.circuit_signature(pt)==old['circuits']['preparation_transpiled']['identity']
        assert legacy.circuit_signature(combined)==old['circuits']['combined_transpiled']['identity']
        with (OLD/'circuits'/cid/'combined_symbolic.qpy').open('rb') as f:saved=qpy.load(f)[0]
        assert combined==saved.assign_parameters({p:(gamma if p.name=='gamma' else beta) for p in saved.parameters})
        parameters=cfg['parameters'];bound=combined.assign_parameters({gamma:parameters['initial_alpha']/parameters['scale'],beta:parameters['initial_beta']});assert not bound.parameters
        folder=OUT/'circuits'/group;folder.mkdir(parents=True,exist_ok=True)
        for name,qc in [('preparation',pt),('combined_symbolic',combined),('combined_bound',bound)]:
            with (folder/(name+'.qpy')).open('wb') as f:qpy.dump(qc,f)
        p0=slack_distribution(energy,0,parameters['initial_beta']);p1=slack_distribution(energy,parameters['initial_gamma'],parameters['initial_beta']);tv=float(.5*np.sum(abs(p0-p1)))
        assert tv>1e-12,'PARAMETER_SENSITIVITY_NOT_OBSERVED'
        table('SLACK_GAMMA_'+group+'.csv',[dict(slack_word=i,p_gamma0=float(x),p_frozen_gamma=float(y)) for i,(x,y) in enumerate(zip(p0,p1))])
        uniform_moment=dict(mean_energy=float(const),energy_variance=float(np.sum(a*a)+np.sum((m['J']/4)**2)),method='Uniform Ising orthogonality; expectation constant, variance sum squared Z/ZZ coefficients')
        resource=dict(group=group,condition=cid,qubits=ad.N,theoretical_statevector_bytes=16*2**ad.N,planned_memory_bytes=old['circuits']['planned_process_bytes'],preparation=legacy.counts(prep),transpiled_preparation=legacy.counts(pt),combined=legacy.counts(combined),prep_build_transpile_seconds=prep_seconds,full_build_transpile_seconds=full_seconds,delta_CX_vs_Uniform=int(combined.count_ops().get('cx',0))-int(ad.condition['p1_CX']),delta_depth_vs_Uniform=combined.depth()-int(ad.condition['p1_depth']),build_transpile_RSS_bytes=process_memory(os.getpid())['aggregate_rss_bytes'])
    result=dict(group=group,condition=cid,state=state,metrics=metrics,fidelity=fid,initial_energy=moment,Uniform_energy=uniform_moment,gamma_diagnostic=dict(gammas=[0,parameters['initial_gamma']],beta=parameters['initial_beta'],total_variation=tv,classification='GAMMA_DEPENDENT_EXACT_SLACK_FACTOR_DIAGNOSTIC',scientific_performance=False),resources=resource,peak_RSS=guard.peak,seconds=time.monotonic()-start,status='STRUCTURED_INITIAL_STATE_OFFLINE_VALIDATED',initial_parameters_usable=True,temporal_feasibility_preserved=metrics[1]['temporal_mass']==1)
    dump('groups/'+group+'.json',result);print(json.dumps(dict(group=group,status=result['status'],seconds=result['seconds'],fidelity=fid,energy=moment,gamma_TV=tv,peak_RSS=guard.peak)),flush=True)
    return result

if __name__=='__main__':
    import sys
    action=sys.argv[1]
    if action=='init':initialize()
    elif action=='first':
        environment();r=one('G1');dump('FIRST_GROUP_REESTIMATE.json',dict(status='PASS',group='G1',seconds=r['seconds'],peak_RSS=r['peak_RSS'],remaining_minutes=[10,20],completed=['construction','support/constraint audit','fidelity','circuit build','resource estimate','energy variance']))
    elif action=='rest':
        assert read(OUT/'FIRST_GROUP_REESTIMATE.json')['status']=='PASS';environment()
        for g in ['G2','G3']:one(g)
