from pathlib import Path
import re,json,copy,hashlib,collections
import pandas as pd
from lxml import etree
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
O=Path(__file__).resolve().parents[1];R=O.parents[1];S3=R/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';base=O/'sources/BASELINE_THESIS.docx';original=Document(base);doc=Document(base)
for el in list(doc._element.body):
 if etree.QName(el).localname!='sectPr':doc._element.body.remove(el)
sec=doc.sections[0];sec.page_height=Cm(29.7);sec.page_width=Cm(21);sec.top_margin=Cm(2.0);sec.bottom_margin=Cm(2.0);sec.left_margin=Cm(2.2);sec.right_margin=Cm(2.2);sec.header_distance=Cm(.85);sec.footer_distance=Cm(.85)
if 'Step4 Table' not in doc.styles:doc.styles.add_style('Step4 Table',WD_STYLE_TYPE.TABLE)
for name in ['Caption','Title','Subtitle']:
 if name not in doc.styles:doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
for name in ['Normal','Body Text','Heading 1','Heading 2','Heading 3','Caption']:
 style=doc.styles[name];style.font.name='DejaVu Sans';style._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Droid Sans Fallback');style.font.size=Pt(10.5 if name in ['Normal','Body Text'] else 15 if name=='Heading 1' else 12 if name=='Heading 2' else 10)
 style.paragraph_format.line_spacing=1.22;style.paragraph_format.space_after=Pt(4)
doc.styles['Title'].font.size=Pt(22)
doc.styles['Subtitle'].font.size=Pt(14)
header=sec.header.paragraphs[0];header.text='KMD修士研究　独立Step4統合trial｜正式採用前';header.style=doc.styles['Caption']
footer=sec.footer.paragraphs[0];footer.text='Step4 trial  •  ';footer.alignment=2;field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
# Clear old section-start page numbering in this independent manuscript.
for el in sec._sectPr.findall(qn('w:pgNumType')):sec._sectPr.remove(el)
source=pd.read_csv(O/'ORIGINAL_THESIS_STRUCTURE.csv',keep_default_na=False);byid={int(x['body_index']):x for x in source.to_dict('records')};used={};ledger=[];figs=[];tables=[];sectionmap=[];textmap=[];bookmark=90000;currentsection='front';currentchapter='front'
chapter_titles=[];sourceels=list(original._element.body)
def anchor(p,name):
 global bookmark
 bookmark+=1;s=OxmlElement('w:bookmarkStart');s.set(qn('w:id'),str(bookmark));s.set(qn('w:name'),name);e=OxmlElement('w:bookmarkEnd');e.set(qn('w:id'),str(bookmark));p._p.insert(0,s);p._p.append(e)
def para(t,style=None):
 p=doc.add_paragraph(t,style);p.paragraph_format.widow_control=True
 textmap.append(dict(section=currentsection,text=t,kind='new',paragraph=len(doc.paragraphs)-1));return p
def heading(t,level=1,mark=None):
 global currentsection,currentchapter
 p=doc.add_heading(t,level)
 if level==1:p.paragraph_format.page_break_before=True;currentchapter=t
 currentsection=t
 if mark:anchor(p,mark);chapter_titles.append(dict(title=t,bookmark=mark))
 sectionmap.append(dict(section=t,level=level,chapter=currentchapter));return p
