"""Immutable comparison contract; metadata differences never alter science settings."""
from traffic_simulation.r24_vrptw_qaoa_worker.contract import *
from traffic_simulation.r24_vrptw_qaoa_worker import contract as standard
SPEC=BASE/'r24_vrptw_uniform_vs_structured_comparison_spec/20260922_v1'
OFFLINE=BASE/'r24_vrptw_structured_initial_state/20260922_v2'
DESIGN=BASE/'r24_vrptw_structured_initial_state/20260922_v1'
OUT=BASE/'r24_vrptw_structured_initial_state/20260922_v3_implementation_preflight'
COMPARISON_HASH='372b7475e0048a5d7d9ea96523a81cfd95c2627d0a5769dc8f3325b4068fb7b9'

def frozen():
    require(sha(SPEC/'FINAL_FREEZE_MANIFEST.json')==COMPARISON_HASH,'comparison manifest')
    for p,h in read(SPEC/'FINAL_FREEZE_MANIFEST.json')['artifacts'].items():require(sha(SPEC/p)==h,p)
    c=read(SPEC/'SCIENTIFIC_COMPARISON_SPEC.json');s=standard.load()
    require(all(c['inherited_settings'][k]==s[k] for k in c['inherited_settings']),'inherited settings')
    require(c['resource_policy']==s['resource_gate'],'resource policy')
    require(c['repetitions_per_cell']==s['repetitions_per_condition']==3,'repetitions')
    require(sha(ROOT/c['S']['constructor'])==c['S']['constructor_sha256'],'constructor')
    require(sha(ROOT/c['S']['candidate_artifact'])==c['S']['candidate_sha256'],'Candidate A')
    return c,s

def run_plan(rid):
    c,s=frozen();matches=[r for r in rows(SPEC/'RUN_PLAN.csv') if r['run_id']==rid];require(len(matches)==1,rid)
    r=matches[0];u=standard.plan(s,r['U_reference_run_id']);require(r['condition']==u['condition'],'condition')
    require(int(r['repetition'])==u['repetition'] and r['seed_mapping_sha256']==u['seed_mapping_sha256'],'paired seeds')
    require([float(r[k]) for k in ['initial_alpha','initial_beta','scale']]==[float(u[k]) for k in ['initial_alpha','initial_beta','scale']],'parameters')
    require(int(r['training_cap'])==s['optimizer']['training_evaluation_cap']==99 and int(r['final_cap'])==1,'caps')
    require(int(r['training_shots'])==s['shots']['training_per_evaluation'] and int(r['final_shots'])==s['shots']['independent_final'],'shots')
    require(int(r['max_circuits'])==100,'run circuits')
    r=dict(r,repetition=u['repetition'],seeds=copy.deepcopy(u['seeds']),initial_parameters=u['initial_parameters'],planned_output_path=r['future_output'],p=s['p'])
    expected=BASE/'r24_vrptw_uniform_vs_structured_comparison/20260922_v1'/('scientific_batch_'+r['batch'][1:])/'runs'/rid
    require(ROOT/r['planned_output_path']==expected,'output namespace')
    return r,u,s,c

def run_identity(rid):
    r,u,s,c=run_plan(rid);i=standard.identity(s,u)
    require(i['qubo_hash']==r['QUBO_hash'],'QUBO hash')
    i.update(run_id=rid,batch_id=r['batch'],arm='STRUCTURED_A',group=r['group'],execution_spec_sha256=COMPARISON_HASH,configuration_hash=c['configuration_hash'],initial_state_hash=r['preparation_state_hash'],U_reference_run_id=u['run_id'])
    return i
