"""Explicit unit/index conversion only. No solver invocation or success fallback."""
from .config import load_conditions, ready_s, CONFIG_SHA256
from .models import Stop, Vehicle, Berth, Experiment, Problem


def from_frozen(scenario_id, *, depot, snaps, od, environment, random_seed=None):
    from kmd_toc.frozen_demand import load_frozen_demand
    demand = load_frozen_demand(scenario_id, method_id='B')
    if set(snaps) != {s.stop_id for s in demand.stops}:
        raise ValueError('FROZEN_SNAP_ID_SET')
    c = load_conditions()
    o = c['operations']
    stops = tuple(Stop(s.stop_id,float(s.longitude),float(s.latitude),s.parcel_count,snaps[s.stop_id],
                       {'kind':'frozen_synthetic_demand','source':f'{scenario_id}.csv',
                        'generation':'frozen_demand_v1_no_runtime_generation','sha256':demand.csv_sha256})
                  for s in demand.stops)
    vehicles = tuple(Vehicle(f'v{v}',o['capacity_per_trip'],o['max_trips_per_vehicle'],
                             ready_s(v,demand.vehicles,c),o['closing_s']) for v in range(demand.vehicles))
    berths = tuple(Berth(f'b{b}',depot.depot_id,o['opening_s'],o['closing_s'],o['loading_s'],
                         o['preparation_s']) for b in range(demand.berths))
    experiment = Experiment(scenario_id,c['conditions_version'],CONFIG_SHA256,random_seed,
                            {'demand_manifest':demand.manifest_sha256,'demand_csv':demand.csv_sha256,
                             'od':od.fingerprint},environment,{},'frozen_research')
    return Problem(stops,vehicles,depot,berths,od,experiment).validate()


def indexed_solver_input(problem):
    """B/C neutral view. Arrays stay in metres/seconds; assignment remains free."""
    problem.validate()
    return {'ids':problem.od.ids,'distance_m':problem.od.distance_m,'duration_s':problem.od.duration_s,
            'demand':(0,*(s.demand for s in problem.stops)), 'vehicles':problem.vehicles,
            'berths':problem.berths,'problem_hash':problem.fingerprint,'od_hash':problem.od.fingerprint}


def to_vehicle_day(problem, *, delta_s=1):
    """Input conversion to existing D contracts; does NOT establish S1 readiness.

    This explicit bridge imports existing D only when called. D distance uses km.
    The exact raw OD stays common; travel is ceiled per arc under common policy.
    """
    import math
    from kmd_toc.column_generation.models import Instance
    from kmd_toc.vehicle_day.model import DayProblem, Vehicle as DayVehicle
    problem.validate()
    if type(delta_s) is not int or delta_s < 1:
        raise ValueError('D_TIME_GRID')
    c = load_conditions()['operations']
    base = Instance(problem.experiment.scenario_id,problem.od.distance_m/1000,
                    (0,*(s.demand for s in problem.stops)),c['capacity_per_trip'])
    vehicles = tuple(DayVehicle(v.vehicle_id,v.capacity,v.first_ready_s,c['opening_s'],
                                v.return_deadline_s,c['loading_s'],c['preparation_s'])
                     for v in problem.vehicles)
    travel = tuple(tuple(math.ceil(float(x)) for x in row) for row in problem.od.duration_s)
    return DayProblem(base,travel,(0,*(c['service_s'] for s in problem.stops)),vehicles,len(problem.berths),delta_s)


def from_vehicle_day(problem, day_problem, columns, berth_assignments, *, method_settings):
    """Serialize D records; preserve reported times/costs for independent rejection.

    D has ordered stops but no per-stop timestamps. Expansion uses the common OD.
    Explicit berth assignment is required; no scheduling, repair, or optimization.
    """
    from .models import Visit, Trip, Plan
    problem.validate()
    service_s = load_conditions()['operations']['service_s']
    if day_problem.fingerprint != to_vehicle_day(problem,delta_s=day_problem.delta_s).fingerprint:
        raise ValueError('D_BRIDGE_INPUT_HASH')
    trips = []
    for column in columns:
        if column.problem_hash != day_problem.fingerprint:
            raise ValueError('D_COLUMN_INPUT_HASH')
        for trip in column.trips:
            try:
                berth_id = berth_assignments[column.vehicle_id,trip.trip_id]
            except KeyError as error:
                raise ValueError('D_EXPLICIT_BERTH_REQUIRED') from error
            clock, node, visits = trip.departure_s, problem.depot.depot_id, []
            for index in trip.customers:
                if type(index) is not int or not 1 <= index < len(problem.od.ids):
                    raise ValueError('D_CUSTOMER_INDEX')
                identifier = problem.od.ids[index]
                _, seconds = problem.od.leg(node,identifier)
                clock += seconds
                visits.append(Visit(identifier,clock,clock,clock+service_s))
                clock += service_s
                node = identifier
            trips.append(Trip(column.vehicle_id,trip.trip_id,problem.depot.depot_id,problem.depot.depot_id,
                              tuple(visits),trip.ready_s,berth_id,trip.load_start_s,trip.load_end_s,
                              trip.departure_s,trip.return_s,trip.distance_km*1000,
                              trip.load_start_s-trip.ready_s))
    return Plan('1.0','D-day-column-export','D',problem.fingerprint,problem.od.fingerprint,tuple(trips),
                method_settings,'quantum_circuit_simulator')
