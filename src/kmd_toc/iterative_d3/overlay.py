"""Narrow, versioned hooks in the pinned v3 coordinator.

Legacy files are immutable inputs. Unique source anchors fail closed if the
registered coordinator changes. Core checkpointing, physics and ranking are reused.
"""
from contextlib import contextmanager
from pathlib import Path

from kmd_toc.iterative_v3 import experiment, reallocation, search
from .operators import local_target, proposals, selected_quantum
from .rng_v2 import call_seeds


def build_function(module, name, edits):
    # Compile only the function being extended. Other globals resolve to the
    # unchanged coordinator module, including its instrumentation wrappers.
    import inspect
    source = inspect.getsource(getattr(module, name))
    for original, replacement in edits:
        if source.count(original) != 1:
            raise RuntimeError(f'INVALID_OVERLAY_ANCHOR: {name}: {original}')
        source = source.replace(original, replacement)
    namespace = {}
    exec(compile(source, f'<iterative_d3:{module.__name__}.{name}>', 'exec'), module.__dict__, namespace)
    return namespace[name]


def variant_run(replay_root=None):
    generate_families = build_function(reallocation, 'generate', [
        ('max_candidates=None):', "max_candidates=None, families=('inter_relocate','inter_swap','intra_transfer')):"),
        ("for family in ('inter_relocate','inter_swap','intra_transfer'):", 'for family in families:'),
    ])
    edits = [
        ("version='iterative-v3'", "version='iterative-d3-v2' if 'rng_v2' in settings else 'iterative-d3-v1'"),
        ("moves=generate(p,state,rng,per_family=settings['moves_per_family'],attempts_per_family=settings['neighbor_attempts_per_family'],max_candidates=remaining)",
         "moves,neighbor_audit=propose(generate_families,p,state,rng,settings,seed,iteration,remaining)"),
        ("input_plan_id=state.plan_id,moves=moves,rng_after=", "input_plan_id=state.plan_id,moves=moves,neighbor_audit=neighbor_audit,rng_after="),
        ("        local_targets=[]\n" + """        for offset in range(len(moves)):
            move=moves[(iteration+branch_id+offset)%len(moves)]
            assigned=decode_routes(move['routes'])
            case=build(p,assigned,settings['local_order_size'],seed+iteration*10007+offset*101,move['affected_slots'])
            if case is not None:local_targets.append((move,assigned,case))
            if len(local_targets)>=settings['local_calls_per_iteration']:break
        if moves and not local_targets:receipts.append(dict(status='NO_ELIGIBLE_FIXED_ORDER_BLOCK'))""",
         """        local_source,local_targets=choose_local_target(build,p,state,moves,settings,seed,branch_id,iteration)
        if not local_targets:receipts.append(dict(status='NO_ELIGIBLE_FIXED_ORDER_BLOCK',local_source=local_source))"""),
        ("assignment_before=assignment_hash(assigned),return_limit=return_limit)",
         """assignment_before=assignment_hash(assigned),return_limit=return_limit,
                state_hash=input_hash,local_source=local_source,parent_move=None if move is None else move['move_id'])"""),
        ("orders,receipt=quantum(case,settings['quantum'],local/'solver',return_limit)",
         """replay=replay_root/f'iteration_{iteration:04d}'/f'local_{j:03d}' if replay_root else None
                    q_settings=settings['quantum']
                    if 'rng_v2' in settings:q_settings=q_settings | revision_seeds(settings['rng_v2'],condition,iteration,q_settings['optimizer_max_evaluations'])
                    orders,receipt=select_quantum(quantum,case,q_settings,local/'solver',return_limit,
                                                   local_header=call_header,replay_dir=replay)"""),
        ("orders,receipt=classical(case,settings['classical'],return_limit);dump",
         """c_settings=settings['classical']
                        if 'rng_v2' in settings:c_settings=c_settings | revision_seeds(settings['rng_v2'],condition,iteration)
                        orders,receipt=classical(case,c_settings,return_limit)
                        if 'rng_seed' in c_settings:receipt['effective_seed']=c_settings['rng_seed']
                        dump"""),
        ("case_hash=case.fingerprint,global_candidate_status=value['status'])",
         """case_hash=case.fingerprint,global_candidate_status=value['status'],
                        parent_state=input_hash,local_source=local_source,parent_move=call_header['parent_move'],
                        selection_reason=item.get('selection_reason'),frequency=item.get('count'),
                        local_distance_m=item['local_distance_m'])"""),
        ("move_id=move['move_id'],case_hash=case.fingerprint,receipt=receipt",
         "move_id=call_header['parent_move'],case_hash=case.fingerprint,local_source=local_source,receipt=receipt"),
        ("reason=repr(e),move_id=move['move_id'],classical_reallocation_preserved=True",
         "reason=repr(e),move_id=call_header['parent_move'],local_source=local_source,classical_reallocation_preserved=True"),
        ("receipts.append(dict(candidate_id=cid,**value));return value",
         """if (value['status']=='FEASIBLE' and move is not None and 'transfer' in move
                    and cid.startswith('reallocation_') and value['metrics']['D_exact']!=metrics(p,state,store.ref)['D_exact']):
                raise RuntimeError('WHOLE_TRANSFER_DISTANCE_CHANGED')
            receipts.append(dict(candidate_id=cid,parent_state=input_hash,
                                 parent_move=None if move is None else move['move_id'],**value))
            return value"""),
        ("        admissible=[]\n        for item in pool:",
         """        admissible=[]
        decisions=[]
        for item in pool:"""),
        ("            if not blocked or aspiration or item['origin']=='current':admissible.append(item)",
         """            eligible=not blocked or aspiration or item['origin']=='current'
            if eligible:admissible.append(item)
            decisions.append(dict(candidate_id=item.get('candidate_id'),plan_hash=identity(item['plan']),
                                  tabu_blocked=blocked,aspiration=aspiration,eligible=eligible))"""),
        ("pool.append(dict(plan=plan,origin=origin,move=move))",
         "pool.append(dict(plan=plan,origin=origin,move=move,candidate_id=cid))"),
        ("moves=prep['moves'],candidate_receipts=receipts,fresh_completion_evaluations=fresh)",
         """moves=prep['moves'],candidate_receipts=receipts,fresh_completion_evaluations=fresh,
            neighbor_audit=prep['neighbor_audit'],local_input_source=local_source,adopted_candidate_id=chosen.get('candidate_id'),
            decisions=decisions)"""),
    ]
    function = build_function(search, '_run', edits)
    # Keep dynamic lookup of the legacy phase wrappers installed by telemetry.
    globals_ = search.__dict__
    globals_.update(generate_families=generate_families, propose=proposals, choose_local_target=local_target,
                    select_quantum=selected_quantum, revision_seeds=call_seeds, replay_root=Path(replay_root) if replay_root else None)
    return function


@contextmanager
def variant_worker(replay_root=None):
    original = search._run
    search._run = variant_run(replay_root)
    try:
        yield
    finally:
        search._run = original
        for key in ('generate_families','propose','choose_local_target','select_quantum','revision_seeds','replay_root'):
            search.__dict__.pop(key, None)


def pilot_trial():
    return build_function(experiment, 'run_trial', [
        ("for condition in ('D_classical','D_quantum'):", "for condition in c['pilot_methods']:"),
        ("for k in ('D_classical','D_quantum'))", "for k in c['pilot_methods'])"),
        ("code_hashes=manifest['code_hashes'])\n            if path.exists():",
         """code_hashes=manifest['code_hashes'],
                replay_root=str(Path(c['D0_archive'])/case['scale']/condition/f'branch_{b}/work'))
            if path.exists():"""),
    ])
