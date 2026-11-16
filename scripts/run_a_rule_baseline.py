#!/usr/bin/env python3
"""Run preregistered A rule conditions only; never overwrite existing outputs."""
import argparse
from kmd_toc.baseline_a.runner import run_study


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--inputs-root',help='Parent of validated common S1/S2/S3 bundles; no coordinate/OD fallback')
    parser.add_argument('--validation-only',action='store_true')
    args=parser.parse_args()
    print(run_study(args.output,inputs_root=args.inputs_root,validation_only=args.validation_only))


if __name__=='__main__':main()
