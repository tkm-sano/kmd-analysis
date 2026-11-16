"""Fresh timed full/scoped/AOA pricing at identical saved dual snapshots.

Catalogue preprocessing and diagnostic coverage are outside pricing time and
reported explicitly. Same completion, rc and duplicate/batch rules for scoped
classical and AOA; all three return validated finite-grid day columns.
"""
import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path
from time import perf_counter
import hashlib
import numpy as np
from kmd_toc.column_generation.aoa import AOAConfig
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile
from kmd_toc.search_improvement.catalogue import build_catalogue
from kmd_toc.search_improvement.master import CatalogueMaster
from kmd_toc.search_improvement.regions import exact_routes,measure_routes
from kmd_toc.search_improvement.study import coverage


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--suffix',default='');args=parser.parse_args()
    root=Path(args.root);cfg=json.loads(Path('configs/toc_delivery_d_pricing_improvement_v1.json').read_text())
    start=perf_counter();p=small_problem(6,1);m=CatalogueMaster(p,build_catalogue(p));prep=perf_counter()-start
    out=root/('SNAPSHOT_BENCHMARK'+args.suffix);out.mkdir(exist_ok=False)
    rows=[]
    for name in ['regression_final_D','regression_initial_W']:
        snapshot=json.loads((root/'coverage_attempt03'/f'{name}_SNAPSHOT.json').read_text())
        pool=[m.index[i] for i in snapshot['pool_ids']];dual=snapshot['dual'];profile=ObjectiveProfile(**snapshot['profile'])
        iteration=len(json.loads((root/'baseline_replay/AOA_N6_B1_D.json').read_text())['trace'])-1 if name=='regression_final_D' else 0
        for version in ['old','expanded']:
            saved=json.loads((root/'coverage_attempt03'/f'{name}_{version}_2101.json').read_text());domains=saved['domains']
            for mode,seeds in [('full_global_classical',[None]),('same_scope_classical',[None]),('aoa',cfg['snapshot_seeds'])]:
                for seed in seeds:
                    begin=perf_counter();q=[]
                    if mode=='aoa':
                        sampled,q=measure_routes(p,dual,profile,domains,replace(AOAConfig(**cfg['aoa']),solver_seed=seed),iteration)
                    elif mode=='same_scope_classical':sampled=exact_routes(p,dual,profile,domains)
                    else:sampled=set(m.route_index)
                    candidates=set(range(len(m.columns))) if mode=='full_global_classical' else m.complete(sampled,m.known(pool))
                    rc=m.rc(dual,profile)
                    negative={i for i in candidates if rc[i]<-1e-7}
                    new=sorted(negative-set(pool),key=lambda i:(rc[i],m.ids[i]))[:20]
                    elapsed=perf_counter()-begin
                    record={'snapshot':name,'regions':version,'sampler':mode,'seed':seed,
                        'pricing_seconds':elapsed,'catalogue_preparation_seconds':prep,
                        'negative_count':len(negative),'min_rc':float(min(rc[i] for i in candidates)),
                        'new_batch_count':len(new),'feasible_completed_day_rate':1. if candidates else None,
                        'feasible_shot_rate':sum(x['result']['feasible_shots'] for x in q)/sum(x['result']['measured_shots'] for x in q) if q else None}
                    rows.append(record)
                    with (out/f'{name}_{version}_{mode}_{seed}.json').open('x') as f:
                        json.dump({'record':record,'snapshot':snapshot,'domains':domains,'quantum':q,'added_ids':[m.ids[i] for i in new]},f,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())
    with (out/'TIMINGS.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with (out/'PROVENANCE.json').open('x') as f:
        json.dump({'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   'config':cfg,'snapshot_directory':'coverage_attempt03','all_inputs_artificial':True},f,indent=2)