def fit_clone(el,archive=False):
 for sp in list(el.xpath('.//w:sectPr')):sp.getparent().remove(sp)
 # Normalize source table widths without changing cell text or equations.
 if etree.QName(el).localname=='tbl':
  ratio=1.0
  grid=el.find(qn('w:tblGrid'))
  if grid is not None:
   cols=grid.findall(qn('w:gridCol'));widths=[int(c.get(qn('w:w'),'1000')) for c in cols];ratio=9400/max(sum(widths),1)
   for c,w in zip(cols,widths):c.set(qn('w:w'),str(int(w*ratio)))
  for tcw in el.xpath('.//w:tcW'):
   if tcw.get(qn('w:type'))=='dxa':tcw.set(qn('w:w'),str(int(int(tcw.get(qn('w:w'),'1000'))*ratio)))
  for tr in el.xpath('.//w:trPr/w:cantSplit'):tr.getparent().remove(tr)
  for p in el.xpath('.//w:p'):
   pp=p.find(qn('w:pPr'))
   if pp is not None:
    for k in list(pp):
     if etree.QName(k).localname in ['keepNext','keepLines','pageBreakBefore']:pp.remove(k)
  for r in el.xpath('.//w:r'):
   rp=r.find(qn('w:rPr'))
   if rp is None:rp=OxmlElement('w:rPr');r.insert(0,rp)
   sz=rp.find(qn('w:sz'))
   if sz is None:sz=OxmlElement('w:sz');rp.append(sz)
   sz.set(qn('w:val'),'16')
 for extent in el.xpath('.//wp:extent'):
  w=int(extent.get('cx'));h=int(extent.get('cy'));maxw=int(Cm(16.1))
  if w>maxw:
   extent.set('cx',str(maxw));extent.set('cy',str(int(h*maxw/w)))
 # Reset inherited exact line heights; source run text and OMML stay intact.
 for p in ([el] if etree.QName(el).localname=='p' else el.xpath('.//w:p')):
  pp=p.find(qn('w:pPr'))
  if pp is None:pp=OxmlElement('w:pPr');p.insert(0,pp)
  for sp in list(pp.findall(qn('w:spacing'))):pp.remove(sp)
  sp=OxmlElement('w:spacing');sp.set(qn('w:line'),'288');sp.set(qn('w:lineRule'),'auto');sp.set(qn('w:before'),'0');sp.set(qn('w:after'),'80');pp.append(sp)
 for pp in el.xpath('.//w:pPr'):
  for k in list(pp):
   if etree.QName(k).localname in ['keepNext','keepLines','pageBreakBefore'] and archive:pp.remove(k)
 return el
def copy_source(a,b):
 global currentsection
 for x in source.to_dict('records'):
  j=int(x['body_index']);idx=int(x['paragraph_index']) if x['element']=='p' else None
  # Tables belong to the last preceding paragraph in source order.
  preceding=source[(source.body_index<j)&(source.element=='p')]
  pi=idx if idx is not None else int(preceding.iloc[-1].paragraph_index)
  if a<=pi<=b:
   if x['element']=='p' and str(x['style']).startswith('Heading'):
    currentsection=x['text'];sectionmap.append(dict(section=currentsection,level=2,chapter=currentchapter))
   el=fit_clone(copy.deepcopy(sourceels[j]));doc._element.body.insert(len(doc._element.body)-1,el);used[j]=currentsection;ledger.append(dict(block_id=x['block_id'],source_body_index=j,category='A',destination=currentsection,action='XML本文再使用；組版だけ調整',reason='地域/需要/数理/会計/凍結式の具体性を保持'))
   if x['element']=='tbl':tables.append(dict(id='SOURCE-T'+str(x['table_index']),title='元需要等の詳細表',scope='current source reuse',source=str(base),CSV_or_locator=x['block_id']))
