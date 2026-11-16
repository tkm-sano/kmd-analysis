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
STEM='KMD_Forum_都市内ラストマイル配送計画_A1縦_白地モデル図版'
TITLE='都市内ラストマイル配送計画における量子計算の寄与条件'
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

# White background, black text; every diagram node has one single-line label.
from pptx.enum.dml import MSO_LINE_DASH_STYLE
S.background.fill.solid();S.background.fill.fore_color.rgb=rgb(WHITE)

def node1(key,x,y,w,h,label,pt=22,planned=False):
    assert '\n' not in label and len(wrap(label,w-8,pt,True))==1,(key,label)
    sh=rect(x,y,w,h,WHITE,I)
    sh.name='node:'+key
    if planned:sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    th=pt*1.18*25.4/72+1
    textshape=txt(x+3,y+(h-th)/2,w-6,th,label,pt,I,True,'center','label:'+key)
    diagram_nodes.append(dict(key=key,text=label,text_shape_id=textshape.shape_id,shape_id=sh.shape_id,planned=planned))

def edge(source,target,x1,y1,x2,y2,kind):
    arrow(x1,y1,x2,y2,I)
    diagrams.setdefault(kind,[]).append(dict(source=source,target=target))

txt(18,7,558,10,'KMD FORUM  |  研究ポスター',17,I,True)
txt(18,22,558,24,TITLE,46,I,True)
txt(18,49,558,15,'大田区の単一拠点を想定したケース分析',29,I)
txt(18,67,558,11,'佐野巧馬  ｜  Q/est',22,I)
line(18,82,576,82,I,1)
txt(18,90,558,11,'研究の問い',23,I,True)
txt(18,105,558,24,'出発までに使える時間の中で、量子計算から得た候補を取り入れると、\n既存の古典手法と比べて配送計画の質や配送成果はどの程度変わるか。',24,I,True)
txt(18,135,558,11,'対象は配送先の車両割当てと訪問順である。出発前に、容量と帰庫期限を満たす計画を得る条件を検討する。',21)

section(154,'01  モデルの構造と仮定｜検証した1台の配送計画')
txt(18,176,277,11,'単一拠点・1台・1巡回の模式図',22,I,True)
node1('depot',30,225,58,20,'拠点',23)
node1('customer_a',139,190,68,20,'配送先A',22)
node1('customer_b',219,234,68,20,'配送先B',22)
node1('customer_c',139,278,68,20,'配送先C',22)
edge('depot','customer_a',88,231,139,205,'model')
edge('customer_a','customer_b',207,205,244,234,'model')
edge('customer_b','customer_c',244,254,207,283,'model')
edge('customer_c','depot',139,283,88,239,'model')
txt(18,303,277,9,'A～Cは配送先を模式的に示した例である。',17.5)
txt(18,315,277,11,'道路は方向ごとの旅行時間で表す。',21)
txt(18,328,277,11,'J：拠点往復の総旅行時間を最小化する。',21,I,True)
txt(18,341,277,10,'各配送先を1回訪問し、同じ拠点へ戻る。',20)

table(310,176,[82,184],[
    ['項目','時間枠なしB系列の仮定・設定 [1,2]'],
    ['対象地域・拠点','大田区・京浜トラックターミナルの\n位置を想定した単一拠点 [3]'],
    ['配送全体の先数','3／4／5／25／100／125先'],
    ['量子側へ渡す先数','全体と同じ3～125先の訪問順全体\n小ブロックへの切出しではない＊'],
    ['車両・巡回','1台・1巡回・拠点発着'],
    ['車両容量','216荷物相当／台（重量kgではない）'],
    ['配送先の作業時間','102秒／先（拠点は0秒）'],
    ['帰庫期限','モデル開始から9時間（32,400秒）'],
    ['顧客別時間枠','なし（共通の帰庫上限とは別である）'],
    ['道路旅行時間','時間帯によらない固定値である'],
    ['古典対照','訪問順の交換を繰り返し、\n行き詰まると順序を崩して再探索']
],[11,19,13,19,13,13,13,13,13,13,19],pt=18,tag='conditions')

section(359,'02  評価パイプライン｜共通入力から候補比較・採用判断・成果評価へ')
txt(18,378,558,9,'入力は拠点・配送先・需要・道路旅行時間、配送成果は帰庫・各先の完了時刻・道路距離である。',19.5)
node1('input',18,414,86,18,'共通の配送入力',20)
node1('classical',139,390,132,18,'古典基準計画',22)
node1('quantum',139,442,132,18,'量子候補の生成',22)
node1('compare',313,414,111,18,'同一条件で比較',21)
node1('decision',452,414,124,18,'出発前の採用判断',21,True)
line(104,423,120,423,I,1.5);line(120,399,120,451,I,1.5)
edge('input','classical',120,399,139,399,'pipeline')
edge('input','quantum',120,451,139,451,'pipeline')
line(271,399,292,399,I,1.5);line(292,399,292,451,I,1.5);line(271,451,292,451,I,1.5)
edge('classical','compare',292,423,313,423,'pipeline')
diagrams['pipeline'].append(dict(source='quantum',target='compare'))
edge('compare','decision',424,423,452,423,'pipeline')
node1('adopt_candidate',365,463,94,18,'候補を採用',20,True)
node1('fallback',482,463,94,18,'基準計画を採用',20,True)
edge('decision','adopt_candidate',487,432,412,463,'pipeline')
edge('decision','fallback',543,432,529,463,'pipeline')
txt(418,438,35,9,'成立',17,I,False,'center','branch:pass')
txt(546,446,30,9,'不成立',17,I,False,'center','branch:fail')
node1('outcome',401,496,175,18,'配送成果の評価',22,True)
edge('adopt_candidate','outcome',412,481,412,496,'pipeline')
edge('fallback','outcome',529,481,529,496,'pipeline')

