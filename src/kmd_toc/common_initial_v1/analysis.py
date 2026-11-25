"""Six comparisons and pi0-based hypothesis, using frozen descriptive arithmetic."""
from copy import deepcopy
from kmd_toc.descriptive_v1 import statistics as s
from kmd_toc.descriptive_v1.analysis import analyze as old_analysis,_pairs
from kmd_toc.measurement_audit_v1.analysis import AuditedReader,load_audited
from .plans import sha,exact_metrics

NAMES={'A':'行政統計に基づく外部ベースライン','B':'従来型配送計画',
       'C':'古典最適化','D':'量子・古典ハイブリッド最適化'}
PAIRS=(('A','B'),('A','C'),('A','D'),('B','C'),('B','D'),('C','D'))


def relation(base,target):
    if target['D']<base['D'] and target['W']<base['W']:return 'STRICTLY_BETTER_BOTH'
    if target['D']==base['D'] and target['W']==base['W']:return 'EQUAL'
    if target['D']<=base['D'] and target['W']<=base['W']:return 'NONWORSE_WITH_ONE_STRICT'
    if target['D']>=base['D'] and target['W']>=base['W']:return 'WORSE_OR_EQUAL_BOTH_WITH_ONE_STRICT'
    return 'TRADEOFF'


def hypothesis(initial,classical,hybrid):
    a=s.dual(initial['D'],initial['W'],classical['D'],classical['W'])
    b=s.dual(initial['D'],initial['W'],hybrid['D'],hybrid['W'])
    return {'I_classical_initial_percent':a,'I_hybrid_initial_percent':b,
        'delta_I_hybrid_minus_classical_percentage_points':b-a if a is not None and b is not None else None,
        'H1_hybrid_index_higher':b>a if a is not None and b is not None else None,
        'hybrid_strict_both_vs_initial':hybrid['D']<initial['D'] and hybrid['W']<initial['W'],
        'hybrid_nonworse_vs_initial':hybrid['D']<=initial['D'] and hybrid['W']<=initial['W'],
        'hybrid_dual_improvement_achieved':b>0 if b is not None else None,
        'hybrid_strict_both_vs_classical':hybrid['D']<classical['D'] and hybrid['W']<classical['W'],
        'final_plan_relation':relation(classical,hybrid),
        'zero_baseline_policy':'undefined relative indices; absolute differences only',
        'classical_delta_D':classical['D']-initial['D'],'classical_delta_W':classical['W']-initial['W'],
        'hybrid_delta_D':hybrid['D']-initial['D'],'hybrid_delta_W':hybrid['W']-initial['W'],
        'classical_r_D_percent':s.relative(initial['D'],classical['D']) if initial['D']>0 and initial['W']>0 else None,
        'classical_r_W_percent':s.relative(initial['W'],classical['W']) if initial['D']>0 and initial['W']>0 else None,
        'hybrid_r_D_percent':s.relative(initial['D'],hybrid['D']) if initial['D']>0 and initial['W']>0 else None,
        'hybrid_r_W_percent':s.relative(initial['W'],hybrid['W']) if initial['D']>0 and initial['W']>0 else None}


