"""Explicit outer-trial units/designs, five comparison slots, no inferred pairing."""
from collections import Counter
from pathlib import Path
import math

from . import statistics as s

SCALES=('S1','S2','S3');METHODS=('B','C','D')
COMPARISONS=(('A','B'),('A','C'),('A','D'),('B','D'),('C','D'))


def _design(reg,key,evidence):
    meta=reg.get('independence',{}).get(key,{})
    if meta.get('confirmed') is not True or not meta.get('reason'):return False
    proof=evidence(meta.get('evidence'))
    return proof.get('kind')=='outer_independence_design' and proof.get('cell')==key and proof.get('independent') is True


def _pairs(design,byid,evidence):
    proof=evidence(design.get('evidence'));kind=design.get('kind')
    if kind not in ('paired_common_random_factors','certified_fixed_reference'):
        raise ValueError('NO_ARBITRARY_PAIRING')
    if proof.get('kind')!=kind or proof.get('registered_before_results') is not True:
        raise ValueError('PAIRING_REQUIRES_PRIOR_DESIGN_EVIDENCE')
    pairs=design.get('pairs',[])
    if proof.get('pairs')!=pairs:raise ValueError('PAIR_MAP_NOT_SAME_AS_REGISTERED_DESIGN')
    if kind=='paired_common_random_factors':
        factors=proof.get('stochastic_shared_factors',[])
        if not factors or not set(factors)-{'same_seed','same_index','same_trial_id','fixed_demand'}:
            raise ValueError('SEED_OR_INDEX_OR_FIXED_DEMAND_IS_NOT_PAIRING')
    elif proof.get('deterministic_certified') is not True or not proof.get('certificate'):
        raise ValueError('OBSERVED_SD_ZERO_IS_NOT_FIXED_REFERENCE_CERTIFICATE')
    seenx=set();seeny=set();a=[];b=[]
    for x,y in pairs:
        if y in seeny or (kind!='certified_fixed_reference' and x in seenx):
            raise ValueError('REUSED_STOCHASTIC_TRIAL_IN_DIFFERENCES')
        seenx.add(x);seeny.add(y)
        if x not in byid or y not in byid:raise ValueError('PAIR_ID_NOT_REGISTERED')
        u,v=byid[x],byid[y]
        if (u['scale']!=design['scale'] or v['scale']!=design['scale'] or
                u['method']!=design['baseline'] or v['method']!=design['comparison']):
            raise ValueError('PAIR_SCOPE_OR_METHOD_MISMATCH')
        if u['eligible'] and v['eligible']:a.append(u);b.append(v)
    independent=proof.get('independent_pairs') is True
    # A design declaration cannot override known repeated complete RNG identities.
    for group in ([a,b] if kind!='certified_fixed_reference' else [b]):
        seeds=[r.get('seed_identity') for r in group if r.get('seed_identity') is not None]
        if len(seeds)!=len(set(seeds)):independent=False
    return a,b,independent


def _A_gate(ref):
    fields=('unit','measurement_scope','time_context','spatial_context','aggregation_target')
    audit=ref.get('comparability_audit',{})
    return ref.get('value') is not None and all(
        isinstance(audit.get(k),dict) and audit[k].get('status')=='PASS' and audit[k].get('evidence') for k in fields)


