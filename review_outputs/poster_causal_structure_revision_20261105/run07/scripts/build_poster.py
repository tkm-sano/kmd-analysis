from poster_primitives import *
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from xml.sax.saxutils import escape
from content import TITLE
P=Poster();scene=[];edges=[]
def rect(x,y,w,h,fill=None,stroke=None):
 P.rect(x,y,w,h,fill,stroke);scene.append(('rect',dict(x=x,y=y,w=w,h=h,fill=fill or 'none',stroke=stroke or 'none')))
def txt(x,y,w,s,pt=21,h=None,c=INK,b=False,tag=''):
 z=P.text(x,y,w,s,pt,b,c,max_h=h,tag=tag or s[:28]);scene.append(('text',dict(x=x,y=y,w=w,s=s,pt=pt,b=b,c=c)));return z
DASH={'A':None,'B':MSO_LINE_DASH_STYLE.DASH,'C':MSO_LINE_DASH_STYLE.ROUND_DOT}
def line(x1,y1,x2,y2,c=RULE,pt=.8,status='A'):
 P.pdf.saveState();P.pdf.setDash([] if status=='A' else ([5,3] if status=='B' else [1.2,2.8]));P.line(x1,y1,x2,y2,c,pt);P.pdf.restoreState()
 if DASH[status] is not None:P.slide.shapes[-1].line.dash_style=DASH[status]
 scene.append(('line',dict(x1=x1,y1=y1,x2=x2,y2=y2,c=c,pt=pt,status=status)))
def arrow(x1,y1,x2,y2,c,status='A'):
 line(x1,y1,x2,y2,c,1.2,status);a=math.atan2(y2-y1,x2-x1)
 for da in [-.5,.5]:line(x2,y2,x2-2.7*math.cos(a+da),y2-2.7*math.sin(a+da),c,1.2)
def section(x,y,w,s,c=NAVY):
 txt(x,y,w,s,25,13,c,True);line(x,y+13,x+w,y+13,c,1)
def box(x,y,w,h,s,c,status):
 rect(x,y,w,h,'#FFFFFF',c if status!='C' else MUTED);txt(x+3,y+3,w-6,s,20,h-4,c)
def link(s,t,x1,y1,x2,y2,c,status):
 arrow(x1,y1,x2,y2,c,status);edges.append(dict(source=s,target=t,status=status))
rect(0,0,W,62,PALE)
txt(15,6,564,'量子計算がEV配送システムに寄与し得る条件：',39,20,NAVY,True)
txt(15,28,564,'配送計画と電池材料評価を介した影響経路の検討',32,17,NAVY,True)
txt(15,49,564,'佐野巧馬 ｜ Q/est',22,11,NAVY)
section(15,70,564,'1 背景・目的：個別の計算能力は、配送での成果へどう伝わるか')
txt(15,89,564,'都市内のEV配送では、荷物を運ぶ計画と走行電力量の両方を検討する必要がある [5]。量子計算には、訪問順を探す用途と材料の電子状態を評価する用途がある [1–3]。本研究は、単一拠点のEV配送を対象に、二つの用途から総移動時間または走行電力量へ影響が伝わる条件と、伝達を妨げる制約を、保存計算と文献から検討する。',22,38)
rect(15,130,564,17,'#F7FAFC')
txt(19,132,556,'対象：1台・1巡回・拠点発着・顧客時間窓なし。計画は総移動時間、車両は走行時の駆動電力量を評価する。',19.5,13)
txt(15,153,564,'図1 研究全体の構造：量子計算の用途と、二経路の分析対象',24,13,NAVY,True)
xs=[15,160,305,450];w=129
for x,s in zip(xs,['① 訪問順の探索 [1]','通常計算機（CPU）\n上の模擬計算','訪問順を入替えた\n古典解と比較','実配送への反映']):
 box(x,174,w,27,s,BLUE,'C' if x==450 else 'A')
link('algorithm','cpu',144,187.5,160,187.5,BLUE,'A');link('cpu','comparison',289,187.5,305,187.5,BLUE,'A');link('comparison','delivery',434,187.5,450,187.5,BLUE,'C')
txt(20,204,559,'比較する対象は候補の総移動時間と実行可能性である。量子実機の性能や、現場の採用・実行を実証するものではない。',17.5,10,BLUE)
for x,s in zip(xs,['② 電子のエネルギー\n評価 [2,3]','材料値・設計を仮定','部材・車両質量','走行時の電力量']):
 box(x,222,w,27,s,ORANGE,'C' if x==15 else 'B')
