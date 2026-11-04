from pathlib import Path
import os,json,shutil,hashlib
O=Path(__file__).resolve().parents[1];R=O.parents[1];S=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';os.environ['MPLCONFIGDIR']=str(O/'logs/matplotlib')
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':220})
tables={};figs={}
def table(id,headers,rows,caption,note,source):
 path=O/'tables'/('T'+id.replace('-','_')+'.csv');pd.DataFrame(rows,columns=headers).to_csv(path,index=False)
 tables[id]=dict(id=id,headers=headers,rows=rows,caption=caption,note=note,source=source,csv=str(path.relative_to(O)))
def figsave(fig,id,name,caption,note,source):
 for ext in ['png','pdf','svg']:fig.savefig(O/'figures'/(name+'.'+ext),bbox_inches='tight')
 plt.close(fig);figs[id]=dict(id=id,image='figures/'+name+'.png',caption=caption,note=note,source=source)
# Literature comparison of scopes; not a list of success claims.
table('2-1',['研究群・主文献','能力・媒介条件','成果・方法','本研究との関係'],[
 ['社会技術：Geels 2002/2012、Hekkert 2007、Bergek 2008','技術・利用・制度／機能の関係','転換・技術発展の過程分析','導入・普及Aの背景。本稿は全過程を再現しない'],
 ['水素：McDowall 2014、Staffell et al.2019','用途、インフラ、技術の選択と費用性能','シナリオ・モデル／用途別レビュー','モデル内条件とモデル外の関係を分ける'],
 ['CCU：Mac Dowell et al.2017','処理規模、速度、長期隔離','気候緩和へのフロー・規模比較','技術出力と成果の評価境界を分ける'],
 ['電力：Sepulveda et al.2018','資源構成、需要・排出制約、代替関係','容量・運用モデルによる費用評価','性能の価値を比較系と制約の中で評価'],
 ['商用EV：Feng & Figliozzi、Davis & Figliozzi 2013','利用距離、電池交換、経路・速度・費用','技術経済・境界分析','設計・運用Bの比較例。外部効果量は転用しない'],
 ['カーゴバイク：Gruber et al.2014','用途適合と利用者の実践・意向','事前評価・logit','採用意向と運用成果を区別'],
 ['本研究','解品質・取得・時間／材料移転・質量・走行','保存実験＋条件付きモデル＋経路比較','主としてB。量子・材料・実EVの帰属を分ける']
],'表2-1　先行研究の横断比較','Aは導入・普及、Bは導入されたシステムの設計・運用条件である。各文献の照合範囲・被引用数・限界は文献台帳に示す。','LITERATURE_CROSS_COMPARISON.csv')
table('3-1',['系列','対象と単位','主な評価','範囲'],[
 ['B主系列','460入力×8設定×10測定＝36,800計画','ΔJ、gap、可行性、測定変動','時間窓なし。旧予算完全統制なし'],
 ['追加統制','3診断入力×96条件合計×97学習＝9,312fit','rep0取得率・Wilson、各fit10測定','CPU順列部分空間。3入力合計96条件'],
 ['追加CPU計測','9,312fit＋古典291＝9,603記録','工程別wall/CPU','QPU・import等を除外'],
 ['C主感度','旧460軌跡×2Crr×144条件＝132,480行','質量・観測窓DC・境界','T08簡略会計／T09既知部材'],
 ['A補助','時間窓あり4顧客78問題、36政策','旧採用・期限内需要の診断','主要指標外。固定ODの仮想政策']
],'表3-1　実験系列・分析単位・評価境界','追加統制の96条件は3入力×支持2×初期2×mixer2×層2×方法2の合計である。感度行・測定反復を独立入力と数えない。','Step2/STATISTICAL_METHODS.md;QAOA_CONTROLLED_EXPERIMENT_DESIGN.md;PATH2_STATISTICAL_REPORT.md')
# Table row expression above '3inputs x96conditions' corrected to avoid ambiguous 3x96.
tables['3-1']['rows'][1][1]='3入力合計96条件×97学習＝9,312fit'
pd.DataFrame(tables['3-1']['rows'],columns=tables['3-1']['headers']).to_csv(O/tables['3-1']['csv'],index=False)
sum0=pd.read_csv(S/'PATH1_STATISTICAL_RESULTS.csv');pri=sum0[(sum0.primary_comparison==True)&(sum0.scale!='ALL')];sizes={'R0':3,'R1':4,'R2':5,'R3':25,'R4':100,'R5':125};rows=[]
for sc in sizes:
 vals=[]
 for cfg in ['MEAN_P2','GROVER_P2','GROVER_P3']:
  x=pri[(pri.scale==sc)&(pri.config_id==cfg)].iloc[0];vals.append(f'{x.input_mean_delta_J_mean:,.3f}')
 x=pri[(pri.scale==sc)&(pri.config_id=='GROVER_P2')].iloc[0];rows.append([f'{sc}／{sizes[sc]}',str(int(x.physical_inputs)),*vals,f'{x.input_mean_delta_J_sd:,.3f}'])
