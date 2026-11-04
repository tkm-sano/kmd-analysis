"""Build an editable A1 poster and a vector PDF from the same layout.

Run with PYTHONPATH=/tmp/kmd-poster-authoring-deps python this_file.py.
Uses saved results; does not rerun scientific experiments.
"""
import csv
import json
import math
from pathlib import Path
from zipfile import ZipFile

from pptx import Presentation
from pptx.util import Mm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
STEM = 'a1_academic_poster_restructured_20261104'
MM = 72 / 25.4
W, H = 594, 841
NAVY, BLUE, ORANGE = '#143653', '#286A96', '#A6522C'
INK, MUTED, RULE, PALE = '#17232D', '#455765', '#B9C6CF', '#EDF3F7'
FONT_PATH = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
pdfmetrics.registerFont(TTFont('CJK', FONT_PATH))
pdfmetrics.registerFont(TTFont('Latin', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('LatinBold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
CJK_GLYPHS = pdfmetrics.getFont('CJK').face.charToGlyph
LATIN_GLYPHS = pdfmetrics.getFont('Latin').face.charToGlyph


def font_for(ch, bold=False):
    if ord(ch) < 0x3000 and ord(ch) in LATIN_GLYPHS:
        return 'LatinBold' if bold else 'Latin'
    if ord(ch) in CJK_GLYPHS:
        return 'CJK'
    if ord(ch) in LATIN_GLYPHS:
        return 'LatinBold' if bold else 'Latin'
    raise ValueError(f'No font for {ch!r} U+{ord(ch):04X}')


def runs(s, bold=False):
    result = []
    for ch in s:
        f = font_for(ch, bold)
        if result and result[-1][0] == f:
            result[-1] = (f, result[-1][1] + ch)
        else:
            result.append((f, ch))
    return result


def width(s, pt, bold=False):
    return sum(pdfmetrics.stringWidth(t, f, pt) for f, t in runs(s, bold)) / MM


def wrap(s, max_width, pt, bold=False):
    result = []
    for paragraph in s.split('\n'):
        line = ''
        for ch in paragraph:
            if line and width(line + ch, pt, bold) > max_width:
                if ch in '、。，．）］」』%％':
                    result.append(line[:-1])
                    line = line[-1] + ch
                else:
                    result.append(line.rstrip())
                    line = ch.lstrip()
            else:
                line += ch
        result.append(line)
    return result


class Poster:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Mm(W), Mm(H)
        self.slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.pdf = canvas.Canvas(str(OUT / f'{STEM}.pdf'), pagesize=(W*MM, H*MM))
        self.blocks = []
        self.text_log = []

    def rect(self, x, y, w, h, fill=None, stroke=None, stroke_pt=0.7):
        self.pdf.setLineWidth(stroke_pt)
        if fill: self.pdf.setFillColor(HexColor(fill))
        if stroke: self.pdf.setStrokeColor(HexColor(stroke))
        self.pdf.rect(x*MM, (H-y-h)*MM, w*MM, h*MM,
                      fill=int(fill is not None), stroke=int(stroke is not None))
        shape = self.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Mm(x), Mm(y), Mm(w), Mm(h))
        if fill:
            shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string(fill[1:])
        else: shape.fill.background()
        if stroke:
            shape.line.color.rgb = RGBColor.from_string(stroke[1:]); shape.line.width = Pt(stroke_pt)
        else: shape.line.fill.background()

    def line(self, x1, y1, x2, y2, color=RULE, pt=0.7):
        self.pdf.setStrokeColor(HexColor(color)); self.pdf.setLineWidth(pt)
        self.pdf.line(x1*MM, (H-y1)*MM, x2*MM, (H-y2)*MM)
        s = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Mm(x1), Mm(y1), Mm(x2), Mm(y2))
        s.line.color.rgb = RGBColor.from_string(color[1:]); s.line.width = Pt(pt)

    def arrow(self, x1, y1, x2, y2, color=MUTED):
        self.line(x1,y1,x2,y2,color,1)
        a = math.atan2(y2-y1,x2-x1)
        for da in (-0.5,0.5):
            self.line(x2,y2,x2-2.5*math.cos(a+da),y2-2.5*math.sin(a+da),color,1)

    def text(self, x, y, w, s, pt=24, bold=False, color=INK, lh=None, align='left', max_h=None, tag=''):
        lh = lh or pt / MM * 1.27
        lines = wrap(s, w, pt, bold)
        h = max(pt / MM * 1.2, len(lines)*lh)
        if max_h is not None and h > max_h + .01:
            raise ValueError(f'Text overflow {tag}: needs {h:.1f}mm, available {max_h}mm: {s[:65]}')
        assert x >= 0 and y >= 0 and x+w <= W+.01 and y+h <= H+.01, (tag,x,y,w,h)
        for i, line in enumerate(lines):
            offset = (w-width(line,pt,bold))/2 if align=='center' else (w-width(line,pt,bold) if align=='right' else 0)
            xp = (x+offset)*MM
            baseline = (H-y-i*lh)*MM - pt*.91
            for f, t in runs(line,bold):
                self.pdf.setFont(f,pt); self.pdf.setFillColor(HexColor(color))
                if bold and f=='CJK':
                    self.pdf.saveState()
                    obj=self.pdf.beginText(xp,baseline);obj.setFont(f,pt);obj.setTextRenderMode(2)
                    self.pdf.setStrokeColor(HexColor(color));self.pdf.setLineWidth(.12)
                    obj.textOut(t);self.pdf.drawText(obj)
                    self.pdf.restoreState()
                else: self.pdf.drawString(xp,baseline,t)
                xp += pdfmetrics.stringWidth(t,f,pt)
        box=self.slide.shapes.add_textbox(Mm(x),Mm(y),Mm(w),Mm(h+.5))
        box.name=tag or s[:32]
        tf=box.text_frame;tf.clear();tf.word_wrap=False
        tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
        tf.vertical_anchor=MSO_ANCHOR.TOP
        for i,line in enumerate(lines):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
            p.line_spacing=Pt(lh*MM);p.space_before=p.space_after=Pt(0)
            if align!='left':
                from pptx.enum.text import PP_ALIGN
                p.alignment=PP_ALIGN.CENTER if align=='center' else PP_ALIGN.RIGHT
            for f,t in runs(line,bold):
                r=p.add_run();r.text=t;r.font.size=Pt(pt);r.font.bold=bold
                r.font.name='Yu Gothic' if f=='CJK' else 'DejaVu Sans'
                r.font.color.rgb=RGBColor.from_string(color[1:])
        self.blocks.append({'tag':tag,'x_mm':x,'y_mm':y,'w_mm':w,'h_mm':h,'font_pt':pt,'text':s})
        self.text_log.append(s)
        return y+h

    def section(self,x,y,w,title,color=NAVY):
        self.text(x,y,w,title,pt=32,bold=True,color=color,max_h=16,tag=title)
        self.line(x,y+15,w+x,y+15,color,1.4)

    def sub(self,x,y,w,title):
        self.text(x,y,w,title,pt=27,bold=True,color=NAVY,max_h=13,tag=title)

    def cell(self,x,y,w,h,s,pt=24,bold=False,fill=None,align='left'):
        if fill: self.rect(x,y,w,h,fill)
        lines=wrap(s,w-5,pt,bold)
        th=len(lines)*pt/MM*1.27
        self.text(x+2.5,y+max(1,(h-th)/2),w-5,s,pt,bold,align=align,max_h=h,tag='table-cell')

    def save(self,notes):
        title='量子技術がEV配送の定時配達率と走行時のバッテリー消費電力量に影響を及ぼす仕組みと成立条件'
        self.prs.core_properties.title=title;self.prs.core_properties.author='佐野巧馬 / Q/est'
        self.slide.notes_slide.notes_text_frame.text=notes
        self.prs.save(OUT/f'{STEM}.pptx')
        self.pdf.setTitle(title);self.pdf.setAuthor('佐野巧馬 / Q/est')
        self.pdf.showPage();self.pdf.save()
        (OUT/f'{STEM}_layout.json').write_text(json.dumps(self.blocks,ensure_ascii=False,indent=2))
        (OUT/f'{STEM}_text.txt').write_text('\n\n'.join(self.text_log))


def read_results():
    rows=list(csv.DictReader((ROOT/'review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv').open()))
    scales=['R0','R1','R2','R3','R4','R5']
    data=[]
    for n,scale in zip([3,4,5,25,100,125],scales):
        r=[v for v in rows if v['scale']==scale and v['config_id'] in ('GROVER_P2','GROVER_P3')]
        assert len(r)==2
        vals=sorted(float(v['mean_delta_objective_s']) for v in r)
        def fmt(v):
            if abs(v)<.005: return '0.00'
            return ('+' if v>0 else '−')+f'{abs(v):,.2f}'
        value=fmt(vals[0]) if abs(vals[1]-vals[0])<.005 else f'{fmt(vals[0])} ～ {fmt(vals[1])}'
        data.append([str(n),r[0]['physical_inputs'],value])
    c=list(csv.DictReader((ROOT/'review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_PAIRED_DIFFERENCES.csv').open()))
    a=[r for r in c if r['dataset']=='CLASSICAL' and r['method']=='CLASSICAL' and r['scenario_id']=='COND_S200_REF' and r['rolling_case']=='CRR_LOWER_BOUND']
    assert len(a)==460 and len({r['problem_id'] for r in a})==460
    energy_pct=100*sum(float(r['saving_DC_Wh']) for r in a)/sum(float(r['baseline_DC_Wh']) for r in a)
    lp,s=96.145654799,90.697357384
    other=988.888888889+55
    rates=[100*(lp-s)/lp,100*(lp-s)/(other+lp),energy_pct]
    return data,rates


def build():
    p=Poster();data,rates=read_results()
    X1,X2,CW=15,304,275
    # Header: exact user title; subtitle intentionally absent.
    for y,s in [(10,'量子技術がEV配送の定時配達率と'),(33,'走行時のバッテリー消費電力量に影響を及ぼす'),(56,'仕組みと成立条件')]:
        p.text(15,y,564,s,pt=56,bold=True,color=NAVY,lh=23,align='center',max_h=24,tag='title')
    p.text(15,83,564,'佐野巧馬　Q/est',pt=29,align='center',max_h=15,tag='author')
    p.line(15,102,579,102,NAVY,1.7)
    p.text(15,109,564,'1　目的　量子計算が配送計画と電池開発を通じて配送システムに寄与し得る条件を、文献と保存計算結果から検討する。',pt=26,max_h=26,tag='purpose')
    p.text(15,137,564,'分析視点：技術と運用・設計判断の関係［社会技術システム：4］、期待効果と前提の省察［RRI：3］。',pt=21,color=MUTED,max_h=11,tag='framework')
    p.line(297,156,297,527,RULE,.7)
    p.section(X1,156,CW,'2　配送計画：方法と結果',BLUE)
    p.section(X2,156,CW,'3　電池材料：方法と結果',ORANGE)
    p.sub(X1,179,CW,'方法')
    y=p.text(X1,194,CW,'対象：3・4・5・25・100・125配送先の計460問題例。全配送先を各1回訪問。顧客時間窓なし。',pt=24,max_h=33,tag='planning-method-target')
    y=p.text(X1,y+2,CW,'比較：初期経路の近傍探索と全訪問順を対象とするGrover型探索[1]。評価方法・探索操作・層数を変えた8条件、各10測定反復。',pt=24,max_h=44,tag='planning-method-comparison')
    y=p.text(X1,y+2,CW,'指標：ΔJ＝J−J₀［秒］。出発・帰庫を含む総移動時間の古典初期解との差。負値は改善。',pt=24,max_h=33,tag='planning-metric')
    p.text(X1,282,CW,'1問題例＝配送先・需要・移動時間行列を定めた入力。',pt=20,color=MUTED,max_h=18,tag='problem-definition')
    p.sub(X2,179,CW,'方法')
    y=p.text(X2,194,CW,'参照：未処理LPと表面処理S-200の電極試験値[5]。保持率から逆算した参照比容量171.9／196.0 Ah/kgを使用。',pt=24,max_h=44,tag='materials-method-source')
    y=p.text(X2,y+2,CW,'換算：容量20 kWh・平均電圧を固定して電極材料量を推計。その他部材を固定し、同じ460速度軌跡で質量だけを変えて電力量を計算。',pt=24,max_h=44,tag='materials-method-conversion')
    p.text(X2,y+2,CW,'別途、電極・集電体・セパレータ・電解液を個別計上した183設計条件を照合した。',pt=24,max_h=30,tag='materials-method-components')
    p.text(X2,282,CW,'1速度軌跡＝保存された走行速度の時系列。計画側の460問題例とは別資料。',pt=20,color=MUTED,max_h=18,tag='trajectory-definition')
    # Symmetric main results, identical level of detail.
    p.sub(X1,306,CW,'結果：総移動時間と探索範囲')
    p.sub(X2,306,CW,'結果：電池・車両・電力量の変化')
    widths=[48,46,181];headers=['配送先数','問題例数','ΔJ［秒］']
    tx=X1
    for w,s in zip(widths,headers):
        p.cell(tx,322,w,14,s,23,True,PALE,'center');tx+=w
    for i,row in enumerate(data):
        ry=336+14*i;tx=X1
        for w,s in zip(widths,row):
            p.cell(tx,ry,w,14,s,23,False,None,'center');tx+=w
        p.line(X1,ry+14,X1+CW,ry+14,RULE,.5)
    p.text(X1,423,CW,'表1　Grover型探索。反復を問題例内で平均後、規模内で平均。範囲は層数2条件の平均値の最小～最大。',pt=20,color=MUTED,max_h=28,tag='table-caption')
    p.text(X1,456,CW,'4・5配送先の改善例は計7問題例。25・100・125配送先では平均総移動時間が増加した。',pt=24,max_h=33,tag='planning-result-scale')
    p.text(X1,490,CW,'近傍に探索範囲を限定した比較では、2,300回のパラメータ最適化すべてで、範囲内の厳密最小値が古典初期値と一致した。',pt=24,max_h=33,tag='planning-result-support')
    # Native shapes, common zero baseline and consistent percent scale.
    bx,bw=X2+137,106
    labels=[('電池質量','96.15 → 90.70 kg'),('走行時総質量','1,140.03 → 1,134.59 kg'),('総走行消費電力量','460速度軌跡の総量')]
    for yy,(label,note),v in zip([331,362,393],labels,rates):
        p.text(X2,yy,132,label,pt=24,bold=True,max_h=12,tag='chart-label')
        p.text(X2,yy+12,132,note,pt=18.5,color=MUTED,max_h=10,tag='chart-source-value')
        p.rect(bx,yy+3,bw*v/6,8,ORANGE)
        digits=2 if v>1 else 3
        p.text(bx+bw*v/6+2,yy,579-(bx+bw*v/6+2),f'{v:.{digits}f}%',pt=24,bold=True,max_h=12,tag='chart-percent')
    p.line(bx,326,bx,420,MUTED,.7);p.line(bx,420,bx+bw,420,MUTED,.7)
    for v in [0,2,4,6]:
        xx=bx+bw*v/6;p.line(xx,420,xx,422,MUTED,.7)
        p.text(xx-5,423,10,str(v),pt=19,align='center',max_h=10,tag='chart-tick')
    p.text(bx,434,bw,'基準LPに対する削減率［%］',pt=20,align='center',max_h=10,tag='chart-axis')
    p.text(X2,450,CW,'図1　容量固定時の比較。各LP値を分母とし、電力量は総量加重。固定速度・平坦路・回生なし・補機除外、下側転がり抵抗条件。運転者55 kg・貨物0 kg。',pt=20,color=MUTED,max_h=37,tag='energy-caption')
    p.text(X2,490,CW,'電極・集電体・セパレータ・電解液を個別計上した別推計では、代表設計の未計上部材差5.98／9.72 kgで軽量化量がゼロ。完成パック質量は未確定。',pt=23,max_h=37,tag='materials-result-design')
    # Discussion follows both empirical panels; no duplicate overview diagram.
    p.section(15,540,564,'4　文献と結果を接続した考察')
    p.sub(X1,563,CW,'配送計画：役割分担と計画更新')
    p.text(X1,579,CW,'実行可能解の状態準備[1]と古典探索内の量子部利用[6]を踏まえると、候補範囲・部分問題の規模を古典部で選ぶ構成が検討対象となる。今回の結果は、その選択が改善可能性を左右することを示唆する。',pt=23,max_h=54,tag='discussion-planning')
    p.sub(X2,563,CW,'電池材料：評価情報と設計選択')
    p.text(X2,579,CW,'文献[2,7]は電圧・イオン移動・安定性の評価と必要量子ビット・ゲート数を扱う。計算資源の改善が配送に寄与するには、配送要求に対応する評価対象を選び、その情報が試験・実用設計で採用される必要がある。',pt=23,max_h=54,tag='discussion-materials')
    # Native conceptual strips, explicitly distinguished from current experiments.
    for x,color,nodes in [(X1,BLUE,['古典：部分問題選択','量子：候補生成','古典：検証・統合']),
                           (X2,ORANGE,['量子材料評価','試験・電池設計','軽量化／容量増加'])]:
        for i,label in enumerate(nodes):
            xx=x+i*94
            p.rect(xx,635,87,22,fill=PALE,stroke=color)
            p.text(xx+2,641,83,label,pt=20,bold=True,align='center',max_h=14,tag='proposed-architecture')
            if i<2:p.arrow(xx+88,646,xx+93,646,color)
    p.text(X1,663,CW,'構成案（未検証）：前処理・待機・計算・検証・統合の総時間を、計画更新に使える時間と比較する。',pt=22,color=MUTED,max_h=30,tag='planning-implication')
    p.text(X2,663,CW,'構成案（未検証）：今回計算した容量固定の軽量化と、容量増加による航続・充電条件の変更を区別する。',pt=22,color=MUTED,max_h=30,tag='materials-implication')
    p.line(15,704,579,704,NAVY,1)
    p.text(15,711,564,'適用範囲　実施したのは保存解の比較、材料参照値の換算、固定速度での電力量計算。動的再計画、量子実機の速度優位、量子計算による材料改善は未実証。',pt=21,color=MUTED,max_h=27,tag='scope')
    # Compact references, with DOI links on every entry in the editable PPTX.
    p.text(15,746,564,'主な参考文献',pt=23,bold=True,color=NAVY,max_h=12,tag='references-title')
    refs=[
      ('[1] Bärtschi & Eidenbenz (2020). Grover Mixers for QAOA. IEEE QCE, 72–82.','https://doi.org/10.1109/QCE49297.2020.00020'),
      ('[2] Delgado et al. (2022). Phys. Rev. A 106, 032428.','https://doi.org/10.1103/PhysRevA.106.032428'),
      ('[3] Stilgoe, Owen & Macnaghten (2013). Research Policy 42, 1568–1580.','https://doi.org/10.1016/j.respol.2013.05.008'),
      ('[4] Geels (2004). Research Policy 33, 897–920.','https://doi.org/10.1016/j.respol.2004.01.015'),
      ('[5] Chen et al. (2020). Nature Communications 11, 3411.','https://doi.org/10.1038/s41467-020-17126-3'),
      ('[6] Holliday et al. (2026). Quantum Machine Intelligence 8, 37.','https://doi.org/10.1007/s42484-026-00375-8'),
      ('[7] Shokrian Zini et al. (2023). Quantum 7, 1049.','https://doi.org/10.22331/q-2023-07-10-1049')]
    for i,(s,url) in enumerate(refs):
        col=0 if i<4 else 1;row=i if i<4 else i-4
        xx=X1 if col==0 else X2;yy=760+16*row
        p.text(xx,yy,CW,s,pt=18,color=MUTED,max_h=15,tag=f'reference-{i+1}')
        shape=p.slide.shapes[-1]
        for para in shape.text_frame.paragraphs:
            for run in para.runs:run.hyperlink.address=url
        p.pdf.linkURL(url,(xx*MM,(H-yy-15)*MM,(xx+CW)*MM,(H-yy)*MM),relative=0)
    p.text(X2,811,CW,'材料値[5]は古典DFT・電極試験の参照例。文献の知見、今回の計算、将来の構成案を区別する。',pt=18,color=MUTED,max_h=18,tag='reference-scope')
    sources=(OUT/'a1_academic_poster_references_20261103.txt').read_text()
    appendix=(OUT/'a1_academic_poster_quantum_systems_20261103_references_addendum.txt').read_text()
    notes='A1縦・本文、表、棒グラフ、構成図をPowerPointの文字・図形で作成。\n今回の作業は保存結果の比較・組版。新たな量子実験や動的実験は実施していない。\n\n'+sources+'\n'+appendix
    p.save(notes)
    prs=Presentation(OUT/f'{STEM}.pptx')
    assert len(prs.slides)==1 and prs.slide_width==Mm(594) and prs.slide_height==Mm(841)
    pictures=[s for s in prs.slides[0].shapes if s.shape_type==13]
    assert not pictures,'Poster must be native editable text/shapes, not a single image'
    with ZipFile(OUT/f'{STEM}.pptx') as z:assert z.testzip() is None
    audit={'format':'A1 portrait 594x841 mm','pptx_shapes':len(prs.slides[0].shapes),'raster_pictures':len(pictures),
           'body_font_pt':24,'discussion_font_pt':23,'caption_font_pt':20,'reference_font_pt':18,
           'results_rows':data,'mass_energy_reduction_percent':rates,
           'source_files':['review_outputs/no_sumo_full_analysis_20261102/run01/B_SUMMARY_BY_SCALE_AND_METHOD.csv',
                           'review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_PAIRED_DIFFERENCES.csv',
                           'review_outputs/thesis_results_interpretation_20261102/run01/04_THESIS_METHODS_DRAFT.md',
                           'review_outputs/thesis_results_interpretation_20261102/run01/05_THESIS_RESULTS_DRAFT.md']}
    (OUT/f'{STEM}_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=='__main__':build()
