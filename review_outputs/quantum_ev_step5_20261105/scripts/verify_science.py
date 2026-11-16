from pathlib import Path
import sys,hashlib,json
from fractions import Fraction as F
import numpy as np,pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate
S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S4=R/'review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043'
pins=[];checks=[]
def pin(p):
 p=Path(p);h=hashlib.sha256(p.read_bytes()).hexdigest();pins.append(dict(path=str(p),sha256=h,bytes=p.stat().st_size));return p

def ck(n,v):
 checks.append(dict(check=n,status='PASS' if v else 'FAIL'));assert v,n
sp=pd.read_csv(pin(S2/'PATH1_SUPPORT_AUDIT.csv'));pa=pd.read_csv(pin(S2/'PATH1_PAIRED_COMPARISONS.csv'),keep_default_na=False,low_memory=False);pa=pa[pa.primary_comparison].drop_duplicates('problem_id').set_index('problem_id')
ck('matching support460 exact minima',len(sp)==460 and all(F(x.exact_matching_orbit_fraction)==F(x.initial_fraction) for x in sp.itertuples()))
ck('greedy not worse than initial460',all(F(x.JC_fraction)<=F(x.initial_fraction) for x in pa.itertuples()))
ck('active grid all t0 only',sp.active_selected_t.eq(0).all())
k=pd.read_csv(pin(S4/'data/DC_MASS_KERNEL_INDEPENDENT.csv'));summary=pd.read_csv(pin(S4/'data/DC_MASS_KERNEL_SUMMARY.csv')).set_index('rolling_case');freeze=json.loads(pin(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text());pin(R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py')
ck('920 conditions paired over 460 trajectories',len(k)==920 and k.trajectory_sha256.nunique()==460 and k.groupby('trajectory_sha256').size().eq(2).all())
results=[]
for h,g in k.groupby('trajectory_sha256'):
 p=pin(g.iloc[0].trajectory_path);ck('trajectory hash '+h,hashlib.sha256(p.read_bytes()).hexdigest()==h)
 data=pd.read_csv(p,usecols=['timestamp_s','speed_m_s']);t=data.timestamp_s.to_numpy();v=data.speed_m_s.to_numpy();cur=v[1:];ds=cur*np.diff(t);dv=cur**2-v[:-1]**2
 for x in g.itertuples():
  pressure=4.5 if x.rolling_case=='CRR_LOWER_BOUND' else 2.6;crr=.005+(.01+.0095*(3.6*cur/100)**2)/pressure
  a=(9.80665*crr*ds+.5*dv)/3600;c=(.5*61*dv+.5*1.2041*1.175*cur**2*ds)/3600;z=a*1000+c
  slope=(a[z>0].sum()+a[(z==0)&(a>0)].sum())/.9
  errors=[]
  for mass,exp in [(1000,x.DC_lo_Wh),(1250,x.DC_hi_Wh)]:
   fresh=np.maximum(a*mass+c,0).sum()/.9;actual,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':mass});errors.extend([abs(fresh-exp),abs(actual['net_DC_Wh']-exp)])
  ck('DC algebra and frozen readback '+h+' '+x.rolling_case,max(errors)<1e-7 and abs(slope-x.right_derivative_lo_Wh_kg)<1e-10 and slope>0)
  results.append(dict(trajectory_sha256=h,rolling_case=x.rolling_case,recomputed_slope_Wh_kg=slope,max_endpoint_error_Wh=max(errors)))
for rc,g in k.groupby('rolling_case'):
 ck('DC summary '+rc,abs(g.right_derivative_lo_Wh_kg.mean()-summary.loc[rc,'slope_mean'])<1e-12 and abs(g.right_derivative_lo_Wh_kg.std(ddof=1)-summary.loc[rc,'slope_SD'])<1e-12)
pd.DataFrame(results).to_csv(O/'data/DC_STEP5_RECHECK.csv',index=False);pd.DataFrame(checks).to_csv(O/'evidence/SCIENCE_CHECKS.csv',index=False);pd.DataFrame(pins).drop_duplicates('path').to_csv(O/'evidence/SCIENCE_INPUT_SHA256.csv',index=False)
(O/'evidence/SCIENCE_RESULT.json').write_text(json.dumps(dict(checks=len(checks),failures=0,scope='existing fixed evidence and frozen endpoint readback; no new material or quantum experiments'),indent=2));print('science verification',len(checks),'PASS')
