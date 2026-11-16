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
STEM='v11_KMD_Forum_量子技術と物流配送計画_A1縦_言語改訂'
TITLE='量子計算を用いた配送計画の比較評価'
N=B=A=I=M='#000000'
ACCENT='#DCEEF8'
TEXT_ACCENT='#225F83'
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
    txt(18,y,558,12.5,title,26,TEXT_ACCENT,True,tag=tag or title)
    rect(11,y+1,3,10,ACCENT)
    line(18,y+14,576,y+14,ACCENT,1.8)

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
            bg=ACCENT if ishead else (WHITE if j%2 else PALE)
            if bodycolors and j in bodycolors:bg=bodycolors[j]
            cell.fill.solid();cell.fill.fore_color.rgb=rgb(bg)
            fg=TEXT_ACCENT if ishead else I
            sz=pt if not ishead else pt-1
            al=aligns[k] if aligns else 'left'
            lines=wrap(s,w-5.4,sz,bold)
            need=len(lines)*sz*1.10*25.4/72+.6
            if need>h-2:raise ValueError(f'Table overflow {tag}[{j},{k}] {need:.2f}>{h-2}: {s}')
            set_text(cell.text_frame,'\n'.join(lines),sz,fg,bold,al,lh=1.10)
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
    sh.line.width=Pt(1.5)
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

# v11: all text is authored from the reviewed source sections, rather than global substitution.
def auto_table(x,y,widths,rows,pt=18,tag='table',aligns=None):
    heights=[]
    for ri,row in enumerate(rows):
        sz=pt-1 if ri==0 else pt
        maxneed=max(len(wrap(s,w-5.4,sz,ri==0 or (tag=='conditions' and ci==0)))*sz*1.10*25.4/72+.6 for ci,(s,w) in enumerate(zip(row,widths)))
        heights.append(math.ceil((maxneed+2.3)*2)/2)
    table(x,y,widths,rows,heights,pt=pt,tag=tag,aligns=aligns)
    return sum(heights)

rect(18,2,558,2,ACCENT)
txt(18,6,558,22,TITLE,42,TEXT_ACCENT,True,tag='title')
txt(18,30,558,14,'大田区の単一拠点・車両1台を想定したQAOAと古典手法の比較',25,I,tag='subtitle')
txt(18,46,558,11,'佐野巧馬｜慶應義塾大学大学院メディアデザイン研究科 修士2年｜永山研究室・Q/est',18.5,tag='author')
line(18,60,576,60,ACCENT,1.8)
txt(18,64,558,11,'今回検証した問い',22,TEXT_ACCENT,True,tag='question_heading')
txt(18,78,558,13,'QAOAで生成した候補と古典手法の基準計画では、総移動時間にどの程度の差があるか。',23,I,True,tag='question')
intro='量子近似最適化アルゴリズム（QAOA）の動作を通常のコンピュータでシミュレーションし、古典手法（量子アルゴリズムを用いない探索手法）の基準計画と比較した。\n今回の対象は、車両1台が配送先を訪れて拠点に戻る訪問順である。出発前の制限時間内での候補採用と、採用後の配送結果は今後評価する。'
txt(18,95,558,19,intro,18.5,tag='scope',lh=1.12)

section(119,'01  対象と計算条件｜車両1台が配送先を巡回する')
txt(18,139,208,11,'1つの拠点を出発し、配送先を訪れて戻る',21,I,True,tag='model_heading')
node1('depot',24,187,54,18,'拠点',22)
node1('customer_a',106,153,64,18,'配送先A',21)
node1('customer_b',171,187,61,18,'配送先B',21)
node1('customer_c',106,220,64,18,'配送先C',21)
edge('depot','customer_a',78,191,106,165,'model')
edge('customer_a','customer_b',170,165,198,187,'model')
edge('customer_b','customer_c',198,205,170,227,'model')
edge('customer_c','depot',106,227,78,201,'model')
txt(18,243,216,9,'A～Cは説明用の配送先であり、実際の位置ではない。',17.5,tag='model_schematic')
txt(18,254,216,26,'各配送先を1回ずつ訪問し、出発した拠点へ戻る。\n拠点を出発して戻るまでの総移動時間Jが短い訪問順を探索する。\nJには、配達作業時間と計画の計算時間を含めない。',18.5,tag='model_objective',lh=1.12)
conditions=[
 ['項目','今回の計算条件 [1,2]'],
 ['対象地域・拠点','大田区。京浜トラックターミナルの位置を想定した1拠点 [3]'],
 ['配送先数','3・4・5・25・100・125か所'],
 ['QAOAが扱う配送先','各計画に含まれる全配送先'],
 ['訪問順の探索範囲','並べ替えられる訪問順の範囲は、QAOAの設定によって異なる'],
 ['車両数・巡回回数','車両1台・1巡回。各配送先を1回ずつ訪れ、出発した拠点に戻る'],
 ['配達作業時間','配送先1か所につき102秒。拠点での作業時間は0秒'],
 ['拠点に戻る期限','モデル上の開始時刻から9時間（32,400秒）'],
 ['配送先ごとの指定時間帯','設定していない'],
 ['地点間の移動時間','地点の組と移動方向ごとに固定し、時間帯による変化は扱わない'],
 ['基準計画の作成方法','隣接交換を用いる反復貪欲法。隣り合う訪問順を交換し、\n改善が止まると順序を崩して探し直す']
]
condition_height=auto_table(242,139,[84,250],conditions,18,tag='conditions')

