"""Build a new DOCX, preserving original XML elements in main text or a history appendix."""
from common import *
from copy import deepcopy
from docx import Document
from docx.shared import Inches,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
sys.path.insert(0,str(O/'rendering_tools/python'))
import latex2mathml.converter,mathml2omml

start=time.monotonic();d=Document(SRC);pars=list(d.paragraphs);oldbody=list(d.element.body);sect=d.element.body.sectPr;before=js(O/'DOCX_STRUCTURE_BEFORE.json');assert sha(SRC)==before['sha256']
# Original table association is preserved with its preceding original paragraph.
attached={};pi=-1;tableidx=0
for e in oldbody:
 if e.tag==qn('w:p'):pi+=1
 elif e.tag==qn('w:tbl'):attached.setdefault(pi,[]).append((tableidx,e));tableidx+=1
for e in oldbody:
 if e is not sect:d.element.body.remove(e)
archives=[];positions={};figlog=[];tablelog=[];pchanges=[];equations=[];bookmark=1000
for style in ['Heading 1','Heading 2','Heading 3']:
 d.styles[style].paragraph_format.keep_with_next=True
 d.styles[style].paragraph_format.keep_together=True
# Existing header stays unchanged; page numbering is the only new footer feature.
footer=d.sections[-1].footer;p=footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run();r.font.size=Pt(9);f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');rr=OxmlElement('w:r');tt=OxmlElement('w:t');tt.text='1';rr.append(tt);f.append(rr);p._p.append(f)
# Continue page numbers across the added orientation sections.
for num in sect.findall(qn('w:pgNumType')):num.attrib.pop(qn('w:start'),None)
base_sect=deepcopy(sect)
for style in ['Heading 1','Heading 2','Heading 3']:
 # Keep original typography, adding only widow/orphan prevention.
 d.styles[style].paragraph_format.widow_control=True

def insert(e):sect.addprevious(e)
def orig(i):
 insert(pars[i]._p)
 for tid,tbl in attached.get(i,[]):
  if tid in [1,7]:
   label,title=('表3-2','配送需要の生成・採用段階') if tid==1 else ('付表A-1','旧局所系列の最適値一致と代表回路')
   caption(label,title);tablelog.append({'table_id':label,'title':title,'source':'original DOCX table '+str(tid),'rows_excluding_header':len(tbl.findall(qn('w:tr')))-1,'columns':len(tbl.find(qn('w:tblGrid'))),'note':'既存表のXML・セル内容を変更せず題名のみ追加','kind':'ORIGINAL_TABLE_CAPTION_ADDED','status':'INTEGRATED_PENDING_RENDER'})
  insert(tbl)
def orig_range(a,b):
 for i in range(a,b+1):orig(i)
def archive(a,b,label):
 block=[]
 for i in range(a,b+1):
  block.append(pars[i]._p)
  block.extend(e for tid,e in attached.get(i,[]))
 archives.append({'start':a,'end':b,'label':label,'elements':block})
def clean(s):
 s=s.replace('**','').replace('`','')
 s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1（\2）',s)
 replacements={'図F3-1':'図3-1','図F3-2':'図3-2','図F5-1':'図5-1','図F5-2':'図5-2','図F5-3':'付図C-1','図F5-4':'図5-4','図F5-5':'図5-5','図F5-6':'図5-6','図F5-7':'図5-7','図FA-1':'付図C-2','F3-1':'図3-1','F3-2':'図3-2','F5-1':'図5-1','F5-2':'図5-2','F5-3':'付図C-1','F5-4':'図5-4','F5-5':'図5-5','F5-6':'図5-6','F5-7':'図5-7','FA-1':'付図C-2','付表A-1':'付表D-1','付表C-1':'付表D-3','付表S-1':'電子付録S-1'}
 for a,b in replacements.items():s=s.replace(a,b)
 s=s.replace('本レビュー09およびSHA256_MANIFEST.csv','付録Eおよび電子資料のSHA256_MANIFEST.csv').replace('本レビューはその記録を保持し','統合時の照合ではその記録を保持し').replace('今回のレビューの独立照合32,269項目','前段の学術レビューの数値照合32,269項目')
 return s

def text(s,style='Body Text',size=None):
 p=d.add_paragraph(style=style);s=clean(s)
 # Do not inject editorial Markdown headings or backticks.
 r=p.add_run(s)
 if size:r.font.size=Pt(size)
 r._element.get_or_add_rPr().append(E.Element(qn('w:lang'),{qn('w:val'):'ja-JP'}))
 p.paragraph_format.widow_control=True
 return p

def head(s,level=2):
 p=text(s,f'Heading {level}');return p

