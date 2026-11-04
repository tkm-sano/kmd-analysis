from pathlib import Path
import re,json
import pandas as pd
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
O=Path(__file__).resolve().parents[1];doc=Document();sec=doc.sections[0];sec.page_height=Cm(29.7);sec.page_width=Cm(21);sec.top_margin=Cm(2.1);sec.bottom_margin=Cm(2.0);sec.left_margin=Cm(2.2);sec.right_margin=Cm(2.2)
for style in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
 s=doc.styles[style];s.font.name='DejaVu Sans';s._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Droid Sans Fallback');s.font.size=Pt(10.5 if style=='Normal' else 18 if style=='Title' else 13 if style=='Heading 1' else 11.5)
s=doc.styles['Normal'];s.paragraph_format.line_spacing=1.25;s.paragraph_format.space_after=Pt(7)
sec.header.paragraphs[0].text='KMD修士研究 | Step 3 独立trial | 正式採用・統合前'
sec.header.paragraphs[0].style=doc.styles['Caption']
f=sec.footer.paragraphs[0];f.alignment=2;f.add_run('Step 3 trial  •  ');field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');f._p.append(field)
def para(t,style=None):
 p=doc.add_paragraph(t,style);p.paragraph_format.widow_control=True;return p
def body(n):
 for line in (O/n).read_text().splitlines():
  if line.startswith('# '):continue
  if line.startswith('## '):doc.add_heading(line[3:],2)
  elif line.strip():para(line)
def picture(path,caption):
 p=doc.add_paragraph();p.alignment=1;p.add_run().add_picture(str(O/path),width=Cm(16.2));p.paragraph_format.keep_with_next=True
 para(caption,'Caption')
def table(title,heads,rows):
 h=doc.add_heading(title,2)
 if title.startswith('表3'):h.paragraph_format.page_break_before=True
 t=doc.add_table(rows=1,cols=len(heads));t.style='Light Shading Accent 1'
 for cell,txt in zip(t.rows[0].cells,heads):cell.text=txt
 pr=t.rows[0]._tr.get_or_add_trPr();el=OxmlElement('w:tblHeader');pr.append(el)
 for row in rows:
  cells=t.add_row().cells
  for cell,txt in zip(cells,row):
   cell.text=str(txt)
   for p in cell.paragraphs:
    p.paragraph_format.space_after=Pt(3)
    for r in p.runs:r.font.size=Pt(8.5)
  el=OxmlElement('w:cantSplit');t.rows[-1]._tr.get_or_add_trPr().append(el)
 para('詳細な条件・不確実性・元CSV/コード/ログは同じtrialの主張台帳およびEVIDENCE_TRACEABILITY.csvに対応する。','Caption')
