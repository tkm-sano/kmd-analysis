"""Method-independent cargo-wait ledger, in integer JST seconds.

Events end at handling START. Handling/service durations never enter W.
Missing observations produce null totals, never implicit zero observations.
"""
from collections import defaultdict
from dataclasses import asdict, dataclass
import math

from kmd_toc.common.config import ROOT, fingerprint, read_json

VERSION = 'ota-toc-cargo-wait-20261119-v2'
MODEL_PATH = ROOT / 'configs/toc_delivery/cargo_wait_model_20261119_v2.json'


@dataclass(frozen=True)
class Exclusion:
    start_s: int
    end_s: int
    reason: str  # break, carrier_delay, weather, other_non_shipper


@dataclass(frozen=True)
class Event:
    event_id: str
    vehicle_id: str
    trip_no: int
    side: str  # loading, unloading, other
    location_id: str
    arrival_s: int | None
    handling_start_s: int | None
    reason: str | None  # shipper, consignee, facility; carrier/weather are excluded
    exclusions: tuple[Exclusion, ...] | None
    provenance: str
    data_kind: str  # observed, assumed, synthetic
    instruction_known: bool
    instructed_s: int | None = None  # earliest instructed arrival, NOT a new VRP window
    registration_s: int | None = None


def load_model(path=MODEL_PATH):
    model = read_json(path)
    return validate_model(model)


def validate_model(model):
    if (model.get('version') != VERSION or
            model.get('destination_wait') not in ('immediate_handover_assumption', 'event_records') or
            model.get('loading_wait') not in ('ready_is_arrival_facility_queue_assumption', 'event_records') or
            model.get('other_wait') not in ('none_assumption', 'event_records') or
            model.get('operation') != 'active_vehicle_day_same_driver' or
            model.get('customer_time_windows') is not False):
        raise ValueError('UNSUPPORTED_WAIT_MODEL')
    if (set(model) != {'version', 'destination_wait', 'loading_wait', 'other_wait', 'operation',
                      'customer_time_windows', 'assumptions'} or
            not isinstance(model['assumptions'], list) or not model['assumptions'] or
            any(not isinstance(a, str) or not a for a in model['assumptions'])):
        raise ValueError('WAIT_MODEL_ASSUMPTIONS_REQUIRED')
    return model


def second(x):
    return type(x) is int and x >= 0


def event_wait(e):
    """MLIT method: max(arrival/registration, instructed arrival) to handling.

    Exclusion intervals are clipped and unioned, so overlapping breaks cannot
    be subtracted twice. Unknown instruction/exclusion status is missing data.
    """
    if (not e.event_id or not e.vehicle_id or type(e.trip_no) is not int or e.trip_no < 1 or
            e.side not in ('loading', 'unloading', 'other') or not e.location_id or
            not e.provenance or e.data_kind not in ('observed', 'assumed', 'synthetic') or
            type(e.instruction_known) is not bool):
        raise ValueError('EVENT_METADATA')
    missing = [k for k in ('arrival_s', 'handling_start_s', 'reason', 'exclusions')
               if getattr(e, k) is None]
    if not e.instruction_known:
        missing.append('instruction_status')
    if missing:
        return {'event_id': e.event_id, 'wait_s': None, 'missing': missing}
    if not second(e.arrival_s) or not second(e.handling_start_s) or e.handling_start_s < e.arrival_s:
        raise ValueError('EVENT_TIME_ORDER')
    if e.instructed_s is not None and not second(e.instructed_s):
        raise ValueError('INSTRUCTED_TIME')
    basis = e.arrival_s
    if e.registration_s is not None:
        if not second(e.registration_s) or not e.arrival_s <= e.registration_s <= e.handling_start_s:
            raise ValueError('REGISTRATION_TIME')
        basis = e.registration_s
    if e.instructed_s is not None:
        basis = max(basis, e.instructed_s)
    basis = min(basis, e.handling_start_s)
    if e.reason not in ('shipper', 'consignee', 'facility', 'carrier', 'weather', 'non_cargo'):
        raise ValueError('UNKNOWN_WAIT_REASON')
    intervals = []
    for x in e.exclusions:
        if (not second(x.start_s) or not second(x.end_s) or x.end_s < x.start_s or
                x.reason not in ('break', 'carrier_delay', 'weather', 'other_non_shipper')):
            raise ValueError('EXCLUSION_TIME_OR_REASON')
        a, b = max(basis, x.start_s), min(e.handling_start_s, x.end_s)
        if a < b:
            intervals.append((a, b))
    excluded, end = 0, basis
    for a, b in sorted(intervals):
        excluded += max(0, b - max(end, a))
        end = max(end, b)
    raw = e.handling_start_s - basis
    wait = raw - excluded if e.reason in ('shipper', 'consignee', 'facility') else 0
    return {'event_id': e.event_id, 'basis_s': basis, 'gross_s': raw,
            'excluded_s': raw - wait, 'wait_s': wait, 'missing': []}


