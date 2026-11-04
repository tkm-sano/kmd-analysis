from pathlib import Path
import json,re,sys,collections
from zipfile import ZipFile
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parents[1]/'thesis_docx_integration_20261103/run01/rendering_tools/python'))
# absolute repo-relative read-only renderer dependency
sys.path.insert(0,str(Path('/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')))
import fitz
D=fitz.open(R/'poster.pdf');P=D[0];mm=72/25.4
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
with ZipFile(R/'poster.pptx') as z:
 xml=ET.fromstring(z.read('ppt/slides/slide1.xml'));pres=ET.fromstring(z.read('ppt/presentation.xml'))
 texts=[''.join(t.itertext()) for t in xml.findall('.//a:t',ns)]
 para=[''.join(t.text or '' for t in p.findall('a:r/a:t',ns)) for p in xml.findall('.//a:p',ns)]
 sizes=pres.find('p:sldSz',ns)
 shapes=xml.findall('.//p:sp',ns);pictures=xml.findall('.//p:pic',ns)
 overflow=[]
 for sp in shapes:
  xf=sp.find('p:spPr/a:xfrm',ns)
  if xf is None:continue
  off=xf.find('a:off',ns);ext=xf.find('a:ext',ns)
  x,y,cx,cy=[int(v) for v in [off.get('x'),off.get('y'),ext.get('cx'),ext.get('cy')]]
  if min(x,y)<0 or x+cx>int(sizes.get('cx')) or y+cy>int(sizes.get('cy')):overflow.append(sp.find('p:nvSpPr/p:cNvPr',ns).get('name'))
def norm(s):return re.sub(r'\s+','',s).replace('−','-').replace('〜','～')
actual=norm(P.get_text())
missing=[s for s in para if s and norm(s) not in actual]
spans=[s for b in P.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans'] if s['text'].strip()]
outside=[s['text'] for s in spans if s['bbox'][0]<12*mm or s['bbox'][2]>582*mm or s['bbox'][1]<8*mm or s['bbox'][3]>833*mm]
# independently check column encroachment in the body, omitting full-width header/footer
cross=[]
for s in spans:
 x0,y0,x1,y1=s['bbox'];y=y0/mm
 if 300<y<695 and x0/mm<295 and x1/mm>295:cross.append(s['text'])
report={'page_count':len(D),'page_width_mm':round(P.rect.width/mm,3),'page_height_mm':round(P.rect.height/mm,3),'native_shapes':len(shapes),'native_textboxes':len(xml.findall('.//p:txBody',ns)),'raster_pictures':len(pictures),'shape_bounds_violations':overflow,'source_paragraphs':len([s for s in para if s]),'paragraphs_not_found_in_pdf':missing,'text_outside_print_margins':outside,'text_crossing_column_gap':cross,'visual_review':'pending','renderer':'LibreOffice Impress 24.2.7.2'}
(R/'render/FINAL_VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