figspec={
'F1':('CROSS_PATH_FIGURES/F1_two_paths.png','図3-1','二つの経路と検証範囲','data/CONTRIBUTION_CONDITIONS_FINAL.csv','構造図：未検証接続を分離'),
'F2':('PATH1_FIGURES/F2_path1_conditions.png','図4-2','探索支持・取得・品質・時間の条件','data/CONTRIBUTION_CONDITIONS_FINAL.csv','経路1条件。支持内の不可能性を一般化しない'),
'F5':('PATH1_FIGURES/F5_saved_quality.png','図4-1','保存B系列の主古典対照に対する品質差','data/PATH1_STATISTICAL_RESULTS.csv','入力内平均の規模内平均；単位秒'),
'F3':('PATH2_FIGURES/F3_path2_conditions.png','図5-1','経路2の主分析と相殺条件','data/PATH2_ANALYTICAL_SENSITIVITY.csv','一般条件とChen依存参考値を分離'),
'F7':('PATH2_FIGURES/F7_independent_mass_response.png','図5-2','材料入力を使わないDC質量応答','data/DC_MASS_KERNEL_INDEPENDENT.csv','460対応軌跡×2Crr、1000〜1250kg；実車ではない'),
'F6':('PATH2_FIGURES/F6_reference_boundaries.png','図5-3','条件付き参考例の部材構造依存','data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv','Chen逆算q依存；主材料入力として未採用'),
'F4':('CROSS_PATH_FIGURES/F4_cross_path.png','図6-1','二経路の比較枠組み','CROSS_PATH_CONDITION_MATRIX.csv','証拠水準の非対称性を維持')}
def figure(key):
 rel,num,title,data,note=figspec[key];src=O/rel if (O/rel).is_file() else S3/rel;target=O/'figures'/(key+'.png');target.write_bytes(src.read_bytes());pdfsrc=src.with_suffix('.pdf');(O/'figures'/(key+'.pdf')).write_bytes(pdfsrc.read_bytes())
 p=doc.add_paragraph();p.alignment=1;p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(target),width=Cm(16.1));cap=para(num+'　'+title+'。'+note+'。画像出典：Step3 '+rel+'。数値・構造の根拠：'+data+'。','Caption');anchor(cap,'s4_'+key)
 figs.append(dict(id=num,title=title,scope='current',source=str(src),CSV_or_locator=data,path=str(target.relative_to(O))))
def table(num,title,heads,rows,data):
 cap=para(num+'　'+title,'Caption');cap.paragraph_format.keep_with_next=True;anchor(cap,'s4_'+num.replace('-','_'));t=doc.add_table(rows=1,cols=len(heads));t.style='Step4 Table'
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  item=OxmlElement('w:'+edge);item.set(qn('w:val'),'single');item.set(qn('w:sz'),'4');item.set(qn('w:color'),'A8B4C4');borders.append(item)
 t._tbl.tblPr.append(borders)
 for cell,txt in zip(t.rows[0].cells,heads):cell.text=str(txt)
 trh=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(trh)
 for row in rows:
  cells=t.add_row().cells
  for cell,txt in zip(cells,row):
   cell.text=str(txt)
   for p in cell.paragraphs:
    p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.05
    for r in p.runs:r.font.size=Pt(8.5)
  t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 para('出典：'+data+'。','Caption');tables.append(dict(id=num,title=title,scope='current',source=str(O/data) if (O/data).is_file() else data,CSV_or_locator=data))
def main_table(key):
 if key=='PATH1':
  d=pd.read_csv(O/'data/PATH1_STATISTICAL_RESULTS.csv');d=d[(d.primary_comparison)&(d.config_id=='GROVER_P2')&(d.scale.isin(['R0','R1','R2','R3','R4','R5']))].sort_values('scale')
  rows=[[x.scale,x.physical_inputs,f'{x.input_mean_delta_J_mean:.1f}',f'{x.input_mean_delta_J_sd:.1f}',x.improving_reps] for x in d.itertuples()];table('表4-1','Grover p2の規模別入力内平均差',['規模','入力数','平均ΔJ 秒','入力間SD 秒','正改善best数'],rows,'data/PATH1_STATISTICAL_RESULTS.csv')
  q=pd.read_csv(O/'data/QAOA_CONTROLLED_CELL_SUMMARY.csv');q=q[(q.problem_id=='R1_020')&(q.support=='FULL_PERMUTATION')&(q.method=='QAOA')];q=q[((q.initial_state=='BASIS_INITIAL')&(q.mixer=='GRAPH_SWAP'))|((q.mixer=='PROJECTOR')&(q.layers==1))]
  rows=[[x.initial_state,x.mixer,x.layers,f'{x.primary_optimal_rep0_count}/97',f'[{x.primary_optimal_Wilson95_lower:.3f},{x.primary_optimal_Wilson95_upper:.3f}]'] for x in q.itertuples()];table('表4-2','R1_020のprimary最適取得（有意差の判定ではない）',['初期','mixer','層','取得','Wilson95%'],rows,'data/QAOA_CONTROLLED_CELL_SUMMARY.csv')
 elif key=='PATH2':
  d=pd.read_csv(O/'data/DC_MASS_KERNEL_SUMMARY.csv');table('表5-1','材料非依存の質量応答：1000kgでの右微分',['Crr','軌跡数','最小','中央値','平均','SD'],[[x.rolling_case,x.n,f'{x.slope_min:.3f}',f'{x.slope_median:.3f}',f'{x.slope_mean:.3f}',f'{x.slope_SD:.3f}'] for x in d.itertuples()],'data/DC_MASS_KERNEL_SUMMARY.csv');para('単位はWh/kg。軌跡間の分布であり、モデル/材料の信頼区間ではない。')
  d=pd.read_csv(O/'data/DC_ENDPOINT_RECHECK.csv');table('表5-2','Chen依存の条件付き参考例（主分析確定値として未採用）',['Crr','軌跡数','DC総和比 %','個別率平均 %','軌跡間SD pp'],[[x.Crr,x.n,f'{x.total_ratio_percent:.6f}',f'{x.individual_mean_percent:.6f}',f'{x.individual_SD_pp:.6f}'] for x in d.itertuples()],'data/DC_ENDPOINT_RECHECK.csv')
