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
STEM='v6_KMD_Forum_量子技術と物流配送計画_A1縦'
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
    ['項目','1台の計画生成・評価条件 [1,2]'],
    ['対象地域・拠点','大田区・京浜トラックターミナルの\n位置を想定した単一拠点 [3]'],
    ['配送先数（計画全体）','3／4／5／25／100／125先'],
    ['量子側が扱う先数','全体と同じ3～125先の訪問順を対象\n設定により交換できる順序を制限'],
    ['車両・巡回数','1台・1巡回・拠点発着'],
    ['積載容量（モデル）','216荷物相当／台（重量kgではない）'],
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

section(562,'04  現状の実行と結果｜1台の保存計画を同じ入力で比較した結果')
table(18,580,[72,207,72,207],[
    ['実行・集計項目','確認できた内容','対象・評価項目','確認範囲・未評価事項'],
    ['実行方法','通常の計算機でQAOAを模擬\n量子実機は未実行','対象と設定','1台・1巡回・460入力\n8設定を同じ入力で比較'],
    ['調整結果の件数','3,680件（460入力×8設定）','各調整結果の抽出','8,192回の抽出から最良1件を保存、10反復'],
    ['保存出力数','36,800件（反復は調整結果を共用）','モデル内の確認','保存した最良候補の容量・帰庫条件を確認'],
    ['比較条件の差','計算に使える時間と、開始時の計画を残す規則が異なる','未計測・未評価','全工程の計画取得時間・実際の採用効果・\n実配送成果・顧客別期限内配達率']
],[11,18,11,11,18],pt=17.5,tag='execution')
txt(18,652,558,9,'結果：Jは往復の総旅行時間［秒］（作業・計算時間を除く）。ΔJ＝QAOA候補−古典対照。負が改善、正が悪化である。',18.5)
rows=[['手法・集計範囲','保存出力数［件］','古典対照の平均J［秒］','QAOA候補の平均J［秒］','平均 ΔJ［秒］','差の絶対値の平均［秒］']]
for label,key in [('位置交換型・6設定','位置交換など6設定'),('全訪問順型・p=2','GROVER_P2'),('全訪問順型・p=3','GROVER_P3')]:
    g=GROUPS[key]
    rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.3f}",f"{float(g['candidate_mean_s']):,.3f}",f"+{float(g['delta_mean_s']):,.3f}",f"{float(g['absolute_mean_s']):,.3f}"])
