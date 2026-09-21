"""Prospective A/B design only. No optimizer, Aer.run, or scientific sampling API.

Read immutable existing conditions; write only this design's new output directory.
"""
from pathlib import Path
import csv, hashlib, itertools, json, os, sys, time
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '05_src'))
BASE = ROOT / 'reproducibility/outputs/traffic_simulation'
OUT = BASE / 'r24_qaoa_initial_state_cross_condition_reproducibility_spec/20260919_v1'
DIRECT = BASE / 'r24_direct_qubo_exact_validation/20260916_v1'
MULTI = BASE / 'r24_direct_qubo_multivehicle_validation/20260916_v1'
OLD = BASE / 'r24_qaoa_standard_x_vs_hybrid_comparison/20260917_v1'
AUD = BASE / 'r24_qaoa_initial_state_mixer_ablation/20260917_v1'
EXEC = BASE / 'r24_qaoa_ablation_execution_spec/20260917_v1'
SCI = BASE / 'r24_qaoa_initial_state_mixer_ablation_scientific/20260917_v1'
DONE = SCI / 'scientific_execution_20260919_v1'
ANCHOR = 'R24-RND-N002-R01-RHO050'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
digest = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()

def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

def table(name, rows):
    rows = list(rows)
    with (OUT / name).open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader()
        w.writerows({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in r.items()} for r in rows)

def route_words(n, m):
    # Only structural node indices enter: no demands, costs, feasible/optimal witnesses.
    return sorted(sum(1 << (slot * (n + 1) + node) for slot, node in enumerate(a))
                  for a in itertools.product(range(n + 1), repeat=n*m)
                  if all(a.count(i) == 1 for i in range(1, n+1)))

