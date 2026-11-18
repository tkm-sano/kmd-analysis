"""Failure-aware pilot estimates and unadopted three-scale design candidates."""
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean,median,stdev,variance
import tarfile
import time
from pilot import (ROOT,DOC,ID,METHODS,SCALES,read,digest,atomic,fingerprint,load_registration,attempt_state)
from kmd_toc.comparison_v1.design import wilson,clopper,rate_count,welch_halfwidth,precision_count,optimal_allocation,variance_upper
from kmd_toc.comparison_v1.design_report import success_attempts

def stats(values):
    values=[v for v in values if v is not None]
    return {'n':len(values),'mean':mean(values) if values else None,'sample_SD':stdev(values) if len(values)>1 else None,
        'variance':variance(values) if len(values)>1 else None,'median':median(values) if values else None,
        'min':min(values) if values else None,'max':max(values) if values else None,
        'reason':None if len(values)>1 else ('INSUFFICIENT_N_FOR_VARIANCE' if values else 'NO_OBSERVATIONS')}

def independent_difference(a,b):
    delta=b['mean']-a['mean'] if a['n'] and b['n'] else None
    reason='INSUFFICIENT_SUCCESS_COUNT' if min(a['n'],b['n'])<2 else ('BOTH_SAMPLE_VARIANCES_ZERO' if a['variance']+b['variance']==0 else None)
    half=welch_halfwidth(a['variance'],b['variance'],a['n'],b['n']) if reason is None else None
    return {'mean_difference':delta,'CI95':None if half is None else [delta-half,delta+half],
        'halfwidth':half,'null_reason':reason,'n_left':a['n'],'n_right':b['n'],
        'assumptions':'independent groups, finite variances, small-sample approximate normal/Welch; shared-host time independence unverified',
        'zero_variance_warning':a['variance']==0 or b['variance']==0}

def rate_record(k,n,pending=0):
    interval={'numerator':k,'denominator':n,'estimate':k/n if n else None,'Wilson95':wilson(k,n),'Clopper_Pearson95':clopper(k,n)}
    return {'all_started':interval if not pending else {'numerator':None,'denominator':n+pending,'estimate':None,'Wilson95':None,'Clopper_Pearson95':None,'reason':'UNRESOLVED_STARTED_TRIALS'},
        'provisional_settled_only':interval if pending else None,'unresolved_started':pending,
        'reason':None if n else 'NO_SETTLED_STARTED_TRIALS','simultaneous_coverage_claimed':False}

