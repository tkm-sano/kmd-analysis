from common import *
t=time.perf_counter();p=frame(O/'PATH1_PAIRED_COMPARISONS.csv');p=p[p.primary_comparison];rows=[]
for scale in sorted(p.scale.unique())+['ALL']:
 for cfg,g in p.groupby('config_id'):
  if scale!='ALL':g=g[g.scale==scale]
  k=int(g.improves.sum());n=len(g);N=g.problem_id.nunique();ck('measurement seed entropy unique per setting scope',g.measurement_seed_entropy.nunique()==n,cfg);ck('equal10rep per fixedinput',g.groupby('problem_id').size().eq(10).all())
  # With k=0 and independent measurement streams conditional on all fixed fits,
  # P(K=0)=prod_i(1-p_i)^10 <= (1-pbar)^(10*N) by log concavity.
  # The confidence procedure returns1 when K>0, so coverage is >=.95 for heterogeneous pi.
  upper=-math.expm1(math.log(.05)/n) if k==0 else 1.
  rows.append(dict(scale=scale,config_id=cfg,fixed_inputs=N,fixed_fits=N,measurement_streams=n,improving_streams=k,observed_improvement_fraction=k/n,one_sided95_upper_mean_measurement_success_probability=upper,upper_percent=100*upper,method='zero-event bound for mean heterogeneous Bernoulli probability; independent PRNG measurement streams conditional on all fixed learned fits',derivation='P(K=0)=product_i(1-p_i)^10 <= (1-pbar)^(10N); upper=1-alpha^(1/(10N)); for K>0 return1',scope='finite saved input+fit cohort only; not training stability, unseen inputs, real fleet, or QPU'))
table('PATH1_ZERO_SUCCESS_FIXED_FIT_BOUND.csv',rows);finish('ZERO_SUCCESS_BOUND',t,dict(rows=len(rows),scope='exploratory supplemental zero-event conditional bound; main bootstrap methods unchanged'))
