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
txt(15,153,564,'図1 二経路の検証範囲：上流の量子技術と、下流で評価できた結果を分ける',24,13,NAVY,True)
xs=[15,160,305,450];w=129
for x,s in zip(xs,['① 訪問順の探索 [1]','通常計算機（CPU）\n上の模擬計算','訪問順を入替えた\n古典解と比較','実配送への反映']):
 box(x,174,w,27,s,BLUE,'C' if x==450 else 'A')
link('algorithm','cpu',144,187.5,160,187.5,BLUE,'A');link('cpu','comparison',289,187.5,305,187.5,BLUE,'A');link('comparison','delivery',434,187.5,450,187.5,BLUE,'C')
txt(20,204,559,'実行した範囲：候補の総移動時間と実行可能性。実機性能・計画取得の全工程時間・現場での採用は未検証である。',17.5,10,BLUE)
for x,s in zip(xs,['② 電子のエネルギー\n評価 [2,3]','材料値・設計を仮定','部材・車両質量','走行時の電力量']):
 box(x,222,w,27,s,ORANGE,'C' if x==15 else 'B')
link('quantum_material','material_input',144,235.5,160,235.5,ORANGE,'C');link('material_input','mass',289,235.5,305,235.5,ORANGE,'B');link('mass','energy',434,235.5,450,235.5,ORANGE,'B')
txt(20,252,559,'電圧・安定性を量子計算で評価する用途は文献上の提案である。本研究は材料計算・合成をせず、設計入力以降を検討した。',17.5,10,ORANGE)
for x,s,status in [(15,'実線：計算出力を比較', 'A'),(203,'破線：仮定を置くモデル計算','B'),(410,'点線：未検証の接続','C')]:
 line(x,271,x+20,271,NAVY,1,status);txt(x+24,266,min(170,579-x-24),s,17,10,MUTED)
section(15,283,269,'2 経路1：配送計画の方法と結果',BLUE);section(310,283,269,'3 経路2：材料・車両の方法と結果',ORANGE)
rect(15,307,269,365,'#F1F6FA');rect(310,307,269,365,'#FAF3ED')
txt(20,311,259,'方法：同じ配送入力で訪問順を比較する',22,12,BLUE,True)
txt(20,328,259,'1入力は拠点・配送先・固定道路移動時間の組である。3/4/5/25/100先を各78入力、125先を70入力、計460入力とした。各先を1回訪問し帰庫する。需要216荷物相当以下、作業102秒/先、帰庫9時間以内である。量子近似最適化（QAOA）で候補の重みを調整し、限定交換・隣接交換・全訪問順のGrover型混合方式をCPU模擬した [1]。',20,48)
txt(20,378,259,'図2 古典解からの総移動時間差',22,12,BLUE,True)
txt(20,394,259,'正：悪化、負：改善。点＝入力間平均、棒＝入力間標準偏差。',17,18,BLUE)
# Plot all saved means / SD; each input first averages 10 measurements.
rows=list(csv.DictReader((OUT/'evidence/SCALE_METHOD_STATISTICS.csv').open(encoding='utf-8-sig')))
plotx,ploty,pw,ph=46,426,220,72
for yy in [0,100,200,300,400]:
 y=ploty+ph*(1-yy/400);line(plotx,y,plotx+pw,y,RULE,.4)
 txt(21,y-3,22,str(yy),16,9,MUTED)
txt(20,414,259,'相対差［%］＝100 ×（候補時間−古典解時間）/古典解時間',16.5,10,BLUE)
ns=[3,4,5,25,100,125]
for i,n in enumerate(ns):
 x=plotx+i*pw/5;txt(x-8,502,26,str(n),17,9)
 for cfg,dx,c,fill in [('MEAN_P2',-2,BLUE,BLUE),('GROVER_P2',0,NAVY,NAVY),('GROVER_P3',2,'#6789A3','#FFFFFF')]:
  r=next(r for r in rows if int(r['delivery_stops'])==n and r['config']==cfg);v=float(r['mean_relative_percent']);sd=float(r['SD_relative_points']);y=ploty+ph*(1-v/400)
  yl=ploty+ph*(1-(v-sd)/400);yh=ploty+ph*(1-(v+sd)/400)
  line(x+dx,yh,x+dx,yl,c,.65);line(x+dx-1.6,yh,x+dx+1.6,yh,c,.65);line(x+dx-1.6,yl,x+dx+1.6,yl,c,.65)
  rect(x+dx-1.1,y-1.1,2.2,2.2,fill,c)
