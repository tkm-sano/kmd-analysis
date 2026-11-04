from pathlib import Path
import json,hashlib,shutil,textwrap,csv
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S1=R/'review_outputs/quantum_ev_step1_design_trial_20261104_153058'
def md(n,s):(O/n).write_text(textwrap.dedent(s).strip()+'\n')
def table(n,x):pd.DataFrame(x).to_csv(O/n,index=False)
raw=pd.read_csv(O/'data/CONTRIBUTION_CONDITION_TABLE.csv',keep_default_na=False)
translations={
'P1-D01':'ΔJ=J_C−J_Qの正値を古典近似に対する改善と定義する。',
'P1-N01':'支持内に古典対照より良い可行解があり、その解へ正の測定確率があることは、有限shotsで正改善を得るための必要条件である。',
'P1-O01':'保存B系列では主greedy対照に対する正改善は36,800計画中0件であり、全保存bestは可行であった。',
'P1-O02':'R5のGrover p2は70入力の入力内平均差の平均が−5,983.706秒であった。',
'P1-O03':'R5のGrover p3も同じ保存比較条件で平均目的値がgreedyより悪かった。',
'P1-S01':'mirror支持最良値は全460入力で初期解に一致し、greedyが初期以下であるため、その支持内で正改善は不可能である。',
'P1-S02':'activeの保存3点gridでは全460入力でt=0の初期状態が選択された。',
'P1-C01':'R1_020の全支持・基底初期・graph p1では独立学習97回のprimary測定で最適解を58回取得した。',
'P1-C02':'同じ診断条件のgraph p2では最適解を78/97回取得した。区間の比較だけで有意差を認定しない。',
'P1-C03':'全支持でも基底初期projector p1は0/97、一様初期projector p1は97/97であり、支持の存在だけでは取得を保証しない。',
'P1-C04':'同角度の脱位相操作は期待目的値を変える条件があるが、最終sampled-bestの古典greedy超えとは異なる。',
'P1-T01':'計画採用にはτ_total≤H_planが必要であるが、H_plan未設定のため今回数値達成を判定できない。',
'P1-H01':'最適参照は414入力に拡張されたが、46は未証明であり、41の保存MIP証拠は外部検証未実施である。',
'P2-D01':'同一軌跡・同一物理条件と検証質量区間では、ΔM=b−δの正負とDC差の正負が一致する。',
'P2-B01':'T08既定条件では追加質量差δが約5.448297kgに達すると質量削減とDC差が消失する。',
'P2-B02':'同電圧・共通部材・追加質量なしではq_S u>q_LPが質量削減の条件であり、利用率境界は約0.877094である。',
'P2-B03':'LP側3.5Vを固定しS側電圧のみを変える既定条件の電圧境界は約3.193156Vである。',
'P2-E01':'下側Crr条件の460保存軌跡でDC総和比削減率は0.412579%、個別率平均は0.409329%であった。',
'P2-E02':'上側Crr条件では総和比0.413590%、個別率平均0.410435%であった。',
'P2-S01':'T09既知部材差は面積方針により約9.722608kgと5.977891kgに変わり、会計構造に依存する。',
'P2-O01':'同一質量差のDC伝達量は保存軌跡とCrr条件で異なるが、運転介入の因果効果を示すものではない。',
'P2-A01':'Controlled-DCは平坦・回生なし・補機等除外・固定軌跡を仮定する。',
'P2-H01':'量子計算の物性予測から実材料性能改善、完成pack、実道路成果への接続は未検証である。'}
claims=[]
for x in raw.to_dict('records'):
 id=x['claim_id'];path=x['path'];types=('A;B;E' if id in ['P1-S01','P2-D01','P2-B01','P2-B02','P2-B03'] else 'A' if id=='P1-D01' else 'A;E' if id=='P1-N01' else 'F' if x['status']=='HOLD' else 'E' if id=='P2-A01' else 'B;C' if x['statistical_evidence'] else 'B')
 claims.append(dict(claim_id='S3-'+id,claim_text=translations[id],path=path,RQ='RQ1' if path=='path1' else 'RQ2',analysis_subject=x['target_scope'],applicability=x['condition'],numeric_evidence=x['numerical_evidence'],source_files=str(S2)+'/'+x['experiment'],source_locator=x['experiment'],method=x['origin'],statistical_evaluation=x['statistical_evidence'],unit_and_n=x['numerical_evidence'],uncertainty=x['uncertainty'],generalization_scope=x['target_scope'],unverified_links=x['limitation'],evidence_types=types,audit_status=x['status'],condition_class=x['classification'],finding_origin=x['origin']))
for id,txt,lev,status,scope in [
('I01','両経路は、比較対象に対する差が中間の選択・会計・伝達条件によって消失し得るという比較枠組みで整理できる。','E','CONDITIONAL','今回の異質な二経路の分析的統合。共通効果量や一般法則ではない。'),
('I02','技術性能から社会技術システム上の成果を直接推定せず、接続ごとの証拠と未検証部分を示すことが評価上有用である。','E','CONDITIONAL','本事例からの方法的示唆。組織・制度・市場効果の実証ではない。'),
('L01','社会技術的変化を視野に入れる既存の観点へ、本研究の限定的な接続条件の評価を位置付ける。','D;E','CONDITIONAL','Geels2002/Schot&Steinmueller2018の限定的書誌・主旨確認。理論全体の検証ではない。'),
('H01','配送計画の改善が実道路での運用改善へ伝達することは今回実証していない。','F','HOLD','B→実運行の未接続'),
('H02','量子物性予測が現実の材料性能改善へつながることは今回実証していない。','F','HOLD','材料探索/合成/電極/full-cell適格性が必要')]:
 claims.append(dict(claim_id='S3-'+id,claim_text=txt,path='cross',RQ='RQI（RQ3表記案）',analysis_subject='経路間比較',applicability=scope,numeric_evidence='数値を合算しない',source_files=str(S2/'CONTRIBUTION_CONDITION_TABLE.csv') if lev!='D;E' else 'evidence/LITERATURE_CHECK.json',source_locator='両経路条件表',method='構造的比較・考察',statistical_evaluation='なし：新しい独立実証ではない',unit_and_n='二経路を二つの独立標本とはしない',uncertainty='因果接続・外部妥当性は未確認',generalization_scope=scope,unverified_links='実道路・実材料・組織制度市場',evidence_types=lev,audit_status=status,condition_class='未検証事項' if status=='HOLD' else 'モデル上の仮定',finding_origin='Step3考察上の推論'))
