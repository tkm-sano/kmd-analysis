#!/usr/bin/env python3
"""Analyze saved pilot plans under the current D/W policy; never runs solvers."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(ROOT/'output/toc_delivery/non_time_variance_pilot_20261117_v1'))
    parser.add_argument('--output', required=True)
    parser.add_argument('--policy', default=str(ROOT/'configs/toc_delivery/dw_policy_20261117_v1.json'))
    args = parser.parse_args()
    from kmd_toc.dw import write_analysis
    result = write_analysis(args.source, args.output, args.policy)
    print(json.dumps({'policy_id': result['policy_id'], 'registered_attempts': len(result['rows']),
                      'output': str(Path(args.output).resolve()), 'hypothesis_status': result['hypothesis_status']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
