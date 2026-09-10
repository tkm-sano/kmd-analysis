from __future__ import annotations

import argparse, csv, hashlib, json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    config_path = ROOT / args.config
    cfg = yaml.safe_load(config_path.read_text())
    out = ROOT / cfg['output_root'] / args.run_id
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f'output exists and is non-empty: {out}')
    out.mkdir(parents=True, exist_ok=True)
    spec_path = ROOT / cfg['source_spec_row']
    specs = list(csv.DictReader(spec_path.open(newline='')))
    rows = [r for r in specs if r['scenario_vehicle_id'] == cfg['vehicle_id']]
    if len(rows) != 1:
        raise SystemExit('vehicle specification row is not unique')
    spec = rows[0]
    battery = float(cfg['battery_capacity_kwh'])
    catalog_range = float(cfg['catalog_range_km'])
    initial = float(cfg['initial_soc'])
    minimum = float(cfg['minimum_soc'])
    rate = battery / catalog_range
    operational = battery * (initial - minimum)
    record = {
        'vehicle_id': cfg['vehicle_id'], 'vehicle_class': cfg['vehicle_class'],
        'fleet_size': int(cfg['fleet_size']), 'fleet_size_classification': 'ASSUMED',
        'fleet_size_assumption_reason': cfg['fleet_size_reason'],
        'payload_capacity_kg': float(cfg['payload_capacity_kg']), 'payload_classification': 'OBSERVED',
        'payload_source': spec['source_id'], 'payload_unit': 'kg',
        'battery_capacity_kwh': battery, 'battery_classification': 'OBSERVED',
        'battery_source': spec['source_id'], 'battery_unit': 'kWh',
        'operational_available_energy_kwh': operational, 'operational_available_energy_classification': 'COMPUTED',
        'operational_available_energy_transformation': 'battery_capacity_kwh * (initial_soc - minimum_soc)',
        'energy_consumption_kwh_per_km': rate, 'energy_classification': 'COMPUTED_APPROXIMATION',
        'energy_source': f'{spec["source_id"]}; battery_capacity_kwh/catalog_range_km',
        'energy_unit': 'kWh/km', 'energy_formula': cfg['energy_formula'],
        'catalog_range_km': catalog_range, 'catalog_range_classification': 'OBSERVED',
        'initial_soc': initial, 'initial_soc_classification': 'ASSUMED',
        'minimum_soc': minimum, 'minimum_soc_classification': 'ASSUMED',
        'soc_unit': 'ratio_0_to_1',
        'soc_assumption_reason': 'external EVRP precedent supports full-charge departure; 20% lower bound supports reserve/deep-discharge avoidance; not manufacturer-specific',
        'final_soc_requirement_enabled': bool(cfg['final_soc_requirement_enabled']),
        'final_soc_requirement': cfg['final_soc_requirement'],
        'depot_return_minimum_soc_applies': bool(cfg['depot_return_minimum_soc_applies']),
        'soc_constraint_semantics': cfg['soc_constraint_semantics'],
        'maximum_operating_time_enabled': bool(cfg['maximum_operating_time_enabled']),
        'maximum_operating_time_min': cfg['maximum_operating_time_min'],
        'vehicle_access_classification': 'ASSUMED', 'vehicle_access_source': 'managed_urban_ev_delivery_v1',
        'vehicle_access_reason': 'SUMO delivery class and R09 accepted edge permission',
        'fixture_n': 10, 'is_production_problem_size': False,
    }
    definition = out / 'vehicle_definition.csv'
    with definition.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(record)); w.writeheader(); w.writerow(record)
    inputs = {}
    for key in ['source_spec_row','source_soc_parameters','source_vehicle_profile','source_depot_validation']:
        p = ROOT / cfg[key]; inputs[key] = {'path': cfg[key], 'sha256': sha256(p)}
    manifest = {'schema_version': cfg['schema_version'], 'run_id': args.run_id,
                'fixture': {'n': 10, 'is_production_problem_size': False},
                'source': {'vehicle_specification': spec, 'inputs': inputs},
                'transformations': {'energy': cfg['energy_formula'], 'operational_available_energy': record['operational_available_energy_transformation']},
                'soc_external_precedents': cfg['soc_external_precedents'],
                'soc_sensitivity_candidates': cfg['soc_sensitivity_candidates'],
                'output': {'vehicle_definition.csv': sha256(definition)},
                'config_sha256': sha256(config_path), 'generator_sha256': sha256(Path(__file__))}
    mp = out / 'r10_ev_manifest.json'; mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    validation = {'vehicle_id': cfg['vehicle_id'], 'status': 'generated', 'output_hash': sha256(definition),
                  'input_hash_validation': 'PENDING'}
    (out / 'r10_ev_generation_report.json').write_text(json.dumps(validation, indent=2) + '\n')
    print(json.dumps({'run_dir': str(out), 'vehicle_id': cfg['vehicle_id'], 'energy_kwh_per_km': rate, 'operational_available_energy_kwh': operational}, indent=2))
    return 0

if __name__ == '__main__': raise SystemExit(main())
