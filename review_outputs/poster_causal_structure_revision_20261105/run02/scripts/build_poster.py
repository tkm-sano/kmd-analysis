"""Causal-pathway-centred A1 revision. No new research calculations."""
from poster_primitives import *
from content import TITLE,RQ,REFS
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from xml.sax.saxutils import escape
import hashlib
P=Poster();scene=[];nodes=[];edges=[]
def rect(x,y,w,h,fill=None,stroke=None):
 P.rect(x,y,w,h,fill,stroke);scene.append(('rect',dict(x=x,y=y,w=w,h=h,fill=fill or 'none',stroke=stroke or 'none')))
def txt(x,y,w,s,pt=22,h=None,c=INK,b=False,tag=''):
 end=P.text(x,y,w,s,pt,b,c,max_h=h,tag=tag or s[:25]);scene.append(('text',dict(x=x,y=y,w=w,s=s,pt=pt,b=b,c=c)));return end
DASH={'A':None,'B':MSO_LINE_DASH_STYLE.DASH,'C':MSO_LINE_DASH_STYLE.ROUND_DOT}
def line(x1,y1,x2,y2,c=RULE,pt=.8,status='A'):
 P.pdf.saveState();P.pdf.setDash([] if status=='A' else ([5,3] if status=='B' else [1.2,2.8]));P.line(x1,y1,x2,y2,c,pt);P.pdf.restoreState()
 if DASH[status] is not None:P.slide.shapes[-1].line.dash_style=DASH[status]
 scene.append(('line',dict(x1=x1,y1=y1,x2=x2,y2=y2,c=c,pt=pt,status=status)))
def arrow(x1,y1,x2,y2,c,status):
 line(x1,y1,x2,y2,c,1.2,status);a=math.atan2(y2-y1,x2-x1)
 for da in (-.5,.5):line(x2,y2,x2-2.7*math.cos(a+da),y2-2.7*math.sin(a+da),c,1.2)
def edge(eid,source,target,x1,y1,x2,y2,c,status,label='',ly=None):
 cc=MUTED if status=='C' else c;arrow(x1,y1,x2,y2,cc,status)
 if label:txt(min(x1,x2)+1,(ly if ly is not None else min(y1,y2)-12),max(25,abs(x2-x1)-2),label,17,10,cc)
 edges.append(dict(id=eid,source=source,target=target,status=status,label=label))
def node(nid,x,y,w,h,title,body,status,c):
 fill='#EDF3F7' if c==NAVY else ('#F1F6FA' if c==BLUE else '#FAF3ED')
 if status=='C':fill='#F5F5F5'
 rect(x,y,w,h,fill,c if status!='C' else RULE)
 txt(x+4,y+4,w-8,title,21,12,c if status!='C' else MUTED,True,tag=nid+'_title')
 if body:txt(x+4,y+20,w-8,body,20, h-22,INK,tag=nid+'_body')
 nodes.append(dict(id=nid,x=x,y=y,w=w,h=h,title=title,body=body,status=status))
def driver(did,x,y,w,s,target_x,target_y,status,c):
 rect(x,y,w,22,'#FFFFFF',RULE);txt(x+3,y+2,w-6,s,18.5,19,c,tag=did)
 edge(did+'_influence',did,'below',target_x,y+22,target_x,target_y,c,status)
def note(x,y,w,title,body,c=INK,pt=21):
 txt(x,y,w,title,23,12,c,True);txt(x,y+15,w,body,pt,34)
