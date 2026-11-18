"""Read inherited evidence; freeze existing assets, never edit them."""
import json
import time
from pathlib import Path
from pilot import ROOT,DOC,OLD,read,digest,dump
start=time.perf_counter()
files=set()
for base in ('src/kmd_toc','scripts','configs/toc_delivery'):
    for p in (ROOT/base).rglob('*'):
        if p.is_file() and p.suffix in ('.py','.json','.yaml','.yml','.toml'):files.add(p)
for name in ('AGENTS.md','README.md','.gitignore'):files.add(ROOT/name)
for base in ('docs/research/termination_rules_20261116_v1','docs/research/comparison_design_20261116_v1',
    'output/toc_delivery/termination_rules_20261116_v1','output/toc_delivery/comparison_design_20261116_v1'):
    for p in (ROOT/base).rglob('*'):
        # Retain the full namespace untouched, but byte-audit the registered
        # settings, snapshots, result/plan files and top-level research records.
        # Historical per-evaluation traces are not reread just to hash them.
        if '__pycache__' in p.parts:continue
        if p.parent==ROOT/base or p.name in ('REGISTERED.json','MAIN_MANIFEST.json','RESULT.json','result.json','plan.json','SOURCE_SNAPSHOT.tar.gz','SETTINGS_LOCK.json'):
            if p.is_file():files.add(p)
old=read(OLD/'REGISTERED.json')
for c in old['cases']:
    for name in c['input']['files']:files.add(Path(c['input']['directory'])/name)
# Runtime external dependency and preserved provenance assets are also hashed at registration.
baseline={str(p.relative_to(ROOT)):digest(p) for p in sorted(files)}
dump(DOC/'BASELINE_HASHES.json',{'files':baseline,'elapsed_s':time.perf_counter()-start,'note':'existing source/config/README/AGENTS, frozen inputs, old top-level records, nested registered settings/snapshots/results/plans. Historical per-evaluation traces are preserved by write scope but not individually rehashed; no protected file edited'})
inspected=[]
required=('STOPPING_RULES.md','STOPPING_AUDIT.md','COUNTER_DEFINITIONS.json','FINAL_REPORT.md','REPRODUCE.md','COMPLETION_STATUS.json')
for name in required:
    p=ROOT/'docs/research/termination_rules_20261116_v1'/name
    text=p.read_text();inspected.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p),'bytes':len(text.encode()),'kind':'inherited rules/report'})
for p in (ROOT/'docs/research/comparison_design_20261116_v1/PROTOCOL.md',ROOT/'src/kmd_toc/comparison_v1/design.py',ROOT/'src/kmd_toc/comparison_v1/design_report.py',ROOT/'scripts/run_comparison_design_supplement.py',ROOT/'src/kmd_toc/termination_v1/runner.py',ROOT/'scripts/audit_termination_rules.py'):
    text=p.read_text();inspected.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p),'bytes':len(text.encode()),'kind':'prior protocol/analysis/runner'})
oldrows=[]
for run in old['runs']:
    d=OLD/'runs'/run['run_id'];r=read(d/'RESULT.json');plan=read(d/'plan.json')
    resources=[json.loads(line) for line in (d/'RESOURCE_SAMPLES.jsonl').read_text().splitlines()]
    branches=[]
    for b in r['branches']:
        stage=d/f"branch_{b['branch_id']:02d}"/'stages'
        ev=[json.loads(line) for line in (stage/'work.jsonl').read_text().splitlines()]
        branches.append({'branch_id':b['branch_id'],'work_events':len(ev),'termination_events':[e for e in ev if e['event'] in ('A_complete','Routing_end','CP_end')],
            'counts':b['counts'],'final_source':b.get('final_candidate_source')})
    oldrows.append({'run_id':r['run_id'],'scale':r['scale'],'method':r['method'],'D':r['D'],'W':r['W'],'T':r['T_program'],'adoptable':r['adoptable'],
        'trip_count':len(plan['trips']),'resource_records':len(resources),'branches':branches})
dump(DOC/'INHERITED_INSPECTION.json',{'inspected_paths':inspected,'old_manifest':str((OLD/'REGISTERED.json').relative_to(ROOT)),
    'old_snapshot_sha256':digest(OLD/'SOURCE_SNAPSHOT.tar.gz'),'functional_15_rows_for_history_only':oldrows,'used_for_new_variance_or_cost':False,
    'prior_regression_status':'termination FINAL_REPORT records 127 pass/2 failures; old time-limit tests not reinstated',
    'no_location_substitution_needed':True})
print(json.dumps({'protected_files':len(baseline),'old_rows_inspected':len(oldrows),'elapsed_s':time.perf_counter()-start}),flush=True)