def audit():
    start = time.monotonic()
    from traffic_simulation.r24_classical_reference.r24_cvrp_model import load_instance
    from traffic_simulation.r24_qaoa_smoke.adapter import Adapter
    policy = dict(criteria=['Direct QUBO PASS', 'independent validator PASS',
        'complete feasible authority', 'proven optimum', 'fixed variable order',
        'current Adapter supports n=2,N in {10,20}', 'unchanged resource gate',
        'minimum-integer visit/slot route plus uniform slack transferable',
        'A and B constructed in identical Standard X pipeline'],
        ranking='Anchor first; prefer unused independent base; then maximize number of novel (N,m,ordered demands,actual_rho) features; ties ascending condition ID.',
        target_total_conditions=3, reason='Lower end of requested 3–4, conserving unchanged global resource budgets.',
        forbidden_selection_inputs=['QAOA samples','QAOA energies','successful seeds','effect directions'],
        initial_state_filter='No redesign; only deterministic size adaptation of existing structural rule.',
        budget_policy='600 per condition/p cumulative across A/B,2000 overall; no automatic retries; no simulated preparation diagnostics.',
        written_before_candidate_evaluation=True)
    dump('SELECTION_POLICY.json', policy)
    dump('TIME_ESTIMATE.json', dict(started_utc='2026-09-19T15:40:17Z',candidate_conditions=None,
        planned_conditions=[3,4],reused_scientific_conditions=1,new_scientific_conditions=[2,3],
        estimated_minutes=[30,60],worst_case_minutes=90,scientific_optimizer_runs=0,scientific_final_sampling_runs=0,
        static_validations=policy['criteria'],circuit_preflights='construct/transpile A/B; analytic memory and historical runtime estimates; zero Aer submissions',
        dominant_factors=['source and reuse audit','structural support enumeration','circuit compilation'],
        stop_conditions=['missing authority','hash/config mismatch','initial-state redesign','unchanged gate or budget failure']))
    protected = {}
    for d in [DIRECT,MULTI,OLD,AUD,EXEC,SCI,BASE/'r24_qaoa_hybrid_initial_state_and_comparison_spec/20260917_v1',BASE/'r24_qaoa_mixer_candidate_analysis/20260916_v1',BASE/'r24_direct_qubo_penalty_landscape_review/20260916_v1',BASE/'r24_qaoa_aer_preflight/20260916_v1']:
        for p in d.rglob('*'):
            if p.is_file(): protected[str(p.relative_to(ROOT))] = sha(p)
    for p in (ROOT/'05_src/traffic_simulation').rglob('*.py'):
        if p.parent != Path(__file__).parent: protected[str(p.relative_to(ROOT))] = sha(p)
    dump('PROTECTED_SHA256.json', protected)
    rows=[]
    paths = sorted((DIRECT/'conditions').glob('*.json'))
    ids = {p.stem for p in paths}
    paths += [p for p in sorted((MULTI/'conditions').glob('*.json')) if p.stem not in ids]
    for p in paths:
        s=read(p);cid=p.stem;n=s['n'];m=s['m'];reasons=[]
        inst=load_instance(BASE/'r24_benchmark_instance_suite/20260915_v1',cid.rsplit('-RHO',1)[0],cid)
        exact=p.parent.parent==DIRECT
        N=len(s.get('variable_order',s.get('bits',[])))
        secondary=read(MULTI/'conditions'/p.name) if (MULTI/'conditions'/p.name).exists() else {}
        secondary_pass=secondary.get('status')=='PROVEN_QUBO_OPTIMAL' and secondary.get('proof_complete',False) and secondary.get('certificate_check',{}).get('status')=='PASS'
        formulation=(s['status']=='PASS' or secondary_pass) if exact else secondary_pass
        validator=s.get('validator_status')=='VALID_SOLUTION' or (secondary_pass and secondary.get('validator_status')=='VALID_SOLUTION')
        if not validator and not exact:
            validator=s.get('independent_validator_status')=='VALID_SOLUTION'
        refpath=BASE/'r24_classical_reference_benchmark/20260915_v1/conditions'/p.name
        ref=read(refpath) if refpath.exists() else {}
        optimum=ref.get('optimality_proven',False) and ref.get('validator_status')=='VALID_SOLUTION'
        authority=exact and s.get('states_enumerated')==2**N and s.get('feasible_states',0)>0
        pipeline=n==2 and N in (10,20) and exact
        mapping=bool(s.get('variable_order'))
        if not formulation: reasons.append('DIRECT_QUBO_NOT_PASS')
        if not validator: reasons.append('VALIDATOR_NOT_PASS')
        if not optimum: reasons.append('MISSING_PROVEN_OPTIMUM')
        if not authority: reasons.append('MISSING_COMPLETE_FEASIBLE_AUTHORITY_IN_CURRENT_PIPELINE')
        if not pipeline: reasons.append('CURRENT_PIPELINE_UNSUPPORTED_SIZE')
        if not mapping: reasons.append('MISSING_ADAPTER_VARIABLE_ORDER')
        if pipeline:
            ad=Adapter(cid)
            assert ad.N==N and len(set(s['variable_order']))==N
        structural=mapping and N==m*n*(n+1)+4*m
        transfer='DIRECTLY_TRANSFERABLE' if structural and n==2 and m==2 else 'TRANSFERABLE_WITH_DETERMINISTIC_SIZE_ADAPTATION' if structural else 'NOT_TRANSFERABLE_WITHOUT_REDESIGN'
        if not structural:reasons.append('INITIAL_STATE_NOT_TRANSFERABLE_WITHOUT_REDESIGN')
        rows.append(dict(condition=cid,independent_base=inst.instance_id,rho_condition=cid.rsplit('-',1)[1],
            structural_relation='rho siblings share base customers/arcs/demands; not independent instances',
            n=n,m=m,qubits=N,capacity=inst.capacity,demands=[inst.demands[c] for c in inst.customers],
            actual_rho=inst.actual_rho,target_rho=inst.target_rho,source=str(p.relative_to(ROOT)),source_sha256=sha(p),
            formulation_pass=formulation,multivehicle_certificate_pass=secondary_pass,validator_pass=validator,feasible_authority_pass=authority,optimum_known=optimum,
            variable_order_pass=mapping,pipeline_pass=pipeline,A_ready=pipeline,B_transferable=transfer,
            resource_estimate_pass=pipeline,eligible=not reasons,exclusion_reasons=reasons,
            selected=False,selection_reason=None))
    selected=[next(r for r in rows if r['condition']==ANCHOR)]
    assert selected[0]['eligible']
    while len(selected)<policy['target_total_conditions']:
        candidates=[r for r in rows if r['eligible'] and r not in selected and r['independent_base'] not in {x['independent_base'] for x in selected}]
        if not candidates:break
        def novelty(r):
            return sum(json.dumps(r[k]) not in {json.dumps(x[k]) for x in selected} for k in ['qubits','m','demands','actual_rho'])
        selected.append(sorted(candidates,key=lambda r:(-novelty(r),r['condition']))[0])
    for r in rows:
        r['selected']=r in selected
        r['selection_reason']='ANCHOR_EXACT_REUSE' if r['condition']==ANCHOR else 'PREDECLARED_STRUCTURAL_DIVERSITY_RANK' if r['selected'] else 'ELIGIBLE_NOT_SELECTED_FIXED_THREE_CONDITION_SCOPE' if r['eligible'] else 'INELIGIBLE'
    dump('CANDIDATE_AUDIT.json',rows)
    table('CANDIDATE_CONDITIONS.csv',rows);table('CONDITION_ELIGIBILITY.csv',rows)
    table('INITIAL_STATE_TRANSFERABILITY.csv',[{k:r[k] for k in ['condition','qubits','B_transferable','exclusion_reasons']} for r in rows])
    summary=dict(candidate_conditions=len(rows),eligible_conditions=sum(r['eligible'] for r in rows),
        selected=[r['condition'] for r in selected],independent_bases=len({r['independent_base'] for r in selected}),
        audit_seconds=time.monotonic()-start,qubit_counts=dict(Counter(r['qubits'] for r in rows)),
        remaining_minutes=[15,30],remaining_worst_case_minutes=45)
    dump('TIME_REESTIMATE_AFTER_ELIGIBILITY.json',summary)
    print(json.dumps(summary),flush=True)

def structured(n,m):
    """Minimum integer one-hot route with each customer once; all slack is free."""
    B=m*n*(n+1)
    word=sum(1 << (slot*(n+1)+(n-slot if slot<n else 0)) for slot in range(m*n))
    return B,word

def circuits(ad, arm, settings):
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit import Parameter
    beta=Parameter('beta');gamma=Parameter('gamma')
    B,word=structured(ad.model['n'],ad.model['m'])
    qc=QuantumCircuit(ad.N)
    if arm=='A':
        for q in range(ad.N):qc.h(q)
    else:
        for q in range(B):
            if (word>>q)&1:qc.x(q)
        for q in range(B,ad.N):qc.h(q)
    qc.global_phase=-gamma*float(ad.c)
    for i,a in enumerate(ad.a):
        if a:qc.rz(2*gamma*float(a),i)
    for (i,j),v in ad.K.items():qc.rzz(2*gamma*float(v),i,j)
    for q in range(ad.N):qc.rx(2*beta,q)
    t=time.monotonic()
    compiled=transpile(qc,**{k:settings[k] for k in ['basis_gates','optimization_level','seed_transpiler','coupling_map','num_processes']})
    assert compiled.layout is None and compiled.num_qubits==ad.N
    return qc,compiled,time.monotonic()-t

