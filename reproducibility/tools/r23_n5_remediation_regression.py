"""Executed assertion harness for remediation; no optimizer runs or historical output writes."""
from __future__ import annotations
import ast
import copy
import dataclasses
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_audit_remediation/20260913_v1'
BASE='33ae964bca0e61199621ee976a927cd4069e1723'
sys.path.insert(0,str(ROOT/'05_src'))
import numpy as np
from traffic_simulation.r20_route_ordering import core
from traffic_simulation.r22_ising_conversion import converter
from traffic_simulation.r23_qaoa_aer import qaoa, optimized_metrics_v4 as candidate, metrics
from traffic_simulation.r23_qaoa_aer.schema import R23Input
from traffic_simulation.r23_qaoa_aer import execution_provenance as provenance
from traffic_simulation.r23_n5_scaling import run_n5_scaling as runner
from traffic_simulation.validation.r23_validation_gate import evaluate_gate, numerical_comparison

REQUIRED=['environment','model_source_unchanged','n2','n3','n4','n5_rank01','n5_rank02','n5_rank03',
          'mapping_rank01','mapping_rank02','mapping_rank03','invalid_inputs','multiple_optimum','gate_mutations','provenance_missing_fields','retired_generators']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def historical(path):return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT,text=True)
def old_module(path,name):
    mod=types.ModuleType(name);mod.__package__='traffic_simulation.r23_qaoa_aer';sys.modules[name]=mod
    exec(compile(historical(path),name,'exec'),mod.__dict__);return mod
OLD=old_module('05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py','before_remediation_helper')
OLD_Q=old_module('05_src/traffic_simulation/r23_qaoa_aer/qaoa.py','before_remediation_qaoa')
OLD_Q.indexed_probability_metrics=OLD.indexed_probability_metrics

def make_input(n):
    ids=tuple(runner.INSTANCES['routing_v18_n5_rank01'][:n]);raw=runner.load_matrix(ids)
    norm,_=core.normalize_travel_time_matrix(runner.DEPOT,ids,raw)
    q=core.build_expanded_qubo(runner.DEPOT,ids,norm,4.);ising=converter.convert_qubo_to_ising(q)
    routes=core.enumerate_routes(runner.DEPOT,ids,raw)['optimal_routes']
    bits=frozenset(core.encode_route(r[1:-1],ids) for r in routes)
    return R23Input('regression_n'+str(n),n,ids,runner.DEPOT,ising.constant,ising.linear,ising.quadratic,'audit','audit',4.,3.,bits,
        frozenset(tuple(1-2*b for b in row) for row in bits),frozenset(tuple(r) for r in routes),norm,{'ising_global_minimum_energy':0.})

def independent_indices(n):
    return sorted(sum(1<<(city*n+pos) for pos,city in enumerate(route)) for route in itertools.permutations(range(n)))

