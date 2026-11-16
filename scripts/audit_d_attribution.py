"""Reconstruct classical day-master controls, never add routes to experiments."""
import json
import os
from pathlib import Path
import time
from kmd_toc.common.models import load_problem,load_plan
from kmd_toc.common.adapters import to_vehicle_day
from kmd_toc.pipeline.hybrid import day_candidates
from kmd_toc.vehicle_day.validation import validate_plan

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112_route_v2'))

if __name__=='__main__':
    out=ROOT/'D_ATTRIBUTION_AUDIT';out.mkdir(exist_ok=True);p=load_problem(ROOT/'roads/inputs/S1');day=to_vehicle_day(p,delta_s=1);positions={sid:i for i,sid in enumerate(p.od.ids)};rows=[]
    for file in sorted((ROOT/'experiments/S1').glob('D*/result.json')):
        start=time.perf_counter();r=json.loads(file.read_text())
        if r['status']!='FEASIBLE':continue
        m=r['plan']['method_settings'];seedpath=out/(file.parent.name+'_seed.json');seedpath.write_text(json.dumps(m['seed_plan'])+'\n');seed=load_plan(seedpath);original={tuple(route) for route in m['seed_routes']}
        columns=day_candidates(day,original,seed,p);selected=[columns[i] for i in m['base']['IP']['selected']];control=validate_plan(day,selected)
        if not control['valid']:raise ValueError('CLASSICAL_CONTROL_INVALID')
        value=control['D_km'] if r['primary']=='D' else control['W_min']
        if abs(value-m['base']['IP']['objective'])>1e-7:raise ValueError('CLASSICAL_CONTROL_INDEX_DRIFT')
        sampled={tuple(route) for q in m['quantum'] for route in q['full_route_obtained']};new=sampled-original
        finalroutes=[tuple(positions[v['stop_id']] for v in t['visits']) for t in r['plan']['trips']]
        rows.append({'condition':file.parent.name,'primary':r['primary'],'integer_tie_policy':m.get('integer_tie_policy'),'classical_seed_D_km':sum(t.distance_m for t in seed.trips)/1000,'classical_seed_W_min':sum(t.waiting_s for t in seed.trips)/60,
                     'classical_master_D_km':control['D_km'],'classical_master_W_min':control['W_min'],'final_D_km':r['D_km'],'final_W_min':r['W_min'],
                     'D_improvement_from_candidate_pool_km':control['D_km']-r['D_km'],'W_improvement_from_candidate_pool_min':control['W_min']-r['W_min'],
                     'new_AOA_routes_sampled':len(new),'new_AOA_routes_selected':sum(route in new for route in finalroutes),
                     'quantum_unique_advantage_claim':False,'elapsed_posthoc_validation_s':time.perf_counter()-start})
    (out/'SUMMARY.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
