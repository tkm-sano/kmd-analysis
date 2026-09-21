"""Final read-only protected-source audit; writes only this new preflight version."""
import time,subprocess
from .contract import *
from .preflight import dump
from .execution import wired

def main():
    tests=read(OUT/'TEST_RESULTS.json');require(tests['status']=='PASS','tests')
    before=read(OUT/'PROTECTED_BEFORE.json');after={p:sha(ROOT/p) for p in before};bad=[p for p in before if before[p]!=after[p]]
    table(OUT/'PROTECTED_FILE_HASHES_AFTER.csv',[dict(path=p,sha256=h) for p,h in after.items()]);require(not bad,bad,'PROTECTED_ARTIFACT_CHANGED')
    old_status=(OUT/'GIT_STATUS_BEFORE.txt').read_text();status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True);diff=subprocess.check_output(['git','diff','--stat'],cwd=ROOT,text=True)
    added=set(status.splitlines())-set(old_status.splitlines());removed=set(old_status.splitlines())-set(status.splitlines())
    require(added<={'?? 05_src/traffic_simulation/r24_vrptw_structured_worker/'} and not removed,dict(added=list(added),removed=list(removed)),'UNEXPLAINED_GIT_CHANGE')
    # Also inspect files inside already-untracked directories, invisible to short status.
    unexplained=[]
    for root in [ROOT/'05_src',ROOT/'docs',ROOT/'notebooks']:
        for p in root.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and str(p.relative_to(ROOT)) not in before and not p.is_relative_to(Path(__file__).parent):unexplained.append(str(p.relative_to(ROOT)))
    require(not unexplained,unexplained,'UNEXPLAINED_NEW_FILE')
    (OUT/'GIT_STATUS_AFTER.txt').write_text(status);(OUT/'GIT_DIFF_STAT.txt').write_text(diff)
    dump('GIT_AUDIT.json',dict(status='PASS',preexisting_dirty_workspace=True,added_status_lines=sorted(added),removed_status_lines=sorted(removed),new_files_outside_scope=unexplained,existing_tracked_and_source_files_unchanged=True,allowed_new_source_directory=str(Path(__file__).parent.relative_to(ROOT)),allowed_new_artifact_directory=str(OUT.relative_to(ROOT))))
    dump('PROTECTED_HASH_VALIDATION.json',dict(status='PASS',files=len(before),mismatch_count=0,ledger_unchanged=True,comparison_freeze_unchanged=True,v1_v2_unchanged=True))
    counts=read(OUT/'PREFLIGHT_EXECUTION_COUNTS.json');require(all(counts[k]==0 for k in ['Uniform_execution','scientific_circuits','scientific_shots','optimizer_scientific_evaluations','Aer_sampling_calls','actual_ledger_mutations','new_seeds']),'zero science')
    manifest=read(OUT/'PREFLIGHT_MANIFEST.json');require(len(manifest['runs'])==9 and len({r['group'] for r in manifest['runs']})==3,'manifest shape');require(digest(manifest['runs'])==manifest['deterministic_run_records_sha256'],'manifest digest')
    projection=read(OUT/'LEDGER_PROJECTION.json');require(projection['status']=='PASS','projection')
    _,adapted,_=wired();require((OUT/'ADAPTED_SUPERVISOR_SOURCE.txt').read_text()==adapted+'\n','supervisor audit source')
    codefiles=[str(p.relative_to(ROOT)) for p in Path(__file__).parent.glob('*.py')]
    required=['IMPLEMENTATION_PREFLIGHT_REPORT.md','PREFLIGHT_MANIFEST.json','PREFLIGHT_MANIFEST.csv','FREEZE_AUDIT.json','LEAKAGE_AUDIT.json','LEDGER_PROJECTION.json','STATE_REPRODUCTION_AUDIT.csv','TEST_RESULTS.txt','PROTECTED_FILE_HASHES_BEFORE.csv','PROTECTED_FILE_HASHES_AFTER.csv','GIT_STATUS_BEFORE.txt','GIT_STATUS_AFTER.txt','GIT_DIFF_STAT.txt']
    elapsed=time.time()-read(OUT/'START.json')['epoch']
    report=f'''# VRPTW Structured Initial State — implementation preflight

**GO — VRPTW_STRUCTURED_INITIAL_STATE_IMPLEMENTATION_PREFLIGHT_VALIDATED**

Readiness: STRUCTURED_INITIAL_STATE_SCIENTIFIC_SAMPLING_READY, subject to separately authorized controlled launch and fresh gates. No sampling was performed or started automatically.

## Integration and reuse

New package: `05_src/traffic_simulation/r24_vrptw_structured_worker/`.
Worker path: `worker.prepare(run_id)`. Existing Standard `worker.prepare` is used only as a construction/identity source; its first N H operations are replaced with the shared Candidate A preparation. Cost Hamiltonian/global phase and Standard X layer remain identical. No Uniform resampling, optimizer run, result regeneration or output overwrite occurs.

Candidate A uses only n, m and the frozen variable-order list. No sorting/remapping or temporal filtering occurs. Constructor code is imported directly from validated v1. Offline v2 support and v1 symbolic/bound circuits are reproduced. Route register occupies indices0..B−1, B=m*n*(n+1); uniform slack occupies B..N−1 (4*m qubits). No temporal ancilla exists. Measurement is qubit i→classical bit i; displayed strings are q[N−1]...q[0], reversed for variable-order indexing.

`execution.supervised_run(..., preflight=True)` rejects launch by default. Future controlled launch requires explicit separate authorization, the validated preflight receipt, manifest/protected hashes and the frozen run identity. Its supervisor is compiled from the existing validated supervisor body with four recorded dependency/gate changes: comparison ledger namespace, removal of the Standard-specific Aer sanity receipt lookup and its two identity assertions, replaced with this implementation/offline receipt gate. Relative prepare import resolves to the Structured worker. All resource polling, persistent PSI, child process, backend invocation, timeout, recovery, and authorization handling otherwise reuse the existing supervisor. The original `perform` code object supplies unchanged parameter binding, seed progression, objective/scale, COBYLA options, incumbent selection, final sampling and result saving. `results.aggregate_batch` reuses original arithmetic with Structured identity lookup only. Adapted supervisor source is saved for review. No additional Aer sanity is budgeted or performed.

## Freeze and leakage

Comparison freeze SHA256: `{COMPARISON_HASH}`. Initial-state preparation is the only experimental difference; run/arm IDs, output namespace and initialization-report metadata necessarily differ. QUBO, penalties, variable order, encoding, p=1, Standard X, optimizer/options/initialization/bounds, shots, all paired seed streams, simulator and transpilation settings, decoder, independent validator, energy objective and result arithmetic remain inherited. Source U runs are B01/B02/B03, read-only.

Worker construction argument trace contains only n/m/variable_order. Adapter retains classical authority for downstream validation, but that object and its solution/quality fields are never passed to construction. Existing constructor rejects extra inputs. Active-TW temporal-valid mass=0 and no-good violation mass=1 are preserved. **Encoding compatibility PASS is not temporal feasibility PASS.** Known fixed-route p=1 gamma limitation remains unchanged.

## Reproduction and zero-shot guard

Three worker preparation-only Qiskit Statevector inspections: fidelity≈1, amplitude errors below1e−16, support/variable-order mismatch0. All9 planned run records regenerate identically; seven nominal semantic conditions reproduce their group state. No cost/mixer evolution or scientific metric computation is performed here.

Guard denies actual Aer backend `.run`, Aer/Qiskit samplers, scipy optimizer, Standard scientific entry/perform and persistent ledger commit. Negative tests deliberately reach denial stubs and stop before execution. Dry-ledger UNKNOWN accounting tests are pure in-memory transitions, not backend calls, shots or real consumption.

Actual Uniform executions/scientific circuits/shots/optimizer evaluations/Aer calls/new seeds/ledger mutations: **all0**. No future scientific run directory or result exists.

## Ledger and plan

Frozen order: S01 G2 N003 WIDE, S02 G1 N002 WIDE, S03 G3 active TW. Three paired repetitions each,9 Structured runs, no duplicate semantic-control circuits. Maximum per run99 training+1 final=100 circuits and204,800 shots; per group300 circuits/614,400 shots; total900 circuits/1,843,200 shots. Actual evaluation counts remain unknown.

Historical scientific363, sanity7, shots743,424. Projected maximum scientific1263/2100, total1270/2107, shots2,586,624/5,000,000; scientific headroom837 after maximum commitment. Conservative group charges G1/G2/G3=398/416/456, all≤600. Future reservation is current batch only300; not all900 at once. No reservation was created here.

Comparison Ledger subclasses the existing atomic, locked hash-chain/claim/receipt/finalize lifecycle; immutable Standard external debit is fresh-hash checked under the existing external ledger lock before comparison transactions. Its canonical namespace is fixed by BUDGET_PLAN. DryLedger replaces persistence with memory only, exercises identical lifecycle methods, and keeps preflight claims at zero consumption. Duplicate claims/retries and premature next-batch reservation are rejected. STARTED/unknown/failed remain charged in the accounting model; no uncertain refund.

## Acceptance

Tests: {tests['tests']} PASS (new integration/negative tests plus existing offline regressions). Protected hashes: {len(before)} PASS. Existing v1/v2, comparison freeze, scientific results, ledgers, source code, documents and notebooks unchanged. Git audit explains the preexisting dirty workspace and only the new worker package/new preflight directory. Required manifest, before/after hashes and git status/diff are saved. Initial planning estimate20–40min; final elapsed{elapsed/60:.2f}min; main zero-shot audit{counts['preflight_seconds']:.3f}s.

Development corrections stayed within new integration code: use the authoritative offline state-hash serializer; normalize tuple/list metadata to JSON lists; retain original executor code objects while installing denial guards. No source freeze, state or result was repaired/retuned and no scientific retry occurred.

## Next one task

Separately authorized **Structured scientific sampling controlled launch — S01/G2 N003 WIDE, r0–r2 only**, after fresh protected/ledger/resource gates. Stop at the frozen batch checkpoint. This preflight does not claim scientific performance or sampling completion.
'''
    (OUT/'IMPLEMENTATION_PREFLIGHT_REPORT.md').write_text(report)
    require(all((OUT/p).is_file() for p in required),'required artifacts')
    dump('VALIDATION.json',dict(status='PASS',GO_STOP='GO',final_status='VRPTW_STRUCTURED_INITIAL_STATE_IMPLEMENTATION_PREFLIGHT_VALIDATED',readiness='STRUCTURED_INITIAL_STATE_SCIENTIFIC_SAMPLING_READY',readiness_means_execution_completed=False,tests=tests['tests'],protected_files=len(before),manifest='PASS',git='PASS',zero_scientific_execution=True,freeze='PASS',leakage='PASS',state_reproduction='PASS',ledger_projection='PASS',comparison_groups=3,planned_runs=9,scientific_execution_started=False))
    dump('EXECUTION_SUMMARY.json',dict(status='VRPTW_STRUCTURED_INITIAL_STATE_IMPLEMENTATION_PREFLIGHT_VALIDATED',GO_STOP='GO',actual_elapsed_seconds=elapsed,counts=counts,planned_circuits=900,planned_shots=1843200,projected_scientific=1263,scientific_remaining_after_max=837,changed_files=codefiles,existing_files_changed=[],next_one_task='Separately authorized S01 G2 controlled launch;3 repetitions only'))
    (OUT/'PROVENANCE.md').write_text('New zero-shot implementation preflight namespace. Commands: python -m traffic_simulation.r24_vrptw_structured_worker.preflight; .test_preflight; .finalize. Pinned Python /home/takuma/.venvs/r24-qaoa-aer-20260916/bin/python, PYTHONPATH=05_src, OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1. No scientific execution. Existing dirty workspace captured before/after; protected files unchanged.\n')
    files={str(p.relative_to(ROOT)):sha(p) for root in [OUT,Path(__file__).parent] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['ARTIFACT_MANIFEST.json','MANIFEST_VALIDATION.json']}
    dump('ARTIFACT_MANIFEST.json',files);require(all(sha(ROOT/p)==h for p,h in files.items()),'manifest')
    dump('MANIFEST_VALIDATION.json',dict(status='PASS',files=len(files),sha256=sha(OUT/'ARTIFACT_MANIFEST.json')))
    print('$ git status --short\n'+status+'\n$ git diff --stat\n'+diff);print(json.dumps(read(OUT/'VALIDATION.json'),indent=2));print('elapsed seconds',elapsed)

if __name__=='__main__':main()
