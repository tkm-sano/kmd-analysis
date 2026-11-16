"""Editable PPTX and matching PDF: white, black, Japanese Mincho only."""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from fontTools.ttLib import TTFont as Font
from fontTools.varLib.instancer import instantiateVariableFont
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image,ImageChops
import fitz

ROOT=Path(__file__).resolve().parent
W,H=1280,720
FONT='Noto Serif JP'
STEM='大田区ToC配送_RQ_仮説_比較_予期される結果_明朝モノクロ'
SOURCES=[
 Path('research_plan_toc_three_objectives_faceted_20261108.docx'),
 Path('docs/research/A_TO_D_PIPELINE_FINAL_REPORT.md'),
 Path('docs/research/A_TO_D_COMPARISON.csv'),
 Path('docs/research/COMMON_CONSTRAINT_AUDIT.md'),
 Path('docs/research/toc_delivery_a/A_JAPAN_POST_T_CORROBORATION.md'),
 Path('configs/toc_delivery/common_conditions_v1_1.json'),
 Path('configs/toc_delivery/a_human_route_time_reference_v1.json'),
]
source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}

def prepare_font():
 variable=ROOT/'assets/NotoSerifJP-Variable.ttf'
 for suffix,weight in [('Regular',400),('SemiBold',600)]:
  p=ROOT/f'assets/NotoSerifJP-{suffix}.ttf'
  if not p.exists():
   f=Font(variable);f=instantiateVariableFont(f,{'wght':weight},inplace=True)
   for platform,encoding,lang in [(3,1,0x409),(1,0,0)]:
    for k,v in {1:FONT,2:suffix,4:FONT+' '+suffix,6:'NotoSerifJP-'+suffix}.items():
     f['name'].setName(v,k,platform,encoding,lang)
   f.save(p)
  pdfmetrics.registerFont(TTFont('Mincho'+suffix,str(p)))
 return {False:'MinchoRegular',True:'MinchoSemiBold'}

FN=prepare_font()
slides=[]

def width(text,size,bold=False):return pdfmetrics.stringWidth(text,FN[bold],size)
def wrap(text,limit,size,bold=False):
 lines=[]
 for original in text.split('\n'):
  line=''
  for ch in original:
   if line and width(line+ch,size,bold)>limit:
    if ch in '、。，．：；？！）］】」』〉》':
     tail=line[-1];line=line[:-1];lines.append(line);line=tail+ch
    else:lines.append(line);line=ch
   else:line+=ch
  lines.append(line)
 return lines

def add_text(s,text,x,y,w,h,size=28,bold=False,leading=None,align='left',role='body'):
 lines=wrap(text,w,size,bold);leading=leading or size*1.5
 needed=size+(len(lines)-1)*leading
 if needed>h+0.5:raise ValueError(f'Text overflow slide{s["number"]} {role}: {needed}>{h}: {text}')
 s['elements'].append(dict(kind='text',text=text,lines=lines,x=x,y=y,w=w,h=h,size=size,bold=bold,leading=leading,align=align,role=role))

def line(s,x1,y1,x2,y2,weight=1):s['elements'].append(dict(kind='line',x=x1,y=y1,x2=x2,y2=y2,weight=weight))
def rect(s,x,y,w,h,weight=1):s['elements'].append(dict(kind='rect',x=x,y=y,w=w,h=h,weight=weight))
def slide(title,source,note):
 n=len(slides)+1;s={'number':n,'title':title,'elements':[],'notes':note};slides.append(s)
 add_text(s,'慶應義塾大学KMD 修士研究｜大田区ToC配送',64,25,1100,28,16,role='running_header')
 add_text(s,title,64,76,1152,61,42,True,role='title')
 line(s,64,149,1216,149,1.2)
 line(s,64,656,1216,656,0.8)
 add_text(s,source,64,673,1080,23,13,role='source')
 add_text(s,f'{n:02d} / 05',1130,673,86,23,14,align='right',role='page')
 return s

def table(s,x,y,widths,headers,rows,heights,size=24):
 total=sum(widths);rect(s,x,y,total,sum(heights),0.9)
 xx=x
 for v in widths[:-1]:xx+=v;line(s,xx,y,xx,y+sum(heights),0.65)
 yy=y
 for i,(cells,height) in enumerate(zip([headers]+rows,heights)):
  if i:line(s,x,yy,x+total,yy,0.65)
  xx=x
  for j,(text,cw) in enumerate(zip(cells,widths)):
   add_text(s,str(text),xx+16,yy+13,cw-32,height-19,size if i else size-1,i==0,leading=size*1.36,role=f'table[{i},{j}]')
   xx+=cw
  yy+=height

