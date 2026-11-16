from pathlib import Path
import json,copy,re,hashlib
import numpy as np,pandas as pd
from docx import Document
from docx.shared import Cm,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import etree
O=Path(__file__).resolve().parents[1];R=O.parents[1];S4=R/'review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043';D=O/'data'
doc=Document(S4/'THESIS_STEP4_INTEGRATED_TRIAL.docx');s=json.loads((D/'SUMMARY.json').read_text());st=pd.read_csv(D/'GAP_DESCRIPTIVE_STATISTICS.csv');ist=pd.read_csv(D/'INPUT_UNIT_STATISTICS.csv');changes=[];figs=[];tables=[]
body=doc._element.body
archive_title='付録B　元原稿の保全記録'
def txt(el):return ''.join(el.xpath('.//w:t/text() | .//m:t/text()'))
def find(title):
 return next(el for el in body if txt(el)==title and el.xpath('./w:pPr/w:pStyle/@w:val') and el.xpath('./w:pPr/w:pStyle/@w:val')[0].startswith('Heading'))
archive=find(archive_title);archxml=[etree.tostring(x) for x in list(body)[list(body).index(archive):]]
# Builders append at the tail temporarily; the returned elements are moved into target sections.
def para(text,style=None):
 p=doc.add_paragraph(text,style);p.paragraph_format.widow_control=True;return p._p
def heading(text,level=2):
 p=doc.add_heading(text,level);return p._p
def table(title,heads,rows):
 els=[para(title,'Caption')];t=doc.add_table(rows=1,cols=len(heads));t.style='Step4 Table'
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','bottom','left','right','insideH','insideV']:
  el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'A8B4C4');borders.append(el)
 t._tbl.tblPr.append(borders);t.autofit=False
 for cell,h in zip(t.rows[0].cells,heads):cell.text=str(h)
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 for row in rows:
  for cell,val in zip(t.add_row().cells,row):cell.text=str(val)
 for row in t.rows:
  row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
  for cell in row.cells:
   for p in cell.paragraphs:
    p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.05
    for run in p.runs:run.font.size=Pt(8.2)
 els.append(t._tbl);tables.append(dict(title=title,heads=heads,rows=rows));return els

def fig(name,number,title,note,width=16.1):
 p=doc.add_paragraph();p.alignment=1;p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(O/'figures'/(name+'.png')),width=Cm(width));cap=para(f'{number}　{title}。{note}。出典：Step5 data/およびfigures/{name}.pdf。','Caption');figs.append(dict(number=number,title=title,file='figures/'+name+'.png',note=note));return [p._p,cap]

def replace(start,end,elements):
 a=find(start);b=find(end);xs=list(body);old=xs[xs.index(a)+1:xs.index(b)]
 for el in old:body.remove(el)
 for el in elements:b.addprevious(el)
 changes.append(dict(start=start,end=end,removed_blocks=len(old),inserted_blocks=len(elements)))

def append_before(end,elements):
 b=find(end)
 for el in elements:b.addprevious(el)
# Front matter, current-only labels.
for p in doc.paragraphs:
 if p._p is archive:break
 if p.text=='修士論文 全文統合trial｜Step 4':p.text='修士論文　Step 5改訂版'
 elif p.text=='2026年11月4日':p.text='2026年11月5日'
 elif p.text.startswith('研究者の採用審査用・独立作成。'):p.text='保存計算の再分析とStep4科学的採用判断を統合した独立改訂稿である。元原稿・既存成果物は変更していない。未検証事項と提出体裁上の保留を残す。'
 elif p.text.startswith('本原稿は11月3日統合版を内容保全の基準'):p.text='本改訂は来歴を確認したStep4全文統合版を基準とする。第1〜7章・付録Aを現行主論証とし、付録Bは元原稿保全の履歴である。付録Bの旧ΔJ符号・旧定時率・旧材料値を現在の結論として採用しない。'
 elif '主差ΔJ=J_C−J_Qは正を改善とする。' in p.text:p.text=p.text.replace('主差ΔJ=J_C−J_Qは正を改善とする。','主差ΔJ=J_candidate−J_greedyは正を悪化、負を改善とする。')
 elif p.text.startswith('本研究は保存結果の再分析、限定したCPU統制実験'):p.text='本研究は保存結果の再分析、既存Step2の限定CPU統制実験、決定論的質量・電力量モデルを用いる。Step5では新しい大規模QAOA・SUMO・厳密求解を行わず、保存ルートと元入力の全件照合、目的値差と時刻差の再集計、凍結DCの軽量検算を行った。保存計算と実世界の観測、数式上の帰結と条件付き推論を区別する。'
 elif p.text=='3.12　再現性と本trialの監査':p.text='3.12　再現性と改訂稿の監査'
 elif p.text.startswith('元入力・原稿をSHA256で固定し、出典'):p.text='作業開始時のGit状態と既存成果物のSHA256を記録し、読取入力・コード・元CSV・計算式・論文箇所を対応付けた。候補36,800ルートと古典460ルートの有向辺和を保存十進数の分数として再計算し、元測定JSON・NPZ・Step2比較と照合した。Step4科学判断を変更せず、Chen入力適格性と実運用/QPU等のHOLDを維持した。電子付録の正本はStep5のevidence/CLAIM_EVIDENCE_MAP.csv、ANALYSIS_INPUT_SHA256.csvおよびSCIENCE_INPUT_SHA256.csvである。旧根拠IDと原式はStep4の保全対応表と付録Bから追跡する。'
