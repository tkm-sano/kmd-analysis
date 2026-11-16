"""Independent mathematical/circuit contracts; no frozen demand generation."""
from dataclasses import replace
import numpy as np
import pytest
from qiskit.quantum_info import Statevector
from kmd_toc.column_generation.models import Instance, Route, artificial_instance, enumerate_routes, route_cost, reduced_cost
from kmd_toc.column_generation.master import solve_lp, solve_integer
from kmd_toc.column_generation.aoa import PricingAOA, AOAConfig
from kmd_toc.column_generation.reduction import contract, build_domains, exact_domain_routes
from kmd_toc.column_generation.runner import run_column_generation


@pytest.fixture
def tiny():
    return Instance('tiny', np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]]), (0, 1, 1), 2)


@pytest.mark.parametrize('variant', ['cover', 'partition'])
def test_classical_cg_equals_full_lp(tiny, variant):
    result = run_column_generation(tiny, variant=variant)
    assert result['stop_reason'] == 'PRICING_CERTIFIED_NONNEGATIVE'
    assert result['integer']['objective'] == pytest.approx(4)
    assert result['final_lp']['objective'] == pytest.approx(solve_lp(tiny, enumerate_routes(tiny), variant)['objective'])
    assert all(b['lp']['objective'] <= a['lp']['objective'] + 1e-8
               for a, b in zip(result['trace'], result['trace'][1:]))


def test_cover_is_not_partition():
    d = np.full((6, 6), .1)
    d[0, :] = d[:, 0] = 1
    np.fill_diagonal(d, 0)
    instance = Instance('cover_counterexample', d, (0, 1, 1, 1, 1, 1), 5)
    routes = [Route((i,)) for i in instance.customers] + [Route((1, 2, 3)), Route((3, 4, 5))]
    assert solve_lp(instance, routes, 'cover')['objective'] == pytest.approx(4.4)
    assert solve_lp(instance, routes, 'partition')['objective'] == pytest.approx(6.2)


@pytest.mark.parametrize('fixed', [False, True])
@pytest.mark.parametrize('penalty', ['paper_literal', 'customer_unique'])
def test_formula_polynomial_ising_and_qiskit(tiny, fixed, penalty):
    model = PricingAOA(tiny, [1.5, 2.5], AOAConfig(slots=3, fixed_depot=fixed, penalty=penalty))
    constant, z, zz = model.ising
    for bits, sequence in zip(model.indices, model.sequences):
        direct = model.direct_energy(sequence)
        eigenvalue = constant + sum(v * (1 - 2 * ((int(bits) >> i) & 1)) for i, v in z.items())
        eigenvalue += sum(v * (1 - 2 * ((int(bits) >> i) & 1)) * (1 - 2 * ((int(bits) >> j) & 1)) for (i, j), v in zz.items())
        assert model.polynomial.value(bits) == pytest.approx(direct)
        assert eigenvalue == pytest.approx(direct)
    angles = [.17, .41, .23, .31]
    state = Statevector.from_instruction(model.circuit(angles))
    assert abs(np.vdot(model.tensor_state(angles), state.data[model.indices])) ** 2 == pytest.approx(1, abs=1e-10)
    assert np.sum(abs(state.data[model.indices]) ** 2) == pytest.approx(1)
    probability_bad_start = sum(abs(a) ** 2 for a, seq in zip(model.tensor_state(angles), model.sequences) if seq[0] != 0)
    assert probability_bad_start == 0 if fixed else probability_bad_start > .01


def test_literal_uniqueness_penalty_does_not_prevent_repeat(tiny):
    cfg = AOAConfig(slots=3)
    fixed = PricingAOA(tiny, [0, 0], cfg)
    literal = PricingAOA(tiny, [0, 0], replace(cfg, penalty='paper_literal'))
    assert fixed.direct_energy((0, 1, 1)) - literal.direct_energy((0, 1, 1)) == pytest.approx(2)
    assert fixed.decode((0, 1, 1))[1] == 'REPEATED_CUSTOMER'


def test_capacity_alim_bias():
    assert [h + h * h for h in [-2, -1, 0, 1]] == [2, 0, 0, 2]


def test_two_node_ring_has_two_displayed_edges():
    instance = Instance('one_customer', np.array([[0, 1], [1, 0]]), (0, 1), 1)
    model = PricingAOA(instance, [1], AOAConfig(slots=2, p=1))
    assert model.ring[0, 1] == 2
    state = model.tensor_state([0, .2])
    assert abs(state[1]) ** 2 == pytest.approx(np.sin(.4) ** 2)


