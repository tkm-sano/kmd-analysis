"""Read-only numerical audit of saved records; never invokes a scientific runner."""
from pathlib import Path
from collections import defaultdict, Counter
from fractions import Fraction
import csv, json, math, hashlib, statistics, re

RUN=Path(__file__).resolve().parents[1]
ROOT=Path('/home/takuma/kmd-analysis')
DATA=ROOT/'review_outputs/no_sumo_full_analysis_20261102/run01'
E=RUN/'evidence'
checks=[]

def rows(name):
    with (DATA/name).open() as f:return list(csv.DictReader(f))

def check(key,actual,expected,source,tol=None):
    ok=(abs(float(actual)-float(expected))<=tol) if tol is not None else actual==expected
    checks.append(dict(id=key,actual=actual,expected=expected,tolerance=tol,status='PASS' if ok else 'FAIL',source=source))
    if not ok:raise AssertionError(checks[-1])

def write_csv(name,rs):
    with (E/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)

def main():
    b=rows('B_PLAN_REFERENCES_36800.csv')
    initial={r['problem_id']:r for r in rows('B_CLASSICAL_INITIAL_BASELINES.csv')}
    check('B_reference_rows',len(b),36800,'B_PLAN_REFERENCES_36800.csv')
    check('B_physical_inputs',len(initial),460,'B_CLASSICAL_INITIAL_BASELINES.csv')
    ids=set(r['problem_id'] for r in b)
    check('B_inputs_match_initial',ids==set(initial),True,'B_PLAN_REFERENCES_36800.csv + B_CLASSICAL_INITIAL_BASELINES.csv')
    check('B_all_best_plans_acquired',sum(r['plan_acquired']=='True' for r in b),36800,'B_PLAN_REFERENCES_36800.csv')
    check('B_all_best_plans_feasible',sum(r['feasible']=='True' for r in b),36800,'B_PLAN_REFERENCES_36800.csv; best of8192 shots, not individual-shot success')
    by_input=defaultdict(list)
    mismatches=0
    exact_ids=set();missing_ids=set()
    for r in b:
        by_input[(r['config_id'],r['problem_id'])].append(r)
        j=Fraction(r['objective_fraction']);j0=Fraction(r['classical_initial_fraction'])
        if abs(float(j-j0)-float(r['delta_objective_vs_initial_s']))>1e-7:mismatches+=1
        route=json.loads(r['route_indices'])
        n=int(r['n_customers'])
        if route[0]!=0 or route[-1]!=0 or sorted(route[1:-1])!=list(range(1,n+1)):mismatches+=1
        if r['exact_reference_available']=='True':
            exact_ids.add(r['problem_id'])
            gap=100*float((j-Fraction(r['exact_optimum_fraction']))/Fraction(r['exact_optimum_fraction']))
            if abs(gap-float(r['global_gap_percent']))>1e-7:mismatches+=1
        else:
            missing_ids.add(r['problem_id'])
            if r['global_gap_percent']!='':mismatches+=1
    check('B_arithmetic_route_gap_mismatches',mismatches,0,'36800 saved references; Fraction objective differences, visit sets, conditional gap')
    check('B_exact_inputs',len(exact_ids),407,'B_PLAN_REFERENCES_36800.csv')
    check('B_missing_exact_inputs',len(missing_ids),53,'B_PLAN_REFERENCES_36800.csv')
    check('B_repetitions_per_input',set(len(v) for v in by_input.values())=={10},True,'B_PLAN_REFERENCES_36800.csv')
    aggregates=[]
    for (cfg,pid),rs in sorted(by_input.items()):
        aggregates.append(dict(config_id=cfg,problem_id=pid,scale=rs[0]['scale'],n=int(rs[0]['n_customers']),
            mean_delta_s=statistics.fmean(float(r['delta_objective_vs_initial_s']) for r in rs),
            mean_gap_percent=statistics.fmean(float(r['global_gap_percent']) for r in rs) if rs[0]['exact_reference_available']=='True' else None,
            repeats=len(rs),all_route_equal_initial=all(json.loads(r['route_indices'])==json.loads(initial[pid]['initial_route']) for r in rs)))
    summary=[]
    for cfg in sorted(set(r['config_id'] for r in b)):
        rr=[r for r in aggregates if r['config_id']==cfg]
        raw=[r for r in b if r['config_id']==cfg]
        summary.append(dict(config_id=cfg,inputs=len(rr),references=len(raw),
            mean_delta_s=statistics.fmean(r['mean_delta_s'] for r in rr),
            mean_gap_percent=statistics.fmean(r['mean_gap_percent'] for r in rr if r['mean_gap_percent'] is not None),
            improving_inputs=sum(r['mean_delta_s']<0 for r in rr),
            equal_inputs=sum(r['mean_delta_s']==0 for r in rr),
            worse_inputs=sum(r['mean_delta_s']>0 for r in rr),
            all_route_equal_initial=all(r['all_route_equal_initial'] for r in rr),
            optimal_reference_matches=sum(r['optimal_match']=='True' for r in raw),
            exact_reference_rows=sum(r['exact_reference_available']=='True' for r in raw)))
    write_csv('B_BY_CONFIGURATION.csv',summary)
    check('B_configs_equal_initial',sum(r['all_route_equal_initial'] for r in summary),6,'B_BY_CONFIGURATION.csv; objective and serialized route checked')
    scaled=[]
    stored=rows('B_SUMMARY_BY_SCALE_AND_METHOD.csv')
    summary_mismatch=0
    for scale,n in zip(['R0','R1','R2','R3','R4','R5'],[3,4,5,25,100,125]):
        for cfg in sorted(set(r['config_id'] for r in b)):
            rr=[r for r in aggregates if r['config_id']==cfg and r['scale']==scale]
            val=statistics.fmean(r['mean_delta_s'] for r in rr)
            st=next(r for r in stored if r['config_id']==cfg and r['scale']==scale)
            if abs(val-float(st['mean_delta_objective_s']))>1e-7:summary_mismatch+=1
        rr=[r for r in aggregates if r['scale']==scale and r['config_id'].startswith('GROVER_')]
        av=[statistics.fmean(r['mean_delta_s'] for r in rr if r['config_id']==cfg) for cfg in ['GROVER_P2','GROVER_P3']]
        scaled.append(dict(scale=scale,delivery_stops=n,physical_inputs=len(rr)//2,delta_min_s=min(av),delta_max_s=max(av),
                           description='mean over 10 measurements within input, then equal-weight mean over inputs; range across p2/p3'))
    check('B_scale_summary_mismatches',summary_mismatch,0,'48 configuration/scale means compared to saved summary')
    for cfg in ['GROVER_P2','GROVER_P3']:
        check('B_improving_inputs_'+cfg,next(r['improving_inputs'] for r in summary if r['config_id']==cfg),7,'B_BY_CONFIGURATION.csv')
    write_csv('B_BY_SCALE.csv',scaled)
    mir=[r for r in b if r['family']=='mirror_family']
    check('B_mirror_orbit_equals_initial',sum(float(r['classical_orbit_delta_s'])==0 for r in mir),23000,'B_PLAN_REFERENCES_36800.csv; matching support exact DP')
    check('B_mirror_unique_fits',len(set(r['fit_id'] for r in mir)),2300,'B_PLAN_REFERENCES_36800.csv')
    ag=rows('B_ACTIVE_GRID_SELECTION.csv')
    check('B_active_t_zero',sum(float(r['selected_t'])==0 for r in ag),460,'B_ACTIVE_GRID_SELECTION.csv; grid only, not continuous optimum')
    fits=rows('B_RESOURCES_PER_FIT.csv')
    check('B_unique_fits',len(fits),3680,'B_RESOURCES_PER_FIT.csv')
    hardware={k:sum(bool(r[k]) for r in fits) for k in ['hardware_qubits','compiled_depth','compiled_gate_count']}
    for k,v in hardware.items():check('B_'+k+'_saved_count',v,0,'B_RESOURCES_PER_FIT.csv')
    resources=rows('B_RESOURCE_SCOPE_SUMMARY.csv')
    time_example=[]
    for scope in ['FIT','FINAL_VALIDATION']:
        r=next(r for r in resources if r['config_id']=='GROVER_P3' and r['scale']=='R3' and r['resource_scope']==scope and r['resource_field']=='wall_seconds')
        time_example.append(dict(config_id='GROVER_P3',delivery_stops=25,scope=scope,mean_seconds=float(r['mean_value']),unique_fits=int(r['unique_fits']),meaning='CPU工程別壁時計時間; 量子実機時間・総求解時間ではない'))
    write_csv('B_CPU_TIME_EXAMPLE.csv',time_example)
    # Independently check C arithmetic from saved energy totals, without reintegrating trajectories.
    c=rows('C_T08_ENERGY_FULL.csv');paired=rows('C_T08_PAIRED_DIFFERENCES.csv')
    csummary=[]
    for case in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
        selected=[r for r in c if r['dataset']=='CLASSICAL' and r['method']=='CLASSICAL' and r['rolling_case']==case]
        lp={r['physical_instance_id']:r for r in selected if r['scenario_id']=='COND_LP_REF'}
        ss={r['physical_instance_id']:r for r in selected if r['scenario_id']=='COND_S200_REF'}
        control={r['physical_instance_id']:r for r in selected if r['scenario_id']=='COND_LP_IDENTICAL_CONTROL'}
        check('C_'+case+'_trajectory_count',len(lp),460,'C_T08_ENERGY_FULL.csv')
        check('C_'+case+'_paired_ids',set(lp)==set(ss)==set(control),True,'C_T08_ENERGY_FULL.csv')
        check('C_'+case+'_same_trajectory_hash',all(lp[k]['trajectory_sha256']==ss[k]['trajectory_sha256']==control[k]['trajectory_sha256'] for k in lp),True,'C_T08_ENERGY_FULL.csv')
        check('C_'+case+'_control_zero',all(float(lp[k]['net_DC_Wh'])==float(control[k]['net_DC_Wh']) for k in lp),True,'C_T08_ENERGY_FULL.csv')
        bm=next(iter(lp.values()));sm=next(iter(ss.values()))
        ml,ms=float(bm['pack_mass_kg']),float(sm['pack_mass_kg'])
        vl,vs=float(bm['running_mass_kg']),float(sm['running_mass_kg'])
        el=math.fsum(float(r['net_DC_Wh']) for r in lp.values());es=math.fsum(float(r['net_DC_Wh']) for r in ss.values())
        rp=100*(ml-ms)/ml;rv=100*(vl-vs)/vl;re=100*(el-es)/el
        independent=[r for r in paired if r['dataset']=='CLASSICAL' and r['method']=='CLASSICAL' and r['scenario_id']=='COND_S200_REF' and r['rolling_case']==case]
        check('C_'+case+'_pair_arithmetic',math.fsum(float(r['saving_DC_Wh']) for r in independent),el-es,'C_T08_PAIRED_DIFFERENCES.csv versus C_T08_ENERGY_FULL.csv',1e-7)
        check('C_'+case+'_running_mass_definition',vl-ml,988.888888889+55,'CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json + methods draft',1e-7)
        csummary.append(dict(case=case,trajectories=460,LP_pack_kg=ml,S_pack_kg=ms,mass_difference_kg=ml-ms,
            LP_running_kg=vl,S_running_kg=vs,LP_DC_sum_Wh=el,S_DC_sum_Wh=es,DC_difference_Wh=el-es,
            battery_reduction_percent=rp,running_reduction_percent=rv,DC_reduction_percent=re,
            q_reference_LP_Ah_kg=121/.704,q_reference_S_Ah_kg=194/.99,
            ratio_battery_to_running=rv/rp,ratio_running_to_DC=re/rv,
            ratio_battery_to_DC=re/rp,ratio_q_to_DC=re/(100*((194/.99)-(121/.704))/(121/.704))))
    write_csv('C_MASS_DC_RECONCILIATION.csv',csummary)
    expected=[5.67,.478,.413]
    actual=[csummary[0]['battery_reduction_percent'],csummary[0]['running_reduction_percent'],csummary[0]['DC_reduction_percent']]
    for key,val,ex,digits in zip(['battery','running','DC'],actual,expected,[2,3,3]):
        check('C_poster_rounding_'+key,round(val,digits),ex,'C_MASS_DC_RECONCILIATION.csv')
    components=rows('C_T09_COMPONENTS_183.csv')
    check('C_component_rows',len(components),183,'C_T09_COMPONENTS_183.csv')
    check('C_all_complete_pack_missing',sum(not r['complete_pack_mass_kg'] for r in components),183,'C_T09_COMPONENTS_183.csv')
    check('C_component_hold_status',sum(r['status']=='HOLD_COMPLETE_PACK_MASS' for r in components),182,'C_T09_COMPONENTS_183.csv')
    check('C_component_incompatible_status',sum(r['status']=='FAIL_FULL_OPPOSING_FOOTPRINT' for r in components),1,'C_T09_COMPONENTS_183.csv')
    bounds=[]
    for cid in ['T09_ROW_031','T09_ROW_079']:
        r=next(r for r in components if r['condition_id']==cid)
        bounds.append(dict(condition_id=cid,policy=r['area_policy'],known_mass_difference_kg=float(r['known_LP_minus_S_mass_kg']),
                           condition='DeltaM=b-delta; delta=b gives zero; NOT a measured full-pack feasibility threshold'))
    write_csv('C_COMPONENT_BOUNDARIES.csv',bounds)
    bridge=rows('C_BRIDGE_MASS_DC_FULL.csv')
    check('C_bridge_rows',len(bridge),25760,'C_BRIDGE_MASS_DC_FULL.csv')
    check('C_bridge_mass_identity',sum(abs(float(r['net_mass_saving_probe_kg'])-(float(r['known_mass_boundary_kg'])-float(r['unknown_mass_difference_probe_kg'])))>1e-8 for r in bridge),0,'C_BRIDGE_MASS_DC_FULL.csv; DeltaM=b-delta')
    write_csv('NUMERICAL_CHECKS.csv',checks)
    audit=dict(status='PASS',scientific_runners_invoked=0,checks=len(checks),failed_checks=0,
        planning=dict(inputs=460,measurement_references=36800,unique_fits=3680,exact_inputs=407,missing_exact=53,
            backends=dict(Counter(r['simulation_backend'] for r in fits)),hardware_saved_counts=hardware,
            scale_results=scaled,configuration_results=summary,cpu_time_example=time_example),
        material=dict(main_trajectories=460,energy_full_rows=len(c),pair_rows=len(paired),mass_DC=csummary,
            component_rows=183,component_status_counts=dict(Counter(r['status'] for r in components)),all_complete_pack_values_missing=True,
            component_boundaries=bounds,bridge_rows=25760),
        interpretation=dict(transmission_ratios='Finite relative-change ratios under specified model inputs; not derivatives, empirical mediation coefficients, or quantum-effect sizes',
            hardware='No hardware-qubit/compiled-depth/gate records; ideal model layers are not compiled circuit depth',
            computation='CPU numerical evaluation of Grover-mixer QAOA cost-phase/rank-one mixing; not marked-item Grover search'))
    (E/'AUDIT_RESULTS.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    print(json.dumps({'checks':len(checks),'failures':0,'B_inputs':460,'B_references':36800,'C_rates':actual,'C_component_status':audit['material']['component_status_counts']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
