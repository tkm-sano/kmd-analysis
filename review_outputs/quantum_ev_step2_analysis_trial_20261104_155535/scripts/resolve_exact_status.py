from common import *
t=time.perf_counter();d=frame(O/'EXACT_REFERENCE_STATUS.csv',dtype=str);q=frame(O/'evidence/EXACT_FULL_RESULTS.csv',dtype=str).set_index('problem_id');impact=[]
for i,x in d.iterrows():
 old=x.old_exact_available=='True';oldv=F(x.old_exact_fraction) if x.old_exact_fraction else None
 if x.problem_id in q.index:
  r=q.loc[x.problem_id];newub=F(r.feasible_upper_fraction)
  if old:ck('new independent feasible tour does not refute old exact reference',newub>=oldv,x.problem_id,float(newub-oldv))
  indep=r.status=='PASS_EXACT_INDEPENDENT_DUAL'
  if old and not indep:
   # A weaker LP relaxation cannot invalidate a saved exact MIP proof.
   d.loc[i,'exact_fraction']=x.old_exact_fraction;d.loc[i,'status']='CONDITIONAL_SAVED_EXACT_MIP_EQUALITY';d.loc[i,'exact_source']=x.source_certificate
  d.loc[i,'independent_LP_certificate']=indep;d.loc[i,'reference_evidence_class']='INDEPENDENT_RATIONAL_DUAL' if indep else 'SAVED_EXACT_MIP_EQUALITY_NO_EXTERNAL_VIPR' if old else 'UNPROVED_VALID_BOUNDS'
  impact.append(dict(problem_id=x.problem_id,old_available=old,old_value_fraction=x.old_exact_fraction,new_independent_LP_certificate=indep,accepted_exact_available=old or indep,accepted_exact_fraction=d.loc[i,'exact_fraction'],old_vs_new_difference_s=float(F(d.loc[i,'exact_fraction'])-oldv) if old and d.loc[i,'exact_fraction'] else None,reason='independent exact LP equality' if indep else 'saved MIP exact bound=witness retained; weaker DFJ LP does not refute it' if old else 'nonzero rational lower-upper gap retained'))
 else:
  d.loc[i,'independent_LP_certificate']='not applicable';d.loc[i,'reference_evidence_class']='RECHECKED_ENUMERATION' if int(x.n_customers)<=5 else 'SAVED_EXACT_INTEGER_HELD_KARP_DP'
 d.loc[i,'accepted_exact_available']=bool(d.loc[i,'exact_fraction'])
table('EXACT_REFERENCE_STATUS.csv',d);table('EXACT_REFERENCE_IMPACT_DETAILS.csv',impact)
finish('EXACT_RESOLVED',t,dict(accepted_exact=int(d.accepted_exact_available.astype(bool).sum()),newly_proved=sum((x['old_available']==False and x['new_independent_LP_certificate']) for x in impact),old_reference_contradictions=0))