def check_domain(inp):
    value,state,_,_=qaoa._statevector_and_expectation(inp,(.1,),(.1,),seed=17,optimization_level=1,optimized=True)
    before=OLD_Q._v4_reporting_metrics(state,inp,1e-12);after=qaoa._v4_reporting_metrics(state,inp,1e-12)
    data=np.asarray(state.data);prob=np.abs(data)**2;idx=independent_indices(inp.n)
    if inp.n<=4:
        bits=((np.arange(len(data),dtype=np.uint64)[:,None]>>np.arange(inp.n**2,dtype=np.uint64))&1).reshape(-1,inp.n,inp.n)
        mask=np.all(bits.sum(axis=1)==1,axis=1)&np.all(bits.sum(axis=2)==1,axis=1)
        assert list(np.flatnonzero(mask))==idx
    # Original metric enumerator is independent of candidate aggregation on small n.
    dictionary=None
    if inp.n<=4:
        dictionary=metrics.probability_metrics({format(i,f'0{inp.n**2}b'):float(p) for i,p in enumerate(prob)},inp)
    opt=[sum(b<<q for q,b in enumerate(row)) for row in inp.exact_optimal_bitstrings]
    total=float(prob.sum(dtype=np.float64));pf=float(prob[idx].sum(dtype=np.float64));po=float(prob[opt].sum(dtype=np.float64))
    ref={'probability_total':total,'P_feasible_exact':pf,'P_opt':po,'invalid_probability_mass':total-pf}
    differences={k:abs(after[k]-ref[k]) for k in ref};before_differences={k:abs(after[k]-before[k]) for k in ref}
    assert all(numerical_comparison(after[k],ref[k]) and numerical_comparison(after[k],before[k]) for k in ref)
    if dictionary:assert all(numerical_comparison(after[k],dictionary[k]) for k in ref)
    assert before['best_feasible_state']==after['best_feasible_state']
    # Independent cost-order route reference, not maximum-probability route.
    candidates=[]
    for k in idx:
        if prob[k]<1e-12:continue
        route=tuple(inp.customer_ids[next(i for i in range(inp.n) if (k>>(i*inp.n+t))&1)] for t in range(inp.n))
        nodes=(inp.depot_id,*route,inp.depot_id);cost=sum(inp.normalized_matrix[a][b] for a,b in zip(nodes,nodes[1:]))
        candidates.append((cost,k,route))
    best=min(candidates)
    assert tuple(after['best_feasible_state']['record']['route'])==best[2]
    expected=0.
    for start in range(0,len(data),262144):
        stop=min(start+262144,len(data));basis=np.arange(start,stop,dtype=np.uint64)
        energy=np.full(stop-start,inp.ising_constant,dtype=np.float64)
        spins=[1.-2.*((basis>>q)&1) for q in range(inp.n**2)]
        for q,c in inp.ising_linear.items():energy+=c*spins[q]
        for (a,b),c in inp.ising_quadratic.items():energy+=c*spins[a]*spins[b]
        expected+=float(prob[start:stop]@energy)
    assert numerical_comparison(value,expected)
    if inp.n<=4:
        old_value,_,_,_=OLD_Q._statevector_and_expectation(inp,(.1,),(.1,),seed=17,optimization_level=1,optimized=True)
        assert numerical_comparison(value,old_value)
    else:old_value=value # evaluator AST equality separately asserted; no duplicate 25q simulation needed
    # Basis-state valid-domain probe, including n5; simple exact expected mass fixed before run.
    basis_state=np.zeros_like(data);basis_state[opt[0]]=1
    basis_result=candidate.indexed_probability_metrics(basis_state,inp.customer_ids,inp.exact_optimal_bitstrings,inp.n)
    assert basis_result['probability_total']==basis_result['P_feasible_exact']==basis_result['P_opt']==1.
    return {'instance':inp.instance_id,'n':inp.n,'parameters':[.1,.1],'dtype':str(data.dtype),'candidate':{k:after[k] for k in ref},
        'independent_reference':ref,'absolute_differences':differences,'before_after_differences':before_differences,
        'expectation':value,'independent_expectation':expected,'expectation_difference':abs(value-expected),
        'decoded_route':list(best[2]),'before_after_route_equal':before['best_feasible_state']==after['best_feasible_state'],
        'basis_state_mass':basis_result['P_opt'],'coverage':'full numeric probabilities; full one-hot mask n<=4, independent factorial indices n5; fixed point, not optimizer trajectory'}

def mapping(rank):
    ids=runner.INSTANCES['routing_v18_n5_'+rank];indices=[]
    for route in itertools.permutations(range(5)):
        k=sum(1<<(i*5+t) for t,i in enumerate(route));bits=tuple((k>>q)&1 for q in range(25))
        result=core.validate_bitstring(bits,5,ids)
        assert result.route==tuple(ids[i] for i in route)
        assert metrics.qiskit_label_to_bits(format(k,'025b'))==bits
        indices.append(k)
    assert len(indices)==len(set(indices))==120 and set(indices)==set(candidate.feasible_basis_indices(ids,5))
    return {'rank':rank,'feasible_routes':len(indices),'unique_indices':len(set(indices)),'roundtrip_passed':len(indices)}