# Abstract.
e=[para('本研究の目的は、都市部のEV配送を対象に、量子技術の能力が配送サービス水準または走行時DC電力量へ寄与する条件を評価することである。配送計画の取得・採用を通じる経路1と、材料特性から部材・車両質量を通じる経路2を分け、技術能力、中間変換、運用成果の接続を検討した。'),para('経路1では、顧客時間窓なし460入力、8設定、各10測定反復の36,800保存計画を、同一入力の古典greedyと比較した。候補は量子アルゴリズムのCPUシミュレーション出力である。ΔJ=J_candidate−J_greedyの平均は+441.791秒、平均相対差は+22.244%、全計画中央値は0秒であった。入力ごとの80出力平均の中央値は+7.474秒、入力間SDは622.305秒であり、悪化はGrover設定と大規模層へ集中した。mirror支持では全460入力における支持内最良値が初期解と一致し、主greedyより良い候補が存在しないことを指定支持内で確認した。固定ODの帰庫差はΔJと一致するが、最終顧客完了差は最終帰路にも依存した。候補の帰庫余裕は最小7,435.748秒であり、対象の共通上限遵守に差は生じなかった。契約上の定時配達率と実採用効果は未検証である。'),para('経路2では、T08の記号的質量感度、同一部材会計の相殺・逆転条件、材料入力を使用しない凍結Controlled-DCの質量応答を主分析とした。460対応軌跡×2Crr、1000〜1250kgの範囲で質量感度は正であり、1000kg右微分の軌跡平均は2.368/2.432Wh/kgであった。Chen由来の逆算容量と具体的な材料質量差・削減率は実用入力として未適格の参考例に限定した。二経路は、支持・取得・採用/期限余裕、または部材会計・質量・走行条件を確定しなければ成果へ直結できない点で共通する。ただし経路1は計算出力比較、経路2は上流材料改善を未実証とする下流モデルであり、同じ証拠強度ではない。量子優位性、完成パック、実車効果、一般的な社会技術転換の法則は結論しない。')]
replace('要旨','目次',e)
# Purpose.
e=[para('本研究は、量子技術がEV配送システムへ寄与するための成立条件と不成立条件を、保存計算と明示した物理・会計モデルの範囲で評価する。上流技術の性能から運用成果を直接推定せず、解品質差または質量感度がどの段階で成果へ伝わるかを問いとする。'),para('RQ0は、何を比較基準・観測単位・証拠範囲とすれば、二経路の寄与を過大評価せずに検討できるかである。入力・反復・需要group、数値整合と科学的入力採用、CPU模擬と実機を区別する。'),para('RQ1は、候補計画が同一入力の主greedyに対して何秒・何%異なり、その差がどの取得・時間・採用・期限条件で配送成果へ反映されるかである。ΔJ=J_candidate−J_greedyを正で悪化と定義し、分布と入力別集計を主に用いる。'),para('RQ2は、材料特性が部材・車両質量へ変換され、その差が走行時DC電力量へ伝わるための条件、および相殺・消失・逆転条件は何かである。未適格の材料入力から実製品の代表効果を確定しない。'),para('RQIは、二経路に共通する接続条件と、技術成熟度・証拠の性質・評価可能範囲の相違は何かである。解品質の秒・%とモデル電力量のWhを同一の量子効果率へ統合しない。')]
replace('1.4　研究目的と研究質問','1.5　論文構成',e)
# Literature positioning: retain full 2.1-2.3.
e=[para('Hadfield et al.（2019）[OR03]の可行部分空間mixer、Bärtschi and Eidenbenz（2020）[OR02]のGrover mixerと状態準備、Palackal et al.（2023）[OR36]のCVRP分解と解品質評価は先行している。したがって支持・取得・可行性を区別する一般概念自体を新規性とはしない。本研究は、指定460入力の主greedyに対する差の分布と、支持内の改善解不存在を対応付ける事例分析として位置付ける。確認範囲は各原著公開要旨・書誌と既存の限定原著確認であり、全既往研究の網羅的精読ではない。'),para('Davis and Figliozzi（2013）[L14]は経路制約・速度・電力量・保有費用を接続しており、Brooker et al.（2015）[S5-L01]のFASTSimは走行cycle上の車両物理とパワートレインを扱う。性能と運用条件を接続する構造には先行例がある。本研究の材料非依存DCは回生・補機等を除いた凍結モデルの条件付き応答であり、FASTSimの実車検証の結果を本研究へ継承しない。'),para('Delgado et al.（2022）[OR37]が扱う耐故障量子計算による電池物性評価・資源見積りと、量子由来材料の合成・実用セルへの採用は異なる。本研究は上流量子材料計算を実行せず、設計入力以降の会計と走行応答を検査する。この証拠非対称性を明示したまま二経路を比較する。'),para('実証的な追加部分は、全保存計画を秒・相対差で再集計し、入力内反復と入力間分布、設定差と少数入力の影響、帰庫と顧客完了の違いを分けた点である。方法的特徴は、主対照/支持/取得/時間/採用と、材料入力来歴/会計/車両質量/DCを追跡可能な台帳へ対応付けた点にある。標準的な対応統計、会計恒等式、閾値の性質を新規発明したとはいわない。'),para('Robinsonの概念モデル、Sargentのverification/validation、Field and Welshのクラスタ依存に関する旧引用は、書誌確認と原著内容確認を分けて保持する。Robinsonの同年文献はPart I（2008a）[OR30]とPart II（2008b）[OR24]に区別する。未確認の旧Papachristos引用は現行の主張根拠としない。「初めて」「先例がない」という主張は用いず、新規性は確認した文献範囲における対象cohortと証拠対応の限定的追加にとどめる。')]
replace('2.4　評価方法と本研究の位置付け','3　研究枠組み・方法',e)
# Methods, sign and statistics.
e=[para('目的値Jはデポ発着の有向OD旅行時間総和（秒）である。ΔJ=J_candidate−J_greedy、|ΔJ|、Relative Gap=100ΔJ/J_greedyを計画ごとに算出する。正は候補の移動時間増、負は移動時間減、0は同等である。J_greedy=0の相対差は未定義とし、欠測と0を区別する。今回の対象で分母0はなかった。旧Step1〜4のΔJ_old=J_greedy−J_candidateは逆符号であり、全件の保存分数から変換を照合した。付録Bの旧記述は履歴の定義である。'),para('符号付き平均と平均絶対差は別に定義する。相対差の平均と100(平均J_candidate−平均J_greedy)/平均J_greedyも別に算出する。全計画・入力別・設定別・測定rep別・入力×設定別に件数、平均、中央値、標本SD（ddof=1）、最小/最大、四分位、5/95百分位を記述する。百分位は線形補間を用いる。'),para('各入力の8設定×10測定を平均してから460入力の分布を併記し、設定ごとは入力×設定の10rep平均を用いる。完全均衡設計で全計画平均と入力等重み平均は一致するが、SD・中央値は異なる。36,800を独立標本とはせず、460にも25需要group・26親からの依存が残る。固定cohortの記述を主とし、Step5ではp値・母集団CIを導入しない。rep0〜9は反復番号であり、乱数entropyは入力/設定ごとに異なる。'),para('既存Step2の群再標本化区間とWilson区間は、それぞれ群変動への補助感度と指定した独立学習/測定手続きに条件付く取得評価である。未見需要やモデル/材料誤差の校正済みCIではない。全shotの可行率と保存best可行率、最適参照を分母とするglobal gapと主greedy相対差を区別する。'),para('運用時刻の再構成では保存NPZのready=0、顧客service=102秒、due=32,400秒を維持する。共通原点t0=0で帰庫R=J+102n、最終顧客完了L=R−最終帰路とする。実出発時計時刻や契約期限を補作せず、共通帰庫上限内の遵守と実配送の定時配達率を区別する。')]
replace('3.8　評価指標と統計','3.9　T08主モデルとT09補完',e)
# Chapter4, comprehensive but data distribution first.
e=[heading('4.1　対象と比較条件'),para('B系列は3/4/5/25/100/125顧客の78/78/78/78/78/70入力、計460入力である。8設定、各1fit、各10測定の36,800保存bestについて、元NPZ・測定JSON・古典RESULTのhashと目的値を全件照合した。全候補と主greedyが容量216PE・全顧客訪問・帰庫上限を満たした。候補は量子アルゴリズムのCPUシミュレーションであり、QPU実行ではない。'),para('主greedyは旧swap-QAOAのCPU秒をsoft capとする反復隣接swap降下であり、現行8設定との予算完全統制は成立していない。また古典bestは初期解保持あり、候補はraw sampled-bestである。以下の差は保存条件下の解品質であり、公平な総性能順位や量子因果効果ではない。初期解・random対照・最適参照は主対照と混合しない。'),heading('4.2　全計画と460入力の解品質差'),para('ΔJの平均は+441.790609秒、平均絶対差は441.790609秒、個別相対差の平均は+22.243524%であった。全計画中央値は0秒・0%である。全差が非負のため今回の二つの平均差は等しいが、一般の定義は異なる。greedy平均1,551.673633秒、候補平均1,993.464242秒から算出した相対差28.471877%は、個別率平均とは異なる。表4-1と図4-1/4-2に分布を示す。[S5-P1-01/02]')]
for level,label,data in [('all_plans','保存計画 n=36,800',st),('input_mean_all','入力80出力平均 n=460',ist)]:
 h=data[data.level.eq(level)];rr=[]
 for x in h.itertuples():
  rr.append([{'delta_s':'ΔJ 秒','abs_delta_s':'|ΔJ| 秒','relative_gap_percent':'相対差 %'}[x.metric],f'{x.mean:.3f}',f'{x.median:.3f}',f'{x.sd:.3f}',f'{x.min:.3f}〜{x.max:.3f}',f'{x.q1:.3f}／{x.q3:.3f}',f'{x.p05:.3f}／{x.p95:.3f}'])
 e+=table('表4-1'+('a' if level=='all_plans' else 'b')+'　'+label,['指標','平均','中央値','SD','最小〜最大','Q1／Q3','P5／P95'],rr)
