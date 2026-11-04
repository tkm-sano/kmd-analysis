from common import *
from docx import Document
# Read-only final open test and final tracked working-tree comparison.
with ZipFile(OUT) as z: assert z.testzip() is None
Document(OUT)
initial=js(O/'INITIAL_GIT_STATE.json')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
diff=subprocess.check_output(['git','diff','--binary','HEAD'],cwd=R,text=True)
status=subprocess.check_output(['git','status','--short','--untracked-files=normal'],cwd=R,text=True)
assert head==initial['HEAD'] and not diff and not initial['diff']
(O/'GIT_DIFF_FINAL.patch').write_text(diff);(O/'GIT_STATUS_FINAL.txt').write_text(status)
assert sha(SRC)=='ea25f2cc71368669a691ebe1e7643a25f30f288c00ce34cd66ed0590d95b3da3'
assert js(O/'render08/RENDER_RUN.json')['DOCX_sha256']==sha(OUT)
assert len(rows(O/'VISUAL_PAGE_REVIEW.csv'))==88
assert all(x['status']=='PASS' for x in rows(O/'PAGE_NUMBER_CHECKS.csv'))
# Keep failed intermediate revisions and describe changes instead of removing evidence.
repairs=[
('R01','本文直下のbookmark境界を復元、新caption名重複を解消','revisions/v01_results_integrated.docx','BOOKMARK_RETARGETING.csv','元29組・53link保持、最終591検証0不一致'),
('R02','横向き節でのページ番号再開始を修正','revisions/v02_results_integrated.docx','PAGE_NUMBER_CHECKS.csv','全88頁連続'),
('R03','新規数式naryの空上限を非表示','revisions/v04_results_integrated.docx','ADDED_EQUATIONS.csv','数値・旧67式未変更'),
('R04','新規T09の正負添字をliteral指定、長い電解液式は同値な体積4行へ分解','revisions/v05_results_integrated.docx','MATH_LAYOUT_FIXTURE.png','表示エラー修正、新データ/モデル変更なし'),
('R05','新3.9の間隔調整で3行だけの次頁送りを解消','revisions/v06_results_integrated.docx','render07/pages/page_021.png','新規段落のみ書式調整'),
('R06','原付録証拠IDの見出しと説明を同頁に維持','revisions/v07_results_integrated.docx','render08/pages/page_047.png','R07孤立解消、全頁再確認'),
]
table('REVISION_AND_REVALIDATION.csv',[{'revision_id':a,'correction':b,'before_path':c,'before_sha256':sha(O/c),'evidence_path':d,'final_sha256':sha(OUT),'revalidation':e,'status':'PASS'} for a,b,c,d,e in repairs])
dump('FINAL_PRESERVATION_AND_OPEN_TEST.json',{'HEAD':head,'tracked_diff_empty':not diff,'original_sha256':sha(SRC),'output_sha256':sha(OUT),'zip_crc_test':'PASS','python_docx_open':'PASS','source_files_unchanged':317,'integrity_checks':591,'integrity_failures':0,'visual_pages':88,'footer_checks':88,'native_Word_tested':False})
# All final research outputs and retained intermediate evidence, excluding extracted tool caches.
excluded=[O/'rendering_tools/root',O/'rendering_tools/packages',O/'rendering_tools/python',O/'rendering_tools/profile']
manifest=O/'OUTPUT_SHA256_MANIFEST.csv';checksum=O/'OUTPUT_SHA256_MANIFEST.sha256'
data=[{'role':'INTEGRATED_DOCX','path':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size}]
for p in sorted(O.rglob('*')):
 if not p.is_file() or p in (manifest,checksum) or '__pycache__' in p.parts or any(x==p or x in p.parents for x in excluded):continue
 data.append({'role':'REVIEW_ARTIFACT','path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
table('OUTPUT_SHA256_MANIFEST.csv',data)
checksum.write_text(sha(manifest)+'  OUTPUT_SHA256_MANIFEST.csv\n')
for row in rows(manifest):
 p=Path(row['path']);p=p if p.is_absolute() else O/p
 assert sha(p)==row['sha256'],p
print(json.dumps({'output':str(OUT),'output_sha256':sha(OUT),'manifest_entries':len(data),'manifest_sha256':sha(manifest),'source_sha256':sha(SRC),'tracked_diff_empty':not diff},ensure_ascii=False,indent=2))