def invalid_inputs():
    s=np.zeros(16,dtype=np.complex128);s[9]=1.;ids=('A','B');opt=((1,0,0,1),)
    cases={'zero_norm':(s*0,ids,opt,2),'norm_four':(s*2,ids,opt,2),'norm_0_999':(s*np.sqrt(.999),ids,opt,2),
       'NaN':(np.full_like(s,np.nan),ids,opt,2),'inf':(np.full_like(s,np.inf),ids,opt,2),'finite_overflow':(np.full_like(s,1e308),ids,opt,2),
       'wrong_dimension':(s[:-1],ids,opt,2),'wrong_rank':(s.reshape(4,4),ids,opt,2),'malformed_complex':(['1+badj']*16,ids,opt,2),
       'complex64':(s.astype(np.complex64),ids,opt,2),'float32':(s.real.astype(np.float32),ids,opt,2),'empty_input':(s[:0],ids,opt,2),
       'invalid_optimal_index':(s,ids,((0,0,0,0),),2),'duplicate_optimal_index':(s,ids,opt+opt,2),'missing_optimal_index':(s,ids,(),2),
       'malformed_optimal_bits':(s,ids,((0,2,0,0),),2),'duplicate_customer':(s,('A','A'),opt,2)}
    rows=[]
    for name,args in cases.items():
        try:candidate.indexed_probability_metrics(*args)
        except candidate.V4InputError as exc:rows.append({'case':name,'rejected':True,'exception':type(exc).__name__,'message':str(exc)})
        else:raise AssertionError(name+' did not fail closed')
    # Inject an invalid computed norm: catches negative and non-finite computation without repairing values.
    saved=candidate.np.vdot
    try:
        for val in (-1.,float('nan'),float('inf')):
            candidate.np.vdot=lambda *args,v=val:complex(v)
            try:candidate.indexed_probability_metrics(s,ids,opt,2)
            except candidate.V4InputError:rows.append({'case':'computed_norm_'+str(val),'rejected':True})
            else:raise AssertionError('invalid computed norm accepted')
    finally:candidate.np.vdot=saved
    return {'cases':rows,'index_policy':'External index arrays are not accepted; invalid/duplicate/missing optimal bit encodings exercise corresponding contract.'}

def multiple():
    ids=('A','B');a=(1,0,0,1);b=(0,1,1,0);s=np.zeros(16,dtype=np.complex128);s[9]=.5;s[6]=np.sqrt(.75)
    result=candidate.indexed_probability_metrics(s,ids,(a,b),2)
    assert numerical_comparison(result['P_opt'],1.)
    other=candidate.indexed_probability_metrics(s,ids,(a,),2);assert numerical_comparison(other['P_opt'],.25)
    return {'optimum_indices':[9,6],'expected_mass':1.,'observed_mass':result['P_opt'],'one_optimum_mass':other['P_opt']}

def gate_mutations():
    row={'test_id':'x','executed':True,'result':'VERIFIED','checks':[{'passed':True}],'evidence':'executed fixture assertion'}
    assert evaluate_gate([row],['x'])['passed']
    mutants=[[],[row,row],[dict(row,executed=False)],[dict(row,evidence='')],[dict(row,checks=[])],[dict(row,checks=[{'passed':False}])],[dict(row,result='NOT_TESTED')]]
    assert all(not evaluate_gate(m,['x'])['passed'] for m in mutants)
    assert not numerical_comparison(.25,.25001) and not numerical_comparison(float('nan'),.25)
    return {'mutations_rejected':len(mutants)+2,'positive_gate_verified':True}

def metadata_test():
    m={k:'recorded' for k in provenance.REQUIRED}
    m.update(git_commit='a'*40,source_sha256='b'*64,runner_sha256='c'*64,helper_sha256='d'*64,authority_manifest_sha256='e'*64,
        objective_trace_sha256='f'*64,environment_path='/home/takuma/.conda/envs/evrp-quantum-temp',dependency_versions=provenance.VERSIONS,
        source_manifest={'runner.py':'c'*64},dirty_worktree=False,thread_settings={k:'EXPLICIT_UNSET' for k in provenance.THREAD_KEYS},
        start_timestamp='2026-09-14T00:00:00Z',end_timestamp='2026-09-14T00:01:00Z',optimizer_options={'maxiter':300,'objective_cap':300},
        seeds={'simulator':17,'transpiler':17,'initialization':'NOT_APPLICABLE','optimizer':'NOT_APPLICABLE'},final_parameters=[.1,.1],
        resource_metrics={'metric':'absolute_process_peak_RSS','units':'bytes','process_id':1,'absolute_peak_rss':1024,'timer_boundaries':'fixture only'})
    m['thread_settings']['affinity']=[0];provenance.validate_formal_run_metadata(m)
    rejected=[]
    for k in provenance.REQUIRED:
        bad=copy.deepcopy(m);del bad[k]
        try:provenance.validate_formal_run_metadata(bad)
        except provenance.FormalRunProvenanceIncomplete:rejected.append(k)
        else:raise AssertionError('missing '+k+' admitted')
    for bad in ({},dict(m,dirty_worktree=True),dict(m,runner_sha256='bad'),dict(m,source_manifest={})):
        try:provenance.validate_formal_run_metadata(bad)
        except provenance.FormalRunProvenanceIncomplete:pass
        else:raise AssertionError('invalid metadata admitted')
    return {'missing_fields_rejected':rejected,'policy':'FORMAL_RUN_PROVENANCE_INCOMPLETE','fixture_is_not_execution_evidence':True}