def static():
    import numpy as np
    from traffic_simulation.r24_direct_qubo.model import factorized,expanded
    from traffic_simulation.r24_qaoa_smoke.adapter import Adapter
    candidates=read(OUT/'CANDIDATE_AUDIT.json');rows=[];authorities=[]
    rule=dict(status='FROZEN_GENERATION_RULE',source_files=[
        '05_src/traffic_simulation/r24_qaoa_mixer_candidate_analysis/analyze.py',
        'reproducibility/outputs/traffic_simulation/r24_qaoa_hybrid_initial_state_and_comparison_spec/20260917_v1/INITIAL_STATE_DESIGN.json',
        '05_src/traffic_simulation/r24_qaoa_hybrid_mixer_implementation_preflight/operator_impl.py'],
        variable_groups='x[k,t,node] in saved order; b[k,l], l=0..3 with weights1,2,4,8, after x',
        visit='Each nondepot customer exactly once across all vehicle slots',slot='Exactly one node per (vehicle,position)',
        route='Minimum unsigned little-endian integer route word satisfying visit/slot; depot padding. No capacity, objective, prefix, reachability or optimum filtering.',
        deterministic_size_adaptation='For n customers, m vehicles, B=m*n*(n+1): first n slots contain customer indices n,n-1,...,1; remaining slots depot0. Matches minimum integer enumeration.',
        slack='All 4*m slack qubits in |+>; no capacity completion, no slack selection',
        support='route_word + (s << B), s=0..2^(4*m)-1',normalization='Every amplitude positive 2^(-2*m); probability2^(-4*m); norm1',
        preparation='X on set route bits, H on every slack qubit; no ancilla or entangler',
        generation_inputs=['n','m','saved variable order'],
        prohibited_generation_inputs=['known feasible states','proven optimum','exact solution','cost coefficients','post-hoc QAOA results','demands'],
        known_solution_dependency=False,design_history_caveat='Original mixer/sector assessment used known feasible and optimal states to verify reachability; route selection itself did not. Uniform slack alternative selected via analytic non-eigenstate rationale. Anchor route coincides with optimum. This is a prospectively transferred existing method, not a claim that original research was blind.',
        ordering_bias='Sensitive to existing customer ordering; no relabeling or result-based route tuning',
        redesign_allowed=False)
    dump('INITIAL_STATE_CONSTRUCTION_RULE.json',rule)
    for r in candidates:
        n=r['n'];m=r['m'];N=r['qubits'];B,word=structured(n,m)
        if N!=B+4*m:
            rows.append(dict(condition=r['condition'],status='UNSUPPORTED_MAPPING'));continue
        s=read(ROOT/r['source']);size=2**(4*m)
        # Object integer supports also cover excluded N>63 without overflow.
        route_bits=np.array([(word>>q)&1 for q in range(B)],dtype=np.int64)
        bits=np.zeros((size,N),dtype=np.int64);bits[:,:B]=route_bits
        bits[:,B:]=(np.arange(size,dtype=np.int64)[:,None]>>np.arange(4*m))&1
        x=bits[:,:B].reshape(size,m,n,n+1)
        assert np.all(x.sum(axis=3)==1) and np.all(x[:,:,:,1:].sum(axis=(1,2))==1)
        h=np.array(s['h_s']);J=np.array(s['J_upper_triangle_s'])
        energies=s['offset_s']+bits@h+np.einsum('bi,ij,bj->b',bits,J,bits,optimize=True)
        uniq=[]
        for e in sorted(energies):
            if not uniq or abs(e-uniq[-1])>1e-6:uniq.append(float(e))
        var=float(np.var(energies));bet=.37;gammas=[0.,1e-6,1e-5,5e-5,.000137];probs=[]
        # Exact classical evaluation of the 4m-qubit slack factor only. No simulator.
        # Fixed route means p1 Standard X output factorizes route x slack.
        for gamma in gammas:
            v=np.exp(-1j*gamma*(energies-energies[0]))/np.sqrt(size)
            for q in range(4*m):
                a=v.reshape(-1,2,1<<q).copy()
                v=np.stack([np.cos(bet)*a[:,0]-1j*np.sin(bet)*a[:,1],np.cos(bet)*a[:,1]-1j*np.sin(bet)*a[:,0]],axis=1).reshape(-1)
            assert abs(float(np.vdot(v,v).real)-1)<1e-10
            probs.append(abs(v)**2)
        tv=max(float(abs(a-b).sum()/2) for a in probs for b in probs)
        classification='GAMMA_INDEPENDENT_AT_P1' if tv<=1e-10 else 'GAMMA_WEAKLY_DEPENDENT_AT_P1' if tv<=1e-3 else 'GAMMA_DEPENDENT_AT_P1'
        row=dict(condition=r['condition'],qubits=N,route_qubits=B,slack_qubits=4*m,route_word=str(word),support_size=size,
            support_fraction=size/2**N,unique_support_energies=len(uniq),energy_mean=float(energies.mean()),energy_variance=var,
            eigenstate=len(uniq)==1 and var<=1e-12,visit_valid_mass=1.,slot_valid_mass=1.,visit_slot_valid_mass=1.,
            gamma_classification=classification,max_pairwise_tv=tv,gamma_grid=gammas,beta=bet,
            gamma_evidence='exact classical slack-factor calculation; full joint TV equals slack TV; no Aer execution',
            fixed_route_marginal_gamma_independent=True,selected=r['selected'])
        if r['eligible']:
            ad=Adapter(r['condition']);assert word==route_words(n,m)[0]
            ef=factorized(ad.model,bits)[2]
            assert np.max(abs(ef-energies))<1e-6
            for idx in [0,size-1]:assert abs(ad.operator_basis_energy(bits[idx])-energies[idx])<1e-6
            # Complete feasible authority via all structurally valid routes and ALL slack.
            # Every feasible bitstring must obey visit/slot; independent validator then filters.
            fs=[];opt=[]
            for rw in route_words(n,m):
                bb=bits.copy();bb[:,:B]=[(rw>>q)&1 for q in range(B)]
                _,pen,_=factorized(ad.model,bb)
                valid=np.logical_and.reduce([v==0 for v in pen.values()])
                for k in np.flatnonzero(valid):
                    checked=ad.inspect(bb[k]);assert checked['feasible']
                    state=rw+(int(k)<<B);fs.append(state)
                    if checked['optimal']:opt.append(state)
            assert len(fs)==s['feasible_states'] and len(opt)==s['ground_state_count']
            authorities.append(dict(condition=r['condition'],feasible_state_ids=sorted(fs),optimal_state_ids=sorted(opt),
                complete=True,independent_validator='PASS',source_expected_count=s['feasible_states'],
                proof='All feasible states satisfy visit/slot. Exhaust all valid route assignments and all slack; filter all existing constraints; independent decode/validator on survivors.',
                used_for_initialization=False))
        rows.append(row)
    table('INITIAL_STATE_STATIC_DIAGNOSTICS.csv',rows);dump('STATIC_DIAGNOSTICS.json',rows)
    dump('FEASIBLE_AUTHORITIES.json',authorities)
    print(json.dumps(dict(static_conditions=len(rows),complete_feasible_authorities=len(authorities),selected=[r for r in rows if r.get('selected')])),flush=True)

