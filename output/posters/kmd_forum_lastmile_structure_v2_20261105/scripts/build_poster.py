"""Create one editable A1 portrait slide. PDF is exported from this PPTX."""
from pathlib import Path
import csv, json, math, re
from functools import lru_cache
from PIL import ImageFont
from pptx import Presentation
from pptx.util import Mm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.xmlchemy import OxmlElement

O=Path(__file__).resolve().parents[1]
ROOT=O.parents[2]
STEM='KMD_Forum_都市内ラストマイル配送計画_A1縦_構造図版'
TITLE='都市内ラストマイル配送計画における量子計算の寄与条件'
N,B,A,I,M,RULE,PALE,PLAN,WHITE='#16354B','#246C94','#A75A36','#20313F','#506575','#CBD7E0','#EFF4F7','#F7EFE9','#FFFFFF'
FONT='Noto Sans JP'
FP=ROOT/'output/slides/sato_revision_20261105/fonts'
P=Presentation(); P.slide_width=Mm(594); P.slide_height=Mm(841)
P._element.sldSz.set('type','custom')
S=P.slides.add_slide(P.slide_layouts[6])
blocks=[]; tablemeta=[]; edges=[]; structural_edges=[]
DATA=json.loads((O/'evidence/POSTER_DATA.json').read_text())
GROUPS={r['poster_group']:r for r in csv.DictReader((O/'evidence/POSTER_RESULT_TABLE.csv').open())}

def rgb(c): return RGBColor.from_string(c.lstrip('#'))

@lru_cache(None)
def font(pt,bold=False):
    return ImageFont.truetype(str(FP/('NotoSansJP-Bold.ttf' if bold else 'NotoSansJP-Regular.ttf')),round(pt*8))

def width(s,pt,bold=False): return font(pt,bold).getlength(s)/8*25.4/72

def wrap(s,w,pt,bold=False):
    lines=[]
    for para in s.split('\n'):
        line=''
        for ch in para:
            if line and width(line+ch,pt,bold)>w:
                tail=re.search(r'[A-Za-z0-9][A-Za-z0-9.,_/%+−–-]*$',line) if ch.isascii() and (ch.isalnum() or ch in '.,_%/') else None
                if ch in '、。，．）］」』％%':
                    lines.append(line[:-1]);line=line[-1]+ch
                elif tail and tail.start()>0:
                    lines.append(line[:tail.start()].rstrip());line=tail.group()+ch
                else:
                    lines.append(line.rstrip());line=ch.lstrip()
            else: line+=ch
        lines.append(line)
    return lines

def fillshape(sh,c,stroke=None):
    sh.fill.solid();sh.fill.fore_color.rgb=rgb(c)
    if stroke:sh.line.color.rgb=rgb(stroke);sh.line.width=Pt(.7)
    else:sh.line.fill.background()
    from pptx.oxml.ns import qn
    style=sh._element.find(qn('p:style'))
    if style is not None:sh._element.remove(style)
    sh._element.spPr.append(OxmlElement('a:effectLst'))

def rect(x,y,w,h,c,stroke=None):
    sh=S.shapes.add_shape(MSO_SHAPE.RECTANGLE,Mm(x),Mm(y),Mm(w),Mm(h))
    fillshape(sh,c,stroke);return sh

def set_text(tf,text,pt,c,bold=False,align='left',lh=1.18):
    tf.clear();tf.word_wrap=False;tf.auto_size=MSO_AUTO_SIZE.NONE
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    tf.vertical_anchor=MSO_ANCHOR.TOP
    for j,ln in enumerate(text.split('\n')):
        p=tf.paragraphs[0] if j==0 else tf.add_paragraph()
        p.space_before=p.space_after=Pt(0);p.line_spacing=Pt(pt*lh)
        p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[align]
        r=p.add_run();r.text=ln;r.font.name=FONT;r.font.size=Pt(pt);r.font.bold=bold;r.font.color.rgb=rgb(c)
        for tag in ['a:ea','a:cs']:
            a=OxmlElement(tag);a.set('typeface',FONT);r._r.get_or_add_rPr().append(a)
        r._r.get_or_add_rPr().set('lang','ja-JP')

