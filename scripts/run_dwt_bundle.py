"""One import-only parent for small validation, registration and limited trials."""

# 2026-11-17: this entry point retains the historical timing-based contract.
# Check before imports so rejection cannot initialize solvers or write files.
if __name__ == "__main__":
    import sys as _history_sys
    if "--historical-reproduction" in _history_sys.argv:
        _history_sys.argv.remove("--historical-reproduction")
    elif any(arg in _history_sys.argv for arg in ("--help", "-h")):
        print("Historical entry point. Current analysis: scripts/analyze_dw.py. "
              "Use --historical-reproduction --help for the previous command options.")
        raise SystemExit(0)
    else:
        raise SystemExit("HISTORICAL_ENTRYPOINT: use scripts/analyze_dw.py for current D/W analysis; "
                         "pass --historical-reproduction only to reproduce the previous study")

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json')
    parser.add_argument('--historical-serial-reproduction', action='store_true')
    parser.add_argument('--include-limited', action='store_true', help='also register/run the explicitly configured limited cohort; default is small validation only')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if not config.get('cpu_parallel', {}).get('enabled') and not args.historical_serial_reproduction:
        parser.error('New runs require CPU parallel configuration')
    if config.get('cpu_parallel', {}).get('enabled') and config['threads'] != config['cpu_parallel']['workers']:
        raise ValueError('CPU budget must equal the explicitly configured parallel workers')
    os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    from kmd_toc.dwt.experiment import register, run_registered
    from kmd_toc.dwt.analysis import analyze
    from kmd_toc.dwt.audit import audit

    root = Path(config['output_root'])
    root.mkdir(parents=True, exist_ok=True)
    pilot = register(args.config, 'pilot')
    pilot_results = run_registered(pilot)
    analyze(root, config)
    report = audit(root)
    print('Small-road independent checks', report['passed'], report['checks'], flush=True)
    for method in ['B', 'C', 'D']:
        if not any(r['method'] == method and r['status'] == 'COMPLETE' for r in pilot_results):
            raise RuntimeError('PILOT_HOLD:' + method)
    if not args.include_limited:
        print('Small validation only; limited/main experiments were not requested', flush=True)
        sys.exit(0)
    limited = register(args.config, 'limited')
    subprocess.run([sys.executable, '-B', 'scripts/register_dwt_controls.py', str(root)], check=True)
    run_registered(limited)
    run_registered(root / 'control_REGISTERED.json')
    run_registered(root / 'baseline_REGISTERED.json')
    analyze(root, config)
    report = audit(root)
    print('Final independent checks', report['passed'], report['checks'], flush=True)


if __name__ == "__main__":
    main()
