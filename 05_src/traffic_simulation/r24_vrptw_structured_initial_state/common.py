"""New offline-only artifact namespace; protected inputs are never written."""
from pathlib import Path
import csv, hashlib, json
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reproducibility/outputs/traffic_simulation'
OUT=BASE/'r24_vrptw_structured_initial_state/20260922_v1'
FREEZE=BASE/'r24_vrptw_qaoa_execution_spec/20260921_v1'
STUDY=BASE/'r24_vrptw_qaoa_execution/20260921_v1'
ROAD=BASE/'r24_vrptw_road_network_routes/20260921_v1'
CV=BASE/'r24_qaoa_initial_state_cross_condition_reproducibility_spec/20260919_v1'
ENC=BASE/'r24_vrptw_quantum_encoding_preflight/20260921_v1'
BENCH=BASE/'r24_vrptw_benchmark_spec/20260921_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()
def dump(n,v):
    p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def rows(p):
    with Path(p).open() as f:return list(csv.DictReader(f))
def table(n,records):
    fields=list(dict.fromkeys(k for r in records for k in r))
    with (OUT/n).open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in records:w.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()})
