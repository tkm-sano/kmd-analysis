"""Create a 12-slide editable deck using only the first slide's design vocabulary."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
import json,csv,math
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.xmlchemy import OxmlElement

O=Path(__file__).resolve().parent;R=O.parents[2]
SRC=R/'研究紹介_佐野巧馬.pptx'
DEST=O/'研究紹介_佐野巧馬_佐藤先生相談用_改訂12枚.pptx'
P=Presentation(SRC)
N,T,V,G,F,K,W='002060','087E88','6A5794','808080','F2F2F2','000000','FFFFFF'
FONT='Noto Sans JP'
B=json.loads((O/'data/B_summary.json').read_text());C=json.loads((O/'data/C_summary.json').read_text())
low,high=C['CRR_LOWER_BOUND'],C['CRR_UPPER_BOUND']
with (O/'data/C_trajectory_model_results.csv').open() as f:points=list(csv.DictReader(f))
sources={
 'B1':'review_outputs/quantum_ev_step5_20261105/data/B_PLAN_GAPS_36800.csv',
 'B2':'review_outputs/quantum_ev_step5_20261105/data/B_INPUT_CONDITIONS_460.csv',
 'B3':'review_outputs/quantum_ev_step5_20261105/STEP5_PATHWAY1_CONDITIONS.md',
 'C1':'review_outputs/quantum_ev_step5_20261105/data/DC_MASS_KERNEL_INDEPENDENT.csv',
 'C2':'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json',
 'C3':'output/slides/sato_revision_20261105/data/C_trajectory_model_results.csv',
 'M1':'review_outputs/quantum_ev_step5_20261105/STEP5_PATHWAY2_EVIDENCE.md',
 'M2':'review_outputs/t08_t09_final_adoption_20261105/FINAL_REPORT_JA.md',
 'A1':'review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654/STEP4_EVIDENCE_DECISIONS.md',
 'A2':'review_outputs/quantum_ev_step5_20261105/THESIS_FULL_TEXT.md',
 'A3':'docs/research/RESEARCH_DESIGN_SUMMARY.md'}
register=[];geoms=[]
def tx(s,x,y,w,h,st,sz=12,color=K,bold=False,align=PP_ALIGN.LEFT):
 z=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=z.text_frame;tf.clear();tf.word_wrap=True
 tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
 for i,line in enumerate(str(st).split('\n')):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.alignment=align;p.line_spacing=Pt(20.5 if sz==14 else sz+3.2);p.space_after=Pt(0);p.space_before=Pt(0)
  run=p.add_run();run.text=line;run.font.name=FONT;run.font.size=Pt(sz);run.font.bold=bold;run.font.color.rgb=RGBColor.from_string(color)
  rp=run._r.get_or_add_rPr();rp.set('lang','ja-JP')
  for tag in ['a:ea','a:cs']:
   e=OxmlElement(tag);e.set('typeface',FONT);rp.append(e)
 geoms.append(dict(slide=len(P.slides),shape=z.shape_id,x=x,y=y,w=w,h=h,text=str(st),size=sz))
 return z
def rect(s,x,y,w,h,fill=F,round=True,line=None):
 z=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
 if round:z.adjustments[0]=.055
 z.fill.solid();z.fill.fore_color.rgb=RGBColor.from_string(fill);z.line.fill.background();z._element.spPr.append(OxmlElement('a:effectLst'))
 if line:z.line.color.rgb=RGBColor.from_string(line);z.line.width=Pt(.7)
 return z
def line(s,x1,y1,x2,y2,color=K,width=.8,dash=False,arrow=False):
 z=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2));z.line.color.rgb=RGBColor.from_string(color);z.line.width=Pt(width)
 if dash:z.line.dash_style=MSO_LINE_DASH_STYLE.DASH
 if arrow:
  e=OxmlElement('a:tailEnd');e.set('type','triangle');e.set('w','sm');e.set('len','sm');z._element.spPr.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ln').append(e)
 return z
def badge(s,n,x,y,color=N):
 rect(s,x,y,.30,.30,color);tx(s,x,y-.015,.30,.30,n,12,W,True,PP_ALIGN.CENTER)
def card(s,x,y,w,h,head,body,color=N,size=12):
 rect(s,x,y,w,h);tx(s,x+.18,y+.14,w-.36,.38,head,14,color,True);tx(s,x+.18,y+.68,w-.36,h-.78,body,size)
def base(title,subtitle,section,refs,minutes,notes=''):
 s=P.slides.add_slide(P.slide_layouts[6]);tx(s,.47,.14,12.4,.43,title,16,N,True)
 tx(s,.47,.70,12.4,.48,subtitle,12);tx(s,.47,1.24,12.4,.28,section,12,N,True)
 tx(s,.47,7.08,11.8,.25,'出典：'+'・'.join(refs)+'　｜　出典一覧・集計条件は発表者ノートと監査報告に記載',10,G)
 tx(s,12.15,7.08,.70,.25,f'{len(P.slides):02d} / 12',10,G,False,PP_ALIGN.RIGHT)
 ns=s.notes_slide
 if ns.notes_text_frame is None:
  a=Presentation();ns.shapes._spTree.append(deepcopy(a.slides.add_slide(a.slide_layouts[6]).notes_slide.notes_placeholder._element))
 ns.notes_text_frame.text=f'目安時間：{minutes}分。全50分。\n{notes}\n【出典】\n'+'\n'.join(f'{r}: {R/sources[r]}' for r in refs)
 register.append(dict(slide=len(P.slides),title=title,minutes=minutes,refs=refs,notes=notes))
 return s
def foot(s,head,body,color=N):
 rect(s,.47,6.20,12.4,.69);tx(s,.66,6.35,1.75,.32,head,12,color,True);tx(s,2.40,6.34,10.24,.42,body,12)
def table(s,x,y,widths,headers,rows,rh=.75,fs=12,color=N):
 for j,h in enumerate(headers):
  xx=x+sum(widths[:j])+.055*j;rect(s,xx,y,widths[j],.40,G);tx(s,xx+.12,y+.055,widths[j]-.24,.29,h,12,W,True)
 for i,row in enumerate(rows):
  yy=y+.49+i*rh
  for j,value in enumerate(row):
   xx=x+sum(widths[:j])+.055*j;rect(s,xx,yy,widths[j],rh-.065)
   tx(s,xx+.12,yy+.105,widths[j]-.24,rh-.15,value,fs,color if j==0 else K,j==0)
def node(s,x,y,w,h,label,color=K,fill=F):
 rect(s,x,y,w,h,fill);tx(s,x+.10,y+.16,w-.20,h-.20,label,12,color,True,PP_ALIGN.CENTER)
def scatter(s,x,y,w,h,field,xlabel,xticks,xmax,title):
 tx(s,x,y,w,.33,title,12,T,True)
 px,py,pw,ph=x+.48,y+.63,w-.66,h-1.18
 line(s,px,py,px,py+ph);line(s,px,py+ph,px+pw,py+ph)
 for val in [0,2,4,6]:
  yy=py+ph*(1-val/7);line(s,px,yy,px+pw,yy,G,.35);tx(s,x-.04,yy-.12,.45,.25,str(val),10,K,False,PP_ALIGN.RIGHT)
 tx(s,x+.02,y+.33,w-.05,.25,'電力量［kWh］',10)
 for val in xticks:
  xx=px+pw*val/xmax;line(s,xx,py+ph,xx,py+ph+.04);tx(s,xx-.24,py+ph+.10,.48,.25,str(val),10,K,False,PP_ALIGN.CENTER)
 tx(s,x+.35,py+ph+.43,w-.45,.30,xlabel,10,K,False,PP_ALIGN.CENTER)
 for p in points:
  if p['rolling_case']!='CRR_LOWER_BOUND':continue
  xv=float(p[field]);xv=xv/60 if field=='moving_duration_s' else xv
  yy=float(p['DC_1000_Wh'])/1000
  z=s.shapes.add_shape(MSO_SHAPE.OVAL,Inches(px+pw*xv/xmax-.014),Inches(py+ph*(1-yy/7)-.014),Inches(.028),Inches(.028));z.fill.solid();z.fill.fore_color.rgb=RGBColor.from_string(T);z.line.fill.background()

# 02: purpose and evidence-bounded contribution
s=base('研究目的と学術的な問い','量子技術の能力が配送成果に寄与するための条件を、保存計算と明示したモデルの範囲で検討する。','研究課題と、現時点で示せる貢献',['A1','A2','A3'],2)
rect(s,.47,1.72,12.4,1.09);tx(s,.68,1.91,11.98,.73,'量子技術の計算能力または材料性能への寄与は、どのような条件を介して、\n定時配達率および走行時のバッテリー消費電力量に反映されるのか。',14,N,True)
card(s,.47,3.08,4.0,2.65,'因果接続の明示','計画の取得・採用・実行と、\n材料・部材・車両質量を分離。\n未接続の区間を根拠と対応させる。')
card(s,4.67,3.08,4.0,2.65,'成立・消失条件の評価','指定した候補集合での改善余地、\n期限余裕、質量差の相殺を検討。\n成立条件は計算の対象範囲に限る。')
card(s,8.87,3.08,4.0,2.65,'証拠の範囲の明確化','入力・反復・比較基準を区別。\n量子模擬の解品質比較と、\n下流の物理モデルを混同しない。')
foot(s,'貢献の位置付け','対象事例の条件評価・証拠対応である。一般法則の発見や量子優位性の実証は主張しない。')

# 03: causal hypotheses and computational links are deliberately distinguished.
s=base('2つの技術経路と、3つの評価工程','図は作用仮説と評価の接続を表す。計算工程の照合を、実世界の因果効果の同定とは扱わない。','技術経路A：配送計画の取得能力　／　技術経路B：電池材料の性能改善可能性',['A1','A2','B3','M1'],3)
for x,cc,ds,lab in [(.55,N,False,'保存計算で確認'),(4.42,T,False,'モデル仮定下の計算'),(8.55,G,True,'未検証の接続')]:
 line(s,x,1.86,x+.48,1.86,cc,1.2,ds,True);tx(s,x+.58,1.73,3.50,.30,lab,12,cc)
node(s,.47,2.30,2.45,.84,'量子最適化アルゴリズム\nCPU模擬',N)
node(s,3.37,2.30,2.10,.84,'配送計画の取得\n保存候補の比較',N)
node(s,5.92,2.30,2.20,.84,'計画の採用・実行\n実運用は未検証',G)
node(s,8.57,2.30,1.80,.84,'訪問順序',K)
line(s,2.93,2.72,3.30,2.72,N,1.2,False,True);line(s,5.49,2.72,5.85,2.72,G,1.2,True,True);line(s,8.14,2.72,8.50,2.72,G,1.2,True,True)
node(s,10.82,2.06,2.05,.84,'① 配達完了時刻\n→ 定時配達率',N)
node(s,10.82,3.12,2.05,.84,'② 走行状態\n→ 消費電力量',T)
line(s,10.39,2.69,10.75,2.48,T,1.1,False,True);line(s,10.39,2.78,10.75,3.46,T,1.1,False,True)
tx(s,.65,3.45,9.6,.55,'①は期限判定のモデル。②は計画の差を電力量へ接続する評価工程である。\n①の契約期限評価、B系列から②への軌跡生成・一貫比較は未完了である。',12)
node(s,.47,4.35,2.45,.94,'量子計算による\n材料物性の予測',V)
node(s,3.37,4.35,2.10,.94,'実材料の\n性能改善可能性',V)
node(s,5.92,4.35,2.20,.94,'実用セル・\nパック設計',V)
node(s,8.57,4.35,1.80,.94,'③ 車両質量',V)
node(s,10.82,4.35,2.05,.94,'走行時の\n消費電力量',V)
for a,b in [(2.93,3.30),(5.49,5.85)]:line(s,a,4.82,b,4.82,G,1.2,True,True)
line(s,8.14,4.82,8.50,4.82,T,1.1,False,True);line(s,10.39,4.82,10.75,4.82,T,1.1,False,True)
tx(s,.65,5.51,11.9,.36,'③は仮定した設計入力以降を計算する。実材料・完成パックへの採用は確認されていない。',12,V)
foot(s,'番号の対応','①・②・③は第1枚目と同じ。技術経路Aは①と②、技術経路Bは③に対応する。')

# 04: exact adopted conditions and different input series
s=base('大田区の配送モデルと実験条件','東京都大田区・単一デポを想定する。需要と訪問対象は研究用に構成され、実注文の観測値ではない。','B系列：配送計画比較　／　C系列：保存走行軌跡の電力量評価',['A2','B2','C1','C2'],3,
'B系列のready=0は時間原点であり時計時刻ではない。容量216PE。需要は合成需要。原道路は動的受入未成立で、固定OD費用表としての比較である。C系列には旧設定の停車が含まれ、Bの時間窓なし条件を転用しない。')
table(s,.47,1.71,[2.23,5.00,5.06],['比較条件','B系列：訪問順序の比較','C系列：保存軌跡の再評価'],[
 ['入力と割当','460入力、3・4・5・25・100・125顧客。\n顧客集合・需要・車両割当・容量を入力ごとに固定。','460保存軌跡を同一条件で再評価。\nB系列との入力対応は未確認。'],
 ['開始・作業時間','開始原点0秒、顧客作業102秒。\n実際の時計時刻・出発遅延は未同定。','保存された1秒刻みの速度時系列を固定。\n停車を含む観測区間と移動時間を区別。'],
 ['期限とサービス','顧客固有の時間窓なし。\n共通上限・デポ帰庫期限32,400秒。','旧設定の保存軌跡である。\nB系列の期限条件を移植しない。'],
 ['交通・運用・車両','配送途中の充電・車両間再割当は扱わない。\n道路の妥当性・実採用には残課題。','背景交通なし、平坦・空荷。\n回生・補機・旋回損失を除外。']],rh=.95)
foot(s,'比較の原則','①は同じ入力の計画比較。②・③は同じ軌跡の物理計算。BとCを直接結合しない。')

# 05: absolute B differences, scale and setting differences.
s=base('① 配送計画：旅行時間差の大きさと分布','ΔJ ＝ 候補計画の旅行時間 − 主greedy計画の旅行時間。正は悪化、負は改善である。','460入力 × 8設定 × 10測定 ＝ 36,800保存計画（CPU模擬）',['B1','B2','A1'],4,
'Jはデポ帰還を含む有向OD旅行時間の和で、作業時間は含まない。グラフは入力ごとの10測定平均を規模内で等重みに集計。その他6設定は全規模で平均が一致する。8設定の合成平均を単一アルゴリズムの効果量にしない。標準偏差はddof=1。')
vals=[('平均',f'+{B["all_outputs"]["mean"]:,.1f} 秒'),('中央値','0.0 秒'),('最小〜最大','0.0〜9,484.0 秒'),('標準偏差','1,459.4 秒')]
for i,(a,b) in enumerate(vals):
 x=.47+3.13*i;rect(s,x,1.72,3.0,.85);tx(s,x+.13,1.82,2.74,.26,a,12,N,True);tx(s,x+.13,2.16,2.74,.28,b,14,N,True)
tx(s,.55,2.79,6.7,.32,'規模別の平均旅行時間差［秒］',12,N,True)
px,py,pw,ph=1.00,3.38,5.35,1.85
line(s,px,py,px,py+ph);line(s,px,py+ph,px+pw,py+ph)
for tick in [0,3000,6000]:
 yy=py+ph*(1-tick/6500);line(s,px,yy,px+pw,yy,G,.35);tx(s,.49,yy-.11,.44,.25,f'{tick:,}',10,K,False,PP_ALIGN.RIGHT)
for j,sc in enumerate(['R0','R1','R2','R3','R4','R5']):
 xx=px+(j+.5)*pw/6
 for off,config,cc in [(-.15,'GROVER_P2',N),(.03,'GROVER_P3',G)]:
  val=next(r['mean'] for r in B['scale_settings'] if r['scale']==sc and r['config_id']==config)
  rect(s,xx+off,py+ph*(1-val/6500),.16,max(.012,ph*val/6500),cc,False)
 tx(s,xx-.38,5.37,.76,.26,str([3,4,5,25,100,125][j]),10,K,False,PP_ALIGN.CENTER)
tx(s,1.04,5.73,5.5,.25,'顧客数　　■ Grover p＝2（濃紺）　■ p＝3（灰色）',10)
table(s,6.88,2.85,[2.36,1.54,1.54],['設定','平均差［秒］','最大差［秒］'],[
 ['Grover p＝2','+1,766.0','9,484.0'],['Grover p＝3','+1,762.0','9,449.6'],['その他6設定','+1.0','44.5']],rh=.62,fs=12)
tx(s,6.99,5.40,5.72,.53,'改善0件／同等28,200件／悪化8,600件。\n入力平均の中央値7.5秒、入力間SD622.3秒。',12)
foot(s,'統計単位','36,800件は独立標本ではない。460入力にも25需要群・26親入力の依存が残る。')

# 06: three necessary stages and threshold outcomes.
s=base('① 改善解の存在・取得・採用を分ける','旅行時間が変わっても、期限余裕の範囲内なら二値の期限判定は変わらない。','計画の解品質と、配送サービスへの反映条件',['B1','B3','A1'],3,
'指定matching支持内最小＝初期解、greedy≦初期解を460入力で確認。全順列・他支持への一般化不可。共通上限内割合100%は契約定時率ではない。最終顧客完了が早い180件も主旅行時間改善を意味しない。')
card(s,.47,1.74,4.0,2.39,'1. 改善解が存在するか','指定したmatching候補集合では、\n全460入力で集合内最小＝初期解。\n主greedyを上回る候補は存在しない。')
card(s,4.67,1.74,4.0,2.39,'2. 改善解を取得できるか','存在しても有限の学習・測定で\n得られるとは限らない。\n10測定は10回の独立学習ではない。')
card(s,8.87,1.74,4.0,2.39,'3. 採用・実行できるか','計画締切、検証、共有、出発が必要。\n全工程時間と実採用は未同定。\n現行対照との予算・出力規則差も残る。')
table(s,.47,4.42,[4.03,4.04,4.22],['帰庫時刻の差','最終顧客の配達完了時刻','定時配達率との違い'],[
 ['帰庫差＝ΔJ。\n候補の最小帰庫余裕7,435.7秒。','差はΔJ−最終帰路の差。\n旅行時間非改善でも180件は早く完了。','共通上限遵守は両側100%。\n契約期限による定時配達率は未検証。']],rh=1.05)
foot(s,'次に必要な評価','顧客別の完了時刻差と期限余裕を照合し、計画採用・出発遅延を含む成立条件を確認する。')

# 07: full energy boundary and exact model.
s=base('② 走行時のバッテリー消費電力量の評価方法','本資料で「走行時DC電力量」は、電池側の駆動電力量を表す。現行条件では回生・補機を含まない。','同じ速度時系列に、凍結した走行仕事モデルを適用する',['C1','C2','C3'],3,
'W(t)は区間機械仕事[J]。mは運転者を含む走行質量[kg]、vは速度[m/s]、Δsは区間距離[m]。g=9.80665m/s²、ρ=1.2041kg/m³、CdA=1.175m²、回転等価質量=61kg、駆動効率0.9。負の合計機械仕事は回生にせず駆動電力量0とする。補機は未評価であり、実物の補機消費が物理的に0という意味ではない。観測末端の未知区間は除外しゼロ補完しない。')
rect(s,.47,1.73,12.4,1.46)
tx(s,.68,1.92,11.96,.42,'W(t)＝m g Crr(v(t)) Δs(t)＋½ρCdA v(t)² Δs(t)＋½(m＋61){v(t)²−v(t−1)²}',14,T,True)
tx(s,.68,2.52,11.96,.39,'E_DC［Wh］＝Σ max(W(t), 0) ÷ (3,600 × 0.9)　　Δs(t)＝v(t) Δt、Δt＝1秒',14,T,True)
card(s,.47,3.46,6.10,2.30,'計算する項目','転がり抵抗、空気抵抗、並進・回転の加減速。\n走行質量mは運転者を含む。回転等価質量61kg。\n区間末の速度で抵抗と距離を評価する。',T)
card(s,6.77,3.46,6.10,2.30,'負の仕事と除外項目','合計機械仕事W(t)を区間ごとに正値化する。\n負の仕事は電池へ回収しない（回生なし）。\n平坦・積載0kg、補機・旋回損失を除外。',T)
foot(s,'抵抗条件','Crr＝0.005＋{0.01＋0.0095(v［km/h］/100)²}/p。p＝4.5／2.6 barの2条件。',T)

# 08: descriptive C results at material-independent mass.
s=base('② 保存軌跡の電力量：距離・移動時間・加減速','460軌跡を比較用の仮想走行質量1,000kgで再評価した。B系列の候補計画を走行させた結果ではない。','点は保存軌跡。転がり抵抗下限条件。有限集合の記述であり、因果効果は同定しない。',['C1','C2','C3'],4,
'移動時間は区間末速度v>0.1m/sの区間秒数。観測時間は停車を含む。停止原因は配達停車・待機・交通要因に分離できない。Spearmanは距離0.992762、移動時間0.962769。p値・独立標本CIなし。成分は合計車輪仕事が正の区間の符号付き仕事を効率で割った会計的配分であり、独立の因果寄与ではない。')
scatter(s,.53,1.75,4.10,3.39,'distance_km','走行距離［km］',[0,10,20,30,40],45,'距離と電力量（順位相関0.993）')
scatter(s,4.82,1.75,4.10,3.39,'moving_duration_s','移動時間［分、v＞0.1m/s］',[0,30,60,90],110,'移動時間と電力量（順位相関0.963）')
table(s,9.13,1.77,[1.63,1.97],['指標','下限条件'],[
 ['電力量 平均','2.799 kWh'],['中央値','2.420 kWh'],['範囲［kWh］','0.992〜6.248'],['距離 範囲','6.76〜41.01 km']],rh=.56,fs=12,color=T)
tx(s,9.23,4.72,3.5,.82,'同じ軌跡で上限抵抗に変更：\n平均＋67.7Wh（＋2.48%）。\n2条件は独立の走行実験ではない。',12)
rect(s,.47,5.40,12.4,.53)
tx(s,.65,5.51,12.0,.34,'駆動区間の仕事内訳（総和比）：転がり9.8%／空気10.8%／並進加減速74.8%／回転4.6%。',12,T)
foot(s,'解釈上の注意','停車には作業・待機等が含まれる。補機なしでは停車自体の電力量は算定されない。',T)

# 09: symbolic mass model, analytic sensitivity, and explicit stage distinction.
s=base('③ 材料性能からパック質量・車両質量への変換','量子計算による物性予測、実材料の改善、実用セル、完成パック、実車効果は別段階である。','T08：解析感度の主モデル　／　T09：面積・部材設計による構造依存の補完',['M1','M2','A1'],2)
rect(s,.47,1.74,12.4,1.09)
tx(s,.68,1.94,11.98,.40,'M_pack ＝ E_g / V × {1 / (q u f_p) ＋ r / (q_n f_n)} ＋ F ＋ D ＋ δ',14,V,True)
tx(s,.68,2.47,11.98,.28,'E_g：設計電力量　V：平均電圧　q・q_n：正負極比容量　u：利用率　f：活物質割合　r：N/P',10)
card(s,.47,3.10,6.10,2.66,'容量・電圧・利用率の感度','他条件固定なら、正極塗工材質量は1/(q u V)。\n比容量qのみ＋10%なら正極塗工材は−9.09%。\n完成パック全体の−9.09%を意味しない。\nF・D・δは重複しない部材会計である。',V)
card(s,6.77,3.10,6.10,2.66,'部材・車両への伝達条件','T09は担持量・空隙率・面積依存部材を扱う。\n未知の外装・タブ等はゼロで埋めない。\n車体・補強・積載を固定した置換条件では、\nパックの質量差＝車両の走行質量差である。',V)
foot(s,'入力の適格性','逆算容量の実用セルへの適格性は保留。量子由来の材料改善・完成パック性能は未実証。',V)

# 10: finite mass response, ranges and cancellation boundary.
s=base('③ 質量感度と、追加部材による相殺境界','同じ軌跡で1,000→1,100kgに変更した有限差分。実材料を入力しない凍結モデルの追加計算である。','質量増加100kg当たりの電力量差［Wh／保存軌跡］',['C1','C2','C3','M1','M2'],3)
table(s,.47,1.75,[2.04,1.53,1.53,1.53,1.53],['抵抗条件','平均','中央値','最小','最大'],[
 ['下限条件','＋236.9','＋195.7','＋82.8','＋546.9'],['上限条件','＋243.3','＋201.0','＋85.5','＋560.1']],rh=.73,color=V)
rect(s,9.05,1.75,3.82,2.39)
tx(s,9.23,1.92,3.46,.33,'軌跡で感度が異なる',14,V,True)
tx(s,9.23,2.54,3.46,1.30,'1,000kgでの平均局所感度：\n2.368／2.432 Wh/kg。\n100kg差は線形近似でなく\n同じ核で再計算した値である。',12)
tx(s,.65,4.00,7.9,.31,'軽量化量 ΔM＝b−δ　　δ＜b：削減／δ＝b：消失／δ＞b：逆転',12,V,True)
tx(s,.65,4.48,12.0,.65,'b：同じ部材会計内の削減量。δ：追加・未知部材の質量差。\n走行質量1,000〜1,250kgの検証範囲では、同じ軌跡・条件で質量差と電力量差の符号が一致する。',12)
rect(s,.47,5.36,12.4,.55)
tx(s,.65,5.47,12.0,.34,'入力未適格の参考例：相殺境界 b＝T08 5.448kg／T09既知部材 9.723kg・5.978kg。',12,V)
foot(s,'参考例の留保','T09の2値は固定担持／固定面積の設計差。完成パックの値・実材料の代表効果には採用しない。',V)

# 11: bounded contribution and A/B/C work classes.
s=base('確認された成果と、残る検証の扱い','保存計算・物理モデル・現実での実証を分け、追加検証の範囲を限定する。','主張できる成果と、研究として残す限界',['A1','A2','B3','M1'],2)
table(s,.47,1.75,[3.15,4.57,4.57],['区分','内容・現時点での成果','今後の扱い'],[
 ['確認済み・条件付き成果','Bの解品質分布と指定支持内の改善余地。\n期限余裕、固定軌跡の質量応答・相殺条件。','対象・仮定・比較基準を付して説明する。\n技術能力から成果への媒介条件が貢献。'],
 ['A 現研究で追加検証可能','入力・設定・反復別の再分析。\n期限感度、同一軌跡でのモデル感度。','優先指標と比較条件を事前に定める。\n計画取得とサービス成果を分けて評価。'],
 ['B 限定的な検証が可能','道路・交通条件の妥当性、適用範囲。\n計画締切・採用・出発への接続条件。','専門家助言と限定的な照合で確認。\nB→Cの入力対応と道路受入は未成立。'],
 ['C 本研究の対象外','量子由来の実材料改善、完成パック実証。\n量子実機優位性、実車での運用実証。','達成を主張しない研究限界である。\n不足値を仮定で埋めて効果を断定しない。']],rh=.95)
foot(s,'新規性の範囲','一般的な媒介概念・会計恒等式の新規発明ではなく、対象事例の条件評価と証拠対応である。')

# 12: specific answerable ITS questions, with assumptions and requested decisions.
s=base('佐藤先生に相談したい3つの論点','交通・ITSの観点から、比較の妥当な範囲と、次に検証すべき条件をご助言いただきたい。','現在の仮定 → 生じる不確実性 → 判断していただきたいこと',['A2','A3','C2'],18,
'50分配分：1枚目3分、2=2、3=3、4=3、5=4、6=3、7=3、8=4、9=2、10=3、11=2、12=18。合計50分。必要に応じ方法説明を短くし、質問ごとの議論時間を確保する。')
for y,head,body in [
 (1.73,'1. 交通モデルの妥当性',
 '仮定：背景交通なし・単独車両の保存SUMO軌跡である。\n不確実性：混雑・信号待ち・経路選択の変化を再現していない。\n判断：旅行時間・電力量の相対比較が使える配送条件と、最低限必要な妥当性確認は何か。'),
 (3.17,'2. 配送サービスの評価',
 '仮定：B系列は顧客時間窓なし、作業102秒、共通帰庫上限32,400秒である。\n不確実性：帰庫差と顧客別の完了差が異なり、契約定時配達率は未評価である。\n判断：訪問順序を定時配達率へ接続するため、最低限必要な期限・作業・採用条件は何か。'),
 (4.61,'3. 電力量モデルの精緻化',
 '仮定：平坦・空荷、回生・補機なし。保存軌跡を共通利用している。\n不確実性：交通量・信号停止・荷重変化・勾配・回生が経路順位を変える可能性がある。\n判断：経路間比較で優先的に検証すべき要因と、必要なデータ・指標は何か。')]:
 rect(s,.47,y,12.4,1.30);tx(s,.67,y+.12,11.98,.31,head,14,N,True);tx(s,.67,y+.55,11.98,.71,body,12)
foot(s,'本日の到達点','適用できる条件、優先する追加検証、最低限必要なデータを整理する。')

assert len(P.slides)==12
for ss in list(P.slides)[1:]:
 for sh in ss.shapes:
  for effect in sh._element.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}effectRef'):
   effect.set('idx','0')
P.core_properties.title='量子技術がEVラストワンマイル配送に与える影響｜佐藤先生相談用'
P.core_properties.author='佐野巧馬';P.core_properties.subject='12枚改訂・保存計算の学術監査・交通ITS研究相談'
P.save(DEST)
tmp=DEST.with_suffix('.tmp.pptx')
with ZipFile(SRC) as orig,ZipFile(DEST) as authored,ZipFile(tmp,'w',ZIP_DEFLATED) as final:
 for name in authored.namelist():
  preserve=(name in ['ppt/slides/slide1.xml','ppt/slides/_rels/slide1.xml.rels'] or name.startswith(('ppt/theme/','ppt/slideMasters/','ppt/slideLayouts/','ppt/media/')))
  final.writestr(name,orig.read(name) if preserve and name in orig.namelist() else authored.read(name))
tmp.replace(DEST)
(O/'evidence/slide_register.json').write_text(json.dumps(register,ensure_ascii=False,indent=2))
(O/'evidence/text_geometry.json').write_text(json.dumps(geoms,ensure_ascii=False,indent=2))
(O/'evidence/source_ids.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2))
print(DEST)
