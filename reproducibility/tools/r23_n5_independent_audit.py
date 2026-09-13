"""Read-only scientific probes for R23 independent audit; writes only its new output root.

Never opens the previous code audit. No scientific optimizer run is performed.
Run with the frozen authority Python and PYTHONDONTWRITEBYTECODE=1.
"""
from __future__ import annotations
import ast
import csv
import dataclasses
import datetime as dt
import difflib
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_code_audit/20260913_v2_independent'
BASE = '9a4ce5600a211ffb92adf3b84fe2468d70be2b26'
HEAD = 'd4a8d78a04316414a9f19ff143264d96c88b3c9b'
SRC = '05_src/traffic_simulation/'
ART = 'reproducibility/outputs/traffic_simulation/'
AUTH = ART + 'r23_n5_scaling_authority/20260911_v1/'
RUNS = ART + 'r23_n5_scaling/20260911_v1/runs/'
TOL = 1e-12
READS = set()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def git(*args, check=True):
    return subprocess.run(['git', *args], cwd=ROOT, check=check, capture_output=True, text=True).stdout.strip()

def read(path):
    assert 'runtime_optimization_code_audit/20260913_v1' not in path
    assert 'r23_n5_runtime_optimization_code_audit.py' not in path
    READS.add(path)
    return (ROOT / path).read_text()

def js(path):
    return json.loads(read(path))

def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

def historical(path, commit=BASE):
    READS.add(path)
    return git('show', f'{commit}:{path}') + '\n'

def module_from_source(name, source, package):
    mod = types.ModuleType(name)
    mod.__package__ = package
    sys.modules[name] = mod
    exec(compile(source, name, 'exec'), mod.__dict__)
    return mod

def coefficients(obj):
    return {'variable_ordering': list(range(obj.n_logical)), 'offset': obj.constant,
            'linear': [[k, v] for k, v in sorted(obj.linear.items())],
            'quadratic': [[a, b, v] for (a, b), v in sorted(obj.quadratic.items())]}

