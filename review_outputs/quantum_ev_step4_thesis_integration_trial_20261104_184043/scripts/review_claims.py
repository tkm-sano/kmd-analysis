from pathlib import Path
import pandas as pd,json,math
from fractions import Fraction as F
O=Path(__file__).resolve().parents[1];R=O.parents[1];S3=R/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535'
c=pd.read_csv(S3/'CONTRIBUTION_CONDITIONS_FINAL.csv',keep_default_na=False);trace=pd.read_csv(S3/'EVIDENCE_TRACEABILITY.csv');review=[]
for x in c.to_dict('records'):
 where='4.1–4.5' if x['path']=='path1' else '5.1–5.4' if x['path']=='path2' else '6.1–6.4'
 if x['result_role']=='条件付き参考例':where='5.5 条件付き参考シナリオ'
 recommendation={'PASS':'A','CONDITIONAL':'B','HOLD':'C','FAIL':'D'}[x['audit_status']]
 review.append(dict(claim_id=x['claim_id'],claim=x['claim_text'],RQ=x['RQ'],source_data=x['source_files'],analysis_method=x['method'],statistical_basis=x['statistical_evaluation'],model_assumptions=x['applicability'],scope=x['generalization_scope'],scientific_judgment=x['audit_status'],adoption_recommendation=recommendation,thesis_location=where,required_wording='参考例・入力未採用を毎回明記' if x['Chen_dependency']=='YES' else '保存計算/モデル/数式/未検証を区別',unresolved=x['unverified_links'],role=x['result_role'],Chen_dependency=x['Chen_dependency'],formal_adoption='NOT_DECIDED'))
pd.DataFrame(review).to_csv(O/'CLAIM_ADOPTION_REVIEW.csv',index=False)
trace.merge(pd.DataFrame(review)[['claim_id','thesis_location','adoption_recommendation']],on='claim_id').to_csv(O/'STEP3_TO_THESIS_EVIDENCE_MATRIX.csv',index=False)
checks=[]
def ck(n,v,src,detail):checks.append(dict(item=n,status='PASS' if v else 'FAIL',source=str(src),detail=detail));assert v,n
p=pd.read_csv(S2/'PATH1_PAIRED_COMPARISONS.csv',keep_default_na=False);p=p[p.primary_comparison];ck('460×8×10=36800',len(p)==36800 and p.problem_id.nunique()==460 and p.config_id.nunique()==8 and p.groupby(['problem_id','config_id']).size().eq(10).all(),S2/'PATH1_PAIRED_COMPARISONS.csv','旧Aと区別')
ck('primary improvement0 and feasible best',all(F(x)<=0 for x in p.delta_J_fraction) and p.feasible.all(),S2/'PATH1_PAIRED_COMPARISONS.csv','saved-best率；raw-shot率と区別')
g=p[(p.scale=='R5')&(p.config_id=='GROVER_P2')].groupby('problem_id').delta_J_s.mean();ck('R5 mean/SD70',len(g)==70 and abs(g.mean()+5983.70645268941)<1e-9 and abs(g.std(ddof=1)-1314.3645367770923)<1e-9,S2/'PATH1_PAIRED_COMPARISONS.csv',f'mean={g.mean()},SD={g.std(ddof=1)}')
s=pd.read_csv(S2/'PATH1_SUPPORT_AUDIT.csv');ck('mirror support460',len(s)==460 and s.matching_orbit_min_equals_initial.all() and all(F(a)<=F(b) for a,b in zip(p.JC_fraction,p.initial_fraction)),S2/'PATH1_SUPPORT_AUDIT.csv','支持内最良＝初期、greedy≤初期')
r=pd.read_csv(S2/'EXACT_REFERENCE_STATUS.csv',keep_default_na=False);ck('414/46/41',r.exact_fraction.ne('').sum()==414 and r.exact_fraction.eq('').sum()==46 and r.reference_evidence_class.eq('SAVED_EXACT_MIP_EQUALITY_NO_EXTERNAL_VIPR').sum()==41,S2/'EXACT_REFERENCE_STATUS.csv','外部証明留保を維持')
q=pd.read_csv(O/'data/QAOA_CONTROLLED_CELL_SUMMARY.csv');ck('96cells×97fit×10rep',len(q)==96 and q.independent_learning_fits.eq(97).all(),S2/'QAOA_CONTROLLED_CELL_SUMMARY.csv','9312fit/93120rep')
for layer,k in [(1,58),(2,78)]:
 x=q[(q.problem_id=='R1_020')&(q.support=='FULL_PERMUTATION')&(q.initial_state=='BASIS_INITIAL')&(q.mixer=='GRAPH_SWAP')&(q.layers==layer)&(q.method=='QAOA')].iloc[0];n=97;z=1.959963984540054;ph=k/n;mid=(ph+z*z/(2*n))/(1+z*z/n);half=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/(1+z*z/n);ck('primary optimal Wilson p'+str(layer),x.primary_optimal_rep0_count==k and abs(x.primary_optimal_Wilson95_lower-(mid-half))<1e-12,S2/'QAOA_CONTROLLED_CELL_SUMMARY.csv','差の有意性検定ではない')
