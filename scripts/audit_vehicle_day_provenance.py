"""Recreate measured-trip provenance/config alignment from saved small results."""
import argparse
import csv
import json
from pathlib import Path
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.generation import seed_plan


def main(source, output):
    source, out = Path(source), Path(output)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(source.glob('AOA_N*_B*_D.json')):
        r = json.loads(path.read_text())
        n, b = int(path.stem.split('_')[1][1:]), int(path.stem.split('_')[2][1:])
        p = small_problem(n, b)
        known = {t.customers for c in seed_plan(p) for t in c.trips} | {(i,) for i in p.base.customers}
        for step in r['trace']:
            sampled = {tuple(ids) for q in step['aoa']['quantum'] for ids in q['expanded_sampled_trips']}
            novel = sampled - known
            added = step['added']
            novel_days = sum(any(tuple(ids) in novel for ids in c['trips']) for c in added)
            assert all(any(tuple(ids) in sampled for ids in c['trips']) for c in added)
            rows.append({'case': path.stem, 'iteration': step['iteration'], 'novel_sampled_trips': len(novel),
                'negative_days_added': len(added), 'added_days_with_novel_measured_trip': novel_days,
                'added_days_only_known_measured_trips': len(added) - novel_days})
            known.update(tuple(ids) for c in added for ids in c['trips'])
    with (out / 'AOA_PROVENANCE.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    cfg = json.loads(Path('configs/toc_delivery_d/vehicle_day_validation_v1.json').read_text())
    checks = []
    for path in source.glob('INPUT_N*_B*.json'):
        data = json.loads(path.read_text())
        assert len(data['vehicles']) == cfg['vehicle_count']
        for v in data['vehicles']:
            for field, key in [('capacity','artificial_capacity_per_trip'),('loading_s','artificial_loading_s'),
                    ('preparation_s','artificial_preparation_s'),('ready_s','artificial_first_ready_s'),
                    ('shift_start_s','artificial_shift_start_s'),('shift_end_s','artificial_shift_end_s')]:
                assert v[field] == cfg[key]
        assert data['delta_s'] == cfg['time_grid_delta_s']
        assert all(q == cfg['parcel_count_per_customer'] for q in data['base']['demand'][1:])
        assert all(t == cfg['artificial_service_s'] for t in data['service_s'][1:])
        assert all(t == (0 if i == j else cfg['artificial_travel_s_per_arc'])
                   for i, row in enumerate(data['travel_s']) for j, t in enumerate(row))
        checks.append(path.name)
    with (out / 'INPUT_CONFIG_ALIGNMENT.json').open('x') as f:
        json.dump({'passed': True, 'inputs': checks}, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    main(args.input, args.output)
