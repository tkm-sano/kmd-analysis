#!/usr/bin/env python3
"""Bounded A v2 functional checks, sequential fresh processes; no main study."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    if '--historical-reproduction' not in sys.argv:
        raise SystemExit('HISTORICAL_ENTRYPOINT: legacy A plans require --historical-reproduction; current A is an external administrative reference')
    sys.argv.remove('--historical-reproduction')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--scenarios', nargs='+', choices=['S1', 'S2', 'S3'], default=['S1', 'S2', 'S3'])
    parser.add_argument('--input-root', default=None, help='Identical hash-pinned bundles may be relocated')
    parser.add_argument('--worker', choices=['S1', 'S2', 'S3'], help=argparse.SUPPRESS)
    parser.add_argument('--allocated-cpus', type=int, nargs=4, help=argparse.SUPPRESS)
    args = parser.parse_args()
    # Set before numpy and every native library is imported in parent/child.
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    preparation = time.perf_counter()
    if args.worker:
        if Path(args.output).exists():
            print('OUTPUT_ALREADY_EXISTS', file=sys.stderr)
            return 2
        try:
            if not args.allocated_cpus or not set(args.allocated_cpus) <= os.sched_getaffinity(0):
                raise ValueError('A_CPU_ALLOCATION')
            os.sched_setaffinity(0, {args.allocated_cpus[0]})
            from kmd_toc.dwt.setup import preload_dependencies
            from kmd_toc.baseline_a.program import execute, settings
            preload_dependencies()  # same import union as current B/C/D; no solver work
            cfg = settings()
            setup = {'dependency_and_affinity_setup_s': time.perf_counter() - preparation,
                     'allocated_cpu_ids': args.allocated_cpus, 'active_cpu_ids': sorted(os.sched_getaffinity(0)),
                     'native_thread_environment': {k: os.environ[k] for k in
                         ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')},
                     'native_solver_execution': False, 'python': sys.version, 'platform': platform.platform(),
                     'executable': sys.executable}
            row = execute(Path(args.input_root or ROOT / cfg['input_root']) / args.worker,
                          args.worker, args.output, setup=setup)
            return 0 if row['status'] == 'VALIDATED' else 1
        except Exception as error:
            out = Path(args.output)
            out.mkdir(parents=True, exist_ok=True)
            (out / 'process_failure.json').write_text(json.dumps({'status': 'SETUP_OR_EXPORT_ERROR',
                'type': type(error).__name__, 'message': str(error)}, ensure_ascii=False, indent=2) + '\n')
            return 1
    from kmd_toc.baseline_a.program import settings, dump, digest
    from kmd_toc.dwt.parallel import cpu_profile
    cfg = settings()
    cpus = cpu_profile({'threads': 4, 'cpu_parallel': {'workers': 4, 'native_threads_per_branch': 1,
                        'cpu_ids': None, 'coordinator_reserve_fraction': .2}})['cpu_ids']
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    scenarios = list(dict.fromkeys(args.scenarios))
    # Preserve the uncommitted implementation actually used for this run.
    import tarfile
    sources = sorted((ROOT / 'src/kmd_toc').rglob('*.py'))
    sources += [Path(__file__).resolve(), ROOT / 'configs/toc_delivery/a_provisional_program_v2.json',
                ROOT / 'configs/toc_delivery/a_rule_baseline_v1.json',
                ROOT / 'configs/toc_delivery/common_conditions_v1_1.json']
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    with tarfile.open(out / 'source_snapshot.tar.gz', 'x:gz') as archive:
        for p in sources:
            archive.add(p, arcname=str(p.relative_to(ROOT)))
    dump(out / 'RUN_DESIGN.json', {'registered_at': datetime.now(timezone.utc).isoformat(),
         'config': cfg, 'scenarios': scenarios, 'allocated_cpu_ids': cpus,
         'source_selection': 'provisional; NOT blinded; no result-dependent selection',
         'python': sys.executable, 'source_files_sha256': source_hashes, 'main_experiment': False})
    with (out / 'environment.txt').open('w') as handle:
        subprocess.run([sys.executable, '-m', 'pip', 'freeze'], stdout=handle, stderr=subprocess.STDOUT, check=True)
    rows = []
    for case in scenarios:
        for repetition in range(cfg['timing_check']['repetitions']):
            target = out / f'{case}-repeat{repetition + 1:02}'
            before = time.perf_counter()
            command = [sys.executable, str(Path(__file__).resolve()), '--historical-reproduction', '--worker', case,
                       '--allocated-cpus', *map(str, cpus), '--output', str(target)]
            if args.input_root:
                command += ['--input-root', str(Path(args.input_root).resolve())]
            try:
                with (out / f'{target.name}.log').open('w') as log:
                    process = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                             timeout=cfg['timing_check']['process_timeout_s'])
                path = target / 'metrics.json'
                row = json.loads(path.read_text()) if path.exists() else {
                    'status': 'PROCESS_FAILURE', 'D_km': None, 'W_min': None, 'T_program_s': None,
                    'error': json.loads((target / 'process_failure.json').read_text()) if (target / 'process_failure.json').exists() else {'returncode': process.returncode}}
                row['returncode'] = process.returncode
                if row['status'] == 'VALIDATED':
                    required = ('plan.json', 'trips.csv', 'metrics.json', 'validation.json', 'manifest.json')
                    complete = process.returncode == 0 and all((target / p).is_file() for p in required)
                    if complete:
                        manifest = json.loads((target / 'manifest.json').read_text())
                        complete = manifest['status'] == 'VALIDATED' and all(
                            digest(target / name) == expected for name, expected in manifest['products_sha256'].items())
                    if not complete:
                        row.update(status='OUTPUT_FAILURE', D_km=None, W_min=None, T_program_s=None,
                                   T_A_program=None, physical_feasible=False,
                                   error={'message': 'child exit or complete output/hash verification failed'})
            except subprocess.TimeoutExpired:
                target.mkdir(parents=True, exist_ok=True)
                row = {'status': 'PROCESS_TIMEOUT', 'D_km': None, 'W_min': None, 'T_program_s': None,
                       'T_attempt_wall_s': None, 'error': 'hard process timeout; no accepted metrics'}
                dump(target / 'process_failure.json', row)
            row.update(scenario_id=case, repetition=repetition + 1,
                       process_wall_including_setup_export_s=time.perf_counter() - before)
            dump(out / f'{target.name}.process.json', {k: v for k, v in row.items() if k not in ('validation', 'second_validation')})
            rows.append(row)
            print(json.dumps({k: row.get(k) for k in ['scenario_id', 'repetition', 'status', 'D_km', 'W_min', 'T_program_s']}, ensure_ascii=False), flush=True)
    summary = []
    for case in scenarios:
        subset = [r for r in rows if r['scenario_id'] == case]
        good = [r for r in subset if r['status'] == 'VALIDATED']
        plan_hashes = [digest(out / f'{case}-repeat{r["repetition"]:02}' / 'plan.json') for r in good]
        summary.append({'scenario_id': case, 'attempts': len(subset), 'validated': len(good),
                        'all_passed': len(good) == len(subset),
                        'same_plan_bytes': len(set(plan_hashes)) == 1 if len(good) == len(subset) else None,
                        'D_km': good[0]['D_km'] if good else None, 'W_min': good[0]['W_min'] if good else None,
                        'T_program_s_all': [r['T_program_s'] for r in subset],
                        'T_program_s_median_descriptive': statistics.median(r['T_program_s'] for r in good) if good else None,
                        'T_A_human_reference': None, 'J': None, 'reference_status': 'NOT_FROZEN',
                        'quantitative_representativeness': 'FAIL'})
    dump(out / 'SUMMARY.json', summary)
    unchanged = all(digest(ROOT / name) == expected for name, expected in source_hashes.items())
    dump(out / 'SOURCE_STABILITY.json', {'unchanged': unchanged, 'main_experiment': False})
    dump(out / 'OUTPUT_HASHES.json', {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob('*')) if p.is_file()})
    return 0 if unchanged and all(r['all_passed'] and r['same_plan_bytes'] for r in summary) else 1


if __name__ == '__main__':
    sys.exit(main())