doc.add_heading('量子技術がEV配送システムに\n寄与する条件の検討',0)
para('Step 3：結果・統合考察・結論の独立試作原稿','Subtitle');para('2026年11月4日 | quantum_ev_step3_synthesis_trial_20261104_174309')
para('本稿は研究者の採否判断前の独立trialである。正式な研究成果への採用と既存Word原稿への統合は未実施である。目的は量子技術の寄与条件の検討であり、量子優位性・実運用改善・量子由来の実材料改善の実証ではない。')
doc.add_heading('経路2の採用判断に関する重要な修正',1)
para('Chen et al.（2020）の保持試験から逆算した171.875/195.959596 Ah/kgは、主分析の確定材料性能値として未採用である。これを用いた約5.448297kgと約0.413%等は条件付き参考例として保持する。T08主モデルの分析は連続入力の解析感度・一般相殺境界・材料入力を使わないDC質量応答へ再構成した。')
para('資料構成：目的・RQ／結果節／考察節／結論節／条件表と限界／図版／引用・再現案内。高桁値は算術追跡用であり実測精度ではない。')
doc.add_page_break();doc.add_heading('研究目的と研究課題の整合性',1);body('RESEARCH_OBJECTIVE_RQ_ALIGNMENT.md');picture('CROSS_PATH_FIGURES/F1_two_paths.png','図1　研究対象と二つの経路。実線は指定計算・モデルの確認範囲、破線は未検証接続である。出典：STEP3_CLAIM_REGISTER.csv。')
doc.add_page_break();doc.add_heading('結果節（転記用草稿）',1);body('THESIS_RESULTS_DRAFT.md')
picture('PATH1_FIGURES/F5_saved_quality.png','図5　保存B系列の主greedy対照に対する平均ΔJ。入力内平均の規模内平均である。36,800を独立単位としない。出典：data/PATH1_STATISTICAL_RESULTS.csv。')
picture('PATH2_FIGURES/F7_independent_mass_response.png','図7　材料入力を使わない凍結DC質量応答。宣言区間1000〜1250kgの下端右微分を表示する。実車測定ではない。出典：data/DC_MASS_KERNEL_INDEPENDENT.csv。')
doc.add_page_break();doc.add_heading('考察節（転記用草稿）',1);body('THESIS_DISCUSSION_DRAFT.md')
doc.add_page_break();doc.add_heading('結論節（転記用草稿）',1);body('THESIS_CONCLUSION_DRAFT.md')
doc.add_page_break();doc.add_heading('寄与条件と研究の限界',1)
table('表1　経路1の主要条件',['主張ID','条件・結果','範囲・判定'],[
('P1-N01','J*_S < J_C は候補存在の必要条件','同一入力/目的/制約；CONDITIONAL'),('P1-S01','mirror：J*_S=J_initial≥J_C','460入力の当該支持；PASS'),('P1-O01','主greedyへの正改善0/36,800、best可行','固定保存集合；PASS'),('P1-O02','R5/p2：平均−5983.706秒、SD1314.365秒','70入力内平均；PASS'),('P1-C01/C02','R1_020 graph p1 58/97、p2 78/97','独立学習primary測定；CONDITIONAL'),('P1-T01','τ_total≤H_plan、H_plan未設定','CPU限定scope；HOLD'),('P1-H01','参照414、未証明46、保存MIPのみ41','最適性指標に留保；HOLD')])
table('表2　経路2の主要条件と参考例',['主張ID／区分','条件・数値','固定条件・判定'],[
('P2-A02／主分析','q/u/V/f_p/q_n/f_n増でM減、r/F/δ増でM増','正の定義域、他入力/D固定；CONDITIONAL'),('P2-A03／主分析','ΔM=b−δ、δ=bで相殺','同一会計・未知差を重複しない；CONDITIONAL'),('P2-D01／主分析','DC(m)の正傾き：全920条件','固定460軌跡×2Crr、1000–1250kg；CONDITIONAL'),('P2-B01〜B03／参考','b 5.448297kg、u* .877094、V*3.193156V','Chen逆算qと設計仮定；未採用参考'),('P2-S01／参考','T09既知差9.722608/5.977891kg','fixed_loading/fixed_area_LP；未知部材NULL'),('P2-E01/E02／参考','DC総和比 .412579/.413590%','Chen依存質量と凍結DC；実EV効果でない')])
lim=pd.read_csv(O/'data/TABLE3_LIMITATIONS.csv');table('表3　未検証事項と研究の限界',['対象','必要な追加証拠','現在の範囲'],lim[['link','required_evidence','current_scope']].values.tolist()+[['Chen逆算入力','同条件の直接測定/full-cell適格性','参考例のみ、主材料入力未採用']])
doc.add_page_break();doc.add_heading('条件構造の図版',1)
picture('PATH1_FIGURES/F2_path1_conditions.png','図2　経路1の寄与条件。改善候補の存在・実際の取得・主対照への改善・時間適合・運用伝達を別判定する。出典：PATH1_CONDITION_CLASSIFICATION.csv。')
picture('PATH2_FIGURES/F3_path2_conditions.png','図3　経路2の主分析。一般収支と材料入力を使わないDC質量応答を中心とする。具体的LP/S値は参考例である。出典：PATH2_CONDITION_CLASSIFICATION.csv。')
doc.add_page_break();picture('CROSS_PATH_FIGURES/F4_cross_path.png','図4　経路間比較。三段階は本trialの分析的整理であり、全段階が実証されたという意味ではない。出典：CROSS_PATH_CONDITION_MATRIX.csv。')
picture('PATH2_FIGURES/F6_reference_boundaries.png','図6　条件付き参考例の構造依存。Chen逆算容量を固定しているため、独立の一般的数値感度とは呼ばない。完成packの比較ではない。出典：data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv、data/PATH2_SENSITIVITY_SUMMARY.csv。')
doc.add_page_break();doc.add_heading('出典と引用の確認範囲',1);body('THESIS_CITATION_CHECK.md');doc.add_heading('監査・採否・再現',1)
para('主張台帳31件の証拠種類A〜FとPASS/CONDITIONAL/HOLD/FAILは別軸である。根拠ファイルのSHA256はSTEP3_SOURCE_MANIFEST.csv、再検算はevidence/NUMERICAL_RECHECK.csv、Chen依存はCHEN_DEPENDENCY_AUDIT.csvに記録した。監査は同一作業主体内の分離工程であり外部査読ではない。')
para('反証的検討と文章修正はSTEP3_ACADEMIC_REVIEW.md、ACADEMIC_REVIEW_CHECKLIST.csv、THESIS_STATEMENT_CORRECTIONS.mdを参照する。既存の道路受入/T09対向条件のFAILと入力・参照・実機・実材料/実道路のHOLDを無条件に解除しない。')
para('Step4では研究者が採用範囲を判断した後に、対象原稿版を指定して独立コピーへ統合する。本稿は正式原稿の上書きではない。ページ確認はLibreOfficeによるPDF表示に限定し、Word実機・大学提出様式の最終確認を残す。')
# Attach page starts to following content; avoid overflow of an empty break paragraph.
for i,p in enumerate(list(doc.paragraphs)):
 if p._p.xpath('.//w:br[@w:type="page"]'):
  nxt=p._p.getnext()
  if nxt is not None:
   pp=nxt.find(qn('w:pPr'))
   if pp is None:pp=OxmlElement('w:pPr');nxt.insert(0,pp)
   pp.append(OxmlElement('w:pageBreakBefore'))
  p._p.getparent().remove(p._p)
doc.core_properties.title='量子技術がEV配送システムに寄与する条件の検討：Step3独立trial';doc.core_properties.subject='寄与条件の統合考察、未採用のChen逆算値の参考分類';doc.save(O/'THESIS_STEP3_TRIAL.docx')
print('DOCX saved',len(doc.paragraphs),'paragraphs',len(doc.inline_shapes),'figures',len(doc.tables),'tables')