note='RQは2026-11-08の研究計画の問いを、現行のA定義とDの実装範囲に合わせて要約。共通条件v1.1と最新の11月12日統合報告、11月13日人手T参照を併用する。旧EV・電池・エネルギー仮説は新研究に転用しない。'
s=slide('RQ｜同じ配送条件で、何が変わるか','基準：共通条件v1.1・凍結需要v1。研究用の仮定条件であり、事業者の実績再現ではない。',note)
add_text(s,'京浜トラックターミナルを起点とする大田区内のToC配送で、\n量子・古典ハイブリッドは、規則ベース推計・従来型手法・\n古典最適化に対して、総走行距離・積込待機・計画作成時間に\nどのような性能差とトレードオフを示すか。',64,195,1152,244,31,leading=51)
add_text(s,'同一需要・同一道路OD・同一の運行制約で評価する。',64,455,1152,45,27,True)
for i,(label,detail) in enumerate([('D','全車両・全便の総走行距離［km］'),('W','積込待機時間の合計［分］'),('T','計画作成に要する経過時間［秒］')]):
 x=64+i*394
 add_text(s,label,x,533,350,42,32,True)
 add_text(s,detail,x,585,365,35,21)

s=slide('比較｜A〜Dの計画作成方法','Aは佐川急便の公開業務を参考にした推計。DはQiskitによるAOAシミュレーションを使用。',
 'A1=地理区域と角度順、A2=区域境界調整と最近隣、A3=限定車両間移動と訪問順改善。既存固定条件を維持。BはVeRyPyの節約量を再利用する有向CW派生で、元の対称版をそのまま実行したものではない。Cも大域最適性を証明していない。Dは有限fragment順列と日列カレンダーの範囲。')
table(s,64,184,[148,496,508],['条件','計画作成方法','研究上の位置付け'],[
 ['A1〜A3','区域・近隣・負荷調整による規則','従来業務を参考にした推計。\n人手Tは別出典による工程推計。'],
 ['B','有向Clarke–Wright節約法\n＋共通古典完成器','VeRyPyの節約量計算を再利用。\n割当・積込計画まで完成させる。'],
 ['C','OR-Tools Routing\n＋CP-SAT','経路と物理車両・2便・積込を連携。\n最適性証明の有無を区別する。'],
 ['D','列生成＋AOA\n＋古典完成器','S1では限定マクロ候補領域。\n量子候補の追加価値を別に検査。'],
],[52,87,87,87,87],23)
add_text(s,'全手法で車両割当と訪問順を決定し、同じ独立制約検査器を使う。',64,607,1152,35,23,True)

s=slide('比較｜共通条件とD・W・Tの測り方','共通条件v1.1。第1便readyは8〜9時に固定、第2便readyは第1便の実帰着時刻。',
 '時刻は秒。第一便ready=28800+floor(3600*(v+0.5)/V)。W=Σ(load_start-ready)/60で、積込1800秒を含まない。全需要ちょうど一度、容量、最大2便、勤務、バース排他を検査。両方向ε制約法。T_programは共通入力読込開始から最終共通検査完了、OD事前生成と実験後追加監査は別。人手Tの下位工程参照を全体Tと混同しない。')
table(s,64,184,[130,145,145,132],['規模','配送先','車両','バース'],[
 ['S1','1,000','10','2'],['S2','2,000','20','4'],['S3','4,000','40','8'],
],[49,49,49,49],24)
add_text(s,'最大2便・容量60単位／便\n積込1,800秒・顧客作業120秒\n帰着後準備0秒・勤務8:00〜20:00\n顧客時間窓なし・有向道路OD',64,417,553,173,23,leading=40)
add_text(s,'D：拠点往復を含む全便の距離合計［km］\nW：積込開始−準備完了の総和［分］',662,186,554,106,23,leading=42)
line(s,662,302,1216,302,0.7)
add_text(s,'T_program：入力読込〜最終制約検査\nA〜Dでwall-clock実測値を比較する。\n\nT_human：Aの人手工程を別に推計\nルート作成の参照値と全体Tを区別する。',662,322,554,220,22,leading=35)
add_text(s,'両方向ε制約法で、対応する可行計画を比較。',662,587,554,36,21,True)

