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
STEM='v3_KMD_Forum_量子技術と物流配送計画_A1縦'
TITLE='量子技術が物流の配送計画に及ぼす影響'
N=B=A=I=M='#000000'
RULE,PALE,PLAN,WHITE='#B8B8B8','#F5F5F5','#FFFFFF','#FFFFFF'
FONT='Noto Sans JP'
FP=ROOT/'output/slides/sato_revision_20261105/fonts'
P=Presentation(); P.slide_width=Mm(594); P.slide_height=Mm(841)
P._element.sldSz.set('type','custom')
S=P.slides.add_slide(P.slide_layouts[6])
blocks=[]; tablemeta=[]; edges=[]; structural_edges=[]; diagram_nodes=[]; diagrams={}
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
    sh=line(x1,y1,x2,y2,c,1.8)
    end=OxmlElement('a:tailEnd');end.set('type','triangle');end.set('w','lg');end.set('len','lg')
    sh._element.spPr.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ln').append(end)

def section(y,title,c=N,tag=''):
    txt(18,y,558,12.5,title,26,I,True,tag=tag or title)
    line(18,y+14,576,y+14,I,.9)

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
            bg=WHITE if ishead else (WHITE if j%2 else PALE)
            if bodycolors and j in bodycolors:bg=bodycolors[j]
            cell.fill.solid();cell.fill.fore_color.rgb=rgb(bg)
            fg=I
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

from pptx.enum.dml import MSO_LINE_DASH_STYLE
S.background.fill.solid();S.background.fill.fore_color.rgb=rgb(WHITE)
future_items=[]

def node1(key,x,y,w,h,label,pt=21,planned=False):
    assert '\n' not in label and len(wrap(label,w-8,pt,True))==1,(key,label)
    sh=rect(x,y,w,h,WHITE,I);sh.name='node:'+key
    if planned:sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    th=pt*1.18*25.4/72+1
    tsh=txt(x+3,y+(h-th)/2,w-6,th,label,pt,I,True,'center','label:'+key)
    diagram_nodes.append(dict(key=key,text=label,text_shape_id=tsh.shape_id,shape_id=sh.shape_id,planned=planned))

def edge(source,target,x1,y1,x2,y2,kind):
    arrow(x1,y1,x2,y2,I)
    diagrams.setdefault(kind,[]).append(dict(source=source,target=target))

def bullet(y,s):
    sh=txt(18,y,558,7.7,s,17,I,tag='future:'+str(len(future_items)+1))
    p=sh.text_frame.paragraphs[0];pr=p._p.get_or_add_pPr()
    pr.set('marL','180000');pr.set('indent','-180000')
    bf=OxmlElement('a:buFont');bf.set('typeface',FONT);pr.append(bf)
    bu=OxmlElement('a:buChar');bu.set('char','•');pr.append(bu)
    blocks[-1]['kind']='bullet';future_items.append(s)

txt(18,8,558,22,TITLE,42,I,True)
txt(18,33,558,14,'大田区の単一拠点を想定した、量子計算による訪問順探索のケース分析',25,I)
txt(18,51,558,11,'佐野巧馬｜慶應義塾大学大学院メディアデザイン研究科 修士2年｜永山研究室・Q/est',18.5)
line(18,66,576,66,I,1)
txt(18,73,558,11,'研究の問い',22,I,True)
txt(18,87,558,13,'量子計算は、どのような過程を経て、配送計画と配送成果に影響するか。',23,I,True)
txt(18,104,558,10,'出発前に使える時間の中で、通常の計算機だけで解く古典手法を基準に、計画の質と配達完了時刻を比較する。',20)
txt(18,117,558,9,'ラストマイル配送は、拠点から届け先までの最終区間の配送である。本研究は車両への割当てと訪問順を対象とする。',18.5)