e+=[para('出典：data/GAP_DESCRIPTIVE_STATISTICS.csvとINPUT_UNIT_STATISTICS.csv。SDは記述用ddof=1、百分位は線形補間である。入力平均の中央値7.473770秒・0.634226%、入力間SD622.305258秒・31.345204ポイントは、計画分布のSD1,459.379051秒・73.504767ポイントと異なる。460入力も独立無作為標本ではない。','Caption')]
e+=fig('F1_paired_objectives','図4-1','greedyと保存候補の旅行時間','全36,800計画を同一460入力に対応。各点は依存する反復出力であり独立標本ではない。両軸は秒')
e+=fig('F2_gap_distributions','図4-2','符号付き差と相対差の分布','36,800保存計画の記述頻度。左は秒、右は%。0は同等、正は候補の悪化')
e+=[heading('4.3　設定と入力規模による差'),para('設定別の入力等重み平均を表4-2、設定ごとの460入力平均の分布を図4-3に示す。mirror5とactiveの6設定は全保存出力が古典初期解と一致し、主greedyとの差は同じ+1.040464秒・+0.065503%であった。Grover p2/p3の平均は+1,766.046542/+1,762.035546秒、相対差は+88.887051/+88.668125%であった。全体平均は8設定を等重みに混合した値であり、単一アルゴリズムの代表値ではない。[S5-P1-03]')]
co=ist[ist.level.eq('input_mean_by_config')].pivot(index='config_id',columns='metric',values='mean')
e+=table('表4-2　設定別平均差（各460入力、各10測定）',['設定','平均ΔJ 秒','平均|ΔJ| 秒','平均相対差 %'],[[k,f'{x.delta_s:.6f}',f'{x.abs_delta_s:.6f}',f'{x.relative_gap_percent:.6f}'] for k,x in co.iterrows()])
e+=[para('出典：INPUT_CONFIG_MEANS_3680.csv/INPUT_UNIT_STATISTICS.csv。全統計とrep別集計は電子付録に保存した。計算予算・支持・初期状態・backendは設定間で一致しない。','Caption')]
e+=fig('F3_setting_input_boxes','図4-3','設定別の解品質差','箱ごと460入力の10rep平均。中央値/四分位、ひげ1.5IQR、外れ点を保持。上は秒、下は%')
e+=[para('Grover p2の平均差はR0〜R2で0秒、R3で+575.109082秒・+37.601662%、R4で+4,470.044218秒・+224.484514%、R5で+5,983.706453秒・+292.076023%であった。R5の70入力間SDは1,314.364537秒、中央値は5,674.647848秒である。主greedy相対差を、最適参照を分母とするglobal gapと混同しない。'),heading('4.4　入力ばらつきと平均への影響'),para('入力ごとの80出力平均は0〜2,315.123775秒であった（図4-4）。差総和への寄与は最大1入力1.139200%、上位5入力5.622822%、上位23入力（5%）21.644748%であった。上位23入力を除いても平均差は364.385416秒であり、1入力除外平均の範囲は437.709273〜442.753116秒であった。単一入力だけで全体平均が生じた結果ではないが、Grover2設定は差総和の99.823367%を占める。[S5-P1-04]')]
e+=fig('F4_input_gaps','図4-4','入力別の解品質差','460入力をproblem_id順に表示。各点は8設定×10測定の平均。上は秒、下は%')
cnt=pd.read_csv(D/'IMPROVED_EQUAL_WORSENED.csv');c=cnt[cnt.level.eq('all_plans')]
e+=table('表4-3　改善・同等・悪化（補助指標、36,800保存計画）',['内訳','件数','割合 %'],[[{'improved':'改善 ΔJ<0','equal':'同等 ΔJ=0','worsened':'悪化 ΔJ>0'}[x.classification],x.count,f'{x.percent:.6f}'] for x in c.itertuples()])
e+=[para('件数よりも、表4-1/4-2の方向と大きさを主結果とする。全計画の76.630435%が0であり、中央値0と正の平均は矛盾しない。','Caption'),heading('4.5　完了時刻・余裕と上限遵守'),para('保存Bのreadyは0、顧客サービスは102秒であり、顧客固有時間窓はない。同じ開始原点では帰庫R=J+102nとなり、全対応の帰庫差はΔJと一致した。平均帰庫差は+441.790609秒である。一方、最終顧客の配送完了Lは帰庫から最終帰路を引くため、平均差は+439.538924秒、差が負の計画は180件であった。各顧客の完了差はその顧客までのprefixにも依存する。[S5-OP-01]')]
op=pd.read_csv(D/'OPERATIONAL_SUMMARY.csv');e+=table('表4-4　完了時刻差と帰庫余裕（モデル内、各4,600保存計画）',['設定','平均帰庫差 秒','平均最終顧客差 秒','候補最小帰庫余裕 秒'],[[x.config_id,f'{x.mean_return_difference_s:.3f}',f'{x.mean_last_delivery_difference_s:.3f}',f'{x.min_candidate_slack_s:.3f}'] for x in op.itertuples()])
e+=[para('出典：data/OPERATIONAL_SUMMARY.csv。実時計時刻は未同定でありt0=0を共通時間原点とする。帰庫は配送完了と同義ではない。','Caption'),para('候補の帰庫上限32,400秒までの余裕は7,435.747703〜31,398.486586秒、greedyの最小余裕は16,556.905432秒であった。全候補とgreedyは共通上限内に帰庫し、各顧客の共通上限内完了割合も両側100%で差0ポイントであった。これは時間窓を除いた保存モデルでの遵守であり、実契約の定時配達率ではない。実開始時計時刻・契約期限・採用記録がないため実定時率は未定義として保持する。[S5-OP-02]'),para('一般の顧客期限D_jについて、greedy余裕s_gj=D_j−C_gjより候補のprefix完了増δC_jが大きければ、期限内から遅配へ変わり得る。この式は成立条件であり、新しい期限を設定した追加実験ではない。今回のBに期限付近の運用効果を外挿しない。計算取得が出発を遅らせる場合は出発遅延差も必要であり、fit秒だけをJへ足さない。'),para('参考採用規則min(J_candidate,J_greedy)なら全件で採用後J差は0となるが、実運用の採用イベントを観測した結果ではない。保存方式のmin(J_candidate,J_initial)とも異なる。旧Aの時間窓あり政策結果はBの運用成果へ転用しない。'),heading('4.6　支持・取得・時間の証拠'),para('matching-chain独立DPは全460入力でmirror支持内最良値=初期解を示した。主greedy≤初期解も全件で確認したため、この指定支持ではgreedyより良い候補が存在しない。これは取得失敗より前の条件Aの不成立であり、全順列や量子一般には及ばない。activeの3点gridが全件t=0を選択した事実を、active全支持最小の証明へ拡張しない。[S5-P1-A]'),para('全順列については、主greedyより小さい採用最適参照が176入力であり、うち135は再検算DP/独立有理双対による証拠、41は保存MIP等値の条件付き証拠である。238入力はgreedyと採用参照が等しく、46入力のJ*は未証明である。候補存在の確認と有限予算での取得を分け、未証明を候補不存在として扱わない。'),para('既存診断3入力の9,312fit/93,120測定では、R1_020 full/基底/graphの最適取得p1=58/97、p2=78/97であった（Wilson95% 49.8〜69.0%、71.4〜87.1%）。当該診断のgreedyは最適であり、最適取得率の差はgreedy超えではない。旧10測定と97独立学習を混ぜず、区間の比較だけで設定差の有意性を認定しない。'),para('CPU工程記録9,603における固定4顧客FULL/UNIFORM/PROJECTOR/p2例の中央値はQAOA34.643ms、脱位相35.014msである。greedy12.142msは1出力、前2者は学習と10測定を含むため、公平な1計画時間比とはしない。全工程τ_totalとH_plan、転送/QPU資源は未同定であり、τ_total≤H_planと実採用・成果への反映はHOLDである。')]
replace('4　配送経路計算の分析結果','5　電池材料・車両の分析結果',e)
# Add T07 scientific roles explicitly in chapter5 without dropping conditional old reference examples.
append_before('5.4  T09：設計構造への補完',[para('T07の数値status=PASSはscientific_adoption=ALL_HOLD、practical_qualification=NOT_EVALUATEDと併存する。T08の数値PASSも実用材料入力の採用を意味しない。パック差を車両質量差へ1対1で伝えるには、他車体・積載・補強/換装部材・運転者を固定する必要がある。これらが変わる場合は車両会計へ追加する。Step4の科学判断を優先する。[S5-P2-01/02]')])
# Chapter6.
e=[heading('6.1　品質差の集中と対照の意味'),para('平均+441.791秒に対して計画中央値が0秒であることは、悪化が全出力へ一様に生じたわけではないことを示す。入力平均中央値は7.474秒であり、典型値は集計単位に依存する。全体平均だけで方式を代表させず、設定・入力規模別の大きさを読む必要がある。Grover2設定への集中が強く、単一入力の外れ値だけで生じた結果ではない。'),para('6設定は古典初期解と同じでも、greedyが初期を改善した入力では差が残る。初期差だけを改善とする評価は主対照への寄与を過大評価し得る。古典と現行8設定の予算/出力規則が完全には一致しないため、観測差を量子性の固有効果へ帰属できない。'),heading('6.2　候補存在と取得能力'),para('mirrorのJ*_S=J_initial≥J_greedyは指定支持での改善候補不存在を意味する。支持内に解がない場合、同じ支持のshotsや角度探索を増やしてもgreedy超えは得られない。一方、全支持では少なくとも採用参照とgreedyを比較して候補が存在する入力があり、そこで取得できないことは別の問題である。'),para('Grover大規模の悪化の理由は単一に同定されていない。有限角度学習・測定、初期状態、支持、backend/精度、対照予算等を候補として残す。診断3入力の最適取得差は指定条件での取得過程を示すが、460入力の確率標本でもgreedy改善でもない。'),heading('6.3　時間差から配送成果への伝達'),para('帰庫差がΔJと一致しても、最終顧客完了差や顧客別時刻差は帰路・訪問順序に依存する。さらに期限を跨がなければ二値成果は変わらない。保存Bには最小7,435.748秒の帰庫余裕があり、品質差は共通上限遵守差へ変換されなかった。これは実配送定時率が不変だったという実測結果ではない。'),para('条件Cの計画締切、条件Dの採用、条件Eの成果反映を独立に検証する必要がある。H_planは配送開始前の計画時間枠であり、帰庫上限32,400秒とは別である。完全な取得時間と出発記録がないため、CPU fitのみで遅配や早着を推定しない。greedyfallbackで差が消えるのも政策の条件付き算術である。'),heading('6.4　材料能力から質量・DCへの伝達'),para('経路2の主結果は記号的感度と固定モデルの質量応答である。容量増が質量を減らすには利用率・電圧・負極・部材設計を含む条件が必要となる。同じ部材会計の削減bより会計外追加差δが大きければ符号が逆転する。δ=bは恒等式であり、研究の内容は会計境界と未知部材、どの物理条件でDCへ符号が伝わるかを確認した点にある。'),para('1000〜1250kgにおける正のDC感度は凍結軌跡・物理の限定結果である。回生、補機、勾配、荷重変動、設計変更等を加えた実車で同じ効果量が成立するとはいえない。T09の面積/担持方針とNULLのBOMは、容量値から完成pack差を直接確定できないことを示す。Chen逆算入力は原報告/算術が確認済みでも実用full-cell適格性がHOLDであり、具体削減率を主結果へ戻さない。'),heading('6.5　二経路の共通点と証拠の非対称性'),para('両経路とも、上流能力の存在だけから運用成果の方向と大きさは同定できない。経路1では主対照・支持・取得・時間・採用・期限余裕、経路2では利用率/電圧・部材会計・車両換装・走行物理という具体的接続が必要となる。共通する矢印構造そのものを新規性としない。')]
comp=pd.read_csv(D/'CROSS_PATH_COMPARISON.csv');e+=table('表6-1　二経路の評価範囲',['比較軸','経路1','経路2'],comp[['axis','path1','path2']].values.tolist())
e+=[para('経路1は量子アルゴリズムのCPU模擬を実行した出力比較である。経路2は上流の量子材料改善を実行せず、設計入力以降の下流モデルを評価している。QPU実用段階と実材料成熟度の達成を証明せず、同じ証拠強度・同じ量子効果率としない。','Caption'),heading('6.6　学術的貢献と既存研究との差'),para('Hadfield [OR03]、Bärtschi/Eidenbenz [OR02]、Palackal [OR36]には支持・状態準備・解品質に関する先行議論がある。本研究の実証的追加は、指定cohortの36,800出力の秒/%分布、460入力のばらつきと影響診断、支持不存在との対応である。保存best可行性とraw-shot可行性、最適取得とgreedy超えを分けた証拠対応が方法的特徴である。'),para('Davis/Figliozzi [L14]やFASTSim [S5-L01]は既に車両性能と運用を接続する。本研究は統合の最初の例とはしない。材料側では連続感度と部材会計・凍結DCへの伝達範囲を、入力適格性から切り分けた。これらは既存の統計・物理・会計概念を対象事例へ適用し、過大な効果帰属を防ぐ限定的貢献である。'),para('理論的示唆は、技術評価の成功を単一の上流性能で置かず、比較基準と媒介条件を明示する必要があるという本事例からの解釈である。GeelsやSchot/Steinmuellerの社会技術的視点と接点を持つが、制度・市場・組織・受容の因果効果や社会技術転換一般の法則を実証したとはいえない。'),heading('6.7　研究限界と残る検証'),para('Bの入力は無作為需要標本ではなく25group・26親から派生する。10測定で学習安定性は推定できない。旧設定間の計算予算・出力規則・backend差を統制せず、規模のみの因果効果を識別していない。最適参照46未証明、41の外部証明、H_plan、QPU/総時間はHOLDである。'),para('材料側は実用full-cell入力、電極/セルの適格性、未知BOM、完成pack、量子計算→実材料、実車DCを未検証とする。モデルの算術PASSを科学的入力採用へ変換しない。道路受入FAILとT09_ROW183対向FAILは維持する。B問題とC軌跡の件数が同じでも同一入力と仮定しない。'),para('旧Papachristos引用原意図と未確認保存引用、Microsoft Word実機、大学提出体裁・目次/引用・相互参照の最終仕上げは残る。付録Bは旧主張の再採用ではなく原内容保全であり、現行の結論と分離する。今後の優先検証は、同予算主対照、完全工程時間と実計画締切、契約期限を持つ実採用/実道路、材料/セル/BOMと実車端子電力量の独立対応である。')]
replace('6　統合考察','7　結論',e)
# Conclusion answers all RQ explicitly.
e=[para('本研究は、量子技術の能力がEV配送の成果へ結び付く条件を二経路で評価した。RQ0に対しては、同一入力の主対照、入力内反復と親/group依存、数値整合と科学的採用、CPU模擬と実機、主モデルと参考シナリオを分ける評価手順を示した。'),para('RQ1に対して、保存B36,800計画のΔJ平均は+441.791秒、平均相対差は+22.244%、全計画中央値は0秒、460入力平均の中央値は+7.474秒であった。差はGroverと大規模層へ集中した。mirror支持では全460入力に主greedyより良い候補がないことを確認し、候補存在と取得失敗を区別した。固定条件の帰庫差はΔJと一致したが、最終顧客完了差は別であった。保存Bの大きな余裕の下で共通上限遵守差は0ポイントであり、契約定時率・実採用・取得時間による出発効果は回答できていない。'),para('RQ2に対して、正の定義域と同一部材会計の下での質量感度、追加部材による相殺・逆転、固定軌跡でのDCへの伝達条件を示した。材料入力を用いない460対応軌跡×2Crrでは、1000〜1250kgで質量感度が正であり、1000kg右微分平均は2.368/2.432Wh/kgであった。Chen逆算入力の実用適格性、完成pack・実車・量子由来の材料改善は未検証であり、具体的材料効果として結論しない。'),para('RQIに対して、技術能力とシステム成果の間には、比較基準・中間変換・採用/運用条件を確定する必要があると、対象事例の証拠に基づいて回答した。経路1は実行済みCPU模擬出力、経路2は上流を未実証とする下流モデルであり、共通構造だけを新規性とせず証拠非対称性を保持した。'),para('本研究の到達点は、指定条件における解品質差の大きさと分布、支持の制約、質量/DC伝達範囲と未接続箇所を追跡可能に示したことである。QPU優位、一般的量子不可能性、実配送/実車の改善、社会技術転換一般への因果効果は主張しない。残る科学的HOLDと提出体裁を含め、最終提出の無条件完了とは判定しない。')]
replace('7　結論','参考文献',e)
# Add the one new bibliographic item, preserving inherited records and existing HOLD classification.
append_before('書誌確認に限定した保存引用',[para('[S5-L01] Brooker, A.; Gonder, J.; Wang, L.; Wood, E.; Lopp, S.; Ramroth, L. (2015). FASTSim: A Model to Estimate Vehicle Efficiency, Cost and Performance. SAE Technical Paper 2015-01-0973. https://doi.org/10.4271/2015-01-0973 （原著p1要旨/概略を確認。公開原著：https://www.nrel.gov/docs/fy15osti/63623.pdf）')])
# Unique same-author/year labels in current bibliography, unaltered archive.
for p in doc.paragraphs:
 if p._p is archive:break
 if p.text.startswith('[OR24;'):p.text=p.text.replace('(2008)','(2008b)')
 if p.text.startswith('[OR30;'):p.text=p.text.replace('(2008)','(2008a)')
