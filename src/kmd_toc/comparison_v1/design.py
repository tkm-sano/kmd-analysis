"""Preregistered settings selection and numerical design, layered on comparison_v1."""
from copy import deepcopy
import math
from statistics import mean, variance

from .contract import ROOT, BCD_CONFIG, read, fingerprint, digest

METHODS = ('A','B','C','D','D_CLASSICAL_REPLACEMENT')
PHASES = ('selection_pilot','variance_pilot','confirmation','formal')
RULES_PATH = 'configs/toc_delivery/comparison_design_20261116_v1.json'


def profile_config(profile):
    config = deepcopy(read(ROOT/BCD_CONFIG))
    if profile == 'lean':
        config['allocation']['C_routing_fraction'] = .25
        config['D'].update(pricing_rounds=1, max_evaluations=40, train_shots=500, final_shots=2048)
    elif profile != 'retained':
        raise ValueError('UNKNOWN_PREREGISTERED_PROFILE')
    return config


def validate_extension(manifest):
    ext=manifest['design_extension']
    if manifest['phase'] not in PHASES: raise ValueError('DESIGN_PHASE_REQUIRED')
    if ext['rules_path'] != RULES_PATH or ext['rules_sha256'] != digest(ROOT/RULES_PATH):
        raise ValueError('PREREGISTERED_RULES_CHANGED')
    rules=read(ROOT/RULES_PATH)
    profile=next((p for p in rules['profiles'] if p['id']==ext['profile']),None)
    if not profile or manifest['BCD_config']!=profile_config(ext['profile']):
        raise ValueError('UNREGISTERED_INTERNAL_CONFIGURATION')
    if ext['tree_memory_limit_MiB'] != rules['pilot']['tree_memory_limit_MiB']:
        raise ValueError('MEMORY_CONTRACT_CHANGED')
    if ext.get('dependency_prefix') != rules['pilot']['dependency_prefix']:
        raise ValueError('DEPENDENCY_SEARCH_PATH_CHANGED')
    for case in manifest['cases']:
        if case['budget_wall_s']!=profile['tau_s'] or case['case_parameters']!={
                'BCD_epsilon_W_min': None, 'BCD_native_cap_s':profile['native_cap_s']}:
            raise ValueError('UNREGISTERED_TIME_CONFIGURATION')
    # Changing configuration after variance measurement makes its design ineligible.
    if manifest['phase'] in ('variance_pilot','confirmation','formal') and not ext.get('settings_lock'):
        raise ValueError('SETTINGS_LOCK_REQUIRED')
    if ext.get('settings_lock') and ext['settings_lock']!=setting_identity(manifest):
        raise ValueError('SETTINGS_LOCK_MISMATCH')
    if manifest['phase']=='formal' and not ext.get('main_lock'):
        raise ValueError('MAIN_DESIGN_LOCK_REQUIRED')
    if manifest['phase']=='formal':
        lock=ext['main_lock']
        if (not all(type(lock.get(k)) in (int,float) and math.isfinite(lock[k]) and lock[k]>0
                    for k in ('h_D','rate_h','budget_s')) or
                lock.get('run_list_hash')!=fingerprint(manifest['runs']) or
                lock.get('fixed_attempt_count')!=len(manifest['runs']) or
                lock.get('stopping')!='fixed_count'):
            raise ValueError('MAIN_FIXED_DESIGN_REQUIRED')
        if sum(next(c['budget_wall_s'] for c in manifest['cases'] if c['case_id']==r['case_id'])
               for r in manifest['runs'])>lock['budget_s']:
            raise ValueError('MAIN_DESIGN_EXCEEDS_BUDGET')


def setting_identity(manifest):
    return fingerprint({'BCD':manifest['BCD_config_hash'],'A':manifest['A_config_hash'],
        'source':manifest['source_hashes'], 'resources':manifest['resource_contract'],
        'cases':[{k:c[k] for k in ('case_id','input','budget_wall_s','case_parameters')} for c in manifest['cases']],
        'dependency_prefix':manifest.get('design_extension',{}).get('dependency_prefix'),
        'T_kind':manifest['T_kind']})


def require_same_settings(manifests):
    ids={setting_identity(m) for m in manifests}
    if len(ids)!=1: raise ValueError('VARIANCE_CONFIGURATION_MISMATCH')
    return ids.pop()


def wilson(k,n,alpha=.05):
    from scipy.stats import norm
    if not n: return None
    z=norm.ppf(1-alpha/2); den=1+z*z/n
    center=(k/n+z*z/(2*n))/den
    radius=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/den
    return [max(0.,center-radius),min(1.,center+radius)]


def clopper(k,n,alpha=.05):
    from scipy.stats import beta
    if not n:return None
    return [float(beta.ppf(alpha/2,k,n-k+1)) if k else 0.,
            float(beta.ppf(1-alpha/2,k+1,n-k)) if k<n else 1.]


def rate_count(halfwidth,alpha=.05):
    """Worst case Wilson halfwidth, including all-success pilots (no p=1 plug-in)."""
    from scipy.stats import norm
    if not 0<halfwidth<.5: raise ValueError('RATE_PRECISION_RANGE')
    z=norm.ppf(1-alpha/2)
    return max(1,math.ceil(z*z/(4*halfwidth*halfwidth)-z*z))


def mean_stats(values):
    return {'n':len(values),'mean':mean(values) if values else None,
            'variance':variance(values) if len(values)>1 else None}


