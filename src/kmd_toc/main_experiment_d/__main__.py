"""Preparatory main-D entry point. Never launches B/C/D experiments."""
import argparse
import json
from .shots import prepare_trial, load_trial, run_main


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--output', required=True)
    prepare.add_argument('--trial-id', required=True)
    prepare.add_argument('--scale', choices=('S1', 'S2', 'S3'), required=True)
    prepare.add_argument('--branch-seeds', type=int, nargs=4, required=True)
    for action in ('audit', 'run'):
        sub.add_parser(action).add_argument('manifest')
    args = parser.parse_args()
    if args.action == 'prepare':
        print(prepare_trial(args.output, args.trial_id, args.scale, args.branch_seeds))
    elif args.action == 'audit':
        from .quantum import audit_trial
        print(json.dumps(audit_trial(args.manifest), indent=2))
    else:
        run_main(args.manifest)


if __name__ == '__main__':
    main()
