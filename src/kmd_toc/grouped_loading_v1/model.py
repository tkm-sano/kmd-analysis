"""Calculate full-plan D and wait components from explicit group calls and routes.

The current legacy problem loader supplies pinned geography, demand, fleet IDs and
rest evidence. Its stored first-ready and loading duration do not enter this queue.
"""
from collections import Counter
from dataclasses import asdict, dataclass
from fractions import Fraction
import math

from kmd_toc.iterative_v3.io import digest_payload, encode_routes
from kmd_toc.objective_alignment_v1.objective import Metrics, selection_key

LOADING_S = 900


class ScheduleError(ValueError):
    """The submitted conditions or complete plan are infeasible."""


def require(condition, reason):
    if not condition:
        raise ScheduleError(reason)


@dataclass(frozen=True)
class TimingDomain:
    earliest_s: int
    latest_s: int
    allow_equal: bool
    min_gap_s: int
    precall_is_wait: bool
    membership_mode: str
    physical_ready_source: str

    def validate(self):
        require(all(type(x) is int for x in (self.earliest_s, self.latest_s, self.min_gap_s))
                and 0 <= self.earliest_s <= self.latest_s < 86400 and self.min_gap_s >= 0,
                "EXPLICIT_CALL_DOMAIN_REQUIRED")
        require(type(self.allow_equal) is bool and type(self.precall_is_wait) is bool
                and self.membership_mode in {"fixed", "decision"}
                and isinstance(self.physical_ready_source, str) and self.physical_ready_source.strip(),
                "EXPLICIT_READY_WAIT_AND_GROUPING_REQUIRED")

    def check_calls(self, calls):
        self.validate()
        require(calls and all(type(x) is int and self.earliest_s <= x <= self.latest_s for x in calls),
                "CALL_OUT_OF_RANGE")
        gap = max(self.min_gap_s, 0 if self.allow_equal else 1)
        require(all(b-a >= gap for a,b in zip(calls, calls[1:])), "CALL_ORDER_OR_GAP")


@dataclass(frozen=True)
class Job:
    customers: tuple
    parcels: int
    distance_km: Fraction
    travel_s: tuple


def build_jobs(problem, routes):
    """Check coverage, physical vehicle/slot IDs and capacity before scheduling."""
    fleet = {v.vehicle_id:v for v in problem.vehicles}
    demand = {s.stop_id:s.demand for s in problem.stops}
    require(all(type(n) is int and n > 0 for n in demand.values()), "PARCEL_DATA")
    require(Counter(s for r in routes.values() for s in r) == Counter(demand.keys()), "DELIVERY_COVERAGE")
    index = {s:i for i,s in enumerate(problem.od.ids)}
    depot = index[problem.depot.depot_id]
    result = {}
    for (v,k), stops in sorted(routes.items()):
        require(v in fleet and type(k) is int and k in (1,2) and k <= fleet[v].max_trips and stops,
                "ACTIVE_TRIP_OR_VEHICLE")
        require(k == 1 or (v,1) in routes, "MISSING_FIRST_TRIP")
        parcels = sum(demand[s] for s in stops)
        require(parcels <= fleet[v].capacity, "TRIP_CAPACITY")
        nodes = (depot, *(index[s] for s in stops), depot)
        arcs = tuple(zip(nodes,nodes[1:]))
        distance = sum((Fraction(str(float(problem.od.distance_m[a,b]))) for a,b in arcs), Fraction())/1000
        travel = tuple(math.ceil(float(problem.od.duration_s[a,b])) for a,b in arcs)
        require(distance >= 0 and all(t >= 0 for t in travel), "OD_TRAVEL_VALUE")
        result[v,k] = Job(tuple(stops), parcels, distance, travel)
    return result