table('5-1',['規模／顧客数','入力数','MEAN p2','Grover p2','Grover p3','p2入力間SD'],rows,'表5-1　主greedyに対する平均ΔJと入力間SD','単位：秒。入力内10測定平均→入力等重み。正が改善。SD列はGrover p2。全8設定は付表C-1。','Step2/PATH1_STATISTICAL_RESULTS.csv;PATH1_PAIRED_COMPARISONS.csv')
ref=pd.read_csv(S/'EXACT_REFERENCE_STATUS.csv');counts=ref.reference_evidence_class.value_counts()
table('5-2',['証拠区分','入力数','採用と制約'],[
 ['小規模再列挙','234','3〜5顧客。再検査した参照'],['保存整数Held–Karp DP','78','25顧客。保存実行・入力・witnessを照合'],['独立有理数双対','61','既存54＋追加7。下界＝可行上界'],['保存MIP等値のみ','41','採用414に含むが外部VIPR未実施の条件付き'],['未証明','46','gap・最適一致をNULL保持']
],'表5-2　参照値の証拠強度と未証明入力','合計460。採用414のうち41は条件付き。41を除く373層別感度と旧407集合も保持した。','Step2/EXACT_REFERENCE_STATUS.csv;EXACT_REFERENCE_RECHECK_RESULTS.csv')
cells=pd.read_csv(S/'QAOA_CONTROLLED_CELL_SUMMARY.csv');q=cells[(cells.problem_id=='R1_020')&(cells.method=='QAOA')];crows=[]
for init,mix,layer in [('BASIS_INITIAL','GRAPH_SWAP',1),('BASIS_INITIAL','GRAPH_SWAP',2),('BASIS_INITIAL','PROJECTOR',1),('UNIFORM_SUPPORT','PROJECTOR',1)]:
 x=q[(q.support=='FULL_PERMUTATION')&(q.initial_state==init)&(q.mixer==mix)&(q.layers==layer)].iloc[0];crows.append([('基底' if init=='BASIS_INITIAL' else '一様'),('graph' if mix=='GRAPH_SWAP' else 'projector'),str(layer),f'{int(x.primary_optimal_rep0_count)}/97',f'{100*x.primary_optimal_rep0_rate:.1f}',f'{100*x.primary_optimal_Wilson95_lower:.1f}–{100*x.primary_optimal_Wilson95_upper:.1f}'])
