"""Auditable, failure-aware pilot summaries and candidate main designs."""
import csv
import json
import math
from pathlib import Path
from statistics import mean

from .contract import ROOT,read,dump,fingerprint,digest
from .design import (METHODS,fixed_analysis,precision_count,optimal_allocation,variance_upper,
                     rate_count,wilson,clopper,welch_halfwidth,require_same_settings)


def records(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def telemetry(directory,row,target):
    samples=records(directory/'RESOURCE_SAMPLES.jsonl')
    trace=[]
    for path in directory.glob('native/branches/*/design_trace.jsonl'):
        trace.extend(records(path))
    valid=[t for t in trace if t.get('event')=='verify_candidate' and 'D' in t]
    # Parent start aligns the monotonic clocks across fork/spawn.
    job=read(directory/'job.json') if (directory/'job.json').exists() else None
    parent_start=job['deadline_perf_counter']-row['budget_wall_s'] if job else None
    best=[];incumbent=None
    for entry in sorted(valid,key=lambda x:x['perf_counter']):
        key=(entry['D'],entry['W'])
        if incumbent is None or key<incumbent:
            incumbent=key
            best.append({'parent_elapsed_s':entry['perf_counter']-parent_start if parent_start else None,
                         'D':entry['D'],'W':entry['W'],'pid':entry['pid'],
                         'scope':'internal double-checked candidate; not parent adoption'})
    qstart=[t for t in trace if t.get('event')=='quantum_call' and t['kind']=='start']
    qend=[t for t in trace if t.get('event')=='quantum_call' and t['kind']=='end']
    native=row.get('native_resources') or {}
    branches=native.get('parallel_branches') or []
    checkpoints=row.get('validation_completed_at_s')
    hit=bool(row['adoptable'] and row['D']<=target['D'] and row['W']<=target['W'])
    costs={}
    for event in ('directed_cw','routing_pool','complete_routes','verify_candidate','hybrid'):
        observed=[t['wall_s'] for t in trace if t.get('event')==event and t['kind']=='end']
        costs[event]={'sum_over_branches_s':sum(observed),'completed_calls':len(observed),
                      'overlap':'hybrid contains completion/verification; do not sum these fields'}
    process_cpu={}
    for s in samples:
        for p in s['processes']:
            process_cpu[p['pid']]=max(process_cpu.get(p['pid'],0.),p['cpu_s'])
    return {'run_id':row['run_id'],'case_id':row['case_id'],'method':row['method'],
        'first_internal_feasible_s':min((t['perf_counter']-parent_start for t in valid),default=None) if parent_start else None,
        'first_parent_validated_s':checkpoints,'quality_trajectory':best,
        'target_met':hit,'target_arrival_s':checkpoints if hit else None,
        'target_censored':not hit,'censor_deadline_s':row['budget_wall_s'],
        'restricted_time_to_target_s':checkpoints if hit else row['budget_wall_s'],
        'restricted_time_note':'administrative cap for nonarrival; nonarrival is NOT an arrival at tau',
        'sampled_tree_peak_RSS_KiB':max((s['tree_rss_sum_KiB'] for s in samples),default=None),
        'CPU_s_sample_lower_bound':sum(process_cpu.values()),
        'CPU_s_native_branches':sum(b.get('process_cpu_s') or 0 for b in branches) if branches else None,
        'parent_CPU_s':row.get('parent_cpu_s'),'parent_RSS_highwater_KiB':row.get('parent_max_rss_KiB'),
        'quantum_started':len(qstart),'quantum_completed_trace':len(qend),
        'incomplete_quantum_calls':max(0,len(qstart)-len(qend)),
        'observed_training_shots':sum(q.get('training_shots',0) for q in qend),
        'observed_final_shots':sum(q.get('final_shots',0) for q in qend),
        'shots_accounting_complete':native.get('quantum_accounting_complete',row['method']=='A'),
        'qubits_observed':sorted({q['qubits'] for q in qstart}),
        'branch_count':len(branches),'stages':costs,
        'timing_partition':{k:row.get(k) for k in ('T_input','T_planning','T_adapter','T_validation','T_setup','T_export')},
        'repair':'no separate repair stage exposed; shared completion and verifications measured',
        'A_native_stage_times':read(directory/'native_result.json') if row['method']=='A' and (directory/'native_result.json').exists() else None}


def success_attempts(n,p,assurance=.9):
    """Planning assurance conditional on a conservative p assumption, not a guarantee."""
    from scipy.stats import binom
    if p<=0:return None
    lo=n;hi=max(n,math.ceil(n/p))
    while binom.sf(n-1,hi,p)<assurance:
        hi*=2
        if hi>10000000:return None
    while lo<hi:
        mid=(lo+hi)//2
        if binom.sf(n-1,mid,p)>=assurance:hi=mid
        else:lo=mid+1
    return lo


def candidates(rules,analysis,telemetry_rows,profile):
    table=[]
    for case in analysis:
        scale=case['case_id'];methods=case['methods'];c=methods['C'];d=methods['D']
        costs={m:methods[m]['T_attempt_all']['mean'] for m in METHODS}
        peak=max((r['sampled_tree_peak_RSS_KiB'] or 0 for r in telemetry_rows if r['case_id']==scale),default=0)
        for metric,hs in rules['auxiliary']['h_candidates'].items():
            a,b=c['metrics'][metric],d['metrics'][metric]
            for sensitivity in ('point','normal_variance_upper'):
                v1,v2=a['variance'],b['variance']
                if sensitivity=='normal_variance_upper':
                    # Bonferroni 95% simultaneous upper envelope for 2 independent normal variances.
                    v1=variance_upper(v1,a['n'],.025) if v1 is not None else None
                    v2=variance_upper(v2,b['n'],.025) if v2 is not None else None
                for h in hs:
                    r=precision_count(v1,v2,h) if v1 is not None and v2 is not None else None
                    allocation=optimal_allocation(v1,v2,costs['C'],costs['D'],h) if r and costs['C'] and costs['D'] else None
                    for policy in ('equal','cost_variance'):
                        rc,rd=(r,r) if policy=='equal' else (allocation if allocation else (None,None))
                        for hp in rules['auxiliary']['rate_halfwidth_candidates']:
                            nr=rate_count(hp)
                            rmap={m:nr for m in METHODS}
                            adequate=rc is not None and rd is not None
                            if adequate:
                                rmap['C']=max(nr,success_attempts(rc,c['success_exact'][0]) or 10000001)
                                rmap['D']=max(nr,success_attempts(rd,d['success_exact'][0]) or 10000001)
                            else:rmap['C']=rmap['D']=None
                            total=sum(rmap.values()) if all(v is not None for v in rmap.values()) else None
                            estimate=sum(rmap[m]*costs[m] for m in METHODS) if total and all(costs.values()) else None
                            ceiling=total*profile['tau_s'] if total else None
                            half=welch_halfwidth(v1,v2,rc,rd) if adequate else None
                            for budget in rules['main']['budget_candidates_s']:
                                within=bool(ceiling and ceiling<=budget and peak<=rules['pilot']['tree_memory_limit_MiB']*1024)
                                table.append({'scale':scale,'N':{'S1':1000,'S2':2000,'S3':4000}[scale],
                                    'evaluation_input':f'frozen-v1:{scale}','M':1,'metric':metric,'h':h,
                                    'sensitivity':sensitivity,'allocation':policy,'rate_h':hp,
                                    'R_A_quality':1,'R_a':rmap,'required_successes_C':rc,'required_successes_D':rd,
                                    'tau_s':profile['tau_s'],'predicted_halfwidth':half,
                                    'prediction_note':'conditional normal-model planning; successes not assured; unknown stochastic zero variance prevents certification',
                                    'rate_precision_worstcase_Wilson_h':hp,'rate_required_attempts':nr,
                                    'total_attempts':total,'estimated_wall_s':estimate,'cap_wall_s':ceiling,
                                    'reserved_core_wall_s':ceiling*4 if ceiling else None,
                                    'parallel_elapsed_s':estimate,'parallel_note':'four branches already inside measured attempt; method concurrency one, no extra division by four',
                                    'sampled_tree_peak_RSS_KiB':peak,'memory_limit_MiB':rules['pilot']['tree_memory_limit_MiB'],
                                    'main_budget_candidate_s':budget,'within_caps':within,'adopted':False,
                                    'reason':'precision/cost choices pending' if within else 'missing variance or exceeds cap',
                                    'zero_sample_variance':a['variance']==0 or b['variance']==0})
    return table


def generalization_sensitivity(rules,analysis,profile):
    from scipy.stats import t
    result=[]
    for case in analysis:
        a=case['methods']['C']['metrics']['D'];b=case['methods']['D']['metrics']['D']
        within=(a['variance']+b['variance']) if a['variance'] is not None and b['variance'] is not None else None
        for M in (5,10,30):
            for R in (1,3,5):
                for sd_between in (5,20,50):
                    h=float(t.ppf(.975,M-1)*math.sqrt((sd_between**2+within/R)/M)) if within is not None else None
                    count=M*len(METHODS)*R
                    result.append({'scale':case['case_id'],'M':M,'R_a':{m:R for m in METHODS},
                        'assumed_between_SD_km':sd_between,'assumption_not_measurement':True,
                        'within_variance_source':'fixed demand pilot, sensitivity only, not population estimate',
                        'predicted_halfwidth_km':h,'total_attempts':count,'cap_wall_s':count*profile['tau_s'],
                        'adopted':False,'reason':'no independent demand-population pilot; demand law/inputs not registered'})
    return result


def report(root,rules,selection,chosen,variance_m,variance_rows,confirm_m,confirm_rows):
    identity=require_same_settings([variance_m,confirm_m])
    out=root/'design';out.mkdir(exist_ok=False)
    analyses={}
    all_telemetry=[];all_rows=[]
    stages=[('selection_'+s['profile']['id'],s['rows']) for s in selection]+[('variance',variance_rows),('confirmation',confirm_rows)]
    for name,rows in stages:
        analyses[name]=fixed_analysis(rows)
        all_rows.extend(rows)
        for row in rows:
            all_telemetry.append({'stage':name,**telemetry(root/name/'runs'/row['run_id'],row,rules['auxiliary']['target_values'][row['case_id']])})
    for name,analysis in analyses.items(): dump(out/(name+'_ANALYSIS.json'),analysis)
    dump(out/'TELEMETRY.json',all_telemetry)
    variance_telemetry=[r for r in all_telemetry if r['stage']=='variance']
    table=candidates(rules,analyses['variance'],variance_telemetry,chosen['profile'])
    dump(out/'CANDIDATES.json',table)
    with (out/'CANDIDATES.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(table[0]));writer.writeheader()
        writer.writerows([{**r,'R_a':json.dumps(r['R_a'])} for r in table])
    dump(out/'GENERALIZATION_SENSITIVITY.json',generalization_sensitivity(rules,analyses['variance'],chosen['profile']))
    # Rate precision and target censoring are reported independently of conditional quality.
    rates=[]
    for stage_name,rows in stages:
        for case in rules['pilot']['scales']:
            for method in METHODS:
                own=[r for r in rows if r['case_id']==case and r['method']==method and r['input_state']=='VALID' and r['termination_reason']!='NOT_STARTED']
                targets=[r for r in all_telemetry if r['stage']==stage_name and r['case_id']==case and r['method']==method]
                hits=sum(r['target_met'] for r in targets)
                rates.append({'stage':stage_name,'case_id':case,'method':method,'n':len(own),
                    'feasible':sum(r['adoptable'] for r in own),'target_hits':hits,
                    'target_Wilson':wilson(hits,len(own)),'target_exact':clopper(hits,len(own)),
                    'restricted_mean_time_to_target_s':mean(r['restricted_time_to_target_s'] for r in targets) if targets else None,
                    'target_arrival_time_scope':'first final parent validation only; no earlier parent checkpoint available'})
    dump(out/'RATES_AND_CENSORING.json',rates)
    # One fixed demand per scale supplies no between-demand variance estimate.
    determinism=[]
    for case in rules['pilot']['scales']:
        for method in METHODS:
            hashes=[]
            for row in variance_rows:
                if row['case_id']==case and row['method']==method and row['adoptable']:
                    plan=read(root/'variance/runs'/row['run_id']/'plan.json')
                    hashes.append(fingerprint(plan['trips']))
            determinism.append({'case_id':case,'method':method,'accepted_plans':len(hashes),
                'distinct_physical_plans':len(set(hashes)),
                'classification':'frozen deterministic rule; timing replicates' if method=='A' and len(set(hashes))==1 else
                    'observed variation' if len(set(hashes))>1 else 'no variation observed; stochastic determinism not established',
                'R_quality_recommended':1 if method=='A' and len(set(hashes))==1 else None})
    dump(out/'DETERMINISM.json',determinism)
    # Resource-feasible fixed-count designs show achievable precision without selecting h afterwards.
    attainable=[]
    for case in analyses['variance']:
        costs={m:case['methods'][m]['T_attempt_all']['mean'] for m in METHODS}
        a=case['methods']['C']['metrics']['D'];b=case['methods']['D']['metrics']['D']
        for budget in rules['main']['budget_candidates_s']:
            R=max(0,math.floor(budget/(len(METHODS)*chosen['profile']['tau_s'])))
            h=welch_halfwidth(a['variance'],b['variance'],R,R) if R>=2 and a['variance'] is not None and b['variance'] is not None else None
            attainable.append({'scale':case['case_id'],'M':1,'R_equal':R,'wall_cap_s':budget,
                'predicted_D_halfwidth_km_if_all_success':h,'worstcase_rate_halfwidth':wilson(R//2,R)[1]-R//2/R if R else None,
                'not_a_guarantee':True})
    dump(out/'BUDGET_ATTAINABLE_PRECISION.json',attainable)
    all_complete=all(r['termination_reason']!='NOT_STARTED' for r in all_rows)
    all_success=sum(r['adoptable'] for r in all_rows)
    total_time=sum(r['T_attempt'] or 0 for r in all_rows)
    quality_identified=all(min(c['methods']['C']['metrics']['D']['n'],c['methods']['D']['metrics']['D']['n'])>=2 for c in analyses['variance'])
    confirm_good=all(r['adoptable'] for r in confirm_rows)
    status={'pilot_pipeline_complete':all_complete,'variance_estimation_available':quality_identified,
        'settings_qualification_passed':chosen['qualified'],'confirmation_all_adoptable':confirm_good,
        'main_start_allowed':False,'main_started':False,'main_decision':'HOLD',
        'remaining_research_decisions':rules['main']['decision_required'],
        'engineering_blockers':([] if chosen['qualified'] else ['no candidate qualified every scale/method with D quantum calls'])+
            ([] if quality_identified else ['fewer than two successful C/D observations in a fixed-demand cell'])+
            ([] if confirm_good else ['confirmation contains failures']),
        'attempts_executed':len([r for r in all_rows if r['termination_reason']!='NOT_STARTED']),
        'accepted_plans':all_success,'measured_total_attempt_wall_s':total_time,
        'selected_profile':chosen['profile'],'setting_identity':identity,
        'M_per_scale':1,'independent_demand_families':1,
        'formal_A_reference_registered':False,'main_R_a':None}
    dump(out/'STATUS.json',status)
    # Fully concrete pilot settings/input hashes retained, intentionally unresolved main choices.
    dump(out/'MAIN_MANIFEST.json',{'experiment_id':rules['experiment_id']+'_main_pending',
        'phase':'formal','executable':False,'start_gate':status,
        'comparison_contract':variance_m['contract_id'],'code_version':variance_m['code_version'],
        'source_hashes':variance_m['source_hashes'],'cases':variance_m['cases'],
        'method_registry':variance_m['registry'],'internal_config':variance_m['BCD_config'],
        'resource_contract':variance_m['resource_contract'],'T_kind':variance_m['T_kind'],
        'M_per_scale':1,'R_a':None,'seed_list':None,'execution_order':None,
        'seed_rule':'fresh domain 2026111701, enumerate method-specific solver/quantum streams after fixed R_a',
        'main_stop_rule':rules['main']['stopping'],'analysis':rules['main']['inference'],
        'selection':'existing verified min D then W then branch ID; no best across independent attempts',
        'failure_policy':'all attempted rows retained, no null quality replaced by zero; no retry substitution',
        'references':'new formal A groups with all exact timing run IDs required; pilot references never reused',
        'unresolved':['h_D','required rate precision','main resource ceiling','R_a','main seed list/order after R_a']})
    return status
