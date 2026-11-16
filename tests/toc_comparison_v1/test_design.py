from copy import deepcopy
import math
import pytest
from kmd_toc.comparison_v1.design import (precision_count,welch_halfwidth,rate_count,
    demand_components,demand_analysis,fixed_analysis,require_same_settings,setting_identity,
    optimal_allocation,profile_config,variance_upper,clopper)
from test_contract_and_evaluation import manifest,rows,failed
from kmd_toc.comparison_v1.contract import ROOT, fingerprint


def test_independent_precision_monotonic_and_t_corrected():
    small=precision_count(4,9,1)
    assert precision_count(8,18,1)>small
    assert precision_count(4,9,.5)>small
    assert welch_halfwidth(4,9,small,small)<=1
    assert welch_halfwidth(4,9,small-1,small-1)>1
    assert precision_count(4,9,1,.01)>small
    allocation=optimal_allocation(16,1,1,4,1)
    assert allocation[0]>allocation[1]
    assert welch_halfwidth(16,1,*allocation)<=1


def test_demand_unit_and_no_double_counting():
    data=[{'mean_D':d,'mean_C':0,'variance_D':4,'variance_C':4,'R_D':4,'R_C':4} for d in (1,3,5)]
    v=demand_components(data)
    assert v['observed_variance_of_demand_means']==4
    assert v['mean_within_sampling_variance']==2
    assert v['between_variance_moments']==2
    assert demand_analysis(data)['M']==3
    with pytest.raises(ValueError,match='MULTIPLE'):demand_components(data[:1])


def test_fixed_seed_labels_do_not_make_pairs_and_failure_survives():
    _,data=rows()
    data2=deepcopy(data)
    for r in data2:r.update(run_id=r['run_id']+'2',repeat_id=2,pair_id='same_label_does_not_pair')
    data2[2]['D']=110;data2[3]['D']=120
    failed(data[2],'OUTER_WALL_LIMIT')
    result=fixed_analysis(data+data2)[0]
    assert result['methods']['C']['valid_input_executed']==2
    assert result['methods']['C']['adopted']==1
    assert result['methods']['C']['failed_run_ids']==['C']
    contrast=next(x for x in result['comparisons'] if x['left']=='C' and x['metric']=='D')
    assert contrast['CI'] is None
    assert contrast['difference_right_minus_left']==0  # means of distinct successful groups
    assert contrast['analysis'].startswith('independent Welch')


def test_deadline_late_plan_is_not_in_success_values():
    _,data=rows();data[2]['T_program']=data[2]['budget_wall_s']+1
    result=fixed_analysis(data)[0]['methods']['C']
    assert result['adopted']==0 and result['failed_run_ids']==['C']
    assert result['metrics']['D']['mean'] is None


def test_variance_configuration_lock_prevents_reuse():
    m=manifest();m['BCD_config_hash']='one';m['cpu_profile']={}
    assert require_same_settings([m,deepcopy(m)])==setting_identity(m)
    n=deepcopy(m);n['BCD_config_hash']='two'
    with pytest.raises(ValueError,match='CONFIGURATION_MISMATCH'):require_same_settings([m,n])
    n=deepcopy(m);n['cases'][0]['budget_wall_s']+=1
    with pytest.raises(ValueError):require_same_settings([m,n])


def test_success_rates_do_not_assume_zero_failure_probability():
    assert rate_count(.05)>rate_count(.1)>rate_count(.15)>3
    assert clopper(3,3)[0]<.5
    assert clopper(3,3)[1]==1
    assert variance_upper(0,3) is None
    assert variance_upper(1,3)>1


def test_profiles_preserve_A_and_cpu_and_preexisting_configuration():
    retained=profile_config('retained');lean=profile_config('lean')
    assert retained['cpu_parallel']==lean['cpu_parallel']
    assert retained['A']==lean['A']
    assert retained['D']['final_shots']>lean['D']['final_shots']
    from kmd_toc.comparison_v1.contract import read,ROOT,BCD_CONFIG
    assert retained==read(ROOT/BCD_CONFIG)


def test_main_manifest_fixed_count_gate_and_pilot_stage_required():
    from kmd_toc.comparison_v1.design import validate_extension,RULES_PATH
    from kmd_toc.comparison_v1.contract import digest
    m=manifest();m['phase']='variance_pilot'
    m['design_extension']={'profile':'lean','rules_path':RULES_PATH,'rules_sha256':digest(ROOT/RULES_PATH),
        'tree_memory_limit_MiB':32768,'settings_lock':None,'dependency_prefix':'/opt/miniconda/envs/qgpu/lib/python3.12/site-packages'}
    m['BCD_config']=profile_config('lean')
    m['cases'][0]['budget_wall_s']=120
    m['cases'][0]['case_parameters']={'BCD_epsilon_W_min':None,'BCD_native_cap_s':60}
    with pytest.raises(ValueError,match='LOCK_REQUIRED'):validate_extension(m)
    m['design_extension']['settings_lock']=setting_identity(m);validate_extension(m)
    m['phase']='formal'
    with pytest.raises(ValueError,match='MAIN_DESIGN_LOCK_REQUIRED'):validate_extension(m)
    m['design_extension']['main_lock']={'h_D':5,'rate_h':.1,'budget_s':100000,
        'run_list_hash':fingerprint(m['runs']),'fixed_attempt_count':len(m['runs']),'stopping':'fixed_count'}
    validate_extension(m)
    m['runs'].pop()
    with pytest.raises(ValueError,match='FIXED_DESIGN_REQUIRED'):validate_extension(m)


def test_exact_macro_replacement_keeps_common_feasibility_and_zero_shots():
    from itertools import permutations
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.dwt.budget import Budget
    from kmd_toc.dwt.methods import generate
    from kmd_toc.common.validation import validate_plan
    problem=artificial_problem(12,4,1)
    budget=Budget(15,.08)
    plan=generate(problem,'D_CLASSICAL_REPLACEMENT',None,budget,
        {'solver_seed':11,'quantum_seed':None},profile_config('lean'))
    assert validate_plan(problem,plan).feasible
    stages=[v for k,v in budget.evidence.items() if k.startswith('D_CLASSICAL_')]
    assert stages
    for stage in stages:
        groups=stage['fragment_groups']
        expected={tuple(i for group in order for i in group) for order in permutations(groups)}
        assert set(map(tuple,stage['full_routes']))==expected
        assert stage['shots']==0
    assert plan.method_settings['classical_only_control']
    assert plan.method_settings['quantum_calls']==0
    assert plan.method_settings['new_quantum_routes_in_final']==0