txt(20,502,16,'先数',15.5,10,MUTED)
for x,label,c,fill in [(20,'限定交換5＋隣接交換1',BLUE,BLUE),(132,'Grover混合 層2',NAVY,NAVY),(207,'Grover混合 層3','#6789A3','#FFFFFF')]:
 rect(x,517,2.5,2.5,fill,c);txt(x+5,514,110 if x==20 else 67,label,15.5,10,c)
txt(20,530,259,'限定交換・隣接交換の6設定は各値が一致し、平均悪化は0〜0.214%であった。全訪問順を対象とするGrover混合方式は25先以上で悪化が大きい。',19,28)
# Outcomes actual counts, no inference to independent repetitions.
vals=[('一致',28200,'#91AEC2'),('悪化',8600,BLUE)];x=20
for s,n,c in vals:
 ww=254*n/36800;rect(x,563,ww,12,c);txt(x+3,564,ww-4,f'{s} {n:,}',17,9,'#FFFFFF' if s=='悪化' else INK,True);x+=ww
txt(20,579,259,'全36,800保存候補で改善0、一致28,200、悪化8,600。全候補がモデルの制約を満たした。',19.5,27)
txt(20,609,259,'改善候補の存在と、探索で得ることは異なる',21,12,BLUE,True)
txt(20,625,259,'指定した限定交換範囲では、460入力すべてに古典解より良い候補がない。全訪問順には135入力でより良い解が確認され、41は条件付き参照、238は古典解と参照が一致、46は最適値未証明である。',19.5,40)
# Right methods.
txt(315,311,259,'方法：材料入力から下流の変化を分ける',22,12,ORANGE,True)
txt(315,328,259,'蓄える電力量20 kWhを固定し、比容量（活物質1 kgが蓄える電荷量）、電圧、利用率（使える容量の割合）を変える。正負極とその他質量を足す簡略式に加え、箔・膜・電解液を面積等から計上した。両モデルは別の部材会計である。',20,48)
txt(315,378,259,'図3a 部材の削減が相殺される条件',22,12,ORANGE,True)
txt(315,395,259,'正味の軽量化量 ΔM＝b−δ ［kg］',26,15,ORANGE,True)
txt(315,414,259,'b：同じ会計範囲での基準−変更後の質量。\nδ：会計外部材の変更後−基準の追加質量差。',18.5,22)
for x,title,s in [(315,'δ < b','軽くなる'),(403,'δ = b','差が消える'),(491,'δ > b','重くなる')]:
 rect(x,441,78,25,'#FFFFFF',ORANGE);txt(x+3,443,72,title,21,11,ORANGE,True);txt(x+3,455,72,s,17.5,10)
txt(315,476,259,'図3b 材料値を使わない電力量の質量感度',21,12,ORANGE,True)
txt(315,491,259,'走行質量1000 kgでの微分。460保存軌跡、抵抗2設定。',16.5,10,ORANGE)
hist=list(csv.DictReader((OUT/'evidence/MASS_RESPONSE_HISTOGRAM.csv').open(encoding='utf-8-sig')))
hx,hy,hw,hh=342,516,220,52;maxc=200
for k in [0,100,200]:
 y=hy+hh*(1-k/maxc);line(hx,y,hx+hw,y,RULE,.4);txt(316,y-3,22,str(k),16,9,MUTED)
