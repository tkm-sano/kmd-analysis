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
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1]
STEM = 'poster'
MM = 72 / 25.4
W, H = 594, 841
NAVY, BLUE, ORANGE = '#16354B', '#246C94', '#A75A36'
INK, MUTED, RULE, PALE = '#20313F', '#506575', '#CBD7E0', '#EFF4F7'
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
                    # Keep numeric/Latin tokens intact whenever possible.
                    import re
                    tail=re.search(r'[A-Za-z0-9][A-Za-z0-9.,_/-]*$',line) if ch.isascii() and (ch.isalnum() or ch in '.,_/-') else None
                    if tail and tail.start()>0:
                        result.append(line[:tail.start()].rstrip())
                        line=tail.group()+ch
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

    def rect(self, x, y, w, h, fill=None, stroke=None, stroke_pt=0.55, radius=0):
        self.pdf.setLineWidth(stroke_pt)
        if fill: self.pdf.setFillColor(HexColor(fill))
        if stroke: self.pdf.setStrokeColor(HexColor(stroke))
        if radius:
            self.pdf.roundRect(x*MM,(H-y-h)*MM,w*MM,h*MM,radius*MM,fill=int(fill is not None),stroke=int(stroke is not None))
        else:
            self.pdf.rect(x*MM,(H-y-h)*MM,w*MM,h*MM,fill=int(fill is not None),stroke=int(stroke is not None))
        shape = self.slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Mm(x), Mm(y), Mm(w), Mm(h))
        if radius: shape.adjustments[0]=radius/min(w,h)
        from pptx.oxml.xmlchemy import OxmlElement
        shape._element.spPr.append(OxmlElement('a:effectLst'))
        from pptx.oxml.ns import qn
        style=shape._element.find(qn('p:style'))
        if style is not None: shape._element.remove(style)
        if fill:
            shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string(fill[1:])
        else: shape.fill.background()
        if stroke:
            shape.line.color.rgb = RGBColor.from_string(stroke[1:]); shape.line.width = Pt(stroke_pt)
        else: shape.line.fill.background()
        return shape

    def line(self, x1, y1, x2, y2, color=RULE, pt=0.7):
        self.pdf.setStrokeColor(HexColor(color)); self.pdf.setLineWidth(pt)
        self.pdf.line(x1*MM, (H-y1)*MM, x2*MM, (H-y2)*MM)
        s = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Mm(x1), Mm(y1), Mm(x2), Mm(y2))
        s.line.color.rgb = RGBColor.from_string(color[1:]); s.line.width = Pt(pt)
        from pptx.oxml.xmlchemy import OxmlElement
        from pptx.oxml.ns import qn
        s._element.spPr.append(OxmlElement('a:effectLst'))
        style=s._element.find(qn('p:style'))
        if style is not None:s._element.remove(style)

    def arrow(self, x1, y1, x2, y2, color=MUTED):
        self.line(x1,y1,x2,y2,color,1)
        a = math.atan2(y2-y1,x2-x1)
        for da in (-0.5,0.5):
            self.line(x2,y2,x2-2.5*math.cos(a+da),y2-2.5*math.sin(a+da),color,1)

    def text(self, x, y, w, s, pt=24, bold=False, color=INK, lh=None, align='left', max_h=None, tag='', host_shape=None):
        lh = lh or pt / MM * 1.27
        lines = wrap(s, w * (.88 if w > 100 else 1), pt, bold)
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
        box=host_shape if host_shape is not None else self.slide.shapes.add_textbox(Mm(x),Mm(y),Mm(w),Mm(h+.5))
        box.name=tag or s[:32]
        tf=box.text_frame;tf.clear();tf.word_wrap=True;tf.auto_size=MSO_AUTO_SIZE.NONE
        tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
        if host_shape is not None:
            tf.margin_left=Mm(x)-box.left
            tf.margin_top=Mm(y)-box.top
            tf.margin_right=box.left+box.width-Mm(x+w)
            tf.margin_bottom=Mm(1)
        tf.vertical_anchor=MSO_ANCHOR.TOP
        for i,line in enumerate(s.split('\n')):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
            p.line_spacing=Pt(lh*MM);p.space_before=p.space_after=Pt(0)
            if True:
                from pptx.enum.text import PP_ALIGN
                p.alignment=PP_ALIGN.CENTER if align=='center' else PP_ALIGN.RIGHT if align=='right' else PP_ALIGN.LEFT
            for f,t in runs(line,bold):
                r=p.add_run();r.text=t;r.font.size=Pt(pt);r.font.bold=bold
                r.font.name='Droid Sans Fallback' if f=='CJK' else 'DejaVu Sans'
                r.font.color.rgb=RGBColor.from_string(color[1:])
                from pptx.oxml.xmlchemy import OxmlElement
                ea=OxmlElement('a:ea');ea.set('typeface',r.font.name);r._r.get_or_add_rPr().append(ea)
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
        from content import TITLE
        title=TITLE
        self.prs.core_properties.title=title;self.prs.core_properties.author='佐野巧馬 / Q/est'
        self.slide.notes_slide.notes_text_frame.text=notes
        self.prs.save(OUT/f'{STEM}.pptx')
        self.pdf.setTitle(title);self.pdf.setAuthor('佐野巧馬 / Q/est')
        self.pdf.showPage();self.pdf.save()
        (OUT/f'{STEM}_layout.json').write_text(json.dumps(self.blocks,ensure_ascii=False,indent=2))
        (OUT/f'{STEM}_text.txt').write_text('\n\n'.join(self.text_log))

