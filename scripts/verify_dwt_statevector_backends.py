"""Small artificial implementation check, never a delivery research experiment.

Runs the real DWT registration and four-branch execution for both statevector
backends. Does not generate frozen demand, use study OD, or run S1/S2/S3.
"""
import argparse
import copy
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='new verification directory; never overwritten')
    args = parser.parse_args()
    os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                      NUMEXPR_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.common.models import save_problem
    from kmd_toc.dwt.experiment import register
    from kmd_toc.dwt.parallel import execute_parallel, cpu_profile
    from kmd_toc.dwt.worker import dump

    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=False)
    base = json.loads(Path('configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json').read_text())
    profile = cpu_profile(base)
    os.sched_setaffinity(0, set(profile['cpu_ids']))
    save_problem(artificial_problem(6, 2, 1), root/'inputs'/'ART_N6')
    checks, results, histories = [], [], {}
    def check(name, passed):
        checks.append({'check': name, 'passed': bool(passed)})
        dump(root/'CHECK_PROGRESS.json', checks)
        if not passed:
            raise AssertionError(name)

    for name in ['qiskit', 'qulacs']:
        config = copy.deepcopy(base)
        config['D']['statevector_backend'] = name
        config['cpu_parallel']['cpu_ids'] = profile['cpu_ids']
        config['input_root'] = str(root/'inputs')
        config['output_root'] = str(root/name)
        config['pilot'] = {'scenarios': ['ART_N6'], 'W_limits_min': [30],
                           'budgets_s': [30], 'repetitions': 1}
        config_path = root/f'{name}.json'
        dump(config_path, config)
        registration = register(config_path, 'pilot', methods=['D'])
        spec = json.loads(registration.read_text())['specs'][0]
        out = root/name/'trial'
        out.mkdir()
        dump(out/'spec.json', spec)
        # Uniform fresh-process preparation; every optimizer/input starts inside T.
        row = execute_parallel(spec, out, allow_import_only_fork=False)
        check(name+': usable verified plan', row['status'] == 'VALIDATED')
        check(name+': correct registered/executed backend',
              row['quantum_backend_environment'] == spec['quantum_backend_environment'])
        check(name+': four distinct processes', len({r['pid'] for r in row['parallel_branches']}) == 4)
        check(name+': one core per branch', all(len(r['cpu_affinity']) == 1 for r in row['parallel_branches'])
              and len({tuple(r['cpu_affinity']) for r in row['parallel_branches']}) == 4)
        check(name+': complete branches joined', all(r['status'] == 'VALIDATED' and r['children_joined']
                                                     for r in row['parallel_branches']))
        check(name+': all quantum work accounted', row['quantum_accounting_complete']
              and row['total_quantum_calls'] > 0
              and row['total_final_shots'] == sum(r['final_shots'] for r in row['parallel_branches']))
        check(name+': timing includes all branches', all(
              row['total_quantum_timing_s'][key] == sum(r['observed_quantum_timing_s'][key]
                                                        for r in row['parallel_branches'])
              for key in row['total_quantum_timing_s']))
        check(name+': exact parent T boundary', row['T_program_s'] == row['timing_events'][-1]['elapsed_s']
              and row['timing_events'][-1]['name'] == 'final_validation_end')
        check(name+': independent validators agree', row['validation']['feasible']
              and row['second_validation']['feasible'])
        per_branch = []
        for branch in range(4):
            quantum = [json.loads(p.read_text()) for p in sorted(
                (out/'branches'/str(branch)/'stages').glob('D_AOA_*.json'))]
            check(name+f': branch{branch} selected backend', bool(quantum) and all(
                q['statevector_backend'] == name and q['result']['statevector_backend'] == name
                and q['sampling_only_s'] is not None for q in quantum))
            per_branch.append([q['result']['history'] for q in quantum])
        histories[name] = per_branch
        results.append(row)
        dump(root/'RESULT_PROGRESS.json', [{k: v for k, v in r.items() if k != 'plan'} for r in results])

    check('all four branch training and sampled bitstrings unchanged', histories['qiskit'] == histories['qulacs'])
    check('same final D and W', (results[0]['D_km'], results[0]['W_min']) ==
          (results[1]['D_km'], results[1]['W_min']))

    # A killed/incomplete D branch must not falsely report zero quantum effort.
    failure = {**spec, 'trial_id': 'qulacs_tiny_budget', 'tau_s': 1e-7}
    out = root/'tiny_budget';out.mkdir()
    dump(out/'spec.json', failure)
    row = execute_parallel(failure, out, allow_import_only_fork=False)
    check('tiny budget cannot fabricate a plan', row['status'] != 'VALIDATED' and row['plan'] is None)
    check('tiny budget children reaped', all(r['children_joined'] for r in row['parallel_branches']))
    check('incomplete quantum timing is unknown', not row['quantum_accounting_complete']
          and row['total_quantum_timing_s'] is None and row['total_final_shots'] is None)
    dump(root/'VERIFICATION.json', {'scope': 'ART_N6 implementation check only; not a D/W/T performance experiment',
        'checks': checks, 'passed': sum(c['passed'] for c in checks),
        'all_passed': all(c['passed'] for c in checks),
        'results': [{k: v for k, v in r.items() if k != 'plan'} for r in results],
        'failure_case': {k: v for k, v in row.items() if k != 'plan'}})
    print(f'Verified {len(checks)} implementation checks; no S1/S2/S3 execution')


if __name__ == '__main__':
    main()
