"""New extension contracts, independent comparison to existing verified master."""
from dataclasses import replace
import numpy as np
import pytest
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.generation import enumerate_days, seed_plan
from kmd_toc.vehicle_day.model import ObjectiveProfile
from kmd_toc.vehicle_day.master import solve_lp, solve_integer, reduced_cost
from kmd_toc.search_improvement.catalogue import build_catalogue, artificial_column_estimate, routes_pruned
from kmd_toc.search_improvement.master import CatalogueMaster
from kmd_toc.search_improvement.regions import expanded_regions, exact_routes, measure_routes
from kmd_toc.search_improvement.study import coverage, zero_face, incumbent_repair, run_search
from kmd_toc.column_generation.aoa import AOAConfig
from kmd_toc.column_generation.models import Route, route_cost
from kmd_toc.column_generation.reduction import contract, exact_domain_routes


@pytest.fixture(scope='module')
def master():
    p=small_problem(4,1)
    return CatalogueMaster(p,build_catalogue(p))


def test_new_catalogue_equal_old_full_domain(master):
    old=enumerate_days(master.problem)
    assert {c.identity for c in old}=={c.identity for c in master.columns}
    assert len(old)==artificial_column_estimate(4,2)
    assert len(routes_pruned(master.problem.base))==16


@pytest.mark.parametrize('profile',[ObjectiveProfile('D'),ObjectiveProfile('W'),ObjectiveProfile('D',2),ObjectiveProfile('W',1.8)])
def test_sparse_lp_ip_duals_equal_verified_dense(master,profile):
    ids=list(range(len(master.columns)))
    a=master.lp(ids,profile); b=solve_lp(master.problem,master.columns,profile)
    assert a['success']==b['success']
    assert a['objective']==pytest.approx(b['objective'])
    assert master.ip(ids,profile)['objective']==pytest.approx(solve_integer(master.problem,master.columns,profile)['objective'])
    assert np.allclose(master.rc(a['dual'],profile),[reduced_cost(master.problem,c,a['dual'],profile) for c in master.columns])


def test_phase_one_customer_artificial_and_dual(master):
    lp=master.lp([],ObjectiveProfile(),phase='I')
    assert lp['objective']==pytest.approx(4)
    assert min(master.rc(lp['dual'],ObjectiveProfile()))<0


@pytest.mark.parametrize('phase,profile',[('I',ObjectiveProfile()),('II',ObjectiveProfile('W'))])
def test_exact_scope_not_changed_by_zero_distance_proxy(master,phase,profile):
    pool=[master.index[c.column_id] for c in seed_plan(master.problem)]
    lp=master.lp(pool,profile,phase=phase)
    regions=expanded_regions(master.problem,lp['dual'],0)
    assert exact_routes(master.problem,lp['dual'],profile,regions)==set(master.route_index)


def test_same_domain_completion_and_null_denominator(master):
    pool=[master.index[c.column_id] for c in seed_plan(master.problem)]
    lp=master.lp(pool,ObjectiveProfile())
    domains=expanded_regions(master.problem,lp['dual'],0)
    exact=exact_routes(master.problem,lp['dual'],ObjectiveProfile(),domains)
    assert exact==set(master.route_index)
    data=coverage(master,pool,lp['dual'],ObjectiveProfile(),domains,exact)
    assert data['candidate_coverage']==1 and data['acquisition_rate']==1
    full=master.lp(list(range(len(master.columns))),ObjectiveProfile())
    zero=coverage(master,pool,full['dual'],ObjectiveProfile(),domains,set())
    assert zero['global_negative_count']==0
    assert zero['candidate_coverage'] is None and zero['acquisition_rate'] is None
    assert master.complete(set(),master.known(pool))==set()


def test_split_merge_boundary_macros_preserve_cost_load_dual(master):
    dual=(.2,.4,.6,.8)
    for groups in [((1,2),(3,4)),((1,),(2,),(3,4)),((1,3),(2,4)),((2,3),(4,1))]:
        d=contract(master.problem.base,dual,groups,'macro',slots=3)
        for local in routes_pruned(d.pricing):
            expanded=d.expand(local)
            assert route_cost(d.pricing,local)==pytest.approx(route_cost(master.problem.base,expanded))
            assert sum(d.pricing.demand[i] for i in local.customers)==sum(master.problem.base.demand[i] for i in expanded.customers)
            assert sum(d.dual[i-1] for i in local.customers)==pytest.approx(sum(dual[i-1] for i in expanded.customers))


def test_new_aoa_sampler_inside_exact_scope_and_unmodified_circuit(master):
    pool=[master.index[c.column_id] for c in seed_plan(master.problem)]
    lp=master.lp(pool,ObjectiveProfile())
    domain=[(1,2,3)]
    routes,log=measure_routes(master.problem,lp['dual'],ObjectiveProfile(),domain,
                            AOAConfig(slots=3,p=2,max_evaluations=20,restarts=1,train_shots=100,final_shots=256))
    assert routes<=exact_routes(master.problem,lp['dual'],ObjectiveProfile(),domain)
    assert log[0]['result']['qubits']==8
    assert log[0]['result']['qiskit_tensor_max_infidelity']<1e-8


def test_integer_extensions_valid_and_explicit_classical(master):
    pool=[master.index[c.column_id] for c in seed_plan(master.problem)]
    face=zero_face(master,pool,ObjectiveProfile())
    repair=incumbent_repair(master,pool,ObjectiveProfile())
    assert face['ip']['metrics']['valid'] and repair['ip']['metrics']['valid']
    assert repair['full_problem_when_two_vehicles']
    assert repair['ip']['objective']==pytest.approx(master.ip(list(range(len(master.columns))),ObjectiveProfile())['objective'])


def test_limits_raise_instead_of_truncation(master):
    with pytest.raises(ValueError,match='SAFETY_LIMIT'):
        build_catalogue(master.problem,max_columns=20)
    with pytest.raises(ValueError,match='DOMAIN_GUARD'):
        build_catalogue(replace(master.problem,vehicles=tuple(replace(master.problem.vehicles[0],vehicle_id=f'X{i}') for i in range(4))))
    pool=[master.index[c.column_id] for c in seed_plan(master.problem)]
    dual=master.lp(pool,ObjectiveProfile())['dual']
    with pytest.raises(ValueError,match='QUBIT_SAFETY_LIMIT'):
        measure_routes(master.problem,dual,ObjectiveProfile(),[(1,2,3)],AOAConfig(slots=3),max_qubits=7)


def test_cg_scope_certificate_is_not_global_certificate(master):
    result=run_search(master,ObjectiveProfile(),AOAConfig(),mode='same_scope_classical')
    assert result['stop']=='DEFINED_DOMAINS_EXHAUSTED_NO_NEW_NEGATIVE'
    assert result['ip']['metrics']['valid']
    assert result['final_global_min_rc_diagnostic']>=-1e-7
