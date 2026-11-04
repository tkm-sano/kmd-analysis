"""Reader-oriented A1: purpose -> two pathways -> methods/results -> interpretation."""
import json
from pathlib import Path
from poster_primitives import Poster,BLUE,ORANGE,NAVY,INK,MUTED,PALE,RULE
from content import TITLE,PURPOSE,RQ,REFS
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.ns import qn
R=Path(__file__).resolve().parents[1];audit=json.loads((R/'evidence/EXTENDED_AUDIT.json').read_text());p=Poster()
def tx(x,y,w,s,pt=24,b=False,c=INK,h=None):return p.text(x,y,w,s,pt,b,c,max_h=h)
def rect(x,y,w,h,fill=None,stroke=None,dash=False):
 p.rect(x,y,w,h,fill,stroke)
 shape=p.slide.shapes[-1];style=shape._element.find(qn('p:style'))
 if style is not None:shape._element.remove(style)
 if dash:
  shape.line.dash_style=MSO_LINE_DASH_STYLE.DASH
  # PDF rect already exists; overlay a white fill and dashed border for the design reference.
  p.pdf.setDash(4,3);p.pdf.setStrokeColorRGB(.45,.48,.51);p.pdf.rect(x*72/25.4,(841-y-h)*72/25.4,w*72/25.4,h*72/25.4,stroke=1,fill=0);p.pdf.setDash()
def arrow(x1,y,x2,c,dash=False):
 p.pdf.setDash(4,3) if dash else p.pdf.setDash()
 p.arrow(x1,y,x2,y,c);p.pdf.setDash()
 if dash:
  for shape in list(p.slide.shapes)[-3:]:shape.line.dash_style=MSO_LINE_DASH_STYLE.DASH

def sec(x,y,s,c):p.section(x,y,275,s,c)
# Title/author are unchanged. Each following section answers a distinct reader question.
tx(15,10,564,'量子計算がEV配送システムに寄与し得る条件：',48,True,NAVY,h=25)
tx(15,36,564,'配送計画と電池材料評価を介した影響経路の検討',40,True,NAVY,h=23)
tx(15,63,564,'佐野巧馬　｜　Q/est',27,c=MUTED,h=14)
p.line(15,82,579,82,NAVY,1.5)
tx(15,89,564,'1　何を明らかにする研究か',30,True,NAVY,h=15)
tx(15,108,564,'量子計算が、配送計画や電池設計を通じてEV配送に寄与するための条件と制約を調べる。保存された定量結果と文献を用い、計算から実用へ至る工程のうち、確認できた関係と未検証の接続を整理した。',24,h=33)
# A map before details. Filled nodes show analyses actually performed; operational links are dashed.
tx(15,145,564,'配送計画の経路：訪問順を探索し、使える配送計画へつなげる',23,True,BLUE,h=13)
xs=[15,159,303,447];ww=[132,132,132,132]
blue=[('量子探索モデル','CPUで数値評価',False),('候補経路の評価','移動時間・制約を確認',False),('運用での選択・統合','未検証',True),('実際の配送・走行電力量','未評価',True)]
brown=[('量子材料計算','材料の性質を評価（未実施）',True),('材料選択・電池設計','量子情報の利用は未検証',True),('電池・車両の質量','文献入力で推計',False),('走行電力量','同一保存速度で計算',False)]
for yy,items,col,fill in [(162,blue,BLUE,'#E9F1F7'),(220,brown,ORANGE,'#F7EEE7')]:
 for i,(title,body,dash) in enumerate(items):
  rect(xs[i],yy,132,31,None if dash else fill,col,dash)
  tx(xs[i]+3,yy+3,126,title,21,True,col,h=13)
  tx(xs[i]+3,yy+18,126,body,18,c=MUTED,h=11)
  if i<3:arrow(xs[i]+134,yy+15,xs[i+1]-3,col,items[i][2] or items[i+1][2])
