"""Isolated guarded unit/regression harness; never execute old artifact writers."""
import os
import sys
import subprocess
import time
import tempfile
from .contract import *
from .ledger import atomic

def child(directory,modules):
    import unittest
    from unittest.mock import patch
    from qiskit_aer import AerSimulator
    from qiskit.quantum_info import Statevector
    sys.path.insert(0,str(ROOT/directory))
    with patch.object(AerSimulator,'run',side_effect=AssertionError('AER_FORBIDDEN')) as aer, \
         patch('scipy.optimize.minimize',side_effect=AssertionError('OPTIMIZER_FORBIDDEN')) as opt, \
         patch.object(Statevector,'from_instruction',side_effect=AssertionError('STATE_EVOLUTION_FORBIDDEN')) as state:
        suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
        if directory.endswith('r24_qaoa_initial_state_cross_condition_worker'):
            # Legacy fresh-run fixture predates the now-completed production runs.
            # Isolate only its completed-output lookup; run the real original lookup
            # against an empty temporary path. All assertions/claim logic unchanged.
            import test_cross_worker as legacy
            original_test=legacy.WorkerTests.test_dry_no_aer_optimizer_statevector
            original_lookup=legacy.w.completed_result
            def isolated_test(self):
                with tempfile.TemporaryDirectory() as td:
                    def isolated_lookup(p):
                        view=dict(p,plan=dict(p['plan'],output_path=str(Path(td)/p['plan']['run_id'])))
                        return original_lookup(view)
                    with patch.object(legacy.w,'completed_result',side_effect=isolated_lookup):original_test(self)
            legacy.WorkerTests.test_dry_no_aer_optimizer_statevector=isolated_test
            suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(status='PASS' if result.wasSuccessful() and not any([aer.call_count,opt.call_count,state.call_count]) else 'FAIL',tests_run=result.testsRun,
        failures=[dict(test=str(t),detail=d) for t,d in result.failures+result.errors],skipped=result.skipped,
        forbidden_call_attempts=dict(Aer=aer.call_count,optimizer=opt.call_count,state_evolution=state.call_count),
        fixture_isolation='Legacy initial dry-run completed-output lookup redirected to empty temp path; original lookup logic and assertions unchanged' if directory.endswith('r24_qaoa_initial_state_cross_condition_worker') else None)
    print('TEST_RESULT_JSON='+json.dumps(report));return 0 if report['status']=='PASS' else 1

def main():
    jobs=[('unit','05_src',['traffic_simulation.r24_vrptw_qaoa_worker.test_worker']),
      ('cvrp_cross_worker','05_src/traffic_simulation/r24_qaoa_initial_state_cross_condition_worker',['test_cross_worker']),
      ('reservation_claim','05_src/traffic_simulation/r24_qaoa_ablation_worker',['test_worker','test_reservation_claim']),
      ('resource_gates','05_src/traffic_simulation/r24_qaoa_resource_gate_redesign',['test_gates']),
      ('cvrp_qubo_decoder','05_src/traffic_simulation/validation',['test_r24_direct_qubo','test_r24_required_input_guards']),
      ('vrptw_validator','05_src',['traffic_simulation.validation.test_r24_vrptw','traffic_simulation.validation.test_r24_vrptw_milp']),
      ('vrptw_encoding','05_src',['traffic_simulation.r24_vrptw_quantum_encoding_preflight.test_encoding'])]
    attempts=read(OUT/'TEST_ATTEMPTS.json') if (OUT/'TEST_ATTEMPTS.json').exists() else []
    previous={n:read(OUT/n) for n in ['UNIT_TEST_RESULTS.json','REGRESSION_TEST_RESULTS.json'] if (OUT/n).exists()}
    if previous:attempts.append(previous);atomic(OUT/'TEST_ATTEMPTS.json',attempts)
    reports=[]
    for name,directory,modules in jobs:
        start=time.monotonic()
        p=subprocess.run([sys.executable,'-m',__package__+'.run_tests','--child',directory,*modules],cwd=ROOT,text=True,capture_output=True,timeout=180)
        (OUT/(name+'_TEST_LOG.txt')).write_text(p.stdout+p.stderr)
        lines=[line for line in p.stdout.splitlines() if line.startswith('TEST_RESULT_JSON=')]
        report=json.loads(lines[-1].split('=',1)[1]) if lines else dict(status='FAIL',tests_run=0,error=p.stderr)
        report.update(name=name,seconds=time.monotonic()-start,returncode=p.returncode);reports.append(report)
        print(json.dumps({k:report[k] for k in ['name','status','tests_run','seconds']}),flush=True)
    atomic(OUT/'UNIT_TEST_RESULTS.json',reports[0])
    atomic(OUT/'REGRESSION_TEST_RESULTS.json',dict(status='PASS' if all(r['status']=='PASS' for r in reports[1:]) else 'FAIL',
        tests_run=sum(r['tests_run'] for r in reports[1:]),suites=reports[1:],scientific_execution=0,
        exclusion='All legacy artifact-writing main entry points and Aer scientific execution excluded; no old files rewritten'))
    return int(any(r['status']!='PASS' for r in reports))

if __name__=='__main__':raise SystemExit(child(sys.argv[2],sys.argv[3:]) if len(sys.argv)>1 and sys.argv[1]=='--child' else main())