# Add self-contained trace and extra tables before historical appendix.
e=[heading('A.1　Step5再集計と根拠対応',2),para('本改訂の元データ対応は電子付録evidence/CLAIM_EVIDENCE_MAP.csvである。data/B_PLAN_GAPS_36800.csvは候補/greedy分数・差・相対差・seed・source hash・時刻を持つ。data/GAP_DESCRIPTIVE_STATISTICS.csvは全計画/入力/設定/rep/入力×設定の全記述統計、INPUT_UNIT_STATISTICS.csvは460入力単位、SEED_MAPPING_36800.csvは入力/設定固有entropyを持つ。相対pathは本Step5ディレクトリを起点とする。'),para('既存S3-IDと旧電子資料のpathはreview_outputs/quantum_ev_step3_synthesis_trial_20261104_174309、Step4のdata/文献/保全対応はreview_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043を起点とする。旧ALGORITHM_PROTOCOL_APPENDIX.md/ALGORITHM_SOURCE_SNAPSHOTS.csvはreview_outputs/thesis_results_interpretation_20261102/run01にある。保存付録の旧定義/値を現行差へ無変換で引用しない。'),heading('A.2　経路1の条件と未検証事項',2)]
conds=pd.read_csv(D/'PATHWAY1_CONDITIONS.csv');e+=table('表A-4　A〜Eの接続条件',['条件','証拠と範囲','未検証'],[[x.condition,x.scope_and_judgment,x.unresolved] for x in conds.itertuples()])
e+=[heading('A.3　改訂監査の範囲',2),para('Git/主要成果物の開始hash、解析入力hash、全件数値検算、モデル検算、DOCX/PDF表示、出典/主張対応を記録した。同一エージェント内の分離した工程であり、第三者学術査読ではない。最終監査はSTEP5_CLAIM_EVIDENCE_AUDIT.mdを参照する。図表/式が保全されていることは旧主張の科学的再採用を意味しない。')]
append_before(archive_title,e)
# Running headers and footer distinguish revision from archived original labels.
for sec in doc.sections:
 for p in sec.header.paragraphs:
  if 'Step4' in p.text:p.text='KMD修士研究　Step5改訂稿｜科学的保留を明記'
 for p in sec.footer.paragraphs:
  for r in p.runs:r.text=r.text.replace('Step4 trial','Step5 revised')
