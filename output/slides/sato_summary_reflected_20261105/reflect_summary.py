"""Reflect the user's updated research summary without changing the opening slide."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
import json,csv,math
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.xmlchemy import OxmlElement
O=Path(__file__).resolve().parent;R=O.parents[2]
PREV=R/'output/slides/sato_revision_20261105';LAST=R/'output/slides/sato_discussion_9slides_20261105'
OLD=next(LAST.glob('*.pptx'));P=Presentation(OLD)
STEM='研究紹介_佐野巧馬_佐藤先生相談用_研究まとめ反映版_本編9枚'
DEST=O/(STEM+'.pptx')
N,T,V,G,F,K,W='002060','087E88','6A5794','808080','F2F2F2','000000','FFFFFF';FONT='Noto Sans JP'
sources=json.loads((PREV/'evidence/source_ids.json').read_text())|{'U1':'研究のまとめ_20261105更新版.pptx','QG':'docs/QUANTITATIVE_GUIDE.md'}
geoms=[];register=[]
code=(PREV/'build_revision.py').read_text();code=code[code.index('def tx('):code.index('# 02:')];exec(compile(code,str(PREV/'build_revision.py'),'exec'))

def replace(page,old,new):
 found=0
 for sh in P.slides[page-1].shapes:
  if sh.has_text_frame and sh.text==old:
   # Rebuild runs while retaining the existing paragraph and font hierarchy.
   p=sh.text_frame.paragraphs[0];r=p.runs[0]
   props=dict(sz=r.font.size.pt,color=str(r.font.color.rgb),bold=r.font.bold,align=p.alignment)
   sh.text_frame.clear()
   for i,st in enumerate(new.split('\n')):
    para=sh.text_frame.paragraphs[0] if i==0 else sh.text_frame.add_paragraph();para.alignment=props['align'];para.line_spacing=Pt(20.5 if props['sz']==14 else props['sz']+3.2);para.space_after=Pt(0)
    rr=para.add_run();rr.text=st;rr.font.name=FONT;rr.font.size=Pt(props['sz']);rr.font.bold=props['bold'];rr.font.color.rgb=RGBColor.from_string(props['color'])
    for tag in ['a:ea','a:cs']:
     x=OxmlElement(tag);x.set('typeface',FONT);rr._r.get_or_add_rPr().append(x)
   found+=1
 assert found==1,(page,old,found)
def notes(page,body,refs):
 P.slides[page-1].notes_slide.notes_text_frame.text=body+'\n【出典】\n'+'\n'.join(k+': '+str(R/sources[k]) for k in refs)
def footer(page,refs):
 for sh in P.slides[page-1].shapes:
  if sh.has_text_frame and sh.text.startswith('出典：'):
   first=sh.text;replace(page,first,'出典：'+'・'.join(refs)+'　｜　条件・採用区分は発表者ノートと反映報告に記載')

# Target model and the full-area synthetic-demand basis.
replace(2,'研究で固定するもの','モデルの基盤')
replace(2,'・配送先と配送需要\n・車両への割当\n・配送の開始条件\n・電池以外の車両条件','・大田区内39,956地点\n・81,859個相当の合成需要\n・1拠点、1巡につき1台\n・配送先・車両割当を固定')
tx(P.slides[1],.48,4.98,2.65,.57,'京浜トラックターミナルを\n想定した代理拠点',10,G)
notes(2,'説明2分。更新版6枚目の拠点名・需要の基盤を反映した。拠点は研究上の代理拠点で、同施設の実配送実績を再現したものではない。39,956地点・81,859PEは合成需要の基盤であり全地点を量子計算したわけではない。模式図のA〜Eは説明用ラベル。',['U1','QG','A2'])
footer(2,['U1','QG','A2'])

# State the current research question and actual optimization output explicitly.
replace(3,'量子計算が配送計画や材料に関する能力を改善した場合、配送成果に反映されるための条件を検討する。','目的：量子技術がEV配送に寄与する条件を、配送計画と電池材料評価の二つの経路から検討する。')
replace(3,'技術的な改善が起こる条件と、その改善が配送成果に伝わる条件を分ける。','問い：技術的な出力は、どの条件で配送計画の改善またはDC電力量の変化につながるのか。')
replace(3,'配送計画の\n取得','訪問順序の\n探索')
replace(3,'訪問順序','古典近似との\n比較')
replace(3,'配達完了時刻','総旅行時間\n（現在の目的関数）')
replace(3,'定時配達率','配達完了・定時率\n（今後の接続先）')
replace(3,'保存計画の比較はCPU模擬である。顧客別の期限による定時配達率と実運用は未検証である。','最小化するのは拠点往復を含む総旅行時間である。待機・配達作業時間・電力量は目的関数に含めない。')
notes(3,'説明3分。更新版2・3・9枚目を反映した。量子・古典の比較対象は同じ配送先集合の訪問順序で、目的関数は有向ODの総旅行時間Jである。配達完了時刻・顧客契約期限による定時配達率は、その先で評価すべき未検証の接続として分ける。材料側の量子物性計算から実材料改善は未実証。第1枚目の①②③は評価工程として維持する。',['U1','B1','B3','M1'])
footer(3,['U1','B1','B3','M1'])

# Model conditions, with the adopted B population distinguished from legacy series.
replace(4,'・配送先・車両割当・開始条件を固定する。\n・顧客ごとの時間窓は設定しない。\n・配達作業102秒、共通期限32,400秒である。\n・配送途中の充電・車両間の再割当は扱わない。','・1巡1台、容量216個相当、全地点を訪問・帰還。\n・配送先・割当・開始条件を固定する。\n・顧客時間窓なし、作業102秒、帰庫上限32,400秒。\n・本比較は3・4・5・25・100・125地点の460入力。\n・配送途中の充電・車両間の再割当は扱わない。')
replace(4,'保存軌跡から電力量を計算する条件','走行・電力量を計算する条件')
replace(4,'・保存された速度時系列を固定する。\n・背景交通なし、平坦路、空荷である。\n・回生ブレーキ・補機電力を含まない。\n・時間窓や停車条件は保存時の設定に従う。','・SUMOの汎用配送車を単独走行させる。\n・MINICAB EVを参照：車両1,100kg、電池20kWh。\n・運転者55kgを加え、基準走行質量1,155kg。\n・保存速度を固定。平坦・空荷・回生・補機なし。\n・車種固有の寸法・加減速性能は未再現である。')
notes(4,'説明3分。更新版6〜8枚目を反映。MINICAB EVは質量・電池容量の参照であり、SUMOの汎用モデルを同車固有に校正した意味ではない。基準走行質量は1100+55=1155kg。荷物質量・荷下ろしによる変化は未反映。電池20kWhは参照の設計容量、凍結モデルのusable stock18kWhとは別概念。今回の主B比較R4は100顧客で、旧99顧客系列と異なる。3・4地点の旧直接比較、150・175・200等の旧規模列挙を36,800件の内訳にしない。保存軌跡の時間窓・停車条件は元の条件で、顧客時間窓なしのBと入力対応未確認。',['U1','B2','C2','A2','QG'])
footer(4,['U1','B2','C2','QG'])
replace(5,'460入力×8設定×10測定＝36,800保存計画。量子側はCPU模擬であり、反復出力は独立標本ではない。','460入力×8設定×10測定＝36,800計画。同等28,200件、長い候補8,600件である。\n量子側はCPU模擬であり、反復出力は独立標本ではない。')

# Retain the original mass-sensitivity illustration in the backup before rewriting page 6.
old_mass=P.slides[5]
backup_mass_xml=[deepcopy(sh._element) for sh in old_mass.shapes if sh.top>=Inches(.65) and sh.top<Inches(7.0)]
backup_mass_notes=old_mass.notes_slide.notes_text_frame.text
for sh in list(old_mass.shapes):old_mass.shapes._spTree.remove(sh._element)
s=old_mass
tx(s,.47,.14,12.4,.43,'材料・電池質量から走行時DC電力量への伝達',16,N,True)
tx(s,.47,.70,12.4,.48,'材料特性を仮定した参考例と、材料値に依存しない質量感度を分けて示す。',12)
tx(s,.47,1.24,12.4,.28,'材料性能が変わっても、部材の増加や走行条件によって電力量への効果が変わる。',12,N,True)
for x,w,label in [(.47,2.5,'材料特性の仮定'),(3.49,2.66,'電池部材・パック質量'),(6.67,2.5,'車両質量'),(9.69,3.18,'走行時DC電力量')]:
 node(s,x,1.98,w,.76,label,V)
 if x<9.5:line(s,x+w+.05,2.36,x+w+.45,2.36,T,1.15,False,True)
tx(s,9.69,1.63,3.18,.28,'同じ走行軌跡を入力',10,G,False,PP_ALIGN.CENTER)
line(s,11.28,1.90,11.28,1.97,T,.9,False,True)
tx(s,.65,3.05,12,.34,'材料条件を仮定した参考例：軽量化の相殺と電力量の変化',14,V,True)
rect(s,.47,3.62,12.4,1.03,F)
tx(s,.66,3.79,5.75,.34,'相殺境界：約5.448 kg',14,V,True)
tx(s,.66,4.22,5.75,.31,'追加部材の質量差がこの値に達すると、軽量化が消える。',12)
tx(s,6.99,3.79,5.65,.34,'条件付きDC削減率：約0.41%',14,V,True)
tx(s,6.99,4.22,5.65,.31,'同じ保存軌跡の電力量総和で比較した参考条件である。',12)
tx(s,.65,4.88,12,.38,'逆算した材料入力の実用適格性は未確認である。実用電池の確定的な性能予測ではない。',12)
tx(s,.65,5.44,12,.53,'材料に依存しない質量感度：1,000→1,100kgで平均＋236.9／＋243.3Wh（下限／上限抵抗）。\nこれは比較用の仮想質量であり、基準走行質量1,155kgや完成パックの予測値とは区別する。',12)
foot(s,'結果の範囲','量子による実材料改善・実車削減は未実証である。運行条件による変化と相殺条件を検討する。',V)
tx(s,.47,7.08,11.8,.25,'出典：U1・M1・M2・C3　｜　参考値の採用区分・条件は発表者ノートに記載',10,G)
tx(s,12.15,7.08,.70,.25,'06 / 9',10,G,False,PP_ALIGN.RIGHT)
notes(6,'説明3分。更新版5・8・9枚目を反映。T08参照条件のb=5.448297415076951kg、DC合計比削減率0.41257901006062697/0.4135904116974739%。0.41%は軌跡別削減率の単純平均ではない。逆算qペアの実用full-cell適格性がHOLDなので、採用済み主効果量でなく入力未適格の参考例としてのみ示す。T08参照パック96.145654799→90.697357384kg、走行質量1140.034543688→1134.586246273kgで、元1155kgに新パックを単純加算しない。100kg感度はこれとは別の材料非依存の凍結モデル比較。T09は部材依存性の補完、完成パックは保留。',['U1','M1','M2','C2','C3'])

replace(7,'・計画間の旅行時間差\n・指定候補集合内での改善余地\n・期限余裕と完了時刻の関係','・道路網・合成需要のモデル構築\n・計画間の総旅行時間差と改善余地\n・期限余裕と完了時刻の関係')
replace(7,'・実際の計画採用と出発までの接続\n・顧客別の契約期限による定時配達率\n・実際の交通・配送での効果','・実際の計画採用と配送での効果\n・全入力の最適証明・取得時間の統制\n・顧客別の定時配達率と実交通の妥当性')
replace(7,'・量子計算による実材料の性能改善\n・実用セル・完成パックの性能\n・実EVでの省電力効果','・量子計算による実材料の性能改善\n・完成パックの質量・寿命・出力の適格性\n・実車固有の消費と交通相互作用')
notes(7,'説明2分。更新版4枚目の検証済み／未検証を反映した。道路・需要の構築済みは実道路の妥当性検証済みとは異なる。全入力最適証明と計画取得時間の公平な統制は未完了。新しい実証成果を追加していない。',['U1','A1','A2','B3','M1'])
footer(7,['U1','A1','A2'])
for page in [8,9]:
 ns=P.slides[page-1].notes_slide.notes_text_frame
 ns.text=ns.text.replace('18分説明＋32分意見交換','19分説明＋31分意見交換')
 if page==8:ns.text=ns.text.replace('目安時間：16分','目安時間：15分')

# Backup 3 now presents the 100kg graph; the correlation scatter is less central to this summary.
s=P.slides[11]
for sh in list(s.shapes):s.shapes._spTree.remove(sh._element)
for element in backup_mass_xml:s.shapes._spTree.insert_element_before(element,'p:extLst')
tx(s,.47,.14,12.4,.43,'補足3：材料に依存しない100kgの質量感度',16,N,True)
tx(s,.47,7.08,11.8,.25,'補足資料｜仮想質量の感度を示す。実材料・実車の性能予測ではない。',10,G)
tx(s,12.04,7.08,.80,.25,'補足3 / 5',10,G,False,PP_ALIGN.RIGHT)
s.notes_slide.notes_text_frame.text='任意補足。以前の本編6枚目の100kg図を移した。\n'+backup_mass_notes

# An explicit reconciliation prevents legacy and current scales being conflated.
s=P.slides.add_slide(P.slide_layouts[6])
tx(s,.47,.14,12.4,.43,'補足5：基盤需要・解析対象・旧系列の違い',16,N,True)
tx(s,.47,.70,12.4,.48,'更新版にある需要基盤と、今回の主要結果を算出した対象を区別する。',12)
table(s,.47,1.64,[2.45,4.63,5.21],['区分','対象','読み取る際の注意'],[
 ['配送モデルの基盤','39,956地点・81,859個相当の合成需要。\n1拠点、1巡につき1台、容量216個相当。','実配送実績ではない。\n全地点を一括して量子計算したわけではない。'],
 ['今回の計画比較','3・4・5・25・100・125顧客の460入力。\n8設定×10測定＝36,800計画。','R4は100顧客。候補はCPU模擬である。\nこの集合から主greedy差を集計した。'],
 ['旧系列・拡張規模','更新版に記載の99・150・175・200等、\n3・4地点を中心とした旧小規模直接比較。','今回の36,800計画とは分ける。\nこれらの結果を今回の件数へ混ぜない。'],
 ['車両参照と感度計算','参照：車両1,100kg＋運転者55kg。\n感度例：走行質量1,000→1,100kg。','参照条件と仮想的な感度例は別である。\nSUMOモデルはMINICAB EV固有ではない。']],rh=1.03)
tx(s,.47,7.08,11.8,.25,'出典：U1・A2・QG・B2・C2　｜　系列差は反映報告にも記録',10,G)
tx(s,12.04,7.08,.80,.25,'補足5 / 5',10,G,False,PP_ALIGN.RIGHT)
ns=s.notes_slide
if ns.notes_text_frame is None:
 z=Presentation();ns.shapes._spTree.append(deepcopy(z.slides.add_slide(z.slide_layouts[6]).notes_slide.notes_placeholder._element))
ns.notes_text_frame.text='説明本編には含めない。更新版の規模行は旧系列と今回Bの対象を分けて解釈した。今回のB入力n_customersとStep5現行本文を優先し、100を99へ書き換えない。拠点名とMINICAB参照は更新版を出典とし、実拠点校正・実車再現は主張しない。'
for page in [10,11,13]:
 for sh in P.slides[page-1].shapes:
  if sh.has_text_frame and '/ 4' in sh.text:replace(page,sh.text,sh.text.replace('/ 4','/ 5'))
for ss in list(P.slides)[1:]:
 for sh in ss.shapes:
  for e in sh._element.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}effectRef'):e.set('idx','0')
P.core_properties.title='佐藤先生研究相談｜研究のまとめ20261105更新版反映'
P.core_properties.subject='本編9枚・補足5枚。説明19分・意見交換31分。'
P.save(DEST)
tmp=DEST.with_suffix('.tmp.pptx')
with ZipFile(OLD) as orig,ZipFile(DEST) as new,ZipFile(tmp,'w',ZIP_DEFLATED) as out:
 for name in new.namelist():out.writestr(name,orig.read(name) if name in ['ppt/slides/slide1.xml','ppt/slides/_rels/slide1.xml.rels'] else new.read(name))
tmp.replace(DEST)
(O/'evidence/questions.json').write_text((LAST/'evidence/questions.json').read_text())
(O/'evidence/source_ids.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2))
print(DEST)
