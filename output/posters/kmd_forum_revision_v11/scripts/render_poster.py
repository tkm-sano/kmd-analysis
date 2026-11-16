from pathlib import Path
import os,subprocess,json

O=Path(__file__).resolve().parents[1]
ROOT=O.parents[2]
STEM='v11_KMD_Forum_量子技術と物流配送計画_A1縦_言語改訂'
T=ROOT/'review_outputs/poster_causal_structure_revision_20261105/run10/tools'
L=T/'lo_root'
env=os.environ.copy()
env.update(LD_LIBRARY_PATH=str(L/'usr/lib/libreoffice/program')+':'+str(L/'usr/lib/x86_64-linux-gnu'),
           LD_PRELOAD=str(ROOT/'review_outputs/poster_causal_structure_revision_20261105/run08/tools/set_langtag.so'),
           THESIS_LANGTAG_DATADIR=str(L/'usr/share/liblangtag'),SAL_USE_VCLPLUGIN='svp')
fontcfg=O/'render/fonts.conf'
fontcfg.write_text(f'''<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig><dir>{ROOT/'output/slides/sato_revision_20261105/fonts'}</dir>
<dir>/usr/share/fonts</dir><cachedir>{O/'render/fontcache'}</cachedir></fontconfig>''')
env['FONTCONFIG_FILE']=str(fontcfg)
cmd=[str(L/'usr/lib/libreoffice/program/soffice'),'-env:UserInstallation='+(O/'render/profile').as_uri(),
     '--headless','--convert-to','pdf:impress_pdf_Export','--outdir',str(O),str(O/f'{STEM}.pptx')]
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=100)
(O/'render/RENDER_LOG.txt').write_text(r.stdout+'\n'+r.stderr)
if r.returncode or not (O/f'{STEM}.pdf').exists():raise RuntimeError(r.stdout+r.stderr)
subprocess.run(['pdftotext','-layout',str(O/f'{STEM}.pdf'),str(O/'render/RENDERED_TEXT.txt')],check=True)
subprocess.run(['pdftoppm','-scale-to','2400','-singlefile','-png',str(O/f'{STEM}.pdf'),str(O/'poster_preview')],check=True)
print(r.stdout)