d=pd.read_csv(O/'data/DC_MASS_KERNEL_INDEPENDENT.csv');ck('920 paired positive DC slope',len(d)==920 and d.trajectory_sha256.nunique()==460 and d.groupby('trajectory_sha256').size().eq(2).all() and (d.right_derivative_lo_Wh_kg>0).all() and (d.mass_lo_kg==1000).all() and (d.mass_hi_kg==1250).all() and d.Chen_capacity_input.eq('NONE').all(),S3/'data/DC_MASS_KERNEL_INDEPENDENT.csv','固定モデル・実車ではない')
t09=pd.read_csv(O/'data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv');ck('T09 complete pack NULL',t09.complete_pack_mass_LP_kg.isna().all() and t09.complete_pack_mass_S_kg.isna().all(),S2/'PATH2_T09_COMMON_INPUT_SENSITIVITY.csv','未知量補完なし')
# Symbolic derivatives: no arbitrary material values or new experiment.
# Independent monomial differentiation of E*V^-1*q^-1*u^-1*fp^-1 + E*V^-1*r*qn^-1*fn^-1.
names=['E','V','q','u','fp','r','qn','fn'];terms=[(1,(1,-1,-1,-1,-1,0,0,0)),(1,(1,-1,0,0,0,1,-1,-1))]
expect={'q':[(-1,(1,-1,-2,-1,-1,0,0,0))],'u':[(-1,(1,-1,-1,-2,-1,0,0,0))],'V':[(-1,(1,-2,-1,-1,-1,0,0,0)),(-1,(1,-2,0,0,0,1,-1,-1))],'fp':[(-1,(1,-1,-1,-1,-2,0,0,0))],'r':[(1,(1,-1,0,0,0,0,-1,-1))],'qn':[(-1,(1,-1,0,0,0,1,-2,-1))],'fn':[(-1,(1,-1,0,0,0,1,-1,-2))]}
for name,expected in expect.items():
 j=names.index(name);derived=[]
 for coeff,powers in terms:
  if powers[j]:
   ex=list(powers);ex[j]-=1;derived.append((coeff*powers[j],tuple(ex)))
 ck('T08 analytical derivative '+name,sorted(derived)==sorted(expected),O/'data/PATH2_ANALYTICAL_SENSITIVITY.csv','power-law symbolic check; other variables/D fixed')
qL=F('171.875');qS=F('195.959596');mass=lambda q,u=F(1),v=F('3.5'):F(20000)/v*(1/(q*u*F('.75'))+F('1.1')/(360*F('.98')))+34
b=mass(qL)-mass(qS);ustar=qL/qS;vstar=20000*(1/(qS*F('.75'))+F('1.1')/(360*F('.98')))/(mass(qL)-34);ck('reference boundaries only',abs(float(b)-5.448297415076934)<1e-12 and abs(float(ustar)-.8770940719841043)<1e-14 and abs(float(vstar)-3.193155683779789)<1e-13,S2/'scripts/path2_analysis.py','Chen依存参考；採用PASSへの昇格なし')
pd.DataFrame(checks).to_csv(O/'NUMERICAL_INTEGRITY_AUDIT.csv',index=False)
(O/'REJECTED_OR_DEFERRED_CLAIMS.md').write_text('''# 不採用・再検討の対象
Cは未証明参照、未検証接続、入力採用等の保留であり、その効果を採用しない。保留の存在自体は本文で明示する。科学的判定とA〜D推奨は別軸で、正式採否は未決定である。
量子最適化一般の不可能性、QPU速度、実EV削減、量子による実材料改善、T09完成pack確定、p2一般有意優位という無限定主張はD（不採用推奨）である。31主張の限定表現と異なる強い読み替えを棄却しているのであり、元台帳に同じ誤文が存在するという意味ではない。
''')
(O/'CHEN_REFERENCE_USAGE_AUDIT.md').write_text('''# Chen参考例の利用監査
Step3修正後の採用判断を優先する。121/.704と194/.99は100cycle保持試験の分母逆算であり、初回放電実測/full-cell設計の確定値として未採用HOLDである。T08解析感度・一般境界と材料非依存DC応答を主分析に置き、具体LP/S値は5.5節の参考例に限定する。旧資料の49点/uV/T09格子、DC約0.413%もChen依存を保持する。
保存付録では旧記述を履歴として保全し、現在の推奨と明確に分離する。旧図に大きな削減値が残っていても、その原データ値を削除せず参考・旧条件と表示する。主本文の結果と要旨に実EV/完成pack/量子材料改善を記載しない。一般b−δと参考b=5.448297kgは別の主張である。
''')
print('Claims',len(review),'recommendations',pd.DataFrame(review).adoption_recommendation.value_counts().to_dict(),'numerical checks',len(checks))
