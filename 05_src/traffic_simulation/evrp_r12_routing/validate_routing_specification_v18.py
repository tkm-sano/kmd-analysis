#!/usr/bin/env python3
"""Independent validation of an R12 routing-specification run."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re
from pathlib import Path
import sumolib

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def authority_value(text: str, key: str) -> str:
    m=re.search(rf'^{re.escape(key)}:\s*(.+)$', text, re.M)
    if not m: raise ValueError(key)
    return m.group(1).strip().strip("'").strip('"')

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',type=Path,required=True); ap.add_argument('--authority',type=Path,required=True); args=ap.parse_args()
    run=args.run_dir; authority_text=args.authority.read_text()
    network=Path(authority_value(authority_text,'network_path')); expected_hash=authority_value(authority_text,'network_sha256')
    observed_hash=sha(network); net=sumolib.net.readNet(str(network),withInternal=False)
    with (run/'endpoint_manifest.csv').open() as f: endpoints=list(csv.DictReader(f))
    with (run/'od_manifest.csv').open() as f: ods=list(csv.DictReader(f))
    cfg=json.loads((run/'r12_routing_config.json').read_text()); schema=json.loads((run/'routing_output_schema.json').read_text())
    ids=[r['endpoint_id'] for r in endpoints]; edges={e.getID():e for e in net.getEdges()}
    type_counts={t:sum(r['endpoint_type']==t for r in endpoints) for t in ('depot','customer','charger')}
    checks={
      'authority_status_formal_accepted':authority_value(authority_text,'status')=='FORMAL_NETWORK_ACCEPTED',
      'network_hash_matches_v18_authority':observed_hash==expected_hash=='460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2',
      'endpoint_id_unique':len(ids)==len(set(ids))==12,
      'endpoint_role_counts':type_counts=={'depot':1,'customer':10,'charger':1},
      'endpoint_edges_exist_and_delivery_permitted':all(r['mapped_edge_id'] in edges and 'delivery' in (edges[r['mapped_edge_id']].getPermissions() or []) for r in endpoints),
      'endpoint_offsets_in_edge_range':all(0<=float(r['edge_offset_m'])<=edges[r['mapped_edge_id']].getLength()+1e-6 for r in endpoints),
      'endpoint_coordinates_and_mapping_distances_finite':all(all(math.isfinite(float(r[k])) for k in ('latitude','longitude','edge_offset_m','mapping_distance_m')) for r in endpoints),
      'directed_od_complete':len(ods)==132 and len({(r['origin_id'],r['destination_id']) for r in ods})==132 and all(r['origin_id']!=r['destination_id'] for r in ods) and {r['origin_id'] for r in ods}==set(ids) and {r['destination_id'] for r in ods}==set(ids),
      'od_per_origin_11':all(sum(r['origin_id']==i for r in ods)==11 for i in ids),
      'units_explicit':schema['units']=={'distance_m':'m','travel_time_s':'s'},
      'offset_semantics_explicit':'from-node' in schema['offset_semantics'] and 'same-edge' in schema['offset_semantics'],
      'objective_unique':cfg['routing_objective']=='travel_time_minimizing' and schema['fields'][10]['name']=='travel_time_s',
      'unreachable_failure_distinction_explicit':all(x in cfg['unreachable_policy'] for x in ('LEGITIMATE_UNREACHABLE','ROUTING_ENGINE_FAILURE','INVALID_ENDPOINT','MISSING_OD')),
      'r13_contract_uses_v18':cfg['r13_command_contract']['network_hash']==expected_hash and cfg['r13_command_contract']['config_path']==str(run/'r12_routing_config.json') and cfg['r13_command_contract']['vehicle_class']=='delivery',
      'no_production_routing_executed':cfg['run_id']==run.name and not (run/'routing_arcs.csv').exists(),
    }
    result={'status':'PASS' if all(checks.values()) else 'FAIL','run_id':run.name,'network_authority':str(args.authority),'network_path':str(network),'network_hash':observed_hash,'endpoint_count':len(endpoints),'endpoint_type_counts':type_counts,'required_od_count':len(ods),'checks':checks,'production_routing_executed':False}
    out=run/'r12_v18_independent_validation.json'; out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
