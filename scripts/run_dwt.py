"""DWT limited experiments and analysis. Existing outputs are never overwritten."""

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
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'run', 'analyze'])
    parser.add_argument('--config', default='configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json')
    parser.add_argument('--phase', choices=['pilot', 'limited'], default='pilot')
    parser.add_argument('--registration')
    parser.add_argument('--historical-serial-reproduction', action='store_true', help='explicit historical single-core reproduction only')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if args.action != 'analyze' and not config.get('cpu_parallel', {}).get('enabled') and not args.historical_serial_reproduction:
        parser.error('New B/C/D runs require CPU parallel configuration; historical serial reproduction must be explicit')
    if args.action == 'run':
        actual_path = Path(args.registration or str(Path(config['output_root']) / (args.phase + '_REGISTERED.json')))
        if actual_path.exists() and not args.historical_serial_reproduction:
            actual = json.loads(actual_path.read_text())
            if any(s['method'] in ('B', 'C', 'D', 'D_CLASSICAL_CONTROL')
                   and not s['config'].get('cpu_parallel', {}).get('enabled') for s in actual['specs']):
                parser.error('Actual registration is historical serial; --historical-serial-reproduction is required')
    os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    from kmd_toc.dwt.experiment import register, run_registered
    from kmd_toc.dwt.analysis import analyze
    if args.action == 'register':
        print(register(args.config, args.phase))
    elif args.action == 'run':
        run_registered(args.registration or str(Path(config['output_root']) / (args.phase + '_REGISTERED.json')))
    else:
        print(json.dumps({k: v for k, v in analyze(config['output_root'], config).items()
                          if k not in ['rows', 'budget_epsilon_summary', 'dominance', 'weight_reference_sensitivity']}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