def read_md(path):
 for line in path.read_text().splitlines():
  if not line.strip():continue
  m=re.fullmatch(r'@@COPY:(\d+):(\d+)@@',line)
  if m:copy_source(*map(int,m.groups()));continue
  m=re.fullmatch(r'@@FIG:(\w+)@@',line)
  if m:figure(m[1]);continue
  m=re.fullmatch(r'@@TABLE:(\w+)@@',line)
  if m:main_table(m[1]);continue
  if line.startswith('# '):
   if path.stem.startswith('00_'):continue
   if path.stem.startswith('08_'):
    heading(line[2:],2);continue
   title=line[2:];num=re.match(r'[1-7]',title);heading(title,1,'s4_ch'+num[0] if num else None)
  elif line.startswith('## '):heading(line[3:],2)
  else:
   p=para(line)
   if path.stem.startswith('08_'):
    p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.1
    for run in p.runs:run.font.size=Pt(9.5)
# Cover and standalone trial disclaimer.
para('量子技術がEV配送システムに\n寄与する条件の検討','Title');para('修士論文 全文統合trial｜Step 4','Subtitle');para('2026年11月4日');para('研究者の採用審査用・独立作成。正式な研究成果への採用、既存原稿への反映、commit/push/公開は未実施である。')
para('本原稿は11月3日統合版を内容保全の基準とし、現行の主論証と旧原稿の保全記録を区別する。付録Bに旧定時率・旧材料値・旧結論が残る箇所は履歴であり、現行分析として採用した意味ではない。')
heading('要旨',1,'s4_abstract');read_md(O/'drafts/00_abstract.md')
heading('目次',1,'s4_toc');toc=[]
for title,mark in [('1　序論','s4_ch1'),('2　先行研究と研究ギャップ','s4_ch2'),('3　研究枠組み・方法','s4_ch3'),('4　配送経路計算の分析結果','s4_ch4'),('5　電池材料・車両の分析結果','s4_ch5'),('6　統合考察','s4_ch6'),('7　結論','s4_ch7'),('参考文献','s4_refs'),('付録A　現行条件・根拠・未検証事項','s4_appA'),('付録B　元原稿の保全記録','s4_appB')]:
 p=para(title+'　……　頁照合中');anchor(p,'toc_'+mark);toc.append(dict(title=title,bookmark=mark))