def reuse():
    import gzip
    from qiskit import qpy
    from traffic_simulation.r24_qaoa_smoke.adapter import Adapter
    sys.path.insert(0,str(ROOT/'05_src/traffic_simulation/r24_qaoa_standard_x_vs_hybrid_comparison'))
    import run as prior
    spec=read(EXEC/'ABLATION_EXECUTION_SPEC.json');s=spec['fixed_conditions'];ad=Adapter(ANCHOR)
    assert prior.identity(ad)==spec['hashes']['runtime_identity']==read(OLD/'RUNTIME_IDENTITY.json')
    manifest=read(DONE/'ARTIFACT_SHA256.json')
    mismatches=[p for p,h in manifest.items() if sha(ROOT/p)!=h]
    assert not mismatches,mismatches
    assert read(DONE/'VALIDATION.json')['status']=='PASS'
    assert s['optimizer']['name']=='COBYLA' and s['p']==1
    lineages=[];runs=[]
    for arm in ['A','B']:
        _,compiled,_=circuits(ad,arm,s['transpilation']);symbols={p.name:p for p in compiled.parameters}
        with (AUD/f'{arm}_SYMBOLIC.qpy').open('rb') as f:old=qpy.load(f)[0]
        assert compiled==old.assign_parameters({p:symbols[p.name] for p in old.parameters})
        for rep in range(3):
            folder=(OLD/f'STANDARD_X_r{rep}') if arm=='A' else (SCI/f'B_r{rep}')
            result=read(folder/'RESULT.json');history=read(folder/'OPTIMIZER_HISTORY.json');final=result['final'];seed=s['seeds'][rep]
            assert result['initial_parameters']==[s['parameters']['initial_alpha'],s['parameters']['initial_beta']]
            assert final['seed']==seed['final_simulator_seed'] and final['shots']==2048
            assert [h['seed'] for h in history]==seed['training_simulator_seeds'][:len(history)]
            if arm=='B':
                assert result['optimizer_settings']==s['optimizer'] and result['seed_set']==seed
                assert result['identity']['execution_spec_sha256']==sha(EXEC/'ABLATION_EXECUTION_SPEC.json')
                assert result['identity']['seed_hash']==digest(seed)
            else:assert read(folder/'VALIDATION_GATE.json')['identity']==prior.identity(ad)
            assert result['incumbent']==min(history,key=lambda h:h['mean_energy'])
            for h in [*history,final]:
                target=compiled.assign_parameters({symbols['gamma']:h['parameters'][0]/s['parameters']['scale'],symbols['beta']:h['parameters'][1]});target.measure_all()
                path=folder/f"{h['role']}_{h['evaluation']}.qpy"
                with path.open('rb') as f:actual=qpy.load(f)[0]
                assert actual==target
                with gzip.open(folder/h['sample_artifact'],'rt') as f:samples=json.load(f)
                assert sum(x['count'] for x in samples)==2048
                assert abs(sum(x['count']*x['qubo_energy'] for x in samples)/2048-h['mean_energy'])<1e-6
                lineages.append(dict(arm=arm,rep=rep,role=h['role'],evaluation=h['evaluation'],qpy_sha256=sha(path),sample_sha256=sha(folder/h['sample_artifact'])))
            runs.append(dict(arm=arm,repetition=rep,source=str(folder.relative_to(ROOT)),result_sha256=sha(folder/'RESULT.json'),
                scientific_circuits=len(history)+1,decision='EXACT_REUSE_ALLOWED'))
    table('ANCHOR_REUSE_LINEAGE.csv',lineages)
    audit=dict(status='PASS',condition=ANCHOR,identity=prior.identity(ad),initial_state=dict(A='uniform20',B='minimum visit-slot route596 + uniform8 slack'),
        mixer='Standard X both arms; full saved QPY equality',optimizer=s['optimizer'],p=1,shots=2048,seeds=s['seeds'],
        decoder=prior.identity(ad)['decoder'],validator=prior.identity(ad)['validator'],runs=runs,
        manifest_hashes_checked=len(manifest),all_training_and_final_QPY_checked=len(lineages),
        scientific_condition_differences=0,decision='EXACT_REUSE_ALLOWED',anchor_reruns=0,
        resource_provenance='Historical A gate provenance retained; current gate validation not retroactively assigned.',
        preserved_scientific_classification=read(DONE/'ABC_CLASSIFICATION.json'))
    dump('ANCHOR_REUSE_AUDIT.json',audit)
    print(json.dumps(dict(anchor_reuse='PASS',runs=len(runs),circuits=len(lineages))),flush=True)

