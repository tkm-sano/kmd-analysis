"""Independent saved-plan checks for the grouped loading experiment."""
from collections import Counter
from fractions import Fraction
import heapq

from .model import require


def recheck(plan, jobs, berths, duty, rest_options, depot_id):
    rows = {(t["vehicle_id"],t["trip_no"]):t for t in plan["trips"]}
    require(len(rows) == len(plan["trips"]) and rows.keys() == jobs.keys(), "SAVED_TRIP_SET")
    rests = {b["vehicle_id"]:b for b in plan["breaks"]}
    require(len(rests) == len(plan["breaks"]) and rests.keys() == {v for v,k in rows}, "ONE_BREAK_PER_ACTIVE_DRIVER")
    events = [(max(a,duty["shift_start_s"]),0,b,0) for b,(a,_) in berths.items()]
    for v,k in rows:
        if k == 1:
            r = plan["physical_ready_s"][v]
            heapq.heappush(events,(max(r,plan["calls_s"][plan["membership"][v]]),1,v,k))
    heapq.heapify(events)
    queue, idle, seen = [], set(), set()
    total_w, total_d = 0, Fraction()
    work, earliest_break = Counter(), {}
    while events and len(seen) < len(rows):
        now = events[0][0]
        while events and events[0][0] == now:
            stamp,kind,identity,k = heapq.heappop(events)
            if kind == 0:
                idle.add(identity)
            else:
                heapq.heappush(queue,(stamp,identity,k))
        while idle and queue:
            q,v,k = heapq.heappop(queue)
            b = min(idle)
            idle.remove(b)
            t, job = rows[v,k], jobs[v,k]
            r = plan["physical_ready_s"][v] if k == 1 else rows[v,1]["return_s"]+duty["preparation_s"]
            call = plan["calls_s"][plan["membership"][v]] if k == 1 else None
            require((t["group_id"],t["group_call_s"]) == (plan["membership"][v] if k == 1 else None,call),
                    "SAVED_GROUP_OR_CALL")
            require((t["physical_ready_s"],t["eligibility_s"],t["load_start_s"],t["berth_id"]) == (r,q,now,b),
                    "EVENT_QUEUE_MISMATCH")
            loading = duty["loading_s"]
            end = now+loading
            require(end <= berths[b][1] and end == t["load_end_s"] == t["departure_s"], "SAVED_LOADING_OR_DEPARTURE")
            require(t["loading_s"] == loading and t["post_loading_s"] == 0, "SAVED_ACTIVITY_DURATIONS")
            require(t["parcels"] == job.parcels and Fraction(t["distance_km_exact"]) == job.distance_km, "SAVED_LOAD_OR_DISTANCE")
            br = rests[v]
            require(rest_options.eligible(br["location_id"])
                    and (br["location_status"],br["evidence"]) == rest_options.evidence(br["location_id"]),
                    "BREAK_LOCATION")
            require(duty["break_start_earliest_s"] <= br["start_s"] <= duty["break_start_latest_s"]
                    and br["end_s"]-br["start_s"] == duty["break_duration_s"]
                    and br["end_s"] <= duty["break_end_latest_s"], "BREAK_WINDOW")
            clock, crossings = end, 0
            require(tuple(x["stop_id"] for x in t["visits"]) == job.customers, "SAVED_ROUTE")
            for visit, leg in zip(t["visits"],job.travel_s):
                stop = visit["stop_id"]
                arrival = clock+leg
                if rest_options.eligible(stop) and duty["break_start_earliest_s"] <= arrival <= duty["break_start_latest_s"]:
                    earliest_break.setdefault(v,(k,stop,arrival,"before_delivery_service"))
                clock = arrival
                if br["trip_no"] == k and br["location_id"] == stop and br["placement"] == "before_delivery_service":
                    require(clock == br["start_s"], "BREAK_NOT_AT_ARRIVAL")
                    clock = br["end_s"]
                    crossings += 1
                require((arrival,clock,clock+duty["service_s"]) ==
                        (visit["arrival_s"],visit["service_start_s"],visit["service_end_s"]), "SAVED_VISIT_TIMES")
                clock += duty["service_s"]
                if rest_options.eligible(stop) and duty["break_start_earliest_s"] <= clock <= duty["break_start_latest_s"]:
                    earliest_break.setdefault(v,(k,stop,clock,"after_delivery_service"))
                if br["trip_no"] == k and br["location_id"] == stop and br["placement"] == "after_delivery_service":
                    require(clock == br["start_s"], "BREAK_NOT_AT_SERVICE_END")
                    clock = br["end_s"]
                    crossings += 1
            clock += job.travel_s[-1]
            require(crossings == int(br["trip_no"] == k) and clock == t["return_s"] <= duty["vehicle_return_deadline_s"],
                    "SAVED_RETURN_OR_BREAK")
            opening = max(0,min(now,min(max(a,duty["shift_start_s"]) for a,_ in berths.values()))-q)
            precall = q-r
            counted = precall if plan["precall_is_wait"] else 0
            w = counted+now-q
            require(0 <= r <= q <= now
                    and (t["pre_call_interval_s"],t["counted_pre_call_wait_s"],t["post_release_wait_s"],
                         t["opening_wait_s"],t["berth_wait_s"],t["waiting_s"]) ==
                    (precall,counted,now-q,opening,now-q-opening,w), "SAVED_WAIT_COMPONENTS")
            total_w += w
            total_d += job.distance_km
            work[v] += sum(job.travel_s)+duty["service_s"]*len(job.customers)+loading+w
            seen.add((v,k))
            heapq.heappush(events,(end,0,b,0))
            if k == 1 and (v,2) in rows:
                heapq.heappush(events,(clock+duty["preparation_s"],1,v,2))
    require(seen == rows.keys(), "INCOMPLETE_EVENT_REPLAY")
    for v,br in rests.items():
        require(work[v] <= duty["nonbreak_window_s"], "SAVED_WORK_WINDOW")
        if br["trip_no"] is None:
            require(rest_options.allow_post_final_depot_break and br["location_id"] == depot_id
                    and v not in earliest_break
                    and br["placement"] == "after_final_return_by_noon"
                    and br["start_s"] == duty["break_start_earliest_s"]
                    and max(t["return_s"] for (vid,_),t in rows.items() if vid == v) <= br["start_s"], "DEPOT_BREAK")
        else:
            require(earliest_break.get(v) == (br["trip_no"],br["location_id"],br["start_s"],br["placement"]),
                    "SAVED_BREAK_NOT_EARLIEST")
    parcels = sum(job.parcels for job in jobs.values())
    require(Counter(s for job in jobs.values() for s in job.customers) ==
            Counter(s for t in plan["trips"] for s in (v["stop_id"] for v in t["visits"])), "SAVED_COVERAGE")
    require((total_d,Fraction(total_w,60),parcels) == (
        Fraction(plan["D_exact"]),Fraction(plan["W_exact"]),plan["parcels"]), "SAVED_D_W_OR_PARCELS")
    require(total_w == plan["W_total_s"] and total_w == plan["W1_s"]+plan["W2_s"]
            and float(Fraction(total_w,60*plan["configured_vehicles"])) == plan["W_min_per_configured_vehicle_day"]
            and float(total_d/parcels) == plan["D_km_per_parcel"], "SAVED_REPORT_UNITS")
    return dict(status="PASS", rechecked_trips=len(seen), W_total_s=total_w, D_exact=str(total_d))