link('quantum_material','material_input',144,235.5,160,235.5,ORANGE,'C');link('material_input','mass',289,235.5,305,235.5,ORANGE,'B');link('mass','energy',434,235.5,450,235.5,ORANGE,'B')
txt(20,252,559,'電圧・安定性を量子計算で評価する用途は文献上の提案である。本研究は材料計算・合成をせず、設計入力以降を分析対象とする。',17.5,10,ORANGE)
for x,s,status in [(15,'実線：比較の手順', 'A'),(203,'破線：仮定を置くモデル計算','B'),(410,'点線：本分析の対象外','C')]:
 line(x,271,x+20,271,NAVY,1,status);txt(x+24,266,min(170,579-x-24),s,17,10,MUTED)
section(15,283,269,'2 経路1：配送計画の分析方法',BLUE);section(310,283,269,'3 経路2：材料・車両の分析方法',ORANGE)
rect(15,307,269,365,'#F1F6FA');rect(310,307,269,365,'#FAF3ED')
txt(20,311,259,'方法：同じ配送入力で訪問順を比較する',22,12,BLUE,True)
txt(20,328,259,'1入力は拠点・配送先・固定道路移動時間の組である。3/4/5/25/100先を各78入力、125先を70入力、計460入力を対象とする。各先を1回訪問し帰庫する。需要216荷物相当以下、作業102秒/先、帰庫9時間以内の条件を置く。',20,45)
txt(20,378,259,'図2 同じ入力に対する二つの計算手順',22,12,BLUE,True)
box(65,398,170,27,'共通入力：拠点・配送先・移動時間',BLUE,'A')
line(150,425,150,432,BLUE,1.2);line(77,432,211,432,BLUE,1.2)
arrow(77,432,77,442,BLUE);arrow(211,432,211,442,BLUE)
box(20,442,116,52,'通常計算の局所探索\n訪問順を入れ替え、\n比較用の古典解を作る',BLUE,'A')
box(158,442,116,52,'量子近似最適化 [1]\n候補の重みを調整し、\nCPU模擬で探索する',BLUE,'A')
line(77,494,77,504,BLUE,1.2);line(211,494,211,504,BLUE,1.2);line(77,504,211,504,BLUE,1.2);arrow(150,504,150,514,BLUE)
box(20,514,254,33,'同じ目的関数・制約で比較する\n総移動時間／実行可能性／工程時間',BLUE,'A')
txt(20,562,259,'比較条件：一部の位置を交換する5条件、隣接位置を交換する1条件、全訪問順を対象とするGrover型混合方式の層数2・3の計8設定である。量子近似最適化（QAOA）は候補の重みを調整して訪問順を探す方法である。',20,44)
txt(20,613,259,'各入力・設定で、学習状態から8192試行中の最良候補を10回測定する。学習・候補生成・検証などの一部工程と全工程の時間を区別し、未記録の時間を補完しない。',20,42)
txt(315,311,259,'方法：材料入力と設計・走行条件を分ける',22,12,ORANGE,True)
txt(315,328,259,'蓄える電力量20 kWhを固定し、比容量（活物質1 kgが蓄える電荷量）、電圧、利用率（使える容量の割合）を入力とする。電池の質量会計と、走行質量に対する電力量応答を分けて扱う。',20,45)
txt(315,378,259,'図3 材料入力から電力量までの計算手順',22,12,ORANGE,True)
box(322,398,250,27,'材料入力：比容量・電圧・利用率\n文献値と設計上の仮定を区別する',ORANGE,'B')
arrow(447,425,447,439,ORANGE,'B')
box(322,439,250,42,'電池質量を二つの会計で推計する\n簡略式：正負極と一括したその他部材\n部材別式：面積・箔・膜・電解液',ORANGE,'B')
arrow(447,481,447,495,ORANGE,'B')
box(322,495,250,27,'車両の走行質量へ換算する\n車体等の他質量・積載を固定する',ORANGE,'B')
arrow(447,522,447,536,ORANGE,'B')
box(322,536,250,27,'同じ保存速度軌跡を用いる\n質量を変え、駆動の物理モデルで計算する',ORANGE,'B')
arrow(447,563,447,577,ORANGE,'B')
box(322,577,250,27,'評価量：走行時の駆動電力量［Wh］',ORANGE,'B')
txt(315,619,259,'材料入力は文献報告・逆算参照・設計仮定を区別し、未知部材を0で補完しない。材料の出力・寿命・安全性、完成パックと実車の性能は、モデルの計算とは別の検証対象である。',20,42)
section(15,684,564,'4 評価項目：比較基準・集計単位・適用範囲を揃える')
txt(15,702,564,'配送計画では、候補と古典解の総移動時間差、実行可能性、計算時間、探索範囲を区別する。時間差は「候補−古典解」と定義する。10測定を入力内でまとめ、方式・規模別に分布を評価する。電池側では、設計条件・既知部材・未知部材を区分し、質量と電力量への伝達を調べる。走行計算は同一速度・平坦・回生/補機なし・積載0・効率0.9に限定する。',21,37)
section(15,747,564,'5 議論の対象：技術的な計算と、運用上の効果を区別する')
txt(15,765,564,'検討するのは、より良い訪問順を探索できる条件と、その計画を運用に用いるための時間・検証条件である。材料側では、材料入力を電池設計に利用する際の前提と、部材・車両質量から走行電力量へ接続する条件を問う。CPU模擬を量子実機の性能とせず、仮定を置いた設計・走行モデルを、完成電池や実車の性能実証と区別する。',21,37)
txt(15,804,564,'位置づけ：EV配送を社会技術システムの一部と捉えるが [4]、主体・制度・採用行動の分析は行っていない。',16,9,MUTED)
refs=[('[1] Bärtschi & Eidenbenz (2020). QCE, 72–82.',15,815),('[2] Delgado et al. (2022). Phys. Rev. A 106, 032428.',15,822),('[3] Shokrian Zini et al. (2023). Quantum 7, 1049.',310,815),('[4] Geels (2004). Res. Policy 33, 897–920.',310,822),('[5] Schneider et al. (2014). Transp. Sci. 48, 500–520.',15,829)]
for s,x,y in refs:txt(x,y,269,s,14,7,MUTED)
P.prs._element.sldSz.set('type','custom')
P.save('A1縦594×841mm。run06から別途作成した結果非掲載版である。数値結果、結果グラフ、改善/悪化内訳、候補存在の実績、質量感度値、相殺条件の結論を掲載しない。背景・目的、研究範囲、二経路の分析手順、評価項目、議論の対象を示す。入力数や計算条件は方法として維持する。既存研究が未実施になったという意味ではなく、結果の掲載を省いた版である。元資料・実験記録は変更していない。')
(OUT/'evidence/FIGURE_EDGES.json').write_text(json.dumps(edges,ensure_ascii=False,indent=2))
def svg():
 ss=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 594 841" width="594mm" height="841mm"><rect width="594" height="841" fill="white"/>']
 for typ,a in scene:
  if typ=='rect':ss.append(f'<rect x="{a["x"]}" y="{a["y"]}" width="{a["w"]}" height="{a["h"]}" fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width=".25"/>')
  elif typ=='line':
   dash='' if a['status']=='A' else ('1.76 1.06' if a['status']=='B' else '.42 .99')
   ss.append(f'<line x1="{a["x1"]}" y1="{a["y1"]}" x2="{a["x2"]}" y2="{a["y2"]}" stroke="{a["c"]}" stroke-width="{a["pt"]/MM}" stroke-dasharray="{dash}"/>')
  else:
   for i,t in enumerate(wrap(a['s'],a['w']*(.88 if a['w']>100 else 1),a['pt'],a['b'])):
    yy=a['y']+i*a['pt']/MM*1.27+a['pt']*.91/MM
    ss.append(f'<text x="{a["x"]}" y="{yy}" font-family="DejaVu Sans,Droid Sans Fallback,sans-serif" font-size="{a["pt"]/MM}" font-weight="{700 if a["b"] else 400}" fill="{a["c"]}">{escape(t)}</text>')
 return '\n'.join(ss+['</svg>'])
(OUT/'poster.svg').write_text(svg())
print('Built editable A1 portrait')
