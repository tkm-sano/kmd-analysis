"""Inspect missing path provenance; never import or run historical routing code."""
from evidence import *
import pyarrow.parquet as pq,collections
def main():
 start=time.monotonic();missing=rows(O/'B_UNRECOVERED_INTERVALS.csv');keys=collections.defaultdict(set)
 for x in missing:keys[int(x['partition_index'])].add((x['from_node'],x['to_node']))
 cp=read(B/SC/'sumo_od_final_validation_20261005/CHECKPOINT_ROWS.json');base=B/SC/'sumo_od_lane_feasible_routing_fix_20261001';router=use(base/'lane_router.py');rh=sha(router)
 for name in ['full_run_v3_failed_only.py','prepare_worker.py','validate.py']:use(base/name)
 original=B/SC/'sumo_od_full_baseline_20261001';use(original/'full_run.py');manifest=read(original/'OD_FULL_RUN_EXECUTION_MANIFEST.json')
 protected=[]
 for path,h in manifest['protected_hashes'].items():
  try:p=use(path,h);protected.append({'original_path':path,'retained_path':str(p),'sha256':h,'status':'PASS'})
  except (FileNotFoundError,ValueError) as e:protected.append({'original_path':path,'sha256':h,'status':'HOLD','reason':str(e)})
 table('OD_GENERATOR_PROTECTED_INPUTS.csv',protected)
 out=[]
 for pi,kk in sorted(keys.items()):
  p=use(cp[pi]['output_path'],cp[pi]['output_hash']);pf=pq.ParquetFile(p)
  cols=[k for k in ['origin_id','destination_id','lane_routing_mode','lane_routing_implementation_sha256','router_sha256','route_status','route_edge_count','network_hash'] if k in pf.schema_arrow.names]
  for ri,x in enumerate(pf.read(columns=cols).to_pylist()):
   if (x['origin_id'],x['destination_id']) not in kk:continue
   out.append({'partition_index':pi,'row_index':ri,'parquet_path':str(p),'parquet_sha256':SOURCES[str(p)]['sha256'],**x,'retained_lane_router_sha256':rh,'lane_router_source_match':x.get('lane_routing_implementation_sha256')==rh,'edge_sequence_status':'HOLD_NOT_RETAINED','regeneration':'HOLD_ORIGINAL_GENERATOR_REPLAY_AND_EXACT_IDENTITY_TEST_NOT_EXECUTED'})
 table('MISSING_OD_GENERATOR_PROVENANCE.csv',out)
 summary={'unique_missing_keys':sum(map(len,keys.values())),'located_rows':len(out),'partitions':len(keys),'lane_modes':dict(collections.Counter(x.get('lane_routing_mode') for x in out)),'source_hash_matches':sum(x['lane_router_source_match'] for x in out),'retained_lane_router_path':str(router),'retained_lane_router_sha256':rh,'original_generator_protected_inputs':dict(collections.Counter(x['status'] for x in protected)),'new_routing_or_native_processes':0,'scope':'Regeneration feasibility only; original baseline schema lacks lane-mode/source-hash columns, not a failed hash equality; original edge identity remains HOLD; do not issue complete input IDs','metrics':metrics(start)}
 write('MISSING_FEASIBILITY_SUMMARY.json',summary);sources('MISSING_FEASIBILITY_SOURCES.json');print(canon(summary))
if __name__=='__main__':main()