para('章レベルの固定目次である。PDFの章開始ページへ照合してから表示用番号を更新する。Wordでの最終自動目次化は提出体裁の作業である。','Caption')
for n in json.loads((O/'evidence/CHAPTER_FILES.json').read_text()):read_md(O/'drafts'/(n+'.md'))
heading('参考文献',1,'s4_refs');read_md(O/'drafts/08_references.md')
heading('付録A　現行条件・根拠・未検証事項',1,'s4_appA');para('この付録は現行の根拠への入口である。元原稿の詳細な需要・数式・再実行契約は付録Bの原位置IDへ対応する。高桁数値は算術追跡用で、実測精度を示すものではない。')
lim=pd.read_csv(S3/'data/TABLE3_LIMITATIONS.csv');table('表A-1','未検証事項',['対象','必要証拠','現在の範囲'],lim[['link','required_evidence','current_scope']].values.tolist(),'Step3 data/TABLE3_LIMITATIONS.csv')
sens=pd.read_csv(O/'data/PATH2_ANALYTICAL_SENSITIVITY.csv');table('表A-2','T08の解析感度と固定条件',['変数','偏微分','符号','定義域'],sens[['variable','derivative','sign','domain']].values.tolist(),'data/PATH2_ANALYTICAL_SENSITIVITY.csv')
claims=pd.read_csv(O/'CLAIM_ADOPTION_REVIEW.csv');table('表A-3','31主張の審査入口',['Claim ID','反映箇所','科学的判定','採用推奨'],claims[['claim_id','thesis_location','scientific_judgment','adoption_recommendation']].values.tolist(),'CLAIM_ADOPTION_REVIEW.csv')
para('推奨A/B/C/Dと科学的PASS/CONDITIONAL/HOLD/FAILは別軸である。Cの未検証事項は、その効果を結果として採用せず、保留の存在を本文で明示する。元CSV・分析コード・ログ・不確実性・Chen依存はSECTION_CLAIM_EVIDENCE_MAP.csvおよび電子台帳に記録する。')
heading('付録B　元原稿の保全記録',1,'s4_appB');para('以下は基準原稿のうち現行本文へ再使用しなかった内容の保全である。旧章・節・図表番号、旧方針、未同定文献、旧参照407/53、旧主指標、旧結果は原版の履歴として読む。現行の優先仕様は第1〜7章であり、この保存記録から現在の主指標や採用値を復活させない。旧の定時率、Chen参考値、道路受入不成立、未知BOMの記録を削除しない。現行本文へ移したblockは対応表に示し、同じ内容を付録へ重複しない。')
# Preserve every remaining meaningful source block; empty layout-only paragraphs are explicitly logged.
lastgroup=None
for x in source.to_dict('records'):
 j=int(x['body_index'])
 if j in used:continue
 el=copy.deepcopy(sourceels[j]);has_content=bool(el.xpath('.//w:t | .//m:t | .//w:drawing | .//w:pict | .//w:fldSimple | .//w:instrText | .//w:bookmarkStart | .//w:bookmarkEnd'))
 if x['element']=='p' and not has_content:
  ledger.append(dict(block_id=x['block_id'],source_body_index=j,category='D',destination='sources/BASELINE_THESIS.docx',action='trial組版上の空段落だけ省略',reason='本文・数式・図・参照を持たない。元byteは保全'));continue
 group=x['chapter']
 if group!=lastgroup:
  heading('保存範囲：'+group,2);para('旧原稿内の記述である。現在の科学的判定・入力採否は本文と採用審査表を優先する。','Caption');lastgroup=group
 el=fit_clone(el,True)
 if x['element']=='p':
  # Scope original headings to the historical appendix; original text remains byte-for-byte in runs.
  pp=el.find(qn('w:pPr'))
  if pp is None:pp=OxmlElement('w:pPr');el.insert(0,pp)
  if str(x['style']).startswith('Heading'):
   style=pp.find(qn('w:pStyle'))
   if style is None:style=OxmlElement('w:pStyle');pp.append(style)
   style.set(qn('w:val'),'Heading3')
  # Plain source identifier is separate from the preserved paragraph text.
  if x['text'] or int(x['OMML']) or int(x['drawings']):
   label=doc.add_paragraph('原位置 '+x['block_id']+'（p'+str(x['paragraph_index'])+'）','Caption');label.paragraph_format.space_after=Pt(1);label.paragraph_format.keep_with_next=True
 doc._element.body.insert(len(doc._element.body)-1,el);ledger.append(dict(block_id=x['block_id'],source_body_index=j,category='C',destination='付録B／原位置'+x['block_id'],action='原内容を保存付録へ移動；章階層/組版だけ調整',reason='旧方針・旧結果・詳細再現資料を失わせず現行主張と区別'))
 if x['element']=='tbl':tables.append(dict(id='保存表-B'+str(x['table_index']),title='元表・原番号は保存範囲に限定',scope='historical appendix',source=str(base),CSV_or_locator=x['block_id']))
 if int(x['drawings']):
  for k in range(int(x['drawings'])):figs.append(dict(id='保存図-'+x['block_id']+'-'+str(k+1),title='元図・原番号は保存範囲に限定',scope='historical appendix',source=str(base),CSV_or_locator=x['block_id'],path='embedded original media'))
