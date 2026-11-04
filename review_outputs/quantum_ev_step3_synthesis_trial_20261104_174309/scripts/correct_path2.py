from pathlib import Path
import pandas as pd, json, hashlib, re, shutil
O=Path(__file__).resolve().parents[1];R=O.parents[1];S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
def md(n,s):(O/n).write_text(s.strip()+'\n')
def tab(n,x):pd.DataFrame(x).to_csv(O/n,index=False)
# Preserve initial Step3 drafting stage, clearly historical and excluded from final claim set.
archive=O/'evidence/pre_correction';archive.mkdir(exist_ok=True)
for p in O.glob('*'):
 if p.is_file() and p.suffix in ['.md','.csv'] and p.name!='STEP3_SOURCE_MANIFEST.csv':shutil.copyfile(p,archive/p.name)
scpath=U/'review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json';sc=json.loads(scpath.read_text());baseline=U/'docs/research/EV_QUANTUM_APPLICABILITY_BASELINE_REVIEW_20261023.md';primary=R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659/sources/chen2020_primary_text.txt'
prov=[]
for s in sc['scenarios']:
 for k,v in s['parameters'].items():
  prov.append(dict(input_id=s['scenario_id']+':'+k,variable=k,value=v['value'],unit=v['unit'],input_type='逆算' if k=='q_ref' else '設計仮定',direct_literature_value=False,Chen_dependency='YES' if k=='q_ref' else 'NO_DIRECT',source_path=str(scpath),locator=s['scenario_id']+'/parameters/'+k,original_basis=v['basis'],original_source=v['source'],adoption='HOLD：主分析の確定材料値として未採用',allowed_use='条件付き参考例',unresolved='保持率分母の基準サイクル/full-cell適格性' if k=='q_ref' else '設計値の実製品適格性'))
for name,val,unit,typ,src,loc,dep,hold in [('LP容量100cycle',121,'Ah/kg','文献実測',primary,'Fig5g/body lines604–609','YES','1C保持試験'),('S200容量100cycle',194,'Ah/kg','文献実測',primary,'Fig5g/body lines604–609','YES','1C保持試験'),('LP保持率',.704,'1','文献実測',primary,'Fig5g/body','YES','分母サイクルHOLD'),('S200保持率',.99,'1','文献実測',primary,'Fig5g/body','YES','分母サイクルHOLD'),('T09未知部材',None,'kg','未知量',S2/'PATH2_T09_COMMON_INPUT_SENSITIVITY.csv','unknown_LP_kg/unknown_S_kg','NO','完成pack未確定'),('Crr圧力パラメータ下側',4.5,'bar','設計仮定',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json','Crr_model/cases/CRR_LOWER_BOUND','NO','圧力介入の実測ではない'),('Crr圧力パラメータ上側',2.6,'bar','設計仮定',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json','Crr_model/cases/CRR_UPPER_BOUND','NO','同上'),('走行質量検算範囲','1000–1250','kg','設計仮定',S2/'scripts/path2_analysis.py','lo,hi=1000,1250','NO','材料設計値の代用ではない'),('T08質量差b',5.448297415076934,'kg','モデル計算',S2/'PATH2_BOUNDARY_ANALYSIS.csv','T08_DEFAULT_MASS','YES','参考例のみ'),('T08利用率境界',.8770940719841043,'1','モデル計算',S2/'PATH2_BOUNDARY_ANALYSIS.csv','T08_DEFAULT_UTILIZATION','YES','参考例のみ'),('T08電圧境界',3.193155683779789,'V','モデル計算',S2/'PATH2_BOUNDARY_ANALYSIS.csv','T08_DEFAULT_VOLTAGE','YES','参考例のみ')]:
 prov.append(dict(input_id=name,variable=name,value=val,unit=unit,input_type=typ,direct_literature_value=typ=='文献実測',Chen_dependency=dep,source_path=str(src),locator=loc,original_basis=typ,original_source=str(src),adoption='HOLD' if 'HOLD' in hold or dep=='YES' else 'CONDITIONAL',allowed_use='文献条件限定' if typ=='文献実測' else '条件付き参考例' if dep=='YES' else 'モデル構造/凍結条件',unresolved=hold))
