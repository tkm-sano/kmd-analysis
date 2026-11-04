from pathlib import Path
import re,json,csv,copy,hashlib,collections
from docx import Document
from docx.shared import Inches,Cm,Pt,RGBColor
from docx.enum.text import WD_LINE_SPACING,WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from lxml import etree
O=Path(__file__).resolve().parents[1]
doc=Document(O/'sources/ORIGINAL_THESIS.docx'); orig=list(doc.paragraphs); body=doc._element.body
original_elements=list(body); originals={id(p._p):i for i,p in enumerate(orig)}
sects=copy.deepcopy(body.sectPr)
for el in list(body):
 if el.tag!=qn('w:sectPr'):body.remove(el)
# Single A4 portrait for revised body; same fonts and original style definitions.
for tag in ['w:headerReference','w:footerReference']:pass
pg=sects.find(qn('w:pgSz'));pg.set(qn('w:w'),'11906');pg.set(qn('w:h'),'16838');pg.attrib.pop(qn('w:orient'),None)
body.replace(body.sectPr,sects)
tables=json.loads((O/'TABLES.json').read_text());figs=json.loads((O/'FIGURES.json').read_text())
bid=1; bookmarks={};used=[];log=[];figure_entries=[];captions=[];equations=[]
def fmt(p,head=0,small=False):
 f=p.paragraph_format;f.line_spacing=Pt(12 if small else (24 if head else 18));f.line_spacing_rule=WD_LINE_SPACING.AT_LEAST
 f.space_before=Pt(12 if head else 0);f.space_after=Pt(6);f.keep_with_next=bool(head);f.widow_control=True
 if head==1:f.page_break_before=True
 if small:
  for r in p.runs:r.font.size=Pt(8)
 # drop inherited section transitions, preserve math and actual run formatting
 for x in p._p.xpath('./w:pPr/w:sectPr'):x.getparent().remove(x)
 return p

def para(text='',style=None,small=False):
 p=doc.add_paragraph(style=style);p.add_run(text);fmt(p,small=small);return p

def bookmark(p,name):
 global bid
 start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(bid));start.set(qn('w:name'),name)
 end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(bid));bid+=1
 p._p.insert(0,start);p._p.append(end);bookmarks[name]=p.text

def caption(text,kind,id):
 p=para(text);p.paragraph_format.keep_with_next=True
 for r in p.runs:r.bold=True;r.font.size=Pt(10)
 name=kind+'_'+id.replace('-','_');bookmark(p,name);captions.append(dict(kind=kind,id=id,text=text,bookmark=name));return p

def table(id):
 x=tables[id];cp=caption(x['caption'],'Table',id)
 if id=='2-1':cp.paragraph_format.page_break_before=True
 t=doc.add_table(rows=1,cols=len(x['headers']));t.autofit=False
 width=15.7/len(x['headers'])
 for col in t.columns:col.width=Cm(width)
 for i,h in enumerate(x['headers']):t.rows[0].cells[i].text=str(h)
 for row in x['rows']:
  for cell,value in zip(t.add_row().cells,row):cell.text=str(value)
 for ri,row in enumerate(t.rows):
  trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
  if ri==0:trpr.append(OxmlElement('w:tblHeader'))
  for c in row.cells:
   c.width=Cm(width)
   for p in c.paragraphs:
    fmt(p,small=True);p.paragraph_format.space_after=Pt(3);p.paragraph_format.keep_with_next=False
    for run in p.runs:run.font.size=Pt(7.5 if len(x['headers'])>=6 else 8.5);run.bold=ri==0
   if ri==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EFF4');c._tc.get_or_add_tcPr().append(sh)
 pr=t._tbl.tblPr;b=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  z=OxmlElement('w:'+side);z.set(qn('w:val'),'single');z.set(qn('w:sz'),'4');z.set(qn('w:color'),'808080');b.append(z)
 pr.append(b);para('注：'+x['note']+' 出典：'+x['source'],small=True)

def fig(id):
 x=figs[id];p=doc.add_paragraph();fmt(p);p.paragraph_format.keep_with_next=True
 p.add_run().add_picture(str(O/x['image']),width=Cm(15.6));caption(x['caption'],'Figure',id)
 para('注：'+x['note']+' 出典：'+x['source'],small=True);figure_entries.append(dict(id=id,path=x['image']))

