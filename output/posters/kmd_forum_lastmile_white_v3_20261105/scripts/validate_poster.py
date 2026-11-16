"""Validate the final PPTX export, including every rendered text block."""
from pathlib import Path
from zipfile import ZipFile
import csv,hashlib,json,re,unicodedata
import pymupdf as fitz
from pptx import Presentation

O=Path(__file__).resolve().parents[1]
stem='KMD_Forum_都市内ラストマイル配送計画_A1縦_白地モデル図版'
ppt=O/f'{stem}.pptx';pdf=O/f'{stem}.pdf'
P=Presentation(ppt);D=fitz.open(pdf);page=D[0];mm=72/25.4
checks=[]
def ck(name,condition,detail=''):
    checks.append(dict(check=name,passed=bool(condition),detail=str(detail)))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
ck('one slide and one page',len(P.slides)==1 and len(D)==1)
ck('PPTX exact A1 portrait',P.slide_width==594*36000 and P.slide_height==841*36000)
ck('PDF A1 portrait',abs(page.rect.width/mm-594)<.02 and abs(page.rect.height/mm-841)<.02,
   f'{page.rect.width/mm:.6f} x {page.rect.height/mm:.6f} mm')
ck('editable native tables',sum(sh.has_table for sh in P.slides[0].shapes)==3)
ck('no rasterized slide content',len(page.get_images())==0)
graphs=json.loads((O/'evidence/DIAGRAM_EDGES.json').read_text())
nodes=json.loads((O/'evidence/DIAGRAM_NODES.json').read_text())
ck('editable depot-customer closed tour',len(graphs['model'])==4)
ck('comparison and adoption pipeline',len(graphs['pipeline'])==9)
ck('future decomposition pipeline',len(graphs['multi'])==3)
ck('adoption failure returns to classical baseline',any(e['source']=='decision' and e['target']=='fallback' for e in graphs['pipeline']))
ck('every diagram node has a single-line label',len(nodes)==16 and all('\n' not in n['text'] for n in nodes))
layout=json.loads((O/'evidence/LAYOUT.json').read_text())
missing=[];geometry=[];overlap=[]
for b in layout:
    r=fitz.Rect(b['x']*mm,b['y']*mm,(b['x']+b['w'])*mm,(b['y']+b['h'])*mm)
    # Small tolerance accommodates baseline metrics and no intentional overlaps.
    read=page.get_text(clip=r+(-2,-2,2,3))
    if norm(b['text']) not in norm(read):missing.append(dict(tag=b['tag'],expected=b['text'],rendered=read))
    if not page.rect.contains(r):geometry.append(b['tag'])
for j,a in enumerate(layout):
    ar=fitz.Rect(a['x'],a['y'],a['x']+a['w'],a['y']+a['h'])
    for b in layout[j+1:]:
        br=fitz.Rect(b['x'],b['y'],b['x']+b['w'],b['y']+b['h'])
        r=ar&br
        if not r.is_empty and r.width>.5 and r.height>.5:overlap.append((a['tag'],b['tag']))
ck('all text recovered within its intended box',not missing,f'{len(layout)} text/cell blocks; missing={len(missing)}')
ck('all intended boxes inside A1',not geometry,geometry)
ck('no overlapping text or cell boxes',not overlap,overlap)
oob=[]
for b in page.get_text('blocks'):
    if b[0]<-.5 or b[1]<-.5 or b[2]>page.rect.width+.5 or b[3]>page.rect.height+.5:oob.append(b[:5])
ck('actual rendered glyphs inside A1',not oob,oob)
ck('Japanese fonts embedded',all('NotoSansJP' in f[3] for f in page.get_fonts()),page.get_fonts())
spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
ck('all rendered text is black',all(s['color']==0 for s in spans),sorted(set(s['color'] for s in spans)))
fills=[d['fill'] for d in page.get_drawings() if d.get('fill') is not None]
ck('no navy or other colored backgrounds',all(max(c)-min(c)<.001 for c in fills))
ck('primary-source URLs remain printed',all(s in page.get_text() for s in ['j-m-t.co.jp/terminal/keihin.html','yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html']))
labels={b['id']:b for b in layout if b['tag'].startswith('label:')}
ck('no automatic wrapping in diagram labels',all('\n' not in labels[n['text_shape_id']]['rendered'] for n in nodes))

data=json.loads((O/'evidence/POSTER_DATA.json').read_text())
tables={r['tag']:r for r in json.loads((O/'evidence/TABLES.json').read_text())}
results=tables['results']['rows']
ck('displayed classical mean',all(r[2]==f"{data['classical_mean_s']:,.3f}" for r in results[1:]))
ck('displayed overall candidate mean',results[-1][3]==f"{data['candidate_mean_s']:,.3f}")
ck('displayed overall signed and absolute delta',results[-1][4]==f"+{data['delta_mean_s']:,.3f}" and results[-1][5]==f"{data['absolute_mean_s']:,.3f}")
ck('four future scales marked unexecuted',all(r[-1]=='計画・未実施' for r in tables['extension']['rows'][1:]))
ck('no EV or battery-material scope in poster',all(t not in (O/'evidence/POSTER_TEXT.txt').read_text() for t in ['EV','電池材料','車両質量','DC電力量']))
sourcechanges=[]
for r in csv.DictReader((O/'evidence/SOURCE_MANIFEST.csv').open()):
    h=hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()
    if h!=r['sha256']:sourcechanges.append(r['path'])
ck('all referenced original files preserved',not sourcechanges,sourcechanges)

validation=dict(checks=checks,missing_text=missing,outside_page=geometry,overlaps=overlap,
                actual_glyphs_outside=oob,pdf_page_mm=[page.rect.width/mm,page.rect.height/mm])
(O/'evidence/VALIDATION.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2))
with (O/'evidence/VALIDATION.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=['check','passed','detail']);w.writeheader();w.writerows(checks)
for suffix,rect in [('model',(12,152,582,355)),('pipeline',(12,357,582,550)),('results',(12,555,582,693)),('plan',(12,693,582,840))]:
    page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),clip=fitz.Rect([z*mm for z in rect]),alpha=False).save(O/'render'/f'{suffix}_detail.png')
print(json.dumps(dict(checks=len(checks),failed=[r for r in checks if not r['passed']],missing=missing),ensure_ascii=False,indent=2))
if not all(r['passed'] for r in checks):raise SystemExit(1)
