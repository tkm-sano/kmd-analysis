"""Method-independent v1 records. Times are integer seconds since JST midnight."""
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path
from .config import load_conditions, ready_s, fingerprint, CONFIG_SHA256, read_json
from .od import OD, save_od, load_od


def integer(value, *, minimum=0):
    return type(value) is int and value >= minimum


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


@dataclass(frozen=True)
class Snap:
    longitude: float
    latitude: float
    distance_m: float
    hint: str
    node_ids: tuple[int, ...]
    graph_id: str
    reviewed: bool
    evidence: str

    def validate(self, graph_id, kind, original=None):
        return self._validate_with_alert(graph_id, kind, original,
                                         load_conditions()['road_policy']['snap_alert_m'])

    def _validate_with_alert(self, graph_id, kind, original, snap_alert_m):
        """Use the same already hash-verified policy within one input check.

        Public validate still verifies its policy itself. Problem.validate has
        already loaded the pinned conditions, so it need not reopen the same
        file once for every delivery point.
        """
        if (not number(self.longitude) or not -180 <= self.longitude <= 180 or
                not number(self.latitude) or not -90 <= self.latitude <= 90 or
                not number(self.distance_m) or self.distance_m < 0 or
                self.distance_m > snap_alert_m or
                not isinstance(self.hint,str) or not self.hint or
                not isinstance(self.node_ids,(list,tuple)) or not self.node_ids or
                any(not integer(i) for i in self.node_ids) or self.graph_id != graph_id or
                self.reviewed is not True or not isinstance(self.evidence,str) or not self.evidence):
            raise ValueError('SNAP_MISSING_UNREVIEWED_OR_INAPPROPRIATE')
        if kind == 'osm_osrm':
            token = self.evidence.removeprefix('sha256:')
            if not self.evidence.startswith('sha256:') or len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
                raise ValueError('SNAP_REVIEW_EVIDENCE_HASH_REQUIRED')
        if original is not None:
            lon, lat = original
            phi1, phi2 = math.radians(lat), math.radians(self.latitude)
            a = (math.sin((phi2-phi1)/2)**2 + math.cos(phi1)*math.cos(phi2)*
                 math.sin(math.radians(self.longitude-lon)/2)**2)
            displacement = 6371008.8 * 2 * math.asin(math.sqrt(min(1,a)))
            # Geodesic distance is only a snap diagnostic, never an OD cost.
            if abs(displacement-self.distance_m) > 3:
                raise ValueError('SNAP_REPORTED_DISTANCE_INCONSISTENT')


@dataclass(frozen=True)
class Stop:
    stop_id: str
    longitude: float
    latitude: float
    demand: int
    snap: Snap
    source: dict


@dataclass(frozen=True)
class Vehicle:
    vehicle_id: str
    capacity: int
    max_trips: int
    first_ready_s: int
    return_deadline_s: int


@dataclass(frozen=True)
class Depot:
    depot_id: str
    longitude: float
    latitude: float
    snap: Snap
    entrance_verified: bool
    entrance_evidence: str


@dataclass(frozen=True)
class Berth:
    berth_id: str
    depot_id: str
    opening_s: int
    closing_s: int
    loading_s: int
    preparation_s: int


@dataclass(frozen=True)
class Experiment:
    scenario_id: str
    conditions_version: str
    conditions_sha256: str
    random_seed: int | None
    data_hashes: dict
    environment: dict
    method_settings: dict
    kind: str  # synthetic_validation, road_validation, or frozen_research