class CommonReader(AuditedReader):
    def __init__(self,path):
        super().__init__(path);self.initial_bindings={}

    def metrics(self,raw,case):
        d,w=super().metrics(raw,case)
        initial=self.json(raw['common_initial_manifest']);proof=self.json(raw['outer_evidence'])
        if initial['version']!='common-initial-20261122-v1' or initial['status']!='COMPLETE':
            raise ValueError('COMMON_INITIAL_NOT_COMPLETE_OR_WRONG_VERSION')
        p,_=self.case(raw['scale'],case)
        if initial['problem_hash']!=p.fingerprint or initial['od_hash']!=p.od.fingerprint:
            raise ValueError('COMMON_INITIAL_SCOPE_MISMATCH')
        if proof.get('common_initial_plan_sha256')!=initial['plan_sha256']:
            raise ValueError('OUTER_RESULT_NOT_BOUND_TO_INITIAL')
        self.json(raw['common_initial_plan'])
        if raw['common_initial_plan']['sha256']!=initial['plan_sha256']:
            raise ValueError('INITIAL_PLAN_HASH_NOT_SAME')
        from kmd_toc.duty_break_v1.models import load_plan
        from kmd_toc.measurement_audit_v1.measurement import physical_payload,digest_payload
        initial_plan=load_plan((self.base/raw['common_initial_plan']['path']).resolve())
        if initial_plan.method_id!='B' or initial.get('generator_role')!='existing_B_algorithm':
            raise ValueError('RESEARCH_INITIAL_MUST_BE_TRADITIONAL_NOT_EXPLICIT_FIXTURE')
        if (exact_metrics(p,initial_plan)!=initial['metrics'] or
                digest_payload(physical_payload(initial_plan))!=initial['physical_plan_hash']):
            raise ValueError('INITIAL_METRICS_OR_PHYSICAL_HASH_NOT_VERIFIED')
        if raw['method']=='B':
            if raw['plan']['sha256']!=initial['plan_sha256']:raise ValueError('B_NOT_THE_COMMON_INITIAL')
        else:
            receipt=self.json(raw['start_receipt'])
            if (receipt['method']!=raw['method'] or receipt['status']!='STARTED_FROM_SHARED_INITIAL' or
                    receipt['initial_plan_sha256']!=initial['plan_sha256'] or
                    receipt['physical_plan_hash']!=initial['physical_plan_hash'] or
                    receipt['metrics']!=initial['metrics'] or receipt.get('classical_final_result_input') is not False or
                    receipt.get('administrative_reference_input') is not False or
                    receipt.get('initial_manifest_sha256')!=raw['common_initial_manifest']['sha256'] or
                    receipt.get('problem_hash')!=p.fingerprint or receipt.get('od_hash')!=p.od.fingerprint or
                    receipt.get('trial_id')!=initial['trial_id']):
                raise ValueError('METHOD_START_IDENTITY_OR_ISOLATION_UNCONFIRMED')
            start_path=(self.base/raw['start_receipt']['path']).parent/'start_plan.json'
            self.json({'path':str(start_path),'sha256':receipt['start_plan_sha256']})
            started=load_plan(start_path)
            if (started.method_id!=raw['method'] or exact_metrics(p,started)!=initial['metrics'] or
                    digest_payload(physical_payload(started))!=initial['physical_plan_hash']):
                raise ValueError('ACTUAL_SAVED_START_PLAN_NOT_IDENTICAL')
        self.initial_bindings[raw['trial_id']]=initial['plan_sha256']
        return d,w


