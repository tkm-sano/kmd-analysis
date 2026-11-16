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
 fill='#F1F6FA' if c==BLUE else '#FAF3ED'
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
# Header and framing: one common question, two distinct conditional pathways.
rect(0,0,W,66,'#EDF3F7')
txt(15,7,811,'量子計算がEV配送システムに寄与し得る条件：',40,20,NAVY,True)
txt(15,29,811,'配送計画と電池材料評価を介した影響経路の検討',34,17,NAVY,True)
txt(15,51,811,'佐野巧馬｜Q/est',22,11,NAVY)
txt(15,74,811,'研究目的：EV配送の計画・電池・運行をつなぐ二つの経路について、計算出力が運用・設計に利用され、成果へ伝わる条件を、保存結果と文献から特定する [1]。',23,24,NAVY)
# Legend is an evidence map, not an assertion of identified real-world causal effects.
for x,status,label in [(15,'A','A 保存計算・モデル内で確認'),(290,'B','B 数式・文献に基づく条件付き接続'),(610,'C','C 未検証の接続')]:
 arrow(x,110,x+27,110,NAVY if status!='C' else MUTED,status);txt(x+34,105,240 if x<600 else 180,label,18,11)
txt(15,119,811,'矢印は情報の利用・モデル上の作用を示す。実世界の因果効果を実証した範囲とは区別する。主体・適用判断・前提を分ける視点に[5,6]を用いる。',17,9,MUTED)
# PATH 1: candidate existence, acquisition, validation/adoption, integration, actual outcomes.
txt(15,132,811,'経路1 配送計画：探索能力が短い配送計画へ伝わるための接続',28,14,BLUE,True)
line(15,147,826,147,BLUE,1.1)
xs=[15,190,365,540,715];ws=[140,140,140,140,111]
driver('P1_S',15,153,140,'探索範囲 S・問題規模 n\n古典主対照 JC',85,183,'B',BLUE)
driver('P1_resources',190,153,140,'初期状態・混合\n学習・測定予算',260,183,'B',BLUE)
driver('P1_H',365,153,140,'全工程時間τ≤許容時間H\n古典側の検証・採用',435,183,'C',BLUE)
driver('P1_dynamic',540,153,140,'需要・道路の更新\n全体計画との整合',610,183,'C',BLUE)
driver('P1_road',715,153,111,'道路・積載\n実際の運行条件',770,183,'C',BLUE)
node('P1_existence',15,183,140,59,'B 改善候補の存在','指定した範囲 S に\nJCより短い候補が\n含まれているか','B',BLUE)
node('P1_acquire',190,183,140,59,'A 候補の取得','','A',BLUE)
rect(195,203,130,11,'#FFFFFF',BLUE);txt(199,204,122,'古典：角度を更新',18.5,10,BLUE,tag='P1_classical_tuning')
rect(195,228,130,11,'#FFFFFF',BLUE);txt(199,229,122,'理想量子（CPU）：状態・測定',18.5,10,BLUE,tag='P1_ideal_sampling')
edge('P1_angles','classical_tuning','ideal_model',220,214,220,228,BLUE,'A')
edge('P1_evaluation','ideal_model','classical_tuning',300,228,300,214,BLUE,'A')
txt(224,217,26,'角度',17.5,9,BLUE);txt(274,217,24,'評価値',17.5,9,BLUE)
node('P1_adopt',365,183,140,59,'A 検証／C 運用採用','候補の移動時間 JQ を検証\n制約・JCとの差を確認\n締切Hの充足は未確認','B',BLUE)
node('P1_integrate',540,183,140,59,'C 全体計画への統合','運用中の計画へ反映\n動的更新・部分問題選択\nは今回未検証','C',BLUE)
node('P1_real',715,183,111,59,'C 実際の配送','実道路での\n移動時間・運行\nを評価する','C',BLUE)
for i,(st,lab) in enumerate([('B','探索'),('A','検証'),('C','統合'),('C','実行')]):edge('P1_main_'+str(i),'P1_'+str(i),'P1_'+str(i+1),xs[i]+ws[i],214,xs[i+1],214,BLUE,st,lab,201)
line(85,242,85,251,BLUE,.6);line(260,242,260,251,BLUE,.6)
note(15,253,391,'確認① 探索範囲が改善を制限する','限定位置交換の全460入力で、範囲S内の最小移動時間＝初期解の移動時間≥JCであった。この範囲には、主対照を改善する候補が存在しない。',BLUE)
note(435,253,391,'確認② 候補の取得と主対照への改善は別である','主対照超えは0/36,800保存候補。小規模診断では初期状態による取得差を確認した。候補の存在と、有限予算での取得を分けて評価する。',BLUE)
txt(15,303,811,'方法：1車両・時間窓なし、総移動時間 J［秒］を最小化。3/4/5/25/100先各78例、125先70例（計460例）。8設定＝限定位置交換5・隣接交換1・GM-QAOA2。\n1例は拠点・配送先・固定移動時間行列の組。各設定10測定反復、各8192回の最良を評価。JCは初期解を隣接交換で反復改善した古典解である [2]。',18.5,28)
# PATH 2: future quantum output is separate from symbolic inputs actually used.
txt(15,340,811,'経路2 電池材料：評価情報が設計・質量・走行電力量へ伝わるための接続',28,14,ORANGE,True)
line(15,355,826,355,ORANGE,1.1)
driver('P2_quantum_resource',15,361,140,'計算精度・費用\n必要な量子資源',85,392,'C',ORANGE)
# This branch enters the model AFTER the unverified design-adoption connection.
rect(280,361,225,22,'#FAF3ED',ORANGE)
txt(284,363,217,'B 容量一定で q,u,V・部材の条件を与える\n量子計算で生成した物性値は用いていない',18.5,19,ORANGE,tag='P2_actual_input')
edge('P2_symbolic_entry','symbolic_assumptions','model_input',356,383,356,423,ORANGE,'B')
driver('P2_driving',540,361,140,'材料値なし／同一速度・係数\n計算範囲1000〜1250kg',610,392,'B',ORANGE)
driver('P2_real_conditions',715,361,111,'実用性能・運行条件\n実車との整合',770,392,'C',ORANGE)
node('P2_qmat',15,392,140,59,'C 量子材料評価','電子状態・エネルギー\n出力：物性評価の情報\n本研究で未実行 [3,4]','C',ORANGE)
node('P2_design',190,392,140,59,'C 情報の設計利用','物性情報を設計者が採用\n実用性能との整合を判断\n→ 設計条件 q,u,V 等','C',ORANGE)
node('P2_mass',365,392,140,59,'B 電池の質量収支','正負極の塗膜・集電体\nセパレータ・電解液＋U\n→ 電池質量 M','B',ORANGE)
node('P2_dc',540,392,140,59,'A/B 車両・走行計算','走行総質量m=共通質量+M\n転がり・加速の仕事が変化\n出力：DC電力量 E_DC','A',ORANGE)
node('P2_real',715,392,111,59,'C 実車の電力量','実パックの質量と\n実際の運行条件で\n効果を評価する','C',ORANGE)
edge('P2_use','quantum_info','engineering_adoption',155,423,190,423,ORANGE,'C','利用',410)
edge('P2_adoption_unverified','engineering_adoption','model_input',330,423,356,423,ORANGE,'C')
edge('P2_mass_from_input','model_input','mass_model',356,423,365,423,ORANGE,'B')
txt(332,410,23,'入力',17,10,ORANGE)
rect(355.2,422.2,1.6,1.6,ORANGE)
edge('P2_mass_dc','mass_model','DC_model',505,423,540,423,ORANGE,'B','換算',410)
edge('P2_real_link','DC_model','actual_EV',680,423,715,423,ORANGE,'C','適用',410)
# Branches modifying the mass balance and the driving response remain visible.
note(15,462,315,'今回の解析範囲を、未検証の上流と分ける','容量一定の質量式を記号的に解析し、部材差の相殺条件を求めた。別に、材料値を使わず保存軌跡の質量応答を検算し、同条件での符号対応を確認した。',ORANGE,20.5)
txt(365,462,140,'部材による相殺',22,11,ORANGE,True)
txt(365,476,140,'正味軽量化 ΔM=b−δ。\n面積・塗工方針→既知の削減b。\n追加差 δ=b で効果が消失。\n完成パック質量は未確定。',19.5,35)
edge('P2_component_modifier','component_design_and_extra_mass','mass_model',435,461,435,451,ORANGE,'B')
txt(540,462,140,'A 確認した走行応答',21,11,ORANGE,True)
txt(540,476,140,'460軌跡×抵抗2設定。\n920条件で質量感度が正。\n同区間で質量差とDC差の\n符号が一致する。',19.5,35)
line(610,451,610,460,ORANGE,.6)
txt(715,462,111,'C 残る接続',21,11,MUTED,True)
txt(715,476,111,'実用電池での成立、\n実車での削減、\n量子計算への帰属は\n未検証である。',19,35)
txt(15,514,811,'qは比容量、uは利用率、Vは電圧。Uは会計外部材質量。bは既知部材の基準−変更後、δは会計外部材の変更後−基準［kg］。走行は平坦・回生／補機なし・荷重一定。',17.5,10,MUTED)
line(15,528,826,528,NAVY,1.1)
txt(15,532,811,'二経路から得た構造的な知見',26,13,NAVY,True)
txt(15,548,811,'同じ探索範囲に改善候補がなければ取得能力を上げても短縮できず、材料入力の差も追加部材で相殺され得る。計算能力から成果への各接続で、何が維持され、どこで失われるかを分けて検証する必要がある。',22,22,NAVY)
refs=['[1] Schneider et al. (2014), Transp. Sci. 48, 500–520.','[2] Bärtschi & Eidenbenz (2020), IEEE QCE, 72–82.','[3] Delgado et al. (2022), Phys. Rev. A 106, 032428.','[4] Shokrian Zini et al. (2023), Quantum 7, 1049.','[5] Geels (2004), Res. Policy 33, 897–920.','[6] Stilgoe et al. (2013), Res. Policy 42, 1568–1580.']
for i,s in enumerate(refs):txt(15+(i%3)*275,575+(i//3)*8,261,s,14,7)
P.save('因果経路図中心の修正。Aは保存計算/固定モデル内での確認、Bは数式・文献に依存する条件付き接続、Cは未検証である。実世界の因果効果を推定した研究ではない。配送の図は主対照より総移動時間の短い計画に寄与する条件を扱う。全顧客を保持した支持を部分顧客分割と混同しない。角度更新は古典、状態・測定はCPU理想量子モデルである。量子実機、動的更新、全体計画への統合は未検証。材料は量子→実物性→実用設計を検証していない。記号入力が未検証の設計採用を迂回してモデルに入ることを分岐で示す。bは同一部材会計内の基準−変更後、δは会計外の変更後−基準。T08記号感度とT09構造補完を区別し、183条件の完成パックは未確定である。DCの正微分と符号対応は同一保存速度・係数、両質量1000〜1250kg、平坦・回生/補機なし等の条件に限る。[5][6]は利用主体と前提を分ける視点に限定して使用する。詳細数値・出典は前版run06の92行の台帳へ接続する。\n'+ '\n'.join(str(r) for r in REFS))
# Editable SVG: text remains text; nodes and causal links remain vector objects.
def svg(crop=False):
 v='0 101 841 423' if crop else '0 0 841 594';out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{v}" width="841mm" height="{423 if crop else 594}mm"><rect width="841" height="594" fill="white"/>']
 for typ,a in scene:
  if typ=='rect':out.append(f'<rect x="{a["x"]}" y="{a["y"]}" width="{a["w"]}" height="{a["h"]}" fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width=".25"/>')
  elif typ=='line':
   dash='' if a['status']=='A' else ('1.76 1.06' if a['status']=='B' else '.42 .99')
   out.append(f'<line x1="{a["x1"]}" y1="{a["y1"]}" x2="{a["x2"]}" y2="{a["y2"]}" stroke="{a["c"]}" stroke-width="{a["pt"]/MM}" stroke-dasharray="{dash}"/>')
  else:
   lines=wrap(a['s'],a['w']*(.88 if a['w']>100 else 1),a['pt'],a['b'])
   for i,s in enumerate(lines):
    yy=a['y']+i*a['pt']/MM*1.27+a['pt']*.91/MM
    out.append(f'<text x="{a["x"]}" y="{yy}" font-family="DejaVu Sans,Droid Sans Fallback,sans-serif" font-size="{a["pt"]/MM}" font-weight="{700 if a["b"] else 400}" fill="{a["c"]}">{escape(s)}</text>')
 return '\n'.join(out+['</svg>'])
(OUT/'poster.svg').write_text(svg());(OUT/'causal_paths.svg').write_text(svg(True))
driver_targets={'P1_S':'P1_existence','P1_resources':'P1_acquire','P1_H':'P1_adopt','P1_dynamic':'P1_integrate','P1_road':'P1_real','P2_quantum_resource':'P2_qmat','P2_driving':'P2_dc','P2_real_conditions':'P2_real'}
main_nodes=['P1_existence','P1_acquire','P1_adopt','P1_integrate','P1_real']
for e in edges:
 if e['id'].endswith('_influence'):e['target']=driver_targets[e['source']]
 if e['id'].startswith('P1_main_'):
  i=int(e['id'].rsplit('_',1)[1]);e['source']=main_nodes[i];e['target']=main_nodes[i+1]
aliases={'quantum_info':'P2_qmat','engineering_adoption':'P2_design','mass_model':'P2_mass','DC_model':'P2_dc','actual_EV':'P2_real'}
for e in edges:
 e['source']=aliases.get(e['source'],e['source']);e['target']=aliases.get(e['target'],e['target'])
modifiers=[dict(id=k) for k in driver_targets]+[dict(id='symbolic_assumptions'),dict(id='model_input'),dict(id='component_design_and_extra_mass')]
internal_nodes=[dict(id='classical_tuning',parent='P1_acquire'),dict(id='ideal_model',parent='P1_acquire')]
(OUT/'evidence/DIAGRAM_STRUCTURE.json').write_text(json.dumps(dict(nodes=nodes,modifiers=modifiers,internal_nodes=internal_nodes,edges=edges),ensure_ascii=False,indent=2))
print('Built native causal diagram:',len(nodes),'nodes,',len(edges),'links')