rows.append(['全8設定の混合',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.3f}",f"{DATA['candidate_mean_s']:,.3f}",f"+{DATA['delta_mean_s']:,.3f}",f"{DATA['absolute_mean_s']:,.3f}"])
table(18,664,[126,62,93,93,92,92],rows,[12,11,11,11,11],pt=18.5,tag='results',aligns=['left','right','right','right','right','right'])
txt(18,724,558,15.5,'差の中央値0秒、最大+9,483.990秒。同等28,200・悪化8,600・改善0件。\n保存出力は同じ訪問順の重複を含む。全体行は8設定の等重み平均。各値は丸め前に集計した。[1,2]',17.5)

section(741,'05  今後実施すること｜運用条件の調査と、比較条件をそろえた再検証')
items=[
    '調査：実営業所の配備車両数と同一便の稼働台数、配送先数、出発前の計画作成時間を公開資料で調べる。',
    '調査：車両容量・配達作業時間・拠点へ戻る期限・顧客別の配達期限について、現行設定の根拠を確認する。',
    '再検証：両側で最良計画を保存し、同じ入力・時間枠で古典手法とQAOAを再比較して、全工程時間を測る。',
    '再検証：探索範囲・初期状態・層数・係数調整を一つずつ変え、改善候補の有無と取得頻度を確認する。',
    '再検証：複数台の割当てと訪問順を古典手法で作り、局所改善後も全配送先への訪問と容量・帰庫条件を確認する。',
    '再検証：顧客別期限と採用規則を明示し、完了時刻・未配達を含む期限内配達率・道路距離への影響を調べる。'
]
for j,s in enumerate(items):
    sh=txt(18,759+j*8.8,558,8.8,s,18.5,I,tag='future:'+str(j+1))
    p=sh.text_frame.paragraphs[0];pr=p._p.get_or_add_pPr()
    pr.set('marL','180000');pr.set('indent','-180000')
    bf=OxmlElement('a:buFont');bf.set('typeface',FONT);pr.append(bf)
    bu=OxmlElement('a:buChar');bu.set('char','•');pr.append(bu)
    blocks[-1]['kind']='bullet';future_items.append(s)
line(18,816,576,816,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800.csv／B_INPUT_CONDITIONS_460.csv、条件整理・運用影響の報告書。',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv。',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内。[4] Farhi et al. (2014), arXiv:1411.4028.',
    '[5] Hadfield et al. (2019), Algorithms 12, 34. [6] Bärtschi & Eidenbenz (2020), QCE, 72–82.'
]
for j,s in enumerate(refs):txt(18,818+j*5.2,558,5.2,s,12,I,lh=1.0)


notes='v5の表を公開ガイドと実験の一次記録に照合し、数値を維持して表記を改善した。入力数、調整結果の件数、保存出力数を区別した。保存出力は同じ訪問順の重複を含み、測定反復は調整済み結果に条件付く。差の絶対値の平均は、同一入力に対応する候補と古典対照の差の絶対値を取ってから平均した値である。表示値は丸め前の値で集計してから既定の精度で表示しており、表示された平均J同士の引き算とは末尾が一致しない場合がある。公開ガイドは読み手に合わせた用語説明、列見出しと単位、数値の右揃えの参考とし、数値や丸め精度を変更する規則としては適用していない。全表のセルごとの数値列とポスター全体の数値トークンを入力v5と照合する。\n以下は元の内容説明である。指定v4からの修正。04はグラフを削除し、「現状の実行内容」と「得られた結果」の2表にした。現状の実行内容はCPU上でのQAOA模擬計算、1台・1巡回・460入力・8設定、3,680件の係数調整、8,192回抽出から最良1件を保存する処理の10反復、計36,800保存候補、容量と帰庫条件の検証を区別して示す。反復は同じ調整結果を共用し、独立した入力数や学習数ではない。\n結果表の20数値セルは前版の棒グラフと同じ値である。位置交換型6設定、全訪問順型p=2とp=3、全8設定の混合を区別した。目的値Jは拠点往復の総旅行時間［秒］、作業時間と計算時間は含まない。ΔJはQAOA候補−古典対照であり、負が改善、正が悪化である。全体行は8設定の混合平均である。\n計算予算・初期解保持規則は未統一であり、速度優位や実配送効果を結論しない。量子実機は未実行であり、全工程の計画取得時間、実際の採用効果、実配送成果、顧客別期限内配達率は未検証である。\n05は未定の規模表を復活させず、具体的な調査2項目と再検証4項目を維持した。台数・配送先数・部分問題サイズは未定である。顧客別期限を置く再検証は既存の時間枠なしB系列の結果とは別の計画である。\n01～03のモデル・評価の流れ・QAOA図を維持した。QAOA図はp組の費用位相操作と混合操作、古典計算による係数調整、調整終了後の候補抽出と制約確認を区別する。本実験は通常計算機での模擬計算である。フロー図のラベルは全て1行である。\n出典：review_outputs/quantum_ev_step5_20261105/data/B_PLAN_GAPS_36800.csv、B_INPUT_CONDITIONS_460.csv；review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv、B_RESOURCES_PER_FIT.csv。\nQAOA出典：Farhi et al. (2014), arXiv:1411.4028；Hadfield et al. (2019), Algorithms 12(2), 34；Bärtschi & Eidenbenz (2020), QCE, 72–82。\n白地・黒文字、A1縦594×841mm・1ページ。元のv4とそれ以前の資料は変更しない。\n'
S.notes_slide.notes_text_frame.text=notes
P.core_properties.title=TITLE
P.core_properties.subject='v6：全表の用語・単位・集計範囲を監査／v5の数値を保持'
P.core_properties.author='佐野巧馬 / 慶應義塾大学大学院メディアデザイン研究科 / 永山研究室 / Q/est'
P.save(O/f'{STEM}.pptx')
for name,data in [('LAYOUT',blocks),('TABLES',tablemeta),('DIAGRAM_NODES',diagram_nodes),('DIAGRAM_EDGES',diagrams),('FUTURE_ITEMS',future_items)]:
    (O/'evidence'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(O/'evidence/SLIDE_NOTES.txt').write_text(notes)
(O/'evidence/POSTER_TEXT.txt').write_text('\n\n'.join(z['text'] for z in blocks))
print(O/f'{STEM}.pptx')
