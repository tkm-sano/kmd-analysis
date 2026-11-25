from fractions import Fraction as F
from types import SimpleNamespace as NS
import pytest
from kmd_toc.duty_break_v1.models import RestOptions
from kmd_toc.duty_break_v1.policy import load_policy
from kmd_toc.grouped_loading_v2.model import Job, ScheduleError, TimingDomain, evaluate, group_map, schedule_jobs
from kmd_toc.grouped_loading_v2.methods import call_move, work_calls

START=28800
DUTY=load_policy()|{"loading_s":900}
REST=RestOptions(allow_assumed_locations=True)
MODE=TimingDomain(START,32400,False,1,False,"fixed","prepared by appointment")
JOB=Job(("x",),1,F(1),(30,30))


def run(n,jobs,calls=(START,START+1200),fleet=10):
    groups={f"v{i}":i//5 for i in range(fleet)}
    return schedule_jobs(jobs,dict.fromkeys(groups,START),groups,calls,MODE,
        {f"b{i}":(START,72000) for i in range(n)},DUTY,REST,"depot",fixed_membership=groups)[0]


@pytest.mark.parametrize(("n","wait"),[(2,3600),(4,900),(8,0)])
def test_hand_900s(n,wait):
    rows=run(n,{(f"v{i}",1):JOB for i in range(5)})
    assert sum(t["waiting_s"] for t in rows)==wait
    for i,t in enumerate(rows):
        assert t["load_start_s"]==START+(i//n)*900
        assert t["departure_s"]==t["load_end_s"]==t["load_start_s"]+900
        assert t["actual_reception_s"]==START and t["physical_ready_s"] is None


def test_receipt_0820_start_0835_and_opening():
    rows=run(2,{(f"v{i}",1):JOB for i in (5,6,7)})
    third=rows[-1]
    assert third["actual_reception_s"]==30000 and third["before_reception_since_shift_s"]==1200
    assert third["load_start_s"]==30900 and third["waiting_s"]==900 and third["departure_s"]==31800
    assert third["counted_pre_call_wait_s"]==0


def test_second_return_competes_with_group_2_and_unused_stays_out():
    jobs={("v0",1):JOB,("v0",2):JOB,("v5",1):JOB,("v6",1):JOB}
    rows=run(2,jobs,(START,START+1080))
    by={(t["vehicle_id"],t["trip_no"]):t for t in rows}
    assert set(by)==set(jobs)
    assert by["v0",2]["actual_reception_s"]==by["v0",1]["return_s"]==START+1080
    assert by["v0",2]["berth_id"]=="b0"
    assert by["v6",1]["load_start_s"]==by["v0",2]["departure_s"]


def test_numeric_vehicle_order_at_equal_release():
    jobs={("v9",1):JOB,("v9",2):JOB,("v10",1):JOB}
    rows=run(1,jobs,(START,START+1,START+1081),fleet=15)
    by={(t["vehicle_id"],t["trip_no"]):t for t in rows}
    assert by["v9",2]["actual_reception_s"]==by["v10",1]["actual_reception_s"]
    assert by["v9",2]["load_start_s"]<by["v10",1]["load_start_s"]
    assert group_map([NS(vehicle_id=f"v{i}") for i in reversed(range(15))])["v10"]==2


def test_empty_group_planned_time_keeps_its_identity():
    group=[NS(vehicle_id=f"v{i}",capacity=60,max_trips=2) for i in range(10)]
    p=NS(vehicles=group, stops=(NS(stop_id="a",demand=1),),
         od=NS(ids=("d","a"),distance_m={(0,1):10,(1,0):20},duration_s={(0,1):30,(1,0):30},fingerprint="o"),
         depot=NS(depot_id="d"),rest_options=REST,berths=[NS(berth_id="b0",opening_s=START,closing_s=72000)],
         fingerprint="test")
    rs={("v0",1):("a",)}
    a=evaluate(p,rs,(START,START+1),DUTY)
    b=evaluate(p,rs,(START,START+2),DUTY)
    assert a["trips"]==b["trips"] and a["physical_hash"]!=b["physical_hash"]
    assert work_calls(p,rs)==(START,START+900)
    # First available actual berth is busy until +900. Time move remains legal.
    assert call_move(p,rs,(START,START+1),0)==(START,START+900)
    for bad in ((START+1,START+2),(START,START),(START,32401)):
        with pytest.raises(ScheduleError):
            evaluate(p,rs,bad,DUTY)
