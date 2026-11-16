"""Run only independent small CVRP benchmarks; no S1/S2/S3 planning entry."""
import argparse
from kmd_toc.column_generation.experiment import execute

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/toc_delivery_d/huang_reference_v1.json')
    parser.add_argument('--output', required=True, help='New run directory; outputs never overwritten')
    args = parser.parse_args()
    execute(args.config, args.output)