# Document every frozen DC control separately.
fpath=R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json';fz=json.loads(fpath.read_text())
for k in ['CdA','rho','g','rotational_equivalent_mass','eta_prop','grade_degrees','regen_model','auxiliary_scope','running_mass_definition']:
 prov.append(dict(input_id='DC:'+k,variable=k,value=json.dumps(fz[k],ensure_ascii=False),unit='see freeze',input_type='設計仮定',direct_literature_value=False,Chen_dependency='NO',source_path=str(fpath),locator=k,original_basis='凍結Controlled-DC',original_source=str(fpath),adoption='CONDITIONAL',allowed_use='一般質量感度；材料性能採用とは独立',unresolved='実車妥当性未検証'))
tab('PATH2_INPUT_PROVENANCE.csv',prov)
md('CHEN_2020_ADOPTION_CORRECTION.md',f'''# Chen et al.（2020）の採用判断の修正
本実行中の研究者指示を最優先とする。従来判断は、{baseline} の§5.1、§5表、§実行ゲートおよび {scpath} の q_ref.adoption=HOLD と一致する。2026年10月29日までの全会話の独立復元はしていないが、現存する10月23/26日の記録から未採用を確認した。
原著の直接報告は100cycle後1CのLP121 Ah/kg・保持率70.4%、S-200 194 Ah/kg・99.0%である。121/.704=171.875、194/.99=195.959595…は保持試験の分母容量の逆算である。保存設定は後者を195.959596に丸めている。初回放電実測値、実用full-cellの確定値、量子計算で改善した値ではない。基準サイクル・前処理・実用適格性はHOLDである。
T08主モデルの役割は維持するが、主分析は連続入力の数式感度・一般的境界・凍結DC質量応答へ再構成した。LP/Sペア、49点、81点u/V格子、T09の162条件、約0.413%は全て条件付き参考分析へ再分類する。数値は保存し、削除・無条件採用はしない。完成pack/実EV/量子材料改善への外挿を認めない。
元Step1/2、元コード、正式原稿は変更しない。本修正はStep3 trialの解釈・記載順・根拠ラベルを実質的に変更した。新しい材料数値は設定していない。
''')
sens=[
('q','−E/(V f_p u q²)','負','q>0,u>0,V>0,f_p>0','他の設計変数固定','49点171.875–195.959596はChen依存参考；独立した実用範囲なし'),
('u','−E/(V f_p q u²)','負','0<u≤1','他固定、保持率/ICEとの重複を避ける','既存0.8–1はChen q固定の参考範囲'),
('V','−E/V² [1/(q u f_p)+r/(q_n f_n)]','負','V>0,E>0','gross E固定；正負両極が変化','既存3.0–3.8Vは参考設定'),
('f_p','−E/(V q u f_p²)','負','0<f_p≤1','他固定；乾燥塗工材中の活物質割合','独立数値範囲未設定HOLD'),
('r=N/P','E/(V q_n f_n)','正','r>0','他固定；設計上の実用下限は未検証','独立数値範囲未設定HOLD'),
('q_n','−E r/(V f_n q_n²)','負','q_n>0','他固定；同じ容量基準','独立数値範囲未設定HOLD'),
('f_n','−E r/(V q_n f_n²)','負','0<f_n≤1','他固定；負極塗工材分母','独立数値範囲未設定HOLD'),
('F','1','正','F≥0','固定部材の会計範囲一定','既存17/34/51kgは共通部材の参考probe'),
('D(q,u,V,geometry)','∂D/∂x を上記に加算','未定','Dの設計式が必要','T09箔/膜/液は幾何式で整理','材料から独立の数値走査なしHOLD'),
('δ','1（scenario質量）、−1（ΔM）','正／負','追加部材差は符号付き実数','bと部材範囲を重複させない','δ=bは一般条件；b値は入力依存')]
tab('data/PATH2_ANALYTICAL_SENSITIVITY.csv',[dict(variable=a,derivative=d,sign=si,domain=do,held_fixed=fi,numerical_range=ra,Chen_dependency='NO_SYMBOLIC',evidence='A;E',status='CONDITIONAL') for a,d,si,do,fi,ra in sens])
p2='''# 経路2：主分析と寄与条件
## 1. 主分析：連続入力のモデル構造
T08は簡略質量モデルとして、M=E/V[1/(q u f_p)+r/(q_n f_n)]+F+D+δを用いる。Eはgross Wh、qとq_nは正負極の有効容量Ah/kg、uは追加利用率、f_p/f_nは乾燥塗工材中の活物質割合、rはN/P、Fは固定部材、Dは明示できる設計依存部材、δはそれらに含めない追加質量である。元T08ではDを独立算定しておらず、未知量を新たに0と確定した意味ではない。usable容量は設計grossと区別する。
data/PATH2_ANALYTICAL_SENSITIVITY.csvに全変数の偏微分・固定条件・範囲を記録した。E>0,V>0,q>0,u>0,0<f_p,f_n≤1,q_n>0,r>0で他を固定すると、q/u/V/f_p/q_n/f_nの増加はMを減らし、N/PとF・追加質量の増加はMを増やす。設計依存Dが変化する場合はその偏微分を足し、符号の維持を別途判断する。これらは数式上の局所感度であり、各変数が現実に独立変更可能であることや材料性能の実現を証明しない。独立材料範囲を新設定した数値実験は行っていない。
同電圧、共通負極・部材、同じf_p、基準u_ref=1、δ=0ではq_s u_s>q_refが質量削減の条件となる。一般には利用率・電圧・負極・設計部材差を全て質量式へ戻して判断する。qだけの向上から結論しない。
## 2. 主分析：成立・消失境界
同じ部材会計で算定した基準−scenarioの削減分をb、当該会計外のscenario−基準追加質量差をδと定義し、ΔM=b−δとする。δ<bで正、δ=bで0、δ>bで負となるのは収支恒等式である。一般のbはモデル式と入力・設計方針に依存する。特定の5.448297kgを普遍的境界とはしない。完成packに未知部材があればb−δの最終符号は未確定となる。
## 3. 主分析：材料入力を使わないDC質量感度
保存C460軌跡を固定し、凍結Controlled-DCのE(m)=Σmax(a_t m+c_t,0)/ηを評価した。Whへの換算をa,cに含める。W1=mgCrr ds、W2=.5ρCdA v²ds、W3=.5mΔv²、W4=.5×61Δv²を区間内で合計してから正値化する。材料比容量は入力しない。
Step2で宣言された走行質量区間1000〜1250kgで、各軌跡×CrrのE(m)は凸区分線形である。傾きが非減少であるため下端の右微分を検算することで区間内の正の質量感度を確認できる。本trialの材料非依存再検算をdata/DC_MASS_KERNEL_INDEPENDENT.csvに保存した。両比較質量がこの区間内で同一軌跡・同一物理条件なら、ΔMとΔE_DCの符号が一致する。δ=bによる質量相殺とDCゼロ点の一致はこの条件下での帰結である。
モデルは平坦、回生なし、補機/旋回損失除外、積載0、共通運転者55kg、固定η=.9、回転等価質量61kgである。二つのCrr設定をCIや圧力介入の実測として扱わない。速度・加減速・転がりの違いによる質量感度分布は固定軌跡の記述であり、920独立実道路試験ではない。
## 4. T09：設計構造への補完
T09は電極face面積、両面箔面積=face/2、面積×厚さ×密度の箔、膜面密度、空隙体積と充填に基づく電解液を計算する。fixed_loadingでは容量変化が面積と箔/膜/液へ伝わり、fixed_areaではその連動の一部が固定される。活物質と塗工材を重複加算しない。未知casing/tabs/foilmargin/packstructureはNULLのままとする。T09は完成packの確定モデルでもT08の外部実証でもない。
## 5. 条件付き参考シナリオ：Chen依存入力
ここからの具体値は主分析の確定材料値・代表効果量として採用しない。LP171.875、S195.959596Ah/kgは100cycle容量/保持率の逆算である。gross20kWh、u1、V3.5、N/P1.1、q_n360、f_p.75、f_n.98、F=100×.19+15=34kgという研究設計仮定を合わせると、T08質量96.145655/90.697357kg、b約5.448297kgとなる。これは実製品の完成pack差ではない。利用率境界0.877094、LP電圧3.5V固定のS側電圧境界3.193156Vも同じ逆算入力に依存する。
T09のB015（ROW031/032、fixed_loading）とB051（ROW103/104、LP面積固定）では、同じ逆算q、共通3.5V/u1、正極担持probe .1kg/m²、正負porosity .25等を置いた既知差が9.722608/5.977891kgである。これも条件付き参考値である。完成pack質量は未確定である。
同じ参考質量変化を凍結DCへ接続した460軌跡の総和比100ΣΔE/ΣE_refは下/上Crrで.412579/.413590%、個別率平均は.409329/.410435%、軌跡間SDは.012172/.012018ポイントである。総和比は基準電力量を重みに持つため個別平均と異なる。これらは量子技術や実EVの削減率ではない。49点q走査、81点u/V格子、T09の162条件、運転条件層別、group感度区間もこの参考入力への依存を保持する。未知部材に確率分布を与えない。
## 問いへの回答
連続入力の効果は設計・会計・走行条件を介して伝達され、追加/未知部材で消失し得る。T08数式感度と凍結DC質量応答を主とし、T09で構造依存を補う。具体的な材料性能、完成pack、実車効果、量子由来材料改善は未検証である。
'''
md('PATH2_CONTRIBUTION_CONDITIONS.md',p2)
md('PATH2_MODEL_DEPENDENCE.md','# モデル構造と参考例\n'+p2[p2.index('## 4.'):p2.index('## 問い')])
md('PATH2_MAIN_VS_REFERENCE_RESULTS.md',p2)
md('PATH2_LIMITATIONS.md','''# 経路2の限界
主分析はT08数式感度、収支境界と凍結DC質量応答であり、実用材料の入力範囲は未確定である。Chen由来の逆算入力は未採用HOLDである。49点・u/V格子・T09具体差・約0.413%は全て参考例で、独立一般数値感度とは呼ばない。活物質割合/N/P/負極性能/設計依存部材は解析感度までであり独立数値走査は未実施である。
完成pack、未知部材、実材料、実車妥当性はHOLD。既存T09_ROW183全面対向FAILと道路受入FAILを維持する。未知量に恣意的な分布を導入せず、保存窓外をゼロ補完しない。旧C460と新B460を対応させない。
''')
# Correct all final root narratives; archive is explicitly historical.
for p in O.glob('*.md'):
 if p.name in ['PATH2_CONTRIBUTION_CONDITIONS.md','PATH2_MODEL_DEPENDENCE.md','PATH2_MAIN_VS_REFERENCE_RESULTS.md','PATH2_LIMITATIONS.md','CHEN_2020_ADOPTION_CORRECTION.md']:continue
 text=p.read_text()
 text=text.replace('T08の具体境界','T08のモデル構造上の境界と参考シナリオの具体値').replace('T08既定条件','T08条件付き参考条件').replace('T08のpack値は仮定を含む出力','T08の参考質量は仮定を含む出力')
 if '経路2' in text or 'T08' in text:
  text+='\n\n経路2の採用修正：主分析は連続入力の解析感度・一般的相殺境界・材料入力を使わないDC質量応答である。LP/S-200の逆算容量およびそこから得た具体値は未採用の条件付き参考例である。旧49点・u/V格子・T09具体値・約0.413%にもChen依存が残る。PATH2_MAIN_VS_REFERENCE_RESULTSとCHEN_DEPENDENCY_AUDITを参照する。\n'
 p.write_text(text)
