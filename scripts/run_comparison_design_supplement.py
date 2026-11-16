#!/usr/bin/env python3
"""Complete the design comparison: uniform ALL methods versus variance/cost allocation.

Analysis only. Reuses frozen variance data; never launches a solver or changes
registered settings. Output keeps unknown stochastic variance and resource
assumptions explicit. Confirmation observations do not enter variance estimates.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.comparison_v1.contract import read,dump,digest,fingerprint
from kmd_toc.comparison_v1.design import (METHODS,precision_count,optimal_allocation,
    variance_upper,rate_count,welch_halfwidth,require_same_settings)
from kmd_toc.comparison_v1.design_report import success_attempts
from kmd_toc.comparison_v1.evaluation import paired


def outside_gaps(root,manifest):
    spans=[]
    for run in manifest['runs']:
        d=root/'variance/runs'/run['run_id']
        if not (d/'job.json').exists() or not (d/'result.json').exists():continue
        j=read(d/'job.json');r=read(d/'result.json')
        start=j['deadline_perf_counter']-j['case']['budget_wall_s']
        spans.append((start,start+r['T_attempt']))
    spans.sort()
    return [max(0.,b[0]-a[1]) for a,b in zip(spans,spans[1:])]


def success_pair(v1,v2,c1,c2,h,policy):
    if v1 is None or v2 is None:return None
    eq=precision_count(v1,v2,h)
    if eq is None:return None
    if policy=='uniform_all':return eq,eq
    if v1==0 and v2==0:return 2,2
    if v1==0:return 2,eq
    if v2==0:return eq,2
    return optimal_allocation(v1,v2,c1,c2,h)


def build(root,out):
    variance_manifest=read(root/'variance/REGISTERED.json')
    confirmation_manifest=read(root/'confirmation/REGISTERED.json')
    settings_id=require_same_settings([variance_manifest,confirmation_manifest])
    rules=read(root/'PREREGISTERED_RULES.json')
    analysis=read(root/'design/variance_ANALYSIS.json')
    telemetry=read(root/'design/TELEMETRY.json')
    variance_rows=read(root/'variance/ALL_RESULTS.json')
    gaps=outside_gaps(root,variance_manifest)
    mean_gap=mean(gaps) if gaps else None
    max_gap=max(gaps) if gaps else None
    # These are transparent planning reserves, not measured strict upper bounds.
    cleanup_reserve_s=10.
    fixed_orchestration_reserve_s=300.
    rows=[]
    for case in analysis:
        scale=case['case_id'];methods=case['methods']
        costs={m:methods[m]['T_attempt_all']['mean'] for m in METHODS}
        c,d=methods['C'],methods['D']
        selected_case=next(x for x in variance_manifest['cases'] if x['case_id']==scale)
        tau=selected_case['budget_wall_s']
        resources=[x for x in telemetry if x['stage']=='variance' and x['case_id']==scale]
        worker_peak=max((x['sampled_tree_peak_RSS_KiB'] or 0 for x in resources),default=0)
        parent_peak=max((x['parent_RSS_highwater_KiB'] or 0 for x in resources),default=0)
        native_peak=max(((r.get('native_resources') or {}).get('aggregate_RSS_upper_bound_KiB') or 0
                        for r in variance_rows if r['case_id']==scale),default=0)
        memory_proxy=max(worker_peak,native_peak)+parent_peak
        for metric,hs in rules['auxiliary']['h_candidates'].items():
            s1,s2=c['metrics'][metric],d['metrics'][metric]
            for sensitivity in ('point','normal_variance_upper'):
                v1,v2=s1['variance'],s2['variance']
                if sensitivity=='normal_variance_upper':
                    v1=variance_upper(v1,s1['n'],.025) if v1 is not None else None
                    v2=variance_upper(v2,s2['n'],.025) if v2 is not None else None
                for h in hs:
                    for hp in rules['auxiliary']['rate_halfwidth_candidates']:
                        nr=rate_count(hp)
                        for policy in ('uniform_all','variance_cost'):
                            quality=success_pair(v1,v2,costs['C'],costs['D'],h,policy) if costs['C'] and costs['D'] else None
                            counts={m:nr for m in METHODS}
                            if quality:
                                nc,nd=quality
                                ac=success_attempts(nc,c['success_exact'][0]);ad=success_attempts(nd,d['success_exact'][0])
                                if ac is not None and ad is not None:
                                    counts['C']=max(nr,ac);counts['D']=max(nr,ad)
                                else:quality=None
                            if policy=='uniform_all' and quality:
                                counts={m:max(counts.values()) for m in METHODS}
                            total=sum(counts.values())
                            expected=sum(counts[m]*costs[m] for m in METHODS) if all(costs.values()) else None
                            h_pred=welch_halfwidth(v1,v2,*quality) if quality else None
                            overhead=total*mean_gap+fixed_orchestration_reserve_s if mean_gap is not None else None
                            cost_with_overhead=expected+overhead if expected is not None and overhead is not None else None
                            attempt_cap=total*tau
                            reserve_cost=total*(tau+cleanup_reserve_s+(max_gap or 0))+fixed_orchestration_reserve_s
                            driver=('unknown quality precision' if not quality else
                                    'feasible/target probability precision' if max(counts.values())==nr else metric+' quality precision/success assurance')
                            zero_observed=(s1['variance']==0 or s2['variance']==0)
                            for budget in rules['main']['budget_candidates_s']:
                                rows.append({'scale':scale,'N':selected_case['input']['counts'][0],
                                    'input_hash':selected_case['input']['input_hash'],'M':1,
                                    'metric':metric,'h':h,'rate_h':hp,'sensitivity':sensitivity,
                                    'allocation':policy,'R_a':counts,'R_A_quality':1,'R_A_timing':counts['A'],
                                    'quality_required_successes_C':quality[0] if quality else None,
                                    'quality_required_successes_D':quality[1] if quality else None,
                                    'quality_design_identified':quality is not None,
                                    'observed_stochastic_zero_variance':zero_observed,
                                    'precision_certified':False,
                                    'predicted_CI_halfwidth':h_pred,
                                    'CI_prediction_scope':'planning conditional on sufficient successes and variance assumptions; not a coverage guarantee',
                                    'success_assurance':'.90 per method conditional on pilot exact lower success probability; not joint .90',
                                    'count_driver':driver,'rate_required_attempts':nr,
                                    'tau_s':tau,'total_attempts':total,
                                    'mean_measured_attempt_cost_s':costs,
                                    'estimated_attempt_wall_s':expected,
                                    'observed_mean_between_attempt_gap_s':mean_gap,
                                    'estimated_wall_including_orchestration_s':cost_with_overhead,
                                    'sum_attempt_caps_s':attempt_cap,
                                    'planning_reserve_wall_s':reserve_cost,
                                    'reserve_assumptions':{'cleanup_s_per_attempt':cleanup_reserve_s,'between_attempt_gap_s':max_gap,
                                                           'fixed_setup_s':fixed_orchestration_reserve_s},
                                    'reserve_not_a_strict_IO_or_system_upper_bound':True,
                                    'parallel_elapsed_s':cost_with_overhead,
                                    'parallelism':'four internal branches already included; methods serial; no second divide by four',
                                    'reserved_core_wall_s':4*reserve_cost,
                                    'sampled_worker_tree_peak_RSS_KiB':worker_peak,
                                    'native_tree_HWM_sum_KiB':native_peak,
                                    'parent_highwater_RSS_KiB':parent_peak,
                                    'memory_upper_proxy_KiB':memory_proxy,
                                    'memory_scope':'max(sampled tree peak,native HWM sum) plus coordinator HWM; shared pages duplicate; highwaters are nonconcurrent; incomplete process observations remain partial',
                                    'tree_memory_limit_MiB':rules['pilot']['tree_memory_limit_MiB'],
                                    'main_budget_s':budget,
                                    'within_planning_time_reserve':reserve_cost<=budget,
                                    'within_observed_memory_proxy':memory_proxy<=rules['pilot']['tree_memory_limit_MiB']*1024,
                                    'adopted':False,
                                    'reason':'research choices pending; unknown zero-variance sensitivity requires additional evidence or registered assumption' if zero_observed else 'research precision/cost choices pending'})
    out.mkdir(parents=True,exist_ok=False)
    dump(out/'CANDIDATES_ALL_METHODS.json',rows)
    control_outcomes={}
    for stage in ('selection_lean','selection_retained','variance','confirmation'):
        path=root/stage/'tables/ALL_ATTEMPTS.json'
        if path.exists():
            control_outcomes[stage]=paired(read(path)['rows'],'D_CLASSICAL_REPLACEMENT','D')
    dump(out/'CONTROL_OUTCOMES.json',{
        'scope':'descriptive joint outcomes by stage; no paired inferential test based on repeat labels',
        'stages':control_outcomes})
    # Discrete heuristic outputs can be identical in a small pilot. A zero
    # sample variance supplies no usable normal upper sensitivity here. Show
    # explicit hypothetical additional SDs instead of claiming exact precision.
    sd_sensitivity=[]
    for case in analysis:
        methods=case['methods'];c=methods['C'];d=methods['D']
        vc,vd=c['metrics']['D']['variance'],d['metrics']['D']['variance']
        if vc is None or vd is None:continue
        tau=next(x['budget_wall_s'] for x in variance_manifest['cases'] if x['case_id']==case['case_id'])
        for extra_c in (0,1,5,10):
            for extra_d in (0,1,5,10):
                for h in rules['primary']['h_candidates_km']:
                    n=precision_count(vc+extra_c**2,vd+extra_d**2,h)
                    for hp in rules['auxiliary']['rate_halfwidth_candidates']:
                        nr=rate_count(hp)
                        ac=success_attempts(n,c['success_exact'][0]) if n else None
                        ad=success_attempts(n,d['success_exact'][0]) if n else None
                        counts={m:nr for m in METHODS}
                        if ac is not None and ad is not None:
                            counts['C']=max(nr,ac);counts['D']=max(nr,ad)
                        else:counts['C']=counts['D']=None
                        total=sum(counts.values()) if all(x is not None for x in counts.values()) else None
                        sd_sensitivity.append({'scale':case['case_id'],'M':1,
                            'additional_SD_C_km':extra_c,'additional_SD_D_km':extra_d,
                            'assumed_not_measured':True,'adopted':False,'h_km':h,'rate_h':hp,
                            'required_quality_successes_per_C_D':n,'R_a':counts,'total_attempts':total,
                            'sum_attempt_caps_s':total*tau if total else None,
                            'note':'independent planning sensitivity, not a variance confidence bound; SD grid 0/1/5/10 is a proposed assumption, not evidence'})
    dump(out/'WITHIN_VARIANCE_SENSITIVITY.json',sd_sensitivity)
    from scipy.stats import norm
    attainable=[]
    z=float(norm.ppf(.975))
    for case in analysis:
        tau=next(x['budget_wall_s'] for x in variance_manifest['cases'] if x['case_id']==case['case_id'])
        c,d=case['methods']['C']['metrics']['D'],case['methods']['D']['metrics']['D']
        for budget in rules['main']['budget_candidates_s']:
            r=max(0,math.floor((budget-fixed_orchestration_reserve_s)/
                (len(METHODS)*(tau+cleanup_reserve_s+(max_gap or 0)))))
            h=welch_halfwidth(c['variance'],d['variance'],r,r) if r>=2 and c['variance'] is not None and d['variance'] is not None else None
            attainable.append({'scale':case['case_id'],'M':1,'budget_s':budget,
                'R_a_uniform_all':{m:r for m in METHODS},'R_A_quality':1,
                'point_predicted_D_halfwidth_km_if_all_success':h,
                'observed_zero_variance_warning':c['variance']==0 or d['variance']==0,
                'worst_case_Wilson_rate_halfwidth':z/(2*math.sqrt(r+z*z)) if r else None,
                'precision_guaranteed':False,
                'cost_basis':'trial caps plus explicit cleanup, measured max gap and setup planning reserves',
                'do_not_claim_original_precision_after_reducing_R':True})
    dump(out/'RESOURCE_LIMIT_PRECISION.json',attainable)
    with (out/'CANDIDATES_ALL_METHODS.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader()
        for r in rows:
            writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,dict) else v for k,v in r.items()})
    dump(out/'ANALYSIS_PROVENANCE.json',{'script':str(Path(__file__).resolve()),'sha256':digest(__file__),
        'variance_registration_sha256':digest(root/'variance/REGISTERED.json'),
        'confirmation_registration_sha256':digest(root/'confirmation/REGISTERED.json'),
        'settings_identity':settings_id,'source_data':'variance phase only; confirmation used solely for settings identity check',
        'frozen_experiment_sources_modified':False,
        'scope':'supplements original table whose equal allocation refers to C/D only; uniform_all equalizes all five methods',
        'all_method_counts_are_planning_alternatives_not_adopted':True,
        'unknown_variance_rows':'rate-only counts, no claim of continuous quality precision',
        'overhead_assumptions':'measured between-trial gaps plus explicit cleanup/setup planning reserves; no absolute disk/host upper-bound guarantee'})
    print(json.dumps({'rows':len(rows),'output':str(out),'main_started':False},ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='output/toc_delivery/comparison_design_20261116_v1')
    parser.add_argument('--output',default='output/toc_delivery/comparison_design_20261116_v1/design_supplement')
    args=parser.parse_args();build(Path(args.root).resolve(),Path(args.output).resolve())


if __name__=='__main__':main()
