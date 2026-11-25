"""Versioned D1–D3 operators on fixed-order and whole-vehicle route proposals."""
from collections import Counter
from .rng_v2 import event
from pathlib import Path
import random
import time

from kmd_toc.iterative_v3.io import (
    assignment_hash, decode_routes, digest_payload, dump, encode_routes,
    memberships, read, routes, sha,
)
from kmd_toc.iterative_v3 import quantum
from kmd_toc.iterative_v3.order import cost
from kmd_toc.iterative_v3.reallocation import valid_structure

FAMILIES = ('inter_relocate', 'inter_swap', 'intra_transfer')
TRANSFER_DOMAIN = 0x44335452


def select(problem, counts, limit):
    started = time.perf_counter()
    frequencies = Counter()
    invalid = 0
    for bits, count in counts.items():
        try:
            order = quantum.decode(bits, problem)
        except ValueError:
            invalid += count
            continue
        frequencies[order] += count
    distances = {order: cost(problem, order) for order in frequencies}
    top = sorted(frequencies, key=lambda order: (-frequencies[order], distances[order], order))
    frequent = top[:min(2, limit)]
    rest = sorted(set(top) - set(frequent), key=lambda order: (distances[order], -frequencies[order], order))
    shortest = rest[:min(2, limit - len(frequent))]
    candidates = [
        dict(order=list(order), count=frequencies[order], local_distance_m=distances[order],
             source='measured_order_only_QAOA', selection_reason=reason)
        for orders, reason in [(frequent, 'frequency'), (shortest, 'distance')]
        for order in orders
    ]
    return candidates, dict(measured_shots=sum(counts.values()), invalid_shots=invalid,
                            unique_valid_orders=len(frequencies), distance_evaluations=len(distances),
                            wall_s=time.perf_counter() - started, rule='frequency2_then_unselected_distance2')


def selected_quantum(kernel, problem, settings, directory, limit, *, local_header, replay_dir=None):
    directory = Path(directory)
    selector = directory.parent / 'SELECTOR.json'
    prior = None
    if replay_dir is not None:
        old = Path(replay_dir)
        paths = [old/'CASE.json', old.parent/'COMMIT.json', old/'solver/RESULT.json', old/'solver/CALL.json']
        if all(path.is_file() for path in paths):
            case, commit, result, call = map(read, paths)
            header = {key: local_header[key] for key in ('problem', 'case_hash', 'assignment_before', 'return_limit')}
            if (digest_payload(case) == digest_payload(header)
                    and commit['input_hash'] == local_header['state_hash']
                    and call['problem_hash'] == problem.fingerprint
                    and call['settings'] == settings and call['return_limit'] == limit
                    and call['encoding'] == problem.encoding and (call['p'], call['optimization_shots'], call['final_shots']) == (2, 1000, 10000)
                    and result['status'] == 'COMPLETE' and result['problem_hash'] == problem.fingerprint):
                prior = result
                provenance = dict(kind='replayed_D0_measurements', result=str(paths[2]), sha256=sha(paths[2]))
    if prior is None:
        _, prior = kernel(problem, settings, directory, limit)
        provenance = dict(kind='variant_QAOA_measurements', result=str(directory/'RESULT.json'), sha256=sha(directory/'RESULT.json'))
    binding = dict(source=provenance, case_hash=problem.fingerprint, limit=limit)
    if selector.exists():
        selected = read(selector)
        if selected['binding'] != binding:
            raise ValueError('SELECTOR_RESUME_BINDING_MISMATCH')
    else:
        candidates, tally = select(problem, prior['sample_counts'], limit)
        selected = dict(binding=binding, candidates=candidates, **tally)
        dump(selector, selected)
    receipt = {key: value for key, value in prior.items() if key not in ('candidates', 'sample_counts')}
    receipt.update(returned=len(selected['candidates']), selector=selected, measurement_provenance=provenance,
                   original_sample_bank_shots=prior['total_shots_actual'],
                   total_shots_actual=0 if provenance['kind']=='replayed_D0_measurements' else prior['total_shots_actual'],
                   fresh_optimizer_evaluations=0 if provenance['kind']=='replayed_D0_measurements' else prior['training_evaluations'])
    return selected['candidates'], receipt


