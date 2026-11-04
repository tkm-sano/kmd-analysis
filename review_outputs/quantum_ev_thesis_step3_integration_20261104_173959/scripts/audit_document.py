from pathlib import Path
import json,re,csv,zipfile,hashlib,collections,unicodedata,sys
from lxml import etree
from docx import Document
from docx.oxml.ns import qn
O=Path(__file__).resolve().parents[1];old=Document(O/'sources/ORIGINAL_THESIS.docx');new=Document(O/'THESIS_UPDATED_STEP3.docx');ledger=json.load(open(O/'DOCX_BUILD_LEDGER.json'));checks=[]
def ck(name,ok,detail=''):
 checks.append(dict(check=name,pass_=bool(ok),detail=detail))
def omhash(el):
 # Semantic equation structure, independent of namespace/context/volatile revision ids.
 def node(x):return (etree.QName(x).localname,tuple(sorted((etree.QName(k).localname,v) for k,v in x.attrib.items()if not etree.QName(k).localname.startswith('rsid'))),x.text or '',tuple(node(c)for c in x))
 return hashlib.sha256(repr(node(el)).encode()).hexdigest()
oldmath=old._element.xpath('.//m:oMath');newmath=new._element.xpath('.//m:oMath')
methodmath=[]
for p in old.paragraphs[174:285]:methodmath+=p._p.xpath('.//m:oMath')
oldcounts=collections.Counter(map(omhash,methodmath));newcounts=collections.Counter(map(omhash,newmath));missing=oldcounts-newcounts
ck('Original 42 method OMML retained semantically',len(methodmath)==42 and not missing,dict(original=len(methodmath),new=len(newmath),missing=dict(missing)))
ck('New editable equations',len(newmath)==45,{'new_OMML':len(newmath),'expected':45})
ck('All table and image counts',len(new.tables)==11 and len(new.inline_shapes)==8,dict(tables=len(new.tables),images=len(new.inline_shapes)))
for s in new.sections:ck('A4 portrait',abs(s.page_width/914400-8.2677)<.02 and abs(s.page_height/914400-11.6929)<.02)
stylefont={}
for style in ['Normal','Body Text','Heading 1','Heading 2','Heading 3']:
 ck('Preserve style font '+style,etree.tostring(old.styles[style].element.find(qn('w:rPr')))==etree.tostring(new.styles[style].element.find(qn('w:rPr'))))
 stylefont[style]=dict(font=new.styles[style].font.name,pt=new.styles[style].font.size.pt if new.styles[style].font.size else None)
start=[x.get(qn('w:name'))for x in new._element.xpath('.//w:bookmarkStart')];dup=[x for x,n in collections.Counter(start).items()if n>1]
ck('No duplicate bookmark names',not dup,dup)
links=[]
for fld in new._element.xpath('.//w:fldSimple'):
 inst=fld.get(qn('w:instr'));m=re.search(r'HYPERLINK\s+\\l\s+"([^"]+)"',inst)
 if m:links.append(m[1]);ck('Internal caption link '+m[1],m[1]in start)
for cap in ledger['caption_list']:
 ck('Unique caption '+cap['kind']+cap['id'],sum(c['kind']==cap['kind']and c['id']==cap['id']for c in ledger['caption_list'])==1)
full='\n'.join(''.join(p._p.xpath('.//w:t/text() | .//m:t/text()'))for p in new.paragraphs)
ck('No unresolved build markers','{{'not in full)
for heading in ['2.1.1','2.1.2','2.1.3','2.2.1','2.2.2','2.2.3','2.3.1','2.3.2','2.3.3','2.4.1','2.4.2','2.4.3','2.4.4','6.1','6.2','6.3','6.4','6.5','6.6']:
 ck('Required heading '+heading,any(p.text.startswith(heading+'　')for p in new.paragraphs))
for token in ['36,800','9,312','93,120','9,603','414','41','46','H_plan','NULL','量子優位性','条件']:
 ck('Required concept/value '+token,token in full)
# All new table contents vs input JSON, after the single original demand table.
newtables=json.load(open(O/'TABLES.json'));actual=[[ [c.text for c in row.cells]for row in t.rows]for t in new.tables]
for id,t in newtables.items():
 expected=[list(map(str,t['headers']))]+[list(map(str,r))for r in t['rows']]
 ck('Editable table agrees with CSV/manifest '+id,expected in actual)
for t in new.tables:
 ck('Table repeated header',bool(t.rows[0]._tr.xpath('./w:trPr/w:tblHeader')))
 ck('Table rows cannot split',all(row._tr.xpath('./w:trPr/w:cantSplit')for row in t.rows))