def preflight():
    from qiskit import qpy
    from traffic_simulation.r24_qaoa_smoke.adapter import Adapter
    from traffic_simulation.r24_qaoa_resource_gate_redesign.gates import SPEC,GateEngine,snapshot,process_memory
    s=read(EXEC/'ABLATION_EXECUTION_SPEC.json')['fixed_conditions'];assert s['resource_gate']==SPEC
    snap=snapshot(os.getpid(),process_memory(os.getpid()),dict(run_id='CROSS_CONDITION_STATIC_PREFLIGHT',elapsed_seconds=0))
    gate=GateEngine(snap,SPEC);trace=[]
    for i in range(6):
        if i:time.sleep(.25)
        now=snapshot(os.getpid(),process_memory(os.getpid()),dict(run_id='CROSS_CONDITION_STATIC_PREFLIGHT',elapsed_seconds=i*.25))
        decision=gate.evaluate(now);trace.append(dict(snapshot=now,decision=decision))
        assert not decision['stop'],decision
    dump('RESOURCE_GATE_PREFLIGHT.json',dict(status='PASS',spec=SPEC,observations=trace,scope='Design process live gate; future scientific process must repeat live gate and retain continuous monitoring'))
    historic=list(csv.DictReader((AUD/'RUNTIME_DECOMPOSITION.csv').open()))
    rates={a:max(float(r['backend_seconds']) for r in historic if r['label'].startswith(a+'_')) for a in ['A','B']}
    out=[]
    for r in read(OUT/'CANDIDATE_AUDIT.json'):
        if not r['eligible']:continue
        ad=Adapter(r['condition'])
        for arm in ['A','B']:
            qc,compiled,seconds=circuits(ad,arm,s['transpilation'])
            syms={p.name:p for p in compiled.parameters}
            bound=compiled.assign_parameters({syms['gamma']:s['parameters']['initial_alpha']/s['parameters']['scale'],syms['beta']:s['parameters']['initial_beta']})
            assert not bound.parameters
            measured=compiled.copy();measured.measure_all()
            assert [(measured.find_bit(z.qubits[0]).index,measured.find_bit(z.clbits[0]).index) for z in measured.data if z.operation.name=='measure']==[(i,i) for i in range(ad.N)]
            if r['selected']:
                with (OUT/f"{r['condition']}_{arm}_SYMBOLIC.qpy").open('wb') as f:qpy.dump(compiled,f)
            sv=16*2**ad.N
            # Conservative historical envelope, deliberately no scaling down for small N.
            estimate=[rates[arm]/2,rates[arm]*4]
            out.append(dict(condition=r['condition'],configuration=arm,qubits=ad.N,logical_gates=qc.size(),
                logical_2q=sum(len(z.qubits)==2 for z in qc.data),logical_depth=qc.depth(),
                transpiled_gates=compiled.size(),transpiled_2q=sum(len(z.qubits)==2 for z in compiled.data),
                transpiled_depth=compiled.depth(),transpile_seconds=seconds,statevector_bytes=sv,
                aer_memory_limit_bytes=256*1024**2,aer_memory_margin_bytes=256*1024**2-sv,
                conservative_process_estimate_bytes=512*1024**2+8*sv,
                process_preventive_margin_bytes=int(.9*4*1024**3)-(512*1024**2+8*sv),
                estimated_backend_seconds_range=estimate,estimated_full_run_seconds_range=[10,600],
                run_hard_limit_seconds=900,estimate_basis='Prior A/B diagnostic backend timings, factor0.5..4; full run includes unknown COBYLA count,2048 counts decoding/validation and monitoring; planning estimate not measurement or guarantee',
                circuit_construction='PASS',resource_pass=sv<256*1024**2 and 512*1024**2+8*sv<int(.9*4*1024**3),
                executed_Aer_circuits=0,selected=r['selected']))
    table('CIRCUIT_RESOURCE_PREFLIGHT.csv',out);dump('RESOURCE_ESTIMATES.json',out)
    print(json.dumps(dict(preflight_rows=len(out),all_pass=all(r['resource_pass'] for r in out))),flush=True)

