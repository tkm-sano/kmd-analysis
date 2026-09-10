#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]; RUN=ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2'
a=json.loads((RUN/'failure_cohort_analysis.json').read_text()); overrides={}
for p in a['pairs']:
 if p['nearby_routeable_alternative']:
  q=p['nearby_alternatives'][0]; overrides[p['origin_stop_id']]=q['from_edge']; overrides[p['destination_stop_id']]=q['to_edge']
(RUN/'routeable_edge_overrides.json').write_text(json.dumps({'status':'MAPPING_FIX','scope':'17 failed OD cohort only','rule':'deterministic nearest delivery-permitted edge with routeable directed continuation within 100m','overrides':overrides},indent=2)+'\n')
print(json.dumps({'overrides':len(overrides),'status':'MAPPING_FIX'}))