section(285,'02  評価の流れ｜計画の比較と、今後の配送結果の評価')
txt(18,303,558,9,'配送先・荷物量・地点間の移動時間を共通にし、基準計画とQAOA候補の総移動時間を比較した。候補の採用判断と、その後の配送結果の評価は今後実施する。',18.5,tag='pipeline_intro')
node1('input',18,331,150,16,'配送先・荷物量・地点間の移動時間',18.5)
node1('classical',185,315,143,16,'古典手法で作成した基準計画',19)
node1('quantum',185,347,143,16,'QAOAで生成した訪問順の候補',19)
node1('compare',344,331,98,16,'総移動時間を比較',19)
node1('decision',458,331,118,16,'今後：出発前に採用を判断',19,True)
line(168,339,176,339,I,1.5);line(176,323,176,355,I,1.5)
edge('input','classical',176,323,185,323,'pipeline')
edge('input','quantum',176,355,185,355,'pipeline')
line(328,323,336,323,I,1.5);line(336,323,336,355,I,1.5);line(328,355,336,355,I,1.5)
edge('classical','compare',336,339,344,339,'pipeline');diagrams['pipeline'].append(dict(source='quantum',target='compare'))
edge('compare','decision',442,339,458,339,'pipeline')
edge('decision','outcomes',517,347,517,359,'pipeline')
node1('outcomes',458,359,118,16,'今後：採用後の配送結果を評価',18.5,True)
txt(18,367,420,17,'今後検証する採用規則：出発までに得られた候補のうち、積載上限と拠点に戻る期限を満たし、基準計画より総移動時間が短い候補を採用する。\n該当する候補がなければ基準計画を用いる。',17.5,tag='adoption_rule',lh=1.12)
txt(18,386,558,9,'採用後は、拠点への帰着時刻、最後の配送先での配達完了時刻、走行距離を評価する。[1]',18,tag='future_outcomes')

section(402,'03  QAOAの計算手順｜量子操作とパラメータ調整を繰り返す')
txt(18,420,558,17,'QAOAは、総移動時間の情報を量子状態に反映する操作と、訪問順に対応する量子状態を混ぜる操作を組み合わせる方法である。\n操作の設定値（パラメータ）を古典計算で調整し、総移動時間の短い候補を探索する。[4–6]',18.5,tag='qaoa_intro',lh=1.12)
txt(112,439,241,8,'2種類の量子操作をp回繰り返す',16.5,I,True,align='center',tag='qaoa:layers')
line(121,449,353,449,I,.8);line(121,449,121,453,I,.8);line(353,449,353,453,I,.8)
qnodes=[('q_init',18,96,'初期の量子状態を準備'),('q_cost',121,105,'総移動時間を位相に反映'),('q_mix',233,120,'訪問順に対応する状態を混ぜる'),('q_eval',360,104,'候補の総移動時間を評価'),('q_update',471,105,'量子操作のパラメータを調整')]
for key,x,w,label in qnodes:node1(key,x,453,w,17,label,18.5)
for a,b in zip(qnodes,qnodes[1:]):edge(a[0],b[0],a[1]+a[2],461.5,b[1],461.5,'qaoa')
line(520,470,520,483,I,1.3);line(520,483,66,483,I,1.3);edge('q_update','q_init',66,483,66,470,'qaoa')
txt(190,472,210,8,'古典計算でパラメータ調整を繰り返す',16.5,I,align='center',tag='qaoa:feedback')
line(550,470,550,494,I,1.3);line(550,494,79,494,I,1.3);edge('q_update','q_fixed',79,494,79,498,'qaoa')
txt(428,484,130,8,'パラメータ調整を終了',16.5,I,align='center',tag='qaoa:finish')
fixednodes=[('q_fixed',18,122,'調整したパラメータを固定'),('q_restate',152,152,'固定したパラメータで量子状態を計算'),('q_sample',316,124,'訪問順の候補を繰り返し抽出'),('q_best',452,124,'最短候補を選び、条件確認して保存')]
for key,x,w,label in fixednodes:node1(key,x,498,w,16,label,18.5)
for a,b in zip(fixednodes,fixednodes[1:]):edge(a[0],b[0],a[1]+a[2],506,b[1],506,'qaoa')
txt(18,517,558,17,'pは2種類の量子操作を繰り返す回数である。本実験は通常のコンピュータでシミュレーションした。\nGroverミキサーを用いた設定では、すべての訪問順を探索対象に含めた。最短は抽出候補内の最短を指す。[1,2,6]',18,tag='qaoa_scope',lh=1.12)

