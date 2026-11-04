from pathlib import Path
from html.parser import HTMLParser
import csv,json,hashlib,subprocess,zipfile
r=Path(__file__).resolve().parents[1]
class P(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,attrs):self.links.extend(v for k,v in attrs if k in ['src','href'])
for f in [r/'README.html',*(r/'reports').glob('*.html')]:
 p=P();p.feed(f.read_text())
 for v in p.links:
  if ':' not in v:assert (f.parent/v.split('#')[0]).exists(),(f,v)
text=(r/'poster_text.txt').read_text()
for v in ['定時配達率','インタビュー','RIQ','M1']:assert v not in text,v
for v in ['5.67%','0.478%','0.413%','未証明53','183条件とも','407']:assert v in text,v
v=json.loads((r/'render/FINAL_VALIDATION.json').read_text());assert v['visual_review'].startswith('PASS')
assert json.loads((r/'evidence/AUDIT_RESULTS.json').read_text())['failed_checks']==0
assert json.loads((r/'evidence/EXTENDED_AUDIT.json').read_text())['failed_checks']==0
assert all(v['status']=='PASS' for v in csv.DictReader((r/'evidence/ORIGINAL_PRESERVATION.csv').open()))
status=subprocess.run(['git','status','--short','--untracked-files=normal'],capture_output=True,text=True,check=True).stdout;(r/'FINAL_GIT_STATUS.txt').write_text(status)
(r/'BUILD_AND_REVIEW.txt').write_text('run03 生成・監査・表示確認\n\n方針：二経路の保存定量結果と文献から寄与条件・制約を検討する。面接・RIQ・M1は採用しない。\n\n入力：run02のポスター・編集コード・本文、保存結果CSV、固定モデル、方法・結果・考察原稿、実装snapshot、460件の厳密参照証明、460元入力行列等である。元ファイルを変更していない。\n\n監査：scripts/audit_inputs.py（41項目）、audit_extended.py（13項目）、audit_saved_routes.py（36800保存経路の目的値と制約の元行列による算術検証）。新しい経路探索・モデル実行・量子回路・速度再積分は行っていない。audit_saved_routes.pyは既存.conda/bin/pythonとNumPyを使用した。\n\n生成：PYTHONPATH=/tmp/kmd-poster-authoring-deps python scripts/build_poster.py。ReportLabとpython-pptxによる文字・図形のネイティブ作成である。\n\n描画：scripts/render_poster.py。run01の独立配置レンダラを読み取り専用で参照し、run03の独立プロファイルでLibreOffice Impress 24.2.7.2を使用した。poster.pdfは実PPTX描画結果、render/layout_reference.pdfはコード上のレイアウト参照である。\n\n確認：scripts/validate_final.pyで寸法、全段落抽出、図形範囲、余白、列間侵入を照合した。全体画像の確認後visual_reviewを記録した。再生成時は再確認が必要である。PDF検証は既存読み取り専用PyMuPDF環境を使用した。\n\n補足：scripts/build_causal_svg.pyとbuild_reports.pyでSVG、HTML、CSVを生成する。原本1848ファイルのhashは保存manifestまたは作業開始時と一致した。\n\n表示：A1縦594×841mm。本文22–26pt、表21pt、詳細18–20pt、文献18pt。フォントDroid Sans Fallback／DejaVu Sans。Microsoft PowerPoint固有の描画と紙への試し刷りは未実施である。印刷にはベクターPDFを使用する。\n\ncommit・push・PR作成は行っていない。\n')
files=[r/f for f in ['README.html','poster.pptx','poster.pdf','poster.png','poster_preview.png','poster_text.txt','poster_layout.json','00_SOURCE_INVENTORY.csv','01_POLICY_AND_SCOPE.txt','BUILD_AND_REVIEW.txt','render/FINAL_VALIDATION.json','FINAL_GIT_STATUS.txt']]
for folder in ['scripts','reports','sources','evidence']:files.extend(p for p in (r/folder).glob('*') if p.is_file())
with (r/'DELIVERABLE_MANIFEST.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['path','bytes','sha256']);w.writerows([str(p.relative_to(r)),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()] for p in files)
with zipfile.ZipFile(r/'poster_revision_package.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[r/'DELIVERABLE_MANIFEST.csv']:z.write(p,p.relative_to(r))
print('All final checks passed. Package files:',len(files)+1,'MB:',round((r/'poster_revision_package.zip').stat().st_size/1e6,2),'Git status unchanged:',status==(r/'INITIAL_GIT_STATUS.txt').read_text())