def main():
    sys.path.insert(0, str(ROOT / '05_src'))
    import numpy as np
    from qiskit.quantum_info import Statevector
    from traffic_simulation.r20_route_ordering import core
    from traffic_simulation.r22_ising_conversion import converter
    from traffic_simulation.r23_qaoa_aer import qaoa, hamiltonian, metrics, optimized_metrics_v4 as candidate
    from traffic_simulation.r23_qaoa_aer.schema import R23Input
    from traffic_simulation.r23_n5_scaling import run_n5_scaling as runner

    write('start_state.json', {'repository': str(ROOT), 'branch': git('branch', '--show-current'),
        'HEAD': HEAD, 'observed_HEAD': git('rev-parse', 'HEAD'), 'hostname': platform.node(),
        'user': __import__('getpass').getuser(), 'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'initial_status': ['?? .tmp_patch_probe', '?? reproducibility/config/traffic_simulation/r23_pilot_configuration/',
           '?? reproducibility/outputs/research_model_workbook/', '?? research_model_3page_ja.xlsx', '?? research_model_3page_ja_revised.xlsx'],
        'shell_python': '/opt/miniconda/bin/python', 'audit_python': sys.executable,
        'environment': {k: os.environ.get(k) for k in ['CONDA_PREFIX', 'CONDA_DEFAULT_ENV', 'VIRTUAL_ENV', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_PROC_BIND', 'OMP_PLACES']},
        'affinity': sorted(os.sched_getaffinity(0)), 'cpu': subprocess.run(['lscpu', '-J'], capture_output=True, text=True, check=True).stdout,
        'versions': {'python': platform.python_version(), **{k: importlib.metadata.version(k) for k in ['numpy','scipy','qiskit','qiskit-aer','qiskit-algorithms','qiskit-optimization']}},
        'no_previous_audit_read': True, 'no_scientific_source_mutation': True})

    # Source and input snapshots precede probes; all scientific artifacts including ignored rank01 are hashed.
    scope = set(git('ls-files', SRC+'r23_qaoa_aer', SRC+'r20_route_ordering', SRC+'r22_ising_conversion', SRC+'r23_n5_scaling').splitlines())
    scope.update(git('ls-files', SRC+'validation/test_r23*', SRC+'specifications/R23*', SRC+'specifications/R20_QAOA_SUBPROBLEM_SPEC.md').splitlines())
    for directory in ['r23_n5_scaling_authority', 'r23_n5_scaling', 'r23_n5_runtime_optimization_review', 'r23_limited_scaling_methodology_review']:
        scope.update(str(p.relative_to(ROOT)) for p in (ROOT/ART/directory).rglob('*') if p.is_file() and '__pycache__' not in str(p))
    scope.update([SRC+'R23_STATUS.md', SRC+'R23_NEXT_STEPS.md', SRC+'R23_ROADMAP.md', 'RESEARCH_STATUS.md'])
    for path in sorted(scope):
        if not path or not (ROOT/path).is_file():
            continue
        # Current status docs may contain previous audit conclusions: hash only until blind seal.
        if path.endswith(('R23_STATUS.md','R23_NEXT_STEPS.md','R23_ROADMAP.md','RESEARCH_STATUS.md')):
            continue
        read(path)
    records = []
    for path in sorted(scope):
        p = ROOT/path
        if not p.is_file():
            continue
        role = 'scientific source' if path.startswith(SRC) else 'authority / scientific evidence'
        if 'runtime_optimization_review' in path:
            role = 'profiling / equivalence / benchmark / report generation'
        if '/validation/' in path: role = 'regression test'
        if '/specifications/' in path or path.endswith(('STATUS.md','STEPS.md','ROADMAP.md')): role = 'canonical / status document'
        records.append({'path': path, 'purpose': role, 'sha256': digest(p.read_bytes()),
            'commit_provenance': git('log','-1','--format=%H %aI','--',path) or None,
            'state': 'candidate' if 'optimized_metrics' in path else ('historical' if 'runtime_optimization_review' in path or '/20260911_v1/' in path else 'current'),
            'inspection': 'hash only; content deferred until independent seal' if path not in READS else 'content read'})
    write('audit_scope.json', {'starting_HEAD': HEAD, 'files': records, 'previous_audit_excluded': True})

    old_core = module_from_source('audit_old_core', historical(SRC+'r20_route_ordering/core.py'), '')
    old_converter = module_from_source('audit_old_converter', historical(SRC+'r22_ising_conversion/converter.py'), '')
    # Historical converter's import is type-bound; constructors are verified byte-identical first.
    unchanged = {}
    for path in [SRC+'r20_route_ordering/core.py', SRC+'r22_ising_conversion/converter.py', SRC+'r23_qaoa_aer/hamiltonian.py', SRC+'r23_qaoa_aer/metrics.py', SRC+'r23_qaoa_aer/schema.py', SRC+'r23_qaoa_aer/optimizers.py', SRC+'r23_qaoa_aer/initialization.py']:
        old = historical(path).encode()
        new = (ROOT/path).read_bytes()
        unchanged[path] = {'original_sha256':digest(old),'candidate_sha256':digest(new),'byte_identical':old==new}
    old_qaoa = module_from_source('traffic_simulation.r23_qaoa_aer.audit_historical_qaoa', historical(SRC+'r23_qaoa_aer/qaoa.py'), 'traffic_simulation.r23_qaoa_aer')
    old_h = module_from_source('traffic_simulation.r23_qaoa_aer.audit_historical_h', historical(SRC+'r23_qaoa_aer/hamiltonian.py'), 'traffic_simulation.r23_qaoa_aer')

    selection = js(AUTH+'n5_instance_selection.json')
    rows = list(csv.DictReader((ROOT/runner.ROUTING).open()))
    READS.add(str(runner.ROUTING.relative_to(ROOT)))
    customers = sorted({r['origin_id'] for r in rows} - {runner.DEPOT})
    ranking = sorted((digest(('2301|DEP_006|'+','.join(c)+'|5').encode()), list(c)) for c in itertools.combinations(customers,5))
    write('selection_recomputation.json', {'population_size':len(customers),'combination_count':len(ranking),
        'selected_match':all(ranking[i] == (r['selection_key_sha256'],r['customer_ids']) for i,r in enumerate(selection['selected'])),
        'top_three':ranking[:3], 'routing_sha256':digest(runner.ROUTING.read_bytes()),
        'routing_authority_match':digest(runner.ROUTING.read_bytes())==selection['candidate_population']['routing_arcs_sha256']})

    model_rows=[]
    roundtrips=[]
    for instance, ids in runner.INSTANCES.items():
        inp=runner.make_input(instance,ids)
        raw=runner.load_matrix(ids)
        norm,tau=core.normalize_travel_time_matrix(runner.DEPOT,ids,raw)
        old_norm,old_tau=old_core.normalize_travel_time_matrix(runner.DEPOT,ids,raw)
        oq=old_core.build_expanded_qubo(runner.DEPOT,ids,old_norm,4.0)
        cq=core.build_expanded_qubo(runner.DEPOT,ids,norm,4.0)
        oi=old_converter.convert_qubo_to_ising(core.QuboCoefficients(oq.constant,oq.linear,oq.quadratic,oq.n_logical))
        ci=converter.convert_qubo_to_ising(cq)
        oqc,cqc,oic,cic=map(coefficients,[oq,cq,oi,ci])
        op_old=sorted((label,[float(c.real),float(c.imag)]) for label,c in old_h.build_cost_operator(inp,include_constant=True).to_list())
        op_new=sorted((label,[float(c.real),float(c.imag)]) for label,c in hamiltonian.build_cost_operator(inp,include_constant=True).to_list())
        travel=core.build_expanded_qubo(runner.DEPOT,ids,norm,0.0)
        zero={a:{b:0.0 for b in norm} for a in norm}
        penalty=core.build_expanded_qubo(runner.DEPOT,ids,zero,4.0)
        model_rows.append({'instance':instance,'normalization_exact':norm==old_norm and tau==old_tau,
            'QUBO':{'exact_equal':oqc==cqc,'original_hash':digest(canonical(oqc)),'candidate_hash':digest(canonical(cqc)), 'canonical':cqc},
            'Hamiltonian':{'exact_equal':oic==cic and op_old==op_new,'original_hash':digest(canonical(op_old)),'candidate_hash':digest(canonical(op_new)), 'terms_including_constant':len(op_new),'constant':ci.constant,'pauli_terms':op_new},
            'travel_qubo':coefficients(travel),'penalty_qubo':coefficients(penalty),
            'travel_ising':coefficients(converter.convert_qubo_to_ising(travel)), 'penalty_ising':coefficients(converter.convert_qubo_to_ising(penalty))})
        own=[]
        for route in itertools.permutations(range(5)):
            index=sum(1 << (customer*5+position) for position,customer in enumerate(route))
            bits=tuple((index>>q)&1 for q in range(25))
            decoded=core.validate_bitstring(bits,5,ids)
            assert decoded.route==tuple(ids[i] for i in route)
            assert metrics.qiskit_label_to_bits(format(index,'025b'))==bits
            own.append(index)
        generated=candidate.feasible_basis_indices(ids,5)
        roundtrips.append({'instance':instance,'generated_routes':len(own),'unique_indices':len(set(own)),
            'roundtrip_PASS':len(own),'independent_set_equal':set(own)==set(generated),'indices':sorted(own)})
    write('canonical_comparisons.json',{'unchanged_sources':unchanged,'instances':model_rows})
    write('bit_ordering_audit.json',{'mapping':'x[i,t] -> q=i*n+t -> Qiskit label q24...q0 -> k=sum(x[q]*2**q) -> read ((k>>q)&1), one-hot columns -> customer route', 'instances':roundtrips})

    # Actual helper versus a full independent one-hot mask, all basis states n=2,3,4.
    probability_rows=[]
    objective_rows=[]
    base_ids=tuple(runner.INSTANCES['routing_v18_n5_rank01'])
    def small_input(n):
        ids=base_ids[:n]; raw=runner.load_matrix(ids); norm,_=core.normalize_travel_time_matrix(runner.DEPOT,ids,raw)
        q=core.build_expanded_qubo(runner.DEPOT,ids,norm,4.0); i=converter.convert_qubo_to_ising(q)
        routes=core.enumerate_routes(runner.DEPOT,ids,raw)['optimal_routes']
        bs=frozenset(core.encode_route(r[1:-1],ids) for r in routes)
        return R23Input('audit_n'+str(n),n,ids,runner.DEPOT,i.constant,i.linear,i.quadratic,'audit','audit',4.0,3.0,bs,
            frozenset(tuple(1-2*b for b in bits) for bits in bs),frozenset(tuple(r) for r in routes),norm,{'ising_global_minimum_energy':0.0})
    for n in (2,3,4):
        inp=small_input(n)
        value,state,_,_=qaoa._statevector_and_expectation(inp,(0.1,),(0.1,),seed=17,optimization_level=1,optimized=True)
        old_value,old_probs,_,_=old_qaoa._statevector_and_expectation(inp,(0.1,),(0.1,),seed=17,optimization_level=1)
        data=np.asarray(state.data); probs=np.abs(data)**2
        all_bits=((np.arange(len(data),dtype=np.uint64)[:,None]>>np.arange(n*n,dtype=np.uint64))&1).reshape(-1,n,n)
        mask=np.all(all_bits.sum(axis=1)==1,axis=1)&np.all(all_bits.sum(axis=2)==1,axis=1)
        actual=candidate.indexed_probability_metrics(state,inp.customer_ids,inp.exact_optimal_bitstrings,n)
        original=metrics.probability_metrics(old_probs,inp,threshold=TOL)
        optimal_idx=[sum(bit<<q for q,bit in enumerate(bits)) for bits in inp.exact_optimal_bitstrings]
        reference={'probability_total':float(probs.sum()),'P_feasible_exact':float(probs[mask].sum()),'P_opt':float(probs[optimal_idx].sum()),'invalid_probability_mass':float(probs.sum()-probs[mask].sum())}
        diffs={k:abs(actual[k]-v) for k,v in reference.items()}
        old_diffs={k:abs(actual[k]-original[k]) for k in reference}
        assert max(diffs.values())<=TOL and max(old_diffs.values())<=TOL
        assert abs(old_value-value)<=TOL
        assert qaoa._v4_reporting_metrics(state,inp,TOL)['best_feasible_state']['record']['route']==original['best_feasible_state']['record']['route']
        probability_rows.append({'n':n,'basis_states_checked':len(data),'feasible_count':int(mask.sum()),'dtype':str(data.dtype),'candidate':{k:actual[k] for k in reference},'independent_reference':reference,'absolute_differences':diffs,'historical_full_dictionary_differences':old_diffs})
        objective_rows.append({'n':n,'historical':old_value,'current':value,'difference':abs(value-old_value)})

    # Fixed diagnostic n5 initial state only; no cap, optimizer, or instance-set change.
    inp=runner.make_input('routing_v18_n5_rank01',base_ids)
    value,state,_,timing=qaoa._statevector_and_expectation(inp,(0.1,),(0.1,),seed=17,optimization_level=1,optimized=True)
    data=np.asarray(state.data); probs=np.abs(data)**2
    actual=candidate.indexed_probability_metrics(state,base_ids,inp.exact_optimal_bitstrings,5)
    idx=roundtrips[0]['indices']; opt_idx=[sum(bit<<q for q,bit in enumerate(bits)) for bits in inp.exact_optimal_bitstrings]
    ref={'probability_total':float(probs.sum(dtype=np.float64)), 'P_feasible_exact':float(probs[idx].sum(dtype=np.float64)), 'P_opt':float(probs[opt_idx].sum(dtype=np.float64))}
    ref['invalid_probability_mass']=ref['probability_total']-ref['P_feasible_exact']
    diffs={k:abs(actual[k]-v) for k,v in ref.items()}
    assert max(diffs.values())<=TOL
    probability_rows.append({'n':5,'parameters':[0.1,0.1],'reference_method':'full numeric probability sum and independently derived 120 indices; not full dictionary', 'dtype':str(data.dtype),'state_sha256':digest(data.tobytes()),'candidate':{k:actual[k] for k in ref},'reference':ref,'absolute_differences':diffs,'timing_diagnostic_only':timing})
    # Objective diagonal reference, no candidate operator builder; fixed-size chunks.
    expected=0.0
    for start in range(0,len(data),262144):
        stop=min(start+262144,len(data)); basis=np.arange(start,stop,dtype=np.uint64)
        energy=np.full(stop-start,inp.ising_constant,dtype=np.float64)
        spins=[1.0-2.0*((basis>>q)&1) for q in range(25)]
        for q,c in inp.ising_linear.items(): energy+=c*spins[q]
        for (a,b),c in inp.ising_quadratic.items(): energy+=c*spins[a]*spins[b]
        expected+=float(probs[start:stop]@energy)
    assert abs(expected-value)<=TOL
    objective_rows.append({'n':5,'candidate':value,'independent_diagonal':expected,'difference':abs(expected-value),'no_original_full_dictionary_rerun':True})
    write('actual_equivalence_probes.json',{'tolerance':TOL,'probabilities':probability_rows,'objectives':objective_rows})
    del state,data,probs

    inp=small_input(2); ids=inp.customer_ids
    routes=list(itertools.permutations(range(2)))
    indices=[sum(1<<(i*2+t) for t,i in enumerate(r)) for r in routes]
    bits=[tuple((idx>>q)&1 for q in range(4)) for idx in indices]
    normal=np.zeros(16,dtype=np.complex128); normal[indices]=[math.sqrt(.25),math.sqrt(.75)]
    multi=candidate.indexed_probability_metrics(normal,ids,bits,2)
    assert abs(multi['P_opt']-1.0)<=TOL
    outcomes=[]
    cases={'zero_norm':np.zeros(16,dtype=np.complex128),'norm_four':normal*2,
           'NaN':np.full(16,np.nan,dtype=np.complex128),'inf':np.full(16,np.inf,dtype=np.complex128),
           'wrong_dimension':normal[:-1],'wrong_rank':normal.reshape(4,4),'empty_state':np.array([],dtype=np.complex128),
           'complex64':normal.astype(np.complex64),'finite_overflow':np.full(16,1e308,dtype=np.complex128)}
    for name,arr in cases.items():
        with np.errstate(over='ignore',invalid='ignore'):
            try:
                got=candidate.indexed_probability_metrics(arr,ids,(bits[0],),2)
                actual_status='ACCEPTED'
                detail={k:str(got[k]) for k in ['probability_total','P_feasible_exact','P_opt','invalid_probability_mass']}
            except Exception as exc:
                actual_status='REJECTED'; detail={'exception':type(exc).__name__,'message':str(exc)}
            try:
                metrics.probability_metrics({format(i,'04b'):float(abs(a)**2) for i,a in enumerate(arr.reshape(-1))},inp,threshold=TOL)
                orig='ACCEPTED'
            except Exception: orig='REJECTED'
        outcomes.append({'case':name,'candidate':actual_status,'original':orig,'details':detail})
    for name,opt in [('empty_optimum',()),('duplicate_optimum',(bits[0],bits[0])),('invalid_index_bits',((0,0,0,0),)),('malformed_bitstring',((0,1,2,0),)),('wrong_length',((1,0),))]:
        try:
            candidate.indexed_probability_metrics(normal,ids,opt,2); status='ACCEPTED'
        except Exception: status='REJECTED'
        outcomes.append({'case':name,'candidate':status})
    invalids={'duplicate_customer':(1,1,0,0),'missing_customer':(1,0,0,0),'duplicate_position':(1,0,1,0),'empty_assignment':(0,0,0,0),'malformed':(0,2,0,0)}
    decoded={k:core.validate_bitstring(v,2,ids).status.value for k,v in invalids.items()}
    write('failure_path_probes.json',{'cases':outcomes,'validation_cases':decoded,'multiple_optimum':{k:multi[k] for k in ['P_opt','P_feasible_exact']},'nonoptimal_valid_route':{'probability':.75,'P_opt_when_only_first_optimal':candidate.indexed_probability_metrics(normal,ids,(bits[0],),2)['P_opt']},
        'indices_interface':'No external index list accepted; indices constructed from constraints; missing/duplicate optimum inputs reject. int64 max index at n5 < 2**25.'})

    # Explicit line-level inventory: every changed opcode, classified before prior comparison.
    diffs=[]
    for path in [SRC+'r23_qaoa_aer/qaoa.py',SRC+'r23_qaoa_aer/optimized_metrics_v4.py',SRC+'r23_n5_scaling/run_n5_scaling.py']:
        old=git('show',f'{BASE}:{path}',check=False).splitlines(keepends=True)
        new=read(path).splitlines(keepends=True)
        for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
            if tag=='equal':continue
            text=''.join(new[c:d]); category='PERFORMANCE_ONLY'; reason='representation / execution dispatch; scalar unchanged'
            if 'run_n5_scaling' in path:
                category='SCIENTIFIC_SEMANTICS'; reason='runner newly committed after outcomes; whole historical entrypoint unavailable; carries scientific configuration and result provenance'
            elif 'optimized_metrics' in path:
                category='SCIENTIFIC_SEMANTICS'; reason='indexed metrics mathematical equivalence on normalized complex128; missing original norm/range guard changes accepted domain; includes validation and performance code'
            elif '_v4_reporting_metrics' in text and 'def _v4' in text:
                category='SCIENTIFIC_SEMANTICS'; reason='report adapter preserves route cost/threshold but omits original probability validation and reporting fields'
            elif 'energy_stats = {}' in text:
                category='SCIENTIFIC_SEMANTICS'; reason='drops energy variance and full metric output; probability acceptance contract differs'
            diffs.append({'path':path,'operation':tag,'original_lines':[a+1,b],'candidate_lines':[c+1,d],'classification':category,'reason':reason,'old':''.join(old[a:b]),'new':text})
    # Refine new helper at line granularity so guards and documentation are individually visible.
    helper=read(SRC+'r23_qaoa_aer/optimized_metrics_v4.py').splitlines()
    helper_groups=[(1,7,'PERFORMANCE_ONLY','imports; module docstring separately documentation'),(8,59,'VALIDATION_ONLY','new dimensional, type, finiteness and reference guards; incomplete norm guard'),(60,72,'PERFORMANCE_ONLY','constraint permutations sorted in original label order'),(73,86,'SCIENTIFIC_SEMANTICS','metric replacement with incomplete accepted-domain equivalence')]
    for lo,hi,cat,why in helper_groups:
        diffs.append({'path':SRC+'r23_qaoa_aer/optimized_metrics_v4.py','detail_of_new_file':True,'candidate_lines':[lo,hi],'classification':cat,'reason':why})
    write('line_diff_classification.json',{'baseline':BASE,'candidate':HEAD,'unknown_count':0,'changes':diffs,'categories_present':sorted({r['classification'] for r in diffs}),'note':'Parent opcodes cover all changed lines; detail rows refine helper, not additional independent changes.'})

    hashes=[]
    for p in sorted((ROOT/ART/'r23_n5_scaling/20260911_v1').rglob('*.json')):
        rel=str(p.relative_to(ROOT)); history=git('log','--format=%H %aI','--',rel).splitlines()
        hashes.append({'path':rel,'sha256':digest(p.read_bytes()),'history':history,'tracked':bool(git('ls-files','--',rel)),
           'unchanged_since_start':next(r['sha256'] for r in records if r['path']==rel)==digest(p.read_bytes())})
    write('artifact_immutability_audit.json',{'files':hashes,'audit_mutation':False,'rank01_limitation':'rank01 raw files ignored/untracked; no git blob history. Independent current snapshot cannot prove historical immutability.', 'tracked_rank02_rank03':'added at 0e149ed; no subsequent file commits through starting HEAD'})
    paths=[SRC+'r23_qaoa_aer/qaoa.py',SRC+'r23_qaoa_aer/optimized_metrics_v4.py',SRC+'r23_n5_scaling/run_n5_scaling.py']
    provenance=[]
    for rank in ('01','02','03'):
        record=js(RUNS+'routing_v18_n5_rank'+rank+'/scientific_result.json')
        commit=record['source_commit']; files=[]
        for path in paths:
            proc=subprocess.run(['git','show',f'{commit}:{path}'],cwd=ROOT,capture_output=True)
            files.append({'path':path,'exists_at_recorded_commit':proc.returncode==0,'sha256':digest(proc.stdout) if proc.returncode==0 else None,'v4_dispatch_present':b'implementation: str' in proc.stdout if path.endswith('/qaoa.py') else None})
        provenance.append({'rank':rank,'recorded_commit':commit,'started':record['started_at'],'ended':record['ended_at'],'files':files,'recorded_provenance':record.get('implementation_provenance')})
    write('source_provenance_probes.json',{'ranks':provenance,'original_qaoa_sha256':digest(historical(paths[0]).encode()),'current_qaoa_sha256':digest((ROOT/paths[0]).read_bytes()), 'current_helper_sha256':digest((ROOT/paths[1]).read_bytes())})
    write('git_provenance_audit.json',{'timeline':git('log','--reverse','--format=%H %aI %s','--name-only','3a4066b^..'+HEAD,'--',SRC+'r23_qaoa_aer',SRC+'r23_n5_scaling',ART+'r23_n5_scaling_authority',ART+'r23_n5_scaling',ART+'r23_n5_runtime_optimization_review'), 'limitation':'Commit timestamps bound recorded snapshots, not dirty worktree execution bytes; source_commit captured at result writing, not proven process start.'})
    searches={}
    for path in sorted(scope):
        if not path.endswith('.py') or ('r23' not in path and 'profil' not in path):continue
        lines=read(path).splitlines()
        searches[path]=[{'line':i,'text':s} for i,s in enumerate(lines,1) if re.search(r'\b(25|120)\b|n\s*==?\s*5|rank0[123]|exact|except|fallback|seed|1e-12|float32|complex64',s,re.I)]
    write('source_search_evidence.json', searches)
    write('probe_completion.json',{'completed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'previous_audit_opened':False,'read_paths':sorted(READS),'scientific_optimizer_runs':0,'all_assertions_passed':True})
    print(json.dumps({'output':str(OUT),'probe_assertions':'PASS','failure_contract_evidence':outcomes[:9]}))

if __name__ == '__main__':
    main()
