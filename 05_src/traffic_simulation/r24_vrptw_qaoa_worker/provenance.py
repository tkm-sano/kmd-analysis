"""Bootstrap and verify protection without altering the frozen specification."""
from datetime import datetime
import subprocess
import time
from .contract import *
from traffic_simulation.r24_qaoa_initial_state_cross_condition_worker.ledger import atomic

DOCS=['05_src/traffic_simulation/CURRENT_RESEARCH_DESIGN.md','docs/ja/R24_VALIDATION_AND_QAOA_REPORT.md',
      'docs/ja/R24_PROBLEM_SOLUTION_DECISION_RECORD.md','05_src/traffic_simulation/RESEARCH_PROGRESS_AND_DECISION_RECORD.md']

def prepare():
    OUT.mkdir(parents=True,exist_ok=False)
    (OUT/'GIT_STATUS_BEFORE.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True))
    atomic(OUT/'TIMING.json',dict(start_epoch=datetime.fromisoformat('2026-09-21T11:25:27+00:00').timestamp(),
        initial_estimate_minutes=[40,70],worst_case_minutes=110))
    protected=read(FREEZE/'PROTECTED_AFTER.json')
    for parent in [FREEZE,ROOT/'05_src/traffic_simulation/r24_vrptw_qaoa_execution_spec',
        ROOT/'05_src/traffic_simulation/r24_qaoa_initial_state_cross_condition_worker',
        ROOT/'05_src/traffic_simulation/r24_qaoa_resource_gate_redesign']:
        for p in parent.rglob('*'):
            if p.is_file() and '__pycache__' not in str(p):protected[str(p.relative_to(ROOT))]=sha(p)
    atomic(OUT/'PROTECTED_BEFORE.json',protected)
    atomic(OUT/'DOCUMENT_PREFIXES_BEFORE.json',{p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in DOCS})
    load()
    atomic(OUT/'WORKER_SPEC.json',dict(status='IMPLEMENTATION_IN_PROGRESS',source=str(FREEZE.relative_to(ROOT)),
        execution_spec_manifest_sha256=MANIFEST_SHA256,conditions=7,planned_runs=21,batches=7,
        scientific_execution=0,Aer=0,optimizer=0,final_sampling=0,
        required_steps=['spec','identity','condition','QUBO','reference','validator','config','seeds','parameters','circuit','transpile','resource','reserve/claim','future optimizer','future final','decode','validate','metrics','save','finalize'],
        frozen_spec_mutations=False,readiness_ceiling='OFFLINE_ACCEPTANCE_VALIDATED'))
    print('Provenance captured; frozen spec verified; protected files',len(protected))

def check():
    protected=read(OUT/'PROTECTED_BEFORE.json')
    bad=[p for p,h in protected.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    require(not bad,bad[:10],'PROTECTED_HASH_MISMATCH')
    return len(protected)

if __name__=='__main__':prepare()
