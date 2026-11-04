"""Generate the auditable editorial package; only this review directory is written."""
from evidence import *
import pandas as pd
T=O/'tables';T.mkdir(exist_ok=True)
def df(n):return pd.read_csv(use(F/n))
def fmt(x):
 if pd.isna(x):return 'HOLD'
 if isinstance(x,float):return f'{x:.6f}'
 return str(x)
def tab(n,title,data,cols,caption):
 z=data[cols];z.to_csv(T/(n+'.csv'),index=False)
 s='# '+title+'\n\n'+caption+'\n\n|'+ '|'.join(cols)+'|\n|'+'|'.join('---' for x in cols)+'|\n'
 s+='\n'.join('|'+ '|'.join(fmt(x) for x in row)+'|' for row in z.itertuples(index=False,name=None))
 (T/(n+'.md')).write_text(s+'\n')
a=df('A_SUMMARY_BY_CONDITION.csv');b=df('B_SUMMARY_BY_SCALE_AND_METHOD.csv');c=df('C_CONDITIONAL_MASS_DC_SUMMARY.csv');res=df('B_RESOURCE_SCOPE_SUMMARY.csv');ci=df('CLUSTER_SENSITIVITY_INTERVALS.csv')
tab('TA-1_ALL_36_POLICIES','付表A-1 全36政策条件',a,['condition_id','L_s','T_Q_s','B_s','physical_inputs','quantum_adopted','classical_switched','positive_departure_inputs','PE_on_time_percent','delta_F_PE_pp','delta_mean_completion_s','delta_return_s'],'原表A_SUMMARY_BY_CONDITION.csv。各条件78問題、556 PE、312配送先。正の時間差は古典単独対照より遅い。率は%、率差はpp、時間は秒。固定ODモデルの結果である。')
tab('T5-1_B_OBJECTIVE','表5-1 規模・設定別の目的値差',b[b.scale!='ALL'],['scale','config_id','physical_inputs','plan_references','mean_delta_objective_s','improve_percent','equal_percent','worsen_percent'],'B_SUMMARY_BY_SCALE_AND_METHOD.csv。差＝保存best−古典初期解[秒]。各入力内10測定rep平均後、規模内入力等重み。改善／同値／悪化率はrep内率を入力平均した%。設定間の同一計算予算は保証しない。')
tab('T5-2_B_EXACT','表5-2 厳密参照範囲と最適性',b[b.scale!='ALL'],['scale','config_id','exact_reference_inputs','exact_missing_inputs','mean_global_gap_percent','optimal_match_percent'],'厳密参照あり407入力のみ。各規模78/78/78/78/57/38入力。53入力を0%gapとしない。最適一致は有理数での目的値一致。')
tab('T5-3_RESOURCE_SCOPES','表5-3 工程別計算資源',res[res.resource_field.isin(['wall_seconds','cpu_seconds','CPU_seconds','peak_RSS_bytes'])],['config_id','scale','resource_scope','resource_field','units','unique_fits','mean_value','max_value'],'保存済み元JSONフィールド別。FIT、FINAL_VALIDATION、RESULT、SELECTED_STATEを分離し、合算していない。bytesはメモリ量、秒は各工程である。保存のないhardware qubits/compiled depth/gatesはHOLDである。')
tab('T5-4_T08_DC','表5-4 T08固定軌跡の条件付きDC感度',c[(c.series_id=='C_T08')&(c.dataset=='CLASSICAL')&(c.scenario_id=='COND_S200_REF')&(c.scale=='ALL')],['rolling_case','trajectories','mass_saving_kg','baseline_sum_Wh','saving_sum_Wh','weighted_saving_percent','individual_mean_percent'],'旧460軌跡を同一速度・共通非パック質量で比較。kg、Wh、%。総量加重率＝100×ΣDC差/Σ基準DC。個別率平均とは異なる。')
tab('TA-2_C_BRIDGE','付表C-1 未知部材質量差の全条件',c[c.series_id=='C_BRIDGE'],['design_policy','probe_id','unknown_mass_difference_kg','known_mass_boundary_kg','reference_running_mass_kg','rolling_case','trajectories','mass_saving_kg','saving_sum_Wh','weighted_saving_percent'],'既存2代表設計×7未知質量差×2参照質量×2Crr。各条件旧460固定軌跡。完成パック質量が確定した比較ではない。')
tab('TA-3_SUPPLEMENT_INTERVALS','付表S-1 補助的な全区間',ci,['series_id','condition_id','metric','scale','unit','point','analysis_units','clusters_present','lower95','upper95','undefined_resamples'],'元CLUSTER_SENSITIVITY_INTERVALS.csvの1,176行を無選択で収録。25需要群を単位とする10,000回percentile区間。現実地域・車両・モデル誤差を含まない。検定0件。')
cohorts=[{'series':'A政策','physical_units':78,'replication':'36条件＝2808判断','independent_structure':'26親、25需要群','endpoint':'固定ODのモデル上の完了・定時率','limit':'実交通・DC未評価'},{'series':'A機構','physical_units':64,'replication':'36条件×4arm＝9216arm','independent_structure':'取得成功例の条件付き部分集合','endpoint':'訪問順・出発変更の対応差','limit':'反実仮想、政策実行とは別'},{'series':'B','physical_units':460,'replication':'8設定×10rep＝36800参照','independent_structure':'26親、25需要群','endpoint':'保存計画のOD品質、CPU工程資源','limit':'exact407/53、配送DC未評価'},{'series':'C主感度','physical_units':460,'replication':'T08全4464行、bridge25760行','independent_structure':'旧保存軌跡、現在Bとは別系列','endpoint':'質量・固定速度Controlled-DC','limit':'地域網FAIL、未知BOM、量子材料改善未実証'}]
table('tables/T3-1_COHORTS.csv',cohorts)
# Primary literature checked using original preprints / publisher metadata; no guessed DOI.
lit=[('Farhi et al.','2014','A Quantum Approximate Optimization Algorithm','https://arxiv.org/abs/1411.4028','3.7/3.13','一次原著の著者・表題・年を照合。今回の実装条件は別途保存コードによる。'),('Hadfield et al.','2019','From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz','https://arxiv.org/abs/1709.03489','3.7/3.13','preprint2017と掲載年2019を区別。DOI 10.3390/a12020034。'),('Bärtschi and Eidenbenz','2020','Grover Mixers for QAOA: Shifting Complexity from Mixer Design to State Preparation','https://arxiv.org/abs/2006.00354','3.13','原著の概念を参照。今回のDP/MC実装は実機資源を検証しない。'),('Chen et al.','2020','Chen et al., Nature Communications 11, 3411','https://www.nature.com/articles/s41467-020-17126-3','3.9','DOI 10.1038/s41467-020-17126-3。保存原論文Fig5g・Methodsをローカル照合。VASP/DFTと電極実験。'),('Field and Welsh','2007','Bootstrapping clustered data','https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9868.2007.00593.x','3.12','JRSS B 69(3),369–390。群内依存への方法論出典。今回の非確率標本の母集団妥当性を保証しない。')]
table('LITERATURE_VERIFICATION.csv',[{'author':x[0],'year':x[1],'title_or_identifier':x[2],'primary_url':x[3],'section':x[4],'scope':x[5],'status':'PASS_METADATA_AND_STATED_SCOPE'} for x in lit]+[{'author':s,'status':'HOLD_BODY_CITATION_WITHOUT_MATCHED_BIBLIOGRAPHY_ENTRY','scope':'本文と末尾一覧の対応を次回編集前に確認。類似姓・異なる年の文献で自動置換しない。'} for s in ['IPCC 2023','Schot and Steinmueller 2018','Geels 2002 (Geels 2012とは別)','Rotolo et al. 2015','Arvidsson et al. 2018','Papachristos 2018','Palackal et al. 2023','Delgado et al. 2022']]+[{'author':'Faraji-Niri et al. 2024','status':'HOLD_DOI_NOT_INDEPENDENTLY_CONFIRMED','scope':'Data in Brief 52,109798の既存引用を保持。DOIは推定しない。'}])
# Evidence claims include rejected extrapolations, retaining file hashes and keyed rows.
claims=[]
def claim(id,sentence,kind,series,file,locator,method,result,figure,limit,decision='採用可能'):
 src=use(F/file);claims.append({'claim_id':id,'claim':sentence,'evidence_class':kind,'series':series,'input_path':str(src),'row_or_problem_id':locator,'calculation':method,'result_and_denominator':result,'source_sha256':sha(src),'implementation_path':str(use(F/('run_a.py' if series=='A' else 'run_b.py' if series=='B' else 'run_c.py' if series=='C' else 'statistics_tables.py'))),'review_code':str(O/'scripts/review_numbers.py'),'figure_ids':figure,'limits':limit,'decision':decision})
