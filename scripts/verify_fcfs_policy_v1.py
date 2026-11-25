#!/usr/bin/env python3
"""Standard-library-only integrity check for frozen FCFS and base research v1."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args(argv)
    spec=importlib.util.spec_from_file_location('fcfs_frozen_policy',ROOT/'src/kmd_toc/fcfs_v1/policy.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.verify(args.root)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(result['status']!='PASS')


if __name__=='__main__':raise SystemExit(main())
