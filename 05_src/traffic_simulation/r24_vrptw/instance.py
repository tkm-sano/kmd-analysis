"""Strict seconds-based input boundary. Standard library only; no solver imports.

Decimal lexical values are converted to exact rational numbers, not a time grid.
All cross-field checks are authoritative here; input.schema.json describes shape.
"""
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from types import MappingProxyType
import re


class InputError(ValueError):
    """Malformed input rather than a valid input with an infeasible route."""


def fields(value, required, optional=(), label='object'):
    if not isinstance(value, Mapping):
        raise InputError(f'{label}: expected object')
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise InputError(f'{label}: missing={sorted(missing)}, unknown={sorted(extra)}')


def identifier(value, label):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise InputError(f'{label}: expected nonempty canonical string ID')
    return value


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise InputError(f'{label}: expected finite decimal seconds/quantity')
    if isinstance(value, str) and not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', value):
        raise InputError(f'{label}: invalid decimal lexical form')
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InputError(f'{label}: invalid decimal') from None
    if not d.is_finite():
        raise InputError(f'{label}: nonfinite number')
    return Fraction(d)


def nonnegative(value, label):
    n = number(value, label)
    if n < 0:
        raise InputError(f'{label}: must be nonnegative')
    return n


def json_number(value):
    """Lossless JSON: integer when integral, otherwise a decimal string in seconds."""
    if value is None:
        return None
    if value.denominator == 1:
        return value.numerator
    with localcontext() as ctx:
        ctx.prec = len(str(abs(value.numerator))) + len(str(value.denominator)) + 5
        return format(Decimal(value.numerator) / Decimal(value.denominator), 'f')


def array(value, label, allow_empty=False):
    if not isinstance(value, list) or (not value and not allow_empty):
        raise InputError(f'{label}: expected {"possibly empty " if allow_empty else "nonempty "}array')


def validate_input(data):
    """Return immutable parsed values. Every call checks IDs, bounds and all arcs.

    Time fields share one seconds origin (not clock strings). Optional metadata is
    descriptive only; unknown fields are rejected to prevent silent typos.
    """
    fields(data, ['schema_version', 'time_unit', 'depot', 'customers', 'vehicles', 'travel'],
           ['metadata'], 'instance')
    if data['schema_version'] != '1.0' or data['time_unit'] != 'seconds':
        raise InputError('schema_version=1.0 and time_unit=seconds required')
    if 'metadata' in data and not isinstance(data['metadata'], Mapping):
        raise InputError('metadata: expected object')
    depot = data['depot']
    fields(depot, ['depot_id', 'opening_time', 'closing_time'], label='depot')
    depot_id = identifier(depot['depot_id'], 'depot_id')
    opening = nonnegative(depot['opening_time'], 'opening_time')
    closing = nonnegative(depot['closing_time'], 'closing_time')
    if opening > closing:
        raise InputError('depot opening > closing')
    customers = {}
    array(data['customers'], 'customers')
    for c in data['customers']:
        fields(c, ['customer_id', 'demand', 'earliest_service_time', 'latest_service_time',
                   'service_duration'], ['coordinates', 'mapped_road_node'], 'customer')
        cid = identifier(c['customer_id'], 'customer_id')
        if cid in customers or cid == depot_id:
            raise InputError(f'duplicate/depot customer ID: {cid}')
        e = nonnegative(c['earliest_service_time'], 'earliest_service_time')
        l = nonnegative(c['latest_service_time'], 'latest_service_time')
        if not opening <= e <= l <= closing:
            raise InputError(f'{cid}: require opening <= earliest <= latest <= closing')
        optional = {}
        if 'coordinates' in c:
            xy = c['coordinates']
            if not isinstance(xy, list) or len(xy) != 2:
                raise InputError('coordinates: expected two finite numbers')
            optional['coordinates'] = tuple(number(x, 'coordinate') for x in xy)
        if 'mapped_road_node' in c:
            optional['mapped_road_node'] = identifier(c['mapped_road_node'], 'mapped_road_node')
        customers[cid] = MappingProxyType(dict(demand=nonnegative(c['demand'], 'demand'),
            earliest=e, latest=l, duration=nonnegative(c['service_duration'], 'service_duration'),
            **optional))
    vehicles = {}
    array(data['vehicles'], 'vehicles')
    for v in data['vehicles']:
        fields(v, ['vehicle_id', 'capacity'], label='vehicle')
        vid = identifier(v['vehicle_id'], 'vehicle_id')
        if vid in vehicles:
            raise InputError(f'duplicate vehicle ID: {vid}')
        capacity = number(v['capacity'], 'capacity')
        if capacity <= 0:
            raise InputError('capacity must be positive')
        vehicles[vid] = capacity
    nodes = {depot_id, *customers}
    arcs = {}
    array(data['travel'], 'travel')
    for a in data['travel']:
        fields(a, ['origin', 'destination', 'travel_time_seconds'], ['travel_distance'], 'arc')
        key = (identifier(a['origin'], 'origin'), identifier(a['destination'], 'destination'))
        if key[0] not in nodes or key[1] not in nodes or key[0] == key[1] or key in arcs:
            raise InputError(f'unknown/self/duplicate arc: {key}')
        arcs[key] = (nonnegative(a['travel_time_seconds'], 'travel_time_seconds'),
                     nonnegative(a['travel_distance'], 'travel_distance') if 'travel_distance' in a else None)
    required = {(i, j) for i in nodes for j in nodes if i != j}
    if required != arcs.keys():
        raise InputError(f'missing travel arcs: {sorted(required - arcs.keys())}')
    return MappingProxyType(dict(depot_id=depot_id, opening=opening, closing=closing,
        customers=MappingProxyType(customers), vehicles=MappingProxyType(vehicles),
        arcs=MappingProxyType(arcs)))
