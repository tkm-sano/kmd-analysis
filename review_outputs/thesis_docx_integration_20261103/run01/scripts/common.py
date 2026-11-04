from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from collections import Counter
from lxml import etree as E
import csv,json,hashlib,sys,re,subprocess,time,resource,os
R=Path('/home/takuma/kmd-analysis');O=Path(__file__).resolve().parents[1];P=R/'review_outputs/thesis_results_interpretation_20261102/run01';F=R/'review_outputs/no_sumo_full_analysis_20261102/run01';SRC=R/'tmp_RsrchMstrDc_1026_revised.docx';OUT=R/'tmp_RsrchMstrDc_1026_results_integrated.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
def sha(p):
 with Path(p).open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()
def rows(p):
 with Path(p).open() as h:return list(csv.DictReader(h))
def js(p):return json.loads(Path(p).read_text())
def dump(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n')
def table(n,data):
 dest=O/n;dest.parent.mkdir(exist_ok=True,parents=True);keys=list(dict.fromkeys(k for x in data for k in x)) if data else ['status']
 with dest.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=keys);w.writeheader();w.writerows(data)
def md(n,s):(O/n).write_text(s.strip()+'\n')
def xmltext(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def structure(p):
 from docx import Document
 d=Document(p)
 with ZipFile(p) as z:
  root=E.fromstring(z.read('word/document.xml'));book=root.xpath('.//w:bookmarkStart/@w:name',namespaces=NS);fields=[]
  for part in z.namelist():
   if part.startswith('word/') and part.endswith('.xml'):
    rr=E.fromstring(z.read(part))
    for q in rr.xpath('.//w:instrText | .//w:fldSimple',namespaces=NS):fields.append({'part':part,'instruction':q.text or q.get('{'+NS['w']+'}instr')})
  return {'path':str(p),'sha256':sha(p),'body_paragraphs':len(d.paragraphs),'all_paragraphs':len(root.xpath('.//w:p',namespaces=NS)),'tables':len(d.tables),'inline_shapes':len(d.inline_shapes),'OMML_equations':len(root.xpath('.//m:oMath',namespaces=NS)),'footnote_refs':len(root.xpath('.//w:footnoteReference',namespaces=NS)),'endnote_refs':len(root.xpath('.//w:endnoteReference',namespaces=NS)),'bookmarks':book,'bookmark_count':len(book),'hyperlinks':len(root.xpath('.//w:hyperlink',namespaces=NS)),'hyperlink_anchors':root.xpath('.//w:hyperlink/@w:anchor',namespaces=NS),'fields':fields,'section_breaks':len(root.xpath('.//w:sectPr',namespaces=NS)),'explicit_page_breaks':len(root.xpath('.//w:br[@w:type="page"]',namespaces=NS)),'header_parts':[x for x in z.namelist() if re.match(r'word/header\d+\.xml$',x)],'footer_parts':[x for x in z.namelist() if re.match(r'word/footer\d+\.xml$',x)],'parts':z.namelist(),'headings':[{'index0':i,'style':p.style.name,'text':p.text} for i,p in enumerate(d.paragraphs) if p.style.name.startswith('Heading')],'paragraph_styles':dict(Counter(p.style.name for p in d.paragraphs)),'sections':[{'width':s.page_width,'height':s.page_height,'left':s.left_margin,'right':s.right_margin,'top':s.top_margin,'bottom':s.bottom_margin} for s in d.sections]}