def csvwrite(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w',newline='') as stream:
        w=csv.DictWriter(stream,fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,allow_nan=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def events(path):
    if path.exists():
        with path.open() as stream:
            for line in stream:
                if line.strip():yield json.loads(line)

def branch_telemetry(directory,b,method):
    path=directory/f"branch_{b['branch_id']:02d}"/'stages';counts=Counter();per=Counter();terminations=[];qstarts=[];qends=[];cp=[];cwend=None
    shots={'training':0,'final':0};training_starts=training_success=training_failed=final_starts=final_ends=0
    first_internal=None
    for e in events(path/'work.jsonl'):
        kind=e['event'];counts[kind]+=1
        if kind=='training_evaluation_start':training_starts+=1;per[(e['call_id'],e['restart'])]+=1
        if kind=='training_evaluation_end':training_success+=1;shots['training']+=e['actual_shots']
        if kind=='training_evaluation_failed':training_failed+=1
        if kind=='final_sample_start':final_starts+=1
        if kind=='final_sample_end':final_ends+=1;shots['final']+=e['actual_shots']
        if kind=='quantum_call_start':qstarts.append({k:e.get(k) for k in ('call_id','seed','max_evaluations_per_restart','total_starts')})
        if kind=='quantum_call_end':qends.append(e['call_id'])
        if kind=='CP_end':cp.append(e)
        if kind=='CW_complete':cwend=e
        if kind in ('A_complete','Routing_end','CP_end','LP_end','IP_end','catalogue_complete'):terminations.append(e)
        if kind=='candidate_checked' and e.get('valid') and first_internal is None:first_internal=e
    qc_complete=len(qstarts)==len(qends) and training_starts==training_success and final_starts==final_ends
    reconciliation=None
    if b.get('counts') is not None:
        bc=b['counts'];reconciliation=(bc.get('quantum_training_shots',0)==shots['training'] and bc.get('quantum_final_shots',0)==shots['final'])
    return {'branch_id':b['branch_id'],'pid':b.get('pid'),'affinity':b.get('cpu_affinity'),'seeds':b.get('seeds'),
        'state':b.get('execution_state'),'plan_state':b.get('plan_state'),'D':b.get('D'),'W':b.get('W'),'wall_s':b.get('wall_s'),
        'cpu_s':b.get('cpu_s'),'HWM_KiB':b.get('max_rss_KiB'),'HWM_scope':'child RUSAGE_SELF highwater, not simultaneous tree RSS',
        'counts':b.get('counts'),'stage_terminations':terminations,'CP_states':[e.get('status') for e in cp],
        'quantum_calls':qstarts,'quantum_completed':len(qends),'training_attempts':training_starts,'training_successes':training_success,
        'training_failures':training_failed,'observed_training_shots':shots['training'] if training_starts else (0 if method!='D' else None),
        'observed_final_shots':shots['final'] if final_starts else (0 if method!='D' else None),
        'complete_training_shots':shots['training'] if training_starts==training_success and (training_starts or method!='D') else None,
        'complete_final_shots':shots['final'] if final_starts==final_ends and (final_starts or method!='D') else None,
        'missing_shots_reason':None if qc_complete else 'INCOMPLETE_OR_FAILED_SAMPLING; observed sums are partial only',
        'initial_evaluations':(b.get('counts') or {}).get('quantum_optimizer_initial_preparations'),
        'cache_hits':(b.get('counts') or {}).get('quantum_optimizer_cache_hits'),
        'shots_accounting_complete':qc_complete,'counter_shots_reconcile':reconciliation,
        'max_evaluations_per_call_start':max(per.values(),default=None),
        'expected_pricing_calls':2*cwend['routes'] if cwend and method in ('D','D_CLASSICAL_REPLACEMENT') else None,
        'all_quantum_calls_processed':len(qstarts)==2*cwend['routes'] if cwend and method=='D' else None,
        'native_observed_threads':b.get('observed_threads'),'source':b.get('final_candidate_source')}

def provenance(root,row,m):
    if not row.get('adoptable'):return {'source':None,'CW_visit_order_set_equal':None,'reason':'NO_ADOPTED_PLAN'}
    directory=root/'runs'/row['run_id'];bid=row['selected_branch_id'];stage=directory/f'branch_{bid:02d}'/'stages'
    plan=read(directory/'plan.json')
    # Frozen OD index 0 is depot; exact ordered routes from existing CW artifact.
    case=next(c for c in m['cases'] if c['case_id']==row['case_id'])
    od=read(Path(case['input']['directory'])/'od/manifest.json')
    ids=od['ids'];mapping={i:s for i,s in enumerate(ids)}
    cwpath=stage/'directed_CW.json'
    if not cwpath.exists():return {'source':row.get('final_candidate_source'),'CW_visit_order_set_equal':None,'reason':'A_HAS_NO_CW'}
    cw=read(cwpath)['routes'];cwset={tuple(mapping[i] for i in route) for route in cw}
    selected={tuple(v['stop_id'] for v in t['visits']) for t in plan['trips']}
    cpe=[e for e in events(stage/'work.jsonl') if e['event']=='CP_end']
    initial=None
    if row['method']=='C':
        # Earliest verified CW candidate is observed before Routing starts.
        for e in events(stage/'work.jsonl'):
            if e['event']=='Routing_start':break
            if 'D' in e and 'W' in e:initial={'D':e['D'],'W':e['W'],'scope':'pre-Routing verified CW completion'}
    return {'source':row.get('final_candidate_source'),'CP_states':[e.get('status') for e in cpe],
        'CW_visit_order_set_equal':selected==cwset,'CW_route_count':len(cwset),'adopted_route_count':len(selected),
        'new_selected_routes_vs_CW':len(selected-cwset),'initial_CW_candidate':initial,
        'new_pricing_routes_in_final':plan['method_settings'].get('new_pricing_routes_in_final'),
        'interpretation':'same visit order set does not fix vehicle assignment; CP FEASIBLE is not optimality; C non-CW implies Routing-pool origin only'}

def resource_summary(directory):
    previous=None;delta=[];lags=[];records=0;maxrss=None;cpus={}
    for e in events(directory/'RESOURCE_SAMPLES.jsonl'):
        measured=max((b['perf_counter'] for b in e['branches']),default=None)
        if measured is not None:
            if previous is not None:delta.append({'record_elapsed_gap_s':e['elapsed_s']-previous[0],
                'measurement_perf_gap_s':measured-previous[1],
                'relative_recording_lag_change_s':e['elapsed_s']-previous[0]-(measured-previous[1])})
            previous=(e['elapsed_s'],measured)
        records+=1;maxrss=max(maxrss or 0,e['tree_rss_sum_KiB'])
        for b in e['branches']:
            for p in b['processes']:cpus[p['pid']]=max(cpus.get(p['pid'],0),p['cpu_s'])
    return {'records':records,'sampled_tree_RSS_max_KiB':maxrss,'CPU_samples_sum_lower_bound_s':sum(cpus.values()) if cpus else None,
        'largest_record_gaps':sorted(delta,key=lambda d:d['record_elapsed_gap_s'],reverse=True)[:5],
        'timestamp_scope':'branch tree_sample perf_counter vs parent elapsed at log serialization; origin cancels in differences; flush completion time not observed',
        'cause_or_total_T_contribution':None,'no_time_correction_applied':True}

def candidate_table(groups):
    from functools import lru_cache
    req= lru_cache(None)(precision_count); opt=lru_cache(None)(optimal_allocation); attempts=lru_cache(None)(success_attempts)
    costs={s:{m:groups[s][m]['T_attempt_all']['mean'] for m in METHODS} for s in SCALES}
    maxima={s:{m:groups[s][m]['T_attempt_all']['max'] for m in METHODS} for s in SCALES}
    plower={s:{m:(groups[s][m]['success_exact95'] or [None])[0] for m in METHODS} for s in SCALES}
    sensitivities=[];table=[]
    for scope in ('inherited_S2_primary','three_scale_primary_Bonferroni'):
        alpha=.05 if scope=='inherited_S2_primary' else .05/3
        for mode,add in [('observed',0),('normal_variance_upper',0),('additional_SD',1),('additional_SD',5),('additional_SD',10)]:
            vs={};reason={}
            for s in SCALES:
                c=groups[s]['C']['metrics']['D'];d=groups[s]['D']['metrics']['D'];vc,vd=c['variance'],d['variance']
                why=None
                if vc is None or vd is None:vc=vd=None;why='INSUFFICIENT_SUCCESS_COUNT'
                elif mode=='normal_variance_upper':
                    va=.025 if scope=='inherited_S2_primary' else .05/6
                    vc,vd=variance_upper(vc,c['n'],va),variance_upper(vd,d['n'],va)
                    if vc is None or vd is None:why='ZERO_SAMPLE_VARIANCE_UNKNOWN_UPPER_BOUND'
                elif add:vc+=add**2;vd+=add**2
                elif vc+vd==0:why='BOTH_ZERO_QUALITY_R_UNIDENTIFIED';vc=vd=None
                vs[s]=(vc,vd);reason[s]=why
                sensitivities.append({'scope':scope,'scale':s,'mode':mode,'sigma_add_each_group_km':add,
                    'observed_variance_C':c['variance'],'observed_variance_D':d['variance'],
                    'planning_variance_C':vc,'planning_variance_D':vd,'null_reason':why,'identified_from_pilot':why is None and add==0 and c['variance']>0 and d['variance']>0,
                    'assumptions':'normal model; chi-square upper only positive variance' if mode=='normal_variance_upper' else ('unadopted symmetric additional variance per group' if add else 'observed variance plug-in; zero observation does not establish true zero'),
                    'variance_envelope_alpha_each':(.025 if scope=='inherited_S2_primary' else .05/6) if mode=='normal_variance_upper' else None})
            for h in (1,5,10):
                for hp in (.15,.10,.05):
                    nr=rate_count(hp)
                    for policy in ('uniform_all_15','cost_variance_CD'):
                        required={};rmap={s:{m:nr for m in METHODS} for s in SCALES};half={};nulls={}
                        for s in SCALES:
                            vc,vd=vs[s];rc=rd=None
                            if vc is not None and vd is not None:
                                if policy=='uniform_all_15':rc=rd=req(vc,vd,h,alpha)
                                elif min(vc,vd)>0 and costs[s]['C'] and costs[s]['D']:
                                    rc,rd=opt(vc,vd,costs[s]['C'],costs[s]['D'],h,alpha)
                                elif vc+vd>0:rc=rd=req(vc,vd,h,alpha) # boundary plug-in, no finite cost-optimum claim
                            required[s]={'C':rc,'D':rd}
                            half[s]=welch_halfwidth(vc,vd,rc,rd,alpha) if rc is not None and rd is not None else None
                            for method,n in [('C',rc),('D',rd)]:
                                p=plower[s][method]
                                total=attempts(n,p) if n is not None and p is not None else None
                                rmap[s][method]=max(nr,total) if total is not None else None
                            if rmap[s]['C'] is None or rmap[s]['D'] is None:nulls[s]=reason[s] or 'NO_POSITIVE_SUCCESS_PROBABILITY_OR_ALLOCATION'
                        available=all(rmap[s][m] is not None for s in SCALES for m in METHODS)
                        if policy=='uniform_all_15':
                            n=max((rmap[s][m] or 0 for s in SCALES for m in METHODS),default=nr) if available else None
                            rmap={s:{m:n for m in METHODS} for s in SCALES}
                        total=sum(rmap[s][m] for s in SCALES for m in METHODS) if available else None
                        estimated=sum(rmap[s][m]*costs[s][m] for s in SCALES for m in METHODS) if available and all(costs[s][m] is not None for s in SCALES for m in METHODS) else None
                        high=sum(rmap[s][m]*maxima[s][m] for s in SCALES for m in METHODS) if estimated is not None else None
                        rateonly=sum(nr*costs[s][m] for s in SCALES for m in METHODS) if all(costs[s][m] is not None for s in SCALES for m in METHODS) else None
                        table.append({'candidate_id':f'{scope}_{mode}_sd{add}_h{h}_rate{hp}_{policy}',
                            'scope':scope,'scales':list(SCALES),'M_per_scale':1,'h_D_km':h,'quality_interval_alpha_each':alpha,
                            'S1_S3_intervals':'exploratory pointwise 95%; same h used as unadopted planning sensitivity' if scope=='inherited_S2_primary' else 'three D-C distance intervals Bonferroni family 95%',
                            'variance_mode':mode,'sigma_add_each_group_km':add,'variance_assumptions':{s:vs[s] for s in SCALES},
                            'allocation':policy,'rate_Wilson_worst_halfwidth':hp,'rate_required_attempts_each':nr,
                            'quality_required_successes':required,'quality_predicted_halfwidth_km':half,
                            'assumed_success_probability':plower,'success_assurance_each':.9,
                            'success_assumption':'pilot two-sided exact 95% success lower limit used as future binomial p; no simultaneous guarantee',
                            'R_a_by_scale':rmap,'R_A_quality_reference':1,'R_A_time_rate_by_scale':{s:rmap[s]['A'] for s in SCALES},
                            'total_attempts_all_scales':total,'estimated_T_attempt_wall_s':estimated,
                            'observed_max_cost_sensitivity_s':high,'reserved_4core_wall_proxy_s':4*estimated if estimated else None,
                            'rate_only_total_attempts':15*nr,'rate_only_estimated_T_attempt_s':rateonly,
                            'rate_only_does_not_establish_distance_precision':True,'quality_R_null_reasons':nulls or None,
                            'finite_wall_upper_bound_s':None,'adopted':False,'decision':'HOLD',
                            'cost_note':'new pilot all-started completed attempt means; max sensitivity is not upper bound; gap/setup separate; no extra division by four',
                            'expected_T_only_within_reference_budgets':{str(hours):estimated<=hours*3600 if estimated else None for hours in (1,4,24)}})
    return table,sensitivities

def aggregate(root):
    begin=time.perf_counter();root=Path(root).resolve();m=load_registration(root);rows=[];telemetry=[];management=[]
    for run in m['runs']:
        directory=root/'runs'/run['run_id'];state=attempt_state(directory)
        if state=='FINISHED':
            row=read(directory/'RESULT.json')
            for k in ('run_id','method','case_id','seeds','branches'):
                if k=='branches':continue
                if row[k]!=run[k]:raise ValueError('RESULT_RUN_IDENTITY_MISMATCH:'+run['run_id'])
            if any(row[k]!=m[k] for k in ('experiment_id','config_hash','T_kind','physical_hash')):raise ValueError('OLD_OR_DIFFERENT_RESULT_REJECTED')
            case=next(c for c in m['cases'] if c['case_id']==run['case_id'])
            if row['input_hash']!=case['input']['input_hash'] or row['OD_hash']!=case['input']['OD_hash']:raise ValueError('RESULT_INPUT_MISMATCH')
        else:row={**run,'execution_state':'NOT_STARTED' if state=='NOT_STARTED' else 'UNFINISHED','adoptable':False,'D':None,'W':None,'T_program':None,'T_attempt':None,'branches':[],'input_state':'NOT_CHECKED','plan_state':'NO_PLAN'}
        row['attempt_collection_state']=state
        row['incomplete_elapsed_observation_s']=None
        row['incomplete_elapsed_reason']=None
        if state=='UNFINISHED':
            active=root/'ACTIVE.json'
            if active.exists():
                from pilot import boot
                observation=read(active)
                if observation['run_id']==run['run_id'] and observation['boot_id']==boot():
                    row['incomplete_elapsed_observation_s']=time.perf_counter()-observation['before_execute_perf_counter']
                    row['incomplete_elapsed_reason']='elapsed since wrapper start; NOT completed attempt cost, not T_program'
            if row['incomplete_elapsed_observation_s'] is None:row['incomplete_elapsed_reason']='NO_COMPARABLE_START_CLOCK_OBSERVED'
        row['provenance']=provenance(root,row,m) if state=='FINISHED' else {'reason':'NO_FINAL_RESULT'}
        target=m['analysis']['targets'][run['case_id']]
        row['inherited_target']=target
        row['inherited_target_met_end']=(row['D']<=target['D'] and row['W']<=target['W']) if row['adoptable'] else (False if state=='FINISHED' else None)
        row['strict_parent_first_target_arrival_s']=None;row['strict_parent_first_target_arrival_null_reason']='NOT_OBSERVED'
        if state=='FINISHED':
            telemetry.append({'run_id':run['run_id'],'method':run['method'],'scale':run['case_id'],
                'branches':[branch_telemetry(directory,b,run['method']) for b in row['branches']],
                'resources':resource_summary(directory),
                'timing':{k:row.get(k) for k in ('T_input','T_planning','T_final_processing','T_attempt','parent_cpu_s','CPU_s_branches','parent_RSS_highwater_KiB','sampled_tree_peak_RSS_KiB')},
                'provenance':row['provenance']})
        if (directory/'MANAGEMENT.json').exists():management.append(read(directory/'MANAGEMENT.json'))
        rows.append(row)
    groups={s:{} for s in SCALES};rates=[];conditions=[]
    for s in SCALES:
        aref=[r for r in rows if r['run_id'] in m['reference_groups'][s]]
        reason=None
        if len(aref)!=5 or not all(r['adoptable'] for r in aref):reason='ALL_REGISTERED_A_REFERENCE_MEMBERS_REQUIRED'
        elif len({(r['D'],r['W']) for r in aref})!=1:reason='A_QUALITY_INCONSISTENT'
        else:
            ref=(aref[0]['D'],aref[0]['W'],median(r['T_program'] for r in aref))
            if min(ref)<=0:reason='NONPOSITIVE_A_REFERENCE_DENOMINATOR'
        for r in [x for x in rows if x['case_id']==s]:
            r['J_reason']=reason or ('TARGET_PLAN_INVALID' if not r['adoptable'] else None)
            r['J']=mean(r[k]/v for k,v in zip(('D','W','T_program'),ref)) if r['J_reason'] is None else None
            r['J_reference_members']=m['reference_groups'][s];r['J_interval_conditional_on_reference']=True
        for method in METHODS:
            own=[r for r in rows if r['case_id']==s and r['method']==method];settled=[r for r in own if r['attempt_collection_state']=='FINISHED'];good=[r for r in settled if r['adoptable']]
            pending=sum(r['attempt_collection_state']=='UNFINISHED' for r in own);not_started=sum(r['attempt_collection_state']=='NOT_STARTED' for r in own)
            g={'scale':s,'method':method,'registered':len(own),'started':len(settled)+pending,'normally_ended':sum(r['execution_state']=='NORMAL' for r in settled),
                'adopted':len(good),'failed_settled':len(settled)-len(good),'unfinished':pending,'not_started':not_started,
                'successful_trial_IDs':[r['run_id'] for r in good],'failure_trial_IDs':[r['run_id'] for r in settled if not r['adoptable']],
                'metrics':{k:stats([r.get(k) for r in good]) for k in ('D','W','T_program','J')},
                'T_attempt_all':stats([r['T_attempt'] for r in settled]),'T_attempt_trial_IDs':[r['run_id'] for r in settled],
                'success_exact95':clopper(len(good),len(settled)) if not pending else None,
                'A_quality_deterministic_reference':method=='A','distinct_D_W':sorted({(r['D'],r['W']) for r in good}),
                'cost_limitation':'incomplete elapsed is not completed cost; prediction conditional on settled subset' if pending else None}
            groups[s][method]=g;conditions.append(g)
            for rate_kind,k in [('plan_acquisition',len(good)),('verified_feasible_plan',len(good)),('inherited_target_met',sum(r['inherited_target_met_end'] is True for r in settled))]:
                rates.append({'scale':s,'method':method,'kind':rate_kind,**rate_record(k,len(settled),pending),
                    'settled_trial_IDs':[r['run_id'] for r in settled],
                    'definition':'parent adopted double-validated plan; no-plan does not prove physical infeasibility' if rate_kind!='inherited_target_met' else 'adopted and both frozen legacy D/W thresholds met at end; no stopping deadline',
                    'first_parent_arrival_s':None,'arrival_reason':'strict first parent arrival not observed; never replaced by T'})
    comparisons=[]
    for s in SCALES:
        for left in ('C','D_CLASSICAL_REPLACEMENT'):
            for metric in ('D','W','T_program','J'):
                comparisons.append({'scale':s,'left':left,'right':'D','metric':metric,
                    'role':'inherited primary planning basis' if (s,left,metric)==('S2','C','D') else 'exploratory pointwise',
                    **independent_difference(groups[s][left]['metrics'][metric],groups[s]['D']['metrics'][metric]),
                    'successful_trial_IDs_left':groups[s][left]['successful_trial_IDs'],'successful_trial_IDs_right':groups[s]['D']['successful_trial_IDs']})
    candidates,sensitivity=candidate_table(groups)
    gaps=[]
    for a,b in zip(management,management[1:]):
        if a['boot_id']==b['boot_id']:gaps.append({'after':a['run_id'],'before':b['run_id'],'gap_outside_wrapper_s':b['before_management_write_perf_counter']-a['after_execute_perf_counter']})
    duration={'T_attempt_total_s':sum(r['T_attempt'] for r in rows if r['T_attempt'] is not None),
        'wrapper_outside_T_s':sum(x['wrapper_outside_T_s'] for x in management),'inter_wrapper_gaps':gaps,
        'gap_stats_s':stats([g['gap_outside_wrapper_s'] for g in gaps]),'registration':read(root/'REGISTRATION_TIMING.json'),
        'last_invocation':read(root/'LAST_INVOCATION.json') if (root/'LAST_INVOCATION.json').exists() else None,
        'nonoverlap':'T_attempt + wrapper_outside_T + inter_wrapper_gap are disjoint between first wrapper start and last wrapper end; setup/registration before first separately; no adding nested timings',
        'finite_wall_upper_bound_s':None}
    # Reference cost total includes all three scales, uniform marginal overhead sensitivity separate.
    marginal=duration['gap_stats_s']['mean']
    wrappermean=stats([x['wrapper_outside_T_s'] for x in management])['mean']
    for c in candidates:
        count=c['total_attempts_all_scales']
        c['estimated_gap_wrapper_extra_s']=(max(0,count-1)*marginal+count*wrappermean) if count and marginal is not None and wrappermean is not None else None
        c['estimated_with_gap_wrapper_s']=c['estimated_T_attempt_wall_s']+c['estimated_gap_wrapper_extra_s'] if c['estimated_T_attempt_wall_s'] is not None and c['estimated_gap_wrapper_extra_s'] is not None else None
        c['setup_registration_analysis_output_cost_note']='observed separately in COST_ACCOUNTING; not double-added to gaps; future fixed setup not guaranteed'
    summary={'experiment_id':ID,'r_pilot':5,'registered':75,'started':sum(g['started'] for g in conditions),'adopted':sum(g['adopted'] for g in conditions),
        'normally_ended':sum(g['normally_ended'] for g in conditions),'failed_settled':sum(g['failed_settled'] for g in conditions),
        'unfinished':sum(g['unfinished'] for g in conditions),'not_started':sum(g['not_started'] for g in conditions),
        'conditions':conditions,'comparisons':comparisons,'rows':rows,'main_decision':'HOLD','main_started':False,
        'statistical_limits':['r_pilot=5 finite initial measurement only','one nested frozen demand per scale; no between-demand inference','no paired inference by repeat/seed','zero sample SD is not true zero/equivalence','all CI pointwise unless candidate explicitly Bonferroni','A quality deterministic reference','conditional successful-plan distributions may differ between methods','shared-host temporal correlation unremoved']}
    for name,value in [('SUMMARY_DATA.json',summary),('RATES_AND_CENSORING.json',{'rates':rates,'rows':[{k:r.get(k) for k in ('run_id','attempt_collection_state','execution_state','inherited_target_met_end','strict_parent_first_target_arrival_s','strict_parent_first_target_arrival_null_reason')} for r in rows]}),
        ('VARIANCE_SENSITIVITY.json',{'adopted':False,'entries':sensitivity}),('TELEMETRY.json',telemetry),('COST_ACCOUNTING.json',duration),('MAIN_CANDIDATES.json',candidates)]:atomic(root/name,value)
    csvwrite(root/'PILOT_SUMMARY.csv',[{k:v for k,v in r.items() if k not in ('branches',)} for r in rows])
    csvwrite(root/'CONDITION_SUMMARY.csv',[{**{k:v for k,v in g.items() if k!='metrics'},**{metric+'_'+stat:val for metric,values in g['metrics'].items() for stat,val in values.items()}} for g in conditions])
    csvwrite(root/'MAIN_CANDIDATES.csv',candidates)
    atomic(root/'ANALYSIS_TIMING.json',{'wall_s':time.perf_counter()-begin,'outside_T':True,'includes':'telemetry/input metadata read, summaries, candidates and aggregate outputs','future_cost_upper_bound':False})
    print(json.dumps({k:summary[k] for k in ('registered','started','normally_ended','adopted','failed_settled','unfinished','not_started','main_decision')}),flush=True)
    return summary