tx(15,203,564,'電池材料の経路：材料の評価情報を設計へ反映し、質量・電力量へつなげる',23,True,ORANGE,h=13)
tx(15,257,564,'色付きは今回比較・計算した部分、破線は未検証の接続である。材料側の計算入力は文献の電極参照値である。',19,c=MUTED,h=19)
# Parallel columns use the same narrative order.
sec(15,282,'2　配送計画で何を比較したか',BLUE)
sec(304,282,'3　材料から何を計算したか',ORANGE)
tx(15,305,275,'古典計算で作った訪問順を「古典初期解」とし、そこから総移動時間を短縮できるかを調べた。時間窓は設けず、全訪問・容量・帰庫の制約を共通とした。',23,h=42)
tx(15,351,275,'3・4・5・25・100・125配送先、計460問題例を比較した。1問題例は、配送先と各地点間の移動時間行列の1組である。',23,h=33)
tx(15,386,275,'探索範囲は、固定した位置の対の交換5設定、隣接位置の交換1設定、全訪問順を候補とする理想状態のGM-QAOA 2設定 [1] である。全てCPUで数値評価した。',22,h=40)
tx(15,430,275,'比較結果：全訪問順を扱うGM-QAOA',25,True,BLUE,h=14)
# Preserve all absolute scale results; normalized figures remain in the supplement.
xx=[15,74,129];ws=[59,55,161]
for x,w,s in zip(xx,ws,['配送先数','例数','初期解からの変化［秒］']):p.cell(x,448,w,15,s,20,True,PALE)
for i,n in enumerate([3,4,5,25,100,125]):
 rows=[v for v in audit['normalized_scale_results'] if v['n']==n and v['config_id'].startswith('GROVER_')]
 lo,hi=sorted(v['mean_delta_s'] for v in rows)
 def f(v):return ('−' if v<0 else '+' if v>0 else '')+f'{abs(v):,.2f}'
 value=f(lo) if round(lo,2)==round(hi,2) else f(lo)+'〜'+f(hi)
 for x,w,s in zip(xx,ws,[str(n),str(rows[0]['inputs']),value]):p.cell(x,463+i*13,w,13,s,22,fill='#F4F8FB' if i%2==0 else None)
tx(15,544,275,'負は短縮、正は長くなったことを示す。各入力の10反復を平均後、入力間で平均した。幅は層数2・3の2設定の値であり、信頼区間ではない。',19,h=29)
tx(15,577,275,'短縮は4配送先1例・5配送先6例の計7例であった。25配送先以上では、平均移動時間が初期解より長くなった。',23,True,BLUE,h=33)
tx(15,614,275,'結果から言えること',25,True,BLUE,h=14)
tx(15,632,275,'位置の対の交換は範囲内最小値＝初期値で、改善解がなかった。隣接交換も今回の条件では初期解を選んだ。全訪問順でも大規模で平均悪化し、改善余地のある範囲と良い解の取得は別である。',22,h=40)
# Material inputs are explained before the two distinct models are used.
tx(304,305,275,'電極試料LPとS-200 [5] の参照値を入力例とし、材料特性の差が車両全体の質量・走行電力量へどの程度伝わるかを調べた。量子計算で改善した材料の比較ではない。',23,h=42)
tx(304,351,275,'① 容量を固定した簡略計算',25,True,ORANGE,h=14)
tx(304,369,275,'容量20 kWh・平均セル電圧3.5 Vで電極量を換算し、電極塗工層＋固定34 kgで電池質量を推計した。同一の旧460保存速度軌跡で、電池から取り出す走行電力量（DC）を計算した。',22,h=40)
tx(304,413,275,'入力の比容量（活物質1 kg当たりの電気容量）は171.9→196.0 Ah/kgである。保持率からの逆算値であり、初回全電池の実測値ではない。',19,h=29)
for i,(label,sub,rate,value) in enumerate([
 ('推計電池質量','96.15 → 90.70 kg',5.666712059409347,'5.67%'),
 ('走行時総質量','1140.03 → 1134.59 kg',.47790634461422765,'0.478%'),
 ('走行電力量','旧460軌跡の合計比',.412579010060621,'0.413%')]):
 y=448+i*29;tx(304,y,138,label,23,True,ORANGE,h=13);tx(304,y+13,138,sub,18,c=MUTED,h=11)
 rect(448,y+2,88*rate/6,9,ORANGE);tx(539,y-1,40,value,23,True,ORANGE,h=13)
