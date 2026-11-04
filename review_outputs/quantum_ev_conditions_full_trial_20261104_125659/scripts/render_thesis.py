from pathlib import Path
import os,sys,json,subprocess,time,hashlib
O=Path(__file__).resolve().parents[1];R=O.parents[1];dest=O/'render_final';dest.mkdir(exist_ok=True)
tool=R/'review_outputs/thesis_docx_integration_20261103/run01/rendering_tools';root=tool/'root';env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(root/'usr/lib/libreoffice/program')+':'+str(root/'usr/lib/x86_64-linux-gnu'),LD_PRELOAD=str(tool/'set_langtag.so'),THESIS_LANGTAG_DATADIR=str(root/'usr/share/liblangtag'),SAL_USE_VCLPLUGIN='svp',TMPDIR=str(O/'logs'),XDG_CACHE_HOME=str(O/'logs/cache'),XDG_CONFIG_HOME=str(O/'logs/config'))
cmd=[str(root/'usr/lib/libreoffice/program/soffice'),'-env:UserInstallation='+(O/'render_final/profile').as_uri(),'--headless','--convert-to','pdf','--outdir',str(dest),str(O/'THESIS_TRIAL.docx')];t=time.monotonic()
with (dest/'render_stdout.txt').open('w') as out,(dest/'render_stderr.txt').open('w') as err:r=subprocess.run(cmd,env=env,stdout=out,stderr=err,timeout=120)
assert r.returncode==0
pdf=dest/'THESIS_TRIAL.pdf';assert pdf.is_file();subprocess.run(['pdftotext','-layout',str(pdf),str(dest/'TEXT.txt')],check=True)
sys.path.insert(0,str(tool/'python'));import fitz
from PIL import Image,ImageDraw
z=fitz.open(pdf);pages=[];thumbs=[]
for i,p in enumerate(z):
 pix=p.get_pixmap(matrix=fitz.Matrix(1.05,1.05));path=dest/f'page_{i+1:03d}.png';pix.save(str(path));text=p.get_text();pages.append({'page':i+1,'characters':len(text),'replacement_characters':text.count('\ufffd'),'width_pt':p.rect.width,'height_pt':p.rect.height,'image':str(path.relative_to(O))});im=Image.open(path).convert('RGB');im.thumbnail((380,540));thumbs.append(im.copy())
for off in range(0,len(thumbs),8):
 ims=thumbs[off:off+8];canvas=Image.new('RGB',(4*400,2*585),'#dddddd');draw=ImageDraw.Draw(canvas)
 for k,im in enumerate(ims):
  x=(k%4)*400+10;y=(k//4)*585+25;canvas.paste(im,(x,y));draw.text((x,y-20),f'Page {off+k+1}',fill='black')
 canvas.save(dest/f'contact_{off//8+1:02d}.png')
summary={'pages':len(z),'wall_s':time.monotonic()-t,'returncode':r.returncode,'renderer':'reused read-only LibreOffice24.2.7.2 binary; new profile/cache entirely inside trial','command':cmd,'pdf_sha256':hashlib.file_digest(pdf.open('rb'),'sha256').hexdigest(),'Word_native_status':'HOLD_NOT_AVAILABLE'}
(dest/'RENDER_RUN.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));(dest/'PAGE_AUDIT.json').write_text(json.dumps(pages,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