# Research logic: socio-technical framing is primary; quantitative paths are scoped cases.
rect(0,0,W,66,'#EDF3F7')
txt(15,7,811,'量子計算がEV配送システムに寄与し得る条件：',40,20,NAVY,True)
txt(15,29,811,'配送計画と電池材料評価を介した影響経路の検討',34,17,NAVY,True)
txt(15,51,811,'佐野巧馬｜Q/est',22,11,NAVY)
txt(15,74,811,'研究目的：EV配送を、利用主体が規則・判断基準の下で技術を選択・運用して配送機能を担う社会技術システムとして捉え、量子計算を計画・設計に組み込む条件を検討する [1,5]。',23,25,NAVY)
txt(15,111,811,'1 社会技術システムの論理構造：技術・主体・規則の相互関係',28,14,NAVY,True)
line(15,127,826,127,NAVY,1.2)
# The outer boundary covers all three analytic dimensions; actors and rules are not side notes.
rect(205,135,621,189,'#F7FAFC',RULE)
txt(221,140,585,'社会的機能：物資の配送を成立させる',25,13,NAVY,True)
node('actors',245,173,215,53,'利用主体','役割として置く計画担当・設計担当\n構成の選択・評価・利用を担う','B',NAVY)
node('rules',585,173,220,53,'規則・判断基準・慣行','目的・評価の基準・作業手順\n現場での具体的な内容は未調査','B',NAVY)
node('configuration',415,263,240,52,'技術・運用の構成','計画システム・車両・電池\n計算の分担と設計・運行の組合せ','B',NAVY)
# Six theoretical interactions, based on the analytic distinction in Geels (2004), Fig.4.
edge('rules_actors','rules','actors',585,190,460,190,NAVY,'B')
txt(473,176,105,'判断を方向付ける',18,10,NAVY)
edge('actors_rules','actors','rules',460,214,585,214,NAVY,'B')
txt(473,216,110,'実践で維持・見直し',17.5,9,NAVY)
line(245,199,226,199,NAVY,1.2,'B');line(226,199,226,289,NAVY,1.2,'B')
edge('actors_config','actors','configuration',226,289,415,289,NAVY,'B')
txt(244,275,160,'選択・設計・運用',18,10,NAVY)
line(415,275,402,275,NAVY,1.2,'B')
edge('config_actors','configuration','actors',402,275,402,226,NAVY,'B')
txt(413,240,165,'可能な行為を制約',18,10,NAVY)
line(690,226,690,287,NAVY,1.2,'B')
edge('rules_config','rules','configuration',690,287,655,287,NAVY,'B')
txt(697,243,103,'設計・運用の\n前提となる',18,18,NAVY)
line(655,307,775,307,NAVY,1.2,'B')
edge('config_rules','configuration','rules',775,307,775,226,NAVY,'B')
txt(679,292,91,'技術と基準の調整',17.5,10,NAVY)
# Quantum technologies enter the configuration as capabilities/information, subject to this context.
rect(15,177,155,120,'#EDF3F7',RULE)
txt(21,183,143,'導入候補の量子計算',23,12,NAVY,True)
txt(21,202,143,'① 計画の候補探索',22,11,BLUE,True)
txt(21,217,143,'CPU理想モデルで検討',19,10,BLUE)
txt(21,241,143,'② 材料の物性評価',22,11,ORANGE,True)
txt(21,256,143,'本研究では未実行',19,10,ORANGE)
txt(21,279,143,'計算能力・評価情報の候補',18,10,MUTED)
line(170,238,195,238,NAVY,1.2,'B');line(195,238,195,305,NAVY,1.2,'B')
edge('quantum_config','quantum_candidate','configuration',195,305,415,305,NAVY,'B')
txt(240,294,159,'利用する構成を検討',17.5,9,NAVY)
txt(15,329,811,'Geels [5] の三つの分析次元を本事例へ適用した関係図である。主体・規則の実際の相互作用を、今回の数値実験で実証したものではない。',17,9,MUTED)
txt(15,344,811,'2 定量分析：上図の「技術・運用の構成」における接続条件を検討する',24,13,NAVY,True)
# Two nested analyses, not two independent studies standing in for the whole socio-technical system.
txt(15,366,391,'① 配送計画：探索範囲・取得・採用の接続',24,13,BLUE,True)
txt(435,366,391,'② 材料評価：設計・部材・走行条件の接続',24,13,ORANGE,True)
txt(15,382,391,'古典処理と理想量子モデルの計算分担を扱う [2]。',17.5,9,BLUE)
txt(574,382,252,'B 今回は設計仮定から解析する [3,4]。',17.5,9,ORANGE)
# Main bounded routes. Node sizes and line breaks prioritise the system logic.
def small(nid,x,y,w,title,body,status,c):
 rect(x,y,w,46,'#F1F6FA' if c==BLUE else '#FAF3ED',c if status!='C' else RULE)
 txt(x+3,y+3,w-6,title,20,11,c,True,tag=nid+'_title');txt(x+3,y+17,w-6,body,18.5,28,tag=nid+'_body')
 nodes.append(dict(id=nid,x=x,y=y,w=w,h=46,title=title,body=body,status=status))