# Rewrite results path2 sections so reference values follow main findings.
p=O/'THESIS_RESULTS_DRAFT.md';t=p.read_text();a=t.index('## 5.');b=t.index('## 8.')
t=t[:a]+'''## 5. T08の連続入力と境界
主分析では、T08のM=E/V[1/(q u f_p)+r/(q_n f_n)]+F+D+δを解析した。他の入力とDを固定した正の定義域で、q/u/V/f_p/q_n/f_nの増加は質量を減らし、N/P、固定部材、追加質量の増加は質量を増やす。Dが設計に連動する場合はその感度を加える必要がある。偏微分、固定条件、適用範囲を表2とdata/PATH2_ANALYTICAL_SENSITIVITY.csvに示す。これは新たな材料実測値や独立の数値走査ではない。
質量差はΔM=b−δと整理した。同一会計の削減分bを追加質量差δが下回れば削減が残り、等しければ消失し、上回れば逆転する。この収支条件自体と、個別入力から算定するbの値を区別した。[S3-P2-A02/A03]
## 6. T09の部材構造
電極幾何により箔・膜・電解液の質量が変化する構造を整理した。固定担持量と固定面積で容量変化の伝達先が異なる。未知部材はNULLのままで、完成pack質量を算定していない。T09はT08のモデル構造依存を調べる補完であり、外部実証ではない。[図3]
## 7. 材料非依存DC質量応答と参考シナリオ
保存C460軌跡×2Crrについて、材料比容量を使わず、Step2の宣言区間1000〜1250kgで凍結DCの区分線形質量応答を再検算した。全920条件で正の傾きが確認された。したがって同区間内の同一軌跡・物理条件では質量削減とDC削減の符号が一致する。この検算は実EVでの削減実証ではない。[S3-P2-D01、data/DC_MASS_KERNEL_INDEPENDENT.csv]
以下は条件付き参考例である。Chen et al.（2020）の100cycle後容量121/194 Ah/kgと保持率70.4/99.0%から逆算したLP171.875/S195.959596 Ah/kgは、初回放電実測値または主分析の確定材料性能値として採用していない。設計仮定gross20kWh、u1、V3.5、N/P1.1、q_n360、f_p.75、f_n.98、固定34kgを置くと、T08簡略質量96.145655/90.697357kg、差5.448297kg、利用率境界0.877094、S側電圧境界3.193156Vとなる。高桁値は算術追跡用で実測精度ではない。[S3-P2-B01〜B03]
T09のfixed_loadingとLP固定面積では、同じ逆算q、共通3.5V/u1、担持量probe .1kg/m²、正負porosity .25等で既知差9.722608/5.977891kgとなった。完成pack差ではない。[S3-P2-S01]
参考質量変化を固定C460軌跡へ接続した総和比100ΣΔE/ΣE_refは下/上Crrで0.412579/0.413590%、個別率平均は0.409329/0.410435%、軌跡間SDは0.012172/0.012018ポイントである。25group区間[0.409778,0.415257]/[0.410775,0.416284]%もこの参考例への条件付き感度である。49点q走査、u/V格子、T09の162条件および走行条件層別はChen依存を保持する。920独立実道路実験、量子由来材料改善、実EV削減率として扱わない。[S3-P2-E01/E02]
''' +t[b:];p.write_text(t)
# Main claims vs dependent reference claims.
c=pd.read_csv(O/'STEP3_CLAIM_REGISTER.csv',keep_default_na=False)
reference=['S3-P2-B01','S3-P2-B02','S3-P2-B03','S3-P2-E01','S3-P2-E02','S3-P2-S01','S3-P2-O01']
for i,row in c.iterrows():
 dep=row.claim_id in reference;c.loc[i,'Chen_dependency']='YES' if dep else 'NO' if row.path!='cross' else 'MIXED_FRAMEWORK';c.loc[i,'result_role']='条件付き参考例' if dep else '主分析/証拠境界'
 if dep:
  c.loc[i,'claim_text']='【未採用の条件付き参考例】'+row.claim_text;c.loc[i,'applicability']='逆算q171.875/195.959596は主分析未採用HOLD；'+row.applicability;c.loc[i,'generalization_scope']='Chen依存・設計仮定限定。主要実証や一般代表値にしない。'+row.generalization_scope;c.loc[i,'audit_status']='CONDITIONAL';c.loc[i,'unverified_links']='入力採用HOLD；'+row.unverified_links
