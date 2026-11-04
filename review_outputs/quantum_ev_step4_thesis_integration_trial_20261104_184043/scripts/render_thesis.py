from pathlib import Path
import os,sys,json,subprocess,time,re,hashlib
import pandas as pd
from docx import Document
from docx.oxml.ns import qn
O=Path(__file__).resolve().parents[1];R=O.parents[1];dest=O/'render';tool=R/'review_outputs/thesis_docx_integration_20261103/run01/rendering_tools';root=tool/'root';env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(root/'usr/lib/libreoffice/program')+':'+str(root/'usr/lib/x86_64-linux-gnu'),LD_PRELOAD=str(tool/'set_langtag.so'),THESIS_LANGTAG_DATADIR=str(root/'usr/share/liblangtag'),SAL_USE_VCLPLUGIN='svp',TMPDIR=str(O/'logs'),XDG_CACHE_HOME=str(O/'logs/cache'),XDG_CONFIG_HOME=str(O/'logs/config'))
sys.path.insert(0,str(tool/'python'));import fitz
from PIL import Image,ImageDraw
word=O/'THESIS_STEP4_INTEGRATED_TRIAL.docx';pdf=word.with_suffix('.pdf');cmd=[str(root/'usr/lib/libreoffice/program/soffice'),'-env:UserInstallation='+(dest/'profile').as_uri(),'--headless','--convert-to','pdf','--outdir',str(O),str(word)];t=time.perf_counter()
def convert(tag):
 with (dest/(tag+'_stdout.txt')).open('w') as out,(dest/(tag+'_stderr.txt')).open('w') as err:r=subprocess.run(cmd,env=env,stdout=out,stderr=err,timeout=120)
 assert r.returncode==0 and pdf.is_file(),r.returncode
norm=lambda s:re.sub(r'\s','',s)
def mapping():
 z=fitz.open(pdf);entries=pd.read_csv(O/'evidence/TOC_ENTRIES.csv');out=[]
 for x in entries.to_dict('records'):
  targets=[i+1 for i,p in enumerate(z) if i>=3 and any(norm(line)==norm(x['title']) for line in p.get_text().splitlines())];assert targets,(x['title'],'heading not found');out.append(dict(**x,page=targets[0]))
 z.close();return out
convert('pass1');maps=mapping();d=Document(word)
for x in maps:
 ps=[p for p in d.paragraphs if p._p.xpath('.//w:bookmarkStart[@w:name="toc_'+x['bookmark']+'"]')];assert len(ps)==1
 p=ps[0]
 # Preserve bookmark elements, replace text runs only.
 for el in list(p._p):
  if el.tag not in [qn('w:pPr'),qn('w:bookmarkStart'),qn('w:bookmarkEnd')]:p._p.remove(el)
 p.add_run(x['title']+'　……　'+str(x['page']))
d.save(word);convert('pass2');finalmaps=mapping();assert [x['page'] for x in maps]==[x['page'] for x in finalmaps],'TOC changed after update'
pd.DataFrame(finalmaps).to_csv(O/'render/TOC_PAGE_MAP.csv',index=False)
# Export final text after TOC update in DOCX order, including equations and tables.
from lxml import etree
lines=[]
for el in d._element.body:
 typ=etree.QName(el).localname
 if typ=='p':
  text=''.join(el.xpath('.//w:t/text() | .//m:t/text()'));style=el.xpath('./w:pPr/w:pStyle/@w:val');lev={'Heading1':'# ','Heading2':'## ','Heading3':'### '}.get(style[0] if style else '','');lines.append(lev+text)
 elif typ=='tbl':
  for row in el.findall(qn('w:tr')):lines.append(' | '.join(''.join(tc.xpath('.//w:t/text() | .//m:t/text()')) for tc in row.findall(qn('w:tc'))))
(O/'THESIS_FULL_TEXT.md').write_text('\n\n'.join(lines)+'\n')
z=fitz.open(pdf);pages=[];thumbs=[];outside=[]
for i,p in enumerate(z):
 pix=p.get_pixmap(matrix=fitz.Matrix(.95,.95));path=dest/f'page_{i+1:03d}.png';pix.save(str(path));text=p.get_text();pages.append(dict(page=i+1,characters=len(text),replacement_characters=text.count('\ufffd'),image=str(path.relative_to(O)),width_pt=p.rect.width,height_pt=p.rect.height))
 for b in p.get_text('blocks'):
  if b[0]<-1 or b[1]<-1 or b[2]>p.rect.width+1 or b[3]>p.rect.height+1:outside.append(dict(page=i+1,bbox=list(b[:4]),text=str(b[4])[:160]))
 im=Image.open(path).convert('RGB');im.thumbnail((285,405));thumbs.append(im.copy())
for off in range(0,len(thumbs),12):
 ims=thumbs[off:off+12];canvas=Image.new('RGB',(1200,1290),'#dddddd');draw=ImageDraw.Draw(canvas)
 for k,im in enumerate(ims):
  x=k%4*300+7;y=k//4*430+22;canvas.paste(im,(x,y));draw.text((x,y-18),f'Page {off+k+1}',fill='black')
 canvas.save(dest/f'contact_{off//12+1:02d}.png')
(dest/'PAGE_AUDIT.json').write_text(json.dumps(pages,indent=2));(dest/'OUTSIDE_PAGE_BLOCKS.json').write_text(json.dumps(outside,ensure_ascii=False,indent=2));(dest/'TEXT.txt').write_text('\n\f\n'.join(p.get_text() for p in z))
run=dict(pages=len(z),wall_s=time.perf_counter()-t,renderer='read-only LibreOffice 24.2.7.2; unique trial profile/cache',command=cmd,TOC_pages_checked=True,Word_native='HOLD_NOT_AVAILABLE',outside_page_blocks=len(outside),PDF_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest());(dest/'RENDER_RUN.json').write_text(json.dumps(run,ensure_ascii=False,indent=2));print(json.dumps(run,ensure_ascii=False,indent=2))