@dataclass(frozen=True)
class Problem:
    stops: tuple[Stop, ...]
    vehicles: tuple[Vehicle, ...]
    depot: Depot
    berths: tuple[Berth, ...]
    od: OD
    experiment: Experiment

    def payload(self):
        return {'schema_version': '1.0', 'stops': [asdict(s) for s in self.stops],
                'vehicles': [asdict(v) for v in self.vehicles], 'depot': asdict(self.depot),
                'berths': [asdict(b) for b in self.berths], 'experiment': asdict(self.experiment),
                'od_hash': self.od.fingerprint}

    @property
    def fingerprint(self):
        return fingerprint(self.payload())

    def validate(self):
        c = load_conditions()
        o, e = c['operations'], self.experiment
        if (e.conditions_version != c['conditions_version'] or e.conditions_sha256 != CONFIG_SHA256 or
                e.kind not in ('synthetic_validation', 'road_validation', 'frozen_research') or
                (e.random_seed is not None and not integer(e.random_seed)) or
                not isinstance(e.environment, dict) or not e.environment or
                not isinstance(e.method_settings, dict) or not isinstance(e.data_hashes, dict)):
            raise ValueError('EXPERIMENT_VERSION_OR_METADATA')
        if not self.stops or not self.vehicles or not self.berths:
            raise ValueError('EMPTY_INPUT')
        for records, key in [(self.stops, 'stop_id'), (self.vehicles, 'vehicle_id'), (self.berths, 'berth_id')]:
            ids = [getattr(r, key) for r in records]
            if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
                raise ValueError('MISSING_OR_DUPLICATE_' + key)
        if not self.depot.depot_id or self.depot.depot_id in {s.stop_id for s in self.stops}:
            raise ValueError('DEPOT_ID')
        if self.depot.entrance_verified is not True or not self.depot.entrance_evidence:
            raise ValueError('DEPOT_ENTRANCE_UNVERIFIED')
        if (self.od.ids != (self.depot.depot_id, *(s.stop_id for s in self.stops)) or
                e.data_hashes.get('od') != self.od.fingerprint):
            raise ValueError('OD_IDS_OR_HASH')
        self.od.audit()
        for record in (*self.stops, self.depot):
            if (not number(record.longitude) or not -180 <= record.longitude <= 180 or
                    not number(record.latitude) or not -90 <= record.latitude <= 90):
                raise ValueError('COORDINATE_RANGE')
            record.snap._validate_with_alert(self.od.metadata['graph_id'], self.od.metadata['kind'],
                                            (record.longitude,record.latitude), c['road_policy']['snap_alert_m'])
        for s in self.stops:
            if type(s.demand) is not int or s.demand != o['demand_per_stop']:
                raise ValueError('DEMAND_UNIT_OR_VALUE')
            if not isinstance(s.source, dict) or not all(s.source.get(k) for k in ('kind', 'source', 'generation', 'sha256')):
                raise ValueError('STOP_PROVENANCE')
        for index, v in enumerate(self.vehicles):
            expected = (o['capacity_per_trip'], o['max_trips_per_vehicle'],
                        ready_s(index, len(self.vehicles), c), o['closing_s'])
            actual = (v.capacity, v.max_trips, v.first_ready_s, v.return_deadline_s)
            if any(type(x) is not int for x in actual) or actual != expected:
                raise ValueError('VEHICLE_CONDITIONS_OR_ORDER')
        for b in self.berths:
            actual = (b.opening_s, b.closing_s, b.loading_s, b.preparation_s)
            if (any(type(x) is not int for x in actual) or
                    actual != tuple(o[k] for k in ('opening_s', 'closing_s', 'loading_s', 'preparation_s')) or
                    b.depot_id != self.depot.depot_id):
                raise ValueError('BERTH_CONDITIONS')
        if e.kind == 'frozen_research':
            self._validate_frozen(c)
        elif e.kind == 'road_validation':
            if (self.od.metadata['kind'] != 'osm_osrm' or not e.scenario_id.startswith('ROAD_') or
                    e.scenario_id in c['scenarios']):
                raise ValueError('ROAD_VALIDATION_LABEL_REQUIRED')
        elif (self.od.metadata['kind'] != 'synthetic' or e.scenario_id in c['scenarios']):
            raise ValueError('SYNTHETIC_LABEL_REQUIRED')
        return self

    def _validate_frozen(self, conditions):
        from kmd_toc.frozen_demand import load_frozen_demand
        e = self.experiment
        frozen = load_frozen_demand(e.scenario_id, method_id='B')
        if (len(self.stops), len(self.vehicles), len(self.berths)) != (frozen.N, frozen.vehicles, frozen.berths):
            raise ValueError('FROZEN_SCENARIO_COUNTS')
        if (e.data_hashes.get('demand_manifest') != frozen.manifest_sha256 or
                e.data_hashes.get('demand_csv') != frozen.csv_sha256):
            raise ValueError('FROZEN_DEMAND_HASH')
        expected = tuple((s.stop_id, float(s.longitude), float(s.latitude), s.parcel_count) for s in frozen.stops)
        if tuple((s.stop_id, s.longitude, s.latitude, s.demand) for s in self.stops) != expected:
            raise ValueError('FROZEN_DEMAND_ATTRIBUTES')
        if any(s.source['sha256'] != frozen.csv_sha256 or s.source['kind'] != 'frozen_synthetic_demand'
               for s in self.stops):
            raise ValueError('FROZEN_STOP_PROVENANCE')
        if self.od.metadata['kind'] != 'osm_osrm':
            raise ValueError('RESEARCH_REQUIRES_OSM_OSRM')


