"""Explicit budget-aware adapters; the historical method entrypoints stay intact."""
import itertools
import math
import time
from dataclasses import asdict
import numpy as np
from kmd_toc.pipeline.classical import directed_cw, routing_pool
from kmd_toc.pipeline.completion import complete_routes, route_distance, assemble, greedy_assignment
from .budget import BudgetExceeded


def verify_candidate(p, candidate, epsilon, budget):
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.independent import recompute
    if candidate is None:
        return False
    started = budget.clock()
    check = validate_plan(p, candidate)
    raw = recompute(p, candidate)
    budget.observe_validation(budget.clock() - started)
    valid = bool(check.feasible and raw['feasible'] and (epsilon is None or check.W_min <= epsilon + 1e-9))
    if valid:
        key = lambda plan: (int(round(math.fsum(t.distance_m for t in plan.trips) * 10)), sum(t.waiting_s for t in plan.trips))
        if budget.incumbent is None or key(candidate) < key(budget.incumbent):
            budget.incumbent = candidate
    return valid


def complete(p, routes, method, epsilon, budget, seed, settings, cap=None, incumbent=None):
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.independent import recompute
    from dataclasses import replace
    before = time.perf_counter()
    def valid(candidate):
        return verify_candidate(p, candidate, epsilon, budget)
    if incumbent is None:
        try:
            incumbent = assemble(p, greedy_assignment(p, routes), method, {'completion': 'shared_greedy_incumbent'})
        except (ValueError, IndexError):
            incumbent = None
    if not valid(incumbent):
        incumbent = None
    cp_error = None
    candidate = None
    try:
        seconds = budget.left(None if cap is None else max(.001, cap - (time.perf_counter() - before)))
        candidate = complete_routes(p, routes, method, 'D', epsilon, seconds=seconds, seed=seed,
                                    settings=settings)
    except (ValueError, BudgetExceeded) as error:
        cp_error = {'type': type(error).__name__, 'message': str(error)}
    if candidate is not None and not valid(candidate):
        cp_error = {'type': 'IndependentRejection', 'message': 'CP candidate failed raw/common checks'}
        candidate = None
    key = lambda plan: (int(round(math.fsum(t.distance_m for t in plan.trips) * 10)), sum(t.waiting_s for t in plan.trips))
    if incumbent is not None and (candidate is None or key(incumbent) < key(candidate)):
        plan = incumbent
        selected = 'verified_incumbent'
    elif candidate is not None:
        plan = candidate
        selected = 'CP_candidate'
    else:
        raise ValueError('NO_VERIFIED_COMMON_COMPLETION:' + str(cp_error))
    info = {**settings, **({'CP_status': candidate.method_settings['CP_status']} if candidate else {}),
            'completion': 'shared_CP_SAT_with_independently_verified_incumbent',
            'pool_routes': len(routes), 'primary': 'D', 'other_limit': epsilon,
            'distance_objective_resolution_m': 0.1,
            'requested_completion_seconds': locals().get('seconds'),
            'completion_input_routes': [list(r) for r in routes], 'completion_selected_source': selected,
            'completion_CP_error': cp_error, 'completion_incumbent_available': incumbent is not None,
            'validation_reserve_s': budget.reserve, 'max_observed_validation_s': budget.max_validation_s,
            'completion_wall_s': time.perf_counter() - before,
            'CP_details': candidate.method_settings if candidate else None}
    budget.capture('completion_' + str(len(budget.events)), info)
    budget.mark('common_completion_end')
    return replace(plan, method_settings=info)


