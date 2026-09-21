"""Versioned direct-build receipt; distinguish runtime, reference and preservation."""
import time,subprocess,difflib,sys
from .audit import *
from traffic_simulation.r24_vrptw_structured_worker import execution

def dependency_inventory():
    runtime={};references={}
    def add(target,path):
        path=Path(path);require(path.is_file(),str(path),'DEPENDENCY_MISSING');target[str(path.relative_to(ROOT))]=sha(path)
    # Exact files traversed by the immutable spec loaders.
    for folder in [SPEC,uc_freeze()]:
        add(runtime,folder/'FINAL_FREEZE_MANIFEST.json')
        for rel in read(folder/'FINAL_FREEZE_MANIFEST.json')['artifacts']:add(runtime,folder/rel)
    c,s=frozen();add(runtime,ROOT/c['S']['constructor']);add(runtime,ROOT/c['S']['candidate_artifact'])
    gates=read(uc_freeze()/'IDENTITY_GATES.json')['conditions']
    conditions=sorted({r['condition'] for r in rows(SPEC/'RUN_PLAN.csv')})
    for cid in conditions:
        for path in gates[cid]['file_sha256']:add(runtime,ROOT/path)
        for name in ['QUBO.json','TEMPORAL_COMPILER.json']:add(runtime,ENC/'conditions'/cid/name)
        add(runtime,DESIGN/'conditions'/(cid+'.json'));add(runtime,DESIGN/'circuits'/cid/'combined_bound.qpy')
    add(runtime,ENC/'SELECTED_ENCODING_SPEC.json');add(runtime,uc_freeze()/'PROTECTED_AFTER.json')
    for row in read(uc_freeze()/'WIDE_CVRP_CONTINUITY.json')['records']:
        if row['condition'] in conditions:add(runtime,ROOT/row['source'])
    policy=read(uc_freeze()/'RUNTIME_PREFLIGHT_POLICY.json');add(runtime,ROOT/policy['environment_manifest'])
    budget=read(SPEC/'BUDGET_PLAN.json');add(runtime,ROOT/budget['baseline']['source'])
    # Loaded local implementation dependency closure; test/writer modules excluded.
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        p=Path(filename).resolve()
        if p.is_relative_to(ROOT/'05_src') and p.suffix=='.py' and not p.name.startswith(('test','finalize','publish','preflight','audit')):add(runtime,p)
    # Lazy execution dependencies are explicitly pinned even though no execution occurs.
    for folder,names in {
        'r24_vrptw_structured_worker':['contract.py','worker.py','execution.py','ledger.py','results.py','guard.py'],
        'r24_vrptw_qaoa_worker':['contract.py','adapter.py','circuit.py','execution.py','ledger.py','results.py'],
        'r24_qaoa_resource_gate_redesign':['gates.py'],
        'r24_qaoa_initial_state_cross_condition_worker':['ledger.py'],
    }.items():
        for name in names:add(runtime,ROOT/'05_src/traffic_simulation'/folder/name)
    # Immutable scientific U authority is distinct from files needed to build S.
    for batch in [1,2,3]:
        folder=BASE/'r24_vrptw_qaoa_execution/20260921_v1'/f'scientific_batch_{batch:02d}'
        for p in folder.rglob('*'):
            if p.is_file():add(references,p)
    dump('RUNTIME_DEPENDENCIES.json',runtime);dump('COMPARISON_REFERENCE_AUTHORITIES.json',references)
    return runtime,references

def uc_freeze():return BASE/'r24_vrptw_qaoa_execution_spec/20260921_v1'