new=[]
for id,txt,num,kind in [('A02','T08の正の定義域で、他の入力と設計部材を固定すると、正極容量/利用率/電圧/活物質割合/負極性能の増加は質量を減らし、N/Pと固定/追加部材の増加は質量を増やす。','data/PATH2_ANALYTICAL_SENSITIVITY.csv','モデル上の仮定'),('A03','同じ会計で定義した削減bと追加差δについてΔM=b−δであり、δ=bが一般の質量相殺条件である。','具体bは入力依存。5.448297kgは参考値。','必要十分条件'),('H02','Chen保持試験の分母容量逆算値を実用full-cellの確定材料入力として主分析採用する根拠は不足する。','121/.704;194/.99;SCENARIOS adoption=HOLD','未検証事項')]:
 row={k:'' for k in c.columns};row.update(claim_id='S3-P2-'+id,claim_text=txt,path='path2',RQ='RQ2',analysis_subject='T08構造/入力採用',applicability='正の定義域/同一部材境界',numeric_evidence=num,source_files=str(O/'data/PATH2_ANALYTICAL_SENSITIVITY.csv') if id=='A02' else str(scpath),source_locator='see formula/provenance',method='数式導出/来歴監査',statistical_evaluation='非統計',unit_and_n='決定論的モデル；標本数ではない',uncertainty='実用入力範囲/設計連動は未確認',generalization_scope='T08の固定仮定内',unverified_links='実材料/完成pack/実EV',evidence_types='F' if id=='H02' else 'A;E',audit_status='HOLD' if id=='H02' else 'CONDITIONAL',condition_class=kind,finding_origin='Step3解析/採用修正',Chen_dependency='YES' if id=='H02' else 'NO',result_role='入力採用HOLD' if id=='H02' else '主分析');new.append(row)
