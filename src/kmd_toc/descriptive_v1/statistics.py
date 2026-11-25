"""Pure descriptive calculations; no p values, CI, power or J selection."""
import math


def finite(values,*,nonnegative=False):
    out=[]
    for x in values:
        if type(x) not in (int,float) or not math.isfinite(x) or (nonnegative and x<0):
            raise ValueError('FINITE_NUMERIC_OBSERVATIONS_REQUIRED_NO_ZERO_IMPUTATION')
        out.append(float(x))
    return out


def quantile(values,p):
    if not 0<=p<=1:raise ValueError('QUANTILE_PROBABILITY')
    x=sorted(finite(values))
    if not x:return None
    position=(len(x)-1)*p;i=math.floor(position);a=position-i
    return x[i]*(1-a)+x[min(i+1,len(x)-1)]*a


def summary(values,*,independent=False):
    if type(independent) is not bool:raise ValueError('EXPLICIT_INDEPENDENCE_BOOLEAN_REQUIRED')
    x=finite(values);n=len(x)
    mean=math.fsum(x)/n if n else None
    sd=math.sqrt(math.fsum((v-mean)**2 for v in x)/(n-1)) if n>=2 else None
    q1,q3=quantile(x,.25),quantile(x,.75);iqr=q3-q1 if n else None
    inside=[v for v in x if q1-1.5*iqr<=v<=q3+1.5*iqr] if n else []
    return {'J':n,'mean':mean,'SD':sd,'median':quantile(x,.5),'Q1':q1,'Q3':q3,'IQR':iqr,
            'min':min(x) if n else None,'max':max(x) if n else None,
            'whisker_low':min(inside) if inside else None,'whisker_high':max(inside) if inside else None,
            'outliers':[v for v in x if v not in inside],
            'MCSE':sd/math.sqrt(n) if independent and sd is not None else None,
            'MCSE_status':'DEFINED_INDEPENDENT_OUTER_UNITS' if independent and sd is not None else
                'HOLD_INDEPENDENCE_UNCONFIRMED' if not independent else 'UNDEFINED_J_LT_2',
            'observed_zero_SD':sd==0 if sd is not None else False,
            'zero_SD_is_determinism_proof':False,'formal_J':'HOLD'}


def relative(base,value):
    finite([base,value],nonnegative=True)
    return 100*(base-value)/base if base>0 else None


def dual(cD,cW,xD,xW):
    finite([cD,cW,xD,xW],nonnegative=True)
    d,w=relative(cD,xD),relative(cW,xW)
    return min(d,w) if d is not None and w is not None else None


def paired(x,y,*,independent_pairs=False):
    a,b=finite(x,nonnegative=True),finite(y,nonnegative=True)
    if len(a)!=len(b):raise ValueError('REGISTERED_ONE_TO_ONE_PAIRS_REQUIRED')
    differences=[v-u for u,v in zip(a,b)]
    rates=[relative(u,v) for u,v in zip(a,b)]
    return {'kind':'registered_trial_differences','delta':summary(differences,independent=independent_pairs),
            'delta_values':differences,'relative_rate':summary([r for r in rates if r is not None],independent=independent_pairs),
            'relative_rate_values':rates,'undefined_rate_count':rates.count(None)}


def independent_contrast(x,y,*,independent_groups=False):
    if type(independent_groups) is not bool:raise ValueError('EXPLICIT_INDEPENDENCE_BOOLEAN_REQUIRED')
    a=summary(finite(x,nonnegative=True));b=summary(finite(y,nonnegative=True))
    delta=b['mean']-a['mean'] if a['J'] and b['J'] else None
    mcse=math.sqrt(a['SD']**2/a['J']+b['SD']**2/b['J']) if (
        independent_groups and a['SD'] is not None and b['SD'] is not None) else None
    return {'kind':'difference_of_group_means_no_trial_pairing','mean_delta':delta,'SD_delta':None,
            'MCSE_delta':mcse,'relative_rate_of_means':relative(a['mean'],b['mean']) if delta is not None else None,
            'MCSE_status':'DEFINED_INDEPENDENT_GROUPS' if mcse is not None else 'HOLD',
            'trial_difference_distribution':None,'strict_dual_trial_rate':None}


def paired_dual(c,x,*,independent_pairs=False):
    if len(c)!=len(x):raise ValueError('REGISTERED_C_REFERENCES_REQUIRED')
    values=[dual(a['D'],a['W'],b['D'],b['W']) for a,b in zip(c,x)]
    good=sum(b['D']<a['D'] and b['W']<a['W'] for a,b in zip(c,x))
    return {'values':values,'summary':summary([v for v in values if v is not None],independent=independent_pairs),
            'undefined_count':values.count(None),'matched_trials':len(values),'strict_dual_count':good,
            'strict_dual_fraction':good/len(values) if values else None,
            'reference':'C_only','mean_of_trial_I_dual_not_I_dual_of_means':True}