def source_check():
    paths=['r20_route_ordering/core.py','r22_ising_conversion/converter.py','r23_qaoa_aer/hamiltonian.py','r23_qaoa_aer/schema.py','r23_qaoa_aer/optimizers.py','r23_qaoa_aer/initialization.py','r23_n5_scaling/run_n5_scaling.py']
    for p in paths:
        path='05_src/traffic_simulation/'+p;assert (ROOT/path).read_text()==historical(path)
    def function(source,name):return ast.dump(next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
    for name in ['_statevector_and_expectation','run_single']:
        assert function(historical('05_src/traffic_simulation/r23_qaoa_aer/qaoa.py'),name)==function((ROOT/'05_src/traffic_simulation/r23_qaoa_aer/qaoa.py').read_text(),name)
    return {'unchanged_source_paths':paths,'objective_and_runner_AST_equal':True}

def environment():
    observed={'python':platform.python_version(),**{k:importlib.metadata.version(k.replace('_','-')) for k in provenance.VERSIONS if k!='python'}}
    assert observed==provenance.VERSIONS
    return {'python':sys.executable,'observed':observed,'expected':provenance.VERSIONS,'environment_modified':False}

def retired():
    rows=json.loads((OUT/'legacy_generator_retirement.json').read_text())['generators']
    for row in rows:
        proc=subprocess.run([sys.executable,str(ROOT/row['path'])],capture_output=True,text=True)
        assert proc.returncode!=0 and 'LEGACY_VALIDATION_GENERATOR_RETIRED' in proc.stderr
    return {'entrypoints_rejected':len(rows)}

def main():
    OUT.mkdir(parents=True,exist_ok=True);manifest=[];evidence={}
    def execute(test_id,requirement,fn):
        try:
            detail=fn();passed=True;error=None
        except Exception as exc:detail={};passed=False;error=repr(exc)
        evidence[test_id]=detail
        manifest.append({'test_id':test_id,'requirement':requirement,'implementation':str(Path(__file__).relative_to(ROOT)),
            'executed':True,'result':'VERIFIED' if passed else 'PARTIAL','checks':[{'passed':passed,'error':error}],
            'evidence':'regression_evidence.json#'+test_id})
        print(test_id+': '+manifest[-1]['result'],flush=True)
    execute('environment','frozen dependency versions',environment)
    execute('model_source_unchanged','scientific definitions/objective unchanged',source_check)
    for n in (2,3,4):execute('n'+str(n),'valid-domain metrics/expectation/route',lambda n=n:check_domain(make_input(n)))
    for rank in ('rank01','rank02','rank03'):
        execute('n5_'+rank,'valid n5 fixed point',lambda rank=rank:check_domain(runner.make_input('routing_v18_n5_'+rank,runner.INSTANCES['routing_v18_n5_'+rank])))
        execute('mapping_'+rank,'120 route/index roundtrips',lambda rank=rank:mapping(rank))
    for key,fn in [('invalid_inputs',invalid_inputs),('multiple_optimum',multiple),('gate_mutations',gate_mutations),('provenance_missing_fields',metadata_test),('retired_generators',retired)]:execute(key,key,fn)
    gate=evaluate_gate(manifest,REQUIRED)
    write('regression_evidence.json',evidence);write('validation_test_manifest.json',{'required_ids':REQUIRED,'tests':manifest,'gate':gate})
    write('valid_domain_regression.json',{'gate':evaluate_gate([r for r in manifest if r['test_id'].startswith('n')],['n2','n3','n4','n5_rank01','n5_rank02','n5_rank03']),
        'points':{k:v for k,v in evidence.items() if k.startswith('n')},'tolerance':1e-12,'optimizer_trajectory':'NOT_TESTED; final parameters not retained'})
    for file,key in [('invalid_input_regression.json','invalid_inputs'),('multiple_optimum_regression.json','multiple_optimum')]:write(file,{'test':next(r for r in manifest if r['test_id']==key),'evidence':evidence[key]})
    write('bit_ordering_regression.json',{'ranks':{k:v for k,v in evidence.items() if k.startswith('mapping_')},'tests':[r for r in manifest if r['test_id'].startswith('mapping_')]})
    if not gate['passed']:raise SystemExit('REGRESSION_FAILED: inspect validation_test_manifest.json')

if __name__=='__main__':main()
