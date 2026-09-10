from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]
def sha256(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('run_dir'); ap.add_argument('--config', default='reproducibility/config/traffic_simulation/evrp_r10_ev_v1.yml'); a=ap.parse_args()
    run=ROOT/a.run_dir; cfg=yaml.safe_load((ROOT/a.config).read_text())
    row=next(csv.DictReader((run/'vehicle_definition.csv').open(newline='')))
    checks={}
    checks['payload_positive']=float(row['payload_capacity_kg'])>0
    checks['battery_positive']=float(row['battery_capacity_kwh'])>0
    checks['operational_available_energy_valid']=0<float(row['operational_available_energy_kwh'])<=float(row['battery_capacity_kwh'])
    checks['energy_positive']=float(row['energy_consumption_kwh_per_km'])>0
    checks['soc_valid']=all(0<=float(row[k])<=1 for k in ('initial_soc','minimum_soc'))
    checks['initial_soc_gt_minimum']=float(row['initial_soc'])>float(row['minimum_soc'])
    checks['final_soc_rule_explicit']=row['final_soc_requirement_enabled'] in ('True','False') and row['final_soc_requirement'] in ('','None')
    checks['operating_time_rule_explicit']=row['maximum_operating_time_enabled'] in ('True','False')
    checks['vehicle_class_delivery']=row['vehicle_class']=='delivery'
    checks['finite']=all(math.isfinite(float(row[k])) for k in ('payload_capacity_kg','battery_capacity_kwh','operational_available_energy_kwh','energy_consumption_kwh_per_km','initial_soc','minimum_soc'))
    checks['provenance_fields']=all(row[k] for k in ('payload_source','battery_source','energy_source','soc_assumption_reason','vehicle_access_source'))
    manifest=json.loads((run/'r10_ev_manifest.json').read_text())
    input_checks={}
    for item in manifest['source']['inputs'].values(): input_checks[item['path']]=sha256(ROOT/item['path'])==item['sha256']
    checks['input_hashes']=all(input_checks.values())
    checks['depot_access_input']=sha256(ROOT/cfg['source_depot_validation']) == manifest['source']['inputs']['source_depot_validation']['sha256']
    checks['energy_formula_recorded']=row['energy_formula']==cfg['energy_formula'] and row['energy_classification']=='COMPUTED_APPROXIMATION'
    checks['depot_return_minimum_soc_semantics']=row['depot_return_minimum_soc_applies']=='True' and 'depot return' in row['soc_constraint_semantics']
    checks['external_soc_precedents']=len(cfg['soc_external_precedents'])>=2 and all(x.get('url') and x.get('setting') and x.get('application') for x in cfg['soc_external_precedents'])
    checks['fixture_recorded']=row['fixture_n']=='10' and row['is_production_problem_size']=='False'
    result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'input_checks':input_checks,
            'route_energy_formula':'E_ij[kWh] = d_ij[km] * energy_consumption_kwh_per_km; SOC at all route nodes including depot return must remain >= minimum_soc',
            'validated_output_sha256':sha256(run/'vehicle_definition.csv')}
    (run/'r10_independent_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['status']=='PASS' else 1
if __name__ == '__main__': raise SystemExit(main())
