#!/usr/bin/env python3
"""Independent V18 R09 depot authority closure checks."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
import sumolib

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = '460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('run_dir', type=Path); a = ap.parse_args()
    out = a.run_dir.resolve(); manifest = json.loads((out/'r09_depot_manifest.json').read_text())
    with (out/'depot_definition.csv').open(newline='', encoding='utf-8') as f: row = next(csv.DictReader(f))
    net_path = ROOT / manifest['inputs']['network']['path']; net = sumolib.net.readNet(str(net_path), withInternal=False)
    edge = net.getEdge(row['mapped_sumo_edge_id']); shape = edge.getShape()
    edge_len = float(edge.getLength()); offset = float(row['edge_offset_m']); md = float(row['mapping_distance_m'])
    checks = {
        'coordinates_preserved_and_valid': row['depot_id'] == 'DEP_006' and row['facility_name'] == '京浜トラックターミナル' and row['classification'] == 'PROXY' and math.isfinite(float(row['longitude'])) and math.isfinite(float(row['latitude'])),
        'accepted_network_hash': row['network_hash'] == EXPECTED and sha(net_path) == EXPECTED,
        'nearest_adopted_edge': edge.getID() == '617631294',
        'delivery_vehicle_access': 'delivery' in edge.getLane(0).getPermissions(),
        'edge_offset_in_range': 0 <= offset <= edge_len,
        'mapping_distance_finite_nonnegative': math.isfinite(md) and md >= 0,
        'edge_length_positive_and_shape_valid': edge_len > 0 and len(shape) >= 2 and all(math.isfinite(v) for point in shape for v in point),
        'topology_valid': bool(edge.getFromNode()) and bool(edge.getToNode()) and edge.getFromNode().getID() != edge.getToNode().getID(),
        'manifest_inputs_hash_valid': all(sha(ROOT/r['path']) == r['sha256'] for r in manifest['inputs'].values()),
    }
    result = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'run_id': manifest['run_id'], 'checks': checks, 'network_hash': EXPECTED, 'mapped_edge': edge.getID(), 'edge_offset_m': offset, 'edge_length_m': edge_len, 'mapping_distance_m': md}
    (out/'r09_v18_validation_report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['status'] == 'PASS' else 1
if __name__ == '__main__': raise SystemExit(main())