def math(latex):
 # Canonical braces prevent a converter treating '+'/'-' as an open script.
 for symbol in ['A','c',r'\rho',r'\epsilon']:
  for sign in ['+','-']:latex=latex.replace(symbol+'_'+sign,symbol+'_{'+sign+'}')
 if latex.startswith(r'M_{liq}=') and r'\left[' in latex:
  # Algebraically identical pore-volume decomposition, with no new parameter.
  text('液体質量の同一式を、正負塗工材の空隙体積V₊、V₋およびセパレータ空隙体積V_sepに分けて表示する（体積の単位はm³）。')
  for expression in [r'V_{+}=\frac{c_{+}}{\rho_{+}}\frac{\epsilon_{+}}{1-\epsilon_{+}}',r'V_{-}=\frac{c_{-}}{\rho_{-}}\frac{\epsilon_{-}}{1-\epsilon_{-}}',r'V_{sep}=\max(A_{+},A_{-})t_s\epsilon_s',r'M_{liq}=\rho_{liq}(V_{+}+V_{-}+V_{sep}+V_{extra})']:
   math(expression)
  return
 omml=mathml2omml.convert(latex2mathml.converter.convert(latex));el=E.fromstring(('<root xmlns:m="'+NS['m']+'">'+omml+'</root>').encode())[0]
 
 for run in el.xpath('.//m:sub//m:r | .//m:sup//m:r',namespaces=NS):
  if ''.join(run.xpath('./m:t/text()',namespaces=NS)) in ['+','-','−']:
   pr=run.find(qn('m:rPr'))
   if pr is None:pr=E.SubElement(run,qn('m:rPr'))
   literal=E.SubElement(pr,qn('m:lit'));literal.set(qn('m:val'),'1')
 for nary in el.xpath('.//m:nary',namespaces=NS):
  pr=nary.find(qn('m:naryPr'))
  for part in ['sub','sup']:
   value=nary.find(qn('m:'+part))
   if value is not None and not ''.join(value.xpath('.//m:t/text()',namespaces=NS)).strip():
    hidden=E.SubElement(pr,qn('m:'+part+'Hide'));hidden.set(qn('m:val'),'1')
 p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p._p.append(el);p.paragraph_format.space_after=Pt(4);equations.append({'latex':latex,'OMML_text':''.join(el.xpath('.//m:t/text()',namespaces=NS))})

def blocks(content,skipfirst=True):
 lines=content.splitlines();buffer=[];inmath=False;ml=[]
 def flush():
  if buffer:text(' '.join(buffer));buffer.clear()
 for line in lines:
  line=line.strip()
  if line.startswith('#'):
   flush()
   if not skipfirst:head(re.sub(r'^#+\s*','',line),3)
  elif line=='\\[':flush();inmath=True;ml=[]
  elif line=='\\]':
   raw=' '.join(ml);parts=re.split(r',\\(?:qquad|quad)\s*',raw)
   for part in parts:math(part.rstrip(','))
   inmath=False
  elif inmath:ml.append(line)
  elif not line:flush()
  else:buffer.append(line)
 flush()

def sections(file):
 s=(P/file).read_text();matches=list(re.finditer(r'^## (.+)$',s,re.M));out={}
 for i,m in enumerate(matches):out[m[1]]=s[m.end():matches[i+1].start() if i+1<len(matches) else len(s)]
 return out
methods=sections('04_THESIS_METHODS_DRAFT.md');results=sections('05_THESIS_RESULTS_DRAFT.md');discussion=sections('06_THESIS_DISCUSSION_DRAFT.md')
def get(sec,prefix):return next(v for k,v in sec.items() if k.startswith(prefix))

def bookmark_p(p,name):
 global bookmark
 a=OxmlElement('w:bookmarkStart');a.set(qn('w:id'),str(bookmark));a.set(qn('w:name'),name);b=OxmlElement('w:bookmarkEnd');b.set(qn('w:id'),str(bookmark));p._p.insert(1 if p._p.pPr is not None else 0,a);p._p.append(b);bookmark+=1

def end_section(landscape=False):
 # The sectPr describes the section ending here, not the following section.
 p=d.paragraphs[-1];pr=p._p.get_or_add_pPr();sp=deepcopy(base_sect);typ=sp.find(qn('w:type'))
 if typ is None:typ=OxmlElement('w:type');sp.insert(0,typ)
 typ.set(qn('w:val'),'nextPage')
 if landscape:
  sz=sp.find(qn('w:pgSz'));w,h=sz.get(qn('w:w')),sz.get(qn('w:h'));sz.set(qn('w:w'),h);sz.set(qn('w:h'),w);sz.set(qn('w:orient'),'landscape')
 pr.append(sp);p.paragraph_format.keep_with_next=False

def caption(label,title):
 p=text(label+'　'+title,size=10);p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(6);p.paragraph_format.space_after=Pt(4);bookmark_p(p,'IT_'+str(bookmark)+'_'+re.sub('[^A-Za-z0-9]','_',label));return p

def pic(path,width):
 p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(2);r=p.add_run();sh=r.add_picture(str(path),width=Inches(width));sh._inline.docPr.set('descr',path.name+'; source and crop provenance in FIGURE_INTEGRATION.csv');return p

