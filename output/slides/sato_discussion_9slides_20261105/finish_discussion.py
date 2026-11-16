"""Render, preserve the opening PDF page, check content, and write concise reports."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
from fractions import Fraction
import json,csv,re,math,hashlib
import pymupdf as fitz
from pptx import Presentation
from PIL import Image,ImageDraw

O=Path(__file__).resolve().parent;R=O.parents[2];PREV=R/'output/slides/sato_revision_20261105'
stem='研究紹介_佐野巧馬_佐藤先生研究相談_本編9枚_補足4枚'
pptx=O/(stem+'.pptx');pdf=O/(stem+'.pdf')
refpdf=PREV/'研究紹介_佐野巧馬_佐藤先生相談用_改訂12枚.pdf'
oldpptx=PREV/'研究紹介_佐野巧馬_佐藤先生相談用_改訂12枚.pptx'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm=lambda s:re.sub(r'\s+','',s)
q=Presentation(pptx)
raw=fitz.open(O/'render'/(stem+'.pdf'));old=fitz.open(refpdf)
final=fitz.open();final.insert_pdf(old,from_page=0,to_page=0);final.insert_pdf(raw,from_page=1,to_page=12)
final.set_metadata({'title':'佐藤先生との研究相談｜本編9枚・補足4枚','author':'佐野巧馬','subject':'説明18分・意見交換32分'})
final.save(pdf,garbage=4,deflate=True);final.close();d=fitz.open(pdf)
assert len(q.slides)==len(d)==13
with ZipFile(oldpptx) as a,ZipFile(pptx) as b:
 exact_slide=a.read('ppt/slides/slide1.xml')==b.read('ppt/slides/slide1.xml')
 exact_rels=a.read('ppt/slides/_rels/slide1.xml.rels')==b.read('ppt/slides/_rels/slide1.xml.rels')
assert exact_slide and exact_rels
pixels=[]
for scale in [1,2,3]:
 a=old[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False);b=d[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
 pixels.append(dict(scale=scale,identical=a.samples==b.samples,sha256=hashlib.sha256(a.samples).hexdigest()))
assert all(p['identical'] for p in pixels)
missing=[];fallback=[];outside=[];overlap=[];fonts=Counter();colors=set();oob=[]
for i,(s,page) in enumerate(zip(q.slides,d)):
 if i:
  for sh in s.shapes:
   if sh.left<0 or sh.top<0 or sh.left+sh.width>q.slide_width+100 or sh.top+sh.height>q.slide_height+100:oob.append([i+1,sh.shape_id])
   if sh.has_text_frame and sh.text.strip() and norm(sh.text) not in norm(page.get_text()):missing.append(dict(page=i+1,shape=sh.shape_id,text=sh.text))
   for z in sh._element.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr'):colors.add(z.get('val'))
 lines=[]
 for block in page.get_text('dict')['blocks']:
  for ln in block.get('lines',[]):
   st=''.join(x['text'] for x in ln['spans']);rr=fitz.Rect(ln['bbox'])
   if st.strip():lines.append((rr,st))
   if not page.rect.contains(rr):outside.append(dict(page=i+1,text=st))
   for span in ln['spans']:
    if i:
     fonts[span['font']]+=1
     if 'NotoSansJP' not in span['font']:fallback.append(dict(page=i+1,font=span['font'],text=span['text']))
 if i:
  for j,(r,st) in enumerate(lines):
   for r2,t in lines[j+1:]:
    area=r&r2
    if area.width>3 and area.height>3:overlap.append(dict(page=i+1,a=st,b=t,box=list(area)))
 page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(O/'render'/f'page_{i+1:02d}.png')
assert not missing,missing
assert not fallback,fallback
assert not oob,oob
assert not outside,outside
assert colors<=set(['002060','087E88','6A5794','808080','F2F2F2','000000','FFFFFF','D6E0E8']),colors
assert all(x.rect==d[0].rect for x in d)
questions=json.loads((O/'evidence/questions.json').read_text())
assert all(norm(st) in norm(d[7].get_text()) for st in questions['slide8'])
assert all(norm(st) in norm(d[8].get_text()) for st in questions['slide9'])
def contact(indices,name,cols=3):
 rows=math.ceil(len(indices)/cols);im=Image.new('RGB',(cols*600,rows*366),'#D6E0E8')
 for j,i in enumerate(indices):
  p=d[i];pix=p.get_pixmap(matrix=fitz.Matrix(600/p.rect.width,600/p.rect.width),alpha=False);im.paste(Image.frombytes('RGB',(pix.width,pix.height),pix.samples),((j%cols)*600,(j//cols)*366+25));ImageDraw.Draw(im).text(((j%cols)*600+8,(j//cols)*366+6),str(i+1) if i<9 else 'Backup '+str(i-8),fill='black')
 im.save(O/name)
contact(list(range(9)),'本編9枚プレビュー.png');contact(list(range(13)),'全13ページプレビュー.png')

# Verify the required values against the same original numerical evidence.
src=R/'review_outputs/quantum_ev_step5_20261105/data/B_PLAN_GAPS_36800.csv'
with src.open() as f:b=list(csv.DictReader(f))
delta=[float(x['delta_s']) for x in b]
assert len(b)==36800 and len(set(x['problem_id'] for x in b))==460
assert all(Fraction(x['J_candidate_fraction'])-Fraction(x['J_greedy_fraction'])==Fraction(x['delta_fraction']) for x in b)
assert round(math.fsum(delta)/len(delta),1)==441.8 and sorted(delta)[len(delta)//2]==0 and round(max(delta),1)==9484.0
assert sum(x<0 for x in delta)==0
with (PREV/'data/C_trajectory_model_results.csv').open() as f:c=list(csv.DictReader(f))
values={}
for rc,expected in [('CRR_LOWER_BOUND',236.9),('CRR_UPPER_BOUND',243.3)]:
 rows=[x for x in c if x['rolling_case']==rc]
 assert len(rows)==460 and len(set(x['trajectory_sha256'] for x in rows))==460
 assert all(abs((float(x['DC_1100_Wh'])-float(x['DC_1000_Wh']))-float(x['delta_100kg_Wh']))<1e-9 for x in rows)
 mean=math.fsum(float(x['delta_100kg_Wh']) for x in rows)/460
 assert round(mean,1)==expected
 values[rc]=mean
before=json.loads((O/'evidence/protected_sources_before.json').read_text())
preserved=[dict(**x,sha256_after=sha(x['path']),unchanged=sha(x['path'])==x['sha256']) for x in before]
assert all(x['unchanged'] for x in preserved)
audit=dict(main_slides=9,backup_slides=4,total_pages=13,explanation_minutes=18,discussion_minutes=32,first_slide_xml_identical=exact_slide,first_slide_relationships_identical=exact_rels,first_pdf_page_pixel_checks=pixels,missing_text=missing,fallback_fonts=fallback,text_outside_page=outside,text_overlap_candidates=overlap,shape_outside_page=oob,font_spans=dict(fonts),palette=sorted(colors),question_texts_preserved=True,protected_sources=len(preserved),source_preservation=preserved,verified_B=dict(n=len(b),mean=math.fsum(delta)/len(delta),median=0,max=max(delta),improved=0),verified_mass_100kg_means=values)
(O/'evidence/validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))

report='''研究相談用資料の修正報告

構成：本編9枚＋任意の補足4枚。説明18分・意見交換32分を想定する。
既存12枚版、原資料、採用済み成果物は上書きしていない。

本編ごとの変更
1. 研究概要：元の第1枚目を完全維持した。PPTXのスライドXML・関連定義をバイト同一で保持した。PDFは元第1ページを直接複写し、3解像度で全画素一致を確認した。
2. 対象と問題設定：配送拠点、配送先、EV、訪問経路を編集可能な模式図として追加した。図は実道路や実験ルートではないと明記し、架空の実験値を追加していない。
3. 目的と技術経路：二つの技術経路を並列化した。第1枚目の①②③は評価工程として維持し、技術経路1→①②、経路2→③と対応付けた。保存計算／仮定下のモデル／未実証を線・ラベルで識別した。
4. モデルと条件：出発→移動・作業→完了→帰庫を図示した。作業102秒、顧客時間窓なし、共通上限32400秒を配送計画側の条件として示し、保存軌跡の条件へ転用しなかった。B/Cという内部名を主見出しから外した。
5. 計画結果と成立条件：旧5・6を統合し、平均+441.8秒、中央値0.0秒、最大悪化+9484.0秒、主対照より短い計画0件を中心にした。候補の存在→取得→出発までの採用を3段で説明した。共通上限と契約定時配達率の違い、CPU模擬、反復の依存を残した。
6. 電池質量と電力量：旧7〜10の中心を統合した。材料→パック質量→車両質量→DC電力量を示し、固定した走行軌跡は電力量計算への別入力として描いた。1000→1100kgの平均差+236.9/+243.3Whを棒グラフで示した。質量差の相殺を文章と簡単な差引きで説明した。
7. 現時点の成果と限界：二つの技術経路について、条件付きの確認範囲と未検証部分を対比した。抽象的な社会技術システムの説明や、検証していない制度・主体間調整を追加していない。
8. 研究動向と量子技術の可能性：指定された5問をそのまま質問文として掲載した。研究動向や古典手法の不足を本資料の事実として断定していない。
9. 研究範囲と追加検証：指定された5問をそのまま掲載した。適用条件と検証の優先順位を決める議論に使う。

補足の構成
補足1：旧5枚目の規模別・設定別の旅行時間差。
補足2：旧7枚目の電力量モデルの数式・抵抗・負の仕事の扱い。
補足3：旧8枚目の保存460軌跡の散布図と電力量集計。
補足4：旧9枚目の材料・部材からパック質量への計算と留保。
補足は本編の18分には含めない。既存の数値と根拠を変更していない。

数値と出典の確認
旅行時間差はStep5の元CSV全36800行を読み、候補−greedyの元分数差を全件照合した。平均・中央値・最大・非改善件数の丸めを確認した。
100kgの差は前版のC_trajectory_model_results.csvを読み、同一軌跡のE(1100)−E(1000)と保存差を全920条件で照合した。460軌跡ずつの平均を確認し、物理モデルや材料入力の新規変更は行っていない。
数値は実材料性能や実EV効果へ読み替えていない。転がり抵抗2条件は同じ460軌跡を共有する。
発表者ノートに元のファイル・集計条件・時間配分を記録した。

デザインと表示
Noto Sans JP、タイトル16pt、本文12pt、質問14pt、出典・軸目盛10ptを維持した。
濃紺・青緑・紫・灰色・白・黒のみを使い、元の角丸・余白を継承した。過剰なカードは増やしていない。
追加ページの実使用フォントはNoto Sans JP Regular/Boldのみ。元PDF先頭の埋込名Thinは元ページのまま保全した。
全13ページを実際にレンダリングし、文字列の欠落、ページ外図形、別書体への代替、文字重なり候補を検査した。検査結果はevidence/validation.jsonに保存した。
PPTXの端末での組版はインストールされた同名フォントに依存する。閲覧用PDFは表示を固定する。

50分の配分目安
第1枚2分、第2枚2分、第3枚3分、第4枚2分、第5枚4分、第6枚3分、第7枚2分＝説明18分。
第8枚・第9枚で計32分。5問ずつを順番にすべて消化するのでなく、重要な論点から深掘りする。
'''
(O/'reports/スライド別修正報告.txt').write_text(report,encoding='utf8')
unresolved='''根拠確認が限定される記述・未実証事項の一覧

根拠のない新しい実験値・成果を追加した箇所はない。
以下は不明値を補作せず、未実証または相談事項として維持した。

1. 顧客別契約期限による定時配達率
保存計画の共通上限内割合は両側100%だが、契約上の定時配達率は未検証である。

2. 計画取得から実採用・配送開始への接続
実際の計画締切、全工程時間、採用・共有・出発の運用記録は未同定である。採用は成果ではなく必要条件として説明した。

3. 道路・交通・配送計画と走行軌跡の対応
地域道路の動的受入は成立していない。背景交通、実配送、B計画とC保存軌跡の入力対応は未確認である。一体的な検証済み実験としない。

4. 材料・実用セル・完成パック・実EV
量子による実材料改善、実用セルへの適格性、完成部材構成、実車省電力は未実証である。仮定下の質量計算と区別した。

5. 量子優位性・実機性能・公平な総性能順位
CPU模擬を量子実機と扱わない。古典側との予算・出力規則の完全統制は未完了であり、平均旅行時間差を量子一般の優劣へ拡張しない。

6. 公開リポジトリとローカル採用成果物の範囲差
指定GitHubのREADMEを接続ツールで確認した。そこには3・4顧客の旧小規模系列が説明されている。
今回の460入力・36800計画の数値は、公開READMEだけでは照合できない。ローカルのStep4採用判断、Step5の元CSV・ノート、前版の数値監査を根拠とした。
公開READMEの旧小規模結果と混ぜて数値を作っていない。取得したREADMEの範囲とcontent SHAをevidence/github_README_excerpt.txtに保存した。

7. 交通・ITS研究動向と古典手法の不足
現状や将来可能性の回答を資料側で補完していない。第8枚は佐藤先生に見解を伺う質問であり、古典手法の不足や量子の有用性を断定するものではない。

第1枚目の既存表現は今回の絶対条件に従って変更していない。後続ページで現在の確認範囲を補足している。
'''
(O/'reports/根拠確認が限定される記述と未実証事項.txt').write_text(unresolved,encoding='utf8')
reg=json.loads((O/'evidence/slide_register.json').read_text())
with (O/'reports/スライドと時間配分.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['slide','title','minutes','type']);w.writerow([1,'研究全体の概要（完全維持）',2,'本編説明'])
 for x in reg:w.writerow([x['slide'],x['title'],x['minutes'],'説明' if x['slide']<=7 else ('意見交換' if x['slide']<=9 else '任意補足')])

# A readable PDF report accompanies the plain-text deliverables.
reportdoc=fitz.open();fontpath=PREV/'fonts/NotoSansJP-Regular.ttf';font=fitz.Font(fontfile=str(fontpath))
for name in ['スライド別修正報告.txt','根拠確認が限定される記述と未実証事項.txt']:
 page=None;y=0
 for st in (O/'reports'/name).read_text().splitlines():
  lines=[];s=''
  for ch in st:
   if font.text_length(s+ch,fontsize=10.5)>510:lines.append(s);s=ch
   else:s+=ch
  lines.append(s)
  for s in lines:
   if page is None or y>784:
    page=reportdoc.new_page(width=595.276,height=841.89);page.insert_font(fontname='NotoR',fontfile=str(fontpath));y=58
    page.insert_text((42,32),'佐藤先生との研究相談｜修正報告',fontname='NotoR',fontsize=12,color=(0,32/255,96/255))
    page.insert_text((42,818),str(len(reportdoc)),fontname='NotoR',fontsize=9)
   if s:page.insert_text((42,y),s,fontname='NotoR',fontsize=10.5)
   y+=16
reportdoc.save(O/'reports/修正報告と根拠確認事項.pdf',garbage=4,deflate=True)
outputs=[]
for p in O.rglob('*'):
 if p.is_file() and p.name!='output_hashes.csv' and p.suffix!='.log':outputs.append([str(p.relative_to(O)),p.stat().st_size,sha(p)])
with (O/'evidence/output_hashes.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['path','bytes','sha256']);w.writerows(outputs)
print(json.dumps({k:audit[k] for k in audit if k!='source_preservation'},ensure_ascii=False,indent=2))
