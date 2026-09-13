"""Direct frozen-environment I03 harness; mutations are in memory or isolated temp copies."""
from __future__ import annotations
import ast
import copy
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import runpy
from r23_i03_remediation import ROOT,OUT,BASE,ORIGINAL,ADDITIONAL,write,sha,git
sys.path.insert(0,str(ROOT/'05_src'))
from traffic_simulation.validation.r23_evidence_gate import (
    validate_experiment,validate_run,run_set_check,check,load,PROFILES,FORMAL,B_AUTH,hash_check)
from traffic_simulation.validation.r23_validation_gate import aggregate_checks,evaluate_gate
from traffic_simulation.validation.r23_lineage_gate import lineage_authority_checks
from traffic_simulation.r23_qaoa_aer.artifact import build_provenance_lineage,validate_provenance_lineage

def main():
    expected={'qiskit':'2.5.2','qiskit-aer':'0.17.2','qiskit-algorithms':'0.4.0','qiskit-optimization':'0.7.0','numpy':'2.4.6','scipy':'1.17.1'}
    observed={k:importlib.metadata.version(k) for k in expected}
    assert observed==expected and sys.version_info[:3]==(3,11,16)
    assert str(Path(sys.executable).parent.parent)=='/home/takuma/.conda/envs/evrp-quantum-temp'
    environment={'python':sys.executable,'version':sys.version,'dependencies':observed,'environment_modified':False,'pytest_installed_by_task':False}
    reports={};positive=[];negative=[]
    for profile in ('B1','B2','B2_FAILURE'):
        r=validate_experiment(ROOT,profile);reports[profile]=r
        assert r['actual_runs']==r['expected_runs']>0
        print(profile,r['status'],r['dimensions'],flush=True)
        if profile!='B2_FAILURE':
            assert all(run['status']=='VERIFIED' for run in r['runs'])
            assert all(r['dimensions'][d]=='VERIFIED' for d in ('execution_completeness','scientific_validity','feasibility','exact_optimum_recovery','probability_integrity','provenance_completeness'))
            if profile=='B1':assert r['status']=='VERIFIED'
            positive.append({'experiment':profile,'result':'VERIFIED','basis':'executed independent run/reference/probability checks; not prior classification',
                'scientific_run_count':len(r['runs']),'retained_optimizer_failures':sum(c['dimension']=='optimizer_convergence' and c['result']=='FAILED' for c in r['checks']),
                'actual_overall_evidence_gate':r['status'],'artifact_integrity':r['dimensions']['artifact_integrity'],
                'artifact_failures':[c for c in r['checks'] if c['dimension']=='artifact_integrity' and c['result']!='VERIFIED']})
        else:assert r['status']!='VERIFIED'
    for profile in ('B1','B2'):
        folder,plan_path=PROFILES[profile];plan=load(ROOT,plan_path);pr=plan['runs'][0];iid=pr['instance_id']
        rec=load(ROOT,folder+'/runs/'+pr['run_id']+'.json');ref=load(ROOT,FORMAL+'/_refs/'+iid+'.json');inp=load(ROOT,FORMAL+'/r20/'+iid+'/r20_input.json')
        init=next(x for x in load(ROOT,B_AUTH+'/initialization_authority.json')['records'] if (x['p'],x['initialization_id'])==(pr['p'],pr['initialization_id']))
        for name in ('missing_run','extra_run','duplicate_run'):
            ids=[x['run_id'] for x in plan['runs']]
            if name=='missing_run':ids=ids[:-1]
            elif name=='extra_run':ids=ids+['UNAUTHORIZED_EXTRA_RUN']
            else:ids=ids+[ids[0]]
            c=check(profile+'/'+name,'execution_completeness',plan_path,lambda:run_set_check(plan['runs'],ids))
            assert c['result']=='FAILED';negative.append({'experiment':profile,'fixture':name,'result':c['result'],'detected':True,'evidence':c})
        mutations=('wrong_route','wrong_objective','missing_exact_reference','bad_probability','missing_metadata','wrong_initialization','empty_probabilities','NaN_probability','missing_SHA','wrong_exact_objective')
        for name in mutations:
            mutated=copy.deepcopy(rec);mr=copy.deepcopy(ref)
            if name=='wrong_route':mutated['result']['probability_metrics']['best_feasible_state']['record']['route'][0]='NOT_A_CUSTOMER'
            elif name=='wrong_objective':mutated['result']['probability_metrics']['best_feasible_state']['normalized_route_objective']+=0.125
            elif name=='missing_exact_reference':mr=None
            elif name=='bad_probability':mutated['result']['probability_metrics']['probability_total']=0.5
            elif name=='missing_metadata':del mutated['result']['optimizer_success']
            elif name=='wrong_initialization':mutated['result']['initial_parameters'][0]+=0.25
            elif name=='empty_probabilities':mutated['result']['probabilities']={}
            elif name=='NaN_probability':mutated['result']['probabilities'][next(iter(mutated['result']['probabilities']))]=float('nan')
            elif name=='missing_SHA':del mutated['authority']['implementation_authority_sha256']
            else:mr['normalized']['best_route_travel_time']+=0.25
            r=validate_run(mutated,pr,mr,inp,init,ROOT,profile)
            assert r['status'] in ('FAILED','BLOCKED'),(profile,name,r)
            negative.append({'experiment':profile,'fixture':name,'result':r['status'],'detected':True,
                'failures':[c for c in r['checks'] if c['required']=='REQUIRED' and c['result']!='VERIFIED']})
        # A metadata-complete optimizer failure must stay in scientific validation.
        assert any(c['dimension']=='optimizer_convergence' and c['result']=='FAILED' for c in reports[profile]['checks'])
    config=load(ROOT,'reproducibility/config/traffic_simulation/r23_pilot_configuration/20260910_r23_reduced_pilot_v1.json')
    lineage=build_provenance_lineage(ROOT,config);validate_provenance_lineage(lineage)
    other={'lineage':{s:lineage[s]['validation'] for s in ('R21','R22')},'B2_failure_namespace':reports['B2_FAILURE'],
        'legacy_regression_claims':{'status':'NOT_TESTED','required':'NOT_APPLICABLE','reason':'No historical pytest/smoke execution is claimed by read-only replacements'}}
    formal=validate_experiment(ROOT,'FORMAL_AUTHORITY');assert formal['status']=='VERIFIED',formal
    other['formal_input_authority']=formal
    for stage in ('R21','R22'):
        for mutation in ('missing_hash','wrong_hash','missing_manifest'):
            auth=copy.deepcopy(config['authority']);key=stage.lower()
            if mutation=='missing_hash':del auth[key+'_results_sha256']
            elif mutation=='wrong_hash':auth[key+'_results_sha256']='0'*64
            else:auth[key+'_manifest']='NONEXISTENT_I03_FIXTURE.json'
            r=lineage_authority_checks(ROOT,auth,stage);assert r['status'] in ('FAILED','BLOCKED')
            negative.append({'experiment':stage,'fixture':mutation,'result':r['status'],'detected':True,'failures':r['checks']})
    bad=copy.deepcopy(lineage);bad['R21']['validation']['checks']=[]
    try:validate_provenance_lineage(bad)
    except ValueError:negative.append({'experiment':'lineage','fixture':'forged_verified_empty_checks','result':'FAILED','detected':True})
    else:raise AssertionError('empty lineage checks accepted')
    with tempfile.TemporaryDirectory(prefix='r23_i03_missing_') as tmp:
        for profile in ('B1','B2'):
            r=validate_experiment(tmp,profile);assert r['status']=='BLOCKED'
            negative.append({'experiment':profile,'fixture':'missing_artifact_root','result':r['status'],'detected':True,'failures':r['checks']})
    gate_cases=[([], 'NOT_TESTED'),([('REQUIRED','VERIFIED')],'VERIFIED'),([('REQUIRED','FAILED'),('REQUIRED','BLOCKED')],'FAILED'),([('REQUIRED','BLOCKED')],'BLOCKED'),([('REQUIRED','NOT_TESTED')],'NOT_TESTED'),([('REQUIRED','VERIFIED'),('REQUIRED','NOT_TESTED')],'PARTIAL'),([('REQUIRED','VERIFIED'),('OPTIONAL','FAILED')],'VERIFIED'),([('NOT_APPLICABLE','NOT_TESTED')],'PARTIAL')]
    for rows,expected_status in gate_cases:
        actual=aggregate_checks([{'required':r,'result':s} for r,s in rows]);assert actual==expected_status
    assert not evaluate_gate([],[])['passed']
    assert not evaluate_gate([{'test_id':'x','executed':False,'result':'VERIFIED','checks':[{'passed':True}],'evidence':'fixture'}],['x'])['passed']
    assert evaluate_gate([{'test_id':'x','executed':True,'result':'VERIFIED','checks':[{'passed':True}],'evidence':'executed fixture'}],['x'])['passed']
    assert evaluate_gate([{'test_id':'x','executed':True,'result':'VERIFIED','checks':[{'passed':False}],'evidence':'negative fixture'}],['x'])['result']=='FAILED'
    assert check('empty','scientific_validity','fixture',lambda:None)['result']=='FAILED'
    # Verify the scientific call/config ASTs remain byte-for-byte AST-equivalent.
    ast_checks=[]
    for path in ('tools/execute_r23_experiment_b2.py','tools/execute_r23_experiment_b2_reexecution.py'):
        before=ast.parse(git('show',BASE+':'+path));after=ast.parse((ROOT/path).read_text())
        def scientific_nodes(tree):
            return sorted(ast.dump(n,include_attributes=False) for n in ast.walk(tree) if
                isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('R23Config','run_single','load_r22_instance'))
        assert scientific_nodes(before)==scientific_nodes(after)
        for var in ('OPTIONS',):
            a=[ast.dump(n.value) for n in before.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==var for t in n.targets)]
            b=[ast.dump(n.value) for n in after.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==var for t in n.targets)]
            assert a==b
        ast_checks.append({'path':path,'scientific_call_and_options_AST_unchanged':True})
        # Execute only the preflight predicate assignment, never main()/QAOA.
        ns=runpy.run_path(str(ROOT/path),run_name='i03_read_only_import')
        ns.update(auth=ns['load'](ns['AUTHZ']),plan=ns['load'](ns['PLAN']),runtime={'scipy':observed['scipy']})
        ns['am']=ns['amendment']=ns['load'](ns['AMEND'])
        name='base_checks' if path.endswith('execute_r23_experiment_b2.py') else 'checks'
        main_node=next(n for n in after.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        assignment=next(n for n in main_node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
        unit=compile(ast.fix_missing_locations(ast.Module(body=[assignment],type_ignores=[])),path,'exec')
        exec(unit,ns);assert ns[name] and all(ns[name].values())
        ns['EXPECTED']=dict(ns['EXPECTED'],plan='0'*64);exec(unit,ns);assert not all(ns[name].values())
        negative.append({'experiment':'B2 preflight','fixture':path+' incorrect plan hash','result':'FAILED','detected':True,'evidence':ns[name]})
    entrypoints=[]
    for path in ORIGINAL+ADDITIONAL:
        if path.endswith('/artifact.py') or '/execute_' in path or path.endswith('/freeze_r23_instance_authority.py'):continue
        proc=subprocess.run([sys.executable,str(ROOT/path)],cwd=ROOT,capture_output=True,text=True)
        parsed=json.loads(proc.stdout);assert (proc.returncode==0)==(parsed['status']=='VERIFIED')
        entrypoints.append({'path':path,'exit_code':proc.returncode,'status':parsed['status'],'historical_writes':False})
    path='05_src/traffic_simulation/r20_route_ordering/freeze_r23_instance_authority.py'
    before=ast.parse(git('show',BASE+':'+path));after=ast.parse((ROOT/path).read_text())
    guards=[n for n in ast.walk(after) if isinstance(n,ast.If) and any(isinstance(x,ast.Constant) and x.value=='R23_R21_AUTHORITY_VALIDATION_FAILED' for x in ast.walk(n))]
    assert len(guards)==1
    unit=compile(ast.fix_missing_locations(ast.Module(body=guards,type_ignores=[])),path,'exec')
    exec(unit,{'r21_result':{'status':'R21_FORMAL_INSTANCE_PASS','checks':{'executed_check':True}}})
    for fixture in ({'status':'FAILED','checks':{'executed_check':True}},{'status':'R21_FORMAL_INSTANCE_PASS','checks':{}},{'status':'R21_FORMAL_INSTANCE_PASS','checks':{'executed_check':False}}):
        try:exec(unit,{'r21_result':fixture})
        except ValueError:negative.append({'experiment':'Formal authority','fixture':fixture,'result':'FAILED','detected':True})
        else:raise AssertionError('R21 failed validation promoted to PASS')
    class RemoveGuard(ast.NodeTransformer):
        def visit_If(self,node):return None if node is guards[0] else self.generic_visit(node)
    assert ast.dump(RemoveGuard().visit(after))==ast.dump(before)
    ast_checks.append({'path':path,'all_AST_except_new_validation_guard_unchanged':True})
    write('b1_validation_review.json',reports['B1']);write('b2_validation_review.json',reports['B2']);write('other_scope_validation_review.json',other)
    write('positive_regression.json',{'status':'VERIFIED','environment':environment,'experiments':positive,'gate_cases_tested':len(gate_cases),'n5_gate_compatibility':'VERIFIED','entrypoints':entrypoints,'scientific_AST_checks':ast_checks,
        'important':'Positive scientific integrity does not override FAILED B2 historical record SHA consistency. No old result or index is rewritten.'})
    write('negative_regression.json',{'status':'VERIFIED' if negative and all(x['detected'] for x in negative) else 'FAILED','cases':negative,'mutations_touch_originals':False})
    manifest=[]
    for profile,r in reports.items():
        for c in r['checks']:manifest.append({'experiment':profile,**c})
    for stage in ('R21','R22'):
        for c in lineage[stage]['validation']['checks']:manifest.append({'experiment':stage,**c})
    for c in formal['checks']:manifest.append({'experiment':'FORMAL_AUTHORITY',**c})
    for c in manifest:
        c.setdefault('requirement',c['validation_id'].split('/')[-1]);c.setdefault('source_authority',PROFILES.get(c['experiment'],('','declared lineage configuration'))[1]);c.setdefault('check_implementation','traffic_simulation.validation.r23_evidence_gate')
    assert manifest and all(all(k in c for k in ('validation_id','experiment','requirement','required','source_authority','check_implementation','result','evidence')) for c in manifest)
    write('validation_manifest.json',{'coverage_status':'VERIFIED','checks':manifest,'count':len(manifest),'note':'Manifest completeness, not a blanket scientific pass; FAILED/BLOCKED/optional observations included.'})
    print(json.dumps({'positive_regression':'VERIFIED','negative_cases':len(negative),'manifest_checks':len(manifest),'entrypoints':len(entrypoints)}),flush=True)

if __name__=='__main__':main()