def freeze():
    import importlib.metadata
    import numpy as np
    from traffic_simulation.r24_qaoa_smoke.adapter import Adapter
    sys.path.insert(0,str(ROOT/'05_src/traffic_simulation/r24_qaoa_standard_x_vs_hybrid_comparison'))
    import run as prior
    candidates=read(OUT/'CANDIDATE_AUDIT.json');selected=[r for r in candidates if r['selected']]
    new=[r for r in selected if r['condition']!=ANCHOR]
    fixed=read(EXEC/'ABLATION_EXECUTION_SPEC.json')['fixed_conditions']
    reuse_audit=read(OUT/'ANCHOR_REUSE_AUDIT.json');assert reuse_audit['status']=='PASS'
    resource=read(OUT/'RESOURCE_ESTIMATES.json');assert all(r['resource_pass'] for r in resource)
    env=read(OLD/'RUNTIME_ENVIRONMENT.json')
    packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    assert env['python']==sys.executable and env['packages']==packages
    dump('ENVIRONMENT_VALIDATION.json',dict(status='PASS',python=sys.executable,packages=packages,
        environment_source=str((OLD/'RUNTIME_ENVIRONMENT.json').relative_to(ROOT)),
        historical_preflight='20260916 initial PREFLIGHT_STATUS was QAOA_AER_ENVIRONMENT_MISSING; later frozen Aer venv and completed scientific results supersede that environment absence. No packages installed.'))
    # Independently enumerate injective customer positions, not the generator's formula.
    for n,m in {(r['n'],r['m']) for r in candidates}:
        words=[]
        for positions in itertools.permutations(range(n*m),n):
            assignment=[0]*(n*m)
            for customer,pos in enumerate(positions,1):assignment[pos]=customer
            words.append(sum(1<<(slot*(n+1)+node) for slot,node in enumerate(assignment)))
        assert structured(n,m)[1]==min(words)
    static_rows=read(OUT/'STATIC_DIAGNOSTICS.json')
    anchor_diag=next(r for r in static_rows if r['condition']==ANCHOR)
    historic=read(AUD/'INITIAL_ENERGY_CHECK.json')
    assert anchor_diag['unique_support_energies']==historic['unique_energy_count']
    assert abs(anchor_diag['energy_variance']-historic['energy_variance'])<1e-3
    pair=list(csv.DictReader((AUD/'GAMMA_PAIRWISE_SUMMARY.csv').open()))
    saved=next(r for r in pair if r['configuration']=='B' and float(r['beta'])==.37)
    assert abs(anchor_diag['max_pairwise_tv']-float(saved['max_pairwise_tv']))<1e-10
    # Entire 10-qubit diagonal checked against independently factorized constraint energy.
    for r in new:
        from traffic_simulation.r24_direct_qubo.model import factorized,expanded
        ad=Adapter(r['condition']);ids=np.arange(2**ad.N,dtype=np.int64)
        bits=(ids[:,None]>>np.arange(ad.N))&1
        assert np.max(abs(expanded(ad.model,bits)-factorized(ad.model,bits)[2]))<1e-6
        for q in range(ad.N):assert ad.key_to_bits(format(1<<q,f'0{ad.N}b'))[q]==1
    # Freeze condition source identities and all input metadata actually used.
    inputs={}
    condition_specs=[]
    for r in selected:
        ad=Adapter(r['condition']);base=BASE/'r24_benchmark_instance_suite/20260915_v1/instances'/r['independent_base']
        paths=[ad.source,BASE/'r24_classical_reference_benchmark/20260915_v1/conditions'/f"{r['condition']}.json"]
        paths += [base/n for n in ['base_instance.json','capacity_conditions.json','od_manifest.csv']]
        for p in paths:inputs[str(p.relative_to(ROOT))]=sha(p)
        B,word=structured(r['n'],r['m'])
        condition_specs.append(dict(**r,identity=prior.identity(ad),initial_state_adaptation=dict(route_word=word,route_qubits=B,
            x_qubits=[q for q in range(B) if (word>>q)&1],h_qubits=list(range(B,ad.N)),support_size=2**(ad.N-B)),
            penalty=ad.saved['penalty_weights_s'],variable_order=ad.saved['variable_order'],
            readiness='READY_FOR_A_B_SCIENTIFIC_COMPARISON',formulation='PASS',validator='PASS',initial_state_transfer='PASS',
            circuit_construction='PASS',resource_preflight='PASS',budget='PASS',
            execution='EXACT_REUSE' if r['condition']==ANCHOR else 'NEW_RUNS_NOT_EXECUTED'))
    for p in [ROOT/'docs/ja/R24_QAOA_RESOURCE_GATE_SPECIFICATION.md',ROOT/'05_src/traffic_simulation/r24_qaoa_resource_gate_redesign/gates.py',Path(__file__)]:
        inputs[str(p.relative_to(ROOT))]=sha(p)
    dump('FROZEN_INPUT_SHA256.json',inputs)
    ledger=read(SCI/'CIRCUIT_RESERVATION_LEDGER.json')['totals']
    anchor_charge=ledger['consumed']+ledger['reserved']
    assert anchor_charge==205
    accounting=[dict(condition=ANCHOR,new_runs=0,reused_runs=6,training_cap_per_new_run=99,new_training_max=0,new_final=0,
        new_scientific_max=0,reused_A_B_scientific=108,historical_other_or_reserved=anchor_charge-108,
        counted_total=anchor_charge,condition_p_cap=600,margin=600-anchor_charge,
        policy='Conservatively inherit complete historical205 ledger charge, including C/diagnostics/reserve only as accounting; no C scientific comparison.')]
    batches=[];runs=[]
    order=[('A',0),('B',0),('B',1),('A',1),('A',2),('B',2)]
    for r in new:
        cid=r['condition']
        accounting.append(dict(condition=cid,new_runs=6,reused_runs=0,training_cap_per_new_run=99,new_training_max=594,
            new_final=6,new_scientific_max=600,reused_A_B_scientific=0,historical_other_or_reserved=0,
            counted_total=600,condition_p_cap=600,margin=0,
            policy='Reserve100 per run before execution; failed/unknown attempts retain reservation. No retries, extra statevector checks or extra diagnostics. All preflight checks here are classical.'))
        for j,(arm,rep) in enumerate(order):
            runs.append(dict(condition=cid,configuration=arm,repetition=rep,run_id=f'{cid}_{arm}_r{rep}',
                batch=f'{cid}_batch{1+j//3}',seeds=fixed['seeds'][rep],
                initial_parameters=[fixed['parameters']['initial_alpha'],fixed['parameters']['initial_beta']],
                training_cap=99,final_circuits=1,shots_per_evaluation=2048,
                output_path=f'reproducibility/outputs/traffic_simulation/r24_qaoa_initial_state_cross_condition_scientific/20260919_v1/{cid}/{arm}_r{rep}'))
        for b in [1,2]:
            batches.append(dict(id=f'{cid}_batch{b}',condition=cid,run_ids=[x['run_id'] for x in runs if x['batch']==f'{cid}_batch{b}'],
                max_runs=3,run_wall_seconds=900,batch_cumulative_wall_seconds=3600,reserved_run_wall_seconds=2700,overhead_margin_seconds=900,
                circuit_condition_ledger='One persistent condition/p ledger across both batches; never reset600',
                total_circuit_shot_ledger='One study ledger across all batches; never reset2000/5000000',
                boundary='Predeclared separate execution batch, not a failure recovery or posthoc continuation. Stop in any batch makes study incomplete; do not replace runs.'))
    total=sum(r['counted_total'] for r in accounting);assert total==1405 and total<=2000
    table('CIRCUIT_BUDGET_ACCOUNTING.csv',accounting)
    budget=dict(condition_p_cap=600,total_cap=2000,total_shots_cap=5000000,
        new_scientific_circuits_max=1200,new_training_max=1188,new_final=12,new_scientific_shots_max=1200*2048,
        expected_new_runs=12,expected_new_scientific_circuits=None,
        expected_circuit_count_reason='Optimizer stopping unknown; reserve upper bound1200; do not use successful historical convergence as guaranteed budget.',
        anchor_exact_reused_runs=6,anchor_A_B_reused_scientific=108,anchor_inherited_ledger_charge=anchor_charge,
        total_counted_max=total,total_circuit_margin=2000-total,
        conservative_all_counted_shots_envelope=total*2048,shot_margin=5000000-total*2048,
        new_condition_margin=0,automatic_retries=0,preparation_simulation_calls=0,diagnostic_simulator_calls=0,
        gate_evidence=[str((ROOT/'docs/ja/R24_QAOA_RESOURCE_GATE_SPECIFICATION.md').relative_to(ROOT)),
            str((EXEC/'CIRCUIT_COUNT_DEFINITION.json').relative_to(ROOT)),str((SCI/'CIRCUIT_RESERVATION_LEDGER.json').relative_to(ROOT))],
        accounting_semantics=read(EXEC/'CIRCUIT_COUNT_DEFINITION.json'),
        batches=batches,wall_scope='Use user-requested separate predeclared execution batches for wall allocations. Each retains original900s/run and3600s cumulative gate. Circuit and shot ledgers remain cumulative across batches. No reset on failure.',
        alternatives_priority=['exact anchor reuse adopted','three conditions selected instead of four','four predeclared3-run execution batches to fit worst-case wall allocations'],
        optimizer_budget_reduction=False)
    classification=dict(precedence=['incomplete','reproduced','partially_reproduced','not_reproduced'],
        per_condition_positive=dict(pooled_feasible_delta='B-A > 0',pooled_mean_distance_delta='B-A < 0',
            feasible_paired_consistency='at least2/3 repetition-level B-A >0',distance_paired_consistency='at least2/3 B-A <0',
            structure_pooled='visit,slot,visit+slot rates each B-A >=0 AND visit+slot B-A >0',
            structure_paired='at least2/3 repetitions have visit+slot B-A >0',
            all_requirements=True,ties='Zero is not positive; zero structure visit/slot is allowed only under nonnegative clauses',numeric_tolerance=1e-12),
        INITIAL_STATE_CROSS_CONDITION_STUDY_INCOMPLETE='Any frozen condition missing a valid3+3 paired final dataset, authority/hash failure, resource/budget stop or changed science; takes precedence; report completed effects but no replacement.',
        INITIAL_STATE_EFFECT_REPRODUCED_ACROSS_SMALL_CONDITIONS='Both of the two new independent bases satisfy every per-condition-positive criterion. Anchor is reference and does not count toward two new replications.',
        INITIAL_STATE_EFFECT_PARTIALLY_REPRODUCED='Exactly one of two new independent bases satisfies every criterion; all frozen datasets complete.',
        INITIAL_STATE_EFFECT_NOT_REPRODUCED='Neither new independent base satisfies every criterion; all datasets complete. Not proof of absence of any effect.',
        interpretation='Exploratory directional reproducibility, not statistical significance, general superiority, causal necessity, or quantum advantage.',
        pooling='No cross-condition shot pooling or significance test; each condition gets equal one-condition assessment; rho siblings never independent bases.',
        optimal_rate='Always report primary metric and paired differences; not an extra success requirement given rare events.')
    stop=['No scientific execution authorized in this task',
        'Any input/hash/variable order/circuit/parameter/optimizer/decoder/validator mismatch',
        'Initial-state redesign, result-based selection or known-solution injection required',
        'Original live RSS/cgroup/PSI/swap/host gates stop; save durable snapshot first',
        'Reserved condition/p circuits would exceed600, study2000 or5000000 shots',
        'Per-run900s, per-predeclared-batch3600s, heartbeat300s; retain cumulative circuit ledgers',
        'Any failed/unknown submission remains charged; no retry or replacement or posthoc exclusion',
        'External cap99: retain earliest minimum finite training-energy incumbent and execute reserved final only if all gates pass',
        'Insufficient remaining wall/circuit/shot reservation before next run: incomplete, never silently reduce settings']
    metrics=dict(primary=['feasible_sample_rate','optimal_sample_rate','mean_nearest_feasible_distance'],
        structure=['visit_valid_rate','slot_valid_rate','visit_slot_valid_rate'],
        frequency_weighted=True,final_only=True,shots_per_run=2048,pooled_shots_per_arm_condition=6144,
        feasible='Unchanged decoder and independent validator PASS; no repair or postselection',
        optimal='Feasible and absolute objective difference from saved proven optimum <=1e-7',
        distance='Minimum Hamming distance over complete condition-specific FEASIBLE_AUTHORITIES.json; same raw saved variable ordering',
        structure_definition='Existing factorized penalty residual visit==0, slot==0, both==0 respectively',
        effects=['delta_P_feasible_j=P_B-P_A','delta_d_j=d_B-d_A','delta_P_optimal_j=P_B-P_A',
            'delta_visit_j','delta_slot_j','delta_visit_slot_j','all repetition-level paired counterparts'],
        effect_outputs=['PER_CONDITION_EFFECTS.csv','PAIRED_EFFECTS.csv','CROSS_CONDITION_CLASSIFICATION.json'],
        component_retention='Optional anchor legacy component only; no hybrid graph or component metric constructed for new conditions.',
        undefined='null, not0; incomplete repetitions not discarded or replaced')
    spec=dict(status='INITIAL_STATE_CROSS_CONDITION_REPRODUCIBILITY_SPEC_FROZEN',version='20260919_v1',
        created_date_JST='2026-09-20',scientific_execution_authorized=False,scientific_execution_performed=False,
        selected_conditions=condition_specs,anchor_reuse=dict(condition=ANCHOR,decision='EXACT_REUSE_ALLOWED',runs=reuse_audit['runs']),
        A=dict(initial='Uniform |+>^N',mixer='Standard X exp(-i beta sum X)'),
        B=dict(initial='Minimum integer visit/slot route basis tensor uniform slack',mixer='Standard X exp(-i beta sum X)'),
        initial_state_rule='INITIAL_STATE_CONSTRUCTION_RULE.json',condition_adaptations='selected_conditions[].initial_state_adaptation',
        optimizer=fixed['optimizer'],parameters=fixed['parameters'],p=1,shots=fixed['shots'],repetitions_per_configuration=3,
        seed_mapping=fixed['seeds'],seed_policy='Exact existing repetition mappings reused across A/B and conditions; streams remain training/final disjoint. Conditions are different instances, not claims of independent RNG streams.',
        optimizer_seed=None,initial_parameter_seed=None,simulator=fixed['simulator'],transpilation=fixed['transpilation'],
        resource_gate=fixed['resource_gate'],circuit_budget=budget,new_runs=runs,metrics=metrics,classification_rules=classification,
        stop_conditions=stop,condition_selection_policy='SELECTION_POLICY.json',
        invariant_within_condition=['Direct QUBO','coefficients','penalty','cost Hamiltonian','p','Standard X mixer','optimizer','optimizer settings','shots','repetitions','seed mapping','initial parameters','decoder','validator','transpilation','Aer backend','resource gate'],
        only_A_B_difference='initial state',
        future_worker_requirements=['Implement both selected10-qubit conditions using frozen circuit generator/Adapter and complete authority; current B-only worker is anchor-specific and must not be launched unchanged.',
            'Port existing validated reservation/claim, monitoring and COBYLA evaluation semantics without changing settings; validate in dry-run before separate scientific authorization.',
            'Static preparation and QPY/hash checks only; additional simulated validation would not fit condition600 reservation.',
            'Recheck protected inputs, environment and live gate before execution; full reserved initial parameters and seeds must match.'],
        limitations=['Only n=2,3 independent bases; rho labels all050 but actual rho differs. No general capacity/size claim.',
            'New10-qubit cases have m=1 and Q14; anchor20-qubit has m=2,Q14. Capacity is not varied.',
            'Anchor outcomes already known and used only as motivation; new selection used metadata,never prior QAOA performance.',
            'Fixed route ordering bias and original design reachability audit remain disclosed.',
            'Freeze establishes a prospective comparison, not reproduced scientific results.'])
    assert len(runs)==12 and len({r['independent_base'] for r in selected})==3
    assert all(not (ROOT/r['output_path']).exists() for r in runs)
    dump('INITIAL_STATE_CROSS_CONDITION_EXECUTION_SPEC.json',spec)
    dump('STUDY_SELECTION.json',dict(status=spec['status'],selected_conditions=[r['condition'] for r in selected],
        independent_bases=[r['independent_base'] for r in selected],candidate_count=len(candidates),eligible_count=sum(r['eligible'] for r in candidates),
        excluded=[dict(condition=r['condition'],reasons=r['exclusion_reasons']) for r in candidates if not r['eligible']],
        eligible_not_selected=[dict(condition=r['condition'],reason=r['selection_reason']) for r in candidates if r['eligible'] and not r['selected']],
        frozen_no_posthoc_additions_or_removals=True))
    table('SELECTION_TABLE.csv',[dict(condition=r['condition'],independent_base=r['independent_base'],qubits=r['qubits'],A_ready=r['A_ready'],
        B_transferable=r['B_transferable'],optimum_known=r['optimum_known'],resource_PASS=r['resource_estimate_pass'],selected=r['selected']) for r in candidates])
    mismatches=[p for p,h in read(OUT/'PROTECTED_SHA256.json').items() if sha(ROOT/p)!=h];assert not mismatches,mismatches
    dump('VALIDATION.json',dict(status='PASS',freeze_status=spec['status'],formulation='PASS',validator='PASS',
        initial_state_rule='PASS',independent_minimum_integer_enumeration='PASS_ALL_OBSERVED_N_M',
        known_solution_generation_dependency=False,complete_feasible_authorities=30,
        anchor_energy_and_gamma_saved_diagnostic_match='PASS',new_full_basis_factorized_energy_check='PASS',
        anchor_exact_reuse='PASS_6_RUNS_108_CIRCUITS',circuit_construction='PASS_60_A_B_CIRCUITS',
        resource_preflight='PASS',budget='PASS_1405_LE_2000_AND600_PER_NEW_CONDITION',
        wall_budget='PASS_FOUR_PREDECLARED_BATCHES_2700_RESERVED_PLUS900_OVERHEAD_EACH',
        source_preservation='PASS',protected_files=len(read(OUT/'PROTECTED_SHA256.json')),
        scientific_optimizer_runs=0,scientific_final_sampling_runs=0,Aer_submissions=0,
        scientific_reproducibility='NOT_YET_EVALUATED',future_live_gate='REQUIRED',
        future_execution_worker='IMPLEMENTATION_AND_DRY_RUN_REQUIRED_NOT_PART_OF_DESIGN_FREEZE'))
    print(json.dumps(dict(status=spec['status'],budget=total,new_runs=len(runs))),flush=True)

if __name__=='__main__':
    {'audit':audit,'static':static,'reuse':reuse,'preflight':preflight,'freeze':freeze}[sys.argv[1]]()