table('5-3',['初期','mixer','p','最適取得','取得率 %','Wilson 95% %'],crows,'表5-3　R1_020の全支持QAOAの代表条件','primary rep0、各97学習start、8192shots。選択入力とexact期待値学習に条件付き。greedyは既に最適。全QAOA条件は図5-2、全96条件は電子資料。','Step2/QAOA_CONTROLLED_CELL_SUMMARY.csv;experiments/QAOA_MAIN_MEASUREMENTS.csv')
rt=pd.read_csv(S/'PATH1_RUNTIME_RESULTS.csv');fixed=rt[(rt.problem_id=='R1_001')&(rt.config_id=='FULL_PERMUTATION/UNIFORM_SUPPORT/PROJECTOR/p2')&rt.method.isin(['QAOA','DEPHASED'])]
table('5-4',['方式','fit数','wall中央値 ms','CPU中央値 ms','出力数/fit'],[[m,'97',f'{g.total_wall_s.median()*1000:.3f}',f'{g.total_CPU_s.median()*1000:.3f}','10計画'] for m,g in fixed.groupby('method',sort=False)],'表5-4　固定小規模条件のCPUパイプライン時間','R1_001、4顧客、全支持・一様初期・projector p2、1thread。同core、学習＋10測定・検証等。共通初期生成・import・転送・QPU queueを除く。','Step2/PATH1_RUNTIME_RESULTS.csv')
ce=pd.read_csv(O/'tables/C_DC_VERIFIED.csv');table('5-5',['Crr条件','軌跡数','総和比 %','個別率平均 %','個別率SD pp'],[[r.rolling_case.replace('CRR_','').replace('_BOUND',''),str(r.trajectories),f'{r.total_weighted_percent:.9f}',f'{r.mean_percent:.9f}',f'{r.sd_percentage_points:.8f}'] for r in ce.itertuples()],'表5-5　T08参照端点のControlled-DC削減率','qLP=171.875、qS=195.959596Ah/kg、u=1、V=3.5V、gross20kWh、回生なし・補機範囲外・平坦・空荷・共通保存速度。SDは軌跡間sample SD。','Step2/PATH2_SENSITIVITY_RESULTS.csv;PATH2_SENSITIVITY_SUMMARY.csv')
boundaries=[('T08簡略',5.448297415076934,'共通その他部材34kgの簡略総会計'),('T09固定担持',9.722608121107783,'既知部材差。未知BOMは別'),('T09固定面積',5.977891152148871,'既知部材差。LP面積固定')]
table('5-6',['会計・構造','相殺b kg','完成pack／留意点'],[[label,f'{b:.9f}',note] for label,b,note in boundaries],'表5-6　追加・未知部材差のゼロ境界','δ=未知・追加S−LP差。δ=bが相殺。T09の完成packはNULL。異なる完成品精度の直接比較ではない。','Step2/PATH2_BOUNDARY_ANALYSIS.csv;PATH2_T09_COMMON_INPUT_SENSITIVITY.csv')
table('6-1',['比較軸','経路1：配送計画','経路2：材料・車両'],[
 ['技術入力','支持・初期・mixer・学習・測定','物性予測の可能性／条件付きq・u・V'],['媒介関係','解取得→検証→採用→出発・運用','実用移転→部材→車両質量→DC'],['評価変数','ΔJ、gap、確率、秒','Ah/kg、V、kg、Wh、削減率'],['不成立・消失','支持内改善余地なし／対照最適／未採用','利用率・電圧／追加部材相殺／運転境界'],['確認範囲','保存CPU計画と3診断入力の統制','簡略・既知部材会計と固定速度の条件付き感度'],['未検証','公平な総予算、H_plan、QPU、B→実走行','量子帰属、実用全電池、未知BOM、実車'],['社会技術的範囲','主に設計・運用B。採用行動は未モデル化','主に設計・運用B。市場・制度は未モデル化']
],'表6-1　二経路の媒介条件と証拠範囲の比較','本表は第5章の証拠を用いた今回のStep 3の統合である。異なる成果指標を共通の改善率として比較しない。','Step2/PATH1_CONDITION_EVIDENCE_MATRIX.csv;PATH2_CONDITION_EVIDENCE_MATRIX.csv;CHAPTER6.md')
table('C-1',['規模','設定','入力数','平均ΔJ s','入力間SD s','gap %','参照入力'],[[r.scale,r.config_id,str(int(r.physical_inputs)),f'{r.input_mean_delta_J_mean:.3f}',f'{r.input_mean_delta_J_sd:.3f}',f'{r.mean_quantum_gap_percent:.6f}',str(int(r.exact_inputs))] for r in pri.itertuples()],'表C-1　全8設定・6規模の主greedy比較','入力内10測定平均後の記述。gapは414採用参照（41条件付き）の有効入力のみ。旧予算完全統制なし。','Step2/PATH1_STATISTICAL_RESULTS.csv')
# Concept diagram with dashed untested links, deliberately distinct from causal identification.
fig,ax=plt.subplots(figsize=(10,4.7));ax.set(xlim=(0,10),ylim=(0,4.7));ax.axis('off')
def box(x,y,w,h,txt,color='#e8eef6'):
 p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',facecolor=color,edgecolor='#34495e');ax.add_patch(p);ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=9)
