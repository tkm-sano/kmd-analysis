"""Compare independently measured R jobs; never assumes prefix identity."""
import gzip
import json
from .study import OUT,read,dump
from .analyze import progress_rows


def main():
    groups=[read(p) for p in (OUT/'groups').glob('screen_*/GROUP.json')]
    groups=[g for g in groups if g.get('status')=='COMPLETE' and g.get('P')==4]
    checks=[]
    for small in groups:
        for large in groups:
            if any(small[k]!=large[k] for k in ['scale','n','K','outer_seed']) or small['R']>=large['R']:continue
            details=[]
            for branch in range(4):
                s=OUT/'groups'/small['tag']/f'branch_{branch}';l=OUT/'groups'/large['tag']/f'branch_{branch}'
                with gzip.open(s/f"ITERATION_{small['R']:03d}.plan.json.gz",'rt') as f:a=json.load(f)
                with gzip.open(l/f"ITERATION_{small['R']:03d}.plan.json.gz",'rt') as f:b=json.load(f)
                plan_same=a==b;calls_same=True
                for r in range(1,small['R']+1):
                    for k in range(1,small['K']+1):
                        name=f'r{r:03d}_k{k:03d}';sp=s/'calls'/name;lp=l/'calls'/name
                        if not (sp/'CALL.json').exists() or not (lp/'CALL.json').exists():calls_same=False;continue
                        sm=read(sp/'CALL.json');lm=read(lp/'CALL.json')
                        if sm['local']!=lm['local'] or sm['seed']!=lm['seed']:calls_same=False
                        se=[e for e in progress_rows(sp/'evaluations.jsonl') if e['event']=='sampling_completed']
                        le=[e for e in progress_rows(lp/'evaluations.jsonl') if e['event']=='sampling_completed']
                        if len(se)!=len(le):calls_same=False;continue
                        for x,y in zip(se,le):
                            if any(x[key]!=y[key] for key in ['phase','evaluation','seed','angles','counts']):calls_same=False
                details.append({'branch':branch,'prefix_plan_identical':plan_same,'all_prefix_counts_angles_ids_seeds_identical':calls_same})
            checks.append({'scale':small['scale'],'n':small['n'],'K':small['K'],'R_short':small['R'],'R_long':large['R'],
                'short_group':small['tag'],'long_group':large['tag'],'branches':details,
                'identical':all(d['prefix_plan_identical'] and d['all_prefix_counts_angles_ids_seeds_identical'] for d in details)})
    result={'status':'NOT_TESTED' if not checks else 'PASS_IDENTICAL_FOR_TESTED_PREFIXES' if all(c['identical'] for c in checks) else 'NOT_IDENTICAL_KEEP_INDEPENDENT_RUNS',
        'checks':checks,'used_to_replace_independent_experiments':False,
        'timing_warning':'prefix state identity does not turn retrospectively summed worker times into a measured parent deadline T'}
    dump(OUT/'PREFIX_CHECK.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
