#!/usr/bin/env python3
"""Run the preregistered external order-component check; never runs A/B/C/D plans."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[key] = '1'
    allowed = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {allowed[0]})
    from kmd_toc.baseline_a.sequence_validation import run
    summary = run(args.data, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if any(row['failed_rows'] for row in summary.values()) else 0


if __name__ == '__main__':
    sys.exit(main())