# Normalize drawing IDs for uniqueness after source reuse plus new figures.
for i,x in enumerate(doc._element.xpath('.//wp:docPr'),1):x.set('id',str(i))
# New current paragraphs with no source body have separate category E in change matrix.
for x in textmap:pass
# XML fields and shapes preserved; publish an honest build inventory.
doc.core_properties.title='量子技術がEV配送システムに寄与する条件の検討：Step4全文統合trial';doc.core_properties.subject='内容保全と条件付き成果の独立統合';doc.save(O/'THESIS_STEP4_INTEGRATED_TRIAL.docx')
pd.DataFrame(ledger).to_csv(O/'THESIS_PRESERVED_CONTENT_AUDIT.csv',index=False);pd.DataFrame(ledger).to_csv(O/'ORIGINAL_TO_REVISED_SECTION_MAP.csv',index=False)
pd.DataFrame(sectionmap).to_csv(O/'CHAPTER_SECTION_MAPPING.csv',index=False);pd.DataFrame(textmap).to_csv(O/'evidence/NEW_PARAGRAPHS.csv',index=False);pd.DataFrame(toc).to_csv(O/'evidence/TOC_ENTRIES.csv',index=False)
pd.DataFrame([dict(type='figure',**x) for x in figs]+[dict(type='table',**x) for x in tables]).to_csv(O/'FIGURE_TABLE_REGISTER.csv',index=False)
# Full text including equations and table cells in document order; Markdown is an audit/export, not a competing manuscript.
lines=[]
for el in doc._element.body:
 typ=etree.QName(el).localname
 if typ=='p':
  text=''.join(el.xpath('.//w:t/text() | .//m:t/text()'));st=el.find(qn('w:pPr'));style=st.find(qn('w:pStyle')).get(qn('w:val')) if st is not None and st.find(qn('w:pStyle')) is not None else '';lev={'Heading1':'# ','Heading2':'## ','Heading3':'### '}.get(style,'');lines.append(lev+text)
 elif typ=='tbl':
  for row in el.findall(qn('w:tr')):lines.append(' | '.join(''.join(tc.xpath('.//w:t/text() | .//m:t/text()')) for tc in row.findall(qn('w:tc'))))
(O/'THESIS_FULL_TEXT.md').write_text('\n\n'.join(lines)+'\n')
build=dict(source_blocks=len(source),source_ledger_rows=len(ledger),new_paragraphs=len(textmap),source_reused=len(used),source_original_tables=len(original.tables),total_tables=len(doc.tables),source_original_images=len(original.inline_shapes),total_inline_images=len(doc.inline_shapes),source_original_OMML=len(original._element.xpath('.//m:oMath')),total_OMML=len(doc._element.xpath('.//m:oMath')),paragraphs=len(doc.paragraphs),body_chars=len((O/'THESIS_FULL_TEXT.md').read_text()),sections=len(doc.sections))
(O/'evidence/DOCX_BUILD.json').write_text(json.dumps(build,indent=2));print(json.dumps(build,indent=2))