def txt(x,y,w,h,s,pt=22,c=I,b=False,align='left',tag='',lh=1.18):
    lines=wrap(s,w-.8,pt,b)
    need=len(lines)*pt*lh*25.4/72+.6
    if need>h:raise ValueError(f'Overflow {tag or s[:30]}: {need:.2f}>{h}')
    assert x>=0 and y>=0 and x+w<=594.01 and y+h<=841.01
    sh=S.shapes.add_textbox(Mm(x),Mm(y),Mm(w),Mm(h));sh.name=tag or s[:45]
    set_text(sh.text_frame,'\n'.join(lines),pt,c,b,align,lh)
    blocks.append(dict(id=sh.shape_id,tag=sh.name,x=x,y=y,w=w,h=h,pt=pt,text=s,rendered='\n'.join(lines),kind='text'))
    return sh

def line(x1,y1,x2,y2,c=RULE,pt=1):
    sh=S.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Mm(x1),Mm(y1),Mm(x2),Mm(y2))
    sh.line.color.rgb=rgb(c);sh.line.width=Pt(pt)
    from pptx.oxml.ns import qn
    style=sh._element.find(qn('p:style'))
    if style is not None:sh._element.remove(style)
    sh._element.spPr.append(OxmlElement('a:effectLst'))
    return sh

def arrow(x1,y1,x2,y2,c=B):
    sh=line(x1,y1,x2,y2,c,1.6)
    end=OxmlElement('a:tailEnd');end.set('type','triangle');end.set('w','sm');end.set('len','sm')
    sh._element.spPr.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ln').append(end)

def section(y,title,c=N,tag=''):
    rect(18,y,558,14,c)
    txt(22,y+.7,550,12.5,title,26,WHITE,True,tag=tag or title)

def table(x,y,widths,rows,heights,pt=20,header=True,color=B,aligns=None,tag='table',bodycolors=None):
    sh=S.shapes.add_table(len(rows),len(widths),Mm(x),Mm(y),Mm(sum(widths)),Mm(sum(heights)))
    sh.name=tag;t=sh.table
    for j,w in enumerate(widths):t.columns[j].width=Mm(w)
    cy=y
    for j,(row,h) in enumerate(zip(rows,heights)):
        t.rows[j].height=Mm(h);cx=x
        for k,(s,w) in enumerate(zip(row,widths)):
            cell=t.cell(j,k)
            cell.margin_left=cell.margin_right=Mm(2.4)
            cell.margin_top=cell.margin_bottom=Mm(1.0)
            ishead=header and j==0
            bold=ishead or (tag=='conditions' and k==0)
            bg=color if ishead else (WHITE if j%2 else PALE)
            if bodycolors and j in bodycolors:bg=bodycolors[j]
            cell.fill.solid();cell.fill.fore_color.rgb=rgb(bg)
            fg=WHITE if ishead else I
            sz=pt if not ishead else pt-1
            al=aligns[k] if aligns else 'left'
            lines=wrap(s,w-5.4,sz,bold)
            need=len(lines)*sz*1.18*25.4/72+.6
            if need>h-2:raise ValueError(f'Table overflow {tag}[{j},{k}] {need:.2f}>{h-2}: {s}')
            set_text(cell.text_frame,'\n'.join(lines),sz,fg,bold,al)
            cell.margin_left=cell.margin_right=Mm(2.4)
            cell.margin_top=Mm(max(1,(h-need)/2))
            cell.margin_bottom=Mm(1)
            tcpr=cell._tc.get_or_add_tcPr()
            for side in ['L','R','T','B']:
                ln=OxmlElement('a:ln'+side);ln.set('w','6350')
                sf=OxmlElement('a:solidFill');cl=OxmlElement('a:srgbClr');cl.set('val',RULE[1:]);sf.append(cl);ln.append(sf);tcpr.append(ln)
            blocks.append(dict(id=sh.shape_id,tag=f'{tag}:{j}:{k}',x=cx+2.4,y=cy+max(1,(h-need)/2),w=w-4.8,h=need,pt=sz,text=s,rendered='\n'.join(lines),kind='cell'))
            cx+=w
        cy+=h
    tablemeta.append(dict(tag=tag,rows=rows,widths=widths,heights=heights,x=x,y=y))
    return t