small('route_scope',15,397,115,'A 範囲・主対照','古典側が範囲 S と\n主対照 JC を設定','A',BLUE)
small('route_candidate',152,397,115,'A 候補の取得','理想量子モデルで\n候補経路を得る\n（CPU数値計算）','A',BLUE)
small('route_adoption',289,397,117,'A 検証／C 採用','JCとの差・制約を検証\n締切 H 内での採用\nは未確認','B',BLUE)
edge('route_search','route_scope','route_candidate',130,420,152,420,BLUE,'B')
edge('route_verification','route_candidate','route_adoption',267,420,289,420,BLUE,'A')
small('material_adoption',435,397,115,'C 設計への利用','物性情報を設計に\n採用する接続は\n今回は未検証','C',ORANGE)
small('material_balance',573,397,115,'B 設計・部材','容量一定の設計仮定\n部材の質量収支\n正味軽量化 b−δ','B',ORANGE)
small('material_DC',711,397,115,'A/B 走行応答','走行総質量 m\n固定の速度軌跡\n→ DC電力量','A',ORANGE)
edge('material_use','material_adoption','material_balance',550,420,573,420,ORANGE,'C')
edge('material_mass_DC','material_balance','material_DC',688,420,711,420,ORANGE,'B')
edge('symbolic_entry','symbolic_assumptions','material_balance',632,391,632,397,ORANGE,'B')
txt(15,449,391,'観測：支持の制約と主対照への非改善',22,12,BLUE,True)
txt(15,465,391,'限定交換の全460入力で、支持内最小＝初期解≥JC。主対照超えは0/36,800候補。どの古典解を基準にするかと、現場での採用判断を区別する。',20.5,30)
txt(435,449,391,'解析：質量差の相殺と条件付きの伝達',22,12,ORANGE,True)
txt(435,465,391,'研究で置いた容量一定の設計仮定と部材条件がbを定める。正味差b−δはδ=bで消える。別のDC検算920条件では、同一条件・1000〜1250kgで質量感度が正であった。',20.5,30)
txt(15,499,811,'① 時間窓なし、460入力×8設定×10反復、各8192回の最良。8設定は限定位置交換5・隣接交換1・Grover型混合QAOA2である。\n② 記号質量式・部材会計と、460軌跡×抵抗2設定の独立DC検算。bは既知部材の削減、δは会計外の追加差［kg］である。',18,18)
txt(15,519,811,'下図の実線A：保存計算／モデル内で確認、破線B：条件付き接続、点線C：未検証。上図の相互関係は社会技術システム論に基づく分析枠組みである。',17,9,MUTED)
line(15,532,826,532,NAVY,1.1)
txt(15,536,811,'研究の位置付け：システムへの組込み条件を、検証範囲を分けて論じる',24,12,NAVY,True)
txt(15,551,811,'量子計算の寄与を、利用主体が技術を計画・設計へ組み込む条件として分析する。定量結果で確認した接続と、主体・規則・実運用に関する未検証の接続を区別する [6]。',22,21,NAVY)
refs=['[1] Schneider et al. (2014), Transp. Sci. 48, 500–520.','[2] Bärtschi & Eidenbenz (2020), IEEE QCE, 72–82.','[3] Delgado et al. (2022), Phys. Rev. A 106, 032428.','[4] Shokrian Zini et al. (2023), Quantum 7, 1049.','[5] Geels (2004), Res. Policy 33, 897–920.','[6] Stilgoe et al. (2013), Res. Policy 42, 1568–1580.']
for i,s in enumerate(refs):txt(15+(i%3)*275,575+(i//3)*8,261,s,14,7)
P.save('社会技術システムを研究全体の分析枠組みに置く修正。Geels2004 Sec2/Fig4の三次元（システムの構成・主体・規則）と相互作用を参照する独自の概念図である。図の実際の主体配置・組織・制度・市場・規則変更を実証したとはしない。規則は組織そのものではない。計画担当・設計担当は分析上の役割であり、面接で抽出した主体ではない。研究者が設定したJCや時間窓なしの制約を現場の制度・採用基準と同一視しない。下段は上位枠組みの部分分析。配送はCPU上の理想モデルと古典主対照の保存差を扱い、実運用採用は未検証。材料は記号感度と部材会計、材料値を使わない固定速度DC検算を区別する。未知部材は0で補完せず、完成pack質量・実用性能・量子由来物性改善・実車の接続は未検証。Chen逆算参照値を主材料値としない。[6]は前提・尺度の省察に限定し、RIQ・面接・M1は方法に戻していない。社会的機能として物資配送を置くが、総移動時間JやモデルDCを社会的便益の包括的評価量と同一視しない。\n'+ '\n'.join(str(r) for r in REFS))
(OUT/'evidence/SYSTEM_STRUCTURE.json').write_text(json.dumps(dict(nodes=nodes,edges=edges),ensure_ascii=False,indent=2))
# Native editable SVG of the socio-technical frame; the poster remains a native PPTX.
def svg(crop=False):
 v='0 108 841 230' if crop else '0 0 841 594';out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{v}" width="841mm" height="{230 if crop else 594}mm"><rect width="841" height="594" fill="white"/>']
 for typ,a in scene:
  if typ=='rect':out.append(f'<rect x="{a["x"]}" y="{a["y"]}" width="{a["w"]}" height="{a["h"]}" fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width=".25"/>')
  elif typ=='line':
   dash='' if a['status']=='A' else ('1.76 1.06' if a['status']=='B' else '.42 .99')
   out.append(f'<line x1="{a["x1"]}" y1="{a["y1"]}" x2="{a["x2"]}" y2="{a["y2"]}" stroke="{a["c"]}" stroke-width="{a["pt"]/MM}" stroke-dasharray="{dash}"/>')
  else:
   for i,s in enumerate(wrap(a['s'],a['w']*(.88 if a['w']>100 else 1),a['pt'],a['b'])):
    yy=a['y']+i*a['pt']/MM*1.27+a['pt']*.91/MM
    out.append(f'<text x="{a["x"]}" y="{yy}" font-family="DejaVu Sans,Droid Sans Fallback,sans-serif" font-size="{a["pt"]/MM}" font-weight="{700 if a["b"] else 400}" fill="{a["c"]}">{escape(s)}</text>')
 return '\n'.join(out+['</svg>'])
(OUT/'poster.svg').write_text(svg());(OUT/'sociotechnical_structure.svg').write_text(svg(True))
