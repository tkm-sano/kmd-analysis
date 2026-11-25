"""python -m kmd_toc.d_local_design {validate,benchmark,coverage,select,report,all}."""
import argparse
from pathlib import Path
from . import pipeline as p


def main():
    parser = argparse.ArgumentParser(description='Design validation only; production experiments are never authorized.')
    parser.add_argument('stage', choices=['validate', 'benchmark', 'coverage', 'select', 'report', 'all', '_worker'])
    parser.add_argument('job', nargs='?')
    parser.add_argument('--output', type=Path, default=p.ROOT / 'output/d_local_design/validation_v1')
    args = parser.parse_args()
    if args.stage == '_worker':
        p.worker(args.job)
        return
    out, config = p.init(args.output)
    stages = ['validate', 'benchmark', 'coverage', 'select', 'report'] if args.stage == 'all' else [args.stage]
    for stage in stages:
        if stage == 'report':
            from .report import report
            report(out)
        else:
            getattr(p, stage)(out, config)
        print(stage + ': evidence saved to ' + str(out), flush=True)


if __name__ == '__main__':
    main()
