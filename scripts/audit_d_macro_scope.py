"""Independent exact permutation comparator for the declared REAL small domains.

Classical oracle routes are used here AFTER experiments, never injected into
AOA plans. This timing is validation cost outside program T.
"""
import itertools
import json
import os
from pathlib import Path
import time
import argparse
from kmd_toc.common.models import load_problem,load_plan
from kmd_toc.common.adapters import to_vehicle_day
from kmd_toc.pipeline.hybrid import day_candidates,EventDayMaster

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--include-s1',action='store_true');args=parser.parse_args()
    out=ROOT/'D_MACRO_SCOPE_AUDIT';out.mkdir(exist_ok=True);rows=[]
    for case in ['ROAD_N6','ROAD_N20','ROAD_N120','ROAD_N240']+(['S1'] if args.include_s1 else []):
        path=ROOT/'experiments'/case/'D_primaryD_epsW_1/result.json'
        if not path.exists():continue
        r=json.loads(path.read_text())
        if r['status']!='FEASIBLE':continue
        begin=time.perf_counter();p=load_problem(ROOT/'roads/inputs'/case);day=to_vehicle_day(p,delta_s=1);meta=r['plan']['method_settings']
        seedpath=out/(case+'_SEED.json');seedpath.write_text(json.dumps(meta['seed_plan'])+'\n');seed=load_plan(seedpath)
        obtained=set();exact=set()
        for sample in meta['quantum']:
            groups=sample['fragment_groups']
            exact.update(tuple(i for g in order for i in groups[g]) for order in itertools.permutations(range(len(groups))))
            obtained.update(tuple(t) for t in sample['full_route_obtained'])
        base=set(tuple(t) for t in meta['seed_routes']);actual_routes=base|obtained;full_routes=base|exact
        actual_columns=day_candidates(day,actual_routes,seed,p);full_columns=day_candidates(day,full_routes,seed,p)
        actual=EventDayMaster(day,actual_columns);full=EventDayMaster(day,full_columns)
        ai=list(range(len(actual_columns)));fi=list(range(len(full_columns)))
        actual_lp=actual.lp(ai,r['primary'],r['other_limit']);full_lp=full.lp(fi,r['primary'],r['other_limit']);full_ip=full.ip(fi,r['primary'],r['other_limit'])
        row={'case':case,'scope':'same fixed fragments, original internal orders and seed calendars; NOT full VRP','exact_macro_routes':len(exact),'obtained_macro_routes':len(exact&obtained),'route_coverage':len(exact&obtained)/len(exact),
             'actual_columns':len(actual_columns),'exact_macro_columns':len(full_columns),'actual_full_pool_LP':actual_lp['objective'],'exact_macro_LP':full_lp['objective'],'exact_macro_IP':full_ip['objective'],
             'experimental_IP':meta['hybrid']['IP']['objective'],'same_scope_gap_to_exact_IP':meta['hybrid']['IP']['objective']-full_ip['objective'],'classical_oracle_injected_into_hybrid':False,'validation_seconds':time.perf_counter()-begin}
        # Price exact-scope columns at the SAME hybrid LP dual, including its
        # physical-vehicle, berth and epsilon rows, without changing the RMP.
        if actual.events==full.events:
            import numpy as np
            from scipy.optimize import linprog
            a,b,rhs,cost=actual.arrays(ai,r['primary'],r['other_limit']);lp=linprog(cost,A_eq=a,b_eq=np.ones(actual.n),A_ub=b,b_ub=rhs,bounds=(0,None),method='highs')
            y=np.r_[lp.eqlin.marginals,lp.ineqlin.marginals[:len(full.rhs)]];epsilon=lp.ineqlin.marginals[-1] if r['other_limit'] is not None else 0
            reduced=(full.d if r['primary']=='D' else full.w)-np.asarray(full.a.T@y).ravel()-epsilon*(full.w if r['primary']=='D' else full.d)
            ids={c.column_id for c in actual_columns};missing=[float(rc) for c,rc in zip(full_columns,reduced) if c.column_id not in ids and rc< -1e-7]
            row.update(unobtained_negative_columns_in_exact_macro_scope=len(missing),minimum_unobtained_reduced_cost=min(missing) if missing else 0.)
        else:row['same_dual_pricing']='not comparable: interval sets differ'
        rows.append(row);print(row,flush=True)
    (out/'SUMMARY.json').write_text(json.dumps(rows,indent=2)+'\n')

if __name__=='__main__':main()