def analyze(reg,rows,evidence):
    reg=deepcopy(reg);rows=deepcopy(rows)
    for by_metric in reg.get('A_references',{}).values():
        for ref in by_metric.values():
            if ref.get('kind') in ('A_rule_v1','rule_proxy') or ref.get('implementation_id')=='A_rule_v1':
                ref['comparability_audit']={}
                ref['hold_reason']='LEGACY_PROXY_IS_NOT_ADMINISTRATIVE_REFERENCE'
    for r in rows:
        if r.get('unit_type')!='outer_trial' or r.get('retry_of') or 'branch_id' in r:
            r['outer_attempt']=False
        if (r.get('status')!='SUCCESS' or r.get('measurement_status')!='PASS' or r.get('unit_type')!='outer_trial' or
                not r.get('outer_attempt') or r.get('retry_of') or 'branch_id' in r):
            previous=r.get('exclusion_reason')
            reason='NOT_VALID_MEASUREMENT_PASSED_SUCCESS_OUTER_TRIAL'
            r.update(eligible=False,D=None,W=None,exclusion_reason=previous+'; '+reason if previous else reason)
    for scale in ('S1','S2','S3'):
        valid=[r for r in rows if r['scale']==scale and r['eligible']]
        if len({r.get('comparison_profile') for r in valid})>1:raise ValueError('MIXED_PHYSICAL_PROFILES')
        for method in ('B','C','D'):
            if len({r.get('configuration_id') for r in valid if r['method']==method})>1:
                raise ValueError('MIXED_NKR_OR_OTHER_SETTINGS')
    legacy=deepcopy(reg);legacy['comparison_designs']=[d for d in reg.get('comparison_designs',[]) if (d['baseline'],d['comparison'])!=('B','C')]
    legacy['dual_designs']=[]
    result=old_analysis(legacy,rows,evidence);byid={r['trial_id']:r for r in rows}
    result.pop('dual_trials');result.pop('aggregate_mean_indices')
    for scale in ('S1','S2','S3'):
        design=next((d for d in reg.get('comparison_designs',[]) if (d['scale'],d['baseline'],d['comparison'])==(scale,'B','C')),None)
        pairs=_pairs(design,byid,evidence) if design and design['kind']!='independent_groups' else None
        for metric in ('D','W'):
            base=[r[metric] for r in rows if r['scale']==scale and r['method']=='B' and r['eligible']]
            target=[r[metric] for r in rows if r['scale']==scale and r['method']=='C' and r['eligible']]
            z=s.independent_contrast(base,target)
            row={'scale':scale,'baseline':'B','comparison':'C','metric':metric,'delta_values':None,**z,
                 'status':'DEFINED_GROUP_MEAN_CONTRAST' if z['mean_delta'] is not None else 'HOLD_NO_VALID_TRIALS'}
            if pairs is not None:
                a,b,ind=pairs;z=s.paired([r[metric] for r in a],[r[metric] for r in b],independent_pairs=ind)
                row.update(mean_delta=z['delta']['mean'],SD_delta=z['delta']['SD'],MCSE_delta=z['delta']['MCSE'],
                           MCSE_status=z['delta']['MCSE_status'],delta_values=z['delta_values'],
                           status='DEFINED' if a else 'HOLD_NO_VALID_PAIRS')
            result['comparisons'].append(row)
    for r in result['comparisons']:
        r.update(baseline_display=NAMES[r['baseline']],comparison_display=NAMES[r['comparison']],
                 baseline_role='administrative_external_reference' if r['baseline']=='A' else 'simulation_plan',
                 unit='km' if r['metric']=='D' else 'min_total_loading_wait')
        if r['baseline']!='A':
            base=next(x['mean'] for x in result['summaries'] if (x['scale'],x['method'],x['metric'])==(r['scale'],r['baseline'],r['metric']))
            value=next(x['mean'] for x in result['summaries'] if (x['scale'],x['method'],x['metric'])==(r['scale'],r['comparison'],r['metric']))
            r['relative_rate_of_means_percent']=s.relative(base,value) if base is not None and value is not None else None
        else:r['relative_rate_of_means_percent']=r.get('relative_rate_of_means')
    result['comparisons'].sort(key=lambda r:(r['scale'],PAIRS.index((r['baseline'],r['comparison'])),r['metric']))
    group=[]
    for scale in ('S1','S2','S3'):
        means={method:{m:next(r['mean'] for r in result['summaries'] if (r['scale'],r['method'],r['metric'])==(scale,method,m)) for m in ('D','W')} for method in ('B','C','D')}
        if all(v is not None for x in means.values() for v in x.values()):
            h=hypothesis(means['B'],means['C'],means['D'])
            group.append({'scale':scale,'estimand':'index_from_method_mean_DW_not_mean_trial_index',**h,
                          'MCSE_of_nonlinear_mean_index_difference':None,
                          'cohort_alignment':'HOLD_UNLESS_REGISTERED_SUCCESS_COHORTS_MATCH',
                          'hypothesis_evaluation':'DESCRIPTIVE_ONLY_NO_SIGNIFICANCE'})
        else:group.append({'scale':scale,'status':'HOLD_NO_VALID_METHOD_MEANS'})
    trials=[];seen_global=set()
    for design in reg.get('initial_triplets',[]):
        proof=evidence(design['evidence'])
        if proof.get('kind')!='registered_common_initial_triplets' or proof.get('registered_before_results') is not True or proof.get('triplets')!=design['triplets']:
            raise ValueError('TRIAL_CORRESPONDENCE_NOT_REGISTERED')
        seen={m:set() for m in ('B','C','D')}
        for ids in design['triplets']:
            a,b,c=[byid[i] for i in ids]
            if ([r['method'] for r in (a,b,c)]!=['B','C','D'] or
                    any(r['scale']!=design['scale'] for r in (a,b,c))):
                raise ValueError('TRIPLET_SCOPE_OR_METHOD')
            if any(r['trial_id'] in seen_global for r in (a,b,c)):raise ValueError('REUSED_TRIPLET_MEMBER')
            seen_global.update(r['trial_id'] for r in (a,b,c))
            for r in (a,b,c):seen[r['method']].add(r['trial_id'])
            if not all(r['eligible'] for r in (a,b,c)):continue
            hashes={r.get('common_initial_plan_sha256') for r in (a,b,c)}
            if None in hashes or len(hashes)!=1:raise ValueError('TRIPLET_NOT_SAME_COMPLETE_INITIAL')
            trials.append({'scale':a['scale'],'trial_ids':ids,'initial_hash':next(iter(hashes)),
                           **hypothesis(a,b,c),'independent_triplets':proof.get('independent_outer_triplets') is True})
    for row in group:
        scale=row['scale'];matched={i for t in trials if t['scale']==scale for i in t['trial_ids']}
        eligible={r['trial_id'] for r in rows if r['scale']==scale and r['eligible']}
        if matched and matched==eligible:row['cohort_alignment']='PASS_REGISTERED_SAME_INITIAL_SUCCESS_COHORTS'
    index_summaries=[];judgment_summaries=[]
    for scale in ('S1','S2','S3'):
        selected=[r for r in trials if r['scale']==scale]
        independent=bool(selected) and all(r['independent_triplets'] for r in selected)
        ids=[i for r in selected for i in r['trial_ids']]
        for method in ('B','C','D'):
            seeds=[byid[i].get('seed_identity') for i in ids if byid[i]['method']==method]
            if any(x is None for x in seeds) or len(seeds)!=len(set(seeds)):independent=False
        judgment_summaries.append({'scale':scale,'valid_registered_triplets':len(selected),
            'hybrid_strict_dual_fraction_vs_initial':sum(r['hybrid_strict_both_vs_initial'] for r in selected)/len(selected) if selected else None,
            'hybrid_nonworse_fraction_vs_initial':sum(r['hybrid_nonworse_vs_initial'] for r in selected)/len(selected) if selected else None,
            'hybrid_strict_dual_fraction_vs_classical':sum(r['hybrid_strict_both_vs_classical'] for r in selected)/len(selected) if selected else None,
            'index_higher_fraction_defined_only':sum(r['H1_hybrid_index_higher'] for r in selected if r['H1_hybrid_index_higher'] is not None)/sum(r['H1_hybrid_index_higher'] is not None for r in selected) if any(r['H1_hybrid_index_higher'] is not None for r in selected) else None,
            'tradeoff_count':sum(r['final_plan_relation']=='TRADEOFF' for r in selected),
            'undefined_I_count':sum(r['I_hybrid_initial_percent'] is None for r in selected),
            'denominator':'valid registered complete triplets; index comparison excludes undefined only'})
        for field in ('I_classical_initial_percent','I_hybrid_initial_percent','delta_I_hybrid_minus_classical_percentage_points'):
            values=[r[field] for r in selected if r[field] is not None]
            index_summaries.append({'scale':scale,'quantity':field,'estimand':'mean_of_verified_trial_indices',
                                   'undefined_count':len(selected)-len(values),**s.summary(values,independent=independent)})
    result.update(common_initial_mean_hypothesis=group,common_initial_trial_hypothesis=trials,
        trial_index_summaries=index_summaries,paired_judgment_summaries=judgment_summaries,audited_rows=rows,
        version='common-initial-20261122-v1',data_role=reg['data_role'],
        legacy_C_reference_duals='historical_diagnostic_only_not_new_hypothesis',
        formal_J_status='HOLD',formal_J=None,n_K_R_status='HOLD',main_experiment='HOLD')
    for r in result['summaries']:
        r['display_name']=NAMES[r['method']]
        failure=next(f for f in result['failures'] if (f['scale'],f['method'])==(r['scale'],r['method']))
        r['observed_valid_records']=r['J']
        r['confirmed_independent_J']=r['J'] if failure['independence_confirmed'] else None
        r['J_interpretation']='observed valid outer records; see confirmed_independent_J; formal J HOLD'
        n=sum(t.get('outer_attempt',False) for t in rows if (t['scale'],t['method'])==(r['scale'],r['method']))
        r['success_rate']=r['J']/n if n else None
    return result
