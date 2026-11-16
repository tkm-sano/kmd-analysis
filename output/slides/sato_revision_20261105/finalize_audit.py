"""Preserve the exact PDF opening page, render every page, and issue evidence reports."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from collections import Counter
import xml.etree.ElementTree as ET
import json,csv,re,hashlib,math
import pymupdf as fitz
from pptx import Presentation
from PIL import Image,ImageDraw

O=Path(__file__).resolve().parent;R=O.parents[2]
stem='研究紹介_佐野巧馬_佐藤先生相談用_改訂12枚'
original=R/'output/slides/研究紹介_佐野巧馬_詳細説明15枚.pdf'
raw=O/'render'/f'{stem}.pdf';pdf=O/f'{stem}.pdf';pptx=O/f'{stem}.pptx'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm=lambda s:re.sub(r'\s+','',s)
a=fitz.open(original);rendered=fitz.open(raw);d=fitz.open()
d.insert_pdf(a,from_page=0,to_page=0);d.insert_pdf(rendered,from_page=1,to_page=11)
d.set_metadata({'title':'量子技術がEVラストワンマイル配送に与える影響｜佐藤先生相談用','author':'佐野巧馬','subject':'原第1ページ保全・12枚改訂・学術監査付き'})
d.save(pdf,garbage=4,deflate=True);d.close();d=fitz.open(pdf)
assert len(d)==12
q=Presentation(pptx);ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
with ZipFile(R/'研究紹介_佐野巧馬.pptx') as z,ZipFile(pptx) as y:
 samexml=z.read('ppt/slides/slide1.xml')==y.read('ppt/slides/slide1.xml')
 rel='ppt/slides/_rels/slide1.xml.rels'
 samerel=z.read(rel)==y.read(rel)
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'))
 styles=[]
 for shape in root.findall('.//p:sp',ns):
  text=''.join(x.text or '' for x in shape.findall('.//a:t',ns))
  for r in shape.findall('.//a:r',ns):
   rp=r.find('a:rPr',ns)
   if rp is not None:
    styles.append(dict(text=''.join(r.itertext()),size_pt=int(rp.get('sz','0'))/100,bold=rp.get('b')=='1',font=(rp.find('a:latin',ns).get('typeface') if rp.find('a:latin',ns) is not None else None)))
 geometry=[dict(shape_id=s.find('p:nvSpPr/p:cNvPr',ns).get('id'),xfrm=ET.tostring(s.find('p:spPr/a:xfrm',ns),encoding='unicode')) for s in root.findall('.//p:sp',ns) if s.find('p:spPr/a:xfrm',ns) is not None]
 pdf_fonts=a[0].get_fonts(full=True)
 design=dict(font_family='Noto Sans JP',source_PDF_embedded_names=sorted(set(x[3].split('+')[-1] for x in pdf_fonts)),original_run_styles=styles,original_shape_geometry=geometry,palette={'title':'#002060','route_1':'#002060','route_2':'#087E88','route_3':'#6A5794','body':'#000000','background':'#FFFFFF','dark_box':'#808080','light_box':'#F2F2F2','original_rule':'#D6E0E8'},title_pt=16,heading_pt=[12,14],body_pt=12,secondary_pt=10,slide_inches=[q.slide_width/914400,q.slide_height/914400],round_rect_adjustment=.055)
(O/'evidence/design_extracted.json').write_text(json.dumps(design,ensure_ascii=False,indent=2))

pixel=[]
for scale in [1,2,3]:
 x=a[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False);y=d[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
 pixel.append(dict(scale=scale,width=x.width,height=x.height,identical=x.samples==y.samples,pixel_hash=hashlib.sha256(x.samples).hexdigest()))
assert samexml and samerel and all(x['identical'] for x in pixel)
geoms=json.loads((O/'evidence/text_geometry.json').read_text())
missing=[];outside=[];fallback=[];overlaps=[];fonts=Counter();used_colors=set()
for z in geoms:
 if norm(z['text']) not in norm(d[z['slide']-1].get_text()):missing.append(z)
for i,page in enumerate(d):
 page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(O/'render'/f'slide_{i+1:02d}.png')
 lines=[]
 for block in page.get_text('dict')['blocks']:
  if 'lines' not in block:continue
  for ln in block['lines']:
   st=''.join(s['text'] for s in ln['spans']);r=fitz.Rect(ln['bbox'])
   if st.strip():lines.append((r,st))
   for span in ln['spans']:
    if i>0:
     fonts[span['font']]+=1;used_colors.add(f'{span["color"]:06X}')
     if 'NotoSansJP' not in span['font']:fallback.append(dict(page=i+1,font=span['font'],text=span['text']))
   if not page.rect.contains(r):outside.append(dict(page=i+1,rect=list(r),text=st))
 if i>0:
  for j,(r,st) in enumerate(lines):
   for t,other in lines[j+1:]:
    inter=r&t
    if inter.width>3 and inter.height>3:overlaps.append(dict(page=i+1,text1=st,text2=other,intersection=list(inter)))
palette=set(['002060','087E88','6A5794','808080','F2F2F2','000000','FFFFFF','D6E0E8'])
shape_colors=set();shape_oob=[];declared_fonts=set()
for i,s in enumerate(q.slides):
 if i==0:continue
 for sh in s.shapes:
  if sh.left<0 or sh.top<0 or sh.left+sh.width>q.slide_width+100 or sh.top+sh.height>q.slide_height+100:shape_oob.append((i+1,sh.shape_id))
  for x in sh._element.findall('.//{'+ns['a']+'}srgbClr'):shape_colors.add(x.get('val'))
  if sh.has_text_frame:
   for p in sh.text_frame.paragraphs:
    for rr in p.runs:declared_fonts.add(rr.font.name)
assert not missing,missing
assert not fallback,fallback
assert not shape_oob,shape_oob
assert shape_colors<=palette,shape_colors-palette
assert declared_fonts=={'Noto Sans JP'},declared_fonts
canvas=Image.new('RGB',(1800,1464),'#D6E0E8')
for i,page in enumerate(d):
 pix=page.get_pixmap(matrix=fitz.Matrix(600/page.rect.width,600/page.rect.width),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
 canvas.paste(im,((i%3)*600,(i//3)*366+25));ImageDraw.Draw(canvas).text(((i%3)*600+8,(i//3)*366+6),str(i+1),fill='black')
canvas.save(O/'全12枚プレビュー.png')

with (O/'evidence/source_manifest.csv').open() as f:pins=list(csv.DictReader(f))
pres=[dict(path=p['path'],sha256_before=p['sha256'],sha256_after=sha(p['path']),unchanged=sha(p['path'])==p['sha256']) for p in pins]
assert all(x['unchanged'] for x in pres)
with (O/'evidence/source_preservation_final.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(pres[0]));w.writeheader();w.writerows(pres)
audit=dict(pages=12,first_slide_xml_identical=samexml,first_slide_relationships_identical=samerel,first_pdf_page_pixel_checks=pixel,first_pdf_page_text_identical=a[0].get_text()==d[0].get_text(),declared_fonts=sorted(declared_fonts),used_new_page_fonts=dict(fonts),fallback_spans=fallback,text_missing=missing,text_outside_page=outside,overlap_candidates=overlaps,shape_outside_page=shape_oob,shape_colors=sorted(shape_colors),all_source_hashes_unchanged=True,protected_source_files=len(pres),same_page_sizes=all(p.rect==d[0].rect for p in d))
(O/'evidence/final_display_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))

B=json.loads((O/'data/B_summary.json').read_text());C=json.loads((O/'data/C_summary.json').read_text());A=json.loads((O/'evidence/analysis_audit.json').read_text());reg=json.loads((O/'evidence/slide_register.json').read_text());ids=json.loads((O/'evidence/source_ids.json').read_text())
ledger=[]
def add(slide,claim,value,unit,path,aggregation,role):ledger.append(dict(slide=slide,claim=claim,value=value,unit=unit,source=str(R/path),aggregation=aggregation,adoption_role=role))
for metric in ['mean','median','min','max','sd']:
 add(5,'B delta '+metric,B['all_outputs'][metric],'s',ids['B1'],'all 36,800 saved outputs; candidate minus greedy; SD ddof=1','adopted fixed-cohort description')
for cls,n in B['counts'].items():add(5,'B '+cls,n,'outputs',ids['B1'],'paired same-input classification; independent N is not 36,800','adopted description')
for key in ['median','sd']:
 add(5,'B input-mean '+key,B['input_means'][key],'s',ids['B1'],'80 outputs per input averaged first; 460 input means; SD ddof=1','adopted description')
add(6,'B minimum return slack',B['min_return_slack_s'],'s',ids['B1'],'32400 minus candidate return; all 36800 outputs','adopted model-time result')
add(6,'B last customer earlier',B['last_delivery_earlier_count'],'outputs',ids['B1'],'last_delivery_difference_s< -1e-9; not total-J improvement','adopted model-time result')
for z in B['scale_settings']:
 add(5,z['scale']+' '+z['config_id']+' mean delta',z['mean'],'s','output/slides/sato_revision_20261105/data/B_scale_setting_statistics.csv','input first 10-measurement mean then equal input weighting','new read-only aggregation of adopted B')
for rc in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
 for metric in ['mean','median','min','max','sd']:
  add(8,rc+' DC1000 '+metric,C[rc]['DC_1000_Wh'][metric],'Wh',ids['C3'],'460 observed windows, m=1000kg; frozen model','new descriptive evaluation inside adopted model scope')
  add(10,rc+' delta100kg '+metric,C[rc]['delta_100kg_Wh'][metric],'Wh',ids['C3'],'same trajectories, E(1100kg)-E(1000kg); exact finite difference','new model calculation; not measured vehicle effect')
 add(10,rc+' mean local mass derivative',C[rc]['dE_dm_1000_Wh_kg']['mean'],'Wh/kg',ids['C1'],'460 trajectory right derivatives at 1000kg','adopted conditional main model result')
for z in C['correlations']:
 add(8,z['rolling_case']+' '+z['factor']+' Spearman',z['spearman'],'rank correlation',ids['C3'],'finite-cohort ranks; no p or independent-sample CI','new descriptive statistic, not causal')
for key,v in C['CRR_LOWER_BOUND']['component_sum_share_percent'].items():
 add(8,key,v,'percent',ids['C3'],'sum signed component on positive total-wheel-work mask / total DC, m1000kg','bookkeeping allocation; not independently identified causal contribution')
for key in ['Crr_paired_absolute_Wh','Crr_paired_relative_percent']:
 add(8,key+' mean',C[key]['mean'],'Wh' if key.endswith('Wh') else 'percent',ids['C3'],'paired upper minus lower; percent is mean individual ratio','descriptive sensitivity')
with (O/'data/material_reference_boundaries.csv').open() as f:
 for z in csv.DictReader(f):
  add(10,z['model']+' '+z['variable']+' '+z['conditions'],z['boundary'],z['unit'],'review_outputs/t08_t09_final_adoption_20261105/data/BOUNDARIES.csv',z['conditions'],'INPUT UNQUALIFIED REFERENCE ONLY; not main material effect')
add(9,'q+10% positive coating mass relative change',100*(1/1.1-1),'percent',ids['M1'],'analytic 1/q response; fixed E,V,u,fp; not pack-level response','analytic illustration, no claimed real material performance')
with (O/'evidence/quantitative_claim_ledger.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)

design_report='''デザイン仕様 — 佐藤先生相談用・改訂12枚

1. 基準と第1枚目の保全
唯一のデザイン基準は「研究紹介_佐野巧馬.pptx」の第1枚目、および既存15枚PDFの第1ページである。
PPTXは元第1スライドXMLと関連定義をバイト同一で保持した。元のマスター・テーマ・レイアウトも保持した。
最終PDFの先頭には元PDF第1ページを直接複写した。再描画・画像置換・文章再制作は行っていない。
1倍・2倍・3倍レンダリングの全画素が一致した。詳細はevidence/final_display_audit.json。
以降の図表は編集可能なPowerPoint図形である。散布図の全460点、棒グラフ、数式・表・矢印も編集できる。

2. フォントと階層
元PPTXの日本語・英数字指定：Noto Sans JP。
タイトル：16pt、太字、濃紺。本文：12pt、標準。経路見出し：12pt。成果指標等の見出し：14pt・太字。
元の左端ラベルに10pt・太字がある。追加ページの軸目盛・出典注記はこの10pt階層を使用した。
元本文の固定行送り15.2pt、タイトル27pt等を参考に、追加本文は15.2pt、同一行階層内で統一した。
日本語・英数字とも同一書体。字間の独自拡張は行っていない。
追加タイトルの位置は左0.47in、上0.14in。本文範囲は左右約0.47in、幅約12.4in。

3. 元PDFの埋込名と書体に関する確認
元PDFの埋込フォント名はNotoSansJP-Thinである。ただし元PPTXの指定はNoto Sans JPで、12pt本文と太字指定を持つ。
以前の静的TTFは実ウェイト400/700にもかかわらずfamily/style名がともにThinのままであった。
この名前不整合を解消し、同じNoto Sans JPの可変フォントからRegular(400)/Bold(700)を生成した。
別書体へ置換したのではない。元PDF第1ページには修正を一切適用せず、そのまま保全した。
追加ページの実使用文字はNotoSansJP-Regular/Boldのみ。数式の下付きtは別書体が使われたためv(t)等へ修正し、再監査した。
PPTX第1枚目は元の編集可能なXMLを保持している。端末での組版はその端末のNoto Sans JP環境に依存する。
配布時の表示を固定する閲覧用成果物は、第1ページを直接保全したPDFである。

4. 色
タイトル・経路①：#002060。経路②：#087E88。経路③：#6A5794。
本文：#000000。背景・濃灰箱の文字：#FFFFFF。
濃灰色の箱：#808080（元テーマbg1の50%相当）。薄灰色の箱：#F2F2F2（95%相当）。
元の補助色：#D6E0E8。新しい色は導入していない。
状態の違いは新しい警告色でなく、文字ラベルと実線・破線で表現する。

5. 図形・表・配置
元と同じ角丸矩形。角丸調整値0.055。塗りのみ、通常の外枠なし。テーマ由来の影を明示的に無効化した。
表は濃灰色の見出し・白字と薄灰色の本文セル。行・列は白い隙間で分離する。
矢印・罫線は黒・濃紺・青緑・灰色を用途別に使う。通常0.8〜1.2pt、補助罫線0.35pt。
第1枚目の図形が基本的に枠なしであるため、線幅を機械的複製せず、同じパレット内で図の可読性を保つ。
縦横比16:9。PPTX寸法13.333333×7.5in。PDFページ寸法は元第1ページと全12枚一致。
因果図・比較表・散布図・棒グラフに応じて配置を変え、元の情報階層と余白を継承した。

6. 用語
第1枚目の①②③を固定。技術経路Aは①②、技術経路Bは③に対応する。
「走行時DC電力量」は「走行時のバッテリー消費電力量」の現行モデル境界を第7枚で定義した略記である。
配達完了時刻と帰庫時刻、訪問順序と走行状態、材料比容量とパック比エネルギーを区別した。
追加本文は「である」調。第1枚目の敬体・相談事項は変更していない。
'''
(O/'reports/デザイン仕様.txt').write_text(design_report,encoding='utf8')

change_report='''改訂内容の報告 — 15枚から12枚へ

1. 目的
交通・ITS分野の佐藤先生との約50分の研究相談用に、研究の問い、2つの技術経路、3つの評価工程、定量結果、相談論点を再構成した。
既存の15枚PDF・PPTX、研究原データ、Step3〜5の成果物は変更していない。

2. スライド対応
旧1→新1：完全保全。
旧2→新2：研究目的に加え、事例に限定した学術的貢献を明示。
旧4・旧14の構造説明→新3：2技術経路と3評価工程の対応、接続の証拠状態を図化。
旧3・旧4→新4：大田区、単一デポ、需要、固定条件、B/Cの違いを比較表へ統合。
旧5・旧6・旧7→新5・新6：件数中心の説明から旅行時間差・規模別・設定別の結果と成立条件へ再編。
旧8・旧9・旧10→新7・新8：電力量モデルの正確な数式・境界と、保存軌跡の新たな具体的集計を掲載。
旧11・旧12・旧13→新9・新10：材料会計、記号感度、実際に計算した100kg差、相殺境界へ統合。
旧14と各頁の重複留保→新11：成果／追加可能A／限定可能B／対象外Cに集約。
旧15→新12：交通モデル・配送サービス・電力量精緻化の3問を、仮定／不確実性／判断事項で具体化。
各頁で繰り返されていた未実証の一般論を減らし、数値の読み違いを防ぐ局所的な留保だけを残した。

3. 追加図表
新3：保存計算、仮定下の計算、未検証接続をラベルと線種で区別した作用仮説図。
新4：B系列とC系列の条件比較表。
新5：規模別の平均旅行時間差の棒グラフ、設定別比較、全出力と入力平均の分布要約。
新7：合計機械仕事の正値化を明記した電力量の数式。
新8：距離とDC電力量、移動時間とDC電力量の散布図（全460点）、抵抗感度、仕事内訳。
新9：部材質量会計と比容量の解析感度。
新10：1000→1100kgの有限差分と相殺条件、参考扱いの具体境界。

4. B系列の主な数値
460入力、8設定、各10測定、36,800保存計画。改善0、同等28,200、悪化8,600。
ΔJは候補−greedy。平均+441.790609秒、中央値0秒、範囲0〜9483.990487秒、出力SD1459.379051秒。
入力ごとの80出力平均を集計した中央値7.473770秒、入力間SD622.305258秒を別記した。
設定別平均はGrover p2 +1766.046542秒、p3 +1762.035546秒、その他6設定はいずれも+1.040464秒。
数値は既存採用済みBの保存結果から再集計した。新しい量子・SUMO実験は実行していない。

5. C系列と質量感度の追加計算
材料値を使わない比較用走行質量1000kgで全460保存軌跡を再評価した。
下限抵抗のDC電力量：平均2.798871kWh、中央値2.419850kWh、範囲0.992121〜6.247564kWh。
距離6.758759〜41.005836km。移動時間はv>0.1m/s区間の秒数と定義し、停車を含む観測時間と区別した。
下限条件の順位相関：距離0.992762、移動時間0.962769。固定集合の記述統計であり、因果推論や母集団CIではない。
上限抵抗へ変更した同一軌跡の増加は平均67.731271Wh、個別増加率の平均2.475518%。
1000→1100kgの平均増加は236.890601／243.287710Wh（下限／上限）。線形近似ではなく凍結核で直接評価した。
局所微分2.368077／2.431780Wh/kgは既存採用済み結果と一致する。
加減速等の内訳は正の合計車輪仕事区間を使う符号付き成分会計である。各成分を個別に正値化したものではない。

6. 材料値の採用区分
T08の記号感度、ΔM=b−δ、材料非依存DC応答を主とした。
5.448kg、9.723kg、5.978kgは、入力未適格の参考例であることを同じ欄と脚注に表示した。
約0.413%という材料依存の削減率は、実材料の代表効果や要旨の主結果として掲載していない。
正極比容量+10%→正極塗工材質量−9.09%は解析式の説明例で、完成パック全体や現実の材料性能値ではない。

7. 出典と再現
研究成果物と新しい集計をevidence/source_ids.json、evidence/quantitative_claim_ledger.csvで対応させた。
読取元493ファイルのSHA256をsource_manifest.csvに保存し、最終時点でも全件一致を確認した。
analyze_revision.pyで集計を再現できる。元成果物は書き換えない。保存軌跡の絶対パスが必要で、納品フォルダ単体で全計算を再実行できるとは主張しない。
'''
(O/'reports/改訂内容の報告.txt').write_text(change_report,encoding='utf8')

audit_report=f'''学術監査結果 — 佐藤先生相談用・改訂12枚

総合判定：提示した対象・仮定・採用区分の範囲で使用可能。現実の因果効果の実証は未完了である。
監査は同一作成者による分離工程であり、独立研究者の査読ではない。

1. 根拠の優先順位
Step3の統合提案を確認し、Step4科学的採用判断を制約として適用した。
Step5の再分析・現行本文をB統計の基準とし、T08/T09最終報告で材料側の保留を確認した。
ファイルの新しさや数値再現PASSだけで、材料入力HOLDを解除しない。
Step4の旧ΔJ符号（greedy−候補）は保存されているが、本資料はStep5と依頼指定の候補−greedyに統一した。

2. 修正した学術的問題
・3評価工程と2技術経路の混同を解消し、②は計画差を電力量に接続する評価工程とした。
・実運用の因果効果と、保存計算の対応・モデル内計算を区別した。
・改善0件だけでなく、秒単位の平均・中央値・範囲・ばらつき・規模・設定差を示した。
・36,800を独立標本として扱わず、460入力、25需要群、26親入力、入力内測定反復を明示した。
・旅行時間J、帰庫、最終顧客の配達完了、顧客別契約期限を区別した。
・共通上限遵守100%と、未検証の契約定時配達率を区別した。
・B計画とC軌跡の入力対応未確認を維持し、直接結合しなかった。
・観測時間と移動時間を区別した。停止原因を信号に帰属しなかった。
・電力量は合計機械仕事を正値化してから効率で割る。成分別正値化や負仕事の回生化を行わなかった。
・材料の比容量、パックの比エネルギー、完成パック、実車効果を区別した。
・材料依存の参考値は主結果と分離し、未知部材をゼロで補わなかった。
・媒介概念・会計恒等式そのものを新発見とせず、事例と証拠対応に貢献を限定した。

3. 数値の検証
analyze_revision.pyの{A['checks']}項目がPASS。元分数によるB全36,800差、期限・作業・容量条件、指定支持内最小を確認した。
C保存460軌跡のSHA256、1秒刻み、保存距離・停止割合、既存1000/1250kg端点を照合した。
1000/1100/1250kgを凍結核で計算。代表3軌跡×2抵抗の1100kg値を独立スカラー積算で照合した。
成分の符号付き正区間会計の和がDCに一致することを全920条件で確認した。
新しい集計の適格性は凍結モデル内に限る。実車への妥当性がこの検算で認定されたわけではない。
全数値のファイル・単位・集計条件・採用役割はquantitative_claim_ledger.csv。

4. 主結果と参考結果
主：Bの同一入力主greedy差、指定支持の制約、モデル内完了・帰庫の区別、材料非依存DC感度、解析的質量感度。
追加記述：C距離・移動時間・加減速等とDCの関係、抵抗2条件の感度、100kg有限差分。
参考のみ：Chen逆算qに基づくT08/T09の具体相殺境界。元のqペアは実用全電池への適格性がHOLDである。
比容量の10%例は式の相対感度の説明であり、実材料入力を採用した計算ではない。

5. 確認できなかった事項
・BとCの共通物理入力対応、および新しい候補計画から同一条件の軌跡・電力量への接続。
・道路の現実妥当性・動的受入、背景交通下での相対順位の安定性。
・顧客別契約期限、時計時刻としての出発、計画取得・共有・採用イベント、全工程締切。
・候補と主greedyの完全な予算・出力規則統制。未見需要と独立学習への一般化。
・未証明46入力の真の最適値。保存MIPのみ41入力の外部証明。今回は主greedy差を用い、最適gapを補作していない。
・C停車の原因分離。配達作業停車、待機、交通停止を速度だけで分類していない。
・回生、補機、勾配、積載変動、旋回、未観測末端の実際の電力量。
・逆算容量の基準サイクルと実用full-cell、平均電圧・利用率・負極・完成BOMの確定。
・量子による実材料改善、量子実機の総性能、実車運用効果。
今回は先行研究の網羅的レビューや外部論文の新規検証を行っていない。

6. 残存する研究上の限界
固定集合の記述で、無作為抽出母集団の因果効果・p値・独立標本CIを主張しない。
相関は走行距離や規模の共変動を含み、距離・停止・加減速の独立した寄与の識別ではない。
DC成分比は選んだ正区間会計の配分であり、交通施策による因果寄与率ではない。
負の機械仕事は回収しない。補機を除くため、長い停車が実車の消費へ与える影響は未評価である。
1,000kg等は比較用の仮想走行質量であり、対象車両の実測質量としての採用ではない。
1000〜1250kgの質量単調性は同じ保存軌跡・物理条件に限る。軌跡・荷重・制御が変われば別検証が必要。
相殺条件δ=bは会計恒等式である。δはS−基準の未知部材差で正負があり、実値は未同定。

7. 追加検証の分類
A 現研究で追加可能：保存データの層別、入力・設定・測定の分離、仮想期限への感度、同一軌跡の物理感度。
B 限定的に可能：道路・交通モデルの検査、適用配送条件、計画締切・採用・実行条件の専門家照合。
C 対象外：量子由来実材料改善、完成パック試作、QPU総性能、実車の運用実証。
実施できることと実施すべきことを同一視せず、佐藤先生の助言で優先順位を決める。

8. 専門家への相談事項
質問1：背景交通なしのSUMO軌跡は、旅行時間・電力量の相対比較にどの範囲で使えるか。最低限必要な検証は何か。
質問2：顧客時間窓なし・作業102秒・帰庫上限32400秒から定時配達率へ進むため、必要な期限・作業・採用条件は何か。
質問3：交通量、信号、荷重変化、勾配、回生のうち、経路間比較を変えやすく優先検証すべき要因と必要データは何か。
最終スライドは各問を仮定／不確実性／判断依頼の3段にした。
50分の目安は説明32分・最終の議論18分。途中の質疑に応じ説明を短縮する。

9. 表示・保全監査
第1スライドXMLと関連定義：元と同一。最終PDF第1ページ：元PDFから直接保全し、3解像度で全画素一致。
新ページの実使用書体：Noto Sans JP Regular/Boldのみ。フォント置換文字列0件。
書体名Thinに関する元PDFの事情はデザイン仕様に明記した。PPTXの端末別組版はインストール書体に依存する。
全12頁をレンダリングし、全頁プレビューと代表拡大画像を確認する。
全文字列の抽出一致、用色のパレット内、図形のページ外0件を確認した。
自動の文字重なり候補はfinal_display_audit.jsonに記録し、目視の対象とする。
既存読取493ファイルのSHA256は最終時点でも全件一致。保全対象は使用・確認したファイル群であり、リポジトリ全ファイルの無変更監査ではない。

10. 参照した成果物
'''+ '\n'.join(f'{k}: {R/v}' for k,v in ids.items()) + '''
追加でStep3採用レビュー、Step4科学台帳、Step5主張対応台帳、T08/T09最終報告・入力採用表を確認した。
source_manifest.csvに実際に照合した全ファイルのパス・SHA256を記録した。
'''
(O/'reports/学術監査結果.txt').write_text(audit_report,encoding='utf8')

# A concise source/condition table is included separately for review, not buried only in slide notes.
with (O/'reports/スライド別出典と時間配分.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['slide','title','minutes','refs','notes']);w.writeheader()
 for z in reg:w.writerow(z|{'refs':' / '.join(z['refs'])})

# Make the three requested reports readable together as a standalone PDF.
report_pdf=fitz.open()
regular=fitz.Font(fontfile=str(O/'fonts/NotoSansJP-Regular.ttf'))
boldfile=str(O/'fonts/NotoSansJP-Bold.ttf')
for reportfile in ['デザイン仕様.txt','改訂内容の報告.txt','学術監査結果.txt']:
 current=None;baseline=0
 def new_page():
  page=report_pdf.new_page(width=595.276,height=841.89)
  page.insert_font(fontname='NotoR',fontfile=str(O/'fonts/NotoSansJP-Regular.ttf'))
  page.insert_font(fontname='NotoB',fontfile=boldfile)
  page.insert_text((42,35),'研究紹介資料｜デザイン・改訂・学術監査',fontname='NotoB',fontsize=12,color=(0,32/255,96/255))
  page.insert_text((42,816),f'佐藤先生相談用　｜　報告 {len(report_pdf)}',fontname='NotoR',fontsize=9,color=(.5,.5,.5))
  return page,64
 for rawline in (O/'reports'/reportfile).read_text().splitlines():
  chunks=[];chunk=''
  for ch in rawline:
   if regular.text_length(chunk+ch,fontsize=10.5)>510:
    chunks.append(chunk);chunk=ch
   else:chunk+=ch
  chunks.append(chunk)
  for chunk in chunks:
   if current is None or baseline>785:current,baseline=new_page()
   if chunk:current.insert_text((42,baseline),chunk,fontname='NotoR',fontsize=10.5)
   baseline+=16
report_pdf.save(O/'reports/デザイン・改訂・学術監査報告.pdf',garbage=4,deflate=True)

all_outputs=[]
for p in O.rglob('*'):
 if p.is_file() and p.name!='output_manifest.csv' and p.suffix!='.log':all_outputs.append(dict(path=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=sha(p)))
with (O/'evidence/output_manifest.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(all_outputs)
print(json.dumps(audit,ensure_ascii=False,indent=2))