def road_activity(job, departure, rested, rest_options, duty):
    clock = departure
    rest = None
    visits = []

    def rest_at(stop, moment, placement):
        if (rested or rest is not None or not rest_options.eligible(stop)
                or not duty["break_start_earliest_s"] <= moment <= duty["break_start_latest_s"]):
            return None
        status, evidence = rest_options.evidence(stop)
        return dict(location_id=stop, start_s=moment, end_s=moment+duty["break_duration_s"],
                    placement=placement, location_status=status, evidence=evidence)

    for stop, leg in zip(job.customers, job.travel_s):
        arrival = clock + leg
        rest_before = rest_at(stop, arrival, "before_delivery_service")
        if rest_before:
            rest = rest_before
        start = rest_before["end_s"] if rest_before else arrival
        end = start+duty["service_s"]
        visits.append(dict(stop_id=stop, arrival_s=arrival, service_start_s=start, service_end_s=end))
        rest_after = rest_at(stop, end, "after_delivery_service")
        if rest_after:
            rest = rest_after
        clock = rest_after["end_s"] if rest_after else end
    return clock+job.travel_s[-1], visits, rest


def schedule_jobs(jobs, physical_ready, membership, calls, domain, berths, duty, rest_options,
                  depot_id, *, fixed_membership=None):
    """Run a single FCFS queue for first and second trips under the 900s policy."""
    loading = duty["loading_s"]
    require(loading == LOADING_S, "GROUPED_LOADING_POLICY_MISMATCH")
    domain.check_calls(calls)
    require(set(physical_ready) == set(membership) and len(physical_ready) == 5*len(calls)
            and Counter(membership.values()) == {i:5 for i in range(len(calls))},
            "FIVE_CONFIGURED_VEHICLES_PER_GROUP")
    if domain.membership_mode == "fixed":
        require(fixed_membership is not None and membership == fixed_membership, "FIXED_GROUP_CHANGED")
    require(all(type(r) is int and duty["shift_start_s"] <= r < duty["shift_end_s"] for r in physical_ready.values()),
            "PHYSICAL_READY_OUTSIDE_WORKDAY")
    require(berths and all(a < b for a,b in berths.values()), "BERTH_HOURS")
    pending = set(jobs)
    released = {(v,1):physical_ready[v] for v,k in jobs if k == 1}
    free = {b:max(opening,duty["shift_start_s"]) for b,(opening,_) in berths.items()}
    returns, breaks, trips, work = {}, {}, [], Counter()
    while pending:
        eligible = []
        for v,k in pending & released.keys():
            r = released[v,k]
            call = calls[membership[v]] if k == 1 else r
            eligible.append((max(r,call),v,k))
        require(eligible, "SECOND_TRIP_WITHOUT_RELEASE")
        q,v,k = min(eligible)
        r = released[v,k]
        start = max(q,min(free.values()))
        berth = min(b for b,t in free.items() if t <= start)
        end = start+loading
        require(end <= berths[berth][1], f"BERTH_CLOSING:{v}:{k}")
        free[berth] = end
        opening_wait = max(0, min(start, min(max(a,duty["shift_start_s"]) for a,_ in berths.values()))-q)
        precall = q-r
        job = jobs[v,k]
        returned, visits, rest = road_activity(job,end,v in breaks,rest_options,duty)
        require(returned <= duty["vehicle_return_deadline_s"], f"VEHICLE_RETURN_DEADLINE:{v}:{k}")
        if rest:
            breaks[v] = rest | dict(vehicle_id=v,trip_no=k)
        elapsed_wait = start-q+(precall if domain.precall_is_wait else 0)
        work[v] += sum(job.travel_s)+duty["service_s"]*len(job.customers)+loading+elapsed_wait
        require(work[v] <= duty["nonbreak_window_s"], f"NONBREAK_WINDOW:{v}")
        returns[v] = returned
        if k == 1 and (v,2) in pending:
            released[v,2] = returned+duty["preparation_s"]
        pending.remove((v,k))
        trips.append(dict(vehicle_id=v, trip_no=k, group_id=membership[v] if k == 1 else None,
            physical_ready_s=r, group_call_s=calls[membership[v]] if k == 1 else None, eligibility_s=q,
            load_start_s=start, load_end_s=end, departure_s=end, return_s=returned, berth_id=berth,
            pre_call_interval_s=precall, counted_pre_call_wait_s=precall if domain.precall_is_wait else 0,
            unclassified_as_wait_pre_call_s=0 if domain.precall_is_wait else precall,
            post_release_wait_s=start-q, opening_wait_s=opening_wait, berth_wait_s=start-q-opening_wait,
            waiting_s=elapsed_wait,
            loading_s=loading, post_loading_s=0, parcels=job.parcels, distance_km_exact=str(job.distance_km),
            visits=visits))
    for v in sorted(returns.keys()-breaks.keys()):
        if (rest_options.allow_post_final_depot_break and rest_options.eligible(depot_id)
                and returns[v] <= duty["break_start_earliest_s"]):
            status, evidence = rest_options.evidence(depot_id)
            start = duty["break_start_earliest_s"]
            breaks[v] = dict(vehicle_id=v, trip_no=None, location_id=depot_id, start_s=start,
                             end_s=start+duty["break_duration_s"], placement="after_final_return_by_noon",
                             location_status=status,evidence=evidence)
        else:
            raise ScheduleError(f"MISSING_DUTY_BREAK:{v}")
    return sorted(trips,key=lambda t:(t["vehicle_id"],t["trip_no"])), list(breaks.values())