# Tables fit within page; consistent current text size and spacing retained.
for x in body.xpath('.//wp:docPr'):
 pass
for i,x in enumerate(body.xpath('.//wp:docPr'),1):x.set('id',str(i))
# Confirm archive block text/OMML/images weren't removed; formatting IDs can change.
def signature(els):
 return [dict(text=txt(e),math=len(e.xpath('.//m:oMath')),drawings=len(e.xpath('.//w:drawing'))) for e in els if etree.QName(e).localname!='sectPr']
base=Document(S4/'THESIS_STEP4_INTEGRATED_TRIAL.docx');bl=list(base._element.body);ai=next(i for i,e in enumerate(bl) if txt(e)==archive_title and e.xpath('./w:pPr/w:pStyle/@w:val')==['Heading1']);current=list(body);bi=current.index(archive)
assert signature(bl[ai:])==signature(current[bi:]),'archive changed'
(O/'evidence/ARCHIVE_RETENTION.json').write_text(json.dumps(dict(blocks=len(signature(bl[ai:])),text_math_drawing_signature_equal=True),indent=2))
doc.core_properties.title='量子技術がEV配送システムに寄与する条件の検討：Step5改訂版';doc.core_properties.subject='解品質差の定量評価と科学的採用判断の統合';doc.save(O/'THESIS_STEP5_REVISED.docx')
pd.DataFrame(changes).to_csv(O/'evidence/THESIS_CHANGELOG.csv',index=False);pd.DataFrame(figs).to_csv(O/'evidence/NEW_FIGURE_REGISTER.csv',index=False)
(O/'evidence/NEW_TABLE_REGISTER.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2))
print('new thesis',len(doc.paragraphs),'paragraphs',len(doc.tables),'tables',len(figs),'new figures')
