from pathlib import Path
import os,json
O=Path(__file__).resolve().parents[1];os.environ['MPLCONFIGDIR']=str(O/'logs/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
import pandas as pd
font=FontProperties(fname='/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf');plt.rcParams.update({'font.family':['DejaVu Sans',font.get_name()],'font.size':12,'pdf.fonttype':42,'savefig.dpi':180})
index=[];nodes=[]
def save(fig,folder,name,title,source,dep):
 for ext in ['png','pdf']:fig.savefig(O/f'{folder}/{name}.{ext}',bbox_inches='tight',facecolor='white')
 index.append(dict(id=name,title=title,path=f'{folder}/{name}.png',source=source,Chen_dependency=dep));plt.close(fig)
def base(title):
 f,a=plt.subplots(figsize=(12,6));a.set(xlim=(0,12),ylim=(0,6));a.axis('off');a.text(.2,5.7,title,fontsize=18,weight='bold');return f,a
def box(a,x,y,w,h,txt,kind='verified'):
 color={'verified':'#e5f1ed','model':'#e7eef8','hold':'#f5eee5','reference':'#f7e6ec'}[kind]
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',facecolor=color,edgecolor='#435267',linestyle='--' if kind=='hold' else '-',lw=1.2));a.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=11)
 nodes.append(dict(text=txt,kind=kind,x=x,y=y,width=w,height=h))
def arrow(a,p,q,dashed=False):a.annotate('',xy=q,xytext=p,arrowprops=dict(arrowstyle='->',color='#435267',lw=1.4,linestyle='--' if dashed else '-'))
f,a=base('図1 研究対象と二つの経路：計算確認と未検証接続')
for y,label in [(3.7,'経路1'),(1.65,'経路2')]:a.text(.2,y+.4,label,fontsize=13,weight='bold')
for x,txt,k in [(1.25,'量子最適化\nCPU計算','verified'),(4,'保存経路計画\nΔJで古典と比較','verified'),(6.8,'採用・時間条件\nH_plan未設定','hold'),(9.5,'実道路の\n運用成果','hold')]:box(a,x,3.3,2.1,1.3,txt,k)
for x in [3.35,6.1,8.9]:arrow(a,(x,3.95),(x+.65,3.95),x>6)
for x,txt,k in [(1.25,'量子物性予測\n→材料実現','hold'),(4,'仮定した設計入力\nT08/T09会計','model'),(6.8,'固定軌跡DC\n質量応答','model'),(9.5,'完成pack・実EV\n適格性/実測','hold')]:box(a,x,1.2,2.1,1.3,txt,k)
for x in [3.35,6.1,8.9]:arrow(a,(x,1.85),(x+.65,1.85),x!=6.1)
a.text(.3,.35,'実線：指定された計算・モデル範囲　破線：未検証接続　材料入力の実現は未実証',fontsize=12)
save(f,'CROSS_PATH_FIGURES','F1_two_paths','研究対象と検証範囲','STEP3_CLAIM_REGISTER.csv','STRUCTURE_NO')
f,a=base('図2 経路1：候補存在・取得・品質・時間を別判定する')
box(a,.4,3.35,2.5,1.25,'探索支持S\n必要：J*_S < J_C');box(a,3.4,3.35,2.5,1.25,'取得過程\n初期・mixer・層・学習');box(a,6.4,3.35,2.5,1.25,'主対照との差\nΔJ = J_C − J_Q');box(a,9.4,3.35,2.1,1.25,'時間適合\nτ_total ≤ H_plan','hold')
for x in [2.9,5.9,8.9]:arrow(a,(x,4),(x+.5,4))
box(a,.4,1.15,3.15,1.25,'mirror 460入力\nJ*_S = J_initial ≥ J_C\n支持内で正改善不可')
box(a,4.05,1.15,3.15,1.25,'3診断入力の取得比較\n最適取得とgreedy超えは別\n58/97・78/97は限定観測')
box(a,7.7,1.15,3.8,1.25,'B系列：正改善0/36,800\n観測0 ≠ 一般的不可能性\n実運用への伝達は未検証','hold')
a.text(.4,.4,'CPUシミュレーションをQPU性能へ換算しない。脱位相は機構対照、greedyは主品質対照。',fontsize=12)
save(f,'PATH1_FIGURES','F2_path1_conditions','経路1寄与条件','PATH1_CONDITION_CLASSIFICATION.csv','NO')
f,a=base('図3 経路2：主分析は連続入力・収支・DC質量応答')
for x,txt in [(.4,'連続設計入力\nq,u,V,f_p,f_n,r,q_n'),(3.4,'部材会計\nT08構造／T09幾何'),(6.4,'走行質量m\nΔM = b − δ'),(9.4,'凍結DC応答\nΔE_DC')]:box(a,x,3.5,2.25,1.1,txt,'model')
for x in [2.65,5.65,8.65]:arrow(a,(x,4.05),(x+.75,4.05))
box(a,.4,1.65,3.3,1.15,'δ < b：削減が残る\nδ = b：質量差ゼロ\nδ > b：逆転','model')
box(a,4.15,1.65,3.4,1.15,'同一軌跡・物理条件\n1000–1250kgの検算範囲\n質量差とDC差の符号が一致','model')
box(a,8,1.65,3.6,1.15,'未確定：完成pack・実材料\n量子由来の改善・実EV\n未知部材をNULL保持','hold')
a.text(.5,.55,'LP/S逆算入力と5.448297kg・約0.413%は条件付き参考例。主分析の確定値として未採用。',fontsize=12)
save(f,'PATH2_FIGURES','F3_path2_conditions','経路2寄与条件','data/PATH2_ANALYTICAL_SENSITIVITY.csv;data/DC_MASS_KERNEL_INDEPENDENT.csv','STRUCTURE_NO;REFERENCE_LABELLED')
f,a=base('図4 共通枠組みと証拠水準の非対称性')
for x,txt in [(2,'技術的能力'),(5.25,'適用・伝達条件'),(8.5,'対象指標')]:a.text(x+1.35,4.9,txt,ha='center',fontsize=14,weight='bold')
a.text(.3,3.6,'経路1',weight='bold');a.text(.3,1.8,'経路2',weight='bold')
for x,txt,k in [(2,'支持・初期・mixer\n量子手法を計算評価','verified'),(5.25,'主対照・可行性\n取得・時間条件','verified'),(8.5,'ΔJ：主改善0\n保存計画に限定','verified')]:box(a,x,3,2.7,1.25,txt,k)
for x,txt,k in [(2,'量子予測→実材料\nこの接続は未検証','hold'),(5.25,'連続入力・部材・質量\nモデル構造を評価','model'),(8.5,'ΔE_DC：固定軌跡\n材料固有値は参考例','model')]:box(a,x,1.2,2.7,1.25,txt,k)
a.text(.3,.35,'二経路を同精度の実証・同一効果量にしない。組織・制度・市場への一般化は考察上の示唆。',fontsize=12)
save(f,'CROSS_PATH_FIGURES','F4_cross_path','共通枠組み','CROSS_PATH_CONDITION_MATRIX.csv','STRUCTURE_NO')
s=pd.read_csv(O/'data/PATH1_STATISTICAL_RESULTS.csv');s=s[s.primary_comparison & s.scale.isin(['R0','R1','R2','R3','R4','R5'])];f,a=plt.subplots(figsize=(9,4.5))
for config in ['GROVER_P2','GROVER_P3','ACTIVE_ADJACENT_P3_GRID']:
 g=s[s.config_id==config].sort_values('scale');a.plot(g.scale,g.input_mean_delta_J_mean,'o-',label=config)
a.axhline(0,c='black',lw=.8);a.set(xlabel='問題規模 R0–R5',ylabel='入力内平均ΔJの規模内平均（秒）',title='図5 保存B系列：主greedy対照に対する解品質差');a.legend(fontsize=8);a.grid(alpha=.2)
save(f,'PATH1_FIGURES','F5_saved_quality','保存Bの品質差','data/PATH1_STATISTICAL_RESULTS.csv','NO')
# Reference values remain, with explicit non-adoption label.
r=pd.read_csv(O/'data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv');su=pd.read_csv(O/'data/PATH2_SENSITIVITY_SUMMARY.csv');f,a=plt.subplots(figsize=(8,4.3))
for pol,g in r[r.V_common==3.5].groupby('policy'):a.plot(g.uS,g.b_known_kg,'o-',label='T09 '+pol)
g=su[(su.model=='T08')&(su.axis=='u_V')&(su.voltage_V==3.5)&(su.rolling_case=='CRR_LOWER_BOUND')];a.plot(g.utilization,g.delta_mass_kg,'s--',label='T08');a.axhline(0,c='black',lw=.7);a.set(xlabel='参考シナリオの利用率',ylabel='既知会計の質量差b（kg）',title='図6 条件付き参考例：Chen逆算qに依存・主材料入力として未採用');a.legend(fontsize=8);a.grid(alpha=.2)
save(f,'PATH2_FIGURES','F6_reference_boundaries','条件付き参考境界','data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv;data/PATH2_SENSITIVITY_SUMMARY.csv','YES_REFERENCE_ONLY')
d=pd.read_csv(O/'data/DC_MASS_KERNEL_INDEPENDENT.csv');f,axs=plt.subplots(1,2,figsize=(10,4))
for case,g in d.groupby('rolling_case'):
 axs[0].hist(g.right_derivative_lo_Wh_kg,bins=25,histtype='step',label=case)
 axs[1].scatter(g.distance_km,g.right_derivative_lo_Wh_kg,s=8,alpha=.4,label=case)
axs[0].set(xlabel='1000kgでの右微分（Wh/kg）',ylabel='軌跡数');axs[1].set(xlabel='保存区間距離（km）',ylabel='右微分（Wh/kg）');axs[0].legend(fontsize=7);f.suptitle('図7 材料入力を使わない凍結DCの質量応答：460対応軌跡×2Crr')
save(f,'PATH2_FIGURES','F7_independent_mass_response','材料非依存DC質量応答','data/DC_MASS_KERNEL_INDEPENDENT.csv','NO')
pd.DataFrame(index).to_csv(O/'FIGURE_INDEX.csv',index=False);pd.DataFrame(nodes).to_csv(O/'data/FIGURE_NODES.csv',index=False)
print('Figures saved:',len(index))