def copyrange(a,b):
 # Copy intervening tables as well as paragraph XML, retaining native OMML/relationships.
 left=original_elements.index(orig[a]._p);right=original_elements.index(orig[b]._p)
 for el in original_elements[left:right]:
  new=copy.deepcopy(el)
  for s in new.xpath('.//w:sectPr'):s.getparent().remove(s)
  body.insert(len(body)-1,new)
  if el.tag==qn('w:p'):
   from docx.text.paragraph import Paragraph
   p=Paragraph(new,doc._body);idx=originals[id(el)];used.append(idx)
   head=2 if p.style.name.startswith('Heading 2') else 0;fmt(p,head=head)
   swaps={210:[('3.8節','付録B.2')],225:[('3.13節','3.7節')],233:[('主指標は','この旧系列の補助指標は')],241:[('図3-1','図B-1')],243:[('原図ID 図3-1','原図ID 図3-1、改訂図B-1')]}
   for old,newtext in swaps.get(idx,[]):
    for r in p.runs:
     if old in r.text:r.text=r.text.replace(old,newtext)
   if idx in [196,258,241]:
    kind,cap_id=('Table','3-2') if idx==196 else ('Figure','3-2' if idx==258 else 'B-1')
    bookmark(p,kind+'_'+cap_id.replace('-','_'));captions.append(dict(kind=kind,id=cap_id,text=p.text,bookmark=kind+'_'+cap_id.replace('-','_')))
   for shape in p._p.xpath('.//wp:extent'):
    if int(shape.get('cx'))>int(Cm(15.6)):
     ratio=int(Cm(15.6))/int(shape.get('cx'));shape.set('cx',str(int(Cm(15.6))));shape.set('cy',str(int(int(shape.get('cy'))*ratio)))
   if new.xpath('.//w:drawing'):p.paragraph_format.keep_with_next=True
  elif el.tag==qn('w:tbl'):
   from docx.table import Table
   tt=Table(new,doc._body)
   for ri,row in enumerate(tt.rows):
    row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    if ri==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    for cell in row.cells:
     for p in cell.paragraphs:fmt(p,small=True)
 log.append({'source_paragraph_start':a,'source_paragraph_end_exclusive':b,'disposition':'copied native XML; section transitions removed; only documented crossreferences/legacy indicator wording changed'})

def equation(id,text):
 p=doc.add_paragraph();fmt(p);p.paragraph_format.line_spacing=Pt(24)
 om=OxmlElement('m:oMathPara');m=OxmlElement('m:oMath');r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;r.append(t);m.append(r);om.append(m);p._p.append(om)
 p.add_run('　('+id+')');bookmark(p,'Eq_'+id.replace('-','_'));equations.append({'id':id,'text':text})

def md(name):
 for block in (O/'drafts'/name).read_text().strip().split('\n\n'):
  block=block.strip()
  if not block:continue
  if block=='{{ORIGINAL_EVIDENCE_LOCATORS}}':
   copyrange(447,449);copyrange(450,461)
   ids={'M%02d'%i for i in range(1,12)}|{'Q01','Q02','R03'}
   for i,p in enumerate(orig):
    m=re.match(r'^([MRQ]\d\d)：',p.text)
    if m and m.group(1) in ids and 463<=i<580:copyrange(i,i+2)
   continue
  m=re.fullmatch(r'\{\{ORIGINAL:(\d+):(\d+)\}\}',block)
  if m:copyrange(*map(int,m.groups()));continue
  m=re.fullmatch(r'\{\{(TABLE|FIG):([^}]+)\}\}',block)
  if m:(table if m[1]=='TABLE' else fig)(m[2]);continue
  m=re.fullmatch(r'\{\{EQ:([^|]+)\|(.+)\}\}',block)
  if m:equation(m[1],m[2]);continue
  m=re.match(r'^(#{1,3})\s+(.+)$',block,re.S)
  if m:
   level=len(m[1]);p=doc.add_paragraph(m[2],style='Heading '+str(level));fmt(p,head=level)
  else:para(block.replace('\n',' '))