def generate(p, method, epsilon, budget, seeds, config):
    if method == 'A':
        from kmd_toc.baseline_a.construction import create_plan
        # Fixed before looking at the new B/C/D outcomes. No A1/A3 selection.
        plan = create_plan(p, config['A']['rule'], config['A']['offset_deg'], budget.mark)
        index = {j: i for i, j in enumerate(p.od.ids)}
        routes = [tuple(index[v.stop_id] for v in t.visits) for t in plan.trips]
        return complete(p, routes, 'A', epsilon, budget, seeds['solver_seed'],
                        {**plan.method_settings, 'single_A_rule': config['A'],
                         'rule_precompletion_plan': asdict(plan), 'T_human_comparable': False}, incumbent=plan)
    routes, info = directed_cw(p)
    budget.capture('directed_CW', {'routes': routes, 'metadata': info})
    budget.mark('directed_CW_end')
    info.update(generated_routes_before_completion=[list(r) for r in routes],
                solver_seed=seeds['solver_seed'], random_generator='NumPy SeedSequence/PCG64; OR ReSeed and CP-SAT integer seed')
    if method == 'B':
        return complete(p, routes, method, epsilon, budget, seeds['solver_seed'], info)
    if method == 'C':
        seed_plan = assemble(p, greedy_assignment(p, routes), 'C', {'completion': 'shared_CW_incumbent'})
        verified_seed = seed_plan if verify_candidate(p, seed_plan, epsilon, budget) else None
        # Original Routing adapter takes integral seconds. Floor is conservative.
        seconds = int(budget.left(config['allocation']['C_routing_fraction'] * budget.seconds))
        if seconds < 1:
            raise BudgetExceeded('INSUFFICIENT_ROUTING_BUDGET')
        routes, extra = routing_pool(p, routes, seconds=seconds, seed=seeds['solver_seed'])
        info.update(extra, requested_routing_seconds=seconds)
        budget.mark('OR_Routing_end')
        return complete(p, routes, method, epsilon, budget, seeds['solver_seed'], info, incumbent=verified_seed)
    if method not in ('D', 'D_CLASSICAL_CONTROL'):
        raise ValueError('UNKNOWN_METHOD')
    return hybrid(p, routes, info, method, epsilon, budget, seeds, config)