def evaluate(problem, plan, *, model=None, events=(), other_coverage=(), planning_time_s=None):
    """Single gateway for B/C/D, with physical reconstruction and coverage audit.

    Supplied records replace automatic events only in event_records mode.
    other_coverage lists vehicle IDs with a complete inventory of other waits,
    including an explicitly empty inventory. It is never inferred from absence.
    """
    from .physical import validate_plan
    model = load_model() if model is None else validate_model(model)
    if plan.method_id not in ('B', 'C', 'D'):
        raise ValueError('A_IS_EXTERNAL_REFERENCE_NOT_A_PLAN')
    if planning_time_s is not None and (type(planning_time_s) not in (int, float) or
            not math.isfinite(planning_time_s) or planning_time_s < 0):
        raise ValueError('PLANNING_TIME')
    physical = validate_plan(problem, plan)
    if not physical.feasible:
        raise ValueError('PHYSICAL_REJECTION:' + str(physical.violations))
    supplied = {}
    for e in events:
        if e.event_id in supplied:
            raise ValueError('DUPLICATE_EVENT')
        supplied[e.event_id] = e
    ledger, operations = [], defaultdict(list)
    for t in sorted(plan.trips, key=lambda t: (t.vehicle_id, t.trip_no)):
        operations[t.vehicle_id].append(t)
        specs = [('loading', problem.depot.depot_id, t.ready_s, t.load_start_s)]
        specs += [('unloading', v.stop_id, v.arrival_s, v.service_start_s) for v in t.visits]
        for side, location, arrival, start in specs:
            identifier = f'{t.vehicle_id}/{t.trip_no}/{side}/{location}'
            mode = model['loading_wait' if side == 'loading' else 'destination_wait']
            if mode == 'event_records':
                e = supplied.pop(identifier, None)
                if e is None:
                    e = Event(identifier, t.vehicle_id, t.trip_no, side, location,
                              arrival, start, None, None, 'required observation missing', 'observed', False)
            else:
                if side == 'unloading' and start != arrival:
                    raise ValueError('IMMEDIATE_HANDOVER_ASSUMPTION_VIOLATED')
                e = Event(identifier, t.vehicle_id, t.trip_no, side, location, arrival, start,
                          'facility' if side == 'loading' else 'consignee', (), mode, 'assumed', True)
            if (e.vehicle_id, e.trip_no, e.side, e.location_id) != (t.vehicle_id, t.trip_no, side, location):
                raise ValueError('EVENT_PLAN_IDENTITY')
            # Missing values stay missing; known timestamps must match the plan.
            if ((e.arrival_s is not None and e.arrival_s != arrival) or
                    (e.handling_start_s is not None and e.handling_start_s != start)):
                raise ValueError('EVENT_PLAN_TIME_MISMATCH_OR_WORK_DOUBLE_COUNT')
            ledger.append({'event': asdict(e), **event_wait(e)})
    if model['other_wait'] == 'none_assumption' and other_coverage:
        raise ValueError('OTHER_COVERAGE_WITH_NONE_ASSUMPTION')
    if set(other_coverage) - operations.keys():
        raise ValueError('UNKNOWN_OTHER_COVERAGE_OPERATION')
    for identifier, e in supplied.items():
        if (model['other_wait'] != 'event_records' or e.side != 'other' or
                e.vehicle_id not in operations or e.trip_no not in [t.trip_no for t in operations[e.vehicle_id]]):
            raise ValueError('UNEXPECTED_OR_ASSUMPTION_CONFLICT_EVENT:' + identifier)
        # Other events can only occupy an existing non-working gap. Additional
        # driving/service/unscheduled delays require a new physical model.
        t = next(t for t in operations[e.vehicle_id] if t.trip_no == e.trip_no)
        gaps = [(t.ready_s, t.load_start_s)] + [(v.arrival_s, v.service_start_s) for v in t.visits]
        if e.arrival_s is not None and e.handling_start_s is not None:
            if not any(a <= e.arrival_s <= e.handling_start_s <= b for a, b in gaps):
                raise ValueError('OTHER_EVENT_OVERLAPS_WORK_OR_DRIVING')
        ledger.append({'event': asdict(e), **event_wait(e)})
    # All event waiting intervals must be disjoint for the same operation.
    for vid in operations:
        intervals = sorted((r['event']['arrival_s'], r['event']['handling_start_s']) for r in ledger
                           if r['event']['vehicle_id'] == vid and r['event']['arrival_s'] is not None
                           and r['event']['handling_start_s'] is not None
                           and r['event']['arrival_s'] < r['event']['handling_start_s'])
        if any(a2 < b1 for (a1, b1), (a2, b2) in zip(intervals, intervals[1:])):
            raise ValueError('OVERLAPPING_WAIT_EVENTS_DOUBLE_COUNT')
    per_operation = []
    for vid, trips in sorted(operations.items()):
        rows = [r for r in ledger if r['event']['vehicle_id'] == vid]
        missing = [r['event_id'] for r in rows if r['wait_s'] is None]
        if model['other_wait'] == 'event_records' and vid not in other_coverage:
            missing.append('other_wait_inventory')
        parts = {side: sum(r['wait_s'] for r in rows if r['event']['side'] == side and r['wait_s'] is not None)
                 for side in ('loading', 'unloading', 'other')}
        per_operation.append({'operation_id': vid, 'trip_count': len(trips), 'missing': missing,
                              'known_wait_s': sum(parts.values()),
                              'W_s': None if missing else sum(parts.values()), 'known_parts_s': parts})
    complete = [r for r in per_operation if r['W_s'] is not None]
    n, missing_n = len(per_operation), len(per_operation) - len(complete)
    total = sum(r['W_s'] for r in complete) / 60 if not missing_n else None
    parts = {side: sum(r['known_parts_s'][side] for r in per_operation) / 60
             for side in ('loading', 'unloading', 'other')}
    return {'evaluation_version': VERSION, 'model': model, 'model_hash': fingerprint(model),
            'problem_hash': problem.fingerprint, 'od_hash': problem.od.fingerprint,
            'method': plan.method_id, 'D_km': physical.D_km,
            'W_total_min': total, 'W_mean_min_per_operation': total / n if total is not None and n else None,
            'operation_count': n, 'complete_operation_count': len(complete), 'missing_operation_count': missing_n,
            'unused_vehicle_count': len(problem.vehicles) - n,
            'known_partial_W_min': sum(r['known_wait_s'] for r in per_operation) / 60,
            'loading_W_min': parts['loading'] if not missing_n else None,
            'unloading_W_min': parts['unloading'] if not missing_n else None,
            'other_W_min': parts['other'] if not missing_n else None,
            'known_partial_parts_min': parts,
            'wait_incidence_pct': 100 * sum(r['W_s'] > 0 for r in complete) / n if n and not missing_n else None,
            'T_program_s': planning_time_s, 'operations': per_operation, 'events': ledger,
            'physical': physical.as_dict(),
            'calculation_status': 'HOLD_MISSING_DATA' if missing_n else 'CONDITIONAL_GO_ASSUMPTIONS'}
