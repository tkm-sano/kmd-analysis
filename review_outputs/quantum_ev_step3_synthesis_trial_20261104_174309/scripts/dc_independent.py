from pathlib import Path
import os
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,json,time,hashlib
import numpy as np,pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate
start=time.perf_counter();S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';op=pd.read_csv(S2/'PATH2_OPERATION_CONDITION_ANALYSIS.csv');manifest=pd.read_csv(O/'STEP3_SOURCE_MANIFEST.csv');paths=dict(zip(manifest.sha256,manifest.path));freeze=json.loads((R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text());out=[]
for h,g in op.groupby('trajectory_sha256'):
 p=Path(paths[h]);assert hashlib.sha256(p.read_bytes()).hexdigest()==h
 d=pd.read_csv(p,usecols=['timestamp_s','speed_m_s']);t=d.timestamp_s.to_numpy();v=d.speed_m_s.to_numpy();cur=v[1:];ds=cur*np.diff(t);dv=cur**2-v[:-1]**2
 for case,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
  crr=.005+(.01+.0095*(3.6*cur/100)**2)/pressure
  a=(9.80665*crr*ds+.5*dv)/3600
  c=(.5*61*dv+.5*1.2041*1.175*cur**2*ds)/3600
  # Sum max of affine terms is convex; right derivative is nondecreasing.
  z=a*1000+c;right_at_lo=(a[z>0].sum()+a[(z==0)&(a>0)].sum())/.9
  zhi=a*1250+c;left_at_hi=(a[zhi>0].sum()+a[(zhi==0)&(a<0)].sum())/.9
  e0=np.maximum(z,0).sum()/.9;e1=np.maximum(zhi,0).sum()/.9
  for mass,expected in [(1000,e0),(1250,e1)]:
   actual,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':mass});assert abs(actual['net_DC_Wh']-expected)<1e-7
  assert right_at_lo>0 and left_at_hi>=right_at_lo-1e-10 and e1>e0
  x=g.iloc[0];out.append(dict(trajectory_sha256=h,trajectory_path=str(p),rolling_case=case,scale=x.scale,group_id=x.group_id,mass_lo_kg=1000,mass_hi_kg=1250,DC_lo_Wh=e0,DC_hi_Wh=e1,DC_increase_Wh=e1-e0,right_derivative_lo_Wh_kg=right_at_lo,left_derivative_hi_Wh_kg=left_at_hi,positive_dv2=float(np.maximum(dv,0).sum()),distance_km=ds.sum()/1000,moving_mean_speed_m_s=cur[cur>0].mean(),Chen_capacity_input='NONE',value_type='deterministic frozen model; mass interval from Step2',status='CONDITIONAL'))
out=pd.DataFrame(out);out.to_csv(O/'data/DC_MASS_KERNEL_INDEPENDENT.csv',index=False)
su=out.groupby('rolling_case').agg(n=('trajectory_sha256','size'),slope_min=('right_derivative_lo_Wh_kg','min'),slope_median=('right_derivative_lo_Wh_kg','median'),slope_mean=('right_derivative_lo_Wh_kg','mean'),slope_SD=('right_derivative_lo_Wh_kg','std'),slope_max=('right_derivative_lo_Wh_kg','max')).reset_index();su.to_csv(O/'data/DC_MASS_KERNEL_SUMMARY.csv',index=False)
(O/'evidence/DC_INDEPENDENT_RUN.json').write_text(json.dumps(dict(wall_s=time.perf_counter()-start,rows=len(out),min_slope=out.right_derivative_lo_Wh_kg.min(),materials_used=False,environment=sys.version),indent=2));print(su.to_string(index=False))