s=slide('予期される結果｜選択条件と適用限界を得る','ここに示すのは成果の形式。性能改善や量子優位を保証する予測ではない。',
 '予期される結果と取得済み結果は別スライド。量子寄与ゼロ、D/W競合なし、古典が優れる場合も有効な知見とする。実行不能は未取得として分母に保持する。T_humanとT_programの単純な実測速度比は未成立。')
columns=[
 ('距離と待機の関係','距離が短い候補と\n待機が少ない候補を、\n対応する計画ごとに示す。','競合しない場合も報告する。'),
 ('計画時間の内訳','経路生成・調整・検査の\nどこに時間を使うかを示す。\nAの人手推計は別に扱う。','規模・資源・予算を併記する。'),
 ('量子候補の追加価値','同じ古典対照との差を示す。\n改善がなければ寄与0とし、\n探索領域の限界を明示する。','古典完成による改善を分ける。'),
]
for i,(head,body,sub) in enumerate(columns):
 x=64+i*394
 add_text(s,head,x,195,364,48,27,True)
 line(s,x,252,x+364,252,0.8)
 add_text(s,body,x,278,364,168,25,leading=44)
 add_text(s,sub,x,475,364,45,21)
rect(s,64,561,1152,60,1)
add_text(s,'成果：指標別の選択条件と、各手法を適用できる範囲を明確にする。',84,575,1112,40,25,True)

data=list(csv.DictReader(Path('docs/research/A_TO_D_COMPARISON.csv').open()))
s1=[r for r in data if r['scenario']=='S1']
a=[r for r in s1 if r['method'].startswith('A') and r['status']=='FEASIBLE' and r['is_replicate']=='False']
def interval(key):
 vals=[float(r[key]) for r in a];return f'{min(vals):.2f}〜{max(vals):.2f}'
measure=[['A：可行6条件',interval('D_km'),interval('W_min'),interval('T_program_s')]]
for method in ['B','C','D']:
 r=next(r for r in s1 if r['condition']==method+'_primaryD_epsW_1')
 measure.append([method,*[f'{float(r[k]):.2f}' for k in ['D_km','W_min','T_program_s']]])
s=slide('参考｜取得済みS1結果と残る検証','出典：2026-11-12統合比較CSV／2026-11-13人手T参照。予期される結果とは分けて提示。',
 '数値はdocs/research/A_TO_D_COMPARISON.csvから読込。S1=1000先/10台/2バース、W≤422.45分の最初の共通ε。Aは9条件中6可行で、A1の3条件は勤務超過。AのD/W各最小・最大は同じ計画とは限らない。表のTは全てプログラムwall時間。Dの量子候補最終採用0本、主目的改善0。人手Tの参照は日本郵便/Loogia2021年、https://loogia.jp/cases/nihonyubin/ 。作成単位の規模・便・人数対応が未確定で全体Tは未校正。')
table(s,64,184,[246,300,300,306],['手法','D［km］','W［分］','T_program［秒］'],measure,[52,60,60,60,60],25)
add_text(s,'共通ε：W ≤ 422.45分。Aの範囲の端点は、同一計画とは限らない。',64,505,1152,37,21)
add_text(s,'現状：S1比較は条件付きで成立。量子由来の追加改善は未確認。',64,559,1152,42,25,True)
add_text(s,'Aの人手参照：熟練5〜10分／新人30〜60分（作成工程のみ）。全体Tは未確定。',64,611,1152,30,19)

def render_pdf():
 p=ROOT/(STEM+'.pdf');c=canvas.Canvas(str(p),pagesize=(W,H),initialFontName=FN[False],initialFontSize=16)
 c.setTitle('大田区ToC配送：RQ・仮説・比較・予期される結果');c.setAuthor('KMD 修士研究資料')
 for s in slides:
  c.setFillColorRGB(1,1,1);c.rect(0,0,W,H,stroke=0,fill=1)
  c.setFillColorRGB(0,0,0);c.setStrokeColorRGB(0,0,0)
  for e in s['elements']:
   if e['kind']=='line':
    c.setLineWidth(e['weight']);c.line(e['x'],H-e['y'],e['x2'],H-e['y2'])
   elif e['kind']=='rect':
    c.setLineWidth(e['weight']);c.rect(e['x'],H-e['y']-e['h'],e['w'],e['h'],stroke=1,fill=0)
   else:
    c.setFont(FN[e['bold']],e['size'])
    for i,t in enumerate(e['lines']):
     yy=H-e['y']-e['size']*.91-i*e['leading']
     if e['align']=='right':c.drawRightString(e['x']+e['w'],yy,t)
     else:c.drawString(e['x'],yy,t)
  c.showPage()
 c.save();return p