@dataclass(frozen=True)
class Visit:
    stop_id: str
    arrival_s: int
    service_start_s: int
    service_end_s: int


@dataclass(frozen=True)
class Trip:
    vehicle_id: str
    trip_no: int
    origin_id: str
    destination_id: str
    visits: tuple[Visit, ...]
    ready_s: int
    berth_id: str
    load_start_s: int
    load_end_s: int
    departure_s: int
    return_s: int
    distance_m: float
    waiting_s: int


@dataclass(frozen=True)
class Plan:
    schema_version: str
    plan_id: str
    method_id: str
    problem_hash: str
    od_hash: str
    trips: tuple[Trip, ...]
    method_settings: dict
    execution_kind: str  # classical or quantum_circuit_simulator


def save_problem(problem, directory):
    problem.validate()
    p = Path(directory)
    p.mkdir(parents=True, exist_ok=False)
    save_od(problem.od, p / 'od')
    data = problem.payload()
    data['problem_hash'] = problem.fingerprint
    (p / 'input.json').write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))


def load_problem(directory):
    p = Path(directory)
    d = read_json(p / 'input.json')
    if set(d) != {'schema_version', 'stops', 'vehicles', 'depot', 'berths', 'experiment', 'od_hash', 'problem_hash'} or d['schema_version'] != '1.0':
        raise ValueError('INPUT_SCHEMA')
    try:
        def with_snap(cls, row):
            row = dict(row)
            snap = dict(row.pop('snap'))
            snap['node_ids'] = tuple(snap['node_ids'])
            return cls(**row, snap=Snap(**snap))
        problem = Problem(tuple(with_snap(Stop, row) for row in d['stops']),
                          tuple(Vehicle(**row) for row in d['vehicles']), with_snap(Depot, d['depot']),
                          tuple(Berth(**row) for row in d['berths']), load_od(p / 'od'), Experiment(**d['experiment']))
    except (TypeError, KeyError) as error:
        raise ValueError('INPUT_FIELDS') from error
    if problem.od.fingerprint != d['od_hash'] or problem.fingerprint != d['problem_hash']:
        raise ValueError('INPUT_HASH')
    return problem.validate()


def save_plan(plan, path):
    with Path(path).open('x') as stream:
        json.dump(asdict(plan), stream, ensure_ascii=False, indent=2, allow_nan=False)


def load_plan(path):
    d = read_json(path)
    try:
        trips = []
        for row in d.pop('trips'):
            row['visits'] = tuple(Visit(**v) for v in row['visits'])
            trips.append(Trip(**row))
        return Plan(**d, trips=tuple(trips))
    except (TypeError, KeyError) as error:
        raise ValueError('OUTPUT_FIELDS') from error