def arrow(x1,x2,y,dashed=False):ax.add_patch(FancyArrowPatch((x1,y),(x2,y),arrowstyle='-|>',mutation_scale=12,color='#34495e',linestyle='--' if dashed else '-'))
for x,y,w,txt in [(0.1,3.0,2.1,'Algorithm capability\nCPU model / support'),(2.65,3.0,2.1,'Plan acquisition\nquality / probability / time'),(5.2,3.0,1.8,'Plan adoption\nand departure'),(7.5,3.0,2.1,'Operational\noutcomes'),(.1,1.0,2.1,'Quantum material\nanalysis (potential)'),(2.65,1.0,2.1,'Conditional material\ninputs / cell-pack design'),(5.2,1.0,1.8,'Vehicle running\nmass'),(7.5,1.0,2.1,'Observed-window\nControlled-DC')]:box(x,y,w,.9,txt,'#e8eef6' if y==3 else '#eaf3e9')
for x1,x2 in [(2.2,2.57),(4.75,5.12),(7.0,7.42)]:arrow(x1,x2,3.45,x1>3)
for x1,x2 in [(2.2,2.57),(4.75,5.12),(7.0,7.42)]:arrow(x1,x2,1.45,x1<3)
ax.text(.1,4.35,'Technical capability → application → system outcome',fontsize=11,weight='bold');ax.text(.15,.38,'Solid: evaluated computational/model relations. Dashed: untested application or attribution.\nA conceptual scope map; no real-world causal identification.',fontsize=8)
figsave(fig,'3-1','F3_1_scope','図3-1　二つの作用経路と評価範囲','実線も実世界の因果実証を意味しない。破線は量子材料への帰属、計画採用・実運用等の未検証接続。定量の母集団は経路ごとに異なる。','今回のStep3概念整理；Step2/CONTRIBUTION_CONDITION_TABLE.csv')
fig,axs=plt.subplots(1,2,figsize=(8,4))
for ax,scs in zip(axs,[['R0','R1','R2'],['R3','R4','R5']]):
 for cfg in ['MEAN_P2','GROVER_P2','GROVER_P3','ACTIVE_ADJACENT_P3_GRID']:
  g=pri[(pri.config_id==cfg)&pri.scale.isin(scs)];ax.plot([sizes[v] for v in g.scale],g.input_mean_delta_J_mean,'o-',label=cfg.replace('ACTIVE_ADJACENT_P3_GRID','ACTIVE grid'))
 ax.axhline(0,color='black',lw=.6);ax.set(xlabel='Customers',ylabel='Mean Delta J vs greedy (s)');ax.grid(alpha=.2)
axs[0].legend(fontsize=7,loc='lower left');fig.tight_layout()
figsave(fig,'5-1','F5_1_quality','図5-1　規模別の主greedyに対する解品質差','B時間窓なし。3/4/5/25/100/125顧客、78/78/78/78/78/70入力、各10測定。正のΔJが改善。表示4設定、全8設定は表C-1。規模だけの因果効果ではない。','Step2/PATH1_STATISTICAL_RESULTS.csv')
fig,axs=plt.subplots(1,2,figsize=(8,4.7),sharey=True)
for ax,(supp,title) in zip(axs,[('FULL_PERMUTATION','Full permutation support'),('MIRROR_ORBIT','Matching support')]):
 labels=[];ys=[];los=[];his=[];ns=[]
 for init in ['BASIS_INITIAL','UNIFORM_SUPPORT']:
  for mix in ['GRAPH_SWAP','PROJECTOR']:
   for layer in [1,2]:
    x=q[(q.support==supp)&(q.initial_state==init)&(q.mixer==mix)&(q.layers==layer)].iloc[0];labels.append(('B' if init=='BASIS_INITIAL' else 'U')+'/'+('G' if mix=='GRAPH_SWAP' else 'P')+f'/p{layer}');ys.append(x.primary_optimal_rep0_rate);los.append(x.primary_optimal_Wilson95_lower);his.append(x.primary_optimal_Wilson95_upper);ns.append(int(x.primary_optimal_rep0_count))
 y=np.array(ys);ax.bar(range(8),y,color=['#3b6ca8','#75a4d6']*4);ax.errorbar(range(8),y,yerr=np.array([y-np.array(los),np.array(his)-y]),fmt='none',ecolor='black',capsize=2);ax.set_xticks(range(8),labels,rotation=60,ha='right');ax.set(title=title,ylim=(0,1.15),ylabel='Optimal acquisition: rep0 / fit');ax.grid(axis='y',alpha=.2)
 for j,(rate,k) in enumerate(zip(y,ns)):ax.text(j,rate+.055,f'{k}',ha='center',fontsize=7)
