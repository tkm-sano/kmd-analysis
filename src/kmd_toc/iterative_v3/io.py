from pathlib import Path
from dataclasses import asdict
import hashlib,json,os,time
from kmd_toc.common_initial_v1.plans import sha,read_initial
from kmd_toc.measurement_audit_v1.measurement import digest_payload,physical_payload
from kmd_toc.duty_break_v1.models import load_plan

ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads(Path(p).read_text())
def identity(plan):return digest_payload(physical_payload(plan))
def atomic(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+f'.tmp.{os.getpid()}.{time.time_ns()}')
    with tmp.open('w') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
    tmp.replace(path)
def dump(path,value):
    if Path(path).exists():raise FileExistsError(path)
    atomic(path,value)
def event(path,value):
    with Path(path).open('a') as f:f.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');f.flush()
def save_plan(path,plan):
    if Path(path).exists():
        if identity(load_plan(path))!=identity(plan):raise ValueError('EXISTING_PLAN_CONTENT_CONFLICT')
    else:dump(Path(path),asdict(plan))
def routes(plan):return {(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips}
def encode_routes(rs):return [dict(vehicle=k[0],trip=k[1],customers=list(v)) for k,v in sorted(rs.items())]
def decode_routes(rs):return {(r['vehicle'],r['trip']):tuple(r['customers']) for r in rs}
def memberships(rs):return {s:k for k,r in rs.items() for s in r}
def assignment_hash(rs):return digest_payload([dict(vehicle=k[0],trip=k[1],customers=sorted(r)) for k,r in sorted(rs.items())])
def load_problem(path,rest):
    from kmd_toc.common.models import load_problem as load
    from kmd_toc.duty_break_v1.models import activate,RestOptions
    return activate(load(path),version='duty-break-20261121-v1',rest_options=RestOptions(
        rest['allow_assumed_locations'],True,tuple(tuple(x) for x in rest['confirmed_locations'])))
def sources():
    # Pin transitive adapters as well as the new implementation. In particular
    # C's reused v2 wrapper/resources and descriptive aggregation are executable
    # dependencies; omitting them would leave the execution identity incomplete.
    files=[*(ROOT/'src/kmd_toc').rglob('*.py'),ROOT/'scripts/run_iterative_v3.py']
    files += [ROOT/'scripts/p2_precision_20261120/sector_mps.py',ROOT/'scripts/large_n_20261119_v5/quantum.py',
        ROOT/'configs/toc_delivery/common_conditions_v1_1.json',ROOT/'configs/toc_delivery/duty_break_20261121_v1.json',
        ROOT/'configs/p2_freeze_20261120/main_experiment_d.json',ROOT/'configs/shots_freeze_20261120/main_experiment_d.json',
        ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json',ROOT/'configs/common_initial_20261122_v1/policy.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))}
def verify_pins(pins):
    for p,h in pins.items():
        if sha(ROOT/p)!=h:raise ValueError('REGISTERED_SOURCE_OR_INPUT_CHANGED:'+p)
def tuples(value):return tuple(tuples(x) for x in value) if isinstance(value,list) else value