def analyze(reg,rows,evidence):
    byid={r['trial_id']:r for r in rows}
    if len(byid)!=len(rows):raise ValueError('DUPLICATE_TRIAL_IDS')
    summaries=[];failure_rows=[];prefixes=[];comparisons=[];duals=[];series={};ind={}
    designs={}
    for d in reg.get('comparison_designs',[]):
        key=(d['scale'],d['baseline'],d['comparison'])
        if key in designs:raise ValueError('DUPLICATE_COMPARISON_DESIGN')
        if key[0] not in SCALES or key[1:] not in (('B','D'),('C','D')):raise ValueError('ONLY_APPROVED_STOCHASTIC_COMPARISONS')
        designs[key]=d
    for scale in SCALES:
        for method in METHODS:
            allrows=sorted((r for r in rows if (r['scale'],r['method'])==(scale,method)),key=lambda r:r['order'])
            attempts=[r for r in allrows if r.get('outer_attempt',True)]
            if len({r['order'] for r in attempts})!=len(attempts):raise ValueError('REGISTERED_SEQUENCE_ORDER_MUST_BE_UNIQUE')
            valid=[r for r in allrows if r['eligible']]
            key=f'{scale}/{method}';ind[key]=_design(reg,key,evidence)
            seeds=[r.get('seed_identity') for r in valid if r.get('seed_identity') is not None]
            if len(seeds)!=len(set(seeds)):ind[key]=False
            status=Counter(r['status'] for r in attempts)
            failure_rows.append({'scale':scale,'method':method,'registered_records':len(allrows),
                                 'registered_outer_attempts':len(attempts),'nonouter_or_retry_records':len(allrows)-len(attempts),
                                 'valid_outer_records':len(valid),
                                 'status_counts':dict(status),'excluded':len(allrows)-len(valid),
                                 'infeasible_fraction':status['INFEASIBLE']/len(attempts) if attempts else None,
                                 'missing_fraction':status['MISSING']/len(attempts) if attempts else None,
                                 'success_conditional_statistics':True,'independence_confirmed':ind[key]})
            for metric in ('D','W'):
                values=[r[metric] for r in valid];summary=s.summary(values,independent=ind[key])
                summaries.append({'scale':scale,'method':method,'metric':metric,**summary})
                series[scale,method,metric]=values
                for n in range(1,len(attempts)+1):
                    vals=[r[metric] for r in attempts[:n] if r['eligible']]
                    prefixes.append({'scale':scale,'method':method,'metric':metric,'registered_prefix':n,
                                     'valid_prefix':len(vals),**s.summary(vals,independent=ind[key])})
        for baseline,comparison in COMPARISONS:
            d=designs.get((scale,baseline,comparison));pairs=None
            if d and d['kind']!='independent_groups':pairs=_pairs(d,byid,evidence)
            for metric in ('D','W'):
                target=series[scale,comparison,metric]
                row={'scale':scale,'baseline':baseline,'comparison':comparison,'metric':metric,
                     'delta_values':None,'mean_delta':None,'SD_delta':None,'MCSE_delta':None,
                     'relative_rate_of_means':None,'status':'HOLD_NO_COMPARABLE_VALUES','MCSE_status':'HOLD'}
                if baseline=='A':
                    ref=reg.get('A_references',{}).get(scale,{}).get(metric,{})
                    row.update(kind='fixed_external_reference',A_value=ref.get('value'),A_SD=None,A_J=None,
                               comparability_audit=ref.get('comparability_audit',{}))
                    if _A_gate(ref):
                        s.finite([ref['value']],nonnegative=True)
                        delta=[v-ref['value'] for v in target];z=s.summary(delta,independent=ind[f'{scale}/{comparison}'])
                        row.update(status='DEFINED' if delta else 'HOLD_NO_VALID_TRIALS',delta_values=delta,
                                   mean_delta=z['mean'],SD_delta=z['SD'],MCSE_delta=z['MCSE'],
                                   MCSE_status=z['MCSE_status'],
                                   relative_rate_of_means=s.relative(ref['value'],s.summary(target)['mean']) if target else None,
                                   A_display_allowed=True)
                    else:row.update(status='HOLD_A_COMPARABILITY',A_display_allowed=False)
                elif pairs is not None:
                    a,b,independent=pairs
                    z=s.paired([r[metric] for r in a],[r[metric] for r in b],independent_pairs=independent)
                    row.update(kind=z['kind'],status='DEFINED' if a else 'HOLD_NO_VALID_PAIRS',
                               delta_values=z['delta_values'],mean_delta=z['delta']['mean'],SD_delta=z['delta']['SD'],
                               MCSE_delta=z['delta']['MCSE'],relative_rate_of_means=None,
                               MCSE_status=z['delta']['MCSE_status'],
                               trial_relative_rates=z['relative_rate_values'],relative_rate_summary=z['relative_rate'],
                               undefined_rate_count=z['undefined_rate_count'],registered_pair_count=len(d['pairs']),valid_pair_count=len(a))
                else:
                    independent=False
                    if d:
                        proof=evidence(d.get('evidence'))
                        independent=(proof.get('kind')=='independent_groups' and proof.get('between_groups_independent') is True
                                     and ind[f'{scale}/{baseline}'] and ind[f'{scale}/{comparison}'])
                    z=s.independent_contrast(series[scale,baseline,metric],target,independent_groups=independent)
                    row.update(z,status='DEFINED_GROUP_MEAN_CONTRAST' if z['mean_delta'] is not None else 'HOLD_NO_VALID_TRIALS')
                comparisons.append(row)
            if baseline=='C' and pairs is not None:
                a,b,independent=pairs
                duals.append({'scale':scale,'method':'D',**s.paired_dual(a,b,independent_pairs=independent)})
        for design in reg.get('dual_designs',[]):
            if design['scale']!=scale:continue
            if design['baseline']!='C' or design['comparison'] not in ('B','D'):raise ValueError('I_DUAL_C_REFERENCE_ONLY')
            if any(r['scale']==scale and r['method']==design['comparison'] for r in duals):raise ValueError('DUPLICATE_DUAL_DESIGN')
            a,b,independent=_pairs(design,byid,evidence)
            duals.append({'scale':scale,'method':design['comparison'],**s.paired_dual(a,b,independent_pairs=independent)})
    # No distribution, SD or success fraction is manufactured from unmatched means.
    aggregate=[]
    for scale in SCALES:
        for method in ('B','D'):
            c={m:s.summary(series[scale,'C',m])['mean'] for m in ('D','W')}
            x={m:s.summary(series[scale,method,m])['mean'] for m in ('D','W')}
            value=s.dual(c['D'],c['W'],x['D'],x['W']) if all(v is not None for v in [*c.values(),*x.values()]) else None
            aggregate.append({'scale':scale,'method':method,'I_dual_of_group_means':value,
                              'not_mean_trial_I_dual':True,'trial_SD':None,'trial_strict_dual_fraction':None})
    return {'summaries':summaries,'failures':failure_rows,'prefixes':prefixes,'comparisons':comparisons,
            'dual_trials':duals,'aggregate_mean_indices':aggregate,'formal_J_status':'HOLD','formal_J':None,
            'MCSE_tolerance':None,'resource_budget':None,'SESOI':None,'MDE':'SUPERSEDED',
            'hypothesis_testing':'NOT_PERFORMED','main_experiment':'HOLD'}