p=para('慶應義塾大学大学院メディアデザイン研究科');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p=para('修士論文　独立改訂稿');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
for r in p.runs:r.font.size=Pt(20)
p=para('量子技術がEVラストマイル配送システムへ寄与する条件\n配送計画と材料・質量・電力量の二経路による検討');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p=para('2026年11月4日\nStep 1・Step 2の証拠照合と、今回のStep 3統合考察');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
para('本稿は元原稿を保全した独立改訂案である。正式採用・既存研究への統合は未実施である。')
md('ABSTRACT.md')
# Editable table of contents with actual static outline; no stale page numbers.
p=doc.add_paragraph('目次',style='Heading 1');fmt(p,head=1)
for title in ['要旨','1　序論','2　文献調査','3　研究方法','4　手続きと再現性の管理','5　研究結果','6　統合考察','7　結論','参考文献','付録A　入力・版・証拠への対応','付録B　旧小規模・時間窓あり系列の補助的仕様','付録C　主系列の全設定と診断条件','付録D　引用・図表・数式の管理範囲']:para(title)
for name in ['CHAPTER1.md','CHAPTER2.md','METHOD_INTRO.md']:md(name)
copyrange(180,199);md('METHOD_34.md');copyrange(202,211)
for name in ['METHOD_36.md','METHOD_37.md','METHOD_38.md']:md(name)
copyrange(244,270)
para('以下では旧古典460速度を共通にしたStep 2の連続感度と境界を評価する。現行Bの460入力との一対一対応や、地域道路網の実走行妥当性を前提としない。')
for name in ['METHOD_311.md','CHAPTER4.md','CHAPTER5.md','CHAPTER6.md','CHAPTER7.md']:md(name)
p=doc.add_paragraph('参考文献',style='Heading 1');fmt(p,head=1)
para('第2章の主要文献と、方法の再現に必要な技術文献を分けて示す。確認した内容範囲と採否は文献台帳に対応する。被引用数は参考文献の真偽・因果妥当性の指標ではない。')
rows=list(csv.DictReader((O/'LITERATURE_SELECTION_LEDGER.csv').open()))
for group,pred in [('主要文献',lambda x:x['selection_decision'].startswith('ADOPT_MAJOR')),('技術文献（被引用数基準の対象外）',lambda x:x['literature_id'].startswith('T'))]:
 p=doc.add_paragraph(group,style='Heading 2');fmt(p,head=2)
 for x in rows:
  if not pred(x):continue
  p=para(f"[{x['literature_id']}] {x['authors']}（{x['year']}）. {x['title']}. {x.get('publication_details','')} ")
  url=x['URL'] or x['DOI'];link=OxmlElement('w:hyperlink');link.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
  run=OxmlElement('w:r');pr=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'0563C1');pr.append(color);run.append(pr);t=OxmlElement('w:t');t.text=url;run.append(t);link.append(run);p._p.append(link)
md('APPENDICES.md')
# Native REF fields for body references to figures and tables. Cached display includes the label.
for p in doc.paragraphs:
 if any(c['text']==p.text for c in captions):continue
 for run in list(p.runs):
  text=run.text
  if not text or run._r.xpath('.//m:oMath | .//w:drawing'):continue
  matches=list(re.finditer(r'(図|表)([2356BC]-\d+)',text))
  valid=[m for m in matches if ('Figure' if m[1]=='図' else 'Table')+'_'+m[2].replace('-','_') in bookmarks]
  if not valid:continue
  parent=run._r.getparent();pos=parent.index(run._r);offset=0
  for m in valid:
   if m.start()>offset:
    rr=copy.deepcopy(run._r);tt=rr.find(qn('w:t'));tt.text=text[offset:m.start()];parent.insert(pos,rr);pos+=1
   fld=OxmlElement('w:fldSimple');name=('Figure' if m[1]=='図' else 'Table')+'_'+m[2].replace('-','_')
   # \n switches suppress caption descriptive text and reference the paragraph number; captions use manual numbers.
   # Use hyperlink field to caption bookmark, keeping exact manual number display (editable, does not expand to entire caption).
   fld.set(qn('w:instr'),' HYPERLINK \\l "'+name+'" ')
   rr=copy.deepcopy(run._r);rr.find(qn('w:t')).text=m[0];fld.append(rr);parent.insert(pos,fld);pos+=1;offset=m.end()
  if offset<len(text):
   rr=copy.deepcopy(run._r);rr.find(qn('w:t')).text=text[offset:];parent.insert(pos,rr)
  parent.remove(run._r)
# Source field/page headers retained; set updateFields to request consistent field displays.
settings=doc.settings.element
u=settings.find(qn('w:updateFields'))
if u is None:u=OxmlElement('w:updateFields');settings.append(u)
u.set(qn('w:val'),'true')
new=O/'THESIS_UPDATED_STEP3.docx';doc.save(new)
# Text export includes Office Math and hyperlinks/field cache.
textlines=[]
for el in doc._element.body:
 txt=''.join(el.xpath('.//w:t/text() | .//m:t/text()'))
 if txt:textlines.append(txt)
(O/'THESIS_SECTIONS_TRIAL.md').write_text('\n\n'.join(textlines))
(O/'DOCX_BUILD_LEDGER.json').write_text(json.dumps(dict(file=str(new),used_source_paragraphs=used,source_ranges=log,caption_list=captions,new_equations=equations,figures=figure_entries,bookmarks=bookmarks),ensure_ascii=False,indent=2))
print('Saved',new,'paras',len(doc.paragraphs),'tables',len(doc.tables),'images',len(doc.inline_shapes),'source paras',len(used))
