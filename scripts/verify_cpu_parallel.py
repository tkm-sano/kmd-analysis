"""Artificial 6/20-stop implementation checks only; never a research experiment."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)

    if args.prepare_only:
        from kmd_toc.baseline_a.fixtures import artificial_problem
        from kmd_toc.common.models import save_problem
        for n in [6, 20]:
            target = root / 'inputs' / f'ART_N{n}'
            if target.exists():
                raise FileExistsError(target)
            save_problem(artificial_problem(n, 2, 1), target)
        print('Artificial fixtures prepared only; no frozen demand or road OD read/written')
        raise SystemExit(0)

    from kmd_toc.dwt.setup import preload_dependencies
    from kmd_toc.dwt.parallel import execute_parallel
    from kmd_toc.dwt.standard import export_standard
    from kmd_toc.dwt.audit import audit
    from kmd_toc.dwt.worker import dump
    config_path = Path('configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json')
    config = json.loads(config_path.read_text())
    preload_s = preload_dependencies()  # this parent never executes a solver or circuit
    checks, rows = [], []
    def check(name, ok):
        checks.append({'check': name, 'passed': bool(ok)})
        if not ok:
            raise AssertionError(name)

    for n in [6, 20]:
        for method in ['B', 'C', 'D', 'D_CLASSICAL_CONTROL']:
            ident = f'CPU4_ART_N{n}_{method}'
            out = root / 'trials' / ident
            out.mkdir(parents=True, exist_ok=False)
            # The four internal seeds are derived independently for each external test.
            spec = {'trial_id': ident, 'scenario_id': f'ART_N{n}', 'instance_id': f'artificial_N{n}',
                    'method': method, 'phase': 'implementation_smoke', 'repetition_id': 0,
                    'input_dir': str(root / 'inputs' / f'ART_N{n}'), 'tau_s': 20, 'epsilon_W_min': 30,
                    'seeds': {'solver_seed': n * 100 + ['B', 'C', 'D', 'D_CLASSICAL_CONTROL'].index(method),
                              'quantum_seed': 7000 + n, 'validation_seed': None},
                    'config': config, 'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest()}
            dump(out / 'spec.json', spec)
            row = execute_parallel(spec, out, allow_import_only_fork=True)
            check(ident + ':usable verified plan', row['status'] == 'VALIDATED')
            check(ident + ':four actual distinct PIDs', len({b['pid'] for b in row['parallel_branches']}) == 4)
            check(ident + ':four distinct CPUs', len({tuple(b['cpu_affinity']) for b in row['parallel_branches']}) == 4
                  and all(len(b['cpu_affinity']) == 1 for b in row['parallel_branches']))
            check(ident + ':all processes reaped', all(b['children_joined'] for b in row['parallel_branches']))
            check(ident + ':all four branches ran solver', all(b['status'] == 'VALIDATED' for b in row['parallel_branches']))
            check(ident + ':actual overlapping search intervals',
                  max(json.loads((out / 'branches' / str(i) / 'progress.json').read_text())['start_perf_counter'] for i in range(4))
                  < min(json.loads((out / 'branches' / str(i) / 'progress.json').read_text())['start_perf_counter']
                        + row['parallel_branches'][i]['T_attempt_wall_s'] for i in range(4)))
            check(ident + ':parent T includes join and validation',
                  row['timing_events'][-1]['name'] == 'final_validation_end'
                  and row['T_program_s'] == row['timing_events'][-1]['elapsed_s'] <= spec['tau_s'])
            check(ident + ':root is one statistical trial', row['cpu_parallel_profile']['statistical_trial_count'] == 1)
            check(ident + ':all branch CPU accounted', row['all_branch_CPU_accounted'] and row['total_process_cpu_s'] >= row['process_cpu_s'])
            check(ident + ':quantum accounting includes unselected',
                  row['total_final_shots'] == sum(b['final_shots'] for b in row['parallel_branches'])
                  and (row['total_quantum_calls'] > 0) == (method == 'D'))
            row['trial_directory'] = str(out)
            row = export_standard(row, spec, out)
            check(ident + ':standard output complete', row['status'] == 'COMPLETE')
            rows.append({k: v for k, v in row.items() if k != 'plan'})
            dump(root / 'SMOKE_PROGRESS.json', rows)
            print(json.dumps({k: row.get(k) for k in ['trial_id', 'D_km', 'W_min', 'T_program_s', 'total_process_cpu_s', 'cpu_affinity']}, ensure_ascii=False), flush=True)

    # All-start failure must produce no fictitious standard plan.
    spec = {**spec, 'trial_id': 'CPU4_ZERO_BUDGET', 'method': 'B', 'tau_s': 1e-9}
    out = root / 'trials' / spec['trial_id']
    out.mkdir(exist_ok=False)
    dump(out / 'spec.json', spec)
    row = execute_parallel(spec, out, allow_import_only_fork=True)
    row['trial_directory'] = str(out)
    row = export_standard(row, spec, out)
    check('tiny budget fails without fake plan', row['status'] != 'COMPLETE' and not (out / 'plan.json').exists())
    check('tiny budget has no surviving children', all(b['children_joined'] for b in row['parallel_branches']))
    rows.append({k: v for k, v in row.items() if k != 'plan'})
    dump(root / 'SMOKE_RESULTS.json', rows)
    raw_audit = audit(root)
    dump(root / 'PARALLEL_SMOKE_VALIDATION.json', {'checks': len(checks), 'passed': sum(c['passed'] for c in checks),
         'details': checks, 'independent_raw_checks': raw_audit['checks'], 'independent_raw_passed': raw_audit['passed'],
         'uniform_dependency_setup_s': preload_s,
         'scope': 'artificial 6/20-stop implementation checks only; no S1/S2/S3 experiments or performance claims'})
    print('Actual parallel process checks', len(checks), 'raw-independent checks', raw_audit['checks'])


if __name__ == "__main__":
    main()