table('STEP3_CLAIM_REGISTER.csv',claims)
for path in ['path1','path2']:table(('PATH1' if path=='path1' else 'PATH2')+'_CONDITION_CLASSIFICATION.csv',[x for x in claims if x['path']==path])
table('CONTRIBUTION_CONDITIONS_FINAL.csv',claims)
trace=[]
for c in claims:trace.append(dict(claim_id=c['claim_id'],source=c['source_files'],locator=c['source_locator'],analysis_code=str(S2/'scripts'/('path1_statistics.py' if c['path']=='path1' else 'path2_analysis.py')),execution_log=str(S2/'logs'/('path1_statistics.log' if c['path']=='path1' else 'path2_analysis.log')),Step3_check='evidence/NUMERICAL_RECHECK.csv',draft='THESIS_RESULTS_DRAFT.md' if c['path']!='cross' else 'THESIS_DISCUSSION_DRAFT.md',figure='図2/表1' if c['path']=='path1' else '図3/表2' if c['path']=='path2' else '図1/図4'))
table('EVIDENCE_TRACEABILITY.csv',trace)
md('CLAIM_EVIDENCE_LEVELS.md','''# 証拠種類と監査判定
Aは数式・アルゴリズム上の帰結、Bは保存計算からの確認、Cは統計的推定・感度、Dは外部文献、Eはモデル仮定付き推論、Fは未検証仮説である。種類は優劣の序列ではなく、複数タグを許す。PASS/CONDITIONAL/HOLD/FAILは別軸であり、数式Aでも適用仮定があればCONDITIONALとなる。
物理的な実道路・材料の効果を確認した主張はない。Bは本資料では主にCPUシミュレーションと保存モデル出力の検証である。「独立検算」は別計算法での検算を意味し、外部第三者による査読ではない。
J*_S<J_Cは支持内に改善候補が存在するための必要条件であり、確率質量、有限測定、学習、時間、運用への伝達を保証しない。物理的十分条件へ昇格させない。
''')
md('CONFIRMED_VS_UNVERIFIED_FINDINGS.md','''# 確認済みと未検証
経路1の段階は、改善候補の存在→改善解への確率質量→取得→古典近似より良い最終解→締切適合→実運行反映である。保存Bでは主改善0、mirrorの候補不存在を支持内に限り確認した。新小規模試験の最適取得は古典超えではない。H_planと実運行接続はHOLDである。
経路2ではq/u/Vを与えた設計算術→部材質量→モデルpack質量→車両質量→固定軌跡DCのうち、T08内の算術・感度とT09既知部材の算術を確認した。現実の材料性能値の量子由来改善、完成pack質量、実車DCは確認していない。T08のpack値は仮定を含む出力、T09の完成値はNULLであり同じ確度ではない。
''')
p1='''# 経路1：寄与条件の統合
## 1. 探索可能性
同一入力・目的・制約で可行支持をSとし、J*_S=min_{s∈S}J(s)とする。改善取得が可能であるためにはJ*_S<J_Cが必要である。反対にJ*_S≥J_Cなら、この支持内のどの出力でもΔJ≤0である。これは支持に関する論証で、量子手法一般の不可能性ではない。
mirrorでは独立matching-chain DPによる全460入力のJ*_S=J_initialと、古典greedyのJ_C≤J_initialを組み合わせる。従ってJ*_S≥J_Cであり正改善の余地はない。初期解が全問題の厳密最適値である必要はなく、改善可能解が支持外にある場合も含む。この証明と保存0件の観測を区別する。[S3-P1-S01]
## 2. 解取得
支持内に改善解があっても測定確率が0なら取得できない。固定状態の可行改善集合に確率pがあるとき、独立Nshotsの少なくとも1回取得確率は1−(1−p)^Nである。p>0でも有限shotsでの取得を保証しない。学習・状態初期化・mixer・層・計算予算がpを左右する。
新実験は時間窓なしの3/4顧客3診断入力であり、支持2・初期2・mixer2・p1/p2・QAOA/脱位相の96cell、97学習start/cell、10測定/fitである。全支持graphのR1_020で58/97と78/97の最適取得を観測した。これは二つのWilson区間からの有意差主張ではなく、同じ上限64評価の局所最適化手続きに条件付きの観測である。支持を変えるgraph比較には生成グラフの変更も含む。脱位相は機構対照、greedyは主品質対照であり役割が異なる。[S3-P1-C01〜C04]
## 3. 解品質
主greedyに対する正改善は0/36,800。全best可行である。R0〜R2のGroverはgreedyと同等、R3〜R5では平均が悪化した。R5/p2の入力内平均差の平均は−5983.706秒、入力間SD1314.365秒、IQR1628.056秒である（70入力、各10測定）。mirror5とactiveは初期解同等であっても、greedyが初期を改善した入力では主対照に劣る。観測0件は未見入力・他の支持・他の学習・理想状態・実機で改善可能性が0という証明ではない。[S3-P1-O01〜O03]
## 4. 時間と資源
τ_total≤H_planは、品質とは別の採用条件である。H_plan未設定のため合否は判定しない。新9603記録はCPU上の限定pipelineであり、Q/dephasedは学習＋10測定、greedyは1計画である。import・共通初期生成・転送等も含まれず公平な1計画総時間比較は未確定である。shots8192、層p、支持次元、MPS/DP/MC backendは確認情報であるが、compiled深さ・nativeゲート・論理実装qubit・物理qubitは未算定である。旧n²表現やmirrorのfloor(n/2)方向を一律に実機必要qubitとしない。[S3-P1-T01]
## 5. 運用への伝達
計画採用・経路実行・道路状況との整合・運行制約を満たして初めて実運用へ接続し得る。しかしBの目的はOD旅行時間であり、実道路の運用改善・DC省電力の実証ではない。この接続は考察後段のHOLDとして残す。
## 問いへの回答
現行主比較で改善は成立しなかった。原因として証明できたのは特定mirror支持の改善候補不存在であり、activeの限定grid選択と新小規模の初期/mixer/layer依存は計算上の観測である。大規模Grover悪化の原因を支持・規模・予算の一要因へ断定できない。品質・取得・時間・運用を順に別判定する設計が経路1の成果である。
'''
md('PATH1_CONTRIBUTION_CONDITIONS.md',p1)
md('PATH1_THEORETICAL_VS_EMPIRICAL.md','''# 理論と観測
J*_S<J_Cという必要条件は最小化の定義から導かれる。mirror支持の具体的な最良値が初期と一致することは460入力についてDPで確認した事実であり、両者を組み合わせた不可能性はその支持内だけの帰結である。
最適取得58/97・78/97はランダム開始角での独立学習に対するprimary測定rep0の計算観測であり、普遍的取得率ではない。既存10repは学習反復ではない。正改善0件、期待値差、古典初期解との差も別の対象である。
''')
md('PATH1_LIMITATIONS.md','''# 経路1の限界
主系列の古典/量子予算は完全統制されていない。新小規模の精密比較は旧staged8全体を統制し直したものではない。選択3入力を確率標本としない。Groverの保存状態は数値近似を伴い、bootstrapはその誤差を含めない。0改善の区間を理想QAOAへ転用しない。
参照414は再列挙234、保存整数DP78、独立LP61（旧54＋新7）、保存MIPのみ41に分かれる。46未証明はNULL。41外部証明未実施を消去せず373参照感度も参照する。H_plan、QPU/compiled、実運行接続はHOLDである。
''')
p2='''# 経路2：寄与条件の統合
## 1. 段階と変換
材料入力q,u,V→必要電荷Q=E_gross/V→正極活物質Q/(qu)・塗工材Q/(qu f_p)、負極活物質NP Q/q_n・塗工材NP Q/(q_n f_n)→簡略pack質量→非pack車体＋pack＋運転者の走行質量→固定軌跡DC、という条件付き連鎖である。材料物性予測→現実の合成・電極性能改善はこの計算の上流にあり未実証である。
## 2. T08の境界
M=E_gross/V[1/(qu f_p)+NP/(q_n f_n)]+F+δを用いる。既定E=20000Wh、usable18000Wh、q_LP=171.875、q_S=195.959596Ah/kg、u=1、V=3.5V、NP=1.1、q_n=360、f_p=.75、f_n=.98、F=100×.19+15=34kgである。qは半電池保持率基準逆算proxyで、実用full-cell値ではない。grossを質量設計に、usableをstockに用い、保持率/ICEをuに二重適用しない。
基準とSのモデル質量差b≈5.448297kgは、同V・同u・共通負極/固定部材条件では正極塗工材差である。δはこれらと重複しないS−LP追加部材差である。δ=bでΔM=0となる式は収支恒等式であり、5.448297という値は指定入力での計算結果である。
同V・共通部材・δ0ではq_S u>q_LPが正の質量削減と同値で、u*=q_LP/q_S=.877094…である。LPのV3.5を固定し、S側のみVを動かす場合はV*=E[1/(q_S f_p)+NP/(q_n f_n)]/(M_LP−34)=3.193156…Vとなる。電圧変化では負極質量も変わる。上記固定条件のままuやVが境界を下回ると削減は消失・逆転する。[S3-P2-B01〜B03]
## 3. T09構造依存
T09は担持量から電極face面積を求め、両面箔面積=face/2、Al/Cu箔質量=面積×厚さ×密度、separator=max正負面積×面密度、液量=両極/膜の空隙＋extraに基づく既知subtotalである。正負塗工材に活物質を重ねて加算しない。
B015（T09_ROW031/032）はfixed_loading、B051（103/104）はLP固定面積である。両方の比較でgross20kWh/V3.5/u1、正極担持量probe.1kg/m²、正負porosity.25、NP1.1等を共通とし、既知差は9.722608/5.977891kgとなる。固定loadingでは材料変化に伴う面積差が箔・膜・液へ伝わり、固定areaではその一部が抑えられる。密度transfer等は仮定である。
δはcasing/tabs/foilmargin/packstructure等のS−LP未知部材差である。個別質量はNULL、差には確率分布を与えない。T08固定19+15kgを既知subtotalに加えて完成品を作らない。T09はT08の外部validationではなく会計構造依存の補完である。[S3-P2-S01]
## 4. DC伝達
各1s区間のW1=m g Crr ds、W2=.5ρCdA v²ds、W3=.5mΔv²、W4=.5×61Δv²を合計してから正値化し、E_DC=Σmax(W1+W2+W3+W4,0)/(3600η)、η=.9とする。各成分別の正値化ではない。massで正値branchが変わるため、成分寄与にはbaseline mask差とbranch補正を保持する。
総和比は100ΣΔE_i/ΣE_ref,i、個別率平均は(1/N)Σ100ΔE_i/E_ref,iである。Crr下/上側で総和比.412579/.413590%、個別平均.409329/.410435%、SD.012172/.012018パーセントポイント、N460である。これは920独立実道路試験ではない。25group感度区間はそれぞれ[.409778,.415257]/[.410775,.416284]%で、材料の実現確率やモデル誤差区間ではない。
## 5. 消失と一般化
検証された全920 trajectory/Crrの1000〜1250kgでDC(m)の傾きが正（最小.827573Wh/kg）である。従って比較する両質量がこの範囲にあり他の物理量が同じなら、ΔE>0/0/<0とδ<b/=/ >bが対応する。δ=bという収支自体と、DCへの単調伝達の検算を別に扱う。固定軌跡・平坦・回生なし・補機/旋回除外・積載0・運転者55kgに限定し、範囲外の物理や実車へ拡張しない。
## 問いへの回答
材料入力の変化は容量・電圧・部材設計条件を通じて質量へ伝わるが、追加/未知部材で相殺される。走行条件は伝達の大きさを変える。T09はb自体の構造依存を示す。完成pack不明のため実製品質量・実車効果は確定できず、量子由来材料改善も未検証である。
'''
md('PATH2_CONTRIBUTION_CONDITIONS.md',p2)
md('PATH2_MODEL_DEPENDENCE.md',p2[p2.index('## 3.'):p2.index('## 4.')]+ '\n共通固定質量の変化は差だけでなく基準エネルギーの分母とbranchを変え得る。異なるbを同一完成packの予測誤差のように比較しない。')
md('PATH2_LIMITATIONS.md','''# 経路2の限界
q/u/Vは実用材料性能の実証値ではない。T08の包括固定部材、T09の密度/面積/液充填仮定と未知BOM、寿命/安全/形成等が残る。既存T09_ROW183の全面対向FAILは維持する。
49点やu/V格子は決定論的感度であり標本数ではない。trajectory間の分布、parameter範囲、未知質量、統計感度は別である。Crr2設定は確率的区間ではない。保存軌跡末端の未観測電力量を0補完しない。旧C460と新B460を対応させない。地域道路受入・実車妥当性と量子材料接続はHOLDである。
''')
# Cross-path three-stage framework; stages are analytic roles, not a claimed time ordering.
cross=[]
for axis,a,b in [('技術能力','支持内改善候補と取得確率。部分的に検証','量子物性予測→実材料改善は未検証'),('適用・伝達','古典対照・可行性・学習/測定・時間。時間締切未確定','q/u/V/部材会計→モデル質量。完成packは未確認'),('対象指標','保存計画ΔJ。正改善0','固定軌跡ΔE。条件付き正/零/負'),('相殺・消失','支持制限、既に最適の対照、取得失敗、採用不可','追加未知質量δ、利用率/電圧低下、幾何連動部材'),('不確実性','入力/測定/学習を分離、理想状態誤差別','決定論的格子/構造/軌跡分布/未知BOMを分離'),('未検証接続','計画→道路上の実運行','量子予測→材料実現、モデル→完成pack/実車')]:cross.append(dict(axis=axis,path1=a,path2=b,common_inference='技術性能だけでは対象指標差を保証しない',evidence_type='E',status='CONDITIONAL',limitation='二経路を同精度・同指標で実証したという意味ではない'))
table('CROSS_PATH_CONDITION_MATRIX.csv',cross)
framework='''# 共通枠組みと経路間比較
技術的能力、システムへの適用・伝達、対象指標への効果の三段階で接続を記述する。ただしこれは分析上の役割であり、経路1のΔJが時間適合の後で初めて測られるという時系列ではない。ΔJは計画段階で評価され、時間は採用の別ゲートである。経路2では上流の量子技術能力自体が未実証で、仮定した材料入力以降をモデル化した。従って両経路で三段階全部を実験検証したとはいえない。
両経路で比較基準は結論を変える。経路1の初期解への改善を主greedy超えへ代用できず、経路2の既知subtotal差を完成pack差へ代用できない。これは因果効果量を足し合わせる共通尺度ではなく、「どの差を、どの境界で評価するか」という方法上の対応である。
不成立の機構も異なる。mirror支持は候補不存在を示し、δ=bは収支相殺を示す。前者を後者と同じ物理的損失と呼ぶことはできない。ただし技術入力が望ましい場合でも中間条件が対象指標差を遮断し得るという限定的な類似を認めることはできる。
未検証接続は、経路1では計画→実道路運用、経路2では量子物性計算→現実材料改善と完成pack/実車である。この非対称性を維持した比較こそ、本事例の統合考察である。
'''
for n in ['COMMON_CONTRIBUTION_FRAMEWORK.md','CROSS_PATH_SYNTHESIS.md','SYNTHESIZED_RESEARCH_FINDINGS.md']:md(n,framework)
md('GENERALIZABILITY_ASSESSMENT.md','''# 一般化の水準
1. 診断入力水準：R1_020の58/97と78/97は指定初期・graph・層・64評価・8192shots・97random-startに限定する。
2. データ/モデル水準：B460の0改善、mirror支持の証明、C460固定軌跡のDC正傾き・境界をそれぞれの支持/会計/物理範囲で述べる。
3. 類似EV事例水準：同じ目的・対照・符号化・運行/部材/物理仮定を共有する場合に検討枠組みを移せる可能性がある。数値の移植には独立検証が必要である。
4. 社会技術システム一般：性能と寄与を媒介条件で分ける視点は考察上の示唆である。組織・制度・市場・利用者の相互作用や普遍的法則を数値モデルから実証したとはいえない。
''')
md('RESEARCH_CONTRIBUTION_STATEMENT.md','''# 研究貢献の限定的記述
本研究の貢献は、EV配送の二つの異なる技術経路について、比較対象・媒介・消失条件と証拠境界を追跡可能な形にした点にある。支持内最良値と主古典対照の関係、取得と品質の区別、追加部材相殺値とDC伝達範囲を数値と結び付けた。
量子技術評価一般に対する世界初の方法や既存研究を網羅的に凌駕する新規性は主張しない。既存の性能中心の問いに加えてシステムへの接続を評価対象にする、本事例における位置付けである。負結果は支持・基準・取得過程の条件を明らかにする材料であり、量子優位の有無で研究の成否を決めない。
''')
md('VERIFIED_AND_UNVERIFIED_CAUSAL_LINKS.md',p1[p1.index('## 5.'):]+ '\n'+p2[p2.index('## 5.'):]+ '\n上流量子材料接続、実道路、組織制度の因果関係は未検証である。verificationを実世界validationへ昇格させない。')
md('RESEARCH_OBJECTIVE_RQ_ALIGNMENT.md','''# 目的とRQの整合性（表現案）
目的は「量子技術がEV配送システムに寄与する条件を検討する」で固定する。量子優位性、実配送改善、実材料改善の実証へ変更しない。
RQ0は上位の寄与条件の問いを保持する。RQ1は同一問題・古典近似に対する解品質と計画時間の条件、RQ2は材料→電池/車両質量→固定条件DCの伝達条件である。Step1のRQIを、論文構成上「RQ3：二経路の比較から伝達条件について何が示唆されるか」と表記する案を示す。新規の独立実証課題を追加した意味ではない。正式RQ名・文言の採用は研究者判断まで未実施である。
Step1の厳密407/欠測53はStep2の監査で414/46へ更新された。主指標、ゼロ許容、hierarchy、T08主/T09補完は維持する。新97learning、解析的shots感度、参照373感度、零event上限はStep2で追加された診断/補助分析として区別する。研究設計自体のすり替えではない。
''')
# Manuscript: results factual, discussion integrates mechanisms and levels, conclusion answers purpose B.
results='''# 結果節草稿
## 1. 分析対象と比較条件
本研究では、時間窓なしのB系列460入力について8設定・各10測定反復、計36,800保存計画を評価した。規模は3・4・5・25・100・125顧客であり、入力数は78・78・78・78・78・70である。旧時間窓あり系列、旧99顧客系列、材料評価に用いた旧保存軌跡とは区別した。目的はデポ発着の有向OD旅行時間総和である。主対照はiterated greedy adjacent swap、random swapを第二対照、古典初期解を補助、厳密値を最適性参照とした。主差ΔJ=J_C−J_Qは正を改善とする。数値判定には保存十進数由来の分数を用いた。[表1、S3-P1-D01]
10測定反復は同じ学習済みfitからの独立乱数streamによる8192shotsの反復であり、10回の独立学習ではない。入力内平均の後に規模内等重み集計を行った。25需要group・26親の依存を保持し、固定cohortの記述を主とした。
## 2. 解品質評価
全保存bestは可行であった。主greedyに対する正改善は0/36,800であった。Grover p2/p3は3〜5顧客で主対照と同等であり、25顧客以上では平均差が負となった。125顧客のGrover p2では70入力の入力内平均差の平均−5983.706秒、入力間SD1314.365秒、IQR1628.056秒を得た。需要group再標本化の95%補助感度は[−6516.669,−5515.460]秒であった。この区間は実配送母集団の校正済みCIではない。[S3-P1-O01/O02]
mirror5設定とactiveの保存解は初期解と一致したが、greedyが初期を改善した入力では主対照より悪かった。全460入力のmatching-chain DPによる支持内最良値が初期と一致することを照合した。activeの3点gridは全入力でt=0を選択した。これらの結果はそれぞれ支持と保存gridに限定した確認である。[S3-P1-S01/S02]
厳密参照は407から414入力に拡張された。46は未証明のまま欠測とし、gap/一致率の分母を414に限定した。414の証拠は再列挙234、保存整数DP78、独立有理数LP61、保存MIPのみ41である。後者の外部証明は未実施であり、除外後373参照の感度を別表とした。[S3-P1-H01]
## 3. 追加統制実験
3診断入力に対して支持・初期状態・mixer・層数・QAOA/脱位相の96cellを設けた。各cell97独立学習start、各fit10測定、計9,312fit・93,120測定を得た。学習はexact期待値を64評価上限のCOBYLAで最小化し、初期角seedと測定seedを分離した。97はprimary測定の最適取得率に対する95% Wilson最大半幅0.10の精度設計に基づく。[図2]
R1_020の全支持・基底初期・graph mixerでは、primary測定の最適取得はp1で58/97（Wilson95% [0.498437,0.689978]）、p2で78/97（[0.714216,0.870861]）であった。全支持projector p1では基底初期0/97に対し一様初期97/97であった。古典greedyは選択入力で既に最適であり、主対照への正改善はなかった。二つのWilson区間だけで設定間の有意差を判定していない。[S3-P1-C01〜C04]
同角度での脱位相に関する期待目的値の変化と、最終sampled-bestの方式差を別に保存した。shots1/8/64/8192の感度は同じ最終状態からの解析値であり、追加の独立学習数には数えなかった。
## 4. 求解時間と計算資源
新規9,603のCPU pipeline記録を工程別に計測した。4顧客の固定例FULL/UNIFORM/PROJECTOR/p2では、QAOAと脱位相の中央値は34.643/35.014msであり、それぞれ97fitの学習と10測定を含む。新greedyの同入力中央値は12.142msであるが1計画であり、作業量・出力数・scopeは一致しない。従って公平な1計画総時間比とはしていない。H_plan未設定のためτ_total≤H_planの達成は未判定である。[S3-P1-T01]
既存fitにはMPS、subset DP、MC等の異なるbackendとscopeがある。shots数・層数は記録されているが、compiled深さ、native gate数、実機qubit、通信、実運用totalは未算定である。CPU時間をQPU時間へ換算していない。
## 5. T08感度
T08を主モデルとし、gross20kWh、u1、V3.5、共通固定34kg等の条件で、LP/Sの簡略pack質量は96.145655/90.697357kg、差b=5.448297kgとなった。追加質量差をδとするとΔM=b−δである。利用率境界は0.877094、LPの電圧を3.5Vに固定したS側の電圧境界は3.193156Vであった。全て仮定したproxy入力に基づくモデル計算である。[表2、S3-P2-B01〜B03]
## 6. T09部材構造
T09を完成packの代替予測ではなく、電極幾何に伴う既知部材の補完モデルとした。同じ基礎条件のfixed_loadingとLP固定areaで、既知差は9.722608/5.977891kgとなった。未知casing/tabs/foilmargin/packstructureはNULL/差変数として保持した。T08の固定部材を加えて完成packを推定していない。[S3-P2-S01]
## 7. 走行条件別DC
旧C古典460軌跡と2Crrを対応させた。総和比100ΣΔE/ΣE_refは0.412579/0.413590%、軌跡ごとの率の平均は0.409329/0.410435%、軌跡間SDは0.012172/0.012018ポイントであった。25group感度区間は[0.409778,0.415257]/[0.410775,0.416284]%である。[S3-P2-E01/E02]
144case・132,480行の感度と162行のT09共通条件分析が保存されている。検証された1000〜1250kgで全920のDC(m)傾きが正であり、最小は0.827573Wh/kgであった。δ=bで質量/DC差がゼロとなり、両側で符号が反転した。距離・再発進・速度等に伴う差を層別したが、運転介入の因果効果は求めていない。[図3、S3-P2-D01/O01]
## 8. 条件の定量的整理
経路1の支持条件と経路2の相殺条件を表1・表2に整理した。定義/数式による帰結、保存計算の観測、統計的感度、仮定付き推論、未検証接続を別の証拠種類として記録した。実道路改善や実材料改善を結果には含めない。主張IDからSTEP3_CLAIM_REGISTERとEVIDENCE_TRACEABILITYを通じて元CSV・コード・ログへ追跡できる構成である。
'''
md('THESIS_RESULTS_DRAFT.md',results)
discussion='''# 考察節草稿
## 1. 経路1で何が成立しなかったか
主greedyに対する正改善が観測されなかったことは、今回の量子最適化がEV配送へ一般に寄与しないことを意味しない。比較した問題・支持・学習・測定・対照を固定した結論である。他方で、初期解との差だけを根拠に量子の寄与を述べることもできない。初期解を改善した古典近似を主対照にすると、初期同等の量子出力が劣る入力が現れるためである。本研究はこの対照依存を明示して負結果を保持した。
## 2. 支持と取得能力
J*_S<J_Cは候補存在の必要条件である。mirrorのJ*_S=J_initialとJ_C≤J_initialから得られる不成立は、単なる取得失敗より強いが、その支持の外には及ばない。改善候補が支持内になければ測定回数やその支持内の角度探索を増やしても主対照超えは得られない。この点は将来のアルゴリズム選択で支持を先に検査する動機となる。[S3-P1-S01]
全支持でも取得は別問題である。R1_020の初期状態、graph/projector、p1/p2の差は、候補空間が同じでも有限予算の学習/測定過程が結果を変えることを示唆する。58/97対78/97を層数一般の因果法則や有意差へ拡張しない。3診断入力は基準解のgapで選んだ機構確認用で、460入力の確率標本ではない。また脱位相は干渉の機構対照であり、主greedyと同等の実用対照ではない。[S3-P1-C01〜C04]
## 3. 材料性能からDCへの伝達
T08の結果は材料改善の実証ではなく、入力が実現し部材仮定が成立する場合の伝達条件である。qの増加が質量を減らすには利用率・電圧・容量設計が必要で、追加質量がbに達すれば差は消える。従って材料単体の比容量の差だけで車両側のDC効果を予測することはできない。
δ=bは質量収支の帰結であり、発見の内容をこの恒等式だけに置かない。指定条件のb/u/Vの値、構造でbが変わること、凍結軌跡/質量範囲でDC差の符号が伝達されることに定量分析の意味がある。[S3-P2-B01〜B03]
## 4. 部材会計と未知量
T09で固定loadingと固定areaが異なるbを与えるのは、正極活物質の差に加えて箔・膜・液が面積・空隙と連動するからである。T08の包括固定項をT09へ加えればこの区別が失われる。未知BOMをNULLに残すことは、完成品の効果について今は何がいえないかを示すために必要である。T09は外部の実測完成packによるT08 validationではない。
## 5. 二経路の共通点と非対称性
両経路は「技術的能力→適用・伝達条件→対象指標」の枠組みで整理できる。しかし経路1では量子手法の計算を実施してΔJを測り、経路2では量子による材料改善を実施せず入力を仮定してΔEを計算した。この非対称性を維持する。秒のΔJとWhのΔEを共通効果量にしない。[図4、S3-I01]
共通するのは、改善可能な入力を与えればシステム成果が自動的に改善する、という直結を支持しない点である。主対照、支持、初期/取得過程、部材会計、固定物理条件という中間条件が必要となる。ただし二事例の類似だけで社会技術システム一般の必要十分条件を導いたとはいえない。
## 6. 社会技術システムへの含意
既存の社会技術的変化を視野に入れる議論（Geels, 2002; Schot and Steinmueller, 2018）との接点として、本研究は個別性能と利用先の成果を接続条件で分ける分析を位置付ける。ここで得た示唆は本事例からの推論であり、組織・制度・利用者・市場の相互作用を数値的に実証したものではない。技術評価において比較対象と未接続を見える形にするという、限定的な方法上の貢献である。[S3-L01/I02]
## 7. 限界と反証可能性
旧Bは設定/支持/予算/backendが異なり、規模だけの因果効果は識別していない。既存10測定から学習安定性は推定できず、group区間は仮想母集団感度である。保存数値状態の誤差も別に残る。46未証明、41保存MIP外部未検証、H_plan、実機資源のHOLDを維持する。
経路2のq/u/V/密度等は仮定付きで、回生・補機・勾配・荷重変動等を評価していない。DC単調性は検証範囲と同じ軌跡/物理条件に限定される。他の物理を加えた場合、同じbとDCゼロ点を無条件に使うことはできない。[表3]
反証の優先対象は、支持変更後の同予算主対照超え、未証明/条件付き参照の独立証明、完全scopeの総計画時間、独立した実材料/full-cell/BOM、実車端子電力量と受入済み道路における運用比較である。どの証拠が現在の主張を狭めるか・覆すかを台帳へ記録した。
## 8. 未検証接続と今後
計画解の改善が実道路運用へ伝わるには、計画採用、出発、道路条件、実行遵守等の接続が必要である。本研究はそれを実証していない。また量子物性予測から材料改善へは、候補選定、合成、電極/セルでの再現、設計採用と安全・寿命等が必要である。本研究の感度計算はこれを代替しない。これらを考察後段に位置付け、次の独立実証課題とする。
'''
md('THESIS_DISCUSSION_DRAFT.md',discussion)
conclusion='''# 結論節草稿
本研究は、量子技術がEV配送システムに寄与する条件を、配送経路計算と電池材料・車両の二経路から検討した。量子優位性、実道路改善、量子由来の実材料改善の実証を目的とはしなかった。
RQ1について、保存B系列の主古典近似に対する正改善は観測されなかった。mirror支持の候補不存在を指定支持内で確認し、候補の存在と取得、初期対照との差と主古典近似超え、解品質と時間適合が別条件であることを整理した。小規模統制は初期・mixer・層・学習/測定への依存を示したが、量子優位や大規模一般則は導かなかった。
RQ2について、仮定した材料入力は部材・質量設計を介して固定軌跡DCへ伝達されるが、利用率・電圧・追加/未知部材によって消失・逆転し得ることを、T08の具体境界とT09の構造依存で示した。完成pack・実車・量子材料の実証とは区別した。
統合の問いRQI（RQ3表記案）への回答は、技術的能力だけで寄与を定義せず、比較基準、媒介条件、対象指標への接続と証拠境界を明示する必要がある、という本事例からの限定的な知見である。経路間の異なる証拠水準を保持した条件台帳と未接続の特定を成果とする。社会技術システム一般の法則や組織・制度効果の検証とは位置付けない。
以上は独立Step3 trialの結論案であり、正式採用・既存原稿への統合は未実施である。
'''
md('THESIS_CONCLUSION_DRAFT.md',conclusion)
# Tables and links are full datasets, not inferred summaries.
for number,path in [(1,'path1'),(2,'path2')]:table(f'data/TABLE{number}_CONDITIONS.csv',[{k:x[k] for k in ['claim_id','claim_text','numeric_evidence','generalization_scope','audit_status','evidence_types']} for x in claims if x['path']==path])
limitations=[dict(id='H'+str(i+1),link=a,required_evidence=b,current_scope=c,status='HOLD') for i,(a,b,c) in enumerate([('計画→実道路','採用/道路受入/実行/成果の対応','保存OD解品質のみ'),('量子予測→実材料','合成/電極/full-cellの独立検証','仮定した材料proxy以降'),('完成pack','部材BOMと安全寿命等','T09未知量NULL'),('実車DC','端子計測/積載/回生補機等','凍結モデル/観測窓'),('計画締切','H_plan根拠と全工程','CPU限定scope'),('参照証明','46厳密証明/41外部証明','414条件付き参照'),('書誌Papachristos2018','元引用意図と原著の特定','本文引用から除外'),('一般化','他事例/組織制度の独立検証','本事例の考察')])]
table('data/TABLE3_LIMITATIONS.csv',limitations);table('UNVERIFIED_LINKS.csv',limitations)
md('UNRESOLVED_ITEMS.md','# 残るHOLDと既存FAIL\n'+ '\n'.join(f"- {x['id']}：{x['link']}。必要証拠：{x['required_evidence']}。現在：{x['current_scope']}。" for x in limitations)+'\nStep2のH01〜H13を承継し、raw-invalid一部/未見入力/理想状態/compiled等も未解消である。旧道路受入FAILとT09_ROW183対向FAILは維持する。誤解釈のFAILは本文修正対象であり、元データの削除や改変で解消しない。')
md('THESIS_FIGURE_TABLE_PLAN.md','''# 図表計画
図1は二経路と検証/未検証接続、図2は支持→取得→ΔJと時間/運用ゲート、図3はq/u/V→部材→mass→DCとδ=b、図4は三段階の経路間比較である。実線は指定計算/モデル範囲、破線は未検証接続とし、物理実証との区別をlegendに明記する。
表1/表2はdata/TABLE1_CONDITIONS.csv/TABLE2_CONDITIONS.csvから作成し主張ID・数値・範囲・判定を付す。表3はdata/TABLE3_LIMITATIONS.csvである。
Step2の数値グラフを複製再利用し、出典CSVの必要部分をdataに保存する。新たな大規模数値グラフ計算は行わない。Wordは結果→考察→結論の順に図表・参照を対応させる。大学指定様式への最終整形はStep4へ引き継ぐ。
''')
md('THESIS_CITATION_CHECK.md','''# 引用監査
本文の数値根拠はS3主張IDとEVIDENCE_TRACEABILITY、Step2元CSV/コード/logへ対応させる。Step3の再集計はevidence/NUMERICAL_RECHECKに記録した。外部文献の効果量を本研究値として転用しない。
Geels, F. W. (2002). Technological transitions as evolutionary reconfiguration processes: a multi-level perspective and a case study. Research Policy,31(8–9),1257–1274. DOI:10.1016/S0048-7333(02)00062-8。著者機関レコードの書誌/要旨の限定確認である。全文精読完了とはしない。https://research.tue.nl/en/publications/technological-transitions-as-evolutionary-reconfiguration-process/
Schot, J., & Steinmueller, W. E. (2018). Three frames for innovation policy: R&D, systems of innovation and transformative change. Research Policy,47(9),1554–1567. DOI:10.1016/j.respol.2018.08.011。著者サイト書誌と出版社レコードを照合し、社会技術的観点への限定言及に用いる。1583–1584頁の別論文と混同しない。https://www.johanschot.com/publications/previous-journal-articles/
両者から本研究の三段階をそのまま引用したとはせず、三段階は本trialの分析上の整理である。社会制度の実証や量子寄与の因果根拠として使わない。
Papachristos(2018)は元引用意図/同定HOLDを維持し、草稿の根拠引用として採用しない。他の旧引用を今回全文再検証したとは主張せず、大規模文献節再構成は実施しない。量子/材料の数値は内部データの条件付き計算を引用するため、未精読の外部論文へ新しい経験的主張を帰属させない。
''')
# Explicit adversarial review with repairs.
corrections=[('全入力で量子の改善可能性はない','保存0件と可能性不存在を混同','保存主比較で0件であり、不可能性は証明したmirror支持内に限定する。'),('p2はp1より有意に優れる','別々のWilson区間では差検定を行っていない','指定条件で58/97と78/97を観測した。有意差と一般則は断定しない。'),('T09で完成packが軽量化した','subtotalと未測定BOMの混同','既知部材差が設計方針で変わる。完成packはNULLである。'),('δ=bという新しい実証法則を発見した','恒等式と検証を混同','収支恒等式と、その具体境界/固定モデルDC単調性の確認を分離する。'),('量子技術が社会技術システムを改善する一般法則を証明した','異質な二経路からの過度な一般化','本事例の限定的な比較枠組みと未検証接続の特定を提示した。'),('34.6msはQPU速度である','CPU/範囲混同','限定CPU pipelineの中央値であり、実機性能・運用締切達成は未判定である。')]
md('THESIS_STATEMENT_CORRECTIONS.md','# 反証的レビューによる文章修正台帳\n'+ '\n\n'.join(f'## R{i+1}：判定FAIL→修正後CONDITIONAL\n棄却する候補文：「{a}」\n理由：{b}。\n採用するtrial文：{c}\nこれらは危険な候補解釈の監査であり、元原稿に全候補文が実在したという主張ではない。' for i,(a,b,c) in enumerate(corrections)))
review=[]
for c in claims:review.append(dict(claim_id=c['claim_id'],original_strength=c['evidence_types'],audit_status=c['audit_status'],counterexample='支持/対照/物理/証拠の条件を変えたとき同じ結論になるとは限らない',falsifier='同条件で正改善を取得、支持最良値の誤り、独立BOM/実車検証、参照反証等',response='対象範囲を明記し上位一般化しない',statement=c['claim_text']))
table('CLAIM_STRENGTH_AUDIT.csv',review)
md('ALTERNATIVE_EXPLANATIONS.md','''# 代替説明と反証条件
正改善0は量子能力一般の欠如以外に、強い古典対照、制限支持、初期状態、有限角度探索、期待値学習とbest評価の相違、測定/数値近似によって説明し得る。mirrorの候補不存在以外の原因寄与を一意に分離したとはいわない。支持を拡張して同予算の改善取得を確認すれば、その支持に限定した不成立は適用されなくなる。
p1/p2差には局所最適化の自由度と同評価数制限、開始角のばらつきが含まれる。層数だけの普遍的効果ではない。同角度脱位相比較は干渉の診断で、最良古典手法との競争ではない。
DC差の代替説明は材料の量子起源ではなく、仮定入力・固定部材・幾何・空力/転がり/加減速・正値branchのモデル構造である。未知追加部材がb以上なら正差は消える。実測BOMや回生/補機モデルで異なる境界が出た場合、本モデル範囲を超える予測を撤回する。
両経路の共通性は分析上の類似であり、二つの独立標本による社会理論の検定ではない。別事例で枠組みが機能しない場合には、一般化水準を下げる必要がある。
''')
questions=[('経路1',8),('経路2',8),('統合',8)]
md('STEP3_ACADEMIC_REVIEW.md','''# 学術的レビュー
主張登録と数値照合後に、経路1・経路2・統合の各8項目を順に監査した。検算と文章レビューは同じ作業エージェント内の分離工程であり、外部査読ではない。
経路1：0観測と不可能性、支持とアルゴリズム、対照、取得と改善、反復、Wilson/層、CPU/QPU、46/41参照を区別した。経路2：量子材料帰属、簡略化、T09役割、未知BOM、収支恒等式、物理範囲、実車表現、軌跡分布を区別した。統合：証拠の非対称性、対象の相違、未接続、一般化、寄与の定義、目的B、量子優位非依存、数値との対応を確認した。
最も強い候補解釈6件をFAILとし、THESIS_STATEMENT_CORRECTIONSの限定表現へ修正した。最終草稿に無限定の該当断定を採用しない。HOLDは未証明参照・未知BOM・実道路/材料・実機・書誌等として維持する。claim別の反証条件はCLAIM_STRENGTH_AUDIT/ALTERNATIVE_EXPLANATIONSである。
''')
md('STEP4_HANDOFF.md','''# Step4への引継ぎ
本trialの採用は未決定であり、正式Wordへまだ統合していない。Step4では研究者の採用判断後、対象原稿版をhashで指定し、独立コピーへ結果/考察/結論と表1〜3・図1〜4を統合する。RQ0/RQ1/RQ2/RQIの保持とRQI→RQ3表記案の採否を記録する。定時配達率中心の旧節は履歴として扱い主指標へ戻さない。
414参照のうち41条件付きと46欠測を凡例で維持し、CPUタイミングscope、反復単位、Crr2条件/49点の非独立性を残す。T08主/T09構造補完、q/u/Vの仮定、BOM NULL、二つの未接続を削除しない。
論文草稿の外部文献は限定2件のみの確認範囲とPapachristos HOLDを承継する。既存文献節は別作業で同定/精読し、今回の草稿で全引用精読済みと表示しない。大学指定様式、Word実機、最終図表番号・引用リンク・頁参照・提出体裁は最終編集で確認する。新規実証やHOLD全面解消を今回の完了へ遡及的に要求しない。
''')
md('MAIN_RESEARCH_FINDINGS.md',conclusion+'\n\n'+framework)
md('EXECUTIVE_SUMMARY.md','''# Step3主要成果
目的Bを保持し、経路1の支持・取得・主対照・時間・運用の条件、経路2の設計・会計・mass/DC伝達・消失条件を分離した。保存主比較の改善0を保持し、mirrorの不成立を支持内に論証した。T08の具体境界とT09の構造依存を同じ完成packの比較にしない。
共通枠組みは技術性能と寄与の間の接続条件を可視化するものであり、異なる証拠水準を均すものではない。論文用結果/考察/結論、主張台帳、対向レビュー、独立DOCXと図表を作成した。実道路・実材料・社会制度の効果は未実証のまま考察後段へ位置付けた。正式採用と原稿統合は未実施である。
''')
md('README.md','''# KMD修士研究 Step3 独立trial
入口はEXECUTIVE_SUMMARY、MAIN_RESEARCH_FINDINGS、STEP3_FINAL_AUDITである。Task3-1〜3-6の対応はSTEP3_COMPLETION_MATRIXに記録する。目的Bを固定し、Step1/2を元CSV・コード・ログへ追跡して最小再集計を行い、条件統合と原稿化を実施した。新規大規模実験は行っていない。
STEP3_CLAIM_REGISTERとEVIDENCE_TRACEABILITYが主張/数値/証拠種類/判定の入口である。PATH1/PATH2の条件・分類・限界、CROSS_PATHの比較/一般化/貢献、THESIS_*の三草稿・図表計画・引用監査・独立Word、学術レビュー/訂正/代替説明を併置する。図表のsourceはscriptsとdata、表示確認はrenderである。全成果物一覧はOUTPUT_SHA256_MANIFEST.csvである。
STEP3_SOURCE_MANIFESTには実在パス・版hash、evidenceには再検算とGit/保全台帳を保存する。一部上流は外部preservationにあり、このtrialだけで旧全実験を再実行できるという意味ではない。元データ・旧trial・正式原稿を変更せず、commit/push/公開/正式統合は行わない。
''')
table('STEP3_COMPLETION_MATRIX.csv',[dict(task='3-'+str(i),execution_status='COMPLETE',judgment='CONDITIONAL',deliverable=x) for i,x in enumerate(['主張/証拠/出典台帳','経路1条件/理論観測/限界','経路2条件/構造/限界','共通枠組み/一般化/研究貢献','RQ整合/三草稿/Word/図表/引用','学術レビュー/反証/訂正/最終監査'],1)])
print('Synthesis and manuscript drafts saved')
