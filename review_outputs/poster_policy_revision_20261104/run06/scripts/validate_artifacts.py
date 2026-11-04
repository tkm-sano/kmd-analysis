from pathlib import Path
import sys,csv,json,re,hashlib,unicodedata
from zipfile import ZipFile
import xml.etree.ElementTree as ET
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
R=Path(__file__).resolve().parents[1];checks=[]
def check(name,ok,detail):checks.append(dict(check=name,status='PASS' if ok else 'FAIL',detail=detail))
def normalize(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-')
blocks=json.loads((R/'poster_layout.json').read_text());doc=fitz.open(R/'poster.pdf');page=doc[0];mm=72/25.4
check('pages',len(doc)==1,str(len(doc)))
check('A1_landscape_mm',abs(page.rect.width/mm-841)<.2 and abs(page.rect.height/mm-594)<.2,str((page.rect.width/mm,page.rect.height/mm)))
missing=[]
for i,b in enumerate(blocks):
 x,y,w,h=[b[k] for k in ['x_mm','y_mm','w_mm','h_mm']]
 clip=fitz.Rect((x-.6)*mm,(y-.6)*mm,(x+w+.6)*mm,(y+h+1)*mm)
 actual=normalize(page.get_text('text',clip=clip));expect=normalize(b['text'])
 if expect not in actual:missing.append(dict(index=i,text=b['text'],extracted=page.get_text('text',clip=clip)))
check('all_text_blocks_present',not missing,f'{len(blocks)} blocks; missing {len(missing)}')
(R/'evidence/RENDER_TEXT_MISMATCHES.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2))
# Shapes are genuine editable text/geometry, not flattened poster images.
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(R/'poster.pptx') as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));pics=root.findall('.//p:pic',ns);texts=root.findall('.//a:t',ns)
check('editable_native_poster',len(pics)==0 and len(texts)>100,f'{len(pics)} raster shapes; {len(texts)} text runs')
check('font_minimum',min(b['font_pt'] for b in blocks)>=14,f'min {min(b["font_pt"] for b in blocks)}pt; bibliography14, body18.5–21, chart ticks16')
# Pairwise occupied text rectangles; excludes intended backgrounds/rules.
overlaps=[]
for i,a in enumerate(blocks):
 for j,b in enumerate(blocks[i+1:],i+1):
  dx=min(a['x_mm']+a['w_mm'],b['x_mm']+b['w_mm'])-max(a['x_mm'],b['x_mm'])
  dy=min(a['y_mm']+a['h_mm'],b['y_mm']+b['h_mm'])-max(a['y_mm'],b['y_mm'])
  if dx>.5 and dy>.8:overlaps.append((i,j,round(dx,2),round(dy,2),a['text'][:20],b['text'][:20]))
check('text_rectangle_overlaps',not overlaps,str(overlaps))
check('all_text_within_slide',all(0<=b['x_mm'] and b['x_mm']+b['w_mm']<=841.01 and 0<=b['y_mm'] and b['y_mm']+b['h_mm']<=594.01 for b in blocks),'native block coordinates')
check('three_column_gutters',all(not(15<b['y_mm']<487) or b['y_mm']<78 or any(abs(b['x_mm']-x)<.01 and b['x_mm']+b['w_mm']<=x+261.01 for x in []) or b['x_mm']+b['w_mm']<=276.01 or (b['x_mm']>=290 and b['x_mm']+b['w_mm']<=551.01) or b['x_mm']>=565 for b in blocks),'column boundaries 15–276 /290–551 /565–826 mm')
# Preserve initial pinned sources and completed late evidence snapshots; other ongoing work is outside this scope.
preservation=[]
for inv in [R/'00_SOURCE_INVENTORY.csv',R/'evidence/LATE_SOURCE_INVENTORY.csv']:
 for v in csv.DictReader(inv.open(encoding='utf-8-sig')):
  p=Path(v['path']);actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'MISSING'
  preservation.append(dict(path=str(p),expected=v['sha256'],actual=actual,status='PASS' if actual==v['sha256'] else 'FAIL'))
check('pinned_original_preservation',all(v['status']=='PASS' for v in preservation),f'{len(preservation)} pinned originals')
# Also compare the two directly reused large source tables to the preserved run05 inventory hashes.
for v in csv.DictReader((R.parent/'run05/00_SOURCE_INVENTORY.csv').open()):
 if Path(v['path']).name in ['B_PLAN_REFERENCES_36800.csv','B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv']:
  check('raw_source_'+Path(v['path']).name,hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'],'same as run05 pre-edit SHA256')
for name,rs in [('ARTIFACT_CHECKS.csv',checks),('ORIGINAL_PRESERVATION.csv',preservation)]:
 with (R/'evidence'/name).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=rs[0]);w.writeheader();w.writerows(rs)
(R/'evidence/ARTIFACT_QA.json').write_text(json.dumps(dict(checks=checks,failed=sum(v['status']=='FAIL' for v in checks),text_blocks=len(blocks),pinned_sources=len(preservation),visual_review='see final review; real PPTX rendered through LibreOffice'),ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))
if any(v['status']=='FAIL' for v in checks):sys.exit(1)
