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
from sections import *
import csv
SRC=OUT.parent/'run04';old_blocks=json.loads((SRC/'poster_layout.json').read_text());old_nodes={n['id']:n for n in json.loads((SRC/'evidence/SYSTEM_STRUCTURE.json').read_text())['nodes']}
def source(prefix):
 v=[b['text'] for b in old_blocks if b['text'].startswith(prefix)];assert len(v)==1,(prefix,len(v));return v[0]
def st(prefix,x,y,w,pt,h,c=INK,b=False):return txt(x,y,w,source(prefix),pt,h,c,b)
def oldnode(nid,x,y,w,h,c):
 n=old_nodes[nid];node(nid,x,y,w,h,n['title'],n['body'],n['status'],c)
def section(y,title):
 txt(15,y,564,title,25,13,NAVY,True);line(15,y+13,579,y+13,NAVY,1)
rect(0,0,W,66,'#EDF3F7')
st('量子計算がEV配送',15,7,564,40,20,NAVY,True)
st('配送計画と電池材料評価を介した',15,29,564,34,17,NAVY,True)
st('佐野巧馬',15,51,564,22,11,NAVY)
section(75,'1 目的');txt(15,94,564,PURPOSE,22,30)
txt(15,132,564,'図1 社会技術システムとしての分析枠組み [5]',24,13,NAVY,True)
txt(15,151,564,'導入候補の量子計算：① 計画探索（CPU理想計算）、② 材料物性評価（本研究未実行）',18.5,17,NAVY)
rect(15,174,564,130,'#F7FAFC',RULE)
st('社会的機能：',30,180,534,22,12,NAVY,True)
oldnode('actors',30,197,150,49,NAVY)
oldnode('rules',414,197,150,49,NAVY)
oldnode('configuration',218,260,160,40,NAVY)
edge('rules_actors','rules','actors',414,210,180,210,NAVY,'B')
txt(230,196,160,'判断を方向付ける',17.5,10,NAVY)
edge('actors_rules','actors','rules',180,235,414,235,NAVY,'B')
txt(225,238,170,'実践で維持・見直し',17.5,10,NAVY)
line(110,246,110,270,NAVY,1.2,'B')
edge('actors_config','actors','configuration',110,270,218,270,NAVY,'B')
txt(116,254,95,'選択・設計・運用',17.5,10,NAVY)
line(218,264,195,264,NAVY,1.2,'B');line(195,264,195,251,NAVY,1.2,'B');line(195,251,150,251,NAVY,1.2,'B')
edge('config_actors','configuration','actors',150,251,150,246,NAVY,'B')
txt(225,250,165,'可能な行為を制約',17.5,10,NAVY)
line(430,246,430,276,NAVY,1.2,'B')
edge('rules_config','rules','configuration',430,276,378,276,NAVY,'B')
txt(440,250,124,'設計・運用の前提',17.5,10,NAVY)
line(378,292,550,292,NAVY,1.2,'B')
edge('config_rules','configuration','rules',550,292,550,246,NAVY,'B')
txt(400,279,139,'技術と基準の調整',17.5,10,NAVY)
line(20,169,20,280,NAVY,1.2,'B')
edge('quantum_config','quantum_candidate','configuration',20,280,218,280,NAVY,'B')
txt(35,286,175,'計算能力・情報の候補',17.5,10,NAVY)
txt(15,310,564,'図1は理論上の枠組みであり、主体・規則の作用は未検証。下方の経路図は実線＝保存計算内の確認、破線＝条件付き接続、点線＝未検証である。',17,16,MUTED)
section(334,'2 方法：二経路の定量分析と文献による検討')
txt(15,350,564,METHOD_INPUT,20,18)
txt(15,370,564,METHOD_ROUTE,21,29,BLUE)
txt(15,402,564,METHOD_MATERIAL,21,29,ORANGE)
section(441,'3 結果：経路1の統計と経路2の追加解析')
rect(15,459,269,196,'#F1F6FA');rect(310,459,269,196,'#FAF3ED')
txt(20,464,259,'① 配送計画：方式・規模別の解品質',23,12,BLUE,True)
txt(315,464,259,'② 材料評価：追加解析と進捗',23,12,ORANGE,True)
def mini(nid,x,y,w,s,c,status):
 rect(x,y,w,22,'#FFFFFF',c if status!='C' else RULE);txt(x+2,y+2,w-4,s,18,18,c)
 nodes.append(dict(id=nid,x=x,y=y,w=w,h=22,body=s,status=status))
