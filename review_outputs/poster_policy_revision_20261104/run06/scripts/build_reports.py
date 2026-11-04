from pathlib import Path
import csv,json,html,hashlib,shutil,difflib
from collections import Counter
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from content import REFS,TITLE,RQ,PURPOSE
R=Path(__file__).resolve().parents[1];ROOT=Path('/home/takuma/kmd-analysis');P=R/'reports';E=R/'evidence'
S2=ROOT/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S3=ROOT/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';S4=ROOT/'review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654';T4=ROOT/'review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043';OLD=ROOT/'review_outputs/no_sumo_full_analysis_20261102/run01';PRE=R.parent/'run05'
def rd(f):return list(csv.DictReader(open(f,encoding='utf-8-sig')))
def esc(s):return html.escape(str(s))
style='body{font-family:sans-serif;max-width:1500px;margin:32px auto;padding:0 24px;color:#17232d;line-height:1.75}h1,h2{color:#143653}table{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}th,td{border:1px solid #bac6cf;padding:9px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#edf3f7}tr:nth-child(even){background:#fafafa}.note{background:#f6f0e8;padding:16px}a{color:#286a96}@media print{body{margin:0}thead{display:table-header-group}tr{break-inside:avoid}}'
def page(name,title,body):
 (P/(name+'.html')).write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+esc(title)+'</title><style>'+style+'</style><body><p><a href="../index.html">成果物一覧</a></p><h1>'+esc(title)+'</h1>'+body+'</body></html>')