section(541,'04  実験条件と比較結果｜基準計画とQAOA候補の総移動時間')
execution=[
 ['項目','実施した内容 [1,2]'],
 ['実行環境','通常のコンピュータでQAOAをシミュレーションした'],
 ['配送データ','車両1台・1巡回の配送データ460組'],
 ['QAOAの設定','各配送データに8設定を適用'],
 ['パラメータ調整の件数','460組 × 8設定 ＝ 3,680件'],
 ['調整後の候補抽出','パラメータを固定し、8,192回の候補抽出から\n最良候補1件を保存'],
 ['候補抽出の繰り返し','同じパラメータを用い、候補抽出と保存を10回実施'],
 ['保存した評価記録数','3,680件 × 10回 ＝ 36,800件。\n同じ訪問順の重複を含む'],
 ['制約条件の確認','保存した候補について、積載上限と\n拠点に戻る期限への適合を確認']
]
execution_height=auto_table(18,560,[82,190],execution,17.5,tag='execution')
txt(306,560,270,17,'ΔJ＝J（QAOA候補）−J（基準計画）。\n正は基準より長く、負は短い総移動時間を表す。',17.5,tag='result_metric',lh=1.12)
txt(306,580,270,9,'基準計画とQAOA候補の平均総移動時間',19.5,I,True,tag='result_table_title')
rows=[['QAOAの設定・集計範囲','評価記録数\n［件］','基準計画\n［秒］','QAOA候補\n［秒］','基準に対する\n平均差［秒］']]
for label,key in [('訪問順の一部を交換する\n6設定','位置交換など6設定'),('Groverミキサー：p=2','GROVER_P2'),('Groverミキサー：p=3','GROVER_P3')]:
    g=GROUPS[key];rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.1f}",f"{float(g['candidate_mean_s']):,.1f}",f"+{float(g['delta_mean_s']):,.1f}"])