fig.text(.5,.01,'R1_020; 97 learning starts/cell. B/U: basis/uniform; G/P: graph/projector; error bars: Wilson 95%.',ha='center',fontsize=8);fig.tight_layout(rect=(0,.04,1,1))
figsave(fig,'5-2','F5_2_acquisition','図5-2　支持・初期・mixer・層による最適解取得','R1_020の全QAOA条件。数値は97fit中のprimary rep0取得件数、各8192shots。区間はWilson 95%。主greedyは既に最適。別学習脱位相を含む全96条件は電子資料。','Step2/QAOA_CONTROLLED_CELL_SUMMARY.csv;experiments/QAOA_MAIN_MEASUREMENTS.csv')
fig,axs=plt.subplots(1,2,figsize=(8,4));methods=['QAOA','DEPHASED'];axs[0].boxplot([fixed[fixed.method==m].total_wall_s*1000 for m in methods],tick_labels=methods,showfliers=True,flierprops={'markersize':2});axs[0].set(ylabel='Pipeline wall (ms)',title='R1_001; 97 fits/method')
cols=['preprocessing_wall_s','optimization_wall_s','sampling_wall_s','verification_wall_s','postprocessing_wall_s'];vals=fixed.groupby('method')[cols].mean().loc[methods]*1000;bottom=np.zeros(2)
for col in cols:axs[1].bar(methods,vals[col],bottom=bottom,label=col.replace('_wall_s',''));bottom+=vals[col].to_numpy()
axs[1].set(ylabel='Mean stage wall (ms)',title='Simulation is inside optimization');axs[1].legend(fontsize=6.5);fig.tight_layout()
figsave(fig,'5-3','F5_3_runtime','図5-3　固定条件のCPU時間分布と工程内訳','R1_001、全支持・一様初期・projector p2、各97fit。左はwall分布、右は非重複工程の平均。simulationはoptimizationの内数。QPUや公平なgreedy speedupを示さない。','Step2/PATH1_RUNTIME_RESULTS.csv')
fig,ax=plt.subplots(figsize=(7,3.8));xx=np.linspace(0,12,100)
for label,bv,note in boundaries:ax.plot(xx,bv-xx,label=label.replace('T08簡略','T08 simplified').replace('T09固定担持','T09 fixed loading').replace('T09固定面積','T09 fixed area'))
ax.axhline(0,color='black',lw=.6);ax.set(xlabel='Additional / unknown S minus LP mass (kg)',ylabel='Net mass saving (kg)',title='Separate mass-accounting boundaries');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout()
figsave(fig,'5-4','F5_4_boundary','図5-4　追加・未知部材差による質量の相殺・逆転','指定会計の恒等式ΔM=b−δを表示。T08とT09代表構造は異なる会計であり、完成pack性能の直接比較ではない。未知δの実値は未測定。','Step2/PATH2_BOUNDARY_ANALYSIS.csv;PATH2_T09_COMMON_INPUT_SENSITIVITY.csv')
# Reuse the inspected Step2 operation plot without changing its scientific data.
for ext in ['png','pdf']:shutil.copyfile(S/'PATH2_FIGURES'/('F5_operation_dependence.'+ext),O/'figures'/('F5_5_operation.'+ext))
figs['5-5']=dict(id='5-5',image='figures/F5_5_operation.png',caption='図5-5　走行条件とT08端点のDC削減の分布',note='旧460軌跡×2Crr、同一速度・空荷・Controlled-DC。左：距離とWh、右：再発進数と個別率%。条件の交絡を除いておらず、相関を運転介入の因果効果としない。',source='Step2/PATH2_FIGURES/F5_operation_dependence.png;PATH2_OPERATION_CONDITION_ANALYSIS.csv')
(O/'TABLES.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2));(O/'FIGURES.json').write_text(json.dumps(figs,ensure_ascii=False,indent=2));pd.DataFrame([{k:v[k] for k in ['id','image','caption','note','source']} for v in figs.values()]).to_csv(O/'FIGURE_SELECTION.csv',index=False)
print('tables',len(tables),'figures',len(figs))