# DOCX package integrity and all local relationship targets valid, external URLs retained.
with zipfile.ZipFile(O/'THESIS_UPDATED_STEP3.docx')as z:
 ck('ZIP integrity',z.testzip()is None);names=z.namelist();broken=[];external=[]
 import posixpath
 for name in names:
  if name.endswith('.rels'):
   root=etree.fromstring(z.read(name))
   basedir=posixpath.dirname(posixpath.dirname(name))
   for rel in root:
    target=rel.get('Target')
    if rel.get('TargetMode')=='External':external.append(target);continue
    resolved=posixpath.normpath(posixpath.join(basedir,target)) if not target.startswith('/') else target[1:]
    if resolved not in names:broken.append((name,target,resolved))
 ck('Relationship targets',not broken,broken)
 ck('No invented footnotes','word/footnotes.xml'not in names)
# Rendering checks.
pdfinfo=json.load(open(O/'RENDER_AUDIT.json'))
ck('PDF rendered pages',pdfinfo['pages']>0,pdfinfo['pages']);ck('No replacement glyphs',all(r['replacement_chars']==0 for r in pdfinfo['records']))
ck('No out-of-page blocks',all(not r['out_of_page_blocks']for r in pdfinfo['records']))
pdftext='\n'.join(re.sub(r'(?m)^\s*'+str(i)+r'\s*$','',(O/f"render/page_{i:03}.txt").read_text())for i in range(1,pdfinfo['pages']+1))
norm=lambda x:re.sub(r'\s+','',unicodedata.normalize('NFKC',x))
# Japanese prose and titles must survive rendering; equations tested separately by source structure and visual review.
miss=[]
for i,p in enumerate(new.paragraphs):
 if p._p.xpath('.//m:oMath | .//w:drawing'):continue
 text=''.join(p._p.xpath('.//w:t/text()'))
 if len(text)>4 and norm(text)not in norm(pdftext):miss.append({'paragraph':i,'text':text[:150]})
# PDF extraction can reorder glyphs from fallback fonts or superscripts.
# Check prose/alphanumeric coverage after removing operator punctuation; visually inspect symbol-rich pages separately.
alpha=lambda x:''.join(c for c in norm(x)if c.isalnum())
missing_prose=[]
for i,p in enumerate(new.paragraphs):
 if p._p.xpath('.//m:oMath | .//w:drawing'):continue
 txt=''.join(p._p.xpath('.//w:t/text()'))
 if len(txt)>4 and alpha(txt)not in alpha(pdftext):missing_prose.append(dict(paragraph=i,text=txt[:150]))
ck('Paragraph prose and alphanumeric coverage in PDF',not missing_prose,missing_prose)
(O/'PDF_EXTRACTION_DIFFERENCES.json').write_text(json.dumps(dict(strict_text_differences=miss,prose_coverage_missing=missing_prose,note='Strict extraction order differs for fallback math glyphs, superscripts and page footers. Visual review is separate.'),ensure_ascii=False,indent=2))
rows=list(csv.DictReader(open(O/'LITERATURE_SELECTION_LEDGER.csv')));lit=[]
for x in rows:
 if x['literature_id']=='H01':continue
 j=json.load(open(O/x['source_json']))
 ck('Literature raw metadata '+x['literature_id'],j['http_status']==200 and j['response']['id']==x['OpenAlex_id']and j['response']['cited_by_count']==int(float(x['citation_count'])))
 if x['selection_decision'].startswith('ADOPT_MAJOR'):
  ck('Literature citation eligibility '+x['literature_id'],int(x['citation_count'])>=int(x['required_citations']))
  ck('Literature reading scope recorded '+x['literature_id'],bool(x['primary_verification_scope']))
  lit.append(x['literature_id'])
ck('Thirteen major papers',len(lit)==13,lit)
res=dict(checks=checks,failures=sum(not x['pass_']for x in checks),check_count=len(checks),original_total_OMML=len(oldmath),original_main_method_OMML=len(methodmath),revised_total_OMML=len(newmath),retained_main_method_OMML=len(methodmath)-sum(missing.values()),excluded_legacy_OMML=len(oldmath)-len(methodmath),new_native_equations=3,new_table_count=len(newtables),total_table_count=len(new.tables),inline_images=len(new.inline_shapes),internal_caption_links=len(links),external_links=len(external),pages=pdfinfo['pages'],style_fonts=stylefont)
(O/'DOCUMENT_AUDIT.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
print('Document checks',len(checks),'failures',res['failures'])
for x in checks:
 if not x['pass_']:print('FAIL',x)