def hybrid(p, routes, info, method, epsilon, budget, seeds, config):
    from kmd_toc.common.adapters import to_vehicle_day
    from kmd_toc.column_generation.models import Route
    if method == 'D':
        from kmd_toc.column_generation.reduction import contract
        from kmd_toc.column_generation.aoa import AOAConfig, PricingAOA
    else:
        PricingAOA = object
    from kmd_toc.vehicle_day.generation import make_day
    from kmd_toc.pipeline.hybrid import EventDayMaster, column_generation
    a = config['allocation']
    seed_plan = complete(p, routes, 'D', epsilon, budget, seeds['solver_seed'], info,
                         cap=budget.seconds * a['D_seed_fraction'])
    budget.mark('D_seed_end')
    budget.capture('D_seed_plan', asdict(seed_plan))
    day = to_vehicle_day(p, delta_s=1)
    id_index = {j: i for i, j in enumerate(p.od.ids)}
    initial = []
    for v in day.vehicles:
        trips = sorted((t for t in seed_plan.trips if t.vehicle_id == v.vehicle_id), key=lambda t: t.trip_no)
        if trips:
            initial.append(make_day(day, v.vehicle_id,
                           tuple(Route(tuple(id_index[s.stop_id] for s in t.visits)) for t in trips),
                           tuple(t.load_start_s for t in trips)))

    class BoundedMaster(EventDayMaster):
        def __init__(self, problem, columns, end):
            super().__init__(problem, columns, native_threads=config.get('cpu_parallel', {}).get('native_threads_per_branch'))
            self.end = end
            self.calls = []

        def allowance(self):
            left = min(budget.left(), self.end - time.perf_counter())
            if left <= 0.005:
                raise BudgetExceeded('D_CLASSICAL_STAGE_BUDGET')
            return left

        def lp(self, indices, primary='D', limit=None):
            # Same primal/dual equations as the existing master, with a real
            # HiGHS deadline. Native inability to stop is caught by watchdog.
            from scipy.optimize import linprog
            seconds = self.allowance()
            aa, bb, rhs, cost = self.arrays(indices, primary, limit)
            native = {} if self.native_threads is None else {'threads': self.native_threads}
            r = linprog(cost, A_eq=aa, b_eq=np.ones(self.n), A_ub=bb, b_ub=rhs,
                        bounds=(0, None), method='highs', options={'time_limit': seconds, **native})
            self.calls.append({'type': 'LP', 'limit_s': seconds, 'status': int(r.status)})
            if not r.success:
                return {'success': False, 'reason': r.message}
            y = np.r_[r.eqlin.marginals, r.ineqlin.marginals[:len(self.rhs)]]
            other = self.w if primary == 'D' else self.d
            dual = r.ineqlin.marginals[-1] if limit is not None else 0.
            rc = (self.d if primary == 'D' else self.w) - np.asarray(self.a.T @ y).ravel() - dual * other
            if not np.allclose(rc[indices], r.lower.marginals, atol=1e-6):
                raise ValueError('D_BOUND_MASTER_DUAL_CHECK')
            return {'success': True, 'objective': float(r.fun), 'weights': r.x.tolist(),
                    'dual_customer': r.eqlin.marginals.tolist(), 'rc': rc.tolist(), 'epsilon_dual': float(dual)}

        def ip(self, indices, primary='D', limit=None, seconds=30):
            cap = min(seconds, self.allowance())
            out = super().ip(indices, primary, limit, cap)
            self.calls.append({'type': 'IP', 'limit_s': cap, 'status': out.get('message', out.get('success'))})
            return out

    def solve(pool, fraction):
        begin = time.perf_counter()
        window = budget.left(budget.seconds * fraction)
        end = begin + window
        construction_end = begin + window * config['D'].get('column_construction_fraction_of_stage', .35)
        # Preserve seed coverage before traversing the same fixed-calendar
        # catalogue as the original implementation. Stop construction in-loop.
        catalogue = {c.column_id: c for c in initial}
        by = {v.vehicle_id: [] for v in day.vehicles}
        for t in seed_plan.trips:
            by[t.vehicle_id].append(t.load_start_s)
        stop = False
        attempted = 0
        routes_in_pool = sorted(set(tuple(r) for r in pool))
        for vehicle in day.vehicles:
            starts = sorted(by[vehicle.vehicle_id]) or [vehicle.ready_s]
            if len(starts) == 1:
                from kmd_toc.pipeline.completion import route_duration
                starts = [starts[0], min(70200, starts[0] + 1800 + min((route_duration(p, r) for r in routes_in_pool), default=0))]
            choices = itertools.chain(((r,) for r in routes_in_pool),
                                      ((x, y) for x in routes_in_pool for y in routes_in_pool if not set(x).intersection(y)))
            for pattern in choices:
                if time.perf_counter() >= construction_end:
                    stop = True
                    break
                attempted += 1
                try:
                    c = make_day(day, vehicle.vehicle_id, tuple(Route(r) for r in pattern), tuple(starts[:len(pattern)]))
                    catalogue[c.column_id] = c
                except ValueError:
                    continue
            if stop:
                break
        columns = list(catalogue.values())
        master = BoundedMaster(day, columns, end)
        index = {c.column_id: i for i, c in enumerate(columns)}
        try:
            outcome = column_generation(master, [index[c.column_id] for c in initial], 'D', epsilon)
        except BudgetExceeded as error:
            outcome = {'stage_timeout': str(error), 'IP': {'success': False}, 'LP': {'success': False}}
        outcome['catalogue_construction'] = {'truncated_at_time_limit': stop, 'attempted_patterns': attempted,
                                              'validated_columns': len(columns), 'construction_window_s': window * config['D'].get('column_construction_fraction_of_stage', .35),
                                              'finite_pool_closure_not_full_catalogue_closure': True}
        return columns, outcome, master.calls

    columns, base, base_calls = solve(routes, a['D_base_fraction'])
    budget.capture('D_base_master', {'outcome': base, 'calls': base_calls, 'columns': len(columns)})
    budget.mark('D_base_master_end')
    duals = base['LP']['dual_customer'] if base.get('LP', {}).get('success') else [0.] * len(p.stops)
    quantum = []
    sampled = set()
    domain = set()
    stopped = False
    quantum_end = time.perf_counter() + budget.left(budget.seconds * a['D_quantum_fraction'])

    class TimedAOA(PricingAOA):
        def circuit(self, angles):
            started = time.perf_counter()
            qc = super().circuit(angles)
            self.circuit_seconds = time.perf_counter() - started
            return qc

    if method == 'D':
        for iteration in range(config['D']['pricing_rounds']):
            for ri, route in enumerate(routes):
                if time.perf_counter() >= quantum_end:
                    stopped = True
                    break
                budget.left()
                groups = tuple(tuple(int(i) for i in arr) for arr in np.array_split(
                    np.array(route, dtype=int), min(config['D']['macro_groups'], len(route))) if len(arr))
                sub = contract(day.base, duals, groups, f'dwt_{iteration}_{ri}', slots=len(groups) + 1)
                qseed = int(np.random.SeedSequence([seeds['quantum_seed'], iteration, ri]).generate_state(1)[0])
                cfg = AOAConfig(slots=len(groups) + 1,
                                **{k: config['D'][k] for k in ['p', 'max_evaluations', 'restarts', 'train_shots', 'final_shots']},
                                solver_seed=qseed)
                engine = TimedAOA(sub.pricing, sub.dual, cfg)
                result = engine.run()
                accepted = []
                for small in result['routes']:
                    if len(small) == len(groups) and set(small) == set(range(1, len(groups) + 1)):
                        full = sub.expand(Route(tuple(small))).customers
                        sampled.add(full)
                        accepted.append(full)
                exact = {tuple(i for k in order for i in groups[k]) for order in itertools.permutations(range(len(groups)))}
                domain.update(exact)
                quantum.append({'iteration': iteration, 'route_index': ri, 'quantum_seed': qseed,
                                'fragment_groups': groups, 'full_routes': accepted,
                                'circuit_build_s': engine.circuit_seconds,
                                'training_evaluations': sum(h['nfev'] for h in result['history']),
                                'training_total_shots': sum(h['nfev'] for h in result['history']) * cfg.train_shots,
                                'final_total_shots': result['measured_shots'],
                                'simulation_sampling_decode_s': result['qiskit_seconds'] - engine.circuit_seconds,
                                'sampling_only_s': None, 'sampling_scope': 'combined statevector evolution, finite-shot sampling and decoding',
                                'result': result})
                budget.capture(f'D_AOA_{iteration}_{ri}', quantum[-1])
            if stopped:
                break
    budget.mark('D_AOA_end' if method == 'D' else 'D_no_quantum_control')
    pool = sorted(set(routes) | sampled)
    cols, solved, calls = solve(pool, a['D_hybrid_fraction'])
    budget.capture('D_hybrid_master', {'outcome': solved, 'calls': calls, 'columns': len(cols)})
    budget.mark('D_hybrid_master_end')
    selected_routes = []
    day_incumbent = None
    if solved.get('IP', {}).get('success'):
        selected_routes = [t.customers for i in solved['IP']['selected'] for t in cols[i].trips]
        vehicle_index = {v.vehicle_id: i for i, v in enumerate(p.vehicles)}
        items = [{'v': vehicle_index[cols[i].vehicle_id], 'trip_no': t.trip_id,
                  'route': t.customers, 'start_s': t.load_start_s}
                 for i in solved['IP']['selected'] for t in cols[i].trips]
        proposed = assemble(p, items, 'D', {'candidate_source': 'bounded_day_IP'})
        if verify_candidate(p, proposed, epsilon, budget):
            day_incumbent = proposed
    meta = {**info, 'algorithm': 'bounded_Huang_AOA_event_day_master_then_shared_completion',
            'scope': 'finite CW macro/time catalogue; no global VRP certificate',
            'quantum_enabled': method == 'D', 'quantum': quantum,
            'quantum_stage_stopped_at_budget': stopped,
            'quantum_calls': len(quantum), 'quantum_new_routes': len(sampled - set(routes)),
            'quantum_obtained_full_routes': len(sampled), 'visited_macro_domain_size': len(domain),
            'macro_domain_coverage_note': 'only domains of circuits actually evaluated; not all possible VRP routes',
            'classical_seed_routes': [list(r) for r in routes], 'seed_plan': asdict(seed_plan),
            'base_columns': len(columns), 'hybrid_columns': len(cols),
            'base': base, 'hybrid': solved, 'base_solver_calls': base_calls, 'hybrid_solver_calls': calls,
            'master_selected_routes': [list(r) for r in selected_routes],
            'day_IP_incumbent_verified': day_incumbent is not None,
            'all_candidate_routes': [list(r) for r in pool], 'quantum_seed': seeds['quantum_seed'],
            'classical_only_control': method == 'D_CLASSICAL_CONTROL',
            'quantum_improvement_claim': False}
    best = seed_plan
    if day_incumbent is not None:
        key = lambda z: (int(round(math.fsum(t.distance_m for t in z.trips) * 10)), sum(t.waiting_s for t in z.trips))
        if key(day_incumbent) < key(best):
            best = day_incumbent
    final = complete(p, pool, 'D', epsilon, budget, seeds['solver_seed'], meta, incumbent=best)
    final_routes = {tuple(id_index[v.stop_id] for v in t.visits) for t in final.trips}
    from dataclasses import replace
    meta = {**final.method_settings, 'new_quantum_routes_in_final': len(final_routes & (sampled - set(routes))),
            'base_seed_D_km': sum(t.distance_m for t in seed_plan.trips) / 1000,
            'final_minus_seed_D_km': sum(t.distance_m for t in final.trips) / 1000 - sum(t.distance_m for t in seed_plan.trips) / 1000}
    # Control is a trial label; the common schema only allows A/B/C/D IDs.
    return replace(final, method_id='D' if method == 'D' else 'B',
                   execution_kind='quantum_circuit_simulator' if method == 'D' else 'classical',
                   method_settings=meta)
