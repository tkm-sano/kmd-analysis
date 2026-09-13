"""Read-only B1/B2 evidence checks. No optimizer/circuit execution or historical writes.

A verified integrity gate is not research acceptance or optimizer convergence.
Reference arithmetic is independent of candidate metrics and result summaries.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
from .r23_validation_gate import aggregate_checks

TOL=1e-12
ART='reproducibility/outputs/traffic_simulation/'
FORMAL=ART+'r23_formal_instance_authority/20260911_v1'
B_AUTH=ART+'r23_experiment_b_authority/20260911_v1'
B2_AUTH=ART+'r23_experiment_b2_authority/20260911_v2'
PROFILES={
 'B1':(ART+'r23_experiment_b1/20260911_v2',B_AUTH+'/b1_planned_run_manifest.json'),
 'B2':(ART+'r23_experiment_b2/20260911_v2',B2_AUTH+'/b2_reexecution_planned_manifest.json'),
 'B2_FAILURE':(ART+'r23_experiment_b2/20260911_v1',ART+'r23_experiment_b2_authority/20260911_v1/b2_planned_run_manifest_v2.json'),
}

class EvidenceBlocked(ValueError):pass

def finite(v):return type(v) in (int,float) and math.isfinite(v)
def close(a,b):return finite(a) and finite(b) and abs(a-b)<=TOL
def require(value,message):
    if not value:raise AssertionError(message)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def load(root,path):
    try:return json.loads((Path(root)/path).read_text())
    except (OSError,ValueError) as exc:raise EvidenceBlocked(f'{path}: {exc}') from exc

def check(check_id,dimension,authority,fn,required='REQUIRED'):
    try:
        detail=fn()
        if detail is False or detail is None or detail=={} or detail==[]:
            raise AssertionError('condition false or no executed-check evidence')
        result='VERIFIED'
    except (EvidenceBlocked,KeyError) as exc:result='BLOCKED';detail=str(exc)
    except (AssertionError,TypeError,ValueError,IndexError,OverflowError) as exc:result='FAILED';detail=str(exc)
    return {'validation_id':check_id,'dimension':dimension,'requirement':check_id.split('/')[-1],
        'required':required,'source_authority':authority,'check_implementation':__name__,
        'result':result,'evidence':detail}

def hash_check(root,path,expected):
    if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):raise EvidenceBlocked('missing/malformed declared SHA for '+path)
    try:actual=sha(Path(root)/path)
    except OSError as exc:raise EvidenceBlocked(str(exc)) from exc
    require(actual==expected,'SHA mismatch: '+path)
    return {'path':path,'expected_sha256':expected,'actual_sha256':actual}

def manifest_checks(root,folder):
    manifest=load(root,folder+'/manifest.json')
    entries=manifest.get('files',manifest.get('artifacts'))
    if not isinstance(entries,dict) or not entries:raise EvidenceBlocked('manifest has no file hashes: '+folder)
    results=[]
    for name,expected in entries.items():
        # All entries, including failed progress/summary records; no selective filtering.
        results.append(check(folder+'/'+name+'/SHA','artifact_integrity',folder+'/manifest.json',lambda n=name,e=expected:hash_check(root,folder+'/'+n,e)))
    return results

def run_set_check(planned,actual_ids):
    expected=[p['run_id'] for p in planned]
    require(bool(expected) and len(expected)==len(set(expected)),'empty/duplicate planned set')
    require(len(actual_ids)==len(set(actual_ids)) and set(actual_ids)==set(expected),
        f'missing={sorted(set(expected)-set(actual_ids))}; extra={sorted(set(actual_ids)-set(expected))}; duplicates={len(actual_ids)-len(set(actual_ids))}')
    return {'expected_from_authority':len(expected),'actual':len(actual_ids),'missing':[],'extra':[]}

def route_cost(route,matrix,depot):
    nodes=[depot,*route,depot]
    values=[matrix[a][b] for a,b in zip(nodes,nodes[1:])]
    require(all(finite(x) and x>=0 for x in values),'non-finite/negative travel time')
    return sum(values)

def reference_check(reference,input_data):
    ids=input_data['customer_ids'];depot=input_data['depot_id'];n=input_data['n']
    require(len(ids)==n and len(set(ids))==n,'malformed customer authority')
    require(reference['customer_ids']==ids and reference['depot_id']==depot,'reference identity mismatch')
    matrix=input_data['normalized_travel_time_matrix']
    costs={tuple(r):route_cost(r,matrix,depot) for r in itertools.permutations(ids)}
    optimum=min(costs.values());optimal={r for r,c in costs.items() if abs(c-optimum)<=reference['reference_tolerance']}
    require(reference['reference_tolerance']==TOL,'reference tolerance differs')
    recorded={tuple(r[1:-1]) for r in reference['normalized']['optimal_routes']}
    require(optimal==recorded and close(optimum,reference['normalized']['best_route_travel_time']),'independent exact reference mismatch')
    require(reference['normalized']['evaluated_permutations']==math.factorial(n),'incomplete exact reference')
    return {'optimum':optimum,'optimal_routes':[list(r) for r in sorted(optimal)],'enumerated':len(costs)}

def validate_run(record,planned,reference,input_data,initialization,root=None,profile=None):
    """Pure per-record checks support in-memory mutations without touching raw evidence."""
    rid=record.get('run_id','MISSING_RUN_ID');checks=[]
    def add(name,dim,fn,required='REQUIRED'):
        checks.append(check(rid+'/'+name,dim,'planned manifest / frozen R20 input / exact reference / initialization authority',fn,required))
    def result():return record['result']
    def refs():
        if reference is None or input_data is None:raise EvidenceBlocked('exact reference or R20 input missing')
        return reference_check(reference,input_data)
    def conditions():
        r=result();require(rid==planned['run_id'],'run id differs')
        for k in ('instance_id','n','p','optimizer','initialization_id'):require(r[k]==planned[k],'condition mismatch: '+k)
        require(r['initial_parameters']==initialization['parameters'],'initialization vector mismatch')
        require(r['initialization_seed']==initialization['seed'],'initialization seed mismatch')
        require(r['initialization_vector_sha256']==initialization['vector_sha256'],'initialization vector hash mismatch')
        require(r['lambda']==input_data['lambda'],'lambda mismatch')
        for k in ('maxiter','objective_evaluation_cap'):
            if k in planned:require(r['maxiter' if k=='maxiter' else 'max_evaluations']==planned[k],'budget differs from authority: '+k)
        if 'optimizer_options' in planned:require(record['optimizer_configuration']['options']==planned['optimizer_options'],'optimizer options differ from authority')
        return {k:r[k] for k in ('instance_id','n','p','optimizer','initialization_id')}
    def termination():
        r=result();t=r['termination'];success=r['optimizer_success']
        require(type(success) is bool,'optimizer success missing/nonboolean')
        for k in ('termination_status','termination_source','termination_message'):
            require(isinstance(r[k],str) and bool(r[k]),'empty '+k)
        require(t['success'] is success and t['status']==r['optimizer_status'],'native status disagreement')
        require(t['termination_status']==r['termination_status'],'termination reason disagreement')
        require(type(r['nfev']) is int and r['nfev']>=0,'invalid evaluation count')
        require(r['termination_status'] not in ('IMPLEMENTATION_EXCEPTION','PROVENANCE_FAILURE','TERMINATION_UNKNOWN'),'not a valid scientific terminal result')
        return {'success':success,'nfev':r['nfev'],'termination':r['termination_status'],'message':r['termination_message']}
    def route():
        best=result()['probability_metrics']['best_feasible_state'];r=best['record']['route'];ids=input_data['customer_ids'];n=len(ids)
        require(len(r)==n and set(r)==set(ids) and len(set(r))==n,'route is not a customer permutation')
        expected=[int(ids[i]==r[t]) for i in range(n) for t in range(n)]
        require(best['record']['bitstring']==expected,'route/bitstring mismatch')
        require(best['record']['qiskit_label']==''.join(map(str,expected[::-1])),'bit-order mismatch')
        require(best['record']['valid'] is True and best['record']['status']=='VALID','feasibility label contradicts permutation')
        return {'route':r,'recomputed_cost':route_cost(r,input_data['normalized_travel_time_matrix'],input_data['depot_id'])}
    def objective():
        rr=route();ref=refs();best=result()['probability_metrics']['best_feasible_state'];cost=rr['recomputed_cost']
        require(close(cost,best['normalized_route_objective']),'reported route objective differs from directed edge sum')
        gap=cost-ref['optimum'];relative=gap/ref['optimum'] if ref['optimum'] else None
        if 'scientific_result' in record:
            sr=record['scientific_result'];require(close(sr['absolute_optimality_gap'],gap),'wrong absolute gap')
            require(relative is not None and close(sr['relative_optimality_gap'],relative),'wrong relative gap')
            require(sr['selected_best_decoded_route']==rr['route'],'summary route mismatch')
        return {'cost':cost,'exact_cost':ref['optimum'],'absolute_gap':gap,'relative_gap':relative,'gap_stored_in_B1':False if 'scientific_result' not in record else True}
    def probabilities():
        r=result();pm=r['probability_metrics'];probs=r['probabilities'];n=input_data['n'];ids=input_data['customer_ids']
        require(isinstance(probs,dict) and len(probs)==2**(n*n),'probability dictionary must contain full basis')
        require(all(isinstance(label,str) and len(label)==n*n and set(label)<={'0','1'} for label in probs),'malformed basis label')
        require(all(finite(v) and -TOL<=v<=1+TOL for v in probs.values()),'invalid probability entry')
        total=math.fsum(probs.values());require(close(total,1.),'probability total violates raw unit norm')
        def label(route):return ''.join(str(int(ids[i]==route[t])) for i in reversed(range(n)) for t in reversed(range(n)))
        feasible=math.fsum(probs[label(r)] for r in itertools.permutations(ids))
        opt=math.fsum(probs[label(r)] for r in refs()['optimal_routes'])
        recomputed={'probability_total':total,'P_feasible_exact':feasible,'P_opt':opt,'invalid_probability_mass':total-feasible}
        for k,v in recomputed.items():require(close(pm[k],v),'probability mismatch '+k)
        tc=pm['probability_tolerance_contract'];require(tc['denominator']=='raw_full_state_probability_mass' and tc['renormalization'] is False,'probability denominator changed')
        require(all(tc[k]==TOL for k in ('isclose_tolerance','range_tolerance','sum_tolerance')),'probability tolerance changed')
        return recomputed
    def recovery():
        rr=route();rf=refs();require(rr['route'] in rf['optimal_routes'],'exact optimum not recovered')
        return {'route_in_independent_optimal_set':True}
    def provenance():
        a=record['authority'];require(isinstance(a,dict) and bool(a),'missing authority metadata')
        keys=['implementation_authority_sha256','instance_authority_manifest_sha256','lambda_policy_sha256']
        keys+=['b1_authorization_sha256','initialization_authority_sha256'] if planned['optimizer']=='COBYLA' else ['authorization_sha256','planned_manifest_sha256','exact_reference_sha256']
        require(all(isinstance(a[k],str) and re.fullmatch('[0-9a-f]{64}',a[k]) for k in keys),'malformed authority SHA')
        if root is None:raise EvidenceBlocked('repository needed for authority SHA comparisons')
        mapping={'instance_authority_manifest_sha256':FORMAL+'/manifest.json','lambda_policy_sha256':'reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json'}
        if planned['optimizer']=='COBYLA':mapping.update({'implementation_authority_sha256':ART+'r23_experiment_b1_implementation_fix/20260911_v1/implementation_authority_v2.json','b1_authorization_sha256':ART+'r23_experiment_b1_implementation_fix/20260911_v1/b1_reexecution_authorization.json','initialization_authority_sha256':B_AUTH+'/initialization_authority.json'})
        elif profile=='B2_FAILURE':mapping.update({'implementation_authority_sha256':ART+'r23_experiment_b1_implementation_fix/20260911_v1/implementation_authority_v2.json','authorization_sha256':ART+'r23_experiment_b2_authority/20260911_v1/b2_execution_authorization_v2.json','planned_manifest_sha256':PROFILES['B2_FAILURE'][1],'exact_reference_sha256':FORMAL+'/_refs/'+planned['instance_id']+'.json'})
        else:mapping.update({'implementation_authority_sha256':B2_AUTH+'/implementation_authority_v3.json','authorization_sha256':B2_AUTH+'/b2_reexecution_authorization.json','planned_manifest_sha256':B2_AUTH+'/b2_reexecution_planned_manifest.json','exact_reference_sha256':FORMAL+'/_refs/'+planned['instance_id']+'.json'})
        return [hash_check(root,path,a[k]) for k,path in mapping.items()]
    add('conditions','execution_completeness',conditions)
    add('termination_metadata','scientific_validity',termination)
    add('independent_reference','scientific_validity',refs)
    add('decoded_feasibility','feasibility',route)
    add('route_objective_gap','scientific_validity',objective)
    add('raw_probability_integrity','probability_integrity',probabilities)
    add('recorded_authority_hashes','provenance_completeness',provenance)
    add('exact_optimum_recovery','exact_optimum_recovery',recovery,'OPTIONAL')
    def convergence():
        termination();require(result()['optimizer_success'] is True,'optimizer reported success=false; scientific validity evaluated separately')
        return {'scope':'native optimizer success only; not global convergence'}
    add('optimizer_convergence','optimizer_convergence',convergence,'OPTIONAL')
    return {'run_id':rid,'checks':checks,'status':aggregate_checks(checks)}

def _validate_experiment(root,profile):
    folder,plan_path=PROFILES[profile];checks=[];runs=[]
    try:
        plan=load(root,plan_path);planned=plan['runs']
        require(bool(planned) and len(planned)==plan['run_count'],'empty/inconsistent planned run count')
        require(len({p['run_id'] for p in planned})==len(planned),'duplicate planned ids')
    except EvidenceBlocked as exc:return {'experiment':profile,'status':'BLOCKED','checks':[check(profile+'/plan','execution_completeness',plan_path,lambda:(_ for _ in ()).throw(exc))],'runs':[]}
    except (KeyError,AssertionError) as exc:return {'experiment':profile,'status':'FAILED','checks':[{'validation_id':profile+'/plan','dimension':'execution_completeness','required':'REQUIRED','result':'FAILED','evidence':str(exc)}],'runs':[]}
    files=sorted((Path(root)/folder/'runs').glob('*.json'));expected={p['run_id'] for p in planned};actual={p.stem for p in files}
    def count_check():
        return run_set_check(planned,[p.stem for p in files])
    checks.append(check(profile+'/run_count','execution_completeness',plan_path,count_check))
    try:checks.extend(manifest_checks(root,folder))
    except EvidenceBlocked as exc:checks.append({'validation_id':profile+'/manifest','dimension':'artifact_integrity','required':'REQUIRED','result':'BLOCKED','evidence':str(exc)})
    try:index=load(root,folder+'/terminal_records.json')['records']
    except (EvidenceBlocked,KeyError) as exc:
        checks.append({'validation_id':profile+'/terminal_index_missing','dimension':'artifact_integrity','required':'REQUIRED','result':'BLOCKED','evidence':str(exc)})
        index=[] # Container only; the explicit BLOCKED check is retained in the gate.
    indexmap={x['run_id']:x for x in index}
    checks.append(check(profile+'/terminal_index_coverage','artifact_integrity',folder+'/terminal_records.json',lambda: bool(index) and len(index)==len(indexmap) and set(indexmap)==expected))
    inits=load(root,B_AUTH+'/initialization_authority.json')['records']
    initmap={(x['initialization_id'],x['p']):x for x in inits}
    for iid in sorted({r['instance_id'] for r in planned}):
        input_folder=FORMAL+'/r20/'+iid
        try:
            checks.extend(manifest_checks(root,input_folder))
            im=load(root,input_folder+'/manifest.json')
            checks.append(check(iid+'/exact_reference_SHA','artifact_integrity',input_folder+'/manifest.json',lambda k=iid,m=im:hash_check(root,FORMAL+'/_refs/'+k+'.json',m['exact_reference_hash'])))
        except (EvidenceBlocked,KeyError) as exc:checks.append({'validation_id':iid+'/input_authority','dimension':'artifact_integrity','required':'REQUIRED','result':'BLOCKED','evidence':str(exc)})
    for planned_row in planned:
        rid=planned_row['run_id'];path=folder+'/runs/'+rid+'.json'
        checks.append(check(rid+'/record_SHA','artifact_integrity',folder+'/terminal_records.json',lambda p=path,k=rid:hash_check(root,p,indexmap[k]['sha256'])))
        try:
            record=load(root,path);iid=planned_row['instance_id'];reference=load(root,FORMAL+'/_refs/'+iid+'.json');inp=load(root,FORMAL+'/r20/'+iid+'/r20_input.json')
            effective_plan={**{k:plan[k] for k in ('maxiter','objective_evaluation_cap') if k in plan},**planned_row}
            one=validate_run(record,effective_plan,reference,inp,initmap[(planned_row['initialization_id'],planned_row['p'])],root,profile)
        except (EvidenceBlocked,KeyError) as exc:
            one={'run_id':rid,'status':'BLOCKED','checks':[{'validation_id':rid+'/required_input','dimension':'scientific_validity','required':'REQUIRED','result':'BLOCKED','evidence':str(exc)}]}
        runs.append(one);checks.extend(one['checks'])
    if profile=='B2':
        baseline=ART+'r23_experiment_b2_authority/20260911_v1/b2_cobyla_baseline_manifest.json'
        try:
            bm=load(root,baseline)
            checks.append(check(profile+'/baseline_manifest_SHA','artifact_integrity',baseline,lambda:hash_check(root,bm['source_manifest'],bm['source_manifest_sha256'])))
            for row in bm['runs']:checks.append(check(profile+'/'+row['run_id']+'/baseline_SHA','artifact_integrity',baseline,lambda r=row:hash_check(root,r['source_path'],r['source_sha256'])))
        except (EvidenceBlocked,KeyError) as exc:checks.append({'validation_id':'B2/baseline','dimension':'artifact_integrity','required':'REQUIRED','result':'BLOCKED','evidence':str(exc)})
    dimensions={d:aggregate_checks([{**c,'required':'REQUIRED'} for c in checks if c['dimension']==d]) for d in sorted({c['dimension'] for c in checks})}
    return {'experiment':profile,'plan':plan_path,'expected_runs':len(planned),'actual_runs':len(files),'checks':checks,'runs':runs,
        'dimensions':dimensions,'status':aggregate_checks(checks),'result_counts':dict(Counter(c['result'] for c in checks)),
        'scope':'Integrity of retained evidence, not new experiment authorization. Missing/contradictory historical evidence stays visible; no repair or exclusion.',
        'optional_checks':['optimizer_convergence','exact_optimum_recovery'],'not_applicable':['nit numeric for COBYLA (native API may return None)','stored B1 gap (derived independently instead)']}

def validate_experiment(root,profile):
    try:return validate_formal_authority(root) if profile=='FORMAL_AUTHORITY' else _validate_experiment(root,profile)
    except (EvidenceBlocked,KeyError) as exc:
        return {'experiment':profile,'status':'BLOCKED','checks':[{'validation_id':profile+'/required_inputs','dimension':'provenance_completeness','required':'REQUIRED','result':'BLOCKED','evidence':str(exc)}],'runs':[]}
    except (TypeError,ValueError,AssertionError) as exc:
        return {'experiment':profile,'status':'FAILED','checks':[{'validation_id':profile+'/malformed_inputs','dimension':'scientific_validity','required':'REQUIRED','result':'FAILED','evidence':str(exc)}],'runs':[]}

def validate_formal_authority(root):
    """Materialized Formal A input/design checks, not a new 45-run QAOA validation."""
    plan=load(root,FORMAL+'/planned_run_manifest.json');rows=plan['runs']
    checks=manifest_checks(root,FORMAL)
    design_path='reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json'
    def design_check():
        d=load(root,design_path);matrix=d['planned_matrix'];ids={r['instance_id'] for r in rows}
        require(len(rows)==matrix['planned_formal_run_count'] and len(ids)==matrix['planned_instance_count'],'formal design count mismatch')
        require({(r['instance_id'],r['p']) for r in rows}==set(itertools.product(ids,d['qaoa']['p_values'])),'formal design condition matrix mismatch')
        require({r['n'] for r in rows}==set(matrix['n_values']),'formal n set mismatch')
        for k in ('optimizer','maxiter','objective_cap'):
            dk={'optimizer':'name','maxiter':'maxiter','objective_cap':'objective_evaluation_cap'}[k]
            require(plan[k]==d['optimizer'][dk],'formal optimizer control mismatch')
        return {'authority':design_path,'expected_runs':matrix['planned_formal_run_count'],'actual_runs':len(rows),'instance_count':len(ids)}
    checks.append(check('FORMAL/design_matrix','execution_completeness',design_path,design_check))
    checks.append(check('FORMAL/planned_count','execution_completeness',FORMAL+'/planned_run_manifest.json',lambda:run_set_check(rows,[r['run_id'] for r in rows]) if len(rows)==plan['run_count'] else False))
    for iid in sorted({r['instance_id'] for r in rows}):
        for stage in ('r20','r21','r22'):checks.extend(manifest_checks(root,FORMAL+'/'+stage+'/'+iid))
        ref=load(root,FORMAL+'/_refs/'+iid+'.json');inp=load(root,FORMAL+'/r20/'+iid+'/r20_input.json')
        checks.append(check(iid+'/independent_exact','scientific_validity',FORMAL+'/r20/'+iid+'/r20_input.json',lambda r=ref,i=inp:reference_check(r,i)))
        checks.append(check(iid+'/reference_SHA','artifact_integrity',FORMAL+'/r20/'+iid+'/r20_input.json',lambda k=iid,i=inp:hash_check(root,FORMAL+'/_refs/'+k+'.json',i['exact_reference_hash'])))
    return {'experiment':'FORMAL_AUTHORITY','status':aggregate_checks(checks),'checks':checks,'planned_count':len(rows),
        'scientific_execution':'NOT_TESTED','execution_authorized':False,'scope':'Retained formal input authority and exact references only; no Formal A optimizer-result revalidation or environment preflight claim'}

def cli(profile):
    import sys
    root=Path(__file__).resolve().parents[3]
    try:result=validate_experiment(root,profile)
    except (EvidenceBlocked,KeyError) as exc:result={'experiment':profile,'status':'BLOCKED','evidence':str(exc)}
    result['legacy_generator_policy']='Read-only validation replacement; no historical writes, new authorization or unexecuted test claims.'
    result['legacy_targeted_pytest_and_dispatch_smokes']={'status':'NOT_TESTED','reason':'This entrypoint validates retained evidence; it does not execute historical pytest/smoke commands.'}
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if result['status']=='VERIFIED' else 1
