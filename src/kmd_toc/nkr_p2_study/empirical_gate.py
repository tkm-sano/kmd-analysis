"""Refine cost forecasts only after three completed four-branch workloads.

Predictions are not observations or guaranteed upper bounds. Hard caps remain.
"""
def prediction(groups,scale,n,K,R,remaining,cap):
    refs=[g for g in groups if g.get('status')=='COMPLETE' and g.get('P')==4 and
          g.get('scale')==scale and g.get('n')==n and g.get('outer_seed')==9201]
    distinct={(g['K'],g['R']) for g in refs}
    if len(distinct)<3:return False,{'reason':'EMPIRICAL_GATE_NEEDS_THREE_DISTINCT_COMPLETE_GROUPS'}
    per_call=max(g['parent_wall_s']/(g['K']*g['R']) for g in refs)
    estimated=1.25*per_call*K*R+60
    return estimated<=min(remaining,cap),{'reason':'EMPIRICAL_FOUR_BRANCH_COST_GATE',
        'predicted_s_not_measurement':estimated,'margin_multiplier':1.25,'fixed_overhead_s':60,
        'reference_groups':[{'tag':g['tag'],'K':g['K'],'R':g['R'],'parent_wall_s':g['parent_wall_s']} for g in refs],
        'remaining_batch_s':remaining,'unchanged_group_cap_s':cap}
