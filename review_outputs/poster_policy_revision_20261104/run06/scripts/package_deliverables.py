from pathlib import Path
import sys,csv,json,hashlib,shutil,subprocess
from zipfile import ZipFile,ZIP_DEFLATED
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
r=Path(__file__).resolve().parents[1];d=fitz.open(r/'poster.pdf');mm=72/25.4
for name,box in [('footer',(10,487,831,593)),('material',(560,145,831,365)),('planning',(285,340,556,482))]:d[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=fitz.Rect(*[v*mm for v in box])).save(r/'render'/f'check_{name}.png')
shutil.copyfile(r/'poster_preview.png',r/'render/preview.png')
x=subprocess.run(['git','status','--porcelain=v1','-uno'],cwd='/home/takuma/kmd-analysis',capture_output=True,text=True,check=True)
(r/'evidence/FINAL_TRACKED_GIT_STATUS.txt').write_text(x.stdout)
(r/'evidence/COMPLETION.json').write_text(json.dumps(dict(output='run06',poster_size_mm=[841,594],pages=1,editable='PPTX native text and geometry',numerical_rechecks=80,numerical_mismatches=0,numeric_provenance_rows=92,PDF_text_blocks=107,PDF_missing=0,layout_overlaps=0,pinned_sources_preserved=321,new_experiments=0,commit_push_PR=False,review_method='third-party-perspective self-review; no independent reader test',physical_print_test=False,science_adoption='completed Step4 bounded claims reflected',HOLD='see reports/06_HOLD.html'),ensure_ascii=False,indent=2))
files=[]
for f in sorted(r.rglob('*')):
 rel=f.relative_to(r)
 if not f.is_file() or f.is_symlink() or rel.parts[0]=='tools' or '__pycache__' in rel.parts or f.suffix=='.zip' or f.name=='OUTPUT_SHA256.csv':continue
 b=f.read_bytes();files.append(dict(path=str(rel),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
with (r/'OUTPUT_SHA256.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=files[0]);w.writeheader();w.writerows(files)
with ZipFile(r/'poster_revision_run06.zip','w',ZIP_DEFLATED) as z:
 for v in files:z.write(r/v['path'],arcname='poster_revision_run06/'+v['path'])
 z.write(r/'OUTPUT_SHA256.csv',arcname='poster_revision_run06/OUTPUT_SHA256.csv')
print(json.dumps(dict(files=len(files),archive_bytes=(r/'poster_revision_run06.zip').stat().st_size,tracked_diff=x.stdout),ensure_ascii=False))