section(135,'01  配送モデルの構造と仮定｜検証済みは1台・1巡回である')
txt(18,156,277,11,'単一拠点から配送先を回って帰る',22,I,True)
node1('depot',30,205,58,20,'拠点',23)
node1('customer_a',139,170,68,20,'配送先A',22)
node1('customer_b',219,214,68,20,'配送先B',22)
node1('customer_c',139,258,68,20,'配送先C',22)
edge('depot','customer_a',88,211,139,185,'model')
edge('customer_a','customer_b',207,185,244,214,'model')
edge('customer_b','customer_c',244,234,207,263,'model')
edge('customer_c','depot',139,263,88,219,'model')
txt(18,283,277,9,'A～Cは配送先の模式例であり、実位置ではない。',17.5)
txt(18,294,277,10,'各配送先を1回訪問し、同じ拠点へ戻る。',20)
txt(18,307,277,10,'往復の総旅行時間 J が短い計画を探す。',20,I,True)
table(310,156,[82,184],[
    ['項目','1台の保存実験の設定 [1,2]'],
    ['対象地域・拠点','大田区・京浜トラックターミナルの\n位置を想定した単一拠点 [3]'],
    ['配送全体の先数','3／4／5／25／100／125先'],
    ['量子側が扱う先数','全体と同じ3～125先の訪問順全体\n小さな顧客群への分割ではない＊'],
    ['車両・巡回数','1台・1巡回・拠点発着'],
    ['車両容量','216荷物相当／台（重量kgではない）'],
    ['配達作業の時間','102秒／先（拠点は0秒）'],
    ['拠点へ戻る期限','モデル開始から9時間（32,400秒）'],
    ['顧客ごとの時間枠','設定なし（拠点へ戻る期限とは別）'],
    ['道路の移動時間','方向別の固定値。時間帯では変えない。'],
    ['古典対照の手法','訪問順の交換を繰り返し、\n行き詰まると順序を崩して再探索']
],[11,18,12,18,12,12,12,12,12,12,18],pt=17.5,tag='conditions')

section(330,'02  評価の流れ｜計画の比較と、採用後の配送成果を区別する')
txt(18,348,558,9,'古典基準と量子近似最適化アルゴリズム（QAOA）の候補を同じ入力で比較する。破線枠の採用・実行は今後の検証対象である。',18.5)
node1('input',18,372,86,17,'共通の入力',20)
node1('classical',132,359,121,17,'古典基準計画',21)
node1('quantum',132,389,121,17,'QAOA候補',21)
node1('compare',284,372,102,17,'同じ入力で比較',20)
node1('decision',414,372,162,17,'出発前に採用判断',21,True)
line(104,380.5,117,380.5,I,1.5);line(117,367.5,117,397.5,I,1.5)
edge('input','classical',117,367.5,132,367.5,'pipeline')
edge('input','quantum',117,397.5,132,397.5,'pipeline')
line(253,367.5,269,367.5,I,1.5);line(269,367.5,269,397.5,I,1.5);line(253,397.5,269,397.5,I,1.5)
edge('classical','compare',269,380.5,284,380.5,'pipeline')
diagrams['pipeline'].append(dict(source='quantum',target='compare'))
edge('compare','decision',386,380.5,414,380.5,'pipeline')
edge('decision','outcomes',495,389,495,401,'pipeline')
node1('outcomes',414,401,162,17,'配送成果を評価',21,True)
txt(18,409,382,9,'採用案：出発前に検証を終え、容量・帰庫条件を満たす、基準より短い候補を使う。',17.5)
txt(18,420,558,8.5,'候補が得られない、または旅行時間が基準以上の場合は古典基準を使う。成果は帰着・完了時刻・道路距離で評価する。',18)

section(435,'03  QAOAのアルゴリズム｜量子操作と古典計算による調整を組み合わせる')
txt(18,453,558,9,'量子近似最適化アルゴリズム（QAOA）は、旅行時間を反映する位相操作と混合操作を交互に行い、候補の確率分布を変える。[4–6]',18.5)
txt(133,465,210,8,'この2操作の組をp回繰り返す',16.5,I,True,align='center',tag='qaoa:layers')
line(128,475,350,475,I,.8);line(128,475,128,479,I,.8);line(350,475,350,479,I,.8)
qnodes=[('q_init',18,88,'初期状態を用意'),('q_cost',128,100,'費用位相操作'),('q_mix',250,100,'混合操作'),('q_eval',372,98,'評価値を計算'),('q_update',492,84,'調整係数を更新')]
for k,x,w,label in qnodes:node1(k,x,480,w,17,label,19.5)
for a,b in zip(qnodes,qnodes[1:]):edge(a[0],b[0],a[1]+a[2],488.5,b[1],488.5,'qaoa')
line(520,497,520,510,I,1.3);line(520,510,62,510,I,1.3);edge('q_update','q_init',62,510,62,497,'qaoa')
txt(210,500,160,8,'通常計算機で調整を継続',16.5,I,align='center',tag='qaoa:feedback')
line(550,497,550,520,I,1.3);line(550,520,79,520,I,1.3);edge('q_update','q_fixed',79,520,79,529,'qaoa')
txt(430,511,100,8,'調整完了',16.5,I,align='center',tag='qaoa:finish')
xs=[18,163.33,308.67,454]
for j,(x,label) in enumerate(zip(xs,['調整結果を固定','状態を再計算','候補を繰り返し抽出','制約確認と最良候補保存'])):
    node1(['q_fixed','q_restate','q_sample','q_best'][j],x,529,122,16,label,18.5)
    if j<3:edge(['q_fixed','q_restate','q_sample'][j],['q_restate','q_sample','q_best'][j],x+122,537,xs[j+1],537,'qaoa')