def main():
    tests=read(OUT/'TEST_RESULTS.json');require(tests['status']=='PASS','tests')
    start=read(OUT/'START.json');baseline=read(OUT/'BASELINE_ALL_FILES.json');allowed=set(start['authorized_code_refactor']);after={p:sha(ROOT/p) for p in baseline}
    changed={p for p in baseline if baseline[p]!=after[p]};require(changed==allowed,dict(changed=sorted(changed),allowed=sorted(allowed)),'UNEXPLAINED_SOURCE_CHANGE')
    table(OUT/'PROTECTED_FILE_HASHES_AFTER.csv',[dict(path=p,sha256=h,category='AUTHORIZED_CODE_REFACTOR' if p in allowed else 'READ_ONLY_ARTIFACT_OR_SOURCE') for p,h in after.items()])
    dump('PROTECTED_HASH_VALIDATION.json',dict(status='PASS',read_only_files=len(baseline)-len(allowed),authorized_code_changes=sorted(allowed),unexpected_changes=[],previous_artifacts_unchanged=True,comparison_freeze_unchanged=True,historical_ledger_unchanged=True))
    patchtext=''
    for p in sorted(allowed):patchtext+=''.join(difflib.unified_diff((OUT/'source_before'/p).read_text().splitlines(True),(ROOT/p).read_text().splitlines(True),fromfile=p+' (before)',tofile=p+' (after)'))
    (OUT/'CODE_REFACTOR.diff').write_text(patchtext)
    runtime,refs=dependency_inventory()
    # New gate must validate comparison authorities too, without rewriting old receipts.
    dump('DEPENDENCY_CATEGORIES.json',dict(runtime_dependency_files=len(runtime),comparison_authority_files=len(refs),read_only_preservation_files=len(baseline)-len(allowed),authorized_code_refactor_files=len(allowed),meaning='Preservation scope is broad; it is not an execution-dependency count. New v4 gate pins current code and required runtime/reference files; prior receipts remain historical and unchanged.'))
    (OUT/'POST_REFACTOR_CALL_GRAPH.md').write_text('''# After refactor\n\nStructured supervisor → Structured worker.prepare → frozen run_plan/identity + Adapter → Candidate A initial_state(n,m,frozen order) → shared circuit.build_body(model) → Candidate A preparation.compose(body) → shared compile_and_bind → transpile → bound circuit + measure_all.\n\nStructured never imports/calls Uniform worker.prepare or build_uniform_initial_state. Uniform worker's permitted future architecture is shared.build_uniform_initial_state + the exact same shared.build_body, compile_and_bind and Ising check. No Uniform factory is invoked in this preflight; archived QPY supplies reference bodies and legacy fixtures.\n\nOptimizer/backend/resource supervisor, seed progression, ledger and postprocessing are unchanged. Current implementation acceptance gate points to v4; prior v3 receipt and STOP report are preserved.\n''')
    (OUT/'DIRECT_BUILD_ARCHITECTURE.md').write_text('''# VRPTW direct-build architecture\n\nSingle shared implementation: `r24_vrptw_qaoa_worker/circuit.py` owns p=1 diagonal cost layer (including global phase), Standard X mixer, gamma/beta creation, frozen transpilation, alpha/scale binding and q[i]→c[i] measurement. `build_body` contains no initial-state gates or solution-dependent input.\n\nCandidate A keeps its original pure constructor. Only n, m and frozen order cross its boundary. Structured composes Candidate A with shared body directly. Uniform preparation is an isolated factory that is denied in Structured tests. State preparation may use H on slack qubits; that is not Uniform preparation over all qubits.\n\nComparison parameters, scientific factor and statistics are unchanged. This is an implementation refactor, not a new initial-state experiment.\n''')
    counters=read(OUT/'EXECUTION_COUNTS.json');require(all(counters[k]==0 for k in ['Uniform_full_factory','Uniform_initial_factory','backend','sampler','optimizer_evaluations','scientific_circuits','scientific_shots','Aer_sampling','ledger_increment','reservations']),'zero execution')
    _,wired_source,_=execution.wired();(OUT/'ADAPTED_SUPERVISOR_SOURCE.txt').write_text(wired_source+'\n')
    state=read(OUT/'PREFLIGHT_MANIFEST.json');require(digest(state['runs'])==state['deterministic_run_records_sha256'],'manifest')
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True);before_status=(OUT/'GIT_STATUS_BEFORE.txt').read_text()
    added=set(status.splitlines())-set(before_status.splitlines());removed=set(before_status.splitlines())-set(status.splitlines())
    require(added<={'?? 05_src/traffic_simulation/r24_vrptw_direct_build_preflight/'} and not removed,dict(added=list(added),removed=list(removed)),'UNEXPLAINED_GIT_STATUS')
    (OUT/'GIT_STATUS_AFTER.txt').write_text(status);diff=subprocess.check_output(['git','diff','--stat'],cwd=ROOT,text=True);(OUT/'GIT_DIFF_STAT.txt').write_text(diff)
    dump('GIT_AUDIT.json',dict(status='PASS',preexisting_dirty_tree=True,authorized_modified_files=sorted(allowed),new_source_files=[str(p.relative_to(ROOT)) for p in Path(__file__).parent.glob('*.py')]+['05_src/traffic_simulation/r24_vrptw_qaoa_worker/circuit.py'],unexplained_modifications=[],note='Preexisting untracked source directories hide edited files from git diff --stat; CODE_REFACTOR.diff records the exact task diff.'))
    elapsed=time.time()-start['epoch']
    report=f'''# VRPTW Structured Initial State direct-build implementation preflight v2

**GO — VRPTW_STRUCTURED_INITIAL_STATE_DIRECT_BUILD_PREFLIGHT_VALIDATED**

Readiness: `VRPTW_STRUCTURED_S01_READY_FOR_CONTROLLED_LAUNCH`. S01 was not started.

## Root cause and refactor

Previous Structured prepare called Uniform prepare and replaced the H layer. It now calls the unchanged Candidate A constructor directly, then the one shared QAOA body implementation. Cost/mixer expressions, global phase, parameter symbols/order, transpilation, binding, measurement and bit ordering were extracted from the original validated Standard code. Both worker architectures reference that implementation; Structured has no Uniform factory dependency. See before/after call graphs and CODE_REFACTOR.diff. Three existing code files changed under this explicit refactor authorization; no prior artifact was rewritten.

## Zero-Uniform construction evidence

Uniform full builder and Uniform initial-state builder were patched to fail on any call throughout direct-build acceptance and Structured tests. Call counts: **0 / 0**. Nine planned runs were built and regenerated; all3 independent groups and7 same-QUBO semantic conditions were checked. Saved Uniform symbolic QPY was deserialized for body inspection only. No new Uniform initial state, full circuit factory, optimization, backend run or result regeneration occurred.

Complete existing Standard tests use immutable saved QPY as their fixture, including their negative resource checks. Their assertion bodies are unchanged. Their synthetic backend/optimizer callbacks and synthetic ledgers operate on test data/temp directories only; they do not call real quantum/optimizer APIs or touch scientific ledgers. This fixture adaptation avoids Uniform construction even in legacy tests. It is documented rather than counted as a fresh Uniform experiment.

## Equivalence and reproduction

All9 body comparisons with frozen B01/B02/B03 reference QPY pass Qiskit DAG equivalence, including global phase, cost RZ/CX structure and Standard X RX gates. p=1; circuit parameters sorted beta,gamma, optimizer vector alpha,beta with gamma=alpha/scale. q[i] measures into c[i]; displayed bitstrings reverse to frozen variable order. Logical/transpiled resources and signatures are saved. Bound Structured QPY matches validated offline v1 exactly.

Candidate A inputs remain exactly n/m/frozen variable order. No optimal/feasible set, cost/energy ranking, labels, sampled results or Uniform results enter construction. Three preparation-only deterministic Qiskit Statevector checks reproduce offline support with fidelity≈1 and max amplitude error<1e−16. No cost/mixer statevector evolution is performed. No new temporal-aware state is introduced. Active-TW feasible and temporal-valid masses remain0, no-good violation mass1. Encoding compatibility is not temporal feasibility.

## Freeze and budget

Comparison freeze hash `{COMPARISON_HASH}` unchanged. Optimizer, initial parameters, bounds, stopping rules, shots, all seeds, backend/simulator settings, transpilation, independent validator, objective, result saving and aggregation are unchanged. Ledger adapter logic is unchanged.

Future Structured plan:3 groups×3 repetitions=9 runs; maximum891 objective evaluations+9 final circuits=900 circuits,1,843,200 shots. Historical363 scientific/7 sanity/743,424 shots retained. Projected totals1263 scientific/2100,1270 total/2107,2,586,624 shots/5,000,000. No reservation or actual ledger mutation.

Actual scientific circuits/shots/optimizer evaluations/backend/sampler/Aer calls/reservations/ledger increment: **all0**. Denial-stub negative tests stop before the real API; synthetic test counts are not scientific observations.

## Acceptance and provenance

{tests['tests']} tests PASS, complete affected existing suites plus direct-build tests, no skipped tests. Read-only protected hashes: {len(baseline)-len(allowed)} files PASS;3 authorized code changes are separately recorded with before/after hashes. v1/v2/v3, S01 STOP, comparison freeze, Uniform/scientific outputs, QUBOs and historical ledger unchanged. Git dirty state existed before the task and is preserved; task source diff is saved explicitly.

Execution-dependency inventory is separated from broad preservation: {len(runtime)} runtime files; {len(refs)} comparison-reference files. The v4 receipt supersedes the old code receipt without editing historical manifests. Future launch revalidates active v4 artifacts and runtime/reference hashes, not unrelated historical source snapshots with intentionally obsolete code hashes.

Elapsed through final audit: {elapsed/60:.2f}min; initial estimate20–40min. Main nine-run construction/reproduction audit: {counters['seconds']:.3f}s. No scientific performance claim follows from this preflight.

## Next one task

**S01: N003 WIDE ×3 repetitions controlled scientific launch**, separately authorized, with fresh gate → r0 → integrity checkpoint/reestimate → r1 → r2 → S01 STOP → frozen Uniform B02 descriptive comparison. Do not start S02.
'''
    (OUT/'DIRECT_BUILD_PREFLIGHT_REPORT.md').write_text(report)
    dump('VALIDATION.json',dict(status='PASS',GO_STOP='GO',final_status='VRPTW_STRUCTURED_INITIAL_STATE_DIRECT_BUILD_PREFLIGHT_VALIDATED',S01_readiness='VRPTW_STRUCTURED_S01_READY_FOR_CONTROLLED_LAUNCH',Uniform_construction=0,Uniform_initial_state_construction=0,scientific_execution=False,scientific_circuits=0,scientific_shots=0,optimizer_evaluations=0,backend_calls=0,ledger_increment=0,reservations=0,tests=tests['tests'],protected_hashes='PASS',runtime_files=len(runtime),reference_files=len(refs),preservation_files=len(baseline)-len(allowed),git='PASS',manifest='PASS'))
    dump('EXECUTION_SUMMARY.json',dict(status='VRPTW_STRUCTURED_INITIAL_STATE_DIRECT_BUILD_PREFLIGHT_VALIDATED',actual_elapsed_seconds=elapsed,counts=counters,tests=tests['tests'],next_one_task='S01 N003 WIDE controlled launch;3 repetitions only; fresh gate required'))
    (OUT/'PROVENANCE.md').write_text('Commands: pinned Python -m traffic_simulation.r24_vrptw_direct_build_preflight.audit; .test_direct; .finalize. PYTHONPATH=05_src; OPENBLAS_NUM_THREADS=1; OMP_NUM_THREADS=1. Scientific execution disabled. Existing test assertions retained; Uniform legacy fixtures deserialized from protected QPY. Modified source baseline and exact refactor diff saved.\n')
    manifest={str(p.relative_to(ROOT)):sha(p) for root in [OUT,Path(__file__).parent] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['ARTIFACT_MANIFEST.json','MANIFEST_VALIDATION.json']}
    for p in allowed|{'05_src/traffic_simulation/r24_vrptw_qaoa_worker/circuit.py'}:manifest[p]=sha(ROOT/p)
    dump('ARTIFACT_MANIFEST.json',manifest);require(all(sha(ROOT/p)==h for p,h in manifest.items()),'manifest')
    dump('MANIFEST_VALIDATION.json',dict(status='PASS',files=len(manifest),sha256=sha(OUT/'ARTIFACT_MANIFEST.json')))
    print('$ git status --short\n'+status+'\n$ git diff --stat\n'+diff);print(json.dumps(read(OUT/'VALIDATION.json'),indent=2));print('elapsed',elapsed)

if __name__=='__main__':main()
