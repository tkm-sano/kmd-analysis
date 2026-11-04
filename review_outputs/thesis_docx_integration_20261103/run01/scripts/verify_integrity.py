"""Independent XML, source protection and keyed-value readback; no analysis reruns."""
from common import *
from docx import Document

def signature(e):return (e.tag,tuple(sorted(e.attrib.items())),(e.text or ''),tuple(signature(c) for c in e))
def root(p):
 with ZipFile(p) as z:return E.fromstring(z.read('word/document.xml'))
t=time.monotonic();old=root(SRC);new=root(OUT);checks=[]
def ck(n,a,b,loc=''):
 checks.append({'check':n,'expected':str(a),'actual':str(b),'locator':loc,'status':'PASS' if a==b else 'FAIL'})
ck('Original DOCX sha',js(O/'DOCX_STRUCTURE_BEFORE.json')['sha256'],sha(SRC))
for tag,label in [('m:oMath','original OMML'),('w:hyperlink','original hyperlink')]:
 a=Counter(signature(e) for e in old.xpath('.//'+tag,namespaces=NS));b=Counter(signature(e) for e in new.xpath('.//'+tag,namespaces=NS))
 for key,count in a.items():ck(label+' intact occurrences',True,b[key]>=count)
for n in ['bookmarkStart','bookmarkEnd']:
 a=old.xpath('.//w:'+n,namespaces=NS);b=new.xpath('.//w:'+n,namespaces=NS);mapped=Counter(tuple(sorted(x.attrib.items())) for x in b)
 for x in a:ck('original '+n,True,mapped[tuple(sorted(x.attrib.items()))]>=1)
# Original table cells and order within each table preserved, even when moved.
old_tables=old.xpath('.//w:tbl',namespaces=NS);new_tables=new.xpath('.//w:tbl',namespaces=NS)
for i,a in enumerate(old_tables):ck('original table XML preserved',True,any(signature(a)==signature(b) for b in new_tables),str(i))
with ZipFile(SRC) as z,ZipFile(OUT) as y:
 for n in z.namelist():ck('original OPC part retained',True,n in y.namelist(),n)
 for n in ['word/header1.xml','word/numbering.xml','word/fontTable.xml','word/theme/theme1.xml']:ck('original part semantic XML unchanged',signature(E.fromstring(z.read(n))),signature(E.fromstring(y.read(n))),n)
 oldrels=E.fromstring(z.read('word/_rels/document.xml.rels'));newrels=E.fromstring(y.read('word/_rels/document.xml.rels'))
 for x in oldrels:ck('old relationship retained',True,any(x.attrib==a.attrib for a in newrels),x.get('Id'))
 doc=Document(OUT);ck('document loads',True,len(doc.paragraphs)>610)
 # Image count = planned retained panels; actual relationships must resolve.
 ck('planned embedded images',sum(int(x['embedded_images']) for x in rows(O/'FIGURE_INTEGRATION.csv')),len(doc.inline_shapes))
 alltext='\n'.join(p.text for p in doc.paragraphs)+'\n'+'\n'.join(c.text for tb in doc.tables for row in tb.rows for c in row.cells)
 for s in ['5.2','2,808','1,344','1,464','936','3,133.461531','36,800','1,765.006','1,760.995','407','53','5.448297415','5,941.555975','0.412579010','9.722608121','5.977891152']:
  ck('key result present',True,s in alltext,s)
 ck('new B DC limit present',True,'走行DCは未評価' in alltext or '走行DCは計算していない' in alltext)
 ck('new fixed OD limit present',True,'固定ODモデル' in alltext)
 # No duplicate bookmark names/ids, new section orientations and caption inventory.
 names=new.xpath('.//w:bookmarkStart/@w:name',namespaces=NS);ids=new.xpath('.//w:bookmarkStart/@w:id',namespaces=NS)
 ck('bookmark names unique',len(names),len(set(names)));ck('bookmark IDs unique',len(ids),len(set(ids)))
 for x in rows(O/'FIGURE_INTEGRATION.csv'):ck('figure caption in text',True,x['number'] in alltext,x['figure_id'])
 ck('main method-heading5.2 unique',1,sum(p.text.startswith('5.2') and p.style.name.startswith('Heading') for p in doc.paragraphs))
 ck('main last section portrait',True,doc.sections[-1].page_width<doc.sections[-1].page_height)
# Read primary precomputed summary rows, not a new analysis.
a=rows(F/'A_SUMMARY_BY_CONDITION.csv');b=rows(F/'B_SUMMARY_BY_SCALE_AND_METHOD.csv');c=rows(F/'C_CONDITIONAL_MASS_DC_SUMMARY.csv')
ck('A saved36 all rates100',True,all(float(x['PE_on_time_percent'])==100 and float(x['count_on_time_percent'])==100 for x in a));ck('A saved36 policy inputs78',True,all(x['physical_inputs']=='78' for x in a))
for cfg,v in [('GROVER_P2',1765.0060775364782),('GROVER_P3',1760.995081995205)]:
 x=next(x for x in b if x['scale']=='ALL' and x['config_id']==cfg);ck('B quoted mean rounded',f'{v:.3f}',f"{float(x['mean_delta_objective_s']):.3f}",cfg)
x=next(x for x in c if x['series_id']=='C_T08' and x['dataset']=='CLASSICAL' and x['scenario_id']=='COND_S200_REF' and x['scale']=='ALL' and x['rolling_case']=='CRR_LOWER_BOUND');ck('C quoted weighted rounded','0.412579010',f"{float(x['weighted_saving_percent']):.9f}")
protection=[]
for x in rows(O/'SOURCE_HASHES_BEFORE.csv'):
 actual=sha(x['path']);protection.append({**x,'after_sha256':actual,'status':'PASS_UNCHANGED' if actual==x['sha256'] else 'FAIL_CHANGED'});ck('source protection',x['sha256'],actual,x['path'])
table('SOURCE_PROTECTION_CHECKS.csv',protection);initial=js(O/'INITIAL_GIT_STATE.json');ck('tracked diff unchanged',initial['diff'],subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R,text=True));table('DOCX_INTEGRITY_CHECKS.csv',checks);fail=[x for x in checks if x['status']=='FAIL'];dump('INTEGRITY_RUN.json',{'checks':len(checks),'failures':len(fail),'original_files_checked':len(protection),'wall_s':time.monotonic()-t,'output_sha256':sha(OUT),'original_sha256':sha(SRC)});print((O/'INTEGRITY_RUN.json').read_text());print('FAILURES',json.dumps(fail,ensure_ascii=False)[:4000])