claim('A01','固定ODモデルの全36政策条件でPE加重・件数定時配達率は100%であり、古典単独対照との差は0ppである。','CONDITIONAL','A','A_SUMMARY_BY_CONDITION.csv','D10-01..36','100×ΣqI(c<=due+102)/Σq','各条件78問題・556PE・312配送先','F3-1;F5-5','時間不変OD・理想サービス。現実の同等性を意味しない。')
claim('A02','QAOA採用1344判断、古典切替1464判断、正の出発遅延936判断であった。','DERIVED','A','A_POLICY_DECISIONS_2808.csv','全2808 policy行','採用方式・departure>0の行数','1344/2808;1464/2808;936/2808','F3-1','取得成功64問題を1344個の独立問題と数えない。')
claim('A03','取得成功64問題中59問題で訪問順が一致し、5問題で異なった。','DERIVED','A','A_POLICY_DECISIONS_2808.csv','acquired=Trueのproblem_idを一意化','Q_route_differs_from_C','59/64,5/64','F3-1','成功部分集合であり未取得14を除く政策全体ではない。')
claim('A04','経路のみの変更による問題別平均完了時刻差は−962.281〜＋5.859秒であった。','CONDITIONAL','A','A_PAIRED_PER_PROBLEM.csv','A_MECHANISM ROUTE_QC_CC','mean(4 complete_Q−4 complete_C)','64入力×36条件の入力別差の範囲','F5-4','全体平均・各配送先差・帰庫差とは異なる。')
claim('A05','出発のみの変更では、正の遅延768条件すべてで第4配送先までに遅延が吸収された。','CONDITIONAL','A','A_DELIVERY_COMPLETION_BY_STOP.csv','MECHANISM64 CC/CQ；departure difference>0','Δcomplete_k=Δdeparture−Σ(wait_CC−wait_CQ)','768/768条件；第1〜3先完全吸収372/684/744','F5-5','同一経路・固定OD。道路上で遅れを取り戻した実測ではない。')
claim('A06','政策評価の最小期限余裕は3133.461531秒であった。','CONDITIONAL','A','A_DELIVERY_COMPLETION_BY_STOP.csv','POLICY78 全11232配送先行','min(deadline−complete)','3133.461531秒','F5-5','旧native候補3099秒とは別指標・別モデル。')
claim('A07','機構比較の1920armは計画利用可能時刻と出発準備を満たさない。','DERIVED','A','A_MECHANISM_COMPARISON.csv','availability_feasible=False','departure >= max(0,plan_available+120) の否定','QC1152,QQ768 /9216arm','F5-4','裸の計画利用可能時刻より前という判定と区別。')
claim('A08','計算方法は配送システムへ影響しない、または同等である。','UNTESTED','A','A_SUMMARY_BY_CONDITION.csv','全36条件','0ppから一般化する推論は成立しない','同等性検定・実配送検証なし','F5-5','時刻差あり、指標飽和、対象と仮定に限定。','使用不可')
claim('B01','保存best計画は全36800参照で取得され、固定ODの実行可能性条件を満たした。','DERIVED','B','B_PLAN_REFERENCES_36800.csv','全36800行','permutation,ΣPE<=216,J+102n<=32400','36800/36800;460入力×8設定×10rep','F5-1','8192shot後のbest。各shot成功率や実配送成功率ではない。')
claim('B02','6設定の保存目的値および訪問順は古典初期解と一致した。','DERIVED','B','B_PLAN_REFERENCES_36800.csv','MEAN,CVAR10,CVAR01,COHERENT2,COHERENT4,ACTIVE','Fraction(objective)==initial；route list equality','27600/27600参照','F5-1','目的値一致だけから経路一致を推論せず、リストを直接照合した。')
claim('B03','mirror5設定では初期解が同じ制限支持内の厳密最小値と一致した。','DERIVED','B','B_CLASSICAL_ORBIT_COMPARISON.csv','mirror_family 2300fit','保存orbit optimum vs initial；元JSONも照合','2300fit全件一致','F5-1','全配送先を残した2^floor(n/2)支持。全n!最適の証明ではない。')
claim('B04','active設定では保存した3点gridでt=0が460入力すべてで選択された。','OBSERVED','B','B_ACTIVE_GRID_SELECTION.csv','460入力 selected_t','保存grid選択のreadback','460/460','F5-1','連続角度や別初期状態を含む一般QAOAの改善不能ではない。')
claim('B05','Grover P2/P3の全入力平均目的値差は＋1765.006／＋1760.995秒であった。','DERIVED','B','B_SUMMARY_BY_SCALE_AND_METHOD.csv','ALL GROVER_P2/P3','入力内10rep平均→460入力等重み','460入力；正は初期解より大きい','F5-1','全規模混合は補助。主は規模別。異なる予算間の一般優劣ではない。')
claim('B06','Grover P2/P3の改善・同値・悪化は各70・2270・2260参照であった。','DERIVED','B','B_PLAN_REFERENCES_36800.csv','各Grover設定4600行','有理数の目的値比較','1.521739% /49.347826% /49.130435%','F5-1','repは独立配送問題ではない。改善70参照は7物理入力に対応。')
claim('B07','厳密参照は407入力に存在し、53入力のgapは未確定である。','DERIVED','B','B_EXACT_REFERENCE_COVERAGE.csv','R4 21、R5 32 missing','exact availabilityの一意入力集計','407/460；gap潜在32560/36800参照','F5-2','未確定を0としない。参照solverを今回再実行していない。')
claim('B08','学習時間だけでは最終検証工程を含む処理時間を表せない。','OBSERVED','B','B_RESOURCE_SCOPE_SUMMARY.csv','GROVER_P3 FINAL_VALIDATION wall','工程別保存値','R3/R4/R5平均168.745/193.651/226.554秒','F5-3','CPU環境固有。QPU時間・共通end-to-end時間は未確定。')
claim('B09','今回の結果は量子計算一般が古典計算より劣ることを証明した。','UNTESTED','B','B_SUMMARY_BY_SCALE_AND_METHOD.csv','全設定','支持・定式化・予算が異なる比較','一般的優劣は判定できない','F5-1;F5-3','量子実機の速度・回路資源は未検証。','使用不可')
claim('B10','系列Bの計画差が走行DCを変化させた。','UNTESTED','B','B_PLAN_REFERENCES_36800.csv','B_DC_status','保存DC列なし','走行DC評価0件','F3-1','旧C軌跡で代用しない。','使用不可')
claim('C01','T08簡略質量会計のLP−S差は5.448297415kgであった。','CONDITIONAL','C','C_T08_ENERGY_FULL.csv','COND_LP_REF/COND_S200_REF','塗工材＋固定19kg＋15kg','96.145654799−90.697357384kg','F3-2;F5-7','完成パック製造や実材料改善を実証していない。')
claim('C02','T08下側Crrの固定軌跡DC差の総和は5941.555975Wh、総量加重削減率は0.412579010%であった。','CONDITIONAL','C','C_T08_PAIRED_DIFFERENCES.csv','CLASSICAL,S200,CRR_LOWER_BOUND','Σ(DC_LP−DC_S)、100Σ差/Σ基準','旧460軌跡；基準1440101.369798Wh','F5-7','保存軌跡・空荷・回生なし等の境界に依存。実EV削減率ではない。')
claim('C03','T09の代表既知部材差は固定担持9.722608121kg、固定面積5.977891152kgであった。','CONDITIONAL','C','C_T09_COMPONENTS_183.csv','B015/B051に対応する代表行','既知6部材LP−Sの和','2代表設計；全設計一律ではない','F5-6','T08との完成パック性能比較ではない。')
claim('C04','既知軽量化bは未知部材S−LP差δで相殺され、正味軽量化はb−δとなる。','CONDITIONAL','C','C_BRIDGE_MASS_DC_FULL.csv','B015/B051 全7probe','(knownLP−knownS)−(unknownS−unknownLP)','δ=bで0、δ>bで逆転','F5-6;FA-1','未知部材の実測分布を得たわけではない。')
claim('C05','T09完成パック質量183行は未確定で、全面対向の1行は不適合である。','INVALID','C','C_T09_COMPONENTS_183.csv','complete_pack_mass_kg；overlap_condition','NULL/FAILの保持','183 HOLD、うち幾何FAIL1','F3-2','不適合の記載は採用可能。設計成功という主張は禁止。')
claim('C06','量子計算による材料改善と実EV電力削減を実証した。','UNTESTED','C','C_T08_ENERGY_FULL.csv','材料参照はChen文献由来','古典DFT・電極試験と量子計算を区別','対象量子改善の実証0件','F3-2','計算算術の正確性は工学的成立を保証しない。','使用不可')
claim('S01','25需要群bootstrapの区間は群構成に対する補助的感度である。','CONDITIONAL','STAT','CLUSTER_SENSITIVITY_INTERVALS.csv','全1176行','25群を丸ごと10000回再標本化；percentile2.5/97.5','26親を含む25群；検定0','付表S-1','交通・材料・モデル構造誤差や現実母集団のCIではない。')
claim('S02','定時率差0ppの区間[0,0]は実配送における同等性を証明した。','UNTESTED','STAT','CLUSTER_SENSITIVITY_INTERVALS.csv','A_POLICY delta_F_PE_pp','飽和した固定cohortの再標本化','同等性検定なし','F5-5','無効果・同等性の一般化は禁止。','使用不可')
table('CLAIM_EVIDENCE_MAPPING.csv',claims)
# inventory reads and hashes source implementations, schemas and original-source ledgers.
for n in ['common.py','run_a.py','run_b.py','run_c.py','verify_independent.py','statistics_tables.py','verify_statistics.py','resource_and_sensitivity.py','FROZEN_PROTOCOL.json','OUTPUT_SCHEMAS_FROZEN.json','INPUT_LEDGER.csv','PARENT_GROUP_MAPPING.csv','B_RESOURCES_PER_FIT.csv','A_RAW_COMPUTATION_RESOURCES_78.csv','ARTIFACT_MANIFEST.json','STATISTICS_VERIFICATION.json','FINAL_REVIEW.json']:
 use(F/n)
use(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json');use(DOC)
finish('EDITORIAL_INPUTS',time.monotonic(),{'tables_main_and_appendix':8,'claims':len(claims),'scientific_runs':0})
