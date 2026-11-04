from common import *
t=time.perf_counter();raw=frame(O/'experiments/QAOA_MAIN_FITS.csv');rep=frame(O/'experiments/QAOA_MAIN_MEASUREMENTS.csv',dtype=str);keys=['problem_id','support','initial_state','mixer','layers','method','learning_rep'];groups=rep.groupby(keys);changes=[];correct={}
for key,g in groups:
 vals=[F(v) for v in g.objective_fraction];sd=0. if len(set(vals))==1 else float(np.std(list(map(float,vals)),ddof=1));correct[key]=sd
public=frame(O/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv')
for i,x in public.iterrows():
 key=tuple(str(x[k]) for k in keys);new=correct[key];old=float(x.sd_objective_s)
 if old!=new:changes.append(dict(zip(keys,key))|dict(original_float_SD_s=old,fraction_based_SD_s=new,reason='exact objective fractions all identical => SD0; preserve raw experiment file'))
 public.loc[i,'sd_objective_s']=new
ck('SD correction only numerical-zero cases',all(abs(x['original_float_SD_s']-x['fraction_based_SD_s'])<1e-10 for x in changes))
table('QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv',public);summary=frame(O/'QAOA_CONTROLLED_CELL_SUMMARY.csv');k2=keys[:-1]
for i,x in summary.iterrows():
 g=public
 for k in k2:g=g[g[k].astype(str)==str(x[k])]
 ck('97 fit count during SD normalization',len(g)==97,x.problem_id);summary.loc[i,'mean_within_measurement_sd_s']=g.sd_objective_s.mean()
table('QAOA_CONTROLLED_CELL_SUMMARY.csv',summary);table('evidence/CONTROLLED_SD_NUMERICAL_REVIEW.csv',changes);finish('CONTROLLED_SD_REVIEW',t,dict(numerical_zero_sd_corrections=len(changes),raw_experiment_unchanged=True))
