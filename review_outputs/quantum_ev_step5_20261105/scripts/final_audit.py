from pathlib import Path
from fractions import Fraction as F
import json,hashlib,re,sys,unicodedata,zipfile,collections
import numpy as np,pandas as pd
from docx import Document
from lxml import etree
O=Path(__file__).resolve().parents[1];R=O.parents[1];S4=R/'review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043';D=O/'data';E=O/'evidence';out=[]
def ck(name,ok,detail=''):
 out.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=str(detail)));assert bool(ok),(name,detail)
s=json.loads((D/'SUMMARY.json').read_text());d=pd.read_csv(D/'B_PLAN_GAPS_36800.csv');stats=pd.read_csv(D/'GAP_DESCRIPTIVE_STATISTICS.csv');ips=pd.read_csv(D/'INPUT_UNIT_STATISTICS.csv');doc=Document(O/'THESIS_STEP5_REVISED.docx');base=Document(S4/'THESIS_STEP4_INTEGRATED_TRIAL.docx')
ck('all plan lattice',len(d)==36800 and d.groupby('problem_id').size().eq(80).all() and not d.duplicated(['problem_id','config_id','measurement_rep']).any())
ck('all rational signs and absolutes',all(np.sign(float(F(x.delta_fraction)))==np.sign(x.delta_s) and abs(float(F(x.delta_fraction)))-x.abs_delta_s<1e-9 for x in d.itertuples()))
ck('relative gaps use greedy',np.allclose(d.relative_gap_percent,100*d.delta_s/d.J_greedy_s,rtol=1e-12,atol=1e-10))
ck('all zero denominators excluded correctly',d.J_greedy_s.gt(0).all())
ck('all complete counts',s['improved']==0 and s['equal']==28200 and s['worsened']==8600 and s['equal']+s['worsened']==len(d))
ck('balanced input average',abs(d.delta_s.mean()-d.groupby('problem_id').delta_s.mean().mean())<1e-9)
ck('mean relative distinguished from ratio',abs(s['mean_relative_gap_percent']-s['ratio_of_means_percent'])>6)
ck('full levels with requested statistics',all(x in stats.level.unique() for x in ['all_plans','by_input','by_config','by_measurement_rep','by_input_config']) and all(x in stats.columns for x in ['n','mean','median','sd','min','max','q1','q3','p05','p95']))
ck('no artificial inferential sample count',s['n_groups']==25 and s['n_parents']==26)
ck('operation return identity',np.allclose(d.candidate_return_s-d.greedy_return_s,d.delta_s,atol=1e-8))
ck('last customer completion distinct',abs(d.last_delivery_difference_s.mean()-439.5389235845553)<1e-8 and d.last_delivery_difference_s.lt(-1e-9).sum()==180)
ck('all common horizons and unmeasured actual outcomes',d.customer_horizon_within_fraction_candidate.eq(1).all() and d.customer_horizon_within_fraction_greedy.eq(1).all() and d.contractual_on_time_rate.isna().all() and d.actual_start_time_s.isna().all())
ck('strict greedy fallback conditional arithmetic',d.strict_greedy_adoption_delta_s.eq(0).all())
ck('old source scientific evidence byte-preserved',hashlib.sha256((E/'STEP4_EVIDENCE_DECISIONS.md').read_bytes()).hexdigest()==hashlib.sha256((R/'review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654/STEP4_EVIDENCE_DECISIONS.md').read_bytes()).hexdigest())
# Archived source blocks and all original mathematical structures.
def text(e):return ''.join(e.xpath('.//w:t/text() | .//m:t/text()'))
def split(doc):
 xs=list(doc._element.body);i=next(i for i,e in enumerate(xs) if text(e)=='付録B　元原稿の保全記録' and e.xpath('./w:pPr/w:pStyle/@w:val')==['Heading1']);return xs[:i],xs[i:]
cur,arc=split(doc);_,oldarc=split(base)
def sig(es):return [(text(e),len(e.xpath('.//m:oMath')),len(e.xpath('.//w:drawing'))) for e in es if etree.QName(e).localname!='sectPr']
ck('historical appendix exact content signature',sig(arc)==sig(oldarc))
ck('86 equations retained',len(doc._element.xpath('.//m:oMath'))==len(base._element.xpath('.//m:oMath'))==86)
with zipfile.ZipFile(S4/'THESIS_STEP4_INTEGRATED_TRIAL.docx') as z0,zipfile.ZipFile(O/'THESIS_STEP5_REVISED.docx') as z1:
 oldimages={hashlib.sha256(z0.read(n)).hexdigest() for n in z0.namelist() if n.startswith('word/media/')};newimages={hashlib.sha256(z1.read(n)).hexdigest() for n in z1.namelist() if n.startswith('word/media/')};ck('all inherited image bytes present',oldimages<=newimages)
