#!/usr/bin/env python3
"""Read saved audits and exercise statistics with conspicuously synthetic data.

No demand generation, algorithm execution or quantum calls occur here.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.descriptive_v1.policy import VERSION,digest
from kmd_toc.descriptive_v1.pipeline import dump,write_analysis


def fixture(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    reg={'version':VERSION,'data_role':'synthetic_statistics_fixture','cases':{},'trials':[],
         'independence':{},'comparison_designs':[],'dual_designs':[], 'A_references':{},
         'warning':'ARITHMETIC/FIGURE FIXTURE ONLY. NOT DELIVERY RESULTS OR AN INDEPENDENCE CERTIFICATE FOR REAL DATA.'}
    data={'C':([100,102,98,101,99,100],[50,52,48,51,49,50]),
          'B':([110,109,112,108,111,140],[60,62,58,61,59,90]),
          'D':([90,91,93,89,92,95],[45,46,47,44,45,55])}
    def proof(name,value):
        p=directory/(name+'.json');dump(p,value)
        return {'path':p.name,'sha256':digest(p)}
    for scale,mult in [('S1',1),('S2',2),('S3',4)]:
        for method,(ds,ws) in data.items():
            key=f'{scale}/{method}'
            reg['independence'][key]={'confirmed':True,'reason':'synthetic fixture design, not empirical evidence',
                'evidence':proof(scale+'_'+method+'_units',{'kind':'outer_independence_design','cell':key,'independent':True,'fixture':True})}
            for i,(d,w) in enumerate(zip(ds,ws)):
                tid=f'{scale}_{method}_{i+1}'
                reg['trials'].append({'trial_id':tid,'outer_unit_id':tid,'unit_type':'outer_trial',
                    'scale':scale,'method':method,'order':i,'seed_identity':'fixture_'+tid,
                    'status':'SUCCESS','D':d*mult,'W':w*mult})
        for x,y,dest in [('B','D','comparison_designs'),('C','D','comparison_designs'),('C','B','dual_designs')]:
            pairs=[[f'{scale}_{x}_{i+1}',f'{scale}_{y}_{i+1}'] for i in range(6)]
            kind='paired_common_random_factors'
            evidence=proof(f'{scale}_{x}_{y}_design',{'kind':kind,'registered_before_results':True,
                'stochastic_shared_factors':['fixture_shared_initial_randomization'],
                'independent_pairs':True,'pairs':pairs,'fixture':True})
            reg[dest].append({'scale':scale,'baseline':x,'comparison':y,'kind':kind,'pairs':pairs,'evidence':evidence})
    p=directory/'registration.json';dump(p,reg)
    return p


def audit(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    sources={}
    def read(path):
        p=ROOT/path;sources[path]=digest(p)
        return json.loads(p.read_text())
    oldpath='output/stat_conditions_pilot_20261120_v2/OBSERVATIONS.json'
    obs=read(oldpath)
    nkpath='output/nkr_p2_20261120_v1/ALL54.csv';sources[nkpath]=digest(ROOT/nkpath)
    with (ROOT/nkpath).open() as f:nkr=list(csv.DictReader(f))
    duty=read('output/duty_break_20261121_v1/replay_verified_v2/MANIFEST.json')
    currentpath='output/stat_conditions_pilot_20261120_v2/CURRENT_S1_S2_S3.csv'
    sources[currentpath]=digest(ROOT/currentpath)
    with (ROOT/currentpath).open() as f:current=list(csv.DictReader(f))
    inventory={'scope':'Previously audited saved observations, n/K/R grid, duty fixed-route replays. No new optimizer runs.',
        'legacy_observations':len(obs),'legacy_method_counts':dict(Counter(r['method'] for r in obs)),
        'legacy_audit_eligible':sum(r['current_variance_eligible'] for r in obs),
        'legacy_exclusions':[{'run_id':r['run_id'],'scale':r['scale'],'method':r['method'],
            'old_current_exclusion_reasons':r['current_exclusion_reasons'],
            'note':'Historical audit preserved. A later selector implementation does not repair old shots/FCFS/architecture or create new outer trials.'} for r in obs],
        'old_current_cells':current,
        'nkr_grid_cells':len(nkr),'nkr_completed_cells':sum(r['status']=='COMPLETE' for r in nkr),
        'nkr_exclusion':'Different parameter cells and four internal branches; old mean W; not independent current outer trials.',
        'duty_replay_manifest':duty,
        'duty_exclusion':'Fixed-route constraint replay, not newly generated independent algorithm runs; old D is not current local D.',
        'eligible_new_outer_trials':0,'no_global_claim_of_absence_outside_audited_sources':True,
        'source_sha256':sources,'J_status':'HOLD','main_experiment':'NOT_RUN'}
    dump(directory/'EXISTING_DATA_AUDIT.json',inventory)
    reg={'version':VERSION,'data_role':'verified_outer_trials','cases':{},'trials':[],
         'independence':{},'comparison_designs':[],'dual_designs':[],
         'A_references':{scale:{metric:{'value':None,'comparability_audit':{},
             'status':'HOLD_SCOPE_UNITS_TIME_SPACE_AND_AGGREGATION_NOT_CERTIFIED',
             'note':'A: 0.58P km; 60U min (2025) / 94U min (2020 reference). P and U have not been identified with this model demand/trips. No pseudo-trials.'}
             for metric in ('D','W')} for scale in ('S1','S2','S3')},
         'eligibility_audit':{'path':'EXISTING_DATA_AUDIT.json','sha256':digest(directory/'EXISTING_DATA_AUDIT.json')}}
    dump(directory/'registration.json',reg)
    write_analysis(directory/'registration.json',directory/'analysis',figures=False)
    return inventory


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    inventory=audit(args.output/'current_audit')
    registration=fixture(args.output/'synthetic_fixture')
    write_analysis(registration,args.output/'synthetic_fixture'/'analysis')
    print(json.dumps({'legacy_observations':inventory['legacy_observations'],
        'eligible_new_outer_trials':0,'synthetic_trials':54,'formal_J':'HOLD','output':str(args.output)}))


if __name__=='__main__':main()