c=pd.concat([c,pd.DataFrame(new)],ignore_index=True)
c.loc[c.claim_id=='S3-P2-D01','source_files']=str(O/'data/DC_MASS_KERNEL_INDEPENDENT.csv')
c.loc[c.claim_id=='S3-P2-D01','method']='Chen容量を入力しない凍結kernelの質量区分線形再検算'
# Normalize trace to actual files only (separate rows).
tr=[]
for i,row in c.iterrows():
 id=row.claim_id
 if id.startswith('S3-P1-S'): names=['PATH1_SUPPORT_AUDIT.csv'];code='support_and_verification.py';log='independent_verification.log'
 elif id.startswith('S3-P1-C'):names=['QAOA_CONTROLLED_CELL_SUMMARY.csv','QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv'];code='controlled_qaoa.py';log='qaoa_main.log'
 elif id=='S3-P1-T01':names=['PATH1_RUNTIME_SUMMARY.csv'];code='runtime_analysis.py';log='runtime_analysis.log'
 elif id=='S3-P1-H01':names=['EXACT_REFERENCE_STATUS.csv'];code='exact_recheck.py';log='exact_full.log'
 elif row.path=='path1':names=['PATH1_PAIRED_COMPARISONS.csv','PATH1_STATISTICAL_RESULTS.csv'];code='path1_statistics.py';log='path1_statistics.log'
 elif id=='S3-P2-D01':names=[];code=None;log=None
 elif row.path=='path2':names=['PATH2_BOUNDARY_ANALYSIS.csv','PATH2_T09_COMMON_INPUT_SENSITIVITY.csv'] if id=='S3-P2-S01' else ['PATH2_SENSITIVITY_SUMMARY.csv'];code='path2_analysis.py';log='path2_analysis.log'
 else:names=['CONTRIBUTION_CONDITION_TABLE.csv'];code=None;log=None
 sources=[S2/n for n in names]
 if id=='S3-P2-D01':sources=[O/'data/DC_MASS_KERNEL_INDEPENDENT.csv']
 if id in ['S3-P2-A02','S3-P2-A03','S3-P2-H02']:sources=[O/'data/PATH2_ANALYTICAL_SENSITIVITY.csv',scpath,baseline]
 c.loc[i,'source_files']=';'.join(map(str,sources))
 for source in sources:
  tr.append(dict(claim_id=id,source=str(source),locator=row.source_locator,analysis_code=str(S2/'scripts'/code) if code else str(O/'scripts/dc_independent.py') if id=='S3-P2-D01' else str(O/'scripts/correct_path2.py'),execution_log=str(S2/'logs'/log) if log and (S2/'logs'/log).is_file() else str(O/'logs/correction.log'),Step3_check=str(O/'evidence/NUMERICAL_RECHECK.csv'),draft='THESIS_RESULTS_DRAFT.md' if row.path!='cross' else 'THESIS_DISCUSSION_DRAFT.md',figure='図2/表1' if row.path=='path1' else '図3/表2' if row.path=='path2' else '図1/図4',Chen_dependency=c.loc[i,'Chen_dependency'],result_role=c.loc[i,'result_role']))
