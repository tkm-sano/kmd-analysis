#!/usr/bin/env python3
"""Calibrate and externally validate the preregistered area-order candidate."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    if '--historical-reproduction' not in sys.argv:
        raise SystemExit('HISTORICAL_ENTRYPOINT: legacy A plans require --historical-reproduction; current A is an external administrative reference')
    sys.argv.remove('--historical-reproduction')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[key] = '1'
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    from kmd_toc.baseline_a.area_study import run
    model = run(args.data,args.output)
    print(json.dumps({'selected':model['selected_parameters'],'best_area':model['best_area_parameters'],
                      'calibration_routes':model['calibration_routes']},ensure_ascii=False))


if __name__=='__main__':
    main()