# Main poster layout; combined with the existing editable native primitives.
rect(0,0,594,80,N);rect(0,78,594,2,B)
txt(18,7,558,10,'KMD FORUM  |  研究ポスター',17,'#D1E1EA',True)
txt(18,21,558,24,TITLE,46,WHITE,True)
txt(18,47,558,15,'大田区の単一拠点を想定したケース分析',29,WHITE)
txt(18,65,558,12,'佐野巧馬  ｜  Q/est',22,'#D1E1EA')

section(90,'01  出発前に、使える配送計画を得る')
txt(18,109,558,20,'限られた出発前の時間で、容量と帰庫期限を満たす配送計画を用意する必要がある。\n対象は配送先の車両割当てと訪問順である。量子計算の寄与を、探索・取得・採用・実行の接続から検討する。',21.5)
rect(18,132,558,39,PALE);rect(18,132,2,39,B)
txt(23,135,548,9,'研究の問い',17,B,True)
txt(23,146,548,23,'出発までに使える時間の中で、量子計算から得た候補を取り入れると、\n既存の古典手法と比べて配送計画の質や配送成果はどの程度変わるか。',24,N,True)

section(183,'02  寄与の構造：候補の質・取得時間・採用判断を経て、配送成果につながる')
flow=[(18,100,'共通需要・道路旅行時間','入力：拠点・先・需要'),
      (128,100,'古典基準計画を作成','出力：割当て・訪問順'),
      (238,130,'同一入力の古典・量子比較','目的・制約／次は時間も統一'),
      (378,100,'出発前に採用判断','質・取得時間・制約'),
      (488,88,'配送成果を評価','完了時刻・道路距離')]
for j,(x,w,title,desc) in enumerate(flow):
    rect(x,203,w,24,PALE,RULE)
    txt(x+2,205,w-4,9,title,17.5,N,True)
    txt(x+2,216,w-4,8,desc,15.5,M)
    if j<4:
        arrow(x+w+1,215,flow[j+1][0]-1,215)
        edges.append(dict(source=j+1,target=j+2))

def node(x,y,w,h,title,body,color,body_y=None):
    rect(x,y,w,h,WHITE,color);rect(x,y,1.5,h,color)
    txt(x+4,y+3,w-8,12,title,21,color,True)
    if body:
        bh=len(wrap(body,w-8-.8,18.5))*18.5*1.18*25.4/72+1
        txt(x+4,body_y or y+18,w-8,bh,body,18.5)

node(18,244,139,96,'量子探索の設計','探索する訪問順の範囲\n初期解・調整方法・抽出回数',B)
line(22,293,153,293,RULE,.7)
txt(22,300,131,34,'改善解の存在と得やすさ、\n計算に要する時間の\n両方に関係する。',18.5,B)
node(183,244,110,41,'得られた候補の質','総旅行時間 J\n容量・帰庫条件の充足',B,body_y=261)
node(183,300,110,41,'使えるまでの時間','前処理・探索・検証の合計\n全工程の比較は未検証',A,body_y=317)
arrow(157,264,183,264,B)
arrow(157,320,183,320,A)
structural_edges.extend([dict(source='quantum_design',target='candidate_quality',status='saved_plan_comparison'),dict(source='quantum_design',target='acquisition_time',status='conditional_not_total_runtime_validation')])

rect(322,244,111,79,PLAN,A)
txt(326,247,103,10,'計画担当者・配車システム',17.5,A,True)
txt(326,259,103,12,'出発前の採用判断',22,A,True)
txt(326,275,103,27,'①古典基準より短い\n②締切内に検証が完了\n③容量・帰庫期限を満たす',18.5)
txt(326,308,103,10,'3条件を全て満たす（案）',17,A,True)
arrow(293,264,322,264,B)
line(293,320,307,320,A,1.5);line(307,320,307,296,A,1.5);arrow(307,296,322,296,A)
structural_edges.extend([dict(source='candidate_quality',target='adoption_gate',condition='strict_improvement_and_feasibility'),dict(source='acquisition_time',target='adoption_gate',condition='completed_before_common_departure_deadline')])