txt(18,518,558,8.5,'取得時間は前処理・候補生成・検証・選択の合計である。破線の枠は採用・実行の検証計画を表す。',18)
txt(18,529,558,9,'量子近似最適化（QAOA）は候補の得やすさを調整する手法である。本結果は通常計算機上での模擬計算である。[1,2]',19)
txt(18,540,558,9,'採用規則（案）：古典基準より短く、出発前に検証が完了し、容量・帰庫期限を満たす候補を採用する。',19)

section(557,'03  検証済みの主結果｜同じ入力の古典対照と量子候補を比較する')
txt(18,575,558,9,'Jは往復の総旅行時間［秒］（作業・計算時間を除く）。ΔJ＝量子候補−古典対照。負が改善、正が悪化である。',19.5)
rows=[['設定','比較件数','古典 J 平均［秒］','候補 J 平均［秒］','平均 ΔJ［秒］','平均絶対差［秒］']]
for label,key in [('位置交換など6設定','位置交換など6設定'),('全訪問順型・2層','GROVER_P2'),('全訪問順型・3層','GROVER_P3')]:
    g=GROUPS[key]
    rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.3f}",f"{float(g['candidate_mean_s']):,.3f}",f"+{float(g['delta_mean_s']):,.3f}",f"{float(g['absolute_mean_s']):,.3f}"])
rows.append(['全8設定の混合',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.3f}",f"{DATA['candidate_mean_s']:,.3f}",f"+{DATA['delta_mean_s']:,.3f}",f"{DATA['absolute_mean_s']:,.3f}"])
table(18,587,[126,62,93,93,92,92],rows,[13,12,12,12,12],pt=19.5,tag='results',aligns=['left','right','right','right','right','right'])
txt(18,651,558,16,'460入力（3・4・5・25・100先が各78、125先が70）×8設定＝3,680件の調整。全体行は8設定の混合平均である。\n各調整済み状態から8,192回抽出×10反復し、反復ごとの最良候補36,800件を保存した。10反復は状態を共用する。[1,2]',18)
txt(18,670,558,23,'全差の中央値0秒、最大+9,483.990秒。同等28,200件・悪化8,600件・改善0件。帰庫余裕は最小7,435.748秒である。\n＊交換範囲を制限する設定を含む。計算予算・初期解の保持規則が異なり、時間優位は未判定である。\n実採用効果・顧客別期限内配達率は未検証、道路距離は主比較で未集計である。実営業所の配置・運用の再現は未確認である。',17.5)

section(695,'04  複数台への拡張計画｜全体割当てと局所改善を分ける')
for j,(x,label) in enumerate(zip([18,162.33,306.67,451],['古典手法で全体割当て','局所の改善方法を比較','全体の制約を再検証','共通締切で採用判断'])):
    node1('multi_'+str(j),x,714,125,15,label,18.5,True)
    if j<3:edge('multi_'+str(j),'multi_'+str(j+1),x+126,721.5,[18,162.33,306.67,451][j+1]-1,721.5,'multi')
table(18,733,[105,104,271,78],[
    ['全体の車両数・先数','量子側の部分問題','検証すること','実施状況'],
    ['5台・500先','3～5先から（案）','車両割当て・各車両の訪問順・同一時間予算の比較手順','計画・未実施'],
    ['10台・1,000先','3～5先から（案）','割当てと訪問順の再現性、同一時間予算の比較手順','計画・未実施'],
    ['20台・2,000先','再現できた規模のみ','古典基準の品質・取得時間を評価し、量子比較の到達規模を記録','計画・未実施'],
    ['30台・3,000先','再現できた規模のみ','容量・帰庫期限への妥当性と古典基準を評価し、量子比較範囲を報告','計画・未実施']
],[12,12,12,12,12],pt=17.5,tag='extension')
txt(18,796,558,15,'最大30台・3,000先は妥当性を確認する計画値である。配備32台の国内例 [4] は規模の参考であり、同一便の稼働台数の根拠ではない。\n各台100先の作業は2時間50分、移動余裕6時間10分（待機なしの概算）。全工程を同じ時間枠で比較する。日間個数は配送先数に換算しない。',16.5)
line(18,814,576,814,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800／B_INPUT_CONDITIONS_460、PATHWAY1_CONDITIONS・OPERATIONAL_IMPACT',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv（再集計・照合）',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内：j-m-t.co.jp/terminal/keihin.html',
    '[4] ヤマト運輸（2023-10-02）八幡営業所公表資料：yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html'
]
for j,s in enumerate(refs):txt(18,816+j*5.7,558,5.7,s,13,I,lh=1.05)

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
S.notes_slide.notes_text_frame.text=notes
P.core_properties.title=TITLE
P.core_properties.subject='KMD Forum：白地・黒文字、モデルと仮定・パイプラインの図示'
P.core_properties.author='佐野巧馬 / Q/est'
P.save(O/f'{STEM}.pptx')
for name,data in [('LAYOUT',blocks),('TABLES',tablemeta),('DIAGRAM_NODES',diagram_nodes),('DIAGRAM_EDGES',diagrams)]:
    (O/'evidence'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(O/'evidence/SLIDE_NOTES.txt').write_text(notes)
(O/'evidence/POSTER_TEXT.txt').write_text('\n\n'.join(z['text'] for z in blocks))
print(O/f'{STEM}.pptx')
