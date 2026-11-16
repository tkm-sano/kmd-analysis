"""Extend the supplied summary slide with editable, source-backed detail slides."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
import json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SRC = ROOT / '研究紹介_佐野巧馬.pptx'
DEST = OUT / '研究紹介_佐野巧馬_詳細説明15枚.pptx'
P = Presentation(SRC)
NAVY, TEAL, PURPLE = '002060', '087E88', '6A5794'
GRAY, PALE, INK, WHITE = '808080', 'F2F2F2', '000000', 'FFFFFF'
FONT = 'Noto Sans JP'
S5 = 'review_outputs/quantum_ev_step5_20261105/'
S2 = 'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535/'
RESEARCH = 'docs/research/RESEARCH_DESIGN_SUMMARY.md'
THESIS = S5 + 'THESIS_FULL_TEXT.md'
GAP = S5 + 'STEP5_OBJECTIVE_GAP_ANALYSIS.md'
COND = S5 + 'STEP5_PATHWAY1_CONDITIONS.md'
MAT = S5 + 'STEP5_PATHWAY2_EVIDENCE.md'
FINAL = 'review_outputs/t08_t09_final_adoption_20261105/FINAL_REPORT_JA.md'

def box(s,x,y,w,h,fill=PALE):
    z=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    z.adjustments[0]=.055
    z.fill.solid(); z.fill.fore_color.rgb=RGBColor.from_string(fill)
    z.line.fill.background()
    z._element.spPr.append(OxmlElement('a:effectLst'))
    return z

def text(s,x,y,w,h,st,size=14,color=INK,bold=False,align=PP_ALIGN.LEFT):
    z=s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf=z.text_frame; tf.clear(); tf.word_wrap=True
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    for i,line in enumerate(st.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment=align; p.space_before=Pt(0); p.space_after=Pt(4)
        p.line_spacing=1.22
        r=p.add_run(); r.text=line
        r.font.name=FONT; r.font.size=Pt(size); r.font.bold=bold
        r.font.color.rgb=RGBColor.from_string(color)
        pr=r._r.get_or_add_rPr()
        ea=OxmlElement('a:ea'); ea.set('typeface',FONT); pr.append(ea)
    return z

def badge(s,n,x,y,color):
    box(s,x,y,.30,.30,color)
    text(s,x,y-.005,.30,.30,str(n),12,WHITE,True,PP_ALIGN.CENTER)

def slide(title,subtitle,section='研究全体',color=NAVY,sources=()):
    s=P.slides.add_slide(P.slide_layouts[6])
    text(s,.47,.14,12.4,.42,title,16,NAVY,True)
    text(s,.47,.70,12.3,.55,subtitle,12)
    text(s,.47,1.22,12.3,.25,section,11,color,True)
    text(s,.47,7.13,11.8,.20,'研究紹介｜佐野巧馬　　経路番号は1枚目の①・②・③に統一',8,GRAY)
    text(s,12.2,7.08,.65,.27,f'{len(P.slides):02d} / 15',9,GRAY,False,PP_ALIGN.RIGHT)
    notes='【資料の位置付け】1枚目は元ファイルのまま。経路①=定時配達、②=経路・電力量、③=材料・質量・電力量。\n'
    notes+='後続論文の経路1は本資料①の上流、経路2は本資料③に対応。\n【根拠資料】\n'
    notes+='\n'.join(str(ROOT/v) for v in sources)
    ns=s.notes_slide
    if ns.notes_text_frame is None:
        template=Presentation()
        body=template.slides.add_slide(template.slide_layouts[6]).notes_slide.notes_placeholder
        ns.shapes._spTree.append(deepcopy(body._element))
    ns.notes_text_frame.text=notes
    return s

def bottom(s,heading,body,color=NAVY):
    box(s,.47,6.12,12.4,.78)
    text(s,.66,6.23,2.05,.44,heading,12,color,True)
    text(s,2.78,6.22,9.85,.53,body,12)

def card(s,x,y,w,h,heading,body,color=NAVY,num=None):
    box(s,x,y,w,h)
    hx=x+.20
    if num is not None:
        badge(s,num,hx,y+.18,color); hx+=.46
    text(s,hx,y+.19,w-(hx-x)-.18,.39,heading,14,color,True)
    text(s,x+.20,y+.83,w-.40,h-.95,body,14)

def flow(s,labels,y=1.78,h=1.05,color=NAVY):
    n=len(labels); gap=.34; w=(12.4-gap*(n-1))/n
    for i,lab in enumerate(labels):
        x=.47+i*(w+gap); box(s,x,y,w,h,GRAY if i in [0,n-1] else PALE)
        text(s,x+.10,y+.23,w-.20,h-.28,lab,14,WHITE if i in [0,n-1] else INK,True,PP_ALIGN.CENTER)
        if i<n-1: text(s,x+w+.025,y+.32,.29,.4,'→',14,color,True,PP_ALIGN.CENTER)

def rows(s,headers,data,widths=(2.5,4.65,5.25),y=1.68,rh=.93,colors=None,size=12):
    xs=[.47]
    for w in widths[:-1]: xs.append(xs[-1]+w+.07)
    for j,(h,w,x) in enumerate(zip(headers,widths,xs)):
        box(s,x,y,w,.43,GRAY); text(s,x+.14,y+.065,w-.28,.30,h,12,WHITE,True)
    for i,row in enumerate(data):
        yy=y+.53+i*rh
        for j,(v,w,x) in enumerate(zip(row,widths,xs)):
            box(s,x,yy,w,rh-.08)
            text(s,x+.14,yy+.12,w-.28,rh-.23,v,size,(colors[i] if colors else NAVY) if j==0 else INK,j==0)

# 02
s=slide('この研究で明らかにしたいこと','量子技術の能力が、どの条件で配送サービスと走行時の電力量に伝わるかを検討します。',sources=(RESEARCH,THESIS))
for n,(h,b,c) in enumerate([
 ('訪問順序と配達完了','計画上の旅行時間が変わると、\n配達作業の完了時刻はどう変わるか。\nその差が期限判定に表れる条件は何か。',NAVY),
 ('配送経路と走行状態','距離・停止・加減速の違いが、\n走行電力量にどう表れるか。\n交通条件で比較はどう変わるか。',TEAL),
 ('材料性能と車両質量','材料性能の変化がパック軽量化へ\n伝わる条件は何か。部材の増加で\n効果が相殺される条件は何か。',PURPLE)],1):
    card(s,.47+(n-1)*4.20,1.75,4.0,3.95,h,b,c,n)
bottom(s,'研究の現在地','限定した計算結果と感度分析を整理した段階。量子技術による実運用改善は未実証。')

# 03
s=slide('比較する配送条件と評価範囲','変える条件と固定する条件を分け、比較が成立する範囲を明示します。',sources=(RESEARCH,THESIS))
rows(s,['経路','変える条件','固定・限定する条件'],[
 ('① 訪問順序 → 定時配達','古典計算／量子アルゴリズムの\n模擬出力による訪問順序','配送先・車両割当・出発時刻・作業時間。\n主要B系列には顧客時間窓なし。'),
 ('② 配送経路 → 電力量','経路・距離・速度時系列・加減速','対象車両1台。背景交通なし。\n車両・電池条件を共通化。'),
 ('③ 材料 → 質量 → 電力量','比エネルギー／部材設計による\nパック質量・車両質量','電池の設計電力量と速度時系列を固定。\n車体・積載など他の質量は固定。')],rh=1.12,colors=[NAVY,TEAL,PURPLE])
bottom(s,'適用範囲の限界','実道路・交通の妥当性に残課題。配送中の充電や車両間の再割当は今回扱わない。')

# 04
s=slide('入力データから評価指標までの流れ','訪問順序の計算と、保存された走行軌跡の電力量評価は別工程です。',sources=(THESIS,RESEARCH))
flow(s,['道路・需要・固定OD','古典／量子模擬\n訪問順序','配達完了時刻\n期限との比較'],1.72,.98,NAVY)
flow(s,['保存された経路','SUMOの保存軌跡\n速度・加減速','走行時の\n消費電力量'],3.15,.98,TEAL)
text(s,.70,2.83,11.9,.27,'①：計画の評価。実行・採用・契約期限への接続は未完了。',12,NAVY)
text(s,.70,4.26,11.9,.27,'②：新しい訪問順序から、同条件の走行軌跡を生成して比較する接続は未完了。',12,TEAL)
box(s,.47,4.85,12.4,.79)
badge(s,3,.68,5.08,PURPLE)
text(s,1.15,5.08,11.3,.34,'材料・部材設計 → パック質量 → 車両質量 → 同じ保存軌跡の電力量を再評価',14,PURPLE,True)
bottom(s,'接続上の留保','経路計算B系列と電力量評価C系列は、件数が同じでも入力の対応が確認された集合ではない。')

# 05
s=slide('経路①：訪問順序から定時配達率を求める方法','定時判定の対象は、配達先への到着時刻ではなく、配達作業の完了時刻です。','① 訪問順序 → 配達完了時刻 → 定時配達率',NAVY,(RESEARCH,COND,THESIS))
flow(s,['訪問順序','移動・待機','配達作業','完了時刻','期限判定'],h=1.05)
card(s,.47,3.16,6.10,2.53,'評価指標の定義','定時配達率 ＝ 期限内に完了した配達数\n　　　　　　　 ÷ 固定した評価対象の配達数\n未配達を分母から除外しない。',NAVY)
card(s,6.77,3.16,6.10,2.53,'計算で区別する時間','計画作成にかかる時間／現場で利用可能な時刻\n旅行時間／時間窓待機／配達作業時間\n顧客での完了時刻／デポへの帰庫時刻',NAVY)
bottom(s,'未完了','契約期限に基づく顧客別完了判定と実運用での検証。B系列の旅行時間差で代用しない。')

# 06
s=slide('経路①：現時点で確認できている結果','保存計画の旅行時間を主古典対照greedyと比較。量子側はCPUシミュレーションの出力です。','① 解品質の比較結果（定時配達率の結果とは別）',NAVY,(GAP,COND))
for x,w,h,b in [(.47,4.0,'460 入力','3〜125顧客の固定評価集合'),(4.67,4.0,'8 設定 × 10 測定','同一学習済み設定からの測定反復'),(8.87,4.0,'36,800 保存計画','主greedyに対する改善 0件')]:
    box(s,x,1.73,w,1.10);text(s,x+.18,1.92,w-.36,.38,h,18,NAVY,True);text(s,x+.18,2.40,w-.36,.28,b,11)
text(s,.65,3.13,11.9,.38,'主greedyに対する旅行時間差：同等 28,200件 ／ 悪化 8,600件 ／ 改善 0件',14,NAVY,True)
barx,bary,barw=.65,3.80,11.95
for xx,ww,cc,lab in [(barx,barw*28200/36800,GRAY,'同等 76.63%'),(barx+barw*28200/36800,barw*8600/36800,NAVY,'悪化 23.37%')]:
    sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(xx), Inches(bary), Inches(ww), Inches(.64)); sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(cc);sh.line.fill.background()
    text(s,xx+.07,bary+.17,ww-.14,.30,lab,13,WHITE,True,PP_ALIGN.CENTER)
text(s,.65,4.80,11.9,.73,'ΔJ ＝ 候補の旅行時間 − greedyの旅行時間（正は悪化）\n設定・規模で結果が異なるため、全体平均を単一手法の代表効果とはしない。',14)
bottom(s,'未検証','旅行時間差が、契約期限に基づく定時配達率の差として現れるかは未検証。')

# 07
s=slide('経路①：統計的妥当性と残る検証','保存結果の記述統計は実施済みですが、公平な性能比較と一般化の根拠は十分ではありません。','① 分析済みの内容と、まだ言えないこと',NAVY,(GAP,COND,S2+'STATISTICAL_VALIDITY_AUDIT.md'))
card(s,.47,1.75,4.0,3.97,'実施済み','・同一入力での対応比較\n・入力別／設定別／規模別の分布\n・平均・中央値・SDなどの集計\n・少数入力への感度の確認\n・保存計画の可行性の再確認',NAVY)
card(s,4.67,1.75,4.0,3.97,'独立性の留保','・10測定は10回の独立学習ではない\n・同じ入力内の出力は反復測定\n・需要group・親入力に依存が残る\n・460入力も独立無作為標本ではない\n・出力件数を独立標本数にしない',NAVY)
card(s,8.87,1.75,4.0,3.97,'追加で必要な検証','・学習反復と未見入力での安定性\n・計算予算と出力規則の統制\n・比較する設定・指標の事前設定\n・契約期限・実行条件を含む評価\n・計画採用と運用成果の接続',NAVY)
bottom(s,'現在の結論','固定集合における記述結果。量子優位性や、定時配達率への統計的な効果は確立していない。')

# 08
s=slide('経路②：配送経路から消費電力量を求める方法','距離だけでなく、停止・再発進や加減速を含む速度時系列を電力量モデルへ入力します。','② 配送経路 → 走行距離・走行状態 → 消費電力量',TEAL,(RESEARCH,THESIS,MAT))
flow(s,['配送経路','SUMO\n速度時系列','走行抵抗\n加減速','電池側の\n電力量推計'],h=1.08,color=TEAL)
card(s,.47,3.28,6.10,2.42,'入力するもの','各区間の速度・加速度・時間\n車両の走行質量、転がり抵抗、空力条件\n駆動効率（凍結モデルでは0.9）',TEAL)
card(s,6.77,3.28,6.10,2.42,'現行モデルの条件','平坦路、空荷、回生なし、補機除外\n対象車両1台・他車両との相互作用なし\n保存された観測区間を評価',TEAL)
bottom(s,'評価境界','現状は限定条件での駆動電力量推計。回生・補機を含む実車の正味電力量全体とは区別する。',TEAL)

# 09
s=slide('経路②：現時点で比較できること','電力量モデルの計算と、「量子側の経路が省電力か」の評価を分けて整理します。','② 保存軌跡の評価と、新しい経路への接続',TEAL,(THESIS,MAT,RESEARCH))
rows(s,['評価対象','現時点で扱える内容','残っている接続・留保'],[
 ('保存された走行軌跡','距離・速度・加減速から、\n同じ電力量モデルで計算できる。','道路・背景交通・観測区間に条件付く。\n実走行での妥当性は未確立。'),
 ('経路間の電力量比較','入力条件が一致する保存資料の範囲で、\n差を記述する。','新しいB系列の候補計画とC系列軌跡を\n直接結び付けた比較は未完了。'),
 ('旅行時間と省電力','距離・停止・加減速を分けて\n比較する必要がある。','短時間化だけで省電力とは断定しない。\n同じ配達サービスを保つ条件も必要。')],rh=1.10,colors=[TEAL]*3)
bottom(s,'未完了','量子模擬／古典の計画から、同条件の走行軌跡・配達成果・電力量まで接続した評価。',TEAL)

# 10
s=slide('経路②：モデル精緻化の課題','現実の走行を説明するために追加したい要因と、その検証に必要な情報を整理します。','② 精緻化の候補（効果量・優先順位は未確定）',TEAL,(THESIS,RESEARCH))
rows(s,['精緻化する要因','現在の扱い','追加検証に必要な情報'],[
 ('交通・道路','背景交通なし。道路受入に残課題。','交通量・信号・渋滞・規制と道路網の検証'),
 ('積載・勾配','空荷・平坦路で計算。','配送中の荷重変化と標高・勾配'),
 ('回生・補機','現行の凍結モデルから除外。','受入回生、電池状態、空調等の消費'),
 ('実車・観測区間','保存された速度・時間の範囲で計算。','電池側計測との照合、末端区間の確認')],rh=.83,colors=[TEAL]*4)
bottom(s,'未検討の範囲','全要因を組み込んだ場合の効果量や、古典／量子候補間の経路順位の変化は未確定。',TEAL)

# 11
s=slide('経路③：材料性能を車両質量へ変換する方法','材料の容量・電圧と、セル・パックの重量エネルギー密度を区別します。','③ 材料物性 → 電池比エネルギー → 車両質量',PURPLE,(RESEARCH,MAT,FINAL))
flow(s,['材料の\n容量・電圧','電極・セル\n部材設計','電池パック\n質量','車両の\n走行質量'],h=1.08,color=PURPLE)
card(s,.47,3.28,6.10,2.42,'単純化した感度分析','パック質量［kg］\n　＝ 設計電力量［Wh］÷ 比エネルギー［Wh/kg］\n設計電力量を固定し、質量差を車両へ反映。',PURPLE)
card(s,6.77,3.28,6.10,2.42,'部材を分けたモデル','正負極・箔・膜・電解液などを計上。\n材料性能の改善と、追加部材による増量を分離。\n不明な外装・タブ等は未知のまま残す。',PURPLE)
bottom(s,'モデル仮定','車体・補強・積載などを固定し、パック質量差を車両質量差へ1対1で反映する。',PURPLE)

# 12
s=slide('経路③：軽量化の効果と相殺条件','同じ軌跡・同じ物理条件で、質量差が走行電力量へ伝わる条件を分析しています。','③ 確認済みのモデル応答と、条件付きの材料参考例',PURPLE,(MAT,FINAL))
card(s,.47,1.75,6.10,2.15,'材料に依存しない質量応答','保存460軌跡 × 転がり抵抗2条件を評価。\n走行質量1000〜1250kgで、質量に対する\n電力量の傾きが正であることを確認。',PURPLE)
card(s,6.77,1.75,6.10,2.15,'部材の追加による相殺','完成パックの軽量化量 ＝ b − δ\nb：同じ会計で得た質量削減\nδ：追加・未知部材の質量差',PURPLE)
for i,(h,b) in enumerate([('δ < b','軽量化が残る'),('δ = b','効果が相殺される'),('δ > b','増量へ逆転する')]):
    x=.47+i*4.2;box(s,x,4.24,4,1.27);text(s,x+.18,4.41,3.64,.36,h,19,PURPLE,True);text(s,x+.18,4.97,3.64,.33,b,14)
bottom(s,'参考値の扱い','具体材料からの質量差・削減率は入力適格性に留保がある参考例。主成果は感度と成立条件。',PURPLE)

# 13
s=slide('経路③：材料・完成パックで未確認のこと','計算の整合性が確認できても、実用材料・完成パックの性能が確認されたことにはなりません。','③ 上流の量子材料研究と下流モデルの間に残る接続',PURPLE,(MAT,FINAL))
rows(s,['段階','必要な確認','現在の状態'],[
 ('量子計算 → 材料改善','物性予測、合成、比較実験への追加的寄与','本研究で量子由来の実材料改善は未実証。'),
 ('材料 → 実用セル','同条件の容量・平均電圧・利用率、\n形成過程・負極・寿命・安全','逆算参照容量の実用全電池への採用は保留。\n材料値をそのままパック性能にしない。'),
 ('セル → 完成パック','外装・タブ・配線・冷却・BMS等の\n完成部材表と設計条件','未知部材が残り、完成質量は一意に未確定。\n未知値をゼロで埋めない。'),
 ('完成パック → 実車','車体・積載・制御・実走行での検証','固定軌跡モデルの結果。実車効果は未検証。')],rh=.84,colors=[PURPLE]*4,size=11.5)
bottom(s,'未完了','量子材料研究から完成パック・実車までの接続。具体的削減率を量子技術の効果に帰属しない。',PURPLE)

# 14
s=slide('3経路の到達点と残る接続','確認できた中間段階と、最終成果への未接続部分を並べます。',sources=(THESIS,GAP,COND,MAT))
rows(s,['因果経路','確認済み・条件付きで示せること','未完了・未検証のこと'],[
 ('① 訪問順序 → 定時配達','【確認済み】保存計画の解品質比較。\n指定した支持内での改善解の有無。','【未検証】契約期限に基づく定時配達率。\n計画取得・採用・実行までの運用接続。'),
 ('② 配送経路 → 電力量','【条件付き】保存軌跡と限定物理条件での\n電力量推計。','【未完了】新しい経路出力との一貫接続。\n交通・回生・積載等の精緻化と実車照合。'),
 ('③ 材料 → 質量 → 電力量','【条件付き】部材会計、相殺条件、\n固定軌跡における質量感度。','【未実証】量子由来の材料改善。\n実用セル・完成パック・実車への接続。')],rh=1.12,colors=[NAVY,TEAL,PURPLE])
bottom(s,'研究として示せること','現時点の成果は、限定した計算結果と、技術性能を配送成果へつなぐ成立・不成立条件。')

# 15
s=slide('今回相談したい事項と次の検証','モデルの仮定・評価指標・研究範囲について、妥当な境界と検証の優先順位を伺います。','今回伺いたい事項',NAVY,(RESEARCH,COND,MAT))
for i,(h,b) in enumerate([
 ('1. モデルの仮定について','他車両との相互作用を考慮しない条件は、経路間の定時配達率や電力量の比較にどう影響するか。\n次の検証：道路・交通の妥当性確認と、経路②の精緻化。'),
 ('2. 評価指標について','定時配達率と走行時の電力量に、補足すべき指標・比較条件はあるか。\n次の検証：経路①の顧客別期限評価、反復・依存・比較予算の整理。'),
 ('3. 研究範囲について','充電・再割当を扱わないモデルは、どの配送条件まで適用できるか。\n次の検証：適用範囲を明示し、経路③の材料入力・完成部材表を確認。')]):
    y=1.65+i*1.43;box(s,.47,y,12.4,1.28)
    text(s,.67,y+.13,11.95,.32,h,14,NAVY,True)
    text(s,.67,y+.58,11.95,.62,b,12)
bottom(s,'検討の目的','成立条件・例外・反例を明らかにする。専門家の説明と、独立した実証根拠を分けて記録する。')

assert len(P.slides)==15
P.core_properties.title='量子技術がEVラストワンマイル配送に与える影響｜詳細説明'
P.core_properties.subject='3経路の詳細・確認済み事項・未完了事項'
P.core_properties.author='佐野巧馬'
P.save(DEST)

# Preserve the exact original slide XML, relationships, and existing package parts.
# python-pptx otherwise serializes slide1 even when it has not been edited.
tmp=DEST.with_suffix('.tmp.pptx')
with ZipFile(SRC) as original, ZipFile(DEST) as authored, ZipFile(tmp,'w',ZIP_DEFLATED) as final:
    orig_names=set(original.namelist())
    for name in authored.namelist():
        keep_original=(name=='ppt/slides/slide1.xml' or name=='ppt/slides/_rels/slide1.xml.rels'
                       or name.startswith(('ppt/theme/','ppt/slideMasters/','ppt/slideLayouts/','ppt/media/')))
        final.writestr(name, original.read(name) if keep_original and name in orig_names else authored.read(name))
tmp.replace(DEST)

# Validate slide count, all source pointers, shape boundaries, and exact summary preservation.
Q=Presentation(DEST); issues=[]
for i,s in enumerate(Q.slides,1):
    for sh in s.shapes:
        if i>1 and (sh.left<0 or sh.top<0 or sh.left+sh.width>Q.slide_width+100 or sh.top+sh.height>Q.slide_height+100):
            issues.append({'slide':i,'shape':sh.shape_id,'issue':'outside canvas'})
for source in (RESEARCH,THESIS,GAP,COND,MAT,FINAL,S2+'STATISTICAL_VALIDITY_AUDIT.md'):
    assert (ROOT/source).exists(), source
with ZipFile(SRC) as a,ZipFile(DEST) as b:
    same=a.read('ppt/slides/slide1.xml')==b.read('ppt/slides/slide1.xml')
assert same and len(Q.slides)==15 and not issues,issues
(OUT/'validation.json').write_text(json.dumps({'slides':15,'original_slide_xml_identical':same,'boundary_issues':issues,'editable':True},ensure_ascii=False,indent=2))
print(DEST)