def table(name,title,rs,intro=''):
 with (P/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
 body='<p>'+esc(intro)+'</p><table><thead><tr>'+''.join('<th>'+esc(k)+'</th>' for k in rs[0])+'</tr></thead><tbody>'
 for r in rs:body+='<tr>'+''.join('<td>'+esc(v).replace('\n','<br>')+'</td>' for v in r.values())+'</tr>'
 page(name,title,body+'</tbody></table>')
def rec(keys,rows):return [dict(zip(keys,r)) for r in rows]
# Snapshot the now-completed scientific adoption record. Do not treat a file's timestamp as adoption.
late=[]
for f in [S4/'STEP4_FINAL_REPORT.md',S4/'STEP4_EVIDENCE_DECISIONS.md',S4/'CLAIM_EVIDENCE_MATRIX.csv',S4/'MATERIAL_INPUT_PROVENANCE_AUDIT.md',S4/'UNRESOLVED_ISSUES.md',T4/'SOURCE_THESIS_AUTHORITY.md',T4/'CHEN_REFERENCE_USAGE_AUDIT.md',T4/'THESIS_STEP4_INTEGRATED_TRIAL.docx',T4/'NUMERICAL_INTEGRITY_AUDIT.csv',S2/'PATH1_SUPPORT_AUDIT.csv',OLD/'C_T09_COMPONENTS_183.csv']:
 b=f.read_bytes();late.append(dict(path=str(f),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()));shutil.copyfile(f,E/('LATEST_'+f.name))
with (E/'LATE_SOURCE_INVENTORY.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=late[0]);w.writeheader();w.writerows(late)
# Independent arithmetic audit of support and structural completeness.
support=rd(S2/'PATH1_SUPPORT_AUDIT.csv');t09=rd(OLD/'C_T09_COMPONENTS_183.csv');adopt=rd(S4/'CLAIM_EVIDENCE_MATRIX.csv')
assert len(support)==460 and all(v['matching_orbit_min_equals_initial']=='True' for v in support)
assert all(float(v['active_selected_t'])==0 for v in support)
assert len(t09)==183 and all(v['complete_pack_mass_kg'] in ['', 'NULL'] for v in t09)
assert len(adopt)==35 and Counter(v['judgment'] for v in adopt)==Counter({'PASS':9,'CONDITIONAL':18,'HOLD':5,'NOT CLAIMED':3})
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(T4/'THESIS_STEP4_INTEGRATED_TRIAL.docx') as z:root=ET.fromstring(z.read('word/document.xml'))
paras=[''.join(v.text or '' for v in q.findall('.//w:t',ns)) for q in root.findall('.//w:p',ns)]
loc=[]
for term in ['36,800','5,983','920','参考','未採用']:
 matches=[(i,s) for i,s in enumerate(paras) if term in s];assert matches,term
 loc.extend(dict(term=term,paragraph_index=i,text=s,source=str(T4/'THESIS_STEP4_INTEGRATED_TRIAL.docx')) for i,s in matches)
with (E/'LATEST_STEP4_THESIS_LOCATORS.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=loc[0]);w.writeheader();w.writerows(loc)
(E/'LATEST_AUTHORITY_RECHECK.json').write_text(json.dumps(dict(support460='PASS',active_t0_460='PASS',T09_183_complete_pack_null='PASS',Step4_claim35_counts='PASS',latest_manuscript5_terms='PASS',scientific_adoption='Step4 completed; bounded main claims adopted; material input HOLD retained',formal_thesis_file_approval='unconfirmed'),ensure_ascii=False,indent=2))
# Information architecture, including why the two routes are paired.
structure=rec(['区画','読者の問い','役割・記載内容','根拠','紙面配分'],[
('左列・背景','なぜEV配送、なぜ量子計算か','物流とエネルギーが交わる対象を導入する。組合せ探索と電子状態評価の用途・到達点を区別する。','一次文献[1]〜[4]','左列上半分。本文20〜21pt'),
('左列・目的と構造','何を明らかにするか／なぜ二経路か',PURPOSE+' 二つの異なる計算出力を利用する工程の接続条件を比較する。','研究者指示、Step4 I-01、[5][6]','左列下半分。問いを背景色で区別'),
('中央列・方法','何をどのように計算したか','1入力、目的関数、需要・帰庫制約、古典主対照、5+1+2方式、CPU理想計算、反復・測定・集計を定義する。','B保存36800・主greedy460・Step2/3','中央列上部'),
('中央列・結果','どれが比較基準を上回ったか','平均ΔJを方式群・規模別に表示する。追加統制の97学習開始点と1入力の最適解取得を、主対照への改善と区別する。','PRIMARY_COMPARISON_RECONCILED.csv; DIAGNOSTIC_SELECTED_CELLS.csv','中央列下部。表の数値19pt'),
('右列・方法と質量条件','材料情報はどこで質量へ変わるか','容量・電圧→塗膜の式、固定・設計依存・会計外部材を定義する。183条件は補完モデルである。','T08記号感度・T09・Step4 P2-01/02/06','右列上部'),
('右列・走行計算','数値は何を意味するか','材料値なしの同一速度軌跡計算を示す。質量に対するDC微分の範囲図は材料改善率を意味しない。','DC核920条件・凍結モデル','右列下部。軸単位・分母・範囲注記を併記'),
('下段・統合結論','確認できた条件と未解決の接続は何か','A結果、B条件付き推論、C未検証を二経路で対応させる。支持内の候補不足と部材相殺を異なる機構として説明する。','Step4採用判断・経路別結果','全幅3行。本文18.5pt'),
('補足資料','どこまで再現・追跡できるか','全数値と数式・旧参考例の分母・方式詳細・時間範囲・原稿段落を収録する。ポスターの主張は紙面でも成立する。','各CSV・原稿・源流コード','本HTML群。参考文献は紙面14pt、全書誌はこちら')])
table('02_STRUCTURE','改訂後の説明構造',structure,'A1横841×594mmである。左→中央→右→下の順に読む。全内容を一段落へ詰め込まず、問い・定義・式・比較表・条件表へ配分した。')
# Numeric provenance: every headline, model parameter, legacy number is scoped.
nums=[]
def num(item,val,unit,definition,source,formula,assumption,interpretation,limit,status='主分析・保存結果'):
 nums.append(dict(項目=item,数値=val,単位=unit,定義=definition,出典=source,算出方法=formula,前提条件=assumption,解釈=interpretation,限界=limit,採用区分=status))
num('配送先規模・入力数','3/4/5/25/100:各78、125:70、合計460','先／入力','同一拠点・顧客集合・行列・需要等を持つ1つの保存問題','B_PLAN_REFERENCES_36800.csv; Step2 PATH1_PAIRED_COMPARISONS.csv','78×5+70=460','B時間窓なし、R4=100、同一入力SHA','異なる460保存入力の有限事例','460実配送や独立母集団標本ではない')
num('保存設定・反復・測定','8設定×10反復、8192ショット','条件／回','限定位置交換5、active1、GM2。反復は同一学習状態からの測定反復','B_PLAN_REFERENCES_36800.csv; SETTING_SCOPE_AUDIT.csv','460×8×10=36800保存best','1反復8192サンプル中の最良解','36800は保存best計画の件数','36800学習・独立入力・QPU実行ではない')
num('目的関数','J=ΣTij','秒','巡回路上の固定OD移動時間の総和','B保存目的fraction・移動時間行列','拠点出発・各先一度・拠点帰着','1車両。時間窓なし','短いほど移動時間の解品質が良い','実道路の配送効率・DC省電力は未検証')
num('主対照','ITERATED_GREEDY_ADJACENT_SWAP','方法','共通初期解へ古典の隣接交換反復改善を適用した解JC','B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv; latest Step4 P1-01','保存classical_best_secondsをFraction比較','同一入力SHA・同一目的・同一制約','旧初期解より強い現行の主品質対照','最速古典法・全域最適を意味しない')
num('変化量・改善件数','ΔJ=JC−JQ、正改善0/36800','秒／件','保存候補JQと主古典JCの差','CURRENT_AUDIT_CHECKS.csv; PRIMARY_COMPARISON_RECONCILED.csv','各候補を有理数比較→正の件数を集計','保存best同士、品質比較。予算公平性は別','対象有限cohortでは主対照を超えなかった','一般的不可能性や量子優位性の判定ではない')
num('旧初期解を改善する入力','7','入力','旧Jinitialと比べGMで改善した物理入力の数','B_IMPROVING_INPUTS.csv; CURRENT_AUDIT_CHECKS.csv','重複除去したproblem_id数','現行主対照ではない','比較基準変更が解釈を変える','現行主対照改善として再使用しない','補助・履歴比較')
for r in rd(E/'PRIMARY_COMPARISON_RECONCILED.csv'):
 num('方式別平均ΔJ '+r['scale']+'/'+r['config_id'],r['mean_primary_delta_s'],'秒','入力内10反復平均の、同規模・同方式内の等重み平均',r['source'],'mean_i(mean_rep(JC_i−JQ_i,rep))',r['inputs']+'入力。方式ごとの保存条件を保持','負なら主対照に比べ長い。紙面GM範囲はp2/p3二つの平均の範囲','範囲はCIではなく、規模・支持・予算の単一因果効果を表さない')
num('需要上限・帰庫時間・サービス','216、32400、102','PE／秒／秒毎配送先','需要尺度上限、総所要上限、固定サービス時間','B no-window feasibility in run_b.py; source arrays','Σdemand≤216; J+102n≤32400','PEからkgへの換算は本資料で設定しない','保存問題の可行性判定に使う','実配送需要・計算締切の観測値ではない')
num('限定位置交換の探索範囲','2^floor(n/2)','状態数','全顧客を維持し、対にした固定位置の交換方向を選ぶ支持','Step2 PATH1_SUPPORT_AUDIT.csv','独立matching-chain DPで支持内最小を計算','対象460入力、JC≤Jinitial','J*_S=Jinitial≥JCのためこの支持内で主対照改善は不可能','部分顧客への分割・必要実機qubit・全問題最適値と同一視しない','条件付き解析結果')
num('active選択','t=0、460/460','選択値／入力','保存の混合時間grid{0,.5,1}の選択値','Step2 PATH1_SUPPORT_AUDIT.csv','全入力active_selected_tを検査','p=3、保存grid・学習手続き','本設定で旧初期解が選択された','連続tや別の支持・予算の効果を断定しない')
num('全域参照の採用','414=234+78+61+41、未証明46','入力','列挙234、整数Held–Karp78、有理数双対61、保存MIP41','Step2 EXACT_REFERENCE_STATUS.csv; Step4 P1-04/07','accepted_exact_available=Trueを証拠別集計','41は外部VIPR等の独立証明なし、除外時373','全問題の参照と支持内最小を区別できる','46のglobal gap・最適一致は不採用。欠測は規模に偏る','条件付き参照。紙面には未掲載')
num('追加統制の規模','3入力×2支持×2初期×2混合×2層×2方式=96条件、97学習開始/条件','入力／条件／開始点','R0_001,R1_001,R1_020を選んだ診断計算','QAOA_CONTROLLED_CELL_SUMMARY.csv','96×97=9312学習、各10測定=93120記録','CPU可行部分空間計算、COBYLA上限64評価','旧8設定に混ぜず、候補存在と取得の機構を診断','3入力は無作為・代表標本ではない')
num('紙面の取得対照','0/97→97/97','学習開始点','R1_020のrep0最良が厳密最適と一致した学習数','DIAGNOSTIC_SELECTED_CELLS.csv','FULL_PERMUTATION/PROJECTOR/p1/QAOAでBASIS_INITIALとUNIFORM_SUPPORTを対照','1つの4配送先診断入力、主greedyは既に最適','初期状態はこの探索手続きの最適解取得に関係した','主対照を改善した入力数・一般取得率・実機効果ではない')
num('旧工程時間','0.8884206184／168.7453417103','秒','25先GM p3のFIT／FINAL_VALIDATION壁時計時間の平均','run05 evidence/B_CPU_TIME_EXAMPLE.csv','各78保存学習記録の対応工程を平均','CPU工程別、異なる計測範囲','検証工程も含め時間を評価する必要がある','全求解時間やQPU速度として使用しない','補助・履歴工程例。紙面未掲載')
num('追加CPU計時記録','9603=9312+291','記録','学習＋10測定のQ/dephased計時と1計画のgreedy計時','Step2 PATH1_RUNTIME_RESULTS.csv','保存sourceとscopeを区分して集計','共通初期生成、import、通信、QPUキュー等を除く','計測範囲を区別するための記録','異なる出力数・予算を公平なend-to-end比較にしない')
num('質量感度の入力','E,V,q,u,f₊,q₋,f₋,r,F,D,δ','各単位は定義欄','E grossWh,V cellV,q Ah/kg,u利用率,f活物質割合,r負正容量比,F/D/δ kg','PATH2_ANALYTICAL_SENSITIVITY.csv; T08 original model','M=E/V[1/(q u f₊)+r/(q₋f₋)]+F+D+δ','正入力、0<f±≤1。QΣ=E/Vは全セルAh総和。紙面では未知絶対質量項をU、基準との差をδと区別する','固定条件で∂M/∂q=−E/(Vu f₊q²)<0','独立に実現可能な材料範囲未確定。D未知を0と確定しない','主モデル・解析条件')
num('質量の相殺条件','ΔM=b−δ、δ=bで0','kg','b:同一会計で基準−変更後。δ:会計外で変更後−基準','PATH2_BOUNDARY_ANALYSIS.csv; latest Step4 P2-02','全質量差=既知会計差−会計外追加差','会計範囲の重複なし。同じ比較条件','δ<bで軽量化、δ>bで増量','完成パック成立・安全性の十分条件ではない','主モデルの収支恒等式')
num('T09設計条件','183、complete pack NULL=183','条件','部材会計・面積/塗工方針を個別計上した別モデル','C_T09_COMPONENTS_183.csv','正負塗膜＋Al/Cu＋膜＋液の既知小計','活物質を塗膜へ重複加算しない。T08固定34kgを加算しない','構造依存と未知BOMを補完する','182HOLD+1footprintFAILを完成pack成功と解さない','主分析を補完する構造モデル')
num('DC質量区間・母数','1000〜1250、460×2=920','kg／条件','宣言した質量範囲内で凍結軌跡・Crr設定ごとに評価','DC_MASS_KERNEL_INDEPENDENT.csv; freeze JSON','E(m)=Σmax(a_t*m+c_t,0)/η','材料入力NONE、同軌跡・同物理。範囲は宣言で実車調査範囲ではない','凸区分線形＋下端正微分により全域単調増加','920独立実道路試験ではない','主モデル結果・条件付き')
for r in rd(E/'DC_SLOPE_RECONCILED.csv'):
 num('DC下端右微分 '+r['case'],r['min_Wh_kg']+'／'+r['mean_Wh_kg']+'／'+r['max_Wh_kg'],'Wh/kg','m=1000kgにおける460軌跡の最小／平均／最大',r['source'],'活性区間係数の総和/η、節点の右微分','同一速度・係数。区間内で微分非減少','両比較質量が指定範囲内ならΔMとΔEの符号が一致','軌跡間幅はCI・実EV推定区間ではない','主モデル結果・条件付き')
num('DC物理・荷重','η=.90、回転等価61、共通運転者55、積載0、勾配0','無次元／kg／度','凍結モデルにおける固定パラメータ','CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json','Wroll=mgCrr ds; Wdrag=.5ρCdA v²ds; Wacc=.5mΔv²; Wrot=.5×61Δv²','各区間で合算後に正値化、3600ηでWh化。回生・補機・旋回損失なし','走行条件を固定して質量だけの応答を分離する','実運行への校正・道路動的妥当性・末端欠損はHOLD','主モデル仮定')
num('DC空気・抵抗係数','CdA=1.175、ρ=1.2041、g=9.80665、p=4.5/2.6','m²／kg/m³／m/s²／bar','固定制御条件およびCrr上下設定','CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json','Crr=.005+(.01+.0095(v_kmh/100)²)/p','上下の二設定、共通軌跡に適用','係数による感度を記述する','実圧力介入試験や信頼区間ではない','主モデル仮定')
# Explicitly retain legacy values without promoting their scientific status.
for r in rd(PRE/'evidence/C_MASS_DC_RECONCILIATION.csv'):
 for k in ['LP_pack_kg','S_pack_kg','mass_difference_kg','LP_running_kg','S_running_kg','LP_DC_sum_Wh','S_DC_sum_Wh','battery_reduction_percent','running_reduction_percent','DC_reduction_percent']:
  unit='%' if 'percent' in k else ('Wh' if 'Wh' in k else 'kg')
  formula={'battery_reduction_percent':'100(M_LP−M_S)/M_LP','running_reduction_percent':'100(m_LP−m_S)/m_LP','DC_reduction_percent':'100Σ(E_LP−E_S)/ΣE_LP'}.get(k,'T08質量式→同一保存軌跡の凍結DC式。基準をLPに固定')
  num('旧参考 '+r['case']+'/'+k,r[k],unit,'未適格な逆算入力から得た条件付き参考シナリオ',str(PRE/'evidence/C_MASS_DC_RECONCILIATION.csv')+'; Step4 P2-R01/R03',formula,'qLP=121/.704、qS=194/.99、E20000Wh,V3.5,u1,r1.1,q−360,f+.75,f−.98,F34kg','算術と分母は照合可能である','主材料効果量・完成pack・量子由来/実EV性能として使用不可','入力HOLD・参考例のみ／紙面削除')
num('Chen直接報告と逆算','LP121/.704=171.875、S194/.99=195.959596','Ah/kg','100cycle1C容量を保持率で割った分母参照値','Chen2020 Fig5g; Step4 MATERIAL_INPUT_PROVENANCE_AUDIT.md','mAh/gとAh/kgは数値同一。報告容量/報告保持率','保持率の分母サイクル/full-cell用途適格性未確認','逆算算術のみ確認','初回実測・実用full-cell入力・量子計算の出力ではない','主材料入力HOLD・参考例のみ')
num('T09旧参考の既知部材差','9.722608／5.977891','kg','固定塗工量B015 ROW031/032／固定面積B051 ROW103/104の基準−変更後小計','Step3 PATH2_MAIN_VS_REFERENCE_RESULTS.md; Step4 P2-R05','正負塗膜＋箔＋膜＋液の同会計差','逆算q、共通3.5V/u1、担持.1kg/m²、porosity.25等','設計方針により既知部材差が異なる例','T08差との直接実証比較・完成pack差ではない','入力HOLD・参考例のみ／紙面削除')
table('03_NUMERIC_PROVENANCE','主要数値・定義・出典・計算条件の対応表',nums,'主分析、モデル仮定、補助観測、旧参考値を区別する。48方式別平均も全行収録した。紙面の丸めは表示のみであり保存値を変更していない。原稿照合段落はevidence/LATEST_THESIS_LOCATORS.csvとLATEST_STEP4_THESIS_LOCATORS.csvにある。')
changes=rec(['対象','従来の記載・問題','修正後','理由・根拠'],[
('背景','何を明らかにするかが先行し、EV配送を選ぶ理由がない','物流とエネルギー、計画・車両・電池の関係から導入する','初見読者が応用対象と研究問題を理解するため。[1]'),
('問いと目的','短い条件列挙、方法と目的の重複','計算能力と利用判断の間にある問題→目的→問い→二経路を扱う理由','共通RQへの論理的接続を説明する'),
('主対照・符号','旧初期解を基準に7入力改善、JQ−Jinitial','最新の反復greedyをJCとし、ΔJ=JC−JQ。正改善0/36800','Step4 P1-01。数値改変ではなく比較対象を明示した最新分析採用'),
('8設定','GMなどの表現から同一方式に読める','限定位置交換5／active隣接1／GM2を分ける','支持・初期・backend・探索予算が異なる'),
('結果表','方式・規模・符号の意味の接続が弱い','n、母数、方式群別平均秒、GM層数別平均範囲を明示','同じ値の限定5とactive1も原表で別々に追跡可能'),
('追加統制','未掲載','3診断入力のうち4先1例で0/97と97/97を表示','学習開始点を独立入力数へ読み替えず、取得と主対照改善を区別する'),
('数値の参照','407／53で参照強度が不明','補足で414／46と41保存MIP限定tier、373除外感度を明示','最新Step2/4。支持内最小と全問題参照を区別する'),
('Chen依存値','5.67%→.478%→.413%が主結果に見える','紙面から主効果量表示を外す。数値対応表にはHOLD参考例として保全','最新採用判断P2-R01/R03。逆算算術と用途適格性は別'),
('材料方法','容量から質量への式と各分母の説明が不足','セルAh総和→正負塗膜→固定/設計/会計外部材を定義する。未知絶対質量Uと差δを区別する','初見読者が質量式を追跡できるようにする'),
('材料主結果','特定材料の効果率が中心','記号感度、ΔM=b−δ、材料値なしDC質量感度へ変更','Step4主分析採用範囲を反映する'),
('図','削減率の伝達が材料性能の実現に見える','1000kgのDC右微分を軸単位・460軌跡幅・平均で図示する','材料入力なしのモデル検算を視覚化する。CIではない'),
('統合考察','各経路の結果と未検証条件の列挙','A確認／B条件付き推論／C未検証を二経路で対照する','候補不存在と質量相殺の機構差、評価段階の非対称性を保持する'),
('レイアウト','A1縦二列で注記が集中','同じA1を横三列へ再配分。本文18.5〜21pt、見出し23〜40pt、参考14pt','新指示が基本レイアウト変更を許容。紙面上の定義を保持し、全導出は補足へ収録する')])
table('04_CHANGES','修正前後の比較',changes,'元のPPTX/PDF/本文をbaselineへ保存した。最新の研究判断により修正した箇所と、説明を補った箇所を分けて示す。')
# Exact text diff, separate from semantic comparison.
a=(R/'baseline/poster_text.txt').read_text() if (R/'baseline/poster_text.txt').exists() else (PRE/'poster_text.txt').read_text();b=(R/'poster_text.txt').read_text()
page('04_TEXT_DIFF','原文と改訂文の全文対照',difflib.HtmlDiff(wrapcolumn=65).make_table(a.splitlines(),b.splitlines(),'run05','run06',context=False))
conditions=rec(['ID','経路','区分','入力・処理・判断・成果','確認できた内容','根拠','適用条件・限界'],[
('P1-A','配送','A 保存結果','保存候補→主greedy比較','正改善0/36800。全候補の可行性とraw-shotの可行率は別','Step4 P1-01、80項目再集計','有限のB入力・保存best。未見入力や方式一般の不可能性ではない'),
('P1-B','配送','B 支持の解析条件','探索支持S→改善候補の存在','J*_S≥JCなら主対照を改善する解はこの支持内にない。mirrorは全460でJ*_S=Jinitial≥JC','PATH1_SUPPORT_AUDIT.csv。今回460行照合','支持内厳密最小は全問題最適値ではない。全配送先を保持し、部分顧客分割ではない'),
('P1-C','配送','A 診断観測','初期状態→有限予算の取得','R1_020全支持projector p1で0/97→97/97','QAOA_CONTROLLED_CELL_SUMMARY.csv','97は学習開始点数、rep0の最良が最適。greedyは既に最適。一般率へ外挿しない'),
('P1-D','配送','B 採用条件候補','候補検証・時間→計画採用','候補の可行性と品質を古典側で検証し、計画取得の全工程τ≤Hを別判定する','Step4 P1-12/時間scope、研究枠組み','Hは更新入力から採用判断までの許容時間。未設定なので合否未確認'),
('P2-A','材料','B 解析モデル','q,u,V等→正負塗膜質量','正入力・他固定でq増加は正極塗膜を減らす。利用率・電圧・設計部材の変化で全体の符号は変わり得る','PATH2_ANALYTICAL_SENSITIVITY.csv','実材料で独立に変更できることは未検証。D未知を0と置かない'),
('P2-B','材料','B 収支恒等式','既知会計bと会計外δ→正味質量差','ΔM=b−δ。δ=bで軽量化が消失、δ>bで逆転','Step4 P2-02、PATH2_BOUNDARY_ANALYSIS.csv','同じ非重複部材会計。数式の境界であり実用電池の十分条件ではない'),
('P2-C','材料','A 条件付き計算観測','固定軌跡・質量→DC応答','920条件全てで下端右微分が正、凸性から指定区間で単調増加','DC_MASS_KERNEL_INDEPENDENT.csv・凍結モデル','1000〜1250kg、平坦・回生/補機なし等。モデル内部の計算確認である'),
('P2-D','材料','B モデルの帰結','質量差→DC電力量差','両質量が区間内・同速度/物理条件ならΔMとΔEの符号が一致する','Step4 P2-05','速度・積載・道路・効率等が変わる場合は本命題を流用しない'),
('P2-E','材料','B 構造補完','材料/設計方針→面積・部材','固定塗工量では面積が変わり箔膜液へ伝達、固定面積ではその伝達の一部を固定する','T09・Step4 P2-06','具体LP/S値は参考入力依存。未知BOM183条件。完成packは未確定'),
('I-1','横断','B 比較・考察','計算能力→利用判断→評価量','配送では候補の存在と取得、材料では設計・質量会計・走行条件がそれぞれ接続を制約する','上記結果・Step4 I-01','同じ改善率へ合成しない。量子上流の証拠は両経路で非対称である')])
table('05_CONDITIONS','成立条件・制約と根拠',conditions,'Aは今回確認した保存結果・固定モデル内の計算観測、Bは明示したモデル・論証・文献に依存する解釈、Cは未検証である。Aも現実の効果を実測したことを意味しない。')
holds=rec(['ID','未確定事項','現在の扱い','解消に必要な根拠','主成果への影響'],[
('H01','正式提出用論文ファイルの研究者承認','最新完了Step4科学採用台帳を優先する。ファイル全体を正式版と認定しない','研究者の版指定・承認記録','boundedな改訂案は作成可能。科学的採否と版承認を分ける'),
('H02','Chen逆算qのfull-cell材料入力適格性','171.875/195.959596と派生削減率は参考例のみ','保持率分母・サイクル条件・full-cell試験・材料工学的適格性','主分析は記号感度と材料非依存DCのため維持できる'),
('H03','独立に実現可能な材料変数範囲','新しい材料範囲や効果量を補わない','同時に整合するq,u,V,寿命,出力,安全性の測定・設計','主モデルの解析条件へ限定する'),
('H04','完成パック質量・未知BOM','case/tabs/冷却/BMS等をNULL保持。残差で補完しない','重複のない部材表、形状・封止・電気熱設計、対象材料での実証','特定材料の正味軽量化の最終符号は未確定'),
('H05','全問題最適値46入力・MIP41の証明強度','46のglobal gap除外、41条件付き参照','同一入力の厳密下界と可行解の等値・外部証明','JCとの差は使用できる。全最適性主張を限定する'),
('H06','道路形状・速度軌跡・位置の校正','建物由来の固定入力・保存区間として使用。実道路妥当性へ拡張しない','元座標変換と抽出系譜、道路N0/N1受入、速度・末端区間の検証','DC計算は制御モデル内部へ限定される'),
('H07','実運用許容H・全求解時間','CPU工程と出力数を区別。総時間合否なし','更新時刻・締切・前処理から採用までのend-to-end測定','品質と採用時間を独立した条件として残す'),
('H08','公平な探索予算・実機資源','方式間優劣・量子優位性を主張しない','同じ候補領域・予算・環境、状態準備・ゲート・qubit・誤りの評価','支持別・取得別の機構分析は保持できる'),
('H09','部分問題選択・全配送計画への統合','将来構成候補。実行済みハイブリッドとしない','選択方針、古典側検証、統合、動的更新に対する実験','今回の全配送先を保持した支持と区別する'),
('H10','量子物性情報→実材料→実用電池→実車','未検証の上流・下流接続。帰属効果なし','精度/費用を含む量子材料評価比較と設計判断、工学試験、実車評価','二経路の条件比較は可能だがシステム改善を実証したとはしない')])
table('06_HOLD','未検証事項・HOLD一覧',holds,'HOLDを埋めるための新実験、量子学習、solver、SUMO、材料・実車実験は今回実行していない。既存結果の算術再集計と原稿照合を行った。面接・RIQ・M1は方法から除外したままである。')
# Extended explanation makes the actual workflow reproducible without filling the poster with footnotes.
paragraphs=[
('研究の読み方',PURPOSE+' 問いは「'+RQ+'」である。配送計画と材料評価は同じ効果指標を作る二手法ではなく、出力の性質と利用工程が異なる二事例である。両者を比較することで、計算能力だけで寄与を判断できない接続箇所を具体化する。'),
('配送問題と場所の条件','B系列の1入力は拠点・n顧客と固定OD移動時間/距離・需要・サービス等の保存配列である。大田区のPLATEAU建物に由来する位置と代理拠点DEP006の系譜を既存方法記録で確認した。実注文の標本、商用拠点の実運行、実道路に校正済みのデータとは扱わない。保存NPZの識別子/行列とSHAは照合できるが、座標の抽出・変換チェーン全体の独立再現はHOLDである。無作為な一様配置などの分布を推測で補わない。'),
('配送の目的と制約','訪問順πについてJ=ΣTijを最小化する。全顧客を1回ずつ訪問し同じ拠点へ戻る。総需要≤216PE、帰庫時間J+102n≤32400秒である。PEは入力の需要尺度としてのみ使用し、kgへの換算を作らない。時間窓を用いない。サービス時間は評価される所要時間に加わるが、同じ入力の順序比較では102nは共通定数であり、目的Jには含めない。'),
('古典計算と量子モデルの役割','共通の保存初期経路Jinitialから、古典のITERATED_GREEDY_ADJACENT_SWAPがJCを作る。主比較はJCと保存量子モデル候補JQである。旧初期経路の生成費用を含む公平な全工程計時は未確定であり、上流の保存コードでは、due/readyが全先共通の条件下で二つの近傍構築と挿入構築から経路を選び、relocateと有向区間反転を最大3走査する。時間窓は全ready=0、due=32400で無効化されている。保存経路と元入力の結び付きはINITIAL_ROUTE_BINDINGS.csvで追跡する。量子側の状態・分布・測定はCPUで計算した。QAOAの混合・位相と古典角度最適化の役割を区別する。'),
('8保存設定の定義','限定位置交換5はMEAN_P2、CVAR01_P2、CVAR10_P2、COHERENT2_P2、COHERENT4_P2であり、全顧客を維持した2^floor(n/2)交換支持を用いる。activeはACTIVE_ADJACENT_P3_GRID、p3/t={0,.5,1}で、全顧客を保持して隣接交換の状態を扱う。GMはGROVER_P2/P3で、全n!順列の一様状態を理想的に扱い、DP/MC等のbackendを含む。これらを古典が事前列挙した同じ候補プールの選択器と説明しない。状態準備の実装コスト・実機コンパイル済み深さは未実証である。'),
('集計と最適性','1保存測定反復は8192ショットのうち最良の可行候補を記録する。入力・設定あたり10測定反復であり、10回の独立学習ではない。入力内平均→規模/方式内の入力等重み平均で表を作る。GM列の二端はp2とp3の平均の範囲でありCIではない。主差ΔJ=JC−JQの正改善は0。旧初期解に対する改善7入力とは異なる。全問題参照414のうち41は保存MIP証拠に条件付け、除外した373も考慮する。46入力はglobal最適値未証明。限定支持の厳密最小はこれと別のJ*_Sである。'),
('各計算が検証するもの','保存Bは有限入力・各保存方式の解品質と支持の制約を調べる。matching-chain DPの支持内最小と主greedyを照合すると、当該限定支持では改善候補そのものがないことが分かる。追加統制は候補が存在する場面で初期状態・混合・層・脱位相などが取得に関係するかを診断する。大規模GMの悪化原因を問題規模だけに帰属させる実験ではない。'),
('追加統制例の読み方','3診断入力、2支持×2初期状態×2混合×2層×QAOA/脱位相の96条件を保存結果から確認した。各条件97学習開始、COBYLA最大64目的評価、1学習10測定反復である。紙面ではR1_020/FULL_PERMUTATION/PROJECTOR/p1/QAOAの最初の測定rep0を用い、最適解を得た開始数を比較した。単一経路の基底状態0/97に対し、全支持へ等振幅で開始した状態は97/97であった。これは同じ小規模入力での取得過程の観測であり、主greedyは既に最適なので、主対照への解品質改善ではない。'),
('計算時間と採用の条件','τ_total≤H_planを採用判断の独立した条件候補とする。H_planは更新入力が与えられてから採用判断までに許容される時間であり、出発余裕や定時配達率を置換した変数ではない。新CPU計時9603行はQ/dephasedの学習＋10測定とgreedyの1計画を含み、出力数が揃わない。前処理・学習・候補生成・検証・後処理のscopeを区別し、初期構築、import、通信、実機待ち等を含む総時間と混同しない。旧25先p3の.888秒/168.745秒はFIT/最終検証という異なる工程の78記録平均である。'),
('材料モデルの正しい入力解釈','T08ではgross設計E[Wh]を平均セル電圧V[V]で割り、全セル容量総和QΣ[Ah]を得る。直列数等を含む端子Ahと異なる。正極活物質量はQΣ/(qu)、正極乾燥塗膜はこれを活物質割合f+で割る。負極塗膜はrQΣ/(q−f−)である。固定F、明示できる設計依存D、会計外の部材質量Uを加える。原稿の主質量式の未知項δは紙面ではUと表記し、比較に用いる差δ=U変更後−U基準と区別した。数値やモデル範囲を変更したものではない。これは完成パックの実測でも検証済みパック設計でもない。uは報告保持率を二重計上しない追加利用率であり、保持率逆算とは区別する。'),
('感度分析と符号条件','q,u,Vなどを連続記号入力として偏微分し、何を固定したときの符号かを示す。例えば∂M/∂q<0はE,V,u,f+等を固定した場合である。Dが変わればその変化も加える。同電圧・同負極・同部材・同f+・会計外差0ならq_new*u_new>q_ref*u_refで正極塗膜が軽くなる。実材料でこれらを独立に変えられるとは限らず、出力・寿命・安全性を満たす材料範囲は未確認である。'),
('T08とT09を区別する','T09はface面積・両面箔面積face/2・厚さ・密度・膜面密度・空隙体積と充填から箔/膜/液を計算する別の部材モデルである。固定塗工量とは単位面積あたり活物質質量を固定し面積を変える設計、固定面積とは基準面積を保ち塗工量・厚さを変える設計である。乾燥塗膜と活物質を二重加算せず、T08固定34kgをT09小計へ重ねない。183条件の完成パックは全てNULLで、未知封止・タブ・余白・構造・熱/BMS等を残す。'),
('b−δの定義','b[kg]を同じ既知部材会計の基準質量−変更後質量、δ[kg]をその会計外の変更後質量−基準質量とする。紙面の主質量式では会計外の絶対質量をUとし、δ=U変更後−U基準である。基準の会計外質量を0と仮定するのではなく、差をδへ集約する。正味削減ΔM=b−δだからδ=bで差が消える。この収支恒等式は、完成パックの工学的成立や量子計算による材料改善を証明しない。'),
('DCの導出と評価範囲','保存区間ごとに転がりmgCrr ds、空気.5ρCdA v²ds、並進慣性.5mΔv²、回転等価.5×61Δv²を足し、正の駆動仕事のみを3600ηでWh化する。a_tは質量依存のWh/kg係数、c_tは空気/固定回転項などのWh係数であり、E_DC(m)=Σmax(a_tm+c_t,0)/ηとなる。回生、補機、旋回損失、勾配を除き、共通運転者55kg・積載0・η.9を固定する。460の同じ保存速度軌跡×Crr二設定について、Step2宣言の1000〜1250kgを検証範囲とした。'),
('DC結果から言えること','E(m)は凸区分線形なので微分は非減少である。全920条件で下端1000kgの右微分が正と確認されたため、この範囲内では質量増加に対し電力量は単調に増える。紙面の線は各Crr設定における460軌跡の下端微分の最小〜最大、点は平均である。両比較質量が範囲内、同軌跡・同物理条件なら質量差とDC差の符号が一致し、δ=bは両者のゼロ点となる。材料入力の値や実EV校正を必要としないモデル内の結果であり、実EV削減率ではない。'),
('Chen値を主結果にしない理由','原著の古典DFT・電極試験と量子材料計算研究は異なる。121/.704と194/.99の逆算算術は確認できても、その値を実用full-cell容量として採用する根拠はHOLDである。最新Step4は逆算入力を使う質量96.15→90.70kg、電池5.67%、走行総質量.478%、DC約.413%と各格子結果を条件付き参考例に限定した。紙面では主結果として表示せず、本数値表で式と分母を保全した。過去の算術PASSを材料入力採用PASSへ昇格させない。'),
('統合して得られた研究上の知見','配送では候補の存在と取得を分けることにより、限定支持の候補不存在と、初期状態による取得差を区別できた。材料では有効物性の差が部材会計で相殺され得ることと、固定走行モデルでの質量/DC符号対応を示した。前者は探索集合の制約、後者は質量収支と走行条件の制約であり、同じ物理機構ではない。量子上流の物性評価利用は材料経路では未検証である。この非対称性を含め、計算能力→利用判断→評価量の接続を段階別に判定する方法的貢献である。'),
('文献の使用範囲','[1]は電動配送における計画・エネルギー制約の背景へ使い、原著の時間窓・充電を本実験へ導入しない。[2]はGM-QAOAと一様可行状態準備の関係、[3][4]は量子電子状態計算の用途・精度・計算資源の位置付けに用いる。[5]は利用主体・技術・運用の区別、[6]は将来構成の予見と固定前提の省察に限定する。包摂・応答性の実践や社会転換の実証、面接、RIQ、M1分析は実施したとしない。')]
page('07_RESEARCH_EXPLANATION','研究の内容・構造・方法・結果を追跡する説明', ''.join('<h2>'+esc(a)+'</h2><p>'+esc(b)+'</p>' for a,b in paragraphs))
# Authority and primary source use.
auth=rec(['資料','権威・用途','扱い'],[
('研究者の現在指示','最優先','定時指標・優位性目的・面接/RIQ/M1へ戻さない。'),
(str(S4/'CLAIM_EVIDENCE_MATRIX.csv'),'完了した35主張の科学的採用判断','PASS9、CONDITIONAL18、HOLD5、NOT CLAIMED3。主分析と参考例を区別する。'),
(str(T4/'THESIS_STEP4_INTEGRATED_TRIAL.docx'),'最新の全文統合試行原稿','本文と段落照合を追加した。正式承認版と自動認定しない。'),
(str(S3/'THESIS_STEP3_TRIAL.docx'),'Chen補正後の14頁試行原稿','方法・主結果の内容照合に使用。全文の代替にしない。'),
(str(S2),'実験・参照強化・統計の保存根拠','元のB候補36800・主greedy460・統制・DC核へ遡って再集計する。'),
('quantum_ev_thesis_step3_integration_20261104_173959','Chen訂正に先行する統合試行','地理・方法の系譜確認に限り、採用判断は新台帳を優先する。'),
('tmp_RsrchMstrDc_1026_results_integrated.docx','11月3日の全方法・付録を含む統合原稿','旧定時指標・面接方針や未採用材料効果量をそのまま再導入しない。'),
('run05 poster.pptx/pdf/text','改稿前の比較対象','baselineに複製し本文差分を保存。元ファイルは変更しない。')])
table('09_SOURCE_AUTHORITY','資料の正本性・採用優先順位',auth,'開始時はStep4が未完了であったが、作業中に完了資料を確認したため補足照合した。科学的採用判断の完了と、研究者による正式提出版の承認は異なる。')
table('10_REFERENCES','参考文献と主張の対応',[dict(番号=r['n'],著者=r['author'],年=r['year'],題名=r['title'],書誌=r['journal'],DOI=r['doi'],URL=r['url'],保存資料=r['file'],使用範囲=r['use']) for r in REFS],'6件。一次論文の本文/保存PDFと出版書誌を照合した。[1]保存PDFは2012年技術報告版で、掲載書誌2014年と区別する。Chenは主分析の参考文献として紙面に置かず、逆算の来歴監査でのみ参照する。')
print('reports built; numeric rows',len(nums))
