import os,subprocess,shutil,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=R/'tools/lo_root';out=R/'render/pptx';out.mkdir(exist_ok=True)
shutil.copy2(R/'poster.pdf',R/'render/layout_reference.pdf')
e=os.environ.copy();e.update(LD_LIBRARY_PATH=str(r/'usr/lib/libreoffice/program')+':'+str(r/'usr/lib/x86_64-linux-gnu'),LD_PRELOAD=str(R/'tools/set_langtag.so'),THESIS_LANGTAG_DATADIR=str(r/'usr/share/liblangtag'),SAL_USE_VCLPLUGIN='svp')
c=[str(r/'usr/lib/libreoffice/program/soffice'),'-env:UserInstallation='+(R/'tools/profile').as_uri(),'--headless','--convert-to','pdf','--outdir',str(out),str(R/'poster.pptx')]
x=subprocess.run(c,env=e,capture_output=True,text=True,timeout=100)
(R/'render/RENDER_LOG.txt').write_text(x.stdout+'\n'+x.stderr)
if x.returncode or not (out/'poster.pdf').exists():raise RuntimeError(x.stdout+x.stderr)
shutil.copy2(out/'poster.pdf',R/'poster.pdf')
subprocess.run(['pdftotext','-layout',str(R/'poster.pdf'),str(R/'render/actual_render_text.txt')],check=True)
subprocess.run(['pdftoppm','-scale-to','2200','-singlefile','-png',str(R/'poster.pdf'),str(R/'poster_preview')],check=True)
print(x.stdout)