for n in ['STEP3_CLAIM_REGISTER.csv','CONTRIBUTION_CONDITIONS_FINAL.csv']:c.to_csv(O/n,index=False)
for no,path in [(1,'path1'),(2,'path2')]:
 c[c.path==path].to_csv(O/f'PATH{no}_CONDITION_CLASSIFICATION.csv',index=False);c[c.path==path][['claim_id','claim_text','numeric_evidence','generalization_scope','audit_status','evidence_types','Chen_dependency','result_role']].to_csv(O/f'data/TABLE{no}_CONDITIONS.csv',index=False)
tab('EVIDENCE_TRACEABILITY.csv',tr)
dep=[]
for _,row in c.iterrows():dep.append(dict(object_type='claim',object_id=row.claim_id,dependency=row.Chen_dependency,role=row.result_role,reason=row.applicability,status=row.audit_status))
for name,depflag,role in [('49点q連続走査','YES','条件付き参考：端点と基準が逆算q'),('81点u/V格子','YES','条件付き参考：q固定値が逆算'),('T09共通162条件','YES','条件付き参考：両容量が逆算'),('約0.413%と運転条件層別','YES','条件付き参考：質量差が逆算由来'),('DC1000–1250kgkernel再検算','NO','主分析：軌跡と物理条件だけ'),('T08偏微分','NO','主分析：記号式/正の定義域'),('δ=b','NO','主分析：収支式'),('図1–4','STRUCTURE_NO;REFERENCE_LABELLED','構造図；数値参考は別ラベル'),('図5_B品質','NO','経路1'),('図6_参考境界','YES','条件付き参考明記')]:dep.append(dict(object_type='analysis/figure',object_id=name,dependency=depflag,role=role,reason='入力依存を遡及分類',status='CONDITIONAL'))
tab('CHEN_DEPENDENCY_AUDIT.csv',dep)
md('STEP3_MIDRUN_CORRECTION_LOG.md','''# 実行中修正記録
研究者の追加指示を優先し、同じStep3 trialを継続した。完了済み数値検算は保持した。初期の生成草稿はevidence/pre_correctionに保存し、採用対象から除外した。経路1の数値・結論は変更していない。
修正前の配置：T08主モデルの具体値5.448297kg等を経路2結果の冒頭に配置。修正後：T08数式感度→一般相殺境界→材料非依存DC質量感度→T09構造→逆算入力の参考例とした。
49点やu/V・T09格子を単に一般感度と呼ぶ解釈を退け、全てのChen依存を台帳へ付した。主張・表・本文・図・Word・最終監査に同一分類を使用する。約0.413%等は数値を変えず残す。高桁は算術追跡用で物理精度を示さない。
新しい材料パラメータや確率分布は導入していない。追加計算は凍結式の材料非依存質量kernel再検算だけである。保持率の分母・full-cell適格性・未知部材・実車・量子材料接続はHOLDのままである。旧Step1/2と正式原稿は保全した。
''')
# Add citation scope, not a fabricated first-cycle measurement.
with (O/'THESIS_CITATION_CHECK.md').open('a') as f:f.write('\nChen, Q., Pei, Y., Chen, H., Song, Y., Zhen, L., Xu, C.-Y., Xiao, P., & Henkelman, G. (2020). Highly reversible oxygen redox in layered compounds enabled by surface polyanions. Nature Communications,11,3411. DOI:10.1038/s41467-020-17126-3。保存原著本文Fig5g対応箇所を確認した。直接報告100cycle容量/保持率と本研究逆算を区別する。主分析の確定材料入力としては未採用HOLDである。\n')
with (O/'UNRESOLVED_ITEMS.md').open('a') as f:f.write('\nChen逆算入力の主分析採用HOLD、独立材料性能範囲、設計部材Dの連動を追加。参考例数値を主要実証へ昇格させない。\n')
# Pin additional primary sources.
m=pd.read_csv(O/'STEP3_SOURCE_MANIFEST.csv');add=[]
for p in [scpath,baseline,primary,fpath,R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py']:
 add.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,version='read-only primary source; SHA256'))
pd.concat([m,pd.DataFrame(add)],ignore_index=True).drop_duplicates('path',keep='first').to_csv(O/'STEP3_SOURCE_MANIFEST.csv',index=False)
print('Correction saved; claims',len(c),'input provenance rows',len(prov))