rows.append(['全8設定の平均〔参考〕',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.1f}",f"{DATA['candidate_mean_s']:,.1f}",f"+{DATA['delta_mean_s']:,.1f}"])
result_height=auto_table(306,591,[87,41,46,48,48],rows,17.5,tag='results',aligns=['left','right','right','right','right'])
txt(306,591+result_height+3,270,38,'比較条件：古典手法は初期計画を最良候補に含むが、QAOAは抽出候補を保存した。古典手法の計算時間上限は旧実験に基づき、今回の8設定とはそろっていない。本表は、その条件で保存された計画の比較である。条件を統一した評価と採用後の配送結果の評価は今後実施する。',17.5,tag='comparison_limits',lh=1.10)
txt(18,560+execution_height+3,272,23,'訪問順の一部を交換する6設定では、平均総移動時間は\n基準計画の1,551.7秒に対して1,552.7秒であった。\nGroverミキサーの2設定では、それぞれ3,317.7秒、3,313.7秒であった。',17.5,tag='result_description',lh=1.10)
foot1=f"総移動時間の差の中央値は0秒、最大値は+{DATA['max_delta_s']:,.1f}秒であった。同等（保存値の差＝0）は28,200件、長い記録は8,600件、短い記録は0件。"
foot2='評価記録には同じ訪問順の重複を含む。全体は8設定を同じ重みで平均した。差は丸め前の値から算出し、表示を小数第1位にそろえた。[1,2]'
txt(18,696,558,17,foot1+'\n'+foot2,17.5,tag='result_notes',lh=1.10)

section(722,'05  今後の検証｜比較条件の統一と配送結果の評価')
future=[
 ['目的','実施する内容'],
 ['運用条件の根拠を確認する','車両数、配送先数、積載上限、配達作業時間、帰着期限、計画作成に使える時間を公開資料で確認する'],
 ['比較条件を統一する','配送データ、計算時間の上限、最良計画を保持する規則をそろえ、計画取得までの全工程の時間を測定する'],
 ['QAOAの設定による違いを調べる','探索対象の訪問順、初期状態、操作の繰り返し回数、パラメータ調整方法を個別に変え、総移動時間の差と短縮候補の取得頻度を比較する'],
 ['複数台の配送へ拡張する','各車両が担当する配送先と訪問順を古典手法で作成し、一部を変更した後も全配送先への訪問、積載上限、帰着期限を満たすか確認する'],
 ['候補採用後の配送結果を評価する','配送先ごとの期限と採用規則を設定し、最後の配送先での配達完了時刻、帰着時刻、走行距離を評価する']
]
future_height=auto_table(18,740,[146,412],future,17.5,tag='future')
line(18,816,576,816,RULE,.8)
refs=[
 '[1] Step5（2026-11-05）「B系列の解品質差の定量評価」「解品質差と配送運用成果」；B_PLAN_GAPS_36800.csv、B_INPUT_CONDITIONS_460.csv。',
 '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv（保存候補）／B_RESOURCES_PER_FIT.csv（調整計算の記録）。',
 '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内。[4] Farhi et al. (2014), arXiv:1411.4028.',
 '[5] Hadfield et al. (2019), Algorithms 12, 34. [6] Bärtschi & Eidenbenz (2020), QCE, 72–82.'
]
for j,s in enumerate(refs):txt(18,818+j*5.2,558,5.2,s,12,I,lh=1.0,tag='reference:'+str(j+1))
notes='''v11はv10を編集元とする。研究全体のRQは変更せず、今回掲載するB系列の総移動時間差を「今回検証した問い」として示した。採用判断・実配送成果・複数台への割当ては今後の計画である。
数値はv10のPOSTER_DATA.jsonとPOSTER_RESULT_TABLE.csvの元値を保持し、結果表と最大値の表示だけを小数第1位に丸めた。ΔJは候補のJからStep5のITERATED_GREEDY_ADJACENT_SWAP基準計画のJを引いた値であり、丸めた平均J同士から再計算していない。no_sumoのclassical_initial列に置き換えていない。
積載単位の換算基準を確定できなかったため、条件表の容量の数値行を省略した。期限内配達率はB系列で契約期限と定義を確定できず、指標名を省略した。モデル上の時間原点と共通上限、最後の配送先の作業完了時刻、同等の厳密な差0判定は保存実験資料で確認した。
候補の全配送先訪問を前提に、抽出から最短候補を選択し、保存候補の条件を確認して記録する工程を示した。選択工程内での順列の除外と保存候補の積載・帰着確認を混同していない。図の「最短」は抽出候補の範囲であり、問題全体の最適性の証明ではない。
参照：review_outputs/quantum_ev_step5_20261105/data/B_PLAN_GAPS_36800.csv・B_INPUT_CONDITIONS_460.csv、STEP5_OBJECTIVE_GAP_ANALYSIS.md・STEP5_OPERATIONAL_IMPACT.md、同scripts/analyze.py；review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv・B_RESOURCES_PER_FIT.csv・run_b.py；外部保全ディレクトリのstaged_qaoa_validation_20261102とcpu_matched_classical_swaps_r0_r5_20261101のPROTOCOL.json・SOURCE_SNAPSHOT。定義の根拠行はevidence/DEFINITION_DECISIONS.jsonに記録した。
新しい実験・QAOA・道路計算は実行していない。既存CSV・保存入力・測定記録の照合と文書の生成だけを行った。配色#DCEEF8と見出し文字#225F83、Noto Sans JP、著者所属はv10を維持した。A1縦594×841mm・1枚。'''
S.notes_slide.notes_text_frame.text=notes
P.core_properties.title=TITLE
P.core_properties.subject='v11：保存実験に対応する定義・文章・図ラベル・表構成の改訂'
P.core_properties.author='佐野巧馬 / 慶應義塾大学大学院メディアデザイン研究科 / 永山研究室 / Q/est'
P.save(O/f'{STEM}.pptx')
for name,data in [('LAYOUT',blocks),('TABLES',tablemeta),('DIAGRAM_NODES',diagram_nodes),('DIAGRAM_EDGES',diagrams),('FUTURE_ITEMS',future[1:])]:
 (O/'evidence'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(O/'evidence/SLIDE_NOTES.txt').write_text(notes)
(O/'evidence/POSTER_TEXT.txt').write_text('\n\n'.join(z['text'] for z in blocks))
print(json.dumps(dict(pptx=str(O/f'{STEM}.pptx'),table_heights=dict(conditions=condition_height,execution=execution_height,results=result_height,future=future_height)),ensure_ascii=False))
