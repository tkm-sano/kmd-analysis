"""Rebuild thesis graphics exclusively from saved analysis CSVs."""
from evidence import *
import os
os.environ['MPLCONFIGDIR']=str(O/'scripts/.mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
import numpy as np
font_manager.fontManager.addfont('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
plt.rcParams.update({'font.family':['DejaVu Sans','Droid Sans Fallback'],'font.size':10,'axes.unicode_minus':False,'svg.fonttype':'path','svg.hashsalt':'THESIS_20261102','pdf.fonttype':42,'figure.constrained_layout.use':True})
t=time.monotonic(); mapping=[]
def frame(n):return pd.read_csv(use(F/n))
def save(fig,id,title,source,subset,denom,unit,direction,aggregate,assumption,read,cannot,section,data=None):
 stem=id.replace('-','_');files=[]
 for ext in ['png','svg','pdf']:
  p=O/'figures'/f'{stem}.{ext}';p.parent.mkdir(exist_ok=True);fig.savefig(p,dpi=220,facecolor='white',metadata=({'Date':None} if ext=='svg' else {'CreationDate':None,'ModDate':None} if ext=='pdf' else None));files.append(str(p.relative_to(O)))
 plt.close(fig)
 if data is not None:data.to_csv(O/'tables'/f'{stem}_PLOT_DATA.csv',index=False)
 mapping.append(dict(figure_id=id,title=title,files=';'.join(files),source_paths=';'.join(str(use(F/x)) for x in source),source_sha256=';'.join(sha(use(F/x)) for x in source),source_selection=subset,denominator=denom,units=unit,comparison_direction=direction,aggregation=aggregate,assumptions=assumption,readable_result=read,unreadable_result=cannot,proposed_section=section,caption=f'{title}。対象：{denom}。{aggregate}。{assumption}。{cannot}。'))
def box(ax,x,y,text,color='#e8f1f8',w=.25,h=.17):
 ax.text(x,y,text,ha='center',va='center',transform=ax.transAxes,bbox=dict(boxstyle='round,pad=.65',fc=color,ec='#546778'),fontsize=11)
def arrow(ax,a,b,style='-'):
 ax.annotate('',xy=b,xytext=a,xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color='#546778',lw=1.4,linestyle=style))
p=frame('A_POLICY_DECISIONS_2808.csv');a=frame('A_SUMMARY_BY_CONDITION.csv');me=frame('A_MECHANISM_SUMMARY.csv');b=frame('B_SUMMARY_BY_SCALE_AND_METHOD.csv');rs=frame('B_RESOURCE_SCOPE_SUMMARY.csv');c=frame('C_T08_PAIRED_DIFFERENCES.csv');br=frame('C_BRIDGE_MASS_DC_FULL.csv')
fig,ax=plt.subplots(figsize=(11,5));ax.axis('off')
for x,y,s in [(.16,.78,'78問題の計画取得\n成功64／未取得14'),(.55,.78,'36運用条件\n2,808政策判断'),(.16,.38,'QAOA採用1,344判断\n古典切替1,464判断'),(.55,.38,'訪問順変更105判断\n正の出発遅延936判断'),(.86,.58,'固定ODモデル\n11,232配送先\n定時率100%')]:box(ax,x,y,s)
arrow(ax,(.31,.78),(.39,.78));arrow(ax,(.53,.69),(.23,.49));arrow(ax,(.32,.38),(.40,.38));arrow(ax,(.69,.40),(.78,.53));ax.text(.51,.07,'単位を区別：問題 → 運用判断 → 配送先のモデル時刻\n地域交通・速度軌跡・走行DCへの接続は未検証',ha='center',transform=ax.transAxes,color='#9b3030')
save(fig,'F3-1','計画取得から固定OD配送成果までの対応',['A_POLICY_DECISIONS_2808.csv','A_DELIVERY_COMPLETION_BY_STOP.csv'],'POLICY78', '78問題×36条件、配送先4件／判断','件、%','政策採用対古典単独','各段階の件数を別集計','時間不変OD・102秒サービス','取得失敗と採用期限による切替','実配送成功を示さない','3.8')
fig,ax=plt.subplots(figsize=(11,5.4));ax.axis('off')
for x,y,s,col in [(.18,.84,'量子材料解析\n対象性能改善は未実証','#fce8e6'),(.18,.40,'文献参照の比容量\n利用率・平均電圧','#e8f1f8'),(.55,.70,'T08：簡略質量会計\n固定部材を仮定','#e8f1f8'),(.55,.32,'T09：電極幾何・部材会計\n既知質量＋未知質量','#e8f1f8'),(.85,.70,'旧保存速度軌跡\nControlled-DC感度','#e8f1f8'),(.85,.23,'完成パック183行HOLD\n全面対向1行FAIL','#fff0d7')]:box(ax,x,y,s,col)
arrow(ax,(.18,.75),(.18,.51),'--');arrow(ax,(.33,.45),(.43,.65));arrow(ax,(.33,.38),(.41,.33));arrow(ax,(.69,.70),(.74,.70));arrow(ax,(.70,.32),(.75,.25));ax.text(.52,.04,'T08とT09を完成パック同士の比較に統合しない。T09からDCへの接続は未知質量差等の条件を要する。',ha='center',transform=ax.transAxes,fontsize=10)
save(fig,'F3-2','材料・設計・質量・電力量の証拠到達範囲',['C_T09_COMPONENTS_183.csv','C_T08_ENERGY_FULL.csv'],'T08 / T09 separate','T08旧460主軌跡；T09 183設計行','kg、Wh','LP−S','モデルごとに分離','材料参照値は量子計算成果ではない','条件付き接続と未知部材の位置','完成パック・実EVの改善を示さない','3.9')
# B delta: all eight retained as table; exact-equal six share one visible line.
bb=b[b.scale!='ALL'];scales=[f'R{i}' for i in range(6)];configs=sorted(bb.config_id.unique())
fig,axes=plt.subplots(1,2,figsize=(11,4.4))
for ax,sel in zip(axes,[scales,scales[:3]]):
 for cfg,label,marker in [('MEAN_P2','初期解と同値の6設定','o'),('GROVER_P2','Grover P2','s'),('GROVER_P3','Grover P3','^')]:
  z=bb[(bb.config_id==cfg)&bb.scale.isin(sel)].set_index('scale').loc[sel];ax.plot(range(len(sel)),z.mean_delta_objective_s,label=label,marker=marker)
 ax.axhline(0,color='gray',lw=.8);ax.set_xticks(range(len(sel)),sel);ax.set_ylabel('目的値差：保存計画 − 古典初期解 [秒]');ax.set_xlabel('規模（R0〜R5：78/78/78/78/78/70入力）');ax.grid(alpha=.2)
axes[0].set_title('全規模');axes[1].set_title('小規模の拡大');axes[0].legend(fontsize=9)
save(fig,'F5-1','規模・設定別の古典初期解に対する目的値差',['B_SUMMARY_BY_SCALE_AND_METHOD.csv'],'scale R0..R5','460入力、8設定、10測定rep／入力設定','秒','正は目的値悪化','測定repを入力内平均後、規模内入力等重み','CPU計算・支持・予算は設定間で異なる','小規模の改善例と大規模側の平均悪化','量子計算一般の優劣・配送時刻差を示さない','5.1',bb)
fig,(ax,ac)=plt.subplots(2,1,figsize=(10,6),gridspec_kw={'height_ratios':[3.2,1]})
pivot=bb.pivot(index='config_id',columns='scale',values='mean_global_gap_percent').loc[configs,scales];im=ax.imshow(pivot,aspect='auto',cmap='YlOrRd');ax.set_xticks(range(6),scales);ax.set_yticks(range(8),configs,fontsize=8)
for i in range(8):
 for j in range(6):ax.text(j,i,f'{pivot.iloc[i,j]:.2f}',ha='center',va='center',color='white' if pivot.iloc[i,j]>150 else 'black',fontsize=9)
fig.colorbar(im,ax=ax,label='平均最適性ギャップ [%]');cov=frame('B_EXACT_REFERENCE_COVERAGE.csv').groupby('scale')['exact_reference_available'].agg(['sum','count']).loc[scales];ac.bar(scales,cov['sum'],label='参照あり');ac.bar(scales,cov['count']-cov['sum'],bottom=cov['sum'],label='参照未確定',color='#d1d1d1');ac.set_ylabel('物理入力数');ac.legend(ncol=2,fontsize=9);ac.set_ylim(0,135)
for i,z in enumerate(cov.itertuples()):ac.text(i,z.count+3,f'{int(z.sum)}/{int(z.count)}',ha='center',fontsize=9)
save(fig,'F5-2','厳密参照値のある入力の最適性ギャップと参照範囲',['B_SUMMARY_BY_SCALE_AND_METHOD.csv','B_EXACT_REFERENCE_COVERAGE.csv'],'exact available only','407/460入力；R4 57/78、R5 38/70','%、入力数','100×(目的値−厳密参照値)/厳密参照値','repを先に平均、参照あり入力を規模内平均','53入力のgapを補完しない','参照範囲内の規模別品質差','未参照53入力を含む最適性を示さない','5.1',pivot.reset_index())
fig,axes=plt.subplots(1,3,figsize=(12,4.2));rplot=[]
for scope,ax,sel,title in [('FIT',axes[0],[x for x in configs if not x.startswith('ACTIVE')],'学習工程 FIT'),('FINAL_VALIDATION',axes[1],['GROVER_P2','GROVER_P3'],'最終検証工程'),('RESULT_ROOT_OR_BACKEND',axes[2],['ACTIVE_ADJACENT_P3_GRID'],'保存RESULT工程')]:
 rr=rs[(rs.resource_scope==scope)&(rs.resource_field=='wall_seconds')]
 # source may use another exact wall field; never silently substitute scopes
 if rr.empty:
  rr=rs[(rs.resource_scope==scope)&rs.resource_field.str.contains('wall')]
 for cfg in sel:
  z=rr[(rr.config_id==cfg)&rr.scale.isin(scales)].drop_duplicates('scale').set_index('scale').reindex(scales)
  if z['mean_value'].notna().any():ax.plot(scales,z.mean_value,marker='o',label=cfg);rplot.extend(z.reset_index().to_dict('records'))
 ax.set_title(title);ax.set_ylabel('保存工程の平均wall時間 [秒]');ax.set_xlabel('規模');ax.grid(alpha=.2);ax.legend(fontsize=6)
fig.suptitle('工程の異なる時間を合算・直接順位化しない',fontsize=12)
save(fig,'F5-3','計算時間の工程別記述',['B_RESOURCE_SCOPE_SUMMARY.csv'],'wall fields; FIT / FINAL_VALIDATION / RESULT separate','3,680保存fit；10測定repを重複加算しない','秒','設定別、工程別','各規模の固有fit平均','CPUシミュレータの工程記録、QPU時間ではない','最終検証を省くと時間評価が変わる','同一予算・同一ハードウェアの速度比較ではない','5.1',pd.DataFrame(rplot))
fig,ax=plt.subplots(figsize=(11,4.3));m=me.pivot(index='condition_id',columns='arm',values='mean_completion_s').sort_index();md=m.copy()
for arm,label in [('QC','経路のみ QC−CC'),('CQ','出発のみ CQ−CC'),('QQ','両者 QQ−CC')]:md[arm+'-CC']=m[arm]-m.CC;ax.plot(range(1,37),md[arm+'-CC'],label=label,marker='.',lw=1.3)
ax.set_xticks([1,6,13,18,25,30,36]);ax.set_xlabel('D10運用条件番号（全36条件、各64取得成功入力）');ax.set_ylabel('入力別平均完了時刻の対応差 [秒]');ax.axhline(0,color='gray',lw=.7);ax.legend(fontsize=9);ax.grid(alpha=.2)
for x in [12.5,24.5]:ax.axvline(x,color='gray',ls=':')
save(fig,'F5-4','経路変更と出発変更の機構比較',['A_MECHANISM_SUMMARY.csv','A_MECHANISM_COMPARISON.csv'],'MECHANISM64, all36','64問題×36条件×4arm＝9,216 arm','秒','QC/CQ/QQ − CC；正は遅い','各問題の4配送先平均を64入力で等重み平均','反実仮想比較であり政策採用結果とは別','経路・出発・組合せの差','利用可能時刻より早い出発を実運用可能とはしない','5.2',md.reset_index())
w=pd.read_csv(O/'tables/A_WAIT_ABSORPTION_SUMMARY.csv');sl=pd.read_csv(O/'tables/A_MIN_DEADLINE_SLACK_78.csv');fig,(ax,ac)=plt.subplots(1,2,figsize=(11,4.4));ax.bar(w.stop_order,w.mean_retained_delay_s,label='完了時刻に残る遅延');ax.bar(w.stop_order,w.mean_cumulative_absorbed_s,bottom=w.mean_retained_delay_s,label='待機減少が吸収した遅延',color='#cbdde9');ax.set_xticks([1,2,3,4]);ax.set_xlabel('配送先の訪問順');ax.set_ylabel('出発遅延510秒の内訳（平均）[秒]');ax.legend(fontsize=9);ax.set_title('出発のみ変更：正の遅延768条件')
ac.hist(sl.min_slack_over36_s/60,bins=12,color='#668eaf',edgecolor='white');ac.axvline(0,color='#b33535',ls='--');ac.set_xlabel('各問題の全36条件における最小期限余裕 [分]');ac.set_ylabel('物理入力数');ac.set_title('政策評価78問題：最小52.22分');ac.set_ylim(0,34)
save(fig,'F5-5','早着待機による遅延吸収と定時指標の飽和',['A_DELIVERY_COMPLETION_BY_STOP.csv','A_POLICY_DECISIONS_2808.csv'],'CC/CQ positive departure and POLICY78','左64×36中768条件、右78問題×36条件の問題別最小','秒、分、問題数','出発のみCQ−CC／deadline−complete','左は配送順ごとの平均；右は問題別最小の分布','固定OD、同一経路、102秒サービス','最終配送先で768/768条件の遅延吸収、政策最小余裕3133.46秒','現実交通で同じ吸収が起こるとはいえない','5.2',w)
fig,axes=plt.subplots(1,2,figsize=(10,4));bp=[]
for ax,design,label in zip(axes,['fixed_loading','fixed_area_LP'],['固定担持 B015','固定面積 B051']):
 z=br[br.design_policy==design][['unknown_mass_difference_probe_kg','net_mass_saving_probe_kg','known_mass_boundary_kg']].drop_duplicates().sort_values('unknown_mass_difference_probe_kg');bp.append(z.assign(design=design));bound=z.known_mass_boundary_kg.iloc[0];ax.plot(z.unknown_mass_difference_probe_kg,z.net_mass_saving_probe_kg,'o-',label='正味軽量化 b−δ');ax.axhline(0,color='gray');ax.axvline(bound,color='#b33535',ls='--',label=f'相殺境界 b={bound:.3f} kg');ax.set_title(label);ax.set_xlabel('未知部材質量差 δ＝S−LP [kg]');ax.set_ylabel('正味軽量化＝LP−S [kg]');ax.legend(fontsize=8);ax.grid(alpha=.2)
save(fig,'F5-6','未知部材による軽量化の相殺・逆転条件',['C_BRIDGE_MASS_DC_FULL.csv'],'B015/B051 saved seven probes','2代表設計×既存7未知質量差条件','kg','LP−S=b−δ','同じ質量条件の重複を除去し、既存点を直線で結ぶ','未知質量差は未実測；bは代表設計の既知部材差','δ<bで軽量、δ=bで相殺、δ>bで逆転','T09完成パックの質量は確定しない','5.3',pd.concat(bp))
z=c[(c.dataset=='CLASSICAL')&(c.scenario_id=='COND_S200_REF')];fig,axes=plt.subplots(1,2,figsize=(10,4.2))
for ax,roll,label in zip(axes,['CRR_LOWER_BOUND','CRR_UPPER_BOUND'],['下側Crr','上側Crr']):
 rr=z[z.rolling_case==roll];weighted=100*rr.saving_DC_Wh.sum()/rr.baseline_DC_Wh.sum();ax.hist(rr.individual_saving_percent,bins=20,color='#6e91aa',edgecolor='white');ax.axvline(weighted,color='#ad3434',ls='--',label=f'総量加重 {weighted:.6f}%');ax.set_title(f'{label}：旧460保存軌跡');ax.set_xlabel('個別軌跡のDC削減率 [%]');ax.set_ylabel('軌跡参照数');ax.legend(fontsize=9)
save(fig,'F5-7','T08簡略質量モデルの固定軌跡DC感度',['C_T08_PAIRED_DIFFERENCES.csv'],'CLASSICAL COND_S200_REF','旧460主軌跡、2 Crr条件','%','100×(LP−S)/LP DC','個別分布と総量加重率を区別','質量差5.448297415kg、速度固定、回生・補機なし','条件付き小幅なDC感度','実EV改善・現行BのDCではない','5.3',z)
fig,axes=plt.subplots(2,2,figsize=(10,7));bridge=[]
for i,design in enumerate(['fixed_loading','fixed_area_LP']):
 for j,mass in enumerate([1200,1400]):
  ax=axes[i,j]
  for roll,label in [('CRR_LOWER_BOUND','下側Crr'),('CRR_UPPER_BOUND','上側Crr')]:
   rr=br[(br.design_policy==design)&(br.reference_running_mass_kg==mass)&(br.rolling_case==roll)];zz=rr.groupby('unknown_mass_difference_probe_kg')[['recomputed_baseline_DC_Wh','recomputed_saving_Wh']].sum().reset_index();zz['weighted_percent']=100*zz.recomputed_saving_Wh/zz.recomputed_baseline_DC_Wh;ax.plot(zz.unknown_mass_difference_probe_kg,zz.weighted_percent,marker='o',label=label,ls='-' if 'LOWER' in roll else '--');bridge.extend(zz.assign(design=design,mass_kg=mass,rolling_case=roll).to_dict('records'))
  ax.axhline(0,color='gray',lw=.8);ax.set_title(('固定担持' if i==0 else '固定面積')+f'・参照走行質量{mass}kg');ax.set_xlabel('未知部材質量差 δ [kg]');ax.set_ylabel('総量加重DC削減率 [%]');ax.legend(fontsize=8);ax.grid(alpha=.2)
save(fig,'FA-1','T09代表設計と未知部材差の条件付きDC感度',['C_BRIDGE_MASS_DC_FULL.csv'],'B015/B051, 7 original probes, 2 masses,2 Crr','各点旧460保存速度、全25,760条件行','kg、%','100×(基準DC−条件DC)/基準DC','各条件の総量加重率','1200/1400kgは既存感度の参照質量であり完成パックやB車両ではない','未知部材差・参照質量・Crrに依存するDC符号','T08とT09の完成パック性能比較ではない','付録C',pd.DataFrame(bridge))
table('FIGURE_SOURCE_MAPPING.csv',mapping)
finish('FIGURES',t,{'figures':len(mapping),'formats':['PNG','SVG','PDF'],'font':'Droid Sans Fallback','matplotlib':matplotlib.__version__,'no_scientific_runs':True})