def figure(id,where):
 x=next(x for x in rows(P/'FIGURE_SOURCE_MAPPING.csv') if x['figure_id']==id);source=P/next(n for n in x['files'].split(';') if n.endswith('.png'));label={'F3-1':'図3-1','F3-2':'図3-2','F5-1':'図5-1','F5-2':'図5-2','F5-3':'付図C-1','F5-4':'図5-4','F5-5':'図5-5','F5-6':'図5-6','F5-7':'図5-7','FA-1':'付図C-2'}[id]
 notes=clean('対象：'+x['denominator']+'。'+x['aggregation']+'。'+x['assumptions']+'。'+x['unreadable_result']+'。出典：'+','.join(Path(n).name for n in x['source_paths'].split(';'))+'（電子資料、原図ID '+id+'）。')
 landscape=id in ['F3-1','F3-2','F5-2','F5-4']
 if landscape:
  end_section(False);caption(label,x['title']);pic(source,9.0);text(notes,size=8);end_section(True);assets=[source]
 else:
  im=Image.open(source);w,h=im.size;assets=[]
  if id=='F5-3':rects=[(round(i*w/3),55,round((i+1)*w/3),h) for i in range(3)];groups=[[0],[1],[2]]
  elif id=='FA-1':rects=[(i*w//2,j*h//2,(i+1)*w//2,(j+1)*h//2) for j in range(2) for i in range(2)];groups=[[0,1],[2,3]]
  else:rects=[(0,0,w//2,h),(w//2,0,w,h)];groups=[[0,1]]
  for i,rect in enumerate(rects):
   a=O/'figure_panels'/f'{id}_panel{i+1}.png';a.parent.mkdir(exist_ok=True);im.crop(rect).save(a,dpi=(220,220));assets.append(a)
  for gi,indices in enumerate(groups):
   title=x['title']+(f'（{gi+1}/{len(groups)}）' if len(groups)>1 else '');p=caption(label,title);p.paragraph_format.page_break_before=True
   for i in indices:pic(assets[i],5.0 if len(indices)==2 else 6.0)
   text(notes,size=8)
  figlog.append({'figure_id':id,'number':label,'placement':where,'title':x['title'],'source_png':str(source),'source_sha256':sha(source),'embedded_images':len(assets),'derived_assets':';'.join(str(a.relative_to(O)) for a in assets),'conversion':'unchanged numerical content; panels cropped without recomputation; all original panels retained','denominator':x['denominator'],'units':x['units'],'source_csv_paths':x['source_paths'],'source_csv_sha256':x['source_sha256'],'caption':notes,'status':'INTEGRATED_PENDING_RENDER'})
  return
 figlog.append({'figure_id':id,'number':label,'placement':where,'title':x['title'],'source_png':str(source),'source_sha256':sha(source),'embedded_images':len(assets),'derived_assets':';'.join(str(a) for a in assets),'conversion':'original PNG unchanged; landscape page for legibility','denominator':x['denominator'],'units':x['units'],'source_csv_paths':x['source_paths'],'source_csv_sha256':x['source_sha256'],'caption':notes,'status':'INTEGRATED_PENDING_RENDER'})

def word_table(number,title,headers,data,source,note='',widths=None):
 caption(number,title);tb=d.add_table(rows=1,cols=len(headers));tb.autofit=False
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'888888');borders.append(el)
 tb._tbl.tblPr.append(borders)
 widths=widths or [6.15/len(headers)]*len(headers)
 for i,h in enumerate(headers):tb.rows[0].cells[i].text=str(h)
 rh=OxmlElement('w:tblHeader');tb.rows[0]._tr.get_or_add_trPr().append(rh)
 for row in data:
  cc=tb.add_row().cells
  for i,val in enumerate(row):cc[i].text=str(val)
 for row in tb.rows:
  trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
  for j,cell in enumerate(row.cells):
   cell.width=Inches(widths[j]);
   for p in cell.paragraphs:
    p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2);p.paragraph_format.line_spacing=1
    for run in p.runs:run.font.size=Pt(8.5)
 for j,col in enumerate(tb.columns):col.width=Inches(widths[j])
 text('出典：'+source+'。'+note,size=8)
 tablelog.append({'table_id':number,'title':title,'source':source,'rows_excluding_header':len(data),'columns':len(headers),'note':note,'status':'INTEGRATED_PENDING_RENDER'})
 return tb

def replace(a,b,title,content):
 archive(a,b,title);head(title);blocks(content)
 positions[title]={'old_start':a,'old_end':b,'action':'REPLACE_MAIN_MOVE_ORIGINAL_XML_TO_APPENDIX_B'}
# Opening and literature: keep source paragraphs and links; normalize only actual headings.
for i in range(174):
 orig(i)
 if i in [0,17,29,173]:
  pp=pars[i];old=pp.text;new={0:'1　背景と研究目的',17:'1.1　研究目的',29:'2　文献調査',173:'3　方法'}[i]
  # These four source headings have no math/hyperlinks/fields.
  assert not pp._p.xpath('.//m:oMath | .//w:hyperlink');pp.text=new;pp.style=d.styles['Heading 2' if i==17 else 'Heading 1'];pchanges.append({'original_index0':i,'before':old,'after':new,'reason':'章番号と階層を実際の節番号へ整合'})
 elif re.match(r'^2\.\d',pars[i].text):pars[i].style=d.styles['Heading 3' if re.match(r'^2\.\d+\.\d+',pars[i].text) else 'Heading 2']
 if i==27:text('本稿で定量評価した範囲は、系列Aの固定ODによるモデル配送成果、系列Bの保存計画品質・CPU計算工程、系列Cの条件付き質量・固定速度DC感度である。地域交通の受入、系列Bの走行DC、量子材料解析による対象材料改善および完成パック性能は未検証である。専門家面接は設計段階であり、実施済みの検証として扱わない。')
replace(174,176,'3.1　分析対象と証拠の区分',get(methods,'3.1'))
cohort=rows(P/'tables/T3-1_COHORTS.csv');word_table('表3-1','主分析の対象と評価範囲',['系列','物理対象','反復条件','評価範囲'],[[x['series'],x['physical_units'],x['replication'],x['endpoint']] for x in cohort],'T3-1_COHORTS.csv','26親・25需要群の依存を保持。Cの旧460速度とBの460入力は別系列。',[.8,.7,2.05,2.6])
orig_range(177,184);text('本全件分析ではN0由来の保存ODを研究用固定費用表として使用する。N0の幾何受入とN1修正候補の動的受入は不成立のままであり、地域SUMOの実走行成果として採用していない。道路変更・OD再計算・新規地域走行は実施していない。')
orig_range(185,193)
replace(194,200,'3.4　主分析の入力と統計単位',get(methods,'3.4'))
orig_range(201,208);text('この節のJ＋102nによる帰庫計算は顧客別時間窓のない系列Bに適用する。系列Aはreadyによる待機を含むため、3.8節の再帰式で計算する。Bの訪問順は全配送先を保持した経路であり、旧局所部分問題系列と同一視しない。')
orig_range(209,213);text('本稿の主比較では、古典初期解、同じmatching支持の古典厳密値、旧CPU予算対応改善解、global厳密参照を分ける。現行Bは厳密参照407入力、未確定53入力である。旧CPU対応古典改善920行は現在8設定との同予算が確認されていない補助比較である。')
# A's acquisition method remains in main text, with original equations intact.
orig_range(214,221);text('ここまでのone-hot／Protocol V2の条件は系列Aの保存取得結果に対応する。系列Bの現行8設定は3.13節で別に定義する。旧時間窓なし直接法、局所ブロック、別全体方式の詳細は付録Bに保存した。')
archive(222,228,'旧3.7節：時間窓なし直接法・局所法・旧アーキテクチャ')
replace(229,233,'3.8　固定ODによる採用政策と配送成果',get(methods,'3.8'));figure('F3-1','本文3.8')
replace(234,247,'3.9　材料参照値と質量会計',get(methods,'3.9'))
# Keep the cancellation definition with the method, avoiding a three-line overflow page.
pp=list(d.paragraphs);begin=next(i for i,p in enumerate(pp) if p.text.startswith('3.9　'))
for p in pp[begin+1:]:
 if p.style.name=='Body Text':p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(4)
 else:p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(2)
figure('F3-2','本文3.9')
replace(248,260,'3.10　固定速度のControlled-DC',get(methods,'3.10'))
archive(261,263,'旧3.11節：実験環境と計測範囲');head('3.11　計算環境と時間計測の区分');text('系列Aの保存Protocol V2はQiskit2.1.1のCPU回路シミュレーションであり、運用政策の仮想取得時間とは別である。現行Bの保存計算資源は3,680固有fitに対応付け、FIT、FINAL_VALIDATION、SELECTED_STATE、RESULTの工程を区別する。10測定seedへ同じfit時間を重複加算しない。hardware qubits、コンパイル後深さ・ゲート数、全fit共通の当時実行環境はHOLDとする。現在の集計・描画環境を元量子計算の環境へ代用しない。旧系列の異なる環境は付録Bへ保全した。')
replace(264,273,'3.12　対応統計・欠測・再現性',get(methods,'3.11'))
archive(274,279,'旧3.13節：11月1日系列と補助的段階検証');head('3.13　系列Bの現行8設定と比較方法');blocks(get(methods,'3.5'));text('図5-1・図5-2に規模別品質を示す。工程別時間は付図C-1に分ける。全凍結設定と実装hashの所在は付録E.4に示す。')
archive(280,285,'旧4章：手続きと再現性の管理');head('4　手続きと再現性の管理',1);text('入力・実装・保存結果は個別SHA256で対応付けた。元科学実験と、保存結果に対する全件算術・独立照合と、今回のWord統合を別工程として記録する。入力やモデルを結果に合わせて修正していない。')
text('再現性は、①保存結果の確認、②保存入力からの再実行、③原資料からの入力再生成、④現実の配送・電池・車両への妥当性の4段階を区別する。保存結果と入力の算術整合は確認した一方、外部保全資料を含む原資料の完全公開と、実地域・対象EVへの妥当性は未達である。研究全体の再現性を確保したとは記述しない。')
text('前段の全件独立検証ではAの再帰をmax-plus式、Bの費用を元NPZの別加算、CのDCを質量係数式で照合した。学術レビューでは元行集計32,269項目と図表・保全等2,912項目を照合し、不一致0件であった。これらの確認項目数は独立標本数ではない。今回のWord統合は数値・図表の読取りと文書構造の検証に限定し、新規SUMO、経路探索、QAOA、全件科学実験の再実行を行っていない。')
text('証拠と再実行入口は付録Aの旧根拠資料に加え、付録Eの現行主分析対応表と電子資料のhash台帳を参照する。未取得、欠測、未評価、HOLD、FAILを区別し、成功へ置換しない。')
orig(286)
replace(287,293,'5.1　時間窓なし配送計画の比較（系列B）',get(results,'5.1'))
b=rows(F/'B_SUMMARY_BY_SCALE_AND_METHOD.csv');scales=[f'R{i}' for i in range(6)]
lookup={(x['scale'],x['config_id']):x for x in b}
word_table('表5-1','規模別の古典初期解に対する平均目的値差',['規模（入力数）','同値6設定','Grover P2','Grover P3'],[[s+'（'+lookup[(s,'MEAN_P2')]['physical_inputs']+'）','0.000',f"{float(lookup[(s,'GROVER_P2')]['mean_delta_objective_s']):+.3f}",f"{float(lookup[(s,'GROVER_P3')]['mean_delta_objective_s']):+.3f}"] for s in scales],'B_SUMMARY_BY_SCALE_AND_METHOD.csv','単位は秒、保存best−古典初期。入力内10repを平均後、入力等重み。同値6設定の名称・全率は付表D-2。')
word_table('表5-2','厳密参照値のカバー範囲',['規模','全入力','参照あり','未確定'],[[s,lookup[(s,'MEAN_P2')]['physical_inputs'],lookup[(s,'MEAN_P2')]['exact_reference_inputs'],lookup[(s,'MEAN_P2')]['exact_missing_inputs']] for s in scales],'B_EXACT_REFERENCE_COVERAGE.csv','合計460、参照407、未確定53。未確定をgap0にしない。')
resource=[]
for cfg in ['MEAN_P2','CVAR10_P2','CVAR01_P2','COHERENT2_P2','COHERENT4_P2','GROVER_P2','GROVER_P3','ACTIVE_ADJACENT_P3_GRID']:
 x=lookup[('ALL',cfg)];resource.append([cfg,'RESULT' if cfg.startswith('ACTIVE') else 'FIT',f"{float(x['mean_fit_wall_s']):.6f}"])
word_table('表5-3','保存工程別の平均wall時間',['設定','工程','平均wall [秒]'],resource,'B_SUMMARY_BY_SCALE_AND_METHOD.csv;B_RESOURCE_SCOPE_SUMMARY.csv','各設定460固有fit。FITは最終検証等を含まない。activeのRESULTとは同範囲でない。最終検証時間は本文と付図C-1。',[2.8,.9,2.45])
figure('F5-1','本文5.1');figure('F5-2','本文5.1')
replace(294,295,'5.2　固定ODによる採用政策と配送成果（系列A）',get(results,'5.2'));figure('F5-4','本文5.2');figure('F5-5','本文5.2')
replace(296,299,'5.3　材料質量と固定速度電力量（系列C）',get(results,'5.3'))
c=rows(P/'tables/T5-4_T08_DC.csv');word_table('表5-4','T08の固定軌跡DC感度',['Crr','基準DC総和 [Wh]','DC差総和 [Wh]','加重削減率 [%]'],[[('下側' if 'LOWER' in x['rolling_case'] else '上側'),f"{float(x['baseline_sum_Wh']):,.3f}",f"{float(x['saving_sum_Wh']):,.3f}",f"{float(x['weighted_saving_percent']):.9f}"] for x in c],'C_T08_PAIRED_DIFFERENCES.csv','各条件旧460速度、質量差5.448297415kg。実EV・現行BのDCではない。個別率平均は本文と電子資料を参照。',[.65,1.9,1.65,1.95]);figure('F5-6','本文5.3');figure('F5-7','本文5.3')
replace(300,305,'5.4　補助的不確実性と未評価範囲',get(results,'5.4'))
orig(306)
# Entire old discussion is retained as archival XML, including original math.
archive(307,327,'旧6章：技術能力境界・材料設計・アーキテクチャ考察')
for k,v in discussion.items():head(k);blocks(v)
archive(328,333,'旧7章：統合前の結論');head('7　結論',1);s=(P/'07_THESIS_CONCLUSION_DRAFT.md').read_text();blocks(s)
# Original bibliography retained verbatim; additions are separately identified.
orig_range(334,397);pars[334].style=d.styles['Heading 1']
head('今回の統合で補った文献',2)
refs=js(O/'REFERENCE_UPDATES.json')
for x in refs:
 if x['action']=='ADD_VERIFIED':text(x['bibliography'])
# Faraji DOI is appended separately so the original bibliography paragraph remains intact.
text('既存Faraji-Niri et al.（2024）の追加識別子： https://doi.org/10.1016/j.dib.2023.109798 （WRAP原著版と書誌を照合）。')
text('Papachristos（2018）は複数の同年候補を区別する根拠が残るため、元引用を維持し、文献同定を要確認とする（付録E.3）。')
orig_range(398,609)
# Old tables keep all cells and formatting. New appendix labels do not rename old data.
head('付録B　統合前の方法・結果・考察記録',1)
text('本付録は統合前の記述と表・数式を保全した履歴であり、現在の主分析と異なる入力・期限・予算を含む。「今回」等の時点表現、旧表番号、旧章番号は統合前の原文を示す。現在の主たる結果は第5章、条件と限界は第3・6章を参照する。旧548入力、R4=99、R6〜R8、局所部分問題、native候補指標を現行B460や固定OD成果へ転用しない。')
for i,x in enumerate(archives,1):
 head(f'B.{i}　{x["label"]}',2);text(f'移動元：元DOCX段落{x["start"]}〜{x["end"]}（0始まり）。元の本文・数式・表を要素ごと保持した。',size=8)
 for e in x['elements']:
  if e.tag==qn('w:p'):
   ps=e.find('w:pPr/w:pStyle',NS)
   if ps is not None and ps.get(qn('w:val')) in ['Heading1','Heading2','Heading3']:ps.set(qn('w:val'),'BodyText')
  insert(e)
 x['destination']=f'付録B.{i}'
head('付録C　計算工程と条件付きDC感度の補助図',1);head('C.1　工程を分けた計算時間',2);text('本文の表5-3を補う工程別結果を示す。原図F5-3の3panelを拡大して掲載し、単一のend-to-end順位にはしない。');figure('F5-3','付録C.1')
head('C.2　未知部材差と参照質量のDC感度',2);text('T09完成パックの採用値ではない既存参照質量1200/1400kgに対し、同じ旧460速度を使用した感度である。原図FA-1の全4panelを設計別に拡大した。');figure('FA-1','付録C.2')
head('付録D　全政策・全設定・条件付き感度の表',1);head('D.1　36政策の全条件',2)
a=rows(P/'tables/TA-1_ALL_36_POLICIES.csv')
for L in ['900','3600','7200']:
 zz=[x for x in a if x['L_s']==L]
 word_table('付表D-1'+{'900':'a','3600':'b','7200':'c'}[L],f'政策条件 L={L}秒',['条件','TQ [秒]','B [秒]','Q採用','C切替','正の遅延','平均完了差 [秒]'],[[x['condition_id'],x['T_Q_s'],x['B_s'],x['quantum_adopted'],x['classical_switched'],x['positive_departure_inputs'],f"{float(x['delta_mean_completion_s']):+.3f}"] for x in zz],'A_SUMMARY_BY_CONDITION.csv','各行78問題・556PE・312配送先。全行PE/件数率100%、古典対照差0pp。時間差は政策−古典単独。',[.85,.7,.55,.65,.65,.85,1.5])
head('D.2　8設定・6規模の品質',2)
quality=rows(P/'tables/T5-1_B_OBJECTIVE.csv')
for i,cfg in enumerate(sorted({x['config_id'] for x in quality}),1):
 zz=[x for x in quality if x['config_id']==cfg];word_table('付表D-2'+chr(96+i),cfg,['規模','入力数','目的値差 [秒]','改善 [%]','同値 [%]','悪化 [%]'],[[x['scale'],x['physical_inputs'],f"{float(x['mean_delta_objective_s']):+.3f}",f"{float(x['improve_percent']):.3f}",f"{float(x['equal_percent']):.3f}",f"{float(x['worsen_percent']):.3f}"] for x in zz],'B_SUMMARY_BY_SCALE_AND_METHOD.csv','入力内10rep平均後、規模内入力等重み。正の差は初期解より大きい。')
head('D.3　T09接続の全56感度条件',2)
cs=rows(P/'tables/TA-2_C_BRIDGE.csv')
for i,design in enumerate(['fixed_loading','fixed_area_LP']):
 zz=[x for x in cs if x['design_policy']==design];word_table('付表D-3'+chr(97+i),'固定担持' if i==0 else '固定面積',['δ [kg]','参照質量 [kg]','Crr','正味軽量化 [kg]','DC差総和 [Wh]','加重率 [%]'],[[f"{float(x['unknown_mass_difference_kg']):.6f}",x['reference_running_mass_kg'],'下側' if 'LOWER' in x['rolling_case'] else '上側',f"{float(x['mass_saving_kg']):.6f}",f"{float(x['saving_sum_Wh']):.3f}",f"{float(x['weighted_saving_percent']):.9f}"] for x in zz],'C_CONDITIONAL_MASS_DC_SUMMARY.csv','各行旧460軌跡。δ＝未知部材S−LP差、正味軽量化b−δ。完成パックは未確定。',[.85,.8,.55,1.15,1.3,1.1])
head('D.4　補助区間の電子付録',2);text('1,176補助区間の全行は電子付録S-1（TA-3_SUPPLEMENT_INTERVALS.csv）およびCLUSTER_SENSITIVITY_INTERVALS.csvに保持する。本文に示したD10-01/D10-04は説明例であり、都合のよい条件のみを選び直していない。25群の10,000回percentile区間で、検定0件、現実交通・材料・モデル構造の誤差は含まれない。')
head('付録E　現行主分析の証拠対応と要確認事項',1);head('E.1　資料の所在とSHA256',2)
text('現行全件分析はreview_outputs/no_sumo_full_analysis_20261102/run01/、原稿・図表はreview_outputs/thesis_results_interpretation_20261102/run01/、Word統合の変更履歴・検証はreview_outputs/thesis_docx_integration_20261103/run01/に保存する。元rawやsource snapshotの一部は外部保全領域にあり、公開Gitのみで再取得できるとは主張しない。')
names=['A_POLICY_DECISIONS_2808.csv','A_DELIVERY_COMPLETION_BY_STOP.csv','A_MECHANISM_COMPARISON.csv','B_PLAN_REFERENCES_36800.csv','B_SUMMARY_BY_SCALE_AND_METHOD.csv','C_CONDITIONAL_MASS_DC_SUMMARY.csv','PAIRED_COMPARISONS.csv']
word_table('付表E-1','主要分析結果のSHA256',['ファイル','SHA256'],[[n,sha(F/n)] for n in names],'各元ファイル','完全な入力・コード・出力台帳は電子資料を参照。',[2.25,3.9])
head('E.2　主張と証拠',2)
for c in rows(P/'CLAIM_EVIDENCE_MAPPING.csv'):
 text(f"{c['claim_id']}［{c['evidence_class']}／{c['decision']}］ {c['claim']} 出典：{Path(c['input_path']).name}、{c['row_or_problem_id']}。限界：{c['limits']}",size=9)
text('全26主張の式・実装・行ID・source SHA256・図対応はCLAIM_EVIDENCE_MAPPING.csvに保存した。「使用不可」の文は否定すべき主張例であり、本稿の結論として採用しない。')
head('E.3　未解決事項',2)
text('背景のPapachristos（2018）は、Futuresの方法論論文と同年会議論文等の候補があり、元引用の意図を一意に示す識別子が残らないためHOLDとする。本文の元引用を削除・別論文へ自動置換していない。他7背景引用は一次資料の書誌と記述対象を照合して参考文献へ補った。')
text('地域網N0/N1の受入FAIL、Aの正の出発遅延native未取得、Bの走行DC未評価、厳密参照53入力HOLD、実機回路資源HOLD、T09完成パック183行HOLD・全面対向1行FAIL、対象量子材料改善未実証を保持する。これらは新たな実証なしに文書編集だけで解消しない。')
head('E.4　アルゴリズムと再実行入口',2);text('Aの保存計画・採用政策・固定ODはrun_a.py、Bの保存参照はrun_b.py、Cの凍結モデル評価はrun_c.py、独立検証はverify_independent.py、統計はstatistics_tables.pyとverify_statistics.pyに対応する。これらは前段の実行入口であり、今回のWord統合では実行していない。')
append=(P/'ALGORITHM_PROTOCOL_APPENDIX.md').read_text();blocks(append[append.index('## 本文3.13へ追加する説明'):]);text('全protocolの角度範囲・開始点・精度・seed規則・budgetはALGORITHM_PROTOCOLS_PINNED.json、実装snapshotの実パス・SHA256はALGORITHM_SOURCE_SNAPSHOTS.csvにある。図表の数値をWord上で再計算せず、FIGURE_SOURCE_MAPPING.csvと図・表生成コードへ遡る。統合DOCXの生成入口はscripts/integrate_docx.py、表示検証と修正履歴は今回レビュー領域に保存した。')
# Keep original evidence-item headings with their explanation (e.g. appendix R07).
for paragraph in d.paragraphs:
 if re.match(r'^[A-Z][0-9]{2}[：:]',paragraph.text):paragraph.paragraph_format.keep_with_next=True
# Formatting is limited to explicitly logged layout repairs and new content.
# Final section retains original portrait geometry and original header relationship.
settings=d.settings.element
update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');settings.append(update)
# Restore all original body-level bookmark pairs. Their source positions are not paragraphs.
starts=[e for e in oldbody if e.tag==qn('w:bookmarkStart')];ends={e.get(qn('w:id')):e for e in oldbody if e.tag==qn('w:bookmarkEnd')}
target_prefix={
 '分析対象と系列の区分':'3.1','対象地域道路建物':'3.2','配送需要の推計と生成':'3.3','担当集合規模別問題od入力':'3.4','訪問順最適化の数理定義':'3.5','古典計算と厳密参照':'3.6','量子計算の構成と標本採用':'3.7','材料性能からセルパック走行質量への換算':'3.9','保存軌跡のcontrolled-dcモデル':'3.10','環境計測範囲':'3.11','指標統計単位検証方法':'3.12','手続きと再現性の管理':'4','研究結果':'5','配送計画の取得品質時間資源':'5.1','材料設計質量dc電力量':'5.3','考察':'6','取得採用出発期限の技術能力境界':'6.1','設計境界と走行条件による材料効果の修飾':'6.2','計算アーキテクチャアルゴリズム構成と未接続区間':'6.3','結論':'7'}
special={'配送計画からsumo実行への接続':(229,233),'月追加検証の方法と適用範囲':(274,279),'月の補足的な全体方式古典対照段階検証':(303,305),'付録a-根拠資料再実行契約':(398,609),'a.1-資料の所在版と分析単位':(399,413),'a.2-本文根拠idと確認箇所':(414,533),'a.3-入力実装結果のsha256':(534,581),'a.4-保存手順から確認した再実行入口':(582,606),'a.5-追加局所の最適値一致分母と代表回路':(607,609)}
bookmarklog=[];allp=list(d.paragraphs)
for st in starts:
 name=st.get(qn('w:name'));en=ends[st.get(qn('w:id'))]
 if name in special:
  ia,ib=special[name];first,last=pars[ia],pars[ib];meaning='旧節／原付録の内容位置を保持'
 else:
  pref=target_prefix[name];ix=next(i for i,p in enumerate(allp) if re.match(re.escape(pref)+r'　',p.text) and p.style.name.startswith('Heading'));first=allp[ix];level=int(first.style.name[-1]);endix=next((j for j in range(ix+1,len(allp)) if allp[j].style.name.startswith('Heading') and int(allp[j].style.name[-1])<=level),len(allp));last=allp[endix-1];meaning='更新後の同じ研究主題の節へ対応'
 first._p.insert(1 if first._p.pPr is not None else 0,st);last._p.append(en);bookmarklog.append({'name':name,'id':st.get(qn('w:id')),'new_start_anchor':first.text[:120],'new_end_anchor':last.text[:120],'reason':meaning})
table('BOOKMARK_RETARGETING.csv',bookmarklog)
d.save(OUT)
# Log disposition of every planned location; the citation issue is retained, not guessed.
execution=[]
for x in rows(O/'INSERTION_PLAN_AUDIT.csv'):
 a,b=int(x['paragraph_index0_start']),int(x['paragraph_index0_end']);dest=[y['destination'] for y in archives if not (y['end']<a or y['start']>b)];status='HOLD' if x['integration_id'] in ['I03','I27'] else 'PASS';execution.append({**x,'execution_status':status,'new_location':x['proposed_section'],'old_material_destination':';'.join(dest) or '原位置で維持','performed_change':x['change_and_reason'],'actual_result':'引用7件・Faraji DOI照合済み、Papachristos同定のみHOLD' if status=='HOLD' else '新原稿・図表を挿入、または実文書と一致を確認して維持','evidence_mapping':str(P/'CLAIM_EVIDENCE_MAPPING.csv')})
table('INSERTION_EXECUTION.csv',execution);table('FIGURE_INTEGRATION.csv',figlog);table('TABLE_INTEGRATION.csv',tablelog);table('ARCHIVED_ORIGINAL_BLOCKS.csv',[{k:v for k,v in x.items() if k!='elements'} for x in archives]);table('HEADING_EDITS.csv',pchanges);table('ADDED_EQUATIONS.csv',equations);dump('DOCX_STRUCTURE_AFTER.json',structure(OUT));dump('BUILD_RUN.json',{'wall_s':time.monotonic()-start,'output_sha256':sha(OUT),'original_sha256':sha(SRC),'figures':len(figlog),'embedded_images':sum(x['embedded_images'] for x in figlog),'new_tables':sum(x.get('kind')!='ORIGINAL_TABLE_CAPTION_ADDED' for x in tablelog),'original_tables_given_captions':sum(x.get('kind')=='ORIGINAL_TABLE_CAPTION_ADDED' for x in tablelog),'old_archive_blocks':len(archives),'insertion_status':dict(Counter(x['execution_status'] for x in execution))});print((O/'BUILD_RUN.json').read_text())
