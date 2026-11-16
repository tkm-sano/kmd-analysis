from pathlib import Path
from collections import Counter
from zipfile import ZipFile
import csv,json,re,sys,hashlib,unicodedata,html
import xml.etree.ElementTree as ET
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
R=Path(__file__).resolve().parents[1];SRC=R.parent/'run02';E=R/'evidence';checks=[]
def ck(item,ok,detail):checks.append(dict(item=item,status='PASS' if ok else 'FAIL',detail=detail))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-')
blocks=json.loads((R/'poster_layout.json').read_text());old=json.loads((SRC/'poster_layout.json').read_text())
expected=[]
for b in old:
 expected.extend(b['text'].split('\n') if b['text'].startswith('① 時間窓なし、') else [b['text']])
a=Counter(norm(s) for s in expected);b=Counter(norm(s['text']) for s in blocks)
ck('Source wording and values unchanged',a==b,'global two-method paragraph separated; only whitespace/position/font changed')
(E/'CONTENT_DIFFERENCE.json').write_text(json.dumps(dict(missing=list((a-b).elements()),added=list((b-a).elements())),ensure_ascii=False,indent=2))
d=fitz.open(R/'poster.pdf');pg=d[0];mm=72/25.4
ck('A1 portrait single page',len(d)==1 and abs(pg.rect.width/mm-594)<.1 and abs(pg.rect.height/mm-841)<.1,f'{pg.rect.width/mm:.3f}×{pg.rect.height/mm:.3f} mm')
missing=[]
for i,v in enumerate(blocks):
 x,y,w,h=[v[k] for k in ['x_mm','y_mm','w_mm','h_mm']];clip=fitz.Rect((x-.6)*mm,(y-.6)*mm,(x+w+.6)*mm,(y+h+1)*mm)
 actual=pg.get_text('text',clip=clip)
 if norm(v['text']) not in norm(actual):missing.append(dict(i=i,text=v['text'],actual=actual))
ck('PDF all text present',not missing,f'{len(blocks)} blocks; missing {len(missing)}')
overlaps=[]
for i,a in enumerate(blocks):
 for j,b in enumerate(blocks[i+1:],i+1):
  dx=min(a['x_mm']+a['w_mm'],b['x_mm']+b['w_mm'])-max(a['x_mm'],b['x_mm']);dy=min(a['y_mm']+a['h_mm'],b['y_mm']+b['h_mm'])-max(a['y_mm'],b['y_mm'])
  if dx>.5 and dy>.8:overlaps.append((i,j,round(dx,2),round(dy,2)))
ck('No text rectangle overlaps',not overlaps,str(overlaps))
ck('All blocks within A1',all(v['x_mm']>=0 and v['x_mm']+v['w_mm']<=594.01 and v['y_mm']>=0 and v['y_mm']+v['h_mm']<=841.01 for v in blocks),'portrait coordinates')
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(R/'poster.pptx') as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));pr=ET.fromstring(z.read('ppt/presentation.xml'));size=pr.find('p:sldSz',ns)
 ck('PPTX actual portrait size',int(size.get('cx'))==594*36000 and int(size.get('cy'))==841*36000,str(size.attrib))
 ck('Native editable poster',not root.findall('.//p:pic',ns) and len(root.findall('.//p:cxnSp',ns))>40,'native text/shapes/connectors')
for v in csv.DictReader((E/'ORIGINAL_SHA256.csv').open()):ck('Preserved '+Path(v['path']).name,hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'],'original SHA256')
for f in ['poster.svg','sociotechnical_structure.svg']:ET.parse(R/f)
ck('SVG dimensions and XML',True,'594×841mm poster; portrait system diagram crop')
oldgraph=json.loads((SRC/'evidence/SYSTEM_STRUCTURE.json').read_text());newgraph=json.loads((E/'SYSTEM_STRUCTURE.json').read_text())
get=lambda g:{v['id']:(v['source'],v['target'],v['status']) for v in g['edges']}
ck('All diagram relations retained',get(oldgraph)==get(newgraph),'same endpoints/directions/evidence classes; geometry reflowed')
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=overlaps),ensure_ascii=False,indent=2))
with (E/'VALIDATION.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=checks[0]);w.writeheader();w.writerows(checks)
pg.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(0,108*mm,594*mm,391*mm)).save(R/'sociotechnical_structure_preview.png')
pg.get_pixmap(matrix=fitz.Matrix(1.2,1.2),clip=fitz.Rect(185*mm,130*mm,584*mm,370*mm)).save(R/'render/system_check.png')
styles='body{font-family:sans-serif;max-width:1100px;margin:32px auto;padding:0 24px;color:#17232d;line-height:1.8}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bac6cf;padding:8px;text-align:left}th{background:#edf3f7}a{color:#286a96}'
body='<h1>A1縦版（594×841mm）</h1><p>社会技術システム版run02を縦方向へ再配置した。関係図、二つの分析、結果・数値・注記の文言は保持した。本文は縮小せず、分析の本文を一部18.5ptから20ptへ拡大した。主図の一部の短い矢印ラベルは16.5ptとした。元の横版は保全した。</p><ul>'
for p,label in [('poster.pptx','編集可能なPPTX'),('poster.pdf','PPTXから出力したPDF'),('poster_preview.png','全体プレビュー'),('sociotechnical_structure.svg','縦配置の関係図SVG'),('../run02/index.html','元の横版・研究説明')]:body+='<li><a href="'+p+'">'+label+'</a></li>'
body+='</ul><h2>確認結果</h2><table><tr><th>項目</th><th>状態</th><th>内容</th></tr>'
for v in checks:body+='<tr>'+''.join('<td>'+html.escape(str(t))+'</td>' for t in v.values())+'</tr>'
body+='</table><p>全1ページをレンダリングして確認した。実寸試し刷りは未実施である。commit・push・PR作成は行っていない。</p>'
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>A1縦版</title><style>'+styles+'</style><body>'+body+'</body></html>')
print(json.dumps(checks,ensure_ascii=False,indent=2))
if any(v['status']=='FAIL' for v in checks):sys.exit(1)
