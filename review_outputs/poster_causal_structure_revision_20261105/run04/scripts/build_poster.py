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
SRC=OUT.parent/'run03'
old_blocks=json.loads((SRC/'poster_layout.json').read_text());old_nodes={n['id']:n for n in json.loads((SRC/'evidence/SYSTEM_STRUCTURE.json').read_text())['nodes']}
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
section(75,'1 目的')
txt(15,94,564,PURPOSE,22,30)
# Retain the socio-technical structure as the primary analytical frame.
txt(15,132,564,'図1 社会技術システムとしての分析枠組み [5]',24,13,NAVY,True)
rect(190,149,389,188,'#F7FAFC',RULE)
st('社会的機能：',205,155,359,22,12,NAVY,True)
oldnode('actors',205,180,145,53,NAVY)
oldnode('rules',415,180,150,53,NAVY)
oldnode('configuration',280,275,210,53,NAVY)
edge('rules_actors','rules','actors',415,208,350,208,NAVY,'B')
txt(355,188,56,'判断を\n方向付ける',16.5,18,NAVY)
edge('actors_rules','actors','rules',350,233,415,233,NAVY,'B')
txt(355,236,56,'実践で維持\n・見直し',16.5,18,NAVY)
line(205,202,198,202,NAVY,1.2,'B');line(198,202,198,300,NAVY,1.2,'B')
edge('actors_config','actors','configuration',198,300,280,300,NAVY,'B')
st('選択・設計・運用',202,287,74,17.5,10,NAVY)
line(280,288,265,288,NAVY,1.2,'B')
edge('config_actors','configuration','actors',265,288,265,233,NAVY,'B')
st('可能な行為を制約',272,254,112,17.5,10,NAVY)
line(505,233,505,300,NAVY,1.2,'B')
edge('rules_config','rules','configuration',505,300,490,300,NAVY,'B')
st('設計・運用の',512,251,60,17.5,18,NAVY)
line(490,316,555,316,NAVY,1.2,'B')
edge('config_rules','configuration','rules',555,316,555,233,NAVY,'B')
st('技術と基準の調整',494,301,58,17.5,10,NAVY)
rect(15,181,150,131,'#EDF3F7',RULE)
st('導入候補の量子計算',21,187,138,23,12,NAVY,True)
st('① 計画の候補探索',21,209,138,22,11,BLUE,True)
st('CPU理想モデルで検討',21,225,138,19,10,BLUE)
st('② 材料の物性評価',21,250,138,22,11,ORANGE,True)
st('本研究では未実行',21,266,138,19,10,ORANGE)
st('計算能力・評価情報の候補',21,291,138,18,10,MUTED)
line(165,247,178,247,NAVY,1.2,'B');line(178,247,178,316,NAVY,1.2,'B')
edge('quantum_config','quantum_candidate','configuration',178,316,280,316,NAVY,'B')
st('利用する構成を検討',198,303,78,17.5,10,NAVY)
txt(15,342,564,'図1は理論に基づく関係図である。主体・規則の実際の相互作用を、今回の数値実験で実証したものではない。',17,16,MUTED)
# Explicit prose for each required academic section.
section(365,'2 方法：二経路の定量分析と文献による検討')
txt(15,381,564,METHOD_INPUT,20,18)
txt(15,402,564,METHOD_ROUTE,21,29,BLUE)
txt(15,435,564,METHOD_MATERIAL,21,29,ORANGE)
section(475,'3 結果：保存計算とモデル解析で確認したこと')
rect(15,493,269,127,'#F1F6FA')
rect(310,493,269,127,'#FAF3ED')
txt(20,498,259,'配送計画',23,12,BLUE,True)
txt(315,498,259,'電池材料・走行計算',23,12,ORANGE,True)
txt(403,513,171,'今回の入力',17.5,9,ORANGE)
def mini(nid,x,y,w,s,c,status):
 rect(x,y,w,25,'#FFFFFF',c if status!='C' else RULE);txt(x+3,y+3,w-6,s,19,21,c)
 nodes.append(dict(id=nid,x=x,y=y,w=w,h=25,body=s,status=status))
for nid,x,s,status in [('scope',20,'探索範囲 S','B'),('candidate',108,'CPU理想計算\nで候補取得','A'),('adopt',196,'古典側の検証\n採用は未確認','C')]:mini(nid,x,529,78,s,BLUE,status)
edge('route_search','scope','candidate',98,542,108,542,BLUE,'B')
edge('route_check','candidate','adopt',186,542,196,542,BLUE,'A')
for nid,x,s,status in [('design',315,'設計への利用\n（未検証）','C'),('mass',403,'設計仮定と\n部材質量収支','B'),('DC',491,'走行総質量\n→ DC応答','A')]:mini(nid,x,529,78,s,ORANGE,status)
edge('material_use','design','mass',393,542,403,542,ORANGE,'C')
edge('material_DC','mass','DC',481,542,491,542,ORANGE,'B')
edge('model_entry','symbolic_inputs','mass',442,522,442,529,ORANGE,'B')
txt(20,565,259,RESULT_ROUTE,21,49)
txt(315,565,259,RESULT_MATERIAL,21,49)
section(631,'4 評価：比較基準と、結果を解釈できる範囲')
txt(15,648,564,EVALUATION,21,46)
section(706,'5 議論：社会技術システムへの組込み条件')
txt(15,723,564,DISCUSSION,22,61)
# Evidence coding applies to the small pathways; the main map is theoretical.
txt(15,786,564,'経路図：実線A＝保存計算／モデル内の確認、破線B＝条件付き接続、点線C＝未検証。',17,9,MUTED)
refs=[b['text'] for b in old_blocks if b['text'].startswith(tuple('['+str(i)+'] ' for i in range(1,7)))]
for i,s in enumerate(refs):txt(15+(i%2)*291,803+(i//2)*8,273,s,14,7)
P.prs._element.sldSz.set('type','custom')
notes=Presentation(str(SRC/'poster.pptx')).slides[0].notes_slide.notes_text_frame.text.split('\n版式変更：')[0]
P.save(notes+'\n改稿：目的・方法・結果・評価・議論を独立した見出しと文章で記述した。内容は既存の保存結果と科学的採用判断に基づく。新規の科学実験・社会調査は追加していない。')
(OUT/'evidence/SYSTEM_STRUCTURE.json').write_text(json.dumps(dict(nodes=nodes,edges=edges),ensure_ascii=False,indent=2))
(OUT/'evidence/SECTION_PROSE.json').write_text(json.dumps(SECTIONS,ensure_ascii=False,indent=2))
def svg(crop=False):
 v='0 128 594 231' if crop else '0 0 594 841';out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{v}" width="594mm" height="{231 if crop else 841}mm"><rect width="594" height="841" fill="white"/>']
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
print('Built A1 portrait with five explicit prose sections')
