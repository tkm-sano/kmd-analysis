from pathlib import Path
from fractions import Fraction as F
import pandas as pd,numpy as np
O=Path(__file__).resolve().parents[1];R=O.parents[1];S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';checks=pd.read_csv(O/'NUMERICAL_INTEGRITY_AUDIT.csv').to_dict('records')
def ck(n,v,src,d):checks.append(dict(item=n,status='PASS' if v else 'FAIL',source=str(src),detail=d));assert v,n
p=pd.read_csv(S2/'PATH1_PAIRED_COMPARISONS.csv',keep_default_na=False,low_memory=False);p=p[p.primary_comparison];ck('Delta sign equation independently recomputed',all(F(a)-F(b)==F(c) for a,b,c in zip(p.JC_fraction,p.JQ_fraction,p.delta_J_fraction)),S2/'PATH1_PAIRED_COMPARISONS.csv','JC−JQ；全36800')
r=pd.read_csv(S2/'PATH1_RUNTIME_RESULTS.csv',low_memory=False);ck('9603 CPU runtime records',len(r)==9603 and r.QPU_execution.eq(False).all(),S2/'PATH1_RUNTIME_RESULTS.csv','9312fit pipeline+291greedy；公平な総時間比ではない')
ex=r[(r.problem_id=='R1_001')&(r.config_id=='FULL_PERMUTATION/UNIFORM_SUPPORT/PROJECTOR/p2')]
for method,expected in [('QAOA',34.643),('DEPHASED',35.014)]:
 g=ex[ex.method==method];ck('runtime fixed-scope median '+method,len(g)==97 and abs(1000*g.total_wall_s.median()-expected)<.001,S2/'PATH1_RUNTIME_RESULTS.csv',str(1000*g.total_wall_s.median())+'ms；学習+10測定')
t=pd.read_csv(O/'data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv');g=t[(t.uS==1)&(t.V_common==3.5)].set_index('policy');ck('T09 conditional endpoints',abs(g.loc['fixed_loading','b_known_kg']-9.722608121107783)<1e-10 and abs(g.loc['fixed_area_LP','b_known_kg']-5.977891152148871)<1e-10,O/'data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv','Chen逆算qに依存；未知BOM NULL')
d=pd.read_csv(O/'data/DC_MASS_KERNEL_INDEPENDENT.csv');s=pd.read_csv(O/'data/DC_MASS_KERNEL_SUMMARY.csv').set_index('rolling_case')
for rc,g in d.groupby('rolling_case'):
 ck('DC mass distribution summary '+rc,abs(g.right_derivative_lo_Wh_kg.mean()-s.loc[rc,'slope_mean'])<1e-12 and abs(g.right_derivative_lo_Wh_kg.std(ddof=1)-s.loc[rc,'slope_SD'])<1e-12,O/'data/DC_MASS_KERNEL_INDEPENDENT.csv','軌跡分布；材料モデル誤差CIではない')
e=pd.read_csv(S2/'PATH2_SENSITIVITY_RESULTS.csv');e=e[(e.model=='T08')&(e.case_id=='Q48')];su=pd.read_csv(O/'data/DC_ENDPOINT_RECHECK.csv').set_index('Crr')
for rc,g in e.groupby('rolling_case'):
 ck('Chen reference DC aggregation '+rc,len(g)==460 and abs(100*g.delta_DC_Wh.sum()/g.baseline_DC_Wh.sum()-su.loc[rc,'total_ratio_percent'])<1e-10 and abs(g.individual_saving_percent.std(ddof=1)-su.loc[rc,'individual_SD_pp'])<1e-10,S2/'PATH2_SENSITIVITY_RESULTS.csv','総和比/個別平均/SDを分離；参考のみ')
pd.DataFrame(checks).to_csv(O/'NUMERICAL_INTEGRITY_AUDIT.csv',index=False);print('Numerical checks',len(checks))