node(469,244,107,79,'配送の実行と成果','帰庫・各先の完了時刻\n走行距離\n実交通下の効果は未検証',A,body_y=268)
txt(437,250,28,9,'成立',16,A,True,align='center')
arrow(433,266,469,266,A)
txt(322,325,111,10,'一つでも不成立',16.5,A,align='center')
arrow(377.5,335,377.5,340,A)
rect(322,341,111,19,PALE,B)
txt(326,344,103,12,'古典基準計画を使う',19,B,True)
line(433,350,451,350,B,1.5);line(451,350,451,304,B,1.5);arrow(451,304,469,304,B)
structural_edges.extend([dict(source='adoption_gate',target='delivery_outcomes',condition='all_gates_pass'),dict(source='adoption_gate',target='classical_fallback',condition='any_gate_fails'),dict(source='classical_fallback',target='delivery_outcomes',condition='use_retained_baseline')])
rect(469,333,107,30,PLAN,RULE)
txt(473,335,99,8,'成果を左右する条件',16.5,A,True)
txt(473,345,99,16,'期限までの余裕・交通・\n配送先での作業時間',17.5)
arrow(522.5,333,522.5,323,A)
structural_edges.append(dict(source='deadline_slack_traffic_service',target='delivery_outcomes',status='conditions_not_empirical_effect_identification'))

for x,w,title,body in [
    (18,176,'A  探索範囲が寄与を制限する','指定した位置交換5設定の範囲には、\n古典対照より良い解が存在しない。\n他の範囲へは一般化しない。[1]'),
    (204,176,'B  取得と採用を分ける','旅行時間の短い候補でも、出発前に\n検証が完了しなければ採用できない。\nこれは次の実験の採用規則の案である。'),
    (390,186,'C  時間差と期限遵守を分ける','両側が帰庫期限を満たす場合は、\n旅行時間が異なっても\n帰庫期限の遵守は変わらない。[1]')]:
    rect(x,374,w,44,PALE,RULE)
    txt(x+3,377,w-6,10,title,19,B,True)
    txt(x+3,390,w-6,25,body,18)
txt(18,423,558,16,'青は保存計画での検証範囲、茶は採用・実行に向けた条件と次の検証を表す。矢印は検討する接続であり、実運用の因果効果を実証したものではない。量子近似最適化（QAOA）を通常計算機上で模擬した結果を用いる。',17.5,M)

section(444,'03  検証済み｜1台の条件と主結果  —  改善候補の取得と、成果への伝達を分ける',B)
table(18,466,[80,199,80,199],[
    ['条件','時間枠なしB系列の設定 [1,2]','条件','時間枠なしB系列の設定 [1,2]'],
    ['対象地域・拠点','大田区・京浜トラックターミナルの\n位置を想定した単一拠点 [3]','車両容量','216荷物相当／台（重量kgではない）'],
    ['配送全体の先数','3／4／5／25／100／125先','QAOAに渡した\n配送先数','全体と同じ3～125先の訪問順全体\n小ブロックへの切出しではない＊'],
    ['車両・巡回','1台・1巡回・拠点発着','作業時間','102秒／先（拠点は0秒）'],
    ['帰庫期限','モデル開始から9時間（32,400秒）','顧客別時間枠','なし（共通の帰庫上限とは別である）'],
    ['古典対照','訪問順の交換を繰り返し、\n行き詰まると順序を崩して再探索','道路旅行時間','時間帯によらない固定値である']
],[11,18,18,11,11,18],pt=18,tag='conditions')
txt(18,556,558,9,'主結果：Jは拠点往復の総旅行時間［秒］（作業・計算時間を除く）。ΔJ＝量子候補−古典対照。負が改善、正が悪化である。',19.5,N,True)
rows=[['設定','比較件数','古典 J 平均［秒］','候補 J 平均［秒］','平均 ΔJ［秒］','平均絶対差［秒］']]
for label,key in [('位置交換など6設定','位置交換など6設定'),('全訪問順型・2層','GROVER_P2'),('全訪問順型・3層','GROVER_P3')]:
    g=GROUPS[key]
    rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.3f}",f"{float(g['candidate_mean_s']):,.3f}",f"+{float(g['delta_mean_s']):,.3f}",f"{float(g['absolute_mean_s']):,.3f}"])
