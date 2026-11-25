"""Cost-gated adaptive B/C/D/E schedule, registered before follow-up outcomes.

Computational modules and the original safety envelope are unchanged.
"""
import json
from pathlib import Path
from .study import OUT,CONFIG,read,dump,digest,gate,supervise,check_pins
from .analyze import analyze,nondominated


def register():
    target=OUT/'FOLLOWUP_PROTOCOL.json'
    if target.exists():return read(target)
    spec={'scope':'adaptive prioritization within original 7200s active-supervisor safety budget',
        'registered_before_followup_outcomes':True,'source_sha256':digest(Path(__file__)),
        'rule':'within each scale, complete non-dominated A conditions sorted by measured parent cost; use cheapest candidate for B:R13 and C:K=V at R5; then D:K=V,R13 if both axes completed and some strict gain vs A; E:confirm cheapest complete positive A with two unused seeds; remaining R25 and K2V only if gates allow',
        'scale_order':['S1','S2','S3'],'non_dominance':'descriptive four-branch mean D/W and parent wall; no performance weights/equivalence claim',
        'failure':'do not continue axes/joint/confirmation for a scale after numerical failure; preserve existing results; never change p/shots/numerical/optimizer settings',
        'seed_scope':'confirmation of chosen measured setting only, not independent demand and not main J',
        'not_a_full_factorial_claim':True,'main_experiment':False}
    dump(target,spec);return spec


def execute():
    spec=register();check_pins()
    if spec['source_sha256']!=digest(Path(__file__)):raise ValueError('FOLLOWUP_DRIVER_CHANGED')
    analyze(False)
    groups=read_table()
    chosen=[]
    for scale,V in [('S1',10),('S2',20),('S3',40)]:
        options=[g for g in groups if g['scale']==scale and int(g['P'])==4 and g['status']=='COMPLETE' and int(g['K'])==V//2 and int(g['R'])==5]
        for g in options:
            for key in ('delta_D_branch_mean','delta_W_branch_mean','parent_wall_s'):g[key]=float(g[key])
        frontier=nondominated(options,['delta_D_branch_mean','delta_W_branch_mean','parent_wall_s'])
        if frontier:chosen.append((min(frontier,key=lambda g:g['parent_wall_s']),V))
    dump(OUT/'FOLLOWUP_SELECTION.json',{'chosen_from_A':[g for g,V in chosen],'rule':spec['rule']})
    for base,V in chosen:
        scale=base['scale'];n=int(base['n']);failed=False
        for K,R in [(V//2,13),(V,5)]:
            tag=f'screen_{scale}_n{n}_K{K}_R{R}_seed9201'
            result=maybe_run(tag,scale,n,K,R,9201)
            if result and result['status']!='COMPLETE':failed=True;break
        if failed:continue
        axes=[OUT/f'groups/screen_{scale}_n{n}_K{K}_R{R}_seed9201/GROUP.json' for K,R in [(V//2,13),(V,5)]]
        if all(p.exists() and read(p)['status']=='COMPLETE' for p in axes):
            analyze(False);updated=read_table()
            axis_rows=[g for g in updated if g['tag'] in [p.parent.name for p in axes]]
            if any(float(g['delta_D_branch_mean'])<base['delta_D_branch_mean'] or float(g['delta_W_branch_mean'])<base['delta_W_branch_mean'] for g in axis_rows):
                tag=f'screen_{scale}_n{n}_K{V}_R13_seed9201'
                result=maybe_run(tag,scale,n,V,13,9201)
                if result and result['status']!='COMPLETE':continue
        if base['delta_D_branch_mean']<0 or base['delta_W_branch_mean']<0:
            for seed in read(CONFIG)['confirmation_outer_seeds']:
                tag=f'confirm_{scale}_n{n}_K{V//2}_R5_seed{seed}'
                result=maybe_run(tag,scale,n,V//2,5,seed)
                if result and result['status']!='COMPLETE':failed=True;break
        if failed:continue
        for K,R in [(V//2,25),(2*V,5)]:
            maybe_run(f'screen_{scale}_n{n}_K{K}_R{R}_seed9201',scale,n,K,R,9201)
    analyze(True)


def read_table():
    import csv
    with (OUT/'GROUPS.csv').open() as stream:return list(csv.DictReader(stream))


def maybe_run(tag,scale,n,K,R,seed):
    path=OUT/'groups'/tag/'GROUP.json'
    if path.exists():return read(path)
    allowed,detail=gate(scale,n,K,R);dump(OUT/'gates'/(tag+'.json'),{'allowed':allowed,**detail})
    if not allowed:return None
    return supervise(tag,scale,n,K,R,seed)


if __name__=='__main__':
    import sys
    print(json.dumps(register(),indent=2)) if sys.argv[1]=='register' else execute()