def test_ising_on_entire_computational_basis(tiny):
    model = PricingAOA(tiny, [2, 3], AOAConfig(slots=3))
    constant, z, zz = model.ising
    for bits in range(1 << model.q):
        eigenvalue = constant + sum(v * (1 - 2 * ((bits >> i) & 1)) for i, v in z.items())
        eigenvalue += sum(v * (1 - 2 * ((bits >> i) & 1)) * (1 - 2 * ((bits >> j) & 1)) for (i, j), v in zz.items())
        assert eigenvalue == pytest.approx(model.polynomial.value(bits))


def test_internal_depot_split_preserves_free_fleet_reduced_cost(tiny):
    model = PricingAOA(tiny, [3, 4], AOAConfig(slots=5))
    routes, reason = model.decode((0, 1, 0, 2, 0))
    assert reason == 'VALID'
    assert routes == [Route((1,)), Route((2,))]
    assert sum(reduced_cost(tiny, r, [3, 4]) for r in routes) == pytest.approx(6 - 7)


def test_asymmetric_routes_are_not_reversed():
    d = np.array([[0, 1, 8], [3, 0, 2], [4, 7, 0]])
    instance = Instance('asymmetric', d, (0, 1, 1), 2)
    assert route_cost(instance, Route((1, 2))) == 7
    assert route_cost(instance, Route((2, 1))) == 18
    assert solve_integer(instance, enumerate_routes(instance))['objective'] == 7


def test_fragment_contraction_is_exact_on_restricted_routes():
    base = artificial_instance(6)
    instance = Instance('fragments', base.distance, (0, 1, 1, 1, 1, 1, 1), 4)
    dual = [1, 2, 3, 4, 5, 6]
    domain = contract(instance, dual, [(1, 2), (3, 4), (5, 6)], 'macros')
    routes = exact_domain_routes(instance, domain)
    assert len(routes) == 9
    for route in enumerate_routes(domain.pricing):
        assert reduced_cost(domain.pricing, route, domain.dual) == pytest.approx(reduced_cost(instance, domain.expand(route), dual))
    assert all(len(r.customers) in (2, 4) for r in routes)
    assert Route((1, 3)) not in routes


def test_domain_enumeration_is_subset_of_full():
    instance = artificial_instance(6)
    dual = solve_lp(instance, [Route((i,)) for i in instance.customers])['dual']
    all_routes = set(enumerate_routes(instance))
    for domain in build_domains(instance, dual):
        assert set(exact_domain_routes(instance, domain)) <= all_routes


def test_restricted_optimal_dual_can_miss_global_improvement():
    base = artificial_instance(6)
    instance = Instance('bad_groups', base.distance, (0, 1, 1, 1, 1, 1, 1), 2)
    domain = contract(instance, [0] * 6, [(1, 3), (2, 5), (4, 6)], 'bad_groups')
    restricted = exact_domain_routes(instance, domain)
    pool = [Route((i,)) for i in instance.customers] + restricted
    dual = solve_lp(instance, pool)['dual']
    assert min(reduced_cost(instance, r, dual) for r in restricted) >= -1e-7
    assert min(reduced_cost(instance, r, dual) for r in enumerate_routes(instance)) < -1e-7


def test_empty_or_invalid_input_rejected(tiny):
    with pytest.raises(ValueError):
        enumerate_routes(tiny, [1, 1])
    with pytest.raises(ValueError):
        contract(tiny, [1, 1], [(1,), (1,)], 'bad')
    with pytest.raises(ValueError):
        Instance('bad', np.array([[0, -1], [1, 0]]), (0, 1), 1)


def test_missed_aoa_column_is_not_a_certificate(tiny, monkeypatch):
    monkeypatch.setattr(PricingAOA, 'run', lambda self: {'routes': []})
    result = run_column_generation(tiny, pricing='aoa')
    assert result['stop_reason'] == 'AOA_NO_IMPROVING_COLUMN'
    assert result['trace'][0]['oracle_improvement_exists']
    assert not result['full_oracle_nonnegative_at_final_dual']
    assert result['oracle_columns_injected'] is False


def test_full_lp_pricing_closure_does_not_certify_global_integer_optimum():
    base = artificial_instance(6)
    instance = Instance('integer_pool_gap', base.distance, (0, 1, 1, 1, 1, 1, 1), 4)
    result = run_column_generation(instance, pricing='classical')
    assert result['full_oracle_nonnegative_at_final_dual']
    assert result['integer_gap_to_full_enumeration'] > .5