txt(18,548,558,9,'pは操作の組の回数（層数）である。本実験は通常計算機で模擬し、全訪問順型にはGrover型の混合操作を用いる。[1,2,6]',18)

section(562,'04  検証結果｜同じ配送入力に対する往復旅行時間の差を比べる')
txt(18,580,558,9,'Jは拠点往復の総旅行時間［秒］（作業・計算時間を除く）。ΔJ＝QAOA候補−古典対照。負が改善、正が悪化である。',18.5)
rows=[['設定','比較件数','古典 J 平均［秒］','QAOA J 平均［秒］','平均 ΔJ［秒］','平均絶対差［秒］']]
for label,key in [('位置交換型・6設定','位置交換など6設定'),('全訪問順型・p=2','GROVER_P2'),('全訪問順型・p=3','GROVER_P3')]:
    g=GROUPS[key]
    rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.3f}",f"{float(g['candidate_mean_s']):,.3f}",f"+{float(g['delta_mean_s']):,.3f}",f"{float(g['absolute_mean_s']):,.3f}"])
rows.append(['全8設定の混合',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.3f}",f"{DATA['candidate_mean_s']:,.3f}",f"+{DATA['delta_mean_s']:,.3f}",f"{DATA['absolute_mean_s']:,.3f}"])
table(18,592,[126,62,93,93,92,92],rows,[12,11,11,11,11],pt=18.5,tag='results',aligns=['left','right','right','right','right','right'])
txt(18,651,558,16,'比較入力は460件（3・4・5・25・100先は各78件、125先は70件）。8設定で計3,680件の係数調整を行った。\n同じ調整結果で8,192回の抽出から最良1件を保存する処理を10回反復した。保存候補は36,800件、全体行は8設定の混合平均である。[1,2]',17.5)
txt(18,670,558,8.5,'差の中央値0秒、最大+9,483.990秒。同等28,200・悪化8,600・改善0件。拠点へ戻る期限までの余裕は最小7,435.748秒である。',17.5)
txt(18,681,558,9,'＊交換範囲を制限する設定を含む。計算予算・初期解保持規則は未統一であり、速度優位・実配送の効果・顧客別期限内配達率は未検証である。',17.5)

section(695,'05  今後実施すること｜複数台への拡張と、出発までの同じ時間枠での検証')
table(18,714,[105,105,280,68],[
    ['全体規模（計画）','量子側の部分問題','主な確認事項','状況'],
    ['5台・500先','3～5先から（案）','車両割当て・訪問順・同じ時間枠での比較手順','未実施'],
    ['10台・1,000先','3～5先から（案）','割当てと訪問順の再現性・比較手順','未実施'],
    ['20台・2,000先','再現できた規模のみ','古典基準を評価し、量子比較の到達規模を記録する','未実施'],
    ['30台・3,000先','再現できた規模のみ','容量・帰庫期限への妥当性と比較可能な規模を確認する','未実施']
],[11,10,10,10,10],pt=16.5,tag='extension')
items=[
    'QAOAの探索範囲・初期状態・係数の調整方法を見直し、改善候補が得られる条件を調べる。',
    '前処理から採用判断までの時間枠と、最良計画を保持する規則を古典側とそろえる。',
    '5・10台で、配送先の車両への割当てと各車両の訪問順を確認し、改善方法を比較する。',
    '20・30台では古典基準を評価し、QAOAとの比較は再現できた部分問題の規模を報告する。',
    '30台・3,000先の妥当性を容量・帰庫条件で確認する。配備台数と同一便の稼働台数は区別する。[7]',
    '顧客ごとの配達期限を定め、未配達も含む期限内配達率と、各先の完了時刻を評価する。'
]
for j,s in enumerate(items):bullet(768+j*7.7,s)
line(18,816,576,816,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800.csv／B_INPUT_CONDITIONS_460.csv、条件整理・運用影響の報告書。',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv。',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内。[4] Farhi et al. (2014), arXiv:1411.4028.',
    '[5] Hadfield et al. (2019), Algorithms 12, 34. [6] Bärtschi & Eidenbenz (2020), QCE, 72–82. [7] ヤマト運輸（2023-10-02）八幡営業所公表資料。'
]
for j,s in enumerate(refs):txt(18,818+j*5.2,558,5.2,s,12,I,lh=1.0)

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

notes+='\n白地モデル図版v3：全背景と見出しは白基調、全テキストは黒とした。モデルの閉路構造、仮定表、古典・量子の比較パイプライン、複数台の分解パイプラインを優先した。全ての図ノードと分岐ラベルは1行であり、詳細条件を図外の表・説明へ移した。実線枠は保存比較、破線枠は採用・実行・複数台の検証計画である。モデル図のA〜Cは実位置ではなく模式例である。数値と計画値区分は前版と同じである。\n'

notes+='\n最新版指定ファイルはリポジトリ直下のv2_KMD_Forum_都市内ラストマイル配送計画_A1縦_白地モデル図版.pptxである。題名は同資料の主題を保ち表現を簡潔化した。佐野巧馬・KMD修士2年・永山研・Q/estは同ファイルから継承し、研究科名と研究室の表記を展開した。寸法は594×841mmに補正した。\nQAOA図は量子状態準備→費用位相操作→混合操作のp層→評価値計算→古典計算での係数調整と再計算→調整後の状態から候補抽出・制約を満たす最良候補の保存を示す。位相操作単独で良い解の確率が増えるとは主張しない。全処理はCPU模擬で、量子実機での回路実行や大規模な状態準備の実証ではない。評価値計算と係数探索は設定によって異なる。mirror5のMEAN/COHERENTは期待値、CVARは短い旅行時間側の裾の評価で学習用1024shots、Groverは保存費用プールとCOBYLA等、activeはt={0,.5,1}の3点探索である。図の継続ループは連続最適化だけを意味せず、離散候補の評価も含む。最良係数選択の後に最終候補の抽出を行う。\n[4] Farhi, Goldstone & Gutmann (2014), A Quantum Approximate Optimization Algorithm, arXiv:1411.4028, Sec. I Eq. (6), Sec. VIII. https://arxiv.org/abs/1411.4028\n[5] Hadfield et al. (2019), From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz, Algorithms 12(2), 34, Sec. 2. https://doi.org/10.3390/a12020034\n[6] Bärtschi & Eidenbenz (2020), Grover Mixers for QAOA, QCE, 72–82, Sec. II Fig. 1. https://arxiv.org/abs/2006.00354\n表現の監査は文化審議会（2022）公用文作成の考え方の専門用語・略語の扱いを参考に行い、用語を言い換えるか、初出で説明を添えた。https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/93657201.html\n末尾の6項目は今後の作業であり、実施済みではない。顧客別配達期限の設定・期限内配達率評価は新たな検証計画であり、時間枠なしのB系列の結果に混ぜない。\n'
S.notes_slide.notes_text_frame.text=notes
P.core_properties.title=TITLE
P.core_properties.subject='指定v2資料の改訂：QAOAアルゴリズム・今後の実施項目・Web言語監査'
P.core_properties.author='佐野巧馬 / 慶應義塾大学大学院メディアデザイン研究科 / 永山研究室 / Q/est'
P.save(O/f'{STEM}.pptx')
for name,data in [('LAYOUT',blocks),('TABLES',tablemeta),('DIAGRAM_NODES',diagram_nodes),('DIAGRAM_EDGES',diagrams),('FUTURE_ITEMS',future_items)]:
    (O/'evidence'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(O/'evidence/SLIDE_NOTES.txt').write_text(notes)
(O/'evidence/POSTER_TEXT.txt').write_text('\n\n'.join(z['text'] for z in blocks))
print(O/f'{STEM}.pptx')