for nid,x,s,status in [('scope',20,'探索範囲 S','B'),('candidate',108,'CPU理想計算\nで候補取得','A'),('adopt',196,'古典側の検証\n採用は未確認','C')]:mini(nid,x,480,78,s,BLUE,status)
edge('route_search','scope','candidate',98,491,108,491,BLUE,'B');edge('route_check','candidate','adopt',186,491,196,491,BLUE,'A')
for nid,x,s,status in [('design',315,'設計への利用\n（未検証）','C'),('mass',403,'設計仮定と\n部材質量収支','B'),('DC',491,'走行総質量\n→ DC応答','A')]:mini(nid,x,480,78,s,ORANGE,status)
edge('material_use','design','mass',393,491,403,491,ORANGE,'C');edge('material_DC','mass','DC',481,491,491,491,ORANGE,'B')
txt(315,506,254,'設計仮定から計算する。',18.5,10,ORANGE)
edge('model_entry','symbolic_inputs','mass',442,506,442,502,ORANGE,'B')
txt(20,508,259,RESULT_ROUTE,18.5,19)
txt(20,529,259,'相対差100ΔJ/JC［%］：入力間平均±標準偏差［ポイント］',17.5,10,BLUE)
# Same data unit in every cell: per-input 10-measurement mean, then input-wise descriptives.
rows=list(csv.DictReader((OUT/'evidence/SCALE_METHOD_STATISTICS.csv').open(encoding='utf-8-sig')))
colx=[20,43,66,132,200];colw=[23,23,66,68,74]
heads=['先数\nn','入力\nN','限定5/隣接1\n（各条件同値）','GM-QAOA\n層2','GM-QAOA\n層3']
for x,w,s in zip(colx,colw,heads):txt(x,542,w,s,17.5,17,BLUE,True)
for i,n in enumerate([3,4,5,25,100,125]):
 y=562+i*11;rr={r['config']:r for r in rows if int(r['delivery_stops'])==n}
 line(20,y-1,274,y-1,RULE,.4)
 vals=[str(n),rr['MEAN_P2']['inputs']]
 for cfg,digits in [('MEAN_P2',3),('GROVER_P2',1),('GROVER_P3',1)]:
  a=rr[cfg];vals.append(f"{float(a['mean_relative_percent']):.{digits}f}±{float(a['SD_relative_points']):.{digits}f}")
 for x,w,s in zip(colx,colw,vals):txt(x,y,w,s,18.5,10)
txt(20,633,259,RESULT_ROUTE_DISTRIBUTION,19,19)
txt(315,524,259,'計算・検算済み（保存記録）',22,12,ORANGE,True)
txt(315,539,259,RESULT_MATERIAL_PROGRESS,20.5,43)
txt(315,584,259,'HOLD：実用入力・完成パック',22,12,ORANGE,True)
txt(315,600,259,RESULT_MATERIAL_HOLD,20.5,29)
txt(315,633,259,RESULT_MATERIAL_MODEL,18.5,19)
section(664,'4 評価：比較単位・不確実性・適用範囲')
txt(15,681,564,EVALUATION,21,42)
section(731,'5 議論：社会技術システムへの組込み条件')
txt(15,748,564,DISCUSSION,22,45)
txt(15,793,564,'補足：方式・規模別分布、再標本化感度、入力採用台帳、計算進捗の出典を同梱する。',16.5,8,MUTED)
refs=[b['text'] for b in old_blocks if b['text'].startswith(tuple('['+str(i)+'] ' for i in range(1,7)))]
for i,s in enumerate(refs):txt(15+(i%2)*291,803+(i//2)*8,273,s,14,7)
P.prs._element.sldSz.set('type','custom')
notes=Presentation(str(SRC/'poster.pptx')).slides[0].notes_slide.notes_text_frame.text
P.save(notes+'\n今回：A1縦594×841mmを維持。経路1はStep5のΔJ=JQ-JCに統一し、入力内10測定平均から方式/規模別相対差の平均と入力間SDを示した。限定5と隣接1は各条件の数値が一致することを保存表で照合した。中央値/IQR、P5/P95と既存再標本化区間は補足へ収録し、旧JC-JQの区間を符号反転してStep5点推定と照合した。区間は実配送母集団CIではない。材料はt08_t09_final_adoptionの完了記録と実用入力/完成パックHOLDを区別する。具体的材料効果量を主結果へ戻していない。新しい科学実験、学習、solver、SUMO、bootstrapは実行していない。')
(OUT/'evidence/SYSTEM_STRUCTURE.json').write_text(json.dumps(dict(nodes=nodes,edges=edges),ensure_ascii=False,indent=2))
(OUT/'evidence/SECTION_PROSE.json').write_text(json.dumps(SECTIONS,ensure_ascii=False,indent=2))
def svg(crop=False):
 v='0 128 594 200' if crop else '0 0 594 841';out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{v}" width="594mm" height="{200 if crop else 841}mm"><rect width="594" height="841" fill="white"/>']
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
print('Built A1 portrait: saved statistical evaluation + material progress/HOLD')