current='\n'.join(text(e) for e in cur);(E/'CURRENT_TEXT.txt').write_text(current)
ck('current sign convention unified','主差ΔJ=J_C−J_Q' not in current and 'ΔJ=J_candidate−J_greedy' in current)
ck('abstract and conclusion scientific limits','主材料入力として未採用' in current and '実用入力として未適格' in current and '契約上の定時配達率' in current)
ck('RQ0 1 2 I answered',all(x in current for x in ['RQ0に対して','RQ1に対して','RQ2に対して','RQIに対して']))
ck('Robinson year suffix and held content labels','[OR24;内容HOLD] S Robinson (2008b)' in current and '[OR30;内容HOLD] S Robinson (2008a)' in current)
# Citations used in new prose have actual bibliography records.
refs=set(re.findall(r'\[(L\d+|OR\d+|S5-L\d+)[;\]]',current));ck('new citations resolved',set(['OR03','OR02','OR36','OR37','L14','S5-L01','OR24','OR30'])<=refs)
# Final PDF metadata and meaningful text comparison. Special glyph extraction is separately reviewed visually.
sys.path.insert(0,str(R/'review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python'));import fitz
pdf=fitz.open(O/'THESIS_STEP5_REVISED.pdf');N=lambda t:re.sub(r'\s+','',unicodedata.normalize('NFKC',t)).replace('\u00ad','')
lines=[N(l) for p in pdf for l in p.get_text().splitlines()];pdfnorm=''.join(l for l in lines if not l.startswith('KMD修士研究') and not l.startswith('Step5revised'))
flat=lambda t:N(t).replace('→','').replace('−','')
current_prose=[]
for p in doc.paragraphs:
 if p.text=='付録B　元原稿の保全記録' and p.style.name=='Heading 1':break
 if len(p.text)>20 and not p._p.xpath('.//m:oMath') and not p._p.xpath('.//w:bookmarkStart[starts-with(@w:name,"toc_")]'):
  current_prose.append(p.text)
matching=[];miss=[]
for t in current_prose:
 ok=flat(t) in flat(pdfnorm);matching.append(dict(text_start=t[:100],characters=len(t),PDF_text_found=ok,normalization='NFKC, whitespace/header/footer/soft-hyphen removed; minus/arrow extraction order excluded for visual review'))
 if not ok:miss.append(t)
pd.DataFrame(matching).to_csv(E/'DOCX_PDF_PROSE_MATCH.csv',index=False)
ck('DOCX PDF current prose normalized agreement',not miss,str(miss[:2]))
ck('PDF all required numerical claims',all(N(t) in pdfnorm for t in ['441.790609','22.243524','7.473770','622.305258','439.538924','7,435.747703']))
pa=json.loads((O/'render/PAGE_AUDIT.json').read_text());ck('PDF all pages no replacements',len(pa)==len(pdf) and sum(x['replacement_characters'] for x in pa)==0)
ck('PDF no page overflow',json.loads((O/'render/OUTSIDE_PAGE_BLOCKS.json').read_text())==[])
ck('all four new figures have captions and references',all('図4-'+str(i) in current for i in range(1,5)) and len(pd.read_csv(E/'NEW_FIGURE_REGISTER.csv'))==4)
# Cell values in current tables, including exact full numeral forms; exclusion of ASCII <= related glyph order only.
cellmatches=[]
for el in cur:
 if etree.QName(el).localname=='tbl':
  for tc in el.xpath('.//w:tc'):
   t=text(tc)
   if t.strip():cellmatches.append(dict(text=t,found=flat(t) in flat(pdfnorm)))
pd.DataFrame(cellmatches).to_csv(E/'DOCX_PDF_TABLE_MATCH.csv',index=False)
# Mathematical/vector glyphs in some inherited table cells are extracted in a different order; inspect all numeric-only cells.
numeric_cells=[x for x in cellmatches if re.fullmatch(r'[0-9,.%\-+〜／ ]+',x['text'])]
ck('all current numeric table cells found',all(x['found'] for x in numeric_cells))
# All declared final audit observations are emitted, not a blanket scientific PASS.
pd.DataFrame(out).to_csv(E/'FINAL_AUTOMATED_CHECKS.csv',index=False)
(E/'FINAL_AUTOMATED_RESULT.json').write_text(json.dumps(dict(checks=len(out),failures=0,pages=len(pdf),current_prose_paragraphs=len(current_prose),numeric_table_cells=len(numeric_cells),all_table_cells=len(cellmatches),all_table_cells_exact_normalized_found=sum(x['found'] for x in cellmatches),math_objects=86,scope='same agent separated audit; not independent peer review; visual and native Word holds separate'),ensure_ascii=False,indent=2))
print('final automated',len(out),'PASS',len(pdf),'pages; prose',len(current_prose))
