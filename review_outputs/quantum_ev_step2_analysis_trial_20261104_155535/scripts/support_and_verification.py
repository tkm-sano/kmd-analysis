from common import *
from decimal import Decimal

def matching_dp(a,route):
 n=len(route);m=n//2;unary=[[F(0),F(0)] for _ in range(m)];pairs=[[[F(0),F(0)],[F(0),F(0)]] for _ in range(m-1)];constant=F(0)
 def variable(pos):
  if pos<0 or pos>=n or (n%2 and pos==n//2):return None
  return min(pos,n-1-pos)
 def label(pos,b):
  if pos<0 or pos>=n:return 0
  return route[n-1-pos] if b else route[pos]
 for i,j in zip(range(-1,n),range(0,n+1)):
  vi,vj=variable(i),variable(j)
  if vi is None and vj is None:constant+=F(str(a['travel'][label(i,0),label(j,0)]))
  elif vi is None or vj is None or vi==vj:
   k=vi if vi is not None else vj
   for b in [0,1]:unary[k][b]+=F(str(a['travel'][label(i,b if vi is not None else 0),label(j,b if vj is not None else 0)]))
  else:
   assert abs(vi-vj)==1;k=min(vi,vj)
   for bi,bj in itertools.product([0,1],repeat=2):pairs[k][bi if vi==k else bj][bj if vj==k+1 else bi]+=F(str(a['travel'][label(i,bi),label(j,bj)]))
 dp=[(constant+unary[0][b],[b]) for b in [0,1]]
 for k in range(1,m):dp=[min((dp[a][0]+pairs[k-1][a][b]+unary[k][b],dp[a][1]+[b]) for a in [0,1]) for b in [0,1]]
 cost,bits=min(dp);chosen=route.copy()
 for i,b in enumerate(bits):
  if b:chosen[i],chosen[n-1-i]=chosen[n-1-i],chosen[i]
 assert objective(a,[0,*chosen,0])==cost
 return cost,bits

def main():
 t=time.perf_counter();base=frame(P/'B_CLASSICAL_INITIAL_BASELINES.csv',dtype=str);meta={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')};active=frame(P/'B_ACTIVE_GRID_SELECTION.csv',dtype=str).set_index('problem_id');rows=[]
 for x in base.to_dict('records'):
  pid=x['problem_id'];a=arr(meta[pid]['instance_path']);route=json.loads(x['initial_route'])[1:-1];cost,bits=matching_dp(a,route);initial=objective(a,[0,*route,0]);ck('same mirror support exact DP equals initial',cost==initial,pid)
  if len(route)<=5:
   allcost=[]
   for bs in itertools.product([0,1],repeat=len(route)//2):
    r=route.copy()
    for i,b in enumerate(bs):
     if b:r[i],r[-1-i]=r[-1-i],r[i]
    allcost.append(objective(a,[0,*r,0]))
   ck('independent matching DP checked by enumeration',cost==min(allcost),pid)
  act=active.loc[pid];raw=js(pin(act.source_path,'active source grid',act.source_sha256));ck('active grid selected initial t0',float(raw['selected_t'])==float(act.selected_t)==0.,pid)
  rows.append(dict(problem_id=pid,scale=x['scale'],n_customers=len(route),binary_pair_directions=len(route)//2,matching_support_size=str(2**(len(route)//2)),initial_fraction=str(initial),exact_matching_orbit_fraction=str(cost),matching_orbit_min_equals_initial=cost==initial,DP_best_bits=json.dumps(bits),active_selected_t=float(raw['selected_t']),scope='restricted mirror orbit exact DP; not full global optimum'))
 table('PATH1_SUPPORT_AUDIT.csv',rows)
 # Independent aggregate checks from long paired rows and reported denominators.
 pairs=frame(O/'PATH1_PAIRED_COMPARISONS.csv');summary=frame(O/'PATH1_STATISTICAL_RESULTS.csv');exact=frame(O/'EXACT_REFERENCE_STATUS.csv');ck('accepted exact414',exact.exact_fraction.ne('').sum()==414)
 for row in summary.to_dict('records'):
  g=pairs[(pairs.config_id==row['config_id'])&(pairs.classical_method==row['classical_method'])]
  if row['scale']!='ALL':g=g[g.scale==row['scale']]
  ck('reported scheduled/valid counts',len(g)==int(row['scheduled_measurement_reps'])==int(row['valid_reps']),row['config_id'])
  ck('equal rep counts input-first mean agrees explicit two-stage',abs(float(row['input_mean_delta_J_mean'])-g.groupby('problem_id').delta_J_s.mean().mean())<1e-9,row['config_id'])
  ck('reported strict improvement count exact',sum(F(str(v))>0 for v in g.delta_J_fraction)==int(row['improving_reps']),row['config_id'])
  ck('exact denominator matches source status',int(row['exact_reps'])==10*g[g.exact_available].problem_id.nunique(),row['config_id'])
 # Hierarchy and seeds.
 g=pairs[pairs.primary_comparison];ck('B hierarchy groups25 parents26 input460',g.group_id.nunique()==25 and g.parent_id.nunique()==26 and g.problem_id.nunique()==460);ck('B repetitions10 and configs8',g.groupby(['problem_id','config_id']).size().eq(10).all() and g.groupby('problem_id').config_id.nunique().eq(8).all())
 # Tightest available lower is distinguished from independent LP lower.
 rec=frame(O/'evidence/EXACT_FULL_RESULTS.csv',dtype=str).set_index('problem_id');bound=[]
 for x in exact.to_dict('records'):
  if str(x['old_exact_available'])!='False':continue
  r=rec.loc[x['problem_id']];oldL=F(x['old_lower_fraction']);indL=F(r.certified_lower_fraction);Uval=F(r.feasible_upper_fraction);bestL=max(oldL,indL)
  ck('best available lower<=upper',bestL<=Uval,x['problem_id'])
  bound.append(dict(problem_id=x['problem_id'],scale=x['scale'],new_exact_available=x['exact_fraction']!='',saved_SCIP_lower_fraction=str(oldL),independent_LP_lower_fraction=str(indL),best_available_lower_fraction=str(bestL),verified_feasible_upper_fraction=str(Uval),best_available_gap_upper_s=float(Uval-bestL),independent_LP_gap_upper_s=float(Uval-indL),best_available_gap_upper_percent=100*float((Uval-bestL)/bestL),independent_LP_gap_upper_percent=100*float((Uval-indL)/indL),best_lower_evidence='independently validated rational LP dual' if indL>=oldL else 'saved exact SCIP MIP lower; no external VIPR proof',status='PASS_NEW_EXACT' if x['exact_fraction'] else 'HOLD_NONZERO_BOUND_GAP'))
 table('EXACT_REFERENCE_BOUND_COMPARISON.csv',bound)
 # Endpoint and cancellation verification from exported long model results.
 sens=frame(O/'PATH2_SENSITIVITY_RESULTS.csv');su=frame(O/'PATH2_SENSITIVITY_SUMMARY.csv')
 for row in su.to_dict('records'):
  z=sens[(sens.model==row['model'])&(sens.case_id==row['case_id'])&(sens.rolling_case==row['rolling_case'])];ck('C trajectory denominator460',len(z)==460 and z.trajectory_sha256.nunique()==460,row['case_id']);ratio=100*math.fsum(z.delta_DC_Wh)/math.fsum(z.baseline_DC_Wh);ck('C weighted ratio reconstructed by fsum',abs(ratio-float(row['total_weighted_saving_percent']))<1e-10,row['case_id'])
 ck('C cancellation endpoints zero',sens[(sens.model=='T08')&(sens.case_id=='CANCEL+0')].delta_DC_Wh.abs().max()<1e-10)
 ck('T09 completed pack remains NULL',frame(O/'PATH2_T09_COMMON_INPUT_SENSITIVITY.csv').complete_pack_mass_LP_kg.eq('').all())
 finish('INDEPENDENT_VERIFICATION',t,dict(mirror_supports=len(rows),primary_improving_plans=int(g.improves.sum()),B_saved_plans=len(g),accepted_exact=414,remaining_unproved=46))
if __name__=='__main__':main()
