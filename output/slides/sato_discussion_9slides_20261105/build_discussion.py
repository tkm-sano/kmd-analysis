"""Nine-slide consultation narrative, with four optional technical backup slides."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
from fractions import Fraction
import json,csv,math,hashlib
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.xmlchemy import OxmlElement

O=Path(__file__).resolve().parent;R=O.parents[2]
PREV=R/'output/slides/sato_revision_20261105'
OLD=PREV/'研究紹介_佐野巧馬_佐藤先生相談用_改訂12枚.pptx'
SRC=R/'研究紹介_佐野巧馬.pptx'
STEM='研究紹介_佐野巧馬_佐藤先生研究相談_本編9枚_補足4枚'
DEST=O/(STEM+'.pptx')
P=Presentation(SRC)
N,T,V,G,F,K,W='002060','087E88','6A5794','808080','F2F2F2','000000','FFFFFF'
FONT='Noto Sans JP'
B=json.loads((PREV/'data/B_summary.json').read_text());C=json.loads((PREV/'data/C_summary.json').read_text())
sources=json.loads((PREV/'evidence/source_ids.json').read_text())
with (PREV/'data/C_trajectory_model_results.csv').open() as f:points=list(csv.DictReader(f))
register=[];geoms=[]
helper=(PREV/'build_revision.py').read_text()
helper=helper[helper.index('def tx('):helper.index('# 02:')]
helper=helper.replace("f'{len(P.slides):02d} / 12'","f'{len(P.slides):02d} / 9'")
exec(compile(helper,str(PREV/'build_revision.py'), 'exec'))

def ellipse(s,x,y,w,h,color=N,fill=W):
 z=s.shapes.add_shape(MSO_SHAPE.OVAL,Inches(x),Inches(y),Inches(w),Inches(h));z.fill.solid();z.fill.fore_color.rgb=RGBColor.from_string(fill);z.line.color.rgb=RGBColor.from_string(color);z.line.width=Pt(.8)
 return z
def warehouse(s,x,y):
 roof=s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE,Inches(x),Inches(y),Inches(1.25),Inches(.58));roof.fill.solid();roof.fill.fore_color.rgb=RGBColor.from_string(G);roof.line.fill.background()
 rect(s,x+.08,y+.50,1.09,.67,G,False)
 rect(s,x+.40,y+.78,.44,.39,W,False)
 tx(s,x-.22,y+1.32,1.70,.60,'配送拠点\n（デポ）',14,N,True,PP_ALIGN.CENTER)
def ev(s,x,y):
 rect(s,x,y,1.05,.43,F,False,line=N);rect(s,x+.76,y+.07,.23,.24,W,False,line=N)
 ellipse(s,x+.12,y+.34,.20,.20,N,N);ellipse(s,x+.74,y+.34,.20,.20,N,N)
 tx(s,x+.10,y+.055,.60,.30,'EV',12,N,True,PP_ALIGN.CENTER)
def chain(s,labels,y,color=N,statuses=None):
 n=len(labels);w=2.10;gap=.45
 for i,label in enumerate(labels):
  x=.47+i*(w+gap);node(s,x,y,w,.85,label,color)
  if i<n-1:
   cc,ds=(statuses[i] if statuses else (color,False));line(s,x+w+.035,y+.425,x+w+gap-.055,y+.425,cc,1.15,ds,True)

# 02 — a deliberately schematic illustration, not invented spatial evidence.
s=base('都市EV配送における研究対象と問題設定','単一の配送拠点から複数の配送先へ荷物を運ぶ、東京都大田区を想定したEV配送を対象とする。','同じ配送先・車両割当・出発条件の下で、訪問順序と電池質量の違いを考える。',['A2','B2','C2'],2,
'図は配送の仕組みを示す模式図で、実道路の形状や実験ルートではない。1台の比較対象を代表して描いている。配送先A〜Eは説明用ラベルで、架空の実験値・地点を追加したものではない。研究用の需要であり実注文観測値ではない。KMD修士研究の紹介として説明する。')
depot=(1.73,3.45);stops=[(3.95,2.20),(6.63,2.45),(7.80,4.25),(5.70,5.25),(3.70,4.65)]
route=[depot,*stops,depot]
for a,b in zip(route,route[1:]):line(s,*a,*b,N,1.0,False,True)
warehouse(s,1.10,2.77)
for name,(x,y) in zip('ABCDE',stops):
 ellipse(s,x-.22,y-.22,.44,.44,N,W);tx(s,x-.22,y-.19,.44,.32,name,12,N,True,PP_ALIGN.CENTER)
 tx(s,x-.70,y+.34,1.40,.32,'配送先'+name,12,N,False,PP_ALIGN.CENTER)
ev(s,3.05,3.10)
tx(s,4.55,3.46,2.55,.60,'訪問順序に沿って\n配送・帰庫する。',12,N)
tx(s,.65,5.91,8.0,.28,'模式図：実道路・実験の経路を示したものではない。',10,G)
rect(s,9.15,1.78,3.72,4.16,F)
tx(s,9.36,1.99,3.30,.36,'研究で固定するもの',14,N,True)
tx(s,9.36,2.64,3.30,1.55,'・配送先と配送需要\n・車両への割当\n・配送の開始条件\n・電池以外の車両条件',12)
tx(s,9.36,4.47,3.30,.36,'着目する違い',14,N,True)
tx(s,9.36,5.07,3.30,.68,'配送計画による訪問順序と、\n電池に由来する車両質量。',12)
foot(s,'評価する指標','定時配達率と、走行時のバッテリー消費電力量（DC電力量）である。')

# 03 — technical route numbers are distinguished from the immutable opening diagram.
s=base('研究目的と二つの技術経路','量子計算が配送計画や材料に関する能力を改善した場合、配送成果に反映されるための条件を検討する。','技術的な改善が起こる条件と、その改善が配送成果に伝わる条件を分ける。',['A1','A2','B3','M1'],3,
'経路1・2は技術の作用経路。第1枚目の①②③は評価工程であり、経路1は①②、経路2は③に対応する。保存計算の確認は因果効果の実証ではない。経路1最後の接続は顧客契約期限による実証がないため破線。経路2の仮定入力から先はモデルの関係で、材料の実用性能を確定していない。計画採用や制度等を検証済み要素として追加していない。')
tx(s,.65,1.83,12.0,.33,'経路1：配送計画（第1枚目の①・②）',14,N,True)
chain(s,['量子最適化\nアルゴリズム','配送計画の\n取得','訪問順序','配達完了時刻','定時配達率'],2.40,N,[(N,False),(N,False),(T,False),(G,True)])
tx(s,.65,3.50,12.0,.34,'保存計画の比較はCPU模擬である。顧客別の期限による定時配達率と実運用は未検証である。',12)
tx(s,.65,4.20,12.0,.33,'経路2：電池材料（第1枚目の③）',14,V,True)
chain(s,['量子計算による\n材料物性評価','材料性能改善の\n可能性','電池パック\n質量','車両質量','走行時\nDC電力量'],4.77,V,[(G,True),(T,False),(T,False),(T,False)])
tx(s,.65,5.81,12.0,.33,'実材料の改善は未実証である。材料・部材の条件を仮定し、質量と電力量の関係を計算する。',12,V)
for x,cc,ds,lab in [(.65,N,False,'保存計算で評価'),(4.58,T,False,'仮定に基づくモデル計算'),(9.05,G,True,'現時点で未実証')]:
 line(s,x,6.57,x+.40,6.57,cc,1.2,ds,True);tx(s,x+.52,6.40,3.55,.34,lab,12,cc)

# 04 — temporal schematic plus two clearly separate comparison scopes.
s=base('配送モデルと評価条件','単一デポからの配送を対象とする。配送計画の比較と、保存走行軌跡からの電力量計算は別の評価である。','訪問順序に沿って移動し、各配送先で作業を終えた時刻を計算する。',['A2','B2','C1','C2'],2,
'計画比較はB系列、軌跡はC系列。内部名は主見出しに出さない。Bのready=0は時間原点で実時計ではない。Bは顧客固有の時間窓なし、顧客service102秒、容量216PE、共通horizon32400秒。これらをCに移植しない。Cの時間窓・停車は元の保存条件に従う。計画と軌跡の入力対応未確認、道路動的受入未成立を維持する。')
for x,w,label in [(.47,2.15,'デポを出発'),(3.05,3.42,'配送先：移動＋作業102秒'),(6.90,2.65,'次の配送先へ'),(9.98,2.89,'デポへ帰庫')]:
 node(s,x,1.84,w,.76,label,N)
 if x<9.9:line(s,x+w+.05,2.22,x+w+.36,2.22,N,1,False,True)
tx(s,3.25,2.83,5.55,.33,'配達完了時刻：到着後に作業を終えた時刻',12,N)
tx(s,9.92,2.83,2.95,.33,'帰庫上限32,400秒',12,N,True)
line(s,.47,3.45,12.87,3.45,G,.55)
tx(s,.65,3.77,5.72,.36,'配送計画を比較する条件',14,N,True)
tx(s,.65,4.43,5.72,1.31,'・配送先・車両割当・開始条件を固定する。\n・顧客ごとの時間窓は設定しない。\n・配達作業102秒、共通期限32,400秒である。\n・配送途中の充電・車両間の再割当は扱わない。',12)
tx(s,6.98,3.77,5.62,.36,'保存軌跡から電力量を計算する条件',14,T,True)
tx(s,6.98,4.43,5.62,1.31,'・保存された速度時系列を固定する。\n・背景交通なし、平坦路、空荷である。\n・回生ブレーキ・補機電力を含まない。\n・時間窓や停車条件は保存時の設定に従う。',12)
foot(s,'比較の範囲','配送計画と保存軌跡の入力対応は未確認であり、一体的な検証済み実験とは扱わない。')

# 05 — four required quantitative results, then three necessary conditions.
s=base('配送計画の計算結果と成立条件','旅行時間差 ΔJ＝候補計画の旅行時間−主greedy計画の旅行時間。正は悪化、負は改善を表す。','greedyは局所的な改善を繰り返す古典計算法であり、比較の基準である。',['B1','B2','B3','A1'],4,
'全36800保存計画、460入力、8設定、各10測定。CPUでの量子アルゴリズム模擬。Jは帰還を含む有向OD旅行時間和で、作業・待機を含まない。平均441.790609、中央値0、最大9483.990487、改善0。設定混合平均は単一方式の代表効果ではない。matching支持460で改善解不存在を確認したが全候補方式一般へ拡張不可。予算・初期解保持の比較条件差がある。保存計画は全て共通上限内であり契約定時率は未検証。')
rect(s,.47,1.76,12.4,1.02,F)
for i,(a,b) in enumerate([('平均旅行時間差','＋441.8秒'),('中央値','0.0秒'),('最大悪化','＋9,484.0秒'),('主対照より短い計画','0件')]):
 x=.65+3.10*i;tx(s,x,1.91,2.90,.30,a,12,N);tx(s,x,2.30,2.90,.34,b,14,N,True)
tx(s,.65,3.00,11.98,.50,'460入力×8設定×10測定＝36,800保存計画。量子側はCPU模擬であり、反復出力は独立標本ではない。',12)
labels=[('1. 良い計画が存在する','比較対象より良い計画が、\n探索する候補集合に含まれる。'),('2. 計算で取得できる','有限の学習・測定の範囲で、\nその計画を取得できる。'),('3. 出発までに採用できる','配送を始めるまでに計画を\n検証し、利用できる。')]
for i,(a,b) in enumerate(labels):
 x=.47+4.20*i;node(s,x,3.69,4.00,.55,a,N);tx(s,x+.17,4.44,3.66,.61,b,12)
 if i<2:line(s,x+4.02,3.97,x+4.17,3.97,N,.9,False,True)
tx(s,.65,5.44,12.0,.34,'指定した候補集合の一部では、主対照より良い計画が存在しないことを確認した。',12)
foot(s,'期限の区別','共通期限の遵守は両側100%である。顧客別の契約期限による定時配達率は未検証である。')

# 06 — mass response, entirely from the previous verified calculation.
s=base('電池質量と走行時DC電力量の関係','材料性能の変化を仮定し、電池の軽量化が車両質量と走行電力量へ伝わる条件を考える。','電池以外の車体・積載条件をそろえ、同じ保存軌跡で質量の影響を調べる。',['C1','C2','C3','M1'],3,
'車体・補強・荷重等の他条件を固定したパック置換で、パック質量差と車両走行質量差を1対1とする仮定。文中の1000→1100kgは運転者を含む比較用仮想走行質量。460保存軌跡×2転がり抵抗、同一凍結核で計算済み。平均有限差分236.8906009675/243.2877099666Whを1桁丸め。新たな再計算や材料入力採用はしていない。上限下限は転がり抵抗の2条件。追加部材差は基準との差で正負があり、完成パックは未確定。')
for x,w,label in [(.47,2.50,'材料性能'),(3.49,2.66,'電池部材・パック質量'),(6.67,2.50,'車両質量'),(9.69,3.18,'走行時DC電力量')]:
 node(s,x,1.99,w,.76,label,V)
 if x<9.5:line(s,x+w+.05,2.37,x+w+.45,2.37,T,1.15,False,True)
tx(s,9.69,1.62,3.18,.28,'同じ走行軌跡を入力',10,G,False,PP_ALIGN.CENTER)
line(s,11.28,1.90,11.28,1.98,T,.9,False,True)
tx(s,.65,2.94,11.98,.34,'質量を1,000kgから1,100kgへ変更したときの、同じ走行軌跡における平均電力量差',14,V,True)
for y,label,val in [(3.65,'下限抵抗条件',236.9),(4.37,'上限抵抗条件',243.3)]:
 tx(s,.65,y+.08,2.05,.33,label,12,V,True)
 rect(s,2.93,y,6.80*val/300,.42,V,False)
 tx(s,2.93+6.80*val/300+.22,y+.06,2.30,.36,f'＋{val:.1f} Wh',14,V,True)
tx(s,.65,5.12,11.98,.34,'同じ460保存軌跡と凍結した電力量モデルの下で得られた、条件付きの質量感度である。',12)
tx(s,.65,5.70,11.98,.34,'材料側の質量削減 − 追加部材の質量差 ＝ 軽量化。追加部材により効果が相殺され得る。',12,V,True)
foot(s,'結果の範囲','実材料の改善量や実EVの省電力効果ではない。材料計算から実材料への接続は未実証である。',V)

# 07 — a succinct two-route evidence boundary, without abstract social-system claims.
s=base('現時点で明らかになったことと研究上の限界','数値やモデルで確認した範囲と、実際の配送・電池で確認していない範囲を分ける。','今回の結果をもとに、修士研究で優先すべき追加検証について相談する。',['A1','B3','M1','A2'],2)
table(s,.47,1.77,[2.05,5.05,5.19],['技術経路','確認した関係（仮定下の計算を含む）','未検証の関係'],[
 ['経路1\n配送計画','・計画間の旅行時間差\n・指定候補集合内での改善余地\n・期限余裕と完了時刻の関係','・実際の計画採用と出発までの接続\n・顧客別の契約期限による定時配達率\n・実際の交通・配送での効果'],
 ['経路2\n電池材料','・材料・部材の仮定と質量の関係\n・同じ軌跡での質量とDC電力量の関係\n・追加部材による効果の相殺条件','・量子計算による実材料の性能改善\n・実用セル・完成パックの性能\n・実EVでの省電力効果']],rh=1.60)
tx(s,.65,5.66,11.98,.34,'配送計画の比較と保存軌跡の評価は、入力対応を確認した一体的な実験ではない。',12)
foot(s,'次に相談したい点','どの条件まで結果を解釈できるか、追加検証の優先順位、研究限界として残す範囲である。')

q8=[
'都市部のラストワンマイル配送に関する交通・ITS研究では、現在どのような課題が特に重視されているか。',
'EV配送研究では、経路最適化、交通流、充電、エネルギー消費、サービス水準の評価が、それぞれどのように発展しているか。',
'現在の配送最適化研究において、既存の古典的な最適化手法が十分に対応できていない課題には、どのようなものがあるか。',
'交通・ITSの観点から、量子計算が将来的に配送システムへ寄与するとすれば、どのような問題や条件が考えられるか。',
'量子計算の技術的な性能改善を、交通システム全体の有用性として評価するためには、どのような指標や比較条件が必要か。']
q9=[
'単一デポ、固定車両、顧客時間窓なしという現在のモデルは、交通・ITS研究の観点からどのように位置づけられるか。',
'背景交通を考慮しないSUMOシミュレーションでは、都市配送の旅行時間や電力量を比較する際に、どのような限界が生じるか。',
'信号待ち、交通混雑、荷重変化、道路勾配、回生ブレーキなどのうち、今回の研究目的に対して優先的に検証すべき要因は何か。',
'定時配達率と走行時DC電力量という二つの指標は、配送サービスと省電力性を評価するうえで妥当か。補足すべき指標はあるか。',
'現在の実験結果を踏まえ、修士研究として追加検証すべき内容と、研究限界として扱ってよい内容をどのように区別すべきか。']
for title,subtitle,questions,foottext in [
 ('交通・ITS研究の全体像と量子技術について伺いたいこと','研究動向と量子技術の将来的な可能性について、交通・ITSの観点からご意見を伺いたい。',q8,'現在重視される課題と、量子技術を評価する際の適切な問題設定を整理したい。'),
 ('現在の研究範囲と不足する検証について伺いたいこと','現在のモデルの位置づけと、修士研究として追加すべき検証の優先順位について伺いたい。',q9,'追加検証する内容と研究限界として残す内容を分け、今後の作業の優先順位を決めたい。')]:
 s=base(title,subtitle,'意見交換：重要な論点からご相談したい。',['A2','A3'],16,
 '掲載文は専門家への質問であり、現在の研究動向や古典手法の不足を事実として断定するものではない。5問を全て順番に消化するのではなく、先生の専門と重要度に応じて深掘りする。充電等を今の研究で検証済みとは扱わない。18分説明＋32分意見交換を想定する。')
 for i,question in enumerate(questions):
  y=1.79+.86*i;badge(s,str(i+1),.60,y+.04,N);tx(s,1.11,y,11.58,.76,question,14)
 foot(s,'議論の目的',foottext)

assert len(P.slides)==9

# Optional backups: original figures and conditions are retained as editable shapes.
previous=Presentation(OLD)
backup_specs=[(5,'補足1：旅行時間差の規模別・設定別内訳'),(7,'補足2：走行時DC電力量モデルの式と条件'),(8,'補足3：保存軌跡の距離・移動時間と電力量'),(9,'補足4：材料・部材条件からパック質量への計算')]
for k,(idx,title) in enumerate(backup_specs,1):
 origin=previous.slides[idx-1];s=P.slides.add_slide(P.slide_layouts[6])
 for sh in origin.shapes:
  if sh.top<Inches(.65) or sh.top>=Inches(7.0):continue
  s.shapes._spTree.insert_element_before(deepcopy(sh._element),'p:extLst')
 tx(s,.47,.14,12.4,.43,title,16,N,True)
 tx(s,.47,7.08,11.8,.25,'補足資料｜本編の説明には含めず、質疑に応じて参照する。',10,G)
 tx(s,12.04,7.08,.80,.25,f'補足{k} / 4',10,G,False,PP_ALIGN.RIGHT)
 ns=s.notes_slide
 if ns.notes_text_frame is None:
  z=Presentation();ns.shapes._spTree.append(deepcopy(z.slides.add_slide(z.slide_layouts[6]).notes_slide.notes_placeholder._element))
 ns.notes_text_frame.text='補足資料。本編18分の説明には含めない。旧12枚版の第'+str(idx)+'枚から、内容と数値を変更せず図形を引き継いだ。\n'+origin.notes_slide.notes_text_frame.text
 register.append(dict(slide=len(P.slides),title=title,minutes=0,refs=['旧12枚版'+str(idx)],notes='Optional backup; original source notes retained.'))

for ss in list(P.slides)[1:]:
 for sh in ss.shapes:
  for effect in sh._element.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}effectRef'):effect.set('idx','0')
P.core_properties.title='量子技術とEV配送｜佐藤先生との研究相談・本編9枚'
P.core_properties.author='佐野巧馬';P.core_properties.subject='説明18分・意見交換32分。本編9枚・補足4枚。'
P.save(DEST)
temp=DEST.with_suffix('.tmp.pptx')
with ZipFile(SRC) as orig,ZipFile(DEST) as authored,ZipFile(temp,'w',ZIP_DEFLATED) as final:
 for name in authored.namelist():
  keep=(name in ['ppt/slides/slide1.xml','ppt/slides/_rels/slide1.xml.rels'] or name.startswith(('ppt/theme/','ppt/slideMasters/','ppt/slideLayouts/','ppt/media/')))
  final.writestr(name,orig.read(name) if keep and name in orig.namelist() else authored.read(name))
temp.replace(DEST)
(O/'evidence/slide_register.json').write_text(json.dumps(register,ensure_ascii=False,indent=2))
(O/'evidence/source_ids.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2))
(O/'evidence/questions.json').write_text(json.dumps({'slide8':q8,'slide9':q9},ensure_ascii=False,indent=2))
print(DEST)