p.line(448,533,536,533,MUTED)
for z in [0,2,4,6]:
 x=448+88*z/6;p.line(x,533,x,536,MUTED);tx(x-4,538,14,str(z),17,c=MUTED,h=9)
tx(470,549,69,'LP基準の削減率［%］',17,c=MUTED,h=11)
tx(304,564,275,'固定の車体・運転者を含めると、電池の差は総質量では小さくなる。電力量は同じ速度・平坦路の保存区間のみで計算した。回生・補機・荷重変化は除く。',20,h=36)
tx(304,600,275,'② 部材を個別に計上した設計分析',25,True,ORANGE,h=14)
tx(304,618,275,'部材質量が変わる設計を調べるため、電極・集電体・セパレータ・電解液を個別計上した183設計を分析した。完成パック質量は全件未確定である。',21,h=34)
tx(304,655,275,'代表する二つの設計条件では、既知部材だけの軽量化は5.98 kg／9.72 kgであった。質量収支上、未知部材が同じ分だけ重くなれば軽量化は消え、さらに増えれば逆転する。',21,h=40)
# Synthesis follows results, with a separate paragraph for the evidence boundary.
tx(15,701,564,'4　二つの分析から、量子計算の寄与をどう考えるか',29,True,NAVY,h=15)
tx(15,721,564,'配送では、古典側が範囲を選び、量子側が探索し、古典側が検証・統合する役割分担が検討課題となる [6]。材料では、計算情報を実用電池の設計へ利用できることが寄与の条件候補となる [2,7]。',23,h=23)
tx(15,749,564,'採用・全体統合、入力更新から採用判断までの時間条件、量子材料情報の有用性、完成パックの出力・寿命・安全性、実車の削減効果は未検証である。',19,c=MUTED,h=18)
tx(15,769,564,'技術と適用判断の区別 [4]、将来構成の予見・固定前提の省察 [3] を分析視点とした。詳細条件と監査結果は別添に示す。',17,c=MUTED,h=9)
p.line(15,782,579,782)
short=[
 '[1] Bärtschi & Eidenbenz (2020). IEEE QCE, 72–82.',
 '[2] Delgado et al. (2022). Phys. Rev. A 106, 032428.',
 '[3] Stilgoe et al. (2013). Res. Policy 42, 1568–1580.',
 '[4] Geels (2004). Res. Policy 33, 897–920.',
 '[5] Chen et al. (2020). Nat. Commun. 11, 3411.',
 '[6] Holliday et al. (2026). Quantum Mach. Intell. 8, 37.',
 '[7] Shokrian Zini et al. (2023). Quantum 7, 1049.'
]
for i,s in enumerate(short):tx(15 if i<4 else 304,788+(i if i<4 else i-4)*11,275,s,18,c=MUTED,h=11)
tx(304,821,275,'GM-QAOA：Grover-mixer QAOA [1]。実機性能・量子優位性は未実証である。',18,c=MUTED,h=11)
p.save(TITLE+'\n'+RQ+'\n'+PURPOSE+'\n\n本版は研究内容を工程順に説明する。本文の「保存結果」「解釈」「未検証」は、別添のA/B/C分類に対応する。\n詳細条件：各設定・入力で10測定反復、各8192標本の最良解。固定OD目的値はデポ発着の旅行時間和。厳密参照407、未証明53（100先21・125先32）。部材別の代表軽量化は面積固定5.977891152kg、担持量固定9.722608121kg。δは未知部材S−LP差、bは既知部材LP−S差、正味軽量化b−δ。回生・補機・勾配・荷重変化は対象外、運転者55kg・積載0、下側転がり係数、保存区間のみ。現在配送460入力と旧460速度は別系列。\n\n'+'\n'.join(f"[{v['n']}] {v['author']} ({v['year']}). {v['title']}. {v['journal']}. DOI: {v['doi']}\n利用範囲：{v['use']}" for v in REFS))
print('Built reader-oriented run05 poster')