def welch_halfwidth(v1,v2,r1,r2,alpha=.05):
    from scipy.stats import t
    if min(r1,r2)<2 or min(v1,v2)<0: raise ValueError('WELCH_INPUT_RANGE')
    a,b=v1/r1,v2/r2
    if a+b==0:return 0.
    df=(a+b)**2/(a*a/(r1-1)+b*b/(r2-1))
    return float(t.ppf(1-alpha/2,df)*math.sqrt(a+b))


def precision_count(v1,v2,h,alpha=.05,max_r=10000000):
    """Equal independent group allocation; numerical t correction, no guarantee."""
    from scipy.stats import norm
    if not math.isfinite(h) or h<=0 or min(v1,v2)<0:raise ValueError('PRECISION_INPUT_RANGE')
    lo=2;hi=max(2,math.ceil(norm.ppf(1-alpha/2)**2*(v1+v2)/h**2))
    while welch_halfwidth(v1,v2,hi,hi,alpha)>h:
        hi*=2
        if hi>max_r: return None
    while lo<hi:
        mid=(lo+hi)//2
        if welch_halfwidth(v1,v2,mid,mid,alpha)<=h:hi=mid
        else:lo=mid+1
    return lo


def variance_upper(v,n,alpha=.05):
    from scipy.stats import chi2
    if n<2 or v<=0:return None  # observed zero does not identify true zero
    return float((n-1)*v/chi2.ppf(alpha,n-1))


def optimal_allocation(v1,v2,c1,c2,h,alpha=.05,minimum=2):
    """Cost-optimal normal ratio, rounded and checked with Welch t."""
    if min(v1,v2,c1,c2)<=0: return None
    ratio=math.sqrt(v1*c2/(v2*c1))
    r2=precision_count(v1,v2,h,alpha)
    if r2 is None:return None
    # Binary search the integer scale with the same allocation ratio.
    def allocation(k):return max(minimum,math.ceil(k*ratio)),max(minimum,k)
    lo=minimum;hi=max(minimum,r2)
    while welch_halfwidth(v1,v2,*allocation(hi),alpha)>h:hi*=2
    while lo<hi:
        mid=(lo+hi)//2
        if welch_halfwidth(v1,v2,*allocation(mid),alpha)<=h:hi=mid
        else:lo=mid+1
    return allocation(lo)


def fixed_analysis(rows,alpha=.05):
    """Independent method groups on each fixed input; never pair by seed/repeat."""
    out=[]
    for case in sorted({r['case_id'] for r in rows}):
        own=[r for r in rows if r['case_id']==case]
        methods={}
        for method in METHODS:
            group=[r for r in own if r['method']==method]
            executed=[r for r in group if r['termination_reason']!='NOT_STARTED' and r['input_state']=='VALID']
            good=[r for r in executed if r['adoptable'] and r['T_program']<=r['budget_wall_s']]
            methods[method]={'planned':len(group),'valid_input_executed':len(executed),'adopted':len(good),
                'not_started':sum(r['termination_reason']=='NOT_STARTED' for r in group),
                'invalid_input':sum(r['input_state']=='INVALID' for r in group),
                'failed_run_ids':[r['run_id'] for r in executed if r not in good],
                'success_wilson':wilson(len(good),len(executed),alpha),
                'success_exact':clopper(len(good),len(executed),alpha),
                'metrics':{k:mean_stats([r[k] for r in good if r.get(k) is not None]) for k in ('D','W','T_program','J')},
                'T_attempt_all':mean_stats([r['T_attempt'] for r in executed]),
                'success_run_ids':[r['run_id'] for r in good]}
        comparisons=[]
        for left,right in [('C','D'),('A','D'),('B','D'),('D_CLASSICAL_REPLACEMENT','D')]:
            for metric in ('D','W','T_program','J'):
                a=methods[left]['metrics'][metric];b=methods[right]['metrics'][metric]
                eligible=min(a['n'],b['n'])>=2
                half=welch_halfwidth(a['variance'],b['variance'],a['n'],b['n'],alpha) if eligible else None
                delta=b['mean']-a['mean'] if a['n'] and b['n'] else None
                comparisons.append({'left':left,'right':right,'metric':metric,'difference_right_minus_left':delta,
                    'CI': [delta-half,delta+half] if half is not None else None,
                    'analysis':'independent Welch; method-specific successful-trial means',
                    'n_left':a['n'],'n_right':b['n'],'zero_sample_variance_warning':eligible and (a['variance']==0 or b['variance']==0)})
        out.append({'case_id':case,'methods':methods,'comparisons':comparisons})
    return out


def demand_components(per_demand):
    """Method means are paired by demand; subtract their sampling noise once.

    Each entry has mean_D, mean_C, variance_D/C, R_D/C. Independent within
    demand method streams; independent demand families, finite variances.
    """
    if len(per_demand)<2: raise ValueError('MULTIPLE_INDEPENDENT_DEMANDS_REQUIRED')
    differences=[x['mean_D']-x['mean_C'] for x in per_demand]
    noise=mean(x['variance_D']/x['R_D']+x['variance_C']/x['R_C'] for x in per_demand)
    return {'observed_variance_of_demand_means':variance(differences),
            'mean_within_sampling_variance':noise,
            'between_variance_moments':max(0.,variance(differences)-noise),
            'M':len(per_demand),'unit':'independent demand family'}


def demand_analysis(per_demand,alpha=.05):
    from scipy.stats import t
    components=demand_components(per_demand)
    differences=[x['mean_D']-x['mean_C'] for x in per_demand]
    half=float(t.ppf(1-alpha/2,len(differences)-1)*math.sqrt(variance(differences)/len(differences)))
    return {**components,'mean_difference':mean(differences),'CI':[mean(differences)-half,mean(differences)+half],
            'note':'variance of demand means already includes within-demand noise; do not add again'}
