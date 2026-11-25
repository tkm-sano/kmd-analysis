#!/usr/bin/env python3
"""Frozen descriptive statistics/SD plots and internal MCSE; never runs solvers."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--no-figures',action='store_true')
    args=parser.parse_args()
    from kmd_toc.descriptive_v1.pipeline import write_analysis
    r=write_analysis(args.registration,args.output,figures=not args.no_figures)
    print(json.dumps({'version':r['version'],'data_role':r['data_role'],'formal_J':r['formal_J'],'formal_J_status':r['formal_J_status'],
                      'MDE':r['MDE'],'output':str(Path(args.output).resolve())},indent=2))


if __name__=='__main__':main()