def transfer_routes(problem, original, source, target):
    active = {v for v, _ in original}
    target_vehicle = next(v for v in problem.vehicles if v.vehicle_id == target)
    if source not in active or target in active:
        raise ValueError('TRANSFER_REQUIRES_ACTIVE_TO_UNUSED')
    proposed = {(target if v == source else v, trip): seq for (v, trip), seq in original.items()}
    if any(trip > target_vehicle.max_trips for (v, trip) in proposed if v == target):
        raise ValueError('TARGET_TRIP_LIMIT')
    valid_structure(problem, proposed)
    return proposed


def whole_transfer(problem, state, branch_seed, iteration, limit=64, *, stream_seed=None):
    original = routes(state)
    active = {v for v, _ in original}
    inactive = {v.vehicle_id for v in problem.vehicles} - active
    pairs = [(s, t) for s in sorted(active) for t in sorted(inactive)]
    if stream_seed is None:
        stream_seed = (TRANSFER_DOMAIN << 64) + (branch_seed << 16) + iteration
    random.Random(stream_seed).shuffle(pairs)
    rejects = Counter()
    audit = dict(stream_seed=stream_seed, available_pairs=len(pairs), attempts=0, rejected={})
    for source, target in pairs[:limit]:
        audit['attempts'] += 1
        try:
            proposed = transfer_routes(problem, original, source, target)
        except ValueError as error:
            rejects[str(error)] += 1
            continue
        before, after = memberships(original), memberships(proposed)
        changes = [dict(customer=s, before=list(before[s]), after=list(after[s]))
                   for s in sorted(before) if before[s] != after[s]]
        audit.update(rejected=dict(rejects), selected=[source, target])
        return dict(move_id='whole_vehicle_transfer_0', family='whole_vehicle_transfer',
                    routes=encode_routes(proposed), membership_diff=changes, transfer=[source, target],
                    affected_slots=[list(slot) for slot in sorted(proposed) if slot[0] == target],
                    inverse_tabu_attributes=[[x['customer'], *x['before']] for x in changes],
                    tabu_destination_attributes=[[x['customer'], *x['after']] for x in changes],
                    distance_screen=False), audit
    audit.update(rejected=dict(rejects), selected=None)
    return None, audit


def proposals(generate, p, state, rng, settings, seed, iteration, remaining):
    cap = min(3, remaining)
    options = dict(per_family=settings['moves_per_family'],
                   attempts_per_family=settings['neighbor_attempts_per_family'])
    if settings['variant'] != 'D3':
        return generate(p, state, rng, max_candidates=cap, **options), {'old_families': list(FAMILIES)}
    rng_context = settings.get('rng_v2')
    outer_seed = None
    transfer_seed = None
    if rng_context is not None:
        outer_seed = event(rng_context, 'D_shared', 'outer-neighbours', iteration)
        transfer_seed = event(rng_context, 'D_shared', 'whole-transfer', iteration)
        rng.seed(outer_seed)
    transfer, audit = whole_transfer(p, state, seed, iteration + 1, settings['transfer_attempts'], stream_seed=transfer_seed)
    if outer_seed is not None:
        audit['outer_seed'] = outer_seed
    index = iteration % 3
    families = [FAMILIES[index], FAMILIES[(index+1) % 3]]
    old_cap = min(2, cap - bool(transfer))
    old = generate(p, state, rng, families=tuple(families), max_candidates=old_cap, **options)
    if transfer is None and cap == 3:
        fallback = FAMILIES[(index+2) % 3]
        old.extend(generate(p, state, rng, families=[fallback], max_candidates=1, **options))
        families.append(fallback)
    audit.update(old_families=families, old_count=len(old))
    # Old-family candidates retain their traversal order. The transfer is the final slot.
    return old + ([transfer] if transfer is not None else []), audit


def local_target(build, p, state, moves, settings, seed, branch, iteration):
    size = settings['local_order_size']
    rng_context = settings.get('rng_v2')
    local_seed = (event(rng_context, 'D_shared', 'local-window', iteration)
                  if rng_context is not None else seed + iteration*10007)
    current = settings['variant'] in ('D2', 'D3') and iteration % 2 == 0
    origin = 'current' if current else 'reallocation'
    if current:
        assigned = routes(state)
        problem = build(p, assigned, size, local_seed)
        return origin, [(None, assigned, problem)] if problem is not None else []
    for offset in range(len(moves)):
        move = moves[(iteration+branch+offset) % len(moves)]
        assigned = decode_routes(move['routes'])
        problem = build(p, assigned, size, local_seed if rng_context is not None else local_seed + offset*101, move['affected_slots'])
        if problem is not None:
            return origin, [(move, assigned, problem)]
    return origin, []