txt(315,505,255,'軌跡数［本］（各設定460本）',16,9,ORANGE)
for i in range(6):
 for j,(case,c) in enumerate([('CRR_LOWER_BOUND',ORANGE),('CRR_UPPER_BOUND','#D7A589')]):
  rr=next(r for r in hist if r['rolling_case']==case and int(r['bin_lower_Wh_kg'])==i);v=int(rr['count']);bw=hw/6
  rect(hx+i*bw+3+j*13,hy+hh-v/maxc*hh,11,v/maxc*hh,c)
for i in range(7):txt(hx+i*hw/6-2,572,20,str(i),16,9)
txt(343,582,230,'質量1 kg増あたりの電力量増［Wh/kg］',15.5,10,MUTED)
for x,s,c in [(315,'転がり抵抗：下側設定',ORANGE),(451,'上側設定','#D7A589')]:
 rect(x,594,3,3,c);txt(x+5,591,125,s,15.5,10,ORANGE)
txt(315,600,259,'平均±軌跡間標準偏差は2.368±1.140 / 2.432±1.167 Wh/kg。1000〜1250 kgで質量削減と電力量削減の符号が一致した。',19,29)
txt(315,635,259,'同じ電圧・配合・負極・その他質量なら、比容量×利用率が基準より大きいと軽量になる。電圧低下や追加部材でこの差は相殺・逆転する。逆算容量は参考値であり、実用入力・完成パックは未確定である。',18.5,35)
section(15,684,564,'4 評価：何を確認し、どこまで比較できるか')
txt(15,702,564,'経路1は、古典の局所探索解とCPU模擬候補の比較である。移動時間と、計算に要する時間は別である。全工程時間と実運用の許容時間は未確認である。限定交換5・隣接交換1・Grover型混合方式（GM）の層2/3、計8設定を用いた [1]。各入力・設定で1回学習し、8192試行中の最良候補を10回測定した。10測定を入力内で平均し、方式・規模別に集計した。全候補数を独立標本数とせず、予算差が残るため速度優位も結論しない。全訪問順の理想状態の準備を実機で実証したものではない。',20,37)
section(15,747,564,'5 議論・結論：探索範囲と中間変換を確定して寄与を判断する')
txt(15,765,564,'経路1では、改善候補を含まない探索範囲では取得を増やしても古典解を上回れず、候補が存在しても実際の取得は別に評価する必要がある。経路2では、材料値の差は設計・未知部材で相殺され、走行条件が電力量への伝達量を変える。電力量計算は同一速度・平坦・回生/補機なし・積載0・効率0.9の範囲である。実機・実運用、材料の出力/寿命/安全性、完成パック・実車効果は未検証である。',20,37)
txt(15,804,564,'位置づけ：EV配送を社会技術システムの一部と捉えるが [4]、主体・制度・採用行動の分析は行っていない。',16,9,MUTED)
refs=[('[1] Bärtschi & Eidenbenz (2020). QCE, 72–82.',15,815),('[2] Delgado et al. (2022). Phys. Rev. A 106, 032428.',15,822),('[3] Shokrian Zini et al. (2023). Quantum 7, 1049.',310,815),('[4] Geels (2004). Res. Policy 33, 897–920.',310,822),('[5] Schneider et al. (2014). Transp. Sci. 48, 500–520.',15,829)]
for s,x,y in refs:txt(x,y,269,s,14,7,MUTED)
P.prs._element.sldSz.set('type','custom')
P.save('A1縦594×841mm。出典と全精度統計は同梱の根拠表に記載。総移動時間差は候補−古典の局所探索比較解。定時率は最新論文で主指標から除外されており再導入しない。未検証の主体・制度作用図を削除。実線はCPU出力比較、破線は設計仮定を置くモデル、点線は未検証。図2は入力内10測定平均の入力間平均±SDでありCIではない。図3bは材料入力なしの既存DC核の1000kg右微分。最新追加解析の逆算材料値は実用入力へ採用しない。新しい科学実験・シミュレーションは本ポスター編集では行わず保存結果を集計・描画した。')
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
