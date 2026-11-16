"""Independent post-run assertions, epsilon references and resource/coverage ledger."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from time import perf_counter
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile
from kmd_toc.vehicle_day.validation import independent_plan_oracle
from kmd_toc.search_improvement.catalogue import build_catalogue
from kmd_toc.search_improvement.master import CatalogueMaster
from kmd_toc.search_improvement.study import pool_from_saved
from kmd_toc.search_improvement.regions import legacy_regions,expanded_regions


def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);args=parser.parse_args()
    root=Path(args.root); cfg=json.loads(Path('configs/toc_delivery_d_pricing_improvement_v1.json').read_text())
    checks=[];ledger=[]
    def check(name,value):
        checks.append({'name':name,'pass':bool(value)})
        if not value:raise AssertionError(name)
    reproduction=json.loads((root/'BASELINE_REPRODUCTION.json').read_text())
    check('all_saved_scientific_fields_reproduced',reproduction['old_scientific_fields_equal'])
    check('760_negative_days_breakdown_709_51',list(reproduction['counts'].values())==[760,709,51])
    rows=list(csv.DictReader((root/'coverage_attempt03/COVERAGE.csv').open()))
    target=[r for r in rows if r['snapshot']=='regression_final_D']
    check('final_snapshot_global_negative_212',all(int(r['global_negative_count'])==212 for r in target))
    check('old_scope_zero_and_expanded_all',all(float(r['candidate_coverage'])==(0 if r['region_version']=='old' else 1) for r in target))
    check('expanded_sample_all212_three_seeds',sum(r['sampler']=='aoa' and r['region_version']=='expanded' and int(r['obtained_negative_count'])==212 for r in target)==3)
    for case in (root/'integrated_attempt02').glob('*aoa_*.json'):
        if 'INTEGER_EXTENSIONS' in case.name:continue
        result=json.loads(case.read_text())
        if 'trace' not in result:continue
        for step in result['trace']:
            domains=[tuple(d) for d in step['domains']]
            allpairs={(i,j) for i in range(1,len(step['lp']['dual']['customer'])+1) for j in range(i+1,len(step['lp']['dual']['customer'])+1)}
            covered={tuple(sorted((a,b))) for d in domains for a in d for b in d if a!=b}
            logs=step['quantum']; keys=[q['ledger_key'] for q in logs]
            ledger.append({'case':case.name,'iteration':step['iteration'],'unique_regions':len(set(keys)),
                 'duplicated_region_calls':len(keys)-len(set(keys)),'covered_pairs':len(covered),
                 'uncovered_pairs':len(allpairs-covered),'unvisited_triples_may_remain':True,
                 'termination_scope':'FINITE_Q2_SINGLETON_TRIP_SCOPE_NOT_GLOBAL_AOA_CERTIFICATE'})
            check(case.stem+'_unique_ledger_'+str(step['iteration']),len(keys)==len(set(keys)))
            check(case.stem+'_pair_cover_'+str(step['iteration']),not (allpairs-covered))
    save(root/'REGION_COVERAGE_LEDGER.json',ledger)
    m=CatalogueMaster(small_problem(6,1),build_catalogue(small_problem(6,1)))
    full=list(range(len(m.columns)));profiles=[ObjectiveProfile('D',e) for e in cfg['epsilon_D_subject_to_W']]+[ObjectiveProfile('W',e) for e in cfg['epsilon_W_subject_to_D']]
    refs=[]
    for profile in profiles:
        begin=perf_counter(); ip=m.ip(full,profile); oracle=independent_plan_oracle(m.problem,m.columns,profile)
        check(f'epsilon_{profile.primary}_{profile.other_limit}_feasibility',ip['success']==oracle['feasible'])
        if oracle['feasible']:check(f'epsilon_{profile.primary}_{profile.other_limit}_objective',abs(ip['objective']-oracle['objective'])<1e-7)
        refs.append({'profile':vars(profile),'full_IP':ip,'independent_objective':oracle.get('objective'),
                     'independent_feasible':oracle['feasible'],'audit_seconds':perf_counter()-begin})
    save(root/'EPSILON_INDEPENDENT_REFERENCES.json',refs)
    # Exact set identity comparison with the original completion implementation.
    from kmd_toc.vehicle_day.generation import enumerate_days
    from kmd_toc.column_generation.models import Route
    baseline=json.loads((root/'baseline_replay/AOA_N6_B1_D.json').read_text());pool=pool_from_saved(m,baseline)
    generated={(1,2),(2,5),(3,)};known=m.known(pool)
    old=enumerate_days(m.problem,route_pool={Route(r) for r in known|generated},required_routes={Route(r) for r in generated})
    new=m.complete(generated,known)
    check('new_completion_exact_identity_with_old',set(c.column_id for c in old)=={m.ids[i] for i in new})
    for stage in ['COVERAGE_ATTEMPT03','INTEGRATED_ATTEMPT02','SCALING']:
        w=json.loads((root/(stage+'_WATCHDOG.json')).read_text())
        check(stage+'_completed_without_safety_abort',w['returncode']==0 and not w['safety_limit_triggered'])
    for row in csv.DictReader((root/'scaling/SCALING.csv').open()):
        check(row['case']+row['mode']+'_valid',row['valid']=='True')
        check(row['case']+row['mode']+'_face_full_ip',abs(float(row['face_IP'])-float(row['full_IP']))<1e-7)
    save(root/'RESULTS_AUDIT.json',{'checks':checks,'all_pass':all(x['pass'] for x in checks),
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'S1_executions':0})
    print(len(checks),'independent result checks passed')