rows.append(['全8設定の混合',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.3f}",f"{DATA['candidate_mean_s']:,.3f}",f"+{DATA['delta_mean_s']:,.3f}",f"{DATA['absolute_mean_s']:,.3f}"])
table(18,569,[126,62,93,93,92,92],rows,[13,12,12,12,12],pt=19.5,tag='results',aligns=['left','right','right','right','right','right'],bodycolors={4:'#E1EDF4'})
txt(18,633,558,9,'全候補の差の中央値0秒、最大+9,483.990秒。同等28,200件・悪化8,600件・改善0件。帰庫余裕は最小7,435.748秒である。[1]',18.5)
txt(18,644,558,16,'460入力（3・4・5・25・100先が各78、125先が70）×8設定＝3,680件の調整。全体行は8設定の混合平均である。\n各調整済み状態から8,192回抽出×10反復し、反復ごとの最良候補36,800件を保存した。10反復は状態を共用する。[1,2]',18)
txt(18,663,558,16,'＊交換範囲を制限する設定を含む。計算予算・初期解保持規則が異なり、全工程の時間優位は未判定である。顧客別期限内配達率は未評価、道路距離は主比較で未集計である。実営業所の車両配置・運用の再現は未確認である。',17.5,M)

section(684,'04  計画｜全体の割当てと、局所の改善を分けて比較する',A)
px=[18,162.33,306.67,451]
for j,(x,title) in enumerate(zip(px,['全体の割当て・基準訪問順\n古典手法で作る','同じ局所を改善\n古典候補／量子候補を比較','全体計画に戻して検証\n容量・帰庫・全先訪問','共通締切で採用判断\n両側で最良計画を保持'])):
    rect(x,701,125,16,PLAN,RULE)
    txt(x+2,702,121,14,title,16,A,True,align='center')
    if j<3:arrow(x+126,709,px[j+1]-1,709,A)
table(18,721,[105,104,271,78],[
    ['全体の車両数・先数','量子側の部分問題','検証すること','実施状況'],
    ['5台・500先','3～5先から（案）','車両割当て・各車両の訪問順・同一時間予算の比較手順','計画・未実施'],
    ['10台・1,000先','3～5先から（案）','割当てと訪問順の再現性、同一時間予算の比較手順','計画・未実施'],
    ['20台・2,000先','再現できた規模のみ','古典基準の品質・取得時間を評価し、量子比較の到達規模を記録','計画・未実施'],
    ['30台・3,000先','再現できた規模のみ','容量・帰庫期限への妥当性と古典基準を評価し、量子比較範囲を報告','計画・未実施']
],[13,13,13,13,13],pt=18,tag='extension',color=A,bodycolors={1:'#FBF7F3',2:PLAN,3:'#FBF7F3',4:PLAN})
txt(18,789,558,14,'最大30台・3,000先は妥当性を確認する計画値である。配備32台の国内例 [4] は規模の参考であり、同一便の稼働台数の根拠ではない。日間個数は配送先数に換算しない。',17,M)
txt(18,804,558,8,'各台100先なら作業2時間50分、移動余裕6時間10分（待機なしの概算）。各台216荷物相当と9時間帰庫を個別に検算する。全工程を同じ時間枠で比較する。[1]',16,M)
line(18,814,576,814,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800／B_INPUT_CONDITIONS_460、PATHWAY1_CONDITIONS・OPERATIONAL_IMPACT',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv（再集計・照合）',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内：j-m-t.co.jp/terminal/keihin.html',
    '[4] ヤマト運輸（2023-10-02）八幡営業所公表資料：yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html'
]
for j,s in enumerate(refs):
    sh=txt(18,816+j*5.7,558,5.7,s,13,M,lh=1.05)
    if j>=2:
        url=['https://www.j-m-t.co.jp/terminal/keihin.html','https://www.yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html'][j-2]
        for p in sh.text_frame.paragraphs:
            for r in p.runs:r.hyperlink.address=url


notes='''作成対象：A1縦594×841mm・1枚。ユーザーの補足により既存資料はrun10/poster.pptxを採用した。
研究相談の文字起こし現物は取得できていない。相談内容の推定引用は行わず、ユーザー指定の研究の問いと構成、および確認した保存資料に従う。
出典[1] review_outputs/quantum_ev_step5_20261105/data/B_PLAN_GAPS_36800.csv、B_INPUT_CONDITIONS_460.csv、同STEP5_OBJECTIVE_GAP_ANALYSIS.md、STEP5_PATHWAY1_CONDITIONS.md、STEP5_OPERATIONAL_IMPACT.md。
出典[2] review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv、B_RESOURCES_PER_FIT.csv。
位置交換など6設定：MEAN_P2、CVAR10_P2、CVAR01_P2、COHERENT2_P2、COHERENT4_P2、ACTIVE_ADJACENT_P3_GRID。各460入力×10反復＝4,600比較、合わせて27,600比較。全順列型はGROVER_P2/P3である。
古典対照はITERATED_GREEDY_ADJACENT_SWAPであり、初期解や脱位相random対照とは異なる。古典側は初期解を保持し、旧swap-QAOAの入力別CPU秒をsoft capとする。現行8設定との同一予算の試験ではない。
候補は8,192回の抽出から最良を選ぶ保存出力で、10反復は同じ調整済み状態に条件付く。36,800は独立標本数でも学習数でもない。460入力も親・需要群の依存がある。記述統計に限定する。
Jは拠点往復を含む有向道路旅行時間の和であり、作業時間は含めない。容量216荷物相当、帰庫J+102n≤32,400秒、各先1回訪問を確認した。顧客固有の時間枠はない。帰庫期限と顧客の配達期限を区別する。
今後の採用規則は制約充足・共通締切内の取得・Jの厳密改善。未取得・同値・悪化時は古典基準を使う。保存結果にこの規則を仮適用したJ差は0だが、実採用の観測ではない。
5/10/20/30台、500/1000/2000/3000先、局所3～5先開始、同一時間予算の比較は計画であり未実施。時間予算の具体値は未確定である。20/30台では古典基準を評価し量子比較は実際に再現できた規模を報告する。30台3000先の全体を量子計算で解いたことを意味しない。
公開資料[3] https://www.j-m-t.co.jp/terminal/keihin.html（大田区平和島2-1-1の拠点位置の根拠のみ）。
公開資料[4] https://www.yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html（2023年公表の八幡営業所の配備集配車両32台。同一便の稼働台数は記載なし）。公開事例は車両数の規模感のみ参照し、車種や運用の再現根拠に使わない。両公開ページ参照日：2026-11-05。
次の実験で各台の需要量、帰庫、全先被覆を検算する。100先×102秒＝10,200秒、32,400−10,200＝22,200秒は待機なしの単純な時間枠の確認であり実行可能性を保証しない。需要量は配送先数やkgへ置換しない。
'''
notes+='\n構造図版の追記：探索設計→候補の質／全工程取得時間→採用ゲート→配送成果を分岐と条件入力で図示した。採用規則・現場の採用行動・実交通下の効果は未検証である。位置交換5設定の探索範囲に改善解が存在しないという結果はmirror5に限定し、ACTIVE_ADJACENT_P3_GRIDや全順列支持の不存在証明に一般化しない。帰庫期限遵守についての条件説明は保存ODモデルに限り、顧客別期限内配達率の実証としない。既存v1の数値結果・計画値区分は維持した。\n'
S.notes_slide.notes_text_frame.text=notes
P.core_properties.title=TITLE
P.core_properties.subject='KMD Forum：検証済み1台B系列と複数台の拡張計画'
P.core_properties.author='佐野巧馬 / Q/est'
P.save(O/f'{STEM}.pptx')
(O/'evidence/LAYOUT.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2))
(O/'evidence/TABLES.json').write_text(json.dumps(tablemeta,ensure_ascii=False,indent=2))
(O/'evidence/FLOW_EDGES.json').write_text(json.dumps(edges,indent=2))
(O/'evidence/SLIDE_NOTES.txt').write_text(notes)
(O/'evidence/POSTER_TEXT.txt').write_text('\n\n'.join(z['text'] for z in blocks))
(O/'evidence/STRUCTURAL_EDGES.json').write_text(json.dumps(structural_edges,ensure_ascii=False,indent=2))
print(O/f'{STEM}.pptx')
