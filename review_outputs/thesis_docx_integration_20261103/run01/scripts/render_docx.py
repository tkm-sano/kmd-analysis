from common import *
# Rendering package only; no scientific runner is invoked.
t=time.monotonic();run=sys.argv[1] if len(sys.argv)>1 else 'render01';dest=O/run;dest.mkdir(exist_ok=True);tool=O/'rendering_tools';root=tool/'root';env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(root/'usr/lib/libreoffice/program')+':'+str(root/'usr/lib/x86_64-linux-gnu'),LD_PRELOAD=str(tool/'set_langtag.so'),THESIS_LANGTAG_DATADIR=str(root/'usr/share/liblangtag'),SAL_USE_VCLPLUGIN='svp')
cmd=[str(root/'usr/lib/libreoffice/program/soffice'),'-env:UserInstallation='+str((tool/'profile').as_uri()),'--headless','--convert-to','pdf','--outdir',str(dest),str(OUT)]
with (dest/'RENDER.log').open('w') as a,(dest/'RENDER.stderr').open('w') as b:r=subprocess.run(cmd,env=env,stdout=a,stderr=b,timeout=180)
pdf=dest/(OUT.stem+'.pdf');assert pdf.is_file() and r.returncode==0,(r.returncode,(dest/'RENDER.stderr').read_text())
subprocess.run(['pdftotext','-layout',str(pdf),str(dest/'TEXT.txt')],check=True)
sys.path.insert(0,str(tool/'python'));import fitz
z=fitz.open(pdf);dump(run+'/RENDER_RUN.json',{'command':cmd,'renderer':'LibreOffice24.2.7.2 local extracted Ubuntu packages','pdf_sha256':sha(pdf),'DOCX_sha256':sha(OUT),'pages':len(z),'wall_s':time.monotonic()-t,'RSS_bytes':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024,'returncode':r.returncode});print((dest/'RENDER_RUN.json').read_text())