def render_pptx():
 prs=Presentation();prs.slide_width=Inches(13.333333);prs.slide_height=Inches(7.5)
 def u(v):return Inches(v/96)
 for s in slides:
  sl=prs.slides.add_slide(prs.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=RGBColor(255,255,255)
  for e in s['elements']:
   if e['kind']=='line':
    sh=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,u(e['x']),u(e['y']),u(e['x2']),u(e['y2']));sh.line.color.rgb=RGBColor(0,0,0);sh.line.width=Pt(e['weight']*.75)
   elif e['kind']=='rect':
    sh=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,u(e['x']),u(e['y']),u(e['w']),u(e['h']));sh.fill.background();sh.line.color.rgb=RGBColor(0,0,0);sh.line.width=Pt(e['weight']*.75)
   else:
    # Separate text frames for each prewrapped line keep editable line positions.
    for i,t in enumerate(e['lines']):
     sh=sl.shapes.add_textbox(u(e['x']),u(e['y']+i*e['leading']),u(e['w']),u(e['size']*1.5))
     tf=sh.text_frame;tf.clear();tf.word_wrap=False;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.vertical_anchor=MSO_ANCHOR.TOP
     p=tf.paragraphs[0];p.space_before=p.space_after=Pt(0);p.line_spacing=Pt(e['leading']*.75)
     if e['align']=='right':
      from pptx.enum.text import PP_ALIGN
      p.alignment=PP_ALIGN.RIGHT
     run=p.add_run();run.text=t;run.font.name=FONT;run.font.size=Pt(e['size']*.75);run.font.bold=e['bold'];run.font.color.rgb=RGBColor(0,0,0)
     rp=run._r.get_or_add_rPr()
     for tag in ['ea','cs']:
      el=OxmlElement('a:'+tag);el.set('typeface',FONT);rp.append(el)
  sl.notes_slide.notes_text_frame.text=s['notes']
 p=ROOT/(STEM+'.pptx');prs.save(p)
 # Use the requested typeface and pure black/white even for inherited theme slots.
 with zipfile.ZipFile(p) as z:parts={name:z.read(name) for name in z.namelist()}
 ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
 theme=ET.fromstring(parts['ppt/theme/theme1.xml'])
 for q in theme.findall('.//a:fontScheme//a:latin',ns)+theme.findall('.//a:fontScheme//a:ea',ns)+theme.findall('.//a:fontScheme//a:cs',ns):q.set('typeface',FONT)
 for slot in theme.findall('.//a:clrScheme/*',ns):
  for child in list(slot):slot.remove(child)
  color=ET.SubElement(slot,'{'+ns['a']+'}srgbClr')
  color.set('val','FFFFFF' if slot.tag.rsplit('}',1)[-1] in ['lt1','lt2'] else '000000')
 parts['ppt/theme/theme1.xml']=ET.tostring(theme,encoding='utf-8',xml_declaration=True)
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in parts.items():z.writestr(name,data)
 return p

