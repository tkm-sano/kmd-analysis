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
# A1 portrait reflow. All scientific wording is taken from the preceding landscape version.
SRC=OUT.parent/'run02'
old_blocks=json.loads((SRC/'poster_layout.json').read_text())
old_graph=json.loads((SRC/'evidence/SYSTEM_STRUCTURE.json').read_text())
old_nodes={n['id']:n for n in old_graph['nodes']}
def source(prefix):
 items=[b['text'] for b in old_blocks if b['text'].startswith(prefix)]
 assert len(items)==1,(prefix,len(items))
 return items[0]
def st(prefix,x,y,w,pt,h,c=INK,b=False):return txt(x,y,w,source(prefix),pt,h,c,b)
def oldnode(nid,x,y,w,h,c):
 n=old_nodes[nid];node(nid,x,y,w,h,n['title'],n['body'],n['status'],c)
def small(nid,x,y,w,c):
 n=old_nodes[nid];rect(x,y,w,49,'#F1F6FA' if c==BLUE else '#FAF3ED',c if n['status']!='C' else RULE)
 txt(x+3,y+3,w-6,n['title'],20,11,c,True,tag=nid+'_title')
 txt(x+3,y+17,w-6,n['body'],20,30,tag=nid+'_body')
 nodes.append(dict(id=nid,x=x,y=y,w=w,h=49,title=n['title'],body=n['body'],status=n['status']))
rect(0,0,W,66,'#EDF3F7')
st('量子計算がEV配送',15,7,564,40,20,NAVY,True)
st('配送計画と電池材料評価を介した',15,29,564,34,17,NAVY,True)
st('佐野巧馬',15,51,564,22,11,NAVY)
st('研究目的：',15,74,564,23,25,NAVY)
st('1 社会技術システム',15,111,564,28,14,NAVY,True)
line(15,127,579,127,NAVY,1.2)
# Portrait system map: same three analytic dimensions, six interactions, and quantum input.
rect(190,135,389,232,'#F7FAFC',RULE)
st('社会的機能：',205,141,359,25,13,NAVY,True)
oldnode('actors',205,174,145,62,NAVY)
oldnode('rules',415,174,150,62,NAVY)
oldnode('configuration',280,292,210,62,NAVY)
edge('rules_actors','rules','actors',415,204,350,204,NAVY,'B')
txt(355,185,56,source('判断を方向付ける').replace('判断を','判断を\n'),16.5,18,NAVY)
edge('actors_rules','actors','rules',350,236,415,236,NAVY,'B')
txt(355,240,56,source('実践で維持').replace('維持','維持\n'),16.5,18,NAVY)
line(205,202,198,202,NAVY,1.2,'B');line(198,202,198,316,NAVY,1.2,'B')
edge('actors_config','actors','configuration',198,316,280,316,NAVY,'B')
st('選択・設計・運用',202,302,74,17.5,10,NAVY)
line(280,304,265,304,NAVY,1.2,'B')
edge('config_actors','configuration','actors',265,304,265,236,NAVY,'B')
st('可能な行為を制約',272,267,112,17.5,10,NAVY)
line(505,236,505,316,NAVY,1.2,'B')
edge('rules_config','rules','configuration',505,316,490,316,NAVY,'B')
st('設計・運用の',512,257,60,17.5,18,NAVY)
line(490,341,555,341,NAVY,1.2,'B')
edge('config_rules','configuration','rules',555,341,555,236,NAVY,'B')
st('技術と基準の調整',494,324,58,17.5,10,NAVY)
rect(15,188,150,136,'#EDF3F7',RULE)
st('導入候補の量子計算',21,194,138,23,12,NAVY,True)
st('① 計画の候補探索',21,215,138,22,11,BLUE,True)
st('CPU理想モデルで検討',21,231,138,19,10,BLUE)
st('② 材料の物性評価',21,255,138,22,11,ORANGE,True)
st('本研究では未実行',21,271,138,19,10,ORANGE)
st('計算能力・評価情報の候補',21,301,138,18,10,MUTED)
line(165,256,178,256,NAVY,1.2,'B');line(178,256,178,341,NAVY,1.2,'B')
edge('quantum_config','quantum_candidate','configuration',178,341,280,341,NAVY,'B')
st('利用する構成を検討',198,326,78,17.5,10,NAVY)
st('Geels [5]',15,373,564,17,18,MUTED)
st('2 定量分析：',15,398,564,24,13,NAVY,True)
st('下図の実線A：',15,414,564,17,17,MUTED)
# The two analyses are stacked, retaining the blue and brown path colours and original content.
st('① 配送計画：',15,435,564,24,13,BLUE,True)
st('古典処理と理想量子モデル',15,451,564,17.5,9,BLUE)
small('route_scope',15,468,160,BLUE)
small('route_candidate',208,468,160,BLUE)
small('route_adoption',401,468,178,BLUE)
edge('route_search','route_scope','route_candidate',175,493,208,493,BLUE,'B')
edge('route_verification','route_candidate','route_adoption',368,493,401,493,BLUE,'A')
st('観測：支持の制約',15,524,564,22,12,BLUE,True)
st('限定交換の全460入力',15,539,564,21,28)
methods=source('① 時間窓なし、').split('\n')
assert len(methods)==2
txt(15,568,564,methods[0],18,18)
st('② 材料評価：',15,594,564,24,13,ORANGE,True)
st('B 今回は設計仮定から',208,610,371,17.5,9,ORANGE)
small('material_adoption',15,627,160,ORANGE)
small('material_balance',208,627,160,ORANGE)
small('material_DC',401,627,178,ORANGE)
edge('material_use','material_adoption','material_balance',175,652,208,652,ORANGE,'C')
edge('material_mass_DC','material_balance','material_DC',368,652,401,652,ORANGE,'B')
edge('symbolic_entry','symbolic_assumptions','material_balance',288,620,288,627,ORANGE,'B')
st('解析：質量差の相殺',15,683,564,22,12,ORANGE,True)
st('研究で置いた容量一定',15,698,564,21,28)
txt(15,727,564,methods[1],18,18)
line(15,750,579,750,NAVY,1.1)
st('研究の位置付け：',15,753,564,24,12,NAVY,True)
st('量子計算の寄与を、',15,769,564,22,21,NAVY)
refs=[b['text'] for b in old_blocks if b['text'].startswith(tuple('['+str(i)+'] ' for i in range(1,7)))]
assert len(refs)==6
for i,s in enumerate(refs):txt(15+(i%2)*291,803+(i//2)*8,273,s,14,7)
oldprs=Presentation(str(SRC/'poster.pptx'));notes=oldprs.slides[0].notes_slide.notes_text_frame.text
P.prs._element.sldSz.set('type','custom')
P.save(notes+'\n版式変更：A1縦594×841mm。主図は縦用に再配置し、定量分析を上下に配置した。本文と数値は横版から保持した。')
(OUT/'evidence/SYSTEM_STRUCTURE.json').write_text(json.dumps(dict(nodes=nodes,edges=edges),ensure_ascii=False,indent=2))
def svg(crop=False):
 v='0 108 594 283' if crop else '0 0 594 841';out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{v}" width="594mm" height="{283 if crop else 841}mm"><rect width="594" height="841" fill="white"/>']
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
print('A1 portrait built, wording sourced from run02')
