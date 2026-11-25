from pathlib import Path
from types import SimpleNamespace as NS

from kmd_toc.duty_break_v1.models import RestOptions
from kmd_toc.duty_break_v1.policy import load_policy
from kmd_toc.grouped_loading_v2 import model,search
from kmd_toc.iterative_d3.rng_v2 import context,event
from kmd_toc.iterative_v3.io import read


def test_resumed_state_includes_times_and_existing_work_count(tmp_path):
    duty=load_policy()|{"loading_s":900}
    ids=("d","a","b","c","e")
    p=NS(vehicles=[NS(vehicle_id=f"v{i}",max_trips=2,capacity=60) for i in range(10)],
         stops=[NS(stop_id=s,demand=1) for s in ids[1:]],depot=NS(depot_id="d"),fingerprint="fixture",
         od=NS(ids=ids,fingerprint="fixture_od",
               distance_m={(i,j):0 if i==j else (i+2*j)*10+100 for i in range(5) for j in range(5)},
               duration_s={(i,j):0 if i==j else 30 for i in range(5) for j in range(5)}),
         rest_options=RestOptions(True),
         berths=[NS(berth_id=f"b{i}",opening_s=28800,closing_s=72000) for i in range(2)])
    base=model.evaluate(p,{("v0",1):("a","b"),("v5",1):("c","e")},[28800,28801],duty)
    ctx=context("diagnostic","S1",0)|{"branch":0}
    settings=dict(outer_iterations=2,physical_completion_budget=14,tabu_tenure=3,variant="D3",
                  moves_per_family=1,neighbor_attempts_per_family=64,transfer_attempts=64,
                  local_order_size=2,returned_order_candidates=4,
                  quantum={"optimizer_max_evaluations":24},classical={"classical_exact_up_to":6,"classical_evaluations":32},
                  rng_v2=ctx)
    seed=event(ctx,"D_shared","branch-identity")
    run=lambda name,**kw:search.run(p,base,tmp_path/name,"D_classical",settings,seed,0,duty,**kw)
    assert run("resume",pause_after=1)["status"]=="PAUSED"
    checkpoint=tmp_path/"resume/iteration_0000/COMMIT.json"
    before=checkpoint.read_bytes()
    continuous=run("continuous")
    resumed=run("resume")
    assert checkpoint.read_bytes()==before
    assert continuous["used"]==resumed["used"]<=14
    assert continuous["calls"]==resumed["calls"]<=2
    assert read(tmp_path/"resume/plan.json")==read(tmp_path/"continuous/plan.json")
    first=read(checkpoint);second=read(tmp_path/"resume/iteration_0001/COMMIT.json")
    assert first["state_hash"]==second["input_hash"]
    assert first["state_calls_s"]==second["input_calls_s"]
    assert any(r["calls_s"]!=r["parent"]["calls_s"] for r in first["candidate_receipts"] if r["kind"]=="reception_time")