def qa(pdf,pptx):
 checks=[]
 def check(v,label):checks.append({'check':label,'passed':bool(v)})
 doc=fitz.open(pdf);check(len(doc)==5,'PDF slide count5')
 montage=Image.new('RGB',(1600,900),'white');font_names=set();used=set()
 for i,page in enumerate(doc):
  pix=page.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False)
  p=ROOT/f'slide_{i+1:02d}.png';pix.save(p)
  im=Image.open(p).convert('RGB');r,g,b=im.split();check(ImageChops.difference(r,g).getbbox() is None and ImageChops.difference(g,b).getbbox() is None,f'grayscale only slide{i+1}')
  thumb=im.resize((533,300));montage.paste(thumb,((i%3)*533,(i//3)*450+65))
  text=page.get_text();check(len(text)>100,f'Japanese text extractable slide{i+1}')
  for f in page.get_fonts(full=True):font_names.add(f[3])
  for block in page.get_text('dict')['blocks']:
   for l in block.get('lines',[]):
    for span in l['spans']:
     if not span['text'].strip():continue
     check(span['color']==0,f'black text PDF slide{i+1}')
     x0,y0,x1,y1=span['bbox'];check(x0>=0 and y0>=0 and x1<=W+.5 and y1<=H+.5,f'no PDF clipping slide{i+1}')
 check(all('NotoSerifJP' in n.replace(' ','') for n in font_names),'PDF uses Mincho embedded font subsets only')
 with zipfile.ZipFile(pptx) as z:
  ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
  names=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)];check(len(names)==5,'PPTX slide count5')
  theme=ET.fromstring(z.read('ppt/theme/theme1.xml'))
  check(all(c.get('val') in ['000000','FFFFFF'] for c in theme.findall('.//a:clrScheme/*/a:srgbClr',ns)),'PPTX theme palette black/white only')
  for name in names:
   t=ET.fromstring(z.read(name))
   for rp in t.findall('.//a:rPr',ns):
    latin=rp.find('a:latin',ns);ea=rp.find('a:ea',ns);color=rp.find('a:solidFill/a:srgbClr',ns)
    check(latin is not None and latin.get('typeface')==FONT and ea is not None and ea.get('typeface')==FONT,'PPTX Mincho Latin/EastAsian:'+name)
    check(color is not None and color.get('val')=='000000','PPTX black text:'+name)
   bg=t.find('.//p:bgPr/a:solidFill/a:srgbClr',ns);check(bg is not None and bg.get('val')=='FFFFFF','PPTX white background:'+name)
 for s in slides:
  for e in s['elements']:
   if e['kind']=='text':
    used.update(''.join(e['lines']));check(e['x']>=0 and e['y']>=0 and e['x']+e['w']<=W and e['y']+e['h']<=H,'scene bounds')
 f=Font(ROOT/'assets/NotoSerifJP-Regular.ttf');cmap=f.getBestCmap();missing=sorted(ch for ch in used if not ch.isspace() and ord(ch) not in cmap)
 check(not missing,'no missing glyphs')
 for name,h in source_hashes.items():check(hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,'research source preserved:'+name)
 montage.save(ROOT/'preview_montage.png')
 result={'all_passed':all(c['passed'] for c in checks),'checks':len(checks),'results':checks,'pdf_fonts':sorted(font_names),'missing_glyphs':missing,
  'PPTX_rendering':'Native editable shapes generated from same scene. PDF pages visually rendered and checked; PowerPoint application rendering is not tested here.'}
 (ROOT/'VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if not result['all_passed']:raise ValueError([c for c in checks if not c['passed']])
 print('QA passed',len(checks),'checks',sorted(font_names))

pdf=render_pdf();pptx=render_pptx();qa(pdf,pptx)
(ROOT/'SLIDE_SCENES.json').write_text(json.dumps(slides,ensure_ascii=False,indent=2)+'\n')
(ROOT/'SOURCE_HASHES.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
content='# スライド内容と編集方針\n\n白背景・黒文字・明朝体（Noto Serif JP）、16:9、5枚。ユーザー提示の仮説原文が確認できるまで、仮説スライドは掲載しない。\n\n'
for s in slides:
 content+='## '+str(s['number'])+' '+s['title']+'\n\n'
 content+='\n\n'.join(e['text'] for e in s['elements'] if e['kind']=='text' and e['role'] not in ['running_header','page','source'])
 content+='\n\n発表者ノート：'+s['notes']+'\n\n'
(ROOT/'CONTENT.md').write_text(content)
(ROOT/'REPRODUCE.md').write_text('生成：専用venvのPythonでbuild_slides.pyを実行。python-pptx1.0.2／reportlab4.4.4／PyMuPDF1.26.5／fonttools4.60.1。\n\nPowerPointは編集可能。PDFは明朝フォントのサブセットを埋め込み、同じシーンから出力。PPTXを編集する端末にはassetsのNoto Serif JPを導入すると表示が安定する。フォントはSIL OFL、ライセンスはassets/OFL.txt。\n\nユーザーが提示していない仮説案H1〜H3を削除。提示原文を特定できていないため、仮説の掲載は保留。独自の仮説や旧研究の仮説で置き換えない。既存の研究計画・コード・凍結需要・実験結果は変更しない。新しい実験やcommit/pushは実施しない。\n')
print(pdf);print(pptx)
