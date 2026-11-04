"""Pin old artifacts and extract DOCX paragraph/table anchors without saving DOCX."""
from evidence import *
from docx import Document
import re
def main():
 t=time.monotonic();manifest=js(F/'ARTIFACT_MANIFEST.json');pins=[]
 for x in manifest:use(F/x['path'],x['sha256']);pins.append({'path':str(F/x['path']),'sha256':x['sha256'],'role':'PREVIOUS_ANALYSIS_ARTIFACT'})
 for root in [F,D]:
  for p in sorted(root.glob('*.md')):use(p).read_text()
 for p in [R/'docs/QUANTITATIVE_GUIDE.md',R/'docs/research/RESEARCH_DESIGN_SUMMARY.md',R/'docs/research/THESIS_REVISION_AUDIT.md',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json',U/'docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md']:use(p).read_text()
 missing=[];paras=[];tables=[];headings=[];bib=[]
 if DOC.is_file():
  use(DOC);d=Document(DOC)
  inbib=False
  for i,p in enumerate(d.paragraphs):
   text=p.text.strip();style=p.style.name
   mathtext=' '.join(x.text or '' for x in p._p.xpath('.//m:t'));paras.append({'paragraph_index0':i,'style':style,'text':text,'OMML_math_text':mathtext})
   if text and (style.startswith('Heading') or (len(text)<95 and (re.match(r'^\d+(\.\d+)*[　\s]',text) or text in ['背景','目的','参考文献','方法','結論']))):headings.append({'paragraph_index0':i,'style':style,'heading':text})
   if text=='参考文献':inbib=True
   if text.startswith('付録A'):inbib=False
   if inbib and text:bib.append({'paragraph_index0':i,'reference_text':text})
  for ti,tab in enumerate(d.tables):
   for ri,row in enumerate(tab.rows):tables.append({'table_index0':ti,'row_index0':ri,'cells':json.dumps([c.text for c in row.cells],ensure_ascii=False)})
  body=[]
  for pi,x in enumerate(d.element.body):
   name=x.tag.rsplit('}',1)[-1];body.append({'body_child_index0':pi,'element':name,'paragraph_index0':sum(y.tag.endswith('}p') for y in list(d.element.body)[:pi]) if name=='p' else None,'table_index0':sum(y.tag.endswith('}tbl') for y in list(d.element.body)[:pi]) if name=='tbl' else None,'text':' '.join(x.itertext())[:200]})
  table('DOCX_BODY_ANCHORS.csv',body)
 else:missing.append(str(DOC))
 table('DOCX_PARAGRAPHS.csv',paras);table('DOCX_TABLES.csv',tables);table('DOCX_HEADINGS.csv',headings);table('DOCX_REFERENCES.csv',bib);doc('DOCX_READONLY_TEXT.md','\n\n'.join(f"[p{x['paragraph_index0']:03d}; {x['style']}] {x['text']}"+(f"\n\nOMML（線形抽出、Wordの数式配置とは別）: {x['OMML_math_text']}" if x['OMML_math_text'] else '') for x in paras if x['text'] or x['OMML_math_text']));table('BASELINE_PINNED_SOURCES.csv',pins+list(SOURCES.values()));dump('INITIAL_STATE.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'git_status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'git_diff':subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R,text=True),'docx_sha256':sha(DOC) if DOC.is_file() else None})
 finish('SOURCE',t,{'previous_analysis_artifacts':len(manifest),'hash_mismatches':0,'docx_exists':DOC.is_file(),'docx_paragraphs':len(paras),'docx_tables':len(d.tables) if DOC.is_file() else None,'headings':len(headings),'bibliography_paragraphs':len(bib),'missing_files':missing})
if __name__=='__main__':main()
