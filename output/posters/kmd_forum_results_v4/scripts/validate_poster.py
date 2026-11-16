"""Validate the final PPTX export, including every rendered text block."""
from pathlib import Path
from zipfile import ZipFile
import csv,hashlib,json,re,unicodedata
import pymupdf as fitz
from pptx import Presentation

O=Path(__file__).resolve().parents[1]
stem='v4_KMD_Forum_量子技術と物流配送計画_A1縦'
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
ck('only the model assumptions remain as a native table',sum(sh.has_table for sh in P.slides[0].shapes)==1)
ck('no rasterized slide content',len(page.get_images())==0)
graphs=json.loads((O/'evidence/DIAGRAM_EDGES.json').read_text())
nodes=json.loads((O/'evidence/DIAGRAM_NODES.json').read_text())
ck('editable depot-customer closed tour',len(graphs['model'])==4)
ck('comparison and adoption pipeline',len(graphs['pipeline'])==6)
q=graphs['qaoa']
ck('QAOA algorithm is explicit',len(q)==9 and {'q_init','q_cost','q_mix','q_eval','q_update','q_fixed','q_restate','q_sample','q_best'}.issubset({n['key'] for n in nodes}))
ck('QAOA classical adjustment returns to state preparation',any(e['source']=='q_update' and e['target']=='q_init' for e in q))
ck('QAOA final sampling follows fixed settings',any(e['source']=='q_fixed' and e['target']=='q_restate' for e in q) and any(e['source']=='q_restate' and e['target']=='q_sample' for e in q))
ck('every diagram node has a single-line label',len(nodes)==19 and all('\n' not in n['text'] for n in nodes))
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
ck('algorithm primary references printed',all(s in page.get_text() for s in ['1411.4028','Hadfield','Eidenbenz']))
labels={b['id']:b for b in layout if b['tag'].startswith('label:')}
ck('no automatic wrapping in diagram labels',all('\n' not in labels[n['text_shape_id']]['rendered'] for n in nodes))

data=json.loads((O/'evidence/POSTER_DATA.json').read_text())
tables={r['tag']:r for r in json.loads((O/'evidence/TABLES.json').read_text())}
figure=json.loads((O/'evidence/RESULT_FIGURE.json').read_text())
results=figure['rows']
ck('displayed classical mean',all(abs(r['classical']-data['classical_mean_s'])<1e-8 for r in results))
ck('displayed overall candidate mean',abs(results[-1]['qaoa']-data['candidate_mean_s'])<1e-8)
ck('displayed overall signed and absolute delta',abs(results[-1]['delta']-data['delta_mean_s'])<1e-8 and abs(results[-1]['absolute']-data['absolute_mean_s'])<1e-8)
by_id={s.shape_id:s for s in P.slides[0].shapes}
ck('eight editable bars use a common zero-based scale',len(figure['bars'])==8 and all(abs(by_id[b['shape_id']].width/36000-figure['axis_width_mm']*b['value_s']/figure['axis_max_s'])<.001 for b in figure['bars']))
ck('unfixed scale table removed','extension' not in tables and all(t not in (O/'evidence/POSTER_TEXT.txt').read_text() for t in ['500先','1,000先','2,000先','3,000先','3～5先から','5・10台','20・30台']))
future=json.loads((O/'evidence/FUTURE_ITEMS.json').read_text())
bullets=[b for b in layout if b['kind']=='bullet']
ck('six investigation and revalidation items appear last',len(future)==len(bullets)==6 and min(b['y'] for b in bullets)>=759 and sum(s.startswith('調査：') for s in future)==2 and sum(s.startswith('再検証：') for s in future)==4)
ck('future items use editable native bullet paragraphs',sum(bool(sh.has_text_frame and sh.text_frame.paragraphs[0]._p.get_or_add_pPr().find('{http://schemas.openxmlformats.org/drawingml/2006/main}buChar') is not None) for sh in P.slides[0].shapes)==6)
inp=json.loads((O/'evidence/INPUT_SOURCE.json').read_text())
source=Presentation(inp['path']);source_tables=[sh.table for sh in source.slides[0].shapes if sh.has_table]
source_results=next(t for t in source_tables if '比較件数' in t.cell(0,1).text)
ck('specified v3 numerical results retained',all([f"{r['n']:,}",f"{r['classical']:,.3f}",f"{r['qaoa']:,.3f}",f"+{r['delta']:,.3f}",f"{r['absolute']:,.3f}"]==[source_results.cell(j+1,k).text for k in range(1,6)] for j,r in enumerate(results)))
audits=list(csv.DictReader((O/'evidence/LANGUAGE_AUDIT.csv').open()))
ck('language audit recorded against web and local primary sources',len(audits)>=15)
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
for suffix,rect in [('model',(12,132,582,325)),('pipeline',(12,328,582,431)),('qaoa',(12,433,582,559)),('results',(12,560,582,738)),('plan',(12,739,582,840))]:
    page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),clip=fitz.Rect([z*mm for z in rect]),alpha=False).save(O/'render'/f'{suffix}_detail.png')
print(json.dumps(dict(checks=len(checks),failed=[r for r in checks if not r['passed']],missing=missing),ensure_ascii=False,indent=2))
if not all(r['passed'] for r in checks):raise SystemExit(1)
