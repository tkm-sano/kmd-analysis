"""Independent day-column contracts. See D_VEHICLE_DAY_FORMULATION.md.

Input distances km, times integer seconds, demand parcels; output immutable data.
No RNG. Invalid/null operational data raise ValueError, never use old defaults.
"""
from dataclasses import dataclass
from functools import cached_property
import hashlib
import json
import math
from kmd_toc.column_generation.models import Instance


@dataclass(frozen=True)
class Vehicle:
    vehicle_id: str
    capacity: int
    ready_s: int
    shift_start_s: int
    shift_end_s: int
    loading_s: int
    preparation_s: int


@dataclass(frozen=True)
class DayProblem:
    base: Instance
    travel_s: tuple[tuple[int, ...], ...]
    service_s: tuple[int, ...]
    vehicles: tuple[Vehicle, ...]
    berths: int
    delta_s: int

    def __post_init__(self):
        n = len(self.base.demand)
        if len(self.travel_s) != n or any(len(r) != n for r in self.travel_s):
            raise ValueError('TRAVEL_SHAPE')
        if any(type(t) is not int or t < 0 for r in self.travel_s for t in r):
            raise ValueError('INVALID_TRAVEL_TIME')
        if len(self.service_s) != n or any(type(t) is not int or t < 0 for t in self.service_s):
            raise ValueError('INVALID_SERVICE_TIME')
        if not self.vehicles or len({v.vehicle_id for v in self.vehicles}) != len(self.vehicles):
            raise ValueError('INVALID_VEHICLES')
        if type(self.berths) is not int or self.berths < 1 or type(self.delta_s) is not int or self.delta_s < 1:
            raise ValueError('INVALID_BERTH_OR_GRID')
        for v in self.vehicles:
            if not v.vehicle_id or any(type(x) is not int for x in [v.capacity, v.ready_s,
                    v.shift_start_s, v.shift_end_s, v.loading_s, v.preparation_s]):
                raise ValueError('INCOMPLETE_OPERATIONS')
            if not (v.capacity > 0 and 0 <= v.shift_start_s <= v.ready_s <= v.shift_end_s
                    and v.loading_s > 0 and v.preparation_s >= 0):
                raise ValueError('INVALID_OPERATIONS')

    @property
    def slots(self):
        return math.ceil(max(v.shift_end_s for v in self.vehicles) / self.delta_s)

    def vehicle(self, vehicle_id):
        return next(v for v in self.vehicles if v.vehicle_id == vehicle_id)

    @cached_property
    def fingerprint(self):
        value = {'name': self.base.name, 'distance': self.base.distance.tolist(),
                 'demand': self.base.demand, 'travel_s': self.travel_s,
                 'service_s': self.service_s, 'vehicles': [vars(v) for v in self.vehicles],
                 'berths': self.berths, 'delta_s': self.delta_s}
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class TripSchedule:
    trip_id: int
    customers: tuple[int, ...]
    parcel_count: int
    ready_s: int
    load_start_s: int
    load_end_s: int
    departure_s: int
    return_s: int
    travel_s: int
    service_s: int
    preparation_s: int
    distance_km: float


@dataclass(frozen=True)
class DayColumn:
    problem_hash: str
    vehicle_id: str
    shift_start_s: int
    shift_end_s: int
    trips: tuple[TripSchedule, ...]

    @property
    def customers(self):
        return tuple(i for trip in self.trips for i in trip.customers)

    @property
    def distance_km(self):
        return sum(t.distance_km for t in self.trips)

    @property
    def waiting_min(self):
        return sum(t.load_start_s - t.ready_s for t in self.trips) / 60

    @property
    def loading_s(self):
        return sum(t.load_end_s - t.load_start_s for t in self.trips)

    @property
    def identity(self):
        return (self.problem_hash, self.vehicle_id,
                tuple((t.customers, t.load_start_s) for t in self.trips))

    @property
    def column_id(self):
        return hashlib.sha256(b'toc-day-column-v1\x00' +
                              json.dumps(self.identity, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class ObjectiveProfile:
    primary: str = 'D'
    other_limit: float | None = None

    def __post_init__(self):
        if self.primary not in ('D', 'W') or (self.other_limit is not None and
                (not math.isfinite(self.other_limit) or self.other_limit < 0)):
            raise ValueError('INVALID_OBJECTIVE_PROFILE')

    def cost(self, column):
        return column.distance_km if self.primary == 'D' else column.waiting_min

    def other(self, column):
        return column.waiting_min if self.primary == 'D' else column.distance_km


def occupied_slots(problem, column):
    return tuple(sorted({u for trip in column.trips for u in
        range(trip.load_start_s // problem.delta_s,
              math.ceil(trip.load_end_s / problem.delta_s))}))
