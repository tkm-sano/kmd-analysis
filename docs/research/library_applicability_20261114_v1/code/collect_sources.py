"""Read-only upstream metadata and preservation manifest; standard library only."""
from pathlib import Path
import urllib.request, json, hashlib, subprocess, datetime, concurrent.futures
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parents[2]
E=ROOT/'evidence'; E.mkdir(exist_ok=True)
urls={
 'qamomile_repo':'https://api.github.com/repos/Jij-Inc/Qamomile',
 'qamomile_releases':'https://api.github.com/repos/Jij-Inc/Qamomile/releases?per_page=5',
 'qunasys_repos':'https://api.github.com/orgs/QunaSys/repos?per_page=100',
 'quri_repo':'https://api.github.com/repos/QunaSys/quri-sdk',
 'quri_releases':'https://api.github.com/repos/QunaSys/quri-sdk/releases?per_page=5',
 'qulacs_repo':'https://api.github.com/repos/qulacs/qulacs',
 'qulacs_releases':'https://api.github.com/repos/qulacs/qulacs/releases?per_page=3',
 'paper':'https://arxiv.org/html/2503.17051v1',
}
for p in ['qamomile','qulacs','quri-parts','quri-parts-qulacs','quri-parts-qiskit','quri-algo','quri-vm','quri-sdk','quri-parts-cuquantum','quri-chem','quket','qulacsvis','quantestpy','pyqret']:
 urls['pypi_'+p]='https://pypi.org/pypi/'+p+'/json'
def get(item):
 name,url=item
 try:
  req=urllib.request.Request(url, headers={'User-Agent':'kmd-library-survey'})
  with urllib.request.urlopen(req,timeout=60) as f: data=f.read()
  dest=E/(name+('.html' if name=='paper' else '.json'));dest.write_bytes(data)
  return dict(name=name,url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),ok=True)
 except Exception as e:return dict(name=name,url=url,ok=False,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: manifest=list(ex.map(get,urls.items()))
(E/'sources_manifest.json').write_text(json.dumps({'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':manifest},indent=2))
files=[p for p in REPO.rglob('AGENTS.md') if not any(x in p.parts for x in ['.git','.conda','output','review_outputs'])]
files += [REPO/'README.md',REPO/'.gitignore']
for folder in ['src/kmd_toc','configs/toc_delivery','configs/toc_delivery_d','tests/toc_cg','tests/toc_vehicle_day','tests/toc_pipeline','tests/toc_dwt','reproducibility/environment']:
 files += [p for p in (REPO/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
(E/'preservation_before.json').write_text(json.dumps({str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))},indent=2))
(E/'git_status_before.txt').write_bytes(subprocess.check_output(['git','status','--short','--untracked-files=normal'],cwd=REPO))
for x in manifest: print(x['name'],x['ok'])
for p in E.glob('pypi_*.json'):
 j=json.loads(p.read_text());v=j['info']['version']; print(p.stem,v,j['info']['requires_python'], j['releases'].get(v,[{}])[0].get('upload_time_iso_8601'))