def measure(trips):
    """Keep internal total units and exact fractions for the existing ranking."""
    return Metrics(sum((Fraction(t["distance_km_exact"]) for t in trips),Fraction()),
                   Fraction(sum(t["waiting_s"] for t in trips),60))


def candidate_key(plan, reference, *, initial=False, branch_id=0):
    return selection_key(measure(plan["trips"]),measure(reference["trips"]),
                         initial=initial,branch_id=branch_id,stable_id=plan["physical_hash"])


def evaluate(problem, routes, physical_ready, membership, calls, domain, duty, *, fixed_membership=None):
    """Rebuild all times for every assignment, sequence or call update."""
    require(set(physical_ready) == {v.vehicle_id for v in problem.vehicles}, "PHYSICAL_READY_FLEET_MISMATCH")
    require(duty["preparation_s"] == 0, "RETURN_PREPARATION_POLICY_CHANGED")
    jobs = build_jobs(problem,routes)
    berths = {b.berth_id:(b.opening_s,b.closing_s) for b in problem.berths}
    trips, breaks = schedule_jobs(jobs,physical_ready,membership,calls,domain,berths,duty,problem.rest_options,
                                  problem.depot.depot_id,fixed_membership=fixed_membership)
    measurements = measure(trips)
    parcels = sum(s.demand for s in problem.stops)
    active = len({t["vehicle_id"] for t in trips})
    fields = ("pre_call_interval_s","counted_pre_call_wait_s","post_release_wait_s","opening_wait_s","berth_wait_s")
    payload = dict(version="grouped-loading-20261124-v1", routes=encode_routes(routes),
                   base_problem_hash=problem.fingerprint, od_hash=problem.od.fingerprint,
                   timing_domain=asdict(domain),
                   calls_s=list(calls), group_gaps_s=[b-a for a,b in zip(calls,calls[1:])],
                   membership=membership, physical_ready_s=physical_ready, precall_is_wait=domain.precall_is_wait,
                   physical_ready_source=domain.physical_ready_source, trips=trips, breaks=breaks)
    return payload | dict(physical_hash=digest_payload(payload), feasible=True,
        L_km=float(measurements.D), D_exact=str(measurements.D), D_km_per_parcel=float(measurements.D/parcels),
        W_total_min=float(measurements.W), W_exact=str(measurements.W), W_total_s=sum(t["waiting_s"] for t in trips),
        W_min_per_configured_vehicle_day=float(measurements.W/len(physical_ready)),
        W1_s=sum(t["waiting_s"] for t in trips if t["trip_no"]==1),
        W2_s=sum(t["waiting_s"] for t in trips if t["trip_no"]==2),
        **{key:sum(t[key] for t in trips) for key in fields},
        parcels=parcels, configured_vehicles=len(physical_ready), active_vehicles=active,
        unused_vehicles=len(physical_ready)-active)
