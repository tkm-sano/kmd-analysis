"""Select saved D finals with an explicit C reference. Never starts optimization."""
import argparse
import json
from .selection import recover_and_select


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = recover_and_select(args.manifest, args.output)
    print(json.dumps({k: result[k] for k in ('status', 'selection_version', 'selected_branch_id', 'selection')}, indent=2))


if __name__ == '__main__':
    main()
