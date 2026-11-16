from pathlib import Path
import urllib.request,json,concurrent.futures,hashlib
E=Path(__file__).resolve().parents[1]/'evidence'
repos=['QunaSys/quri-parts-cuquantum','QunaSys/quri-parts-qsci','QunaSys/quration','QunaSys/qurs','QunaSys/qulacs-visualizer','QunaSys/qiskit-qube-backend','QunaSys/ActiveSpaceFinder','qulacs/qulacs','qulacs/QuantestPy','quket/quket']
urls={}
for r in repos:
 name=r.replace('/','__');urls[name+'_repo.json']='https://api.github.com/repos/'+r
 for f in ['README.md','LICENSE','pyproject.toml']:
  urls[name+'__'+f]='https://raw.githubusercontent.com/'+r+'/HEAD/'+f
for r,ref,files in [('Jij-Inc/Qamomile','main',['README.md','pyproject.toml']),('Jij-Inc/Qamomile','v0.15.2',['README.md','pyproject.toml','qamomile/optimization/qaoa.py','qamomile/circuit/algorithm/qaoa.py','qamomile/optimization/fqaoa.py','qamomile/optimization/binary_model/model.py','tests/optimization/test_binary_model.py']),('QunaSys/quri-sdk','v0.28.0',['README.md','quri-parts/LICENSE','quri-algo/LICENSE','quri-vm/LICENSE','quri-parts/packages/qiskit/pyproject.toml'])]:
 for f in files:urls[r.replace('/','__')+'__'+ref+'__'+f.replace('/','__')]='https://raw.githubusercontent.com/'+r+'/'+ref+'/'+f
urls['qunasys_services.html']='https://qunasys.com/en/services/'
urls['qunasys_quri_release.html']='https://qunasys.com/en/news/posts/quri-parts-release/'
def get(kv):
 name,url=kv
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'kmd-survey'})
  data=urllib.request.urlopen(req,timeout=30).read();(E/name).write_bytes(data)
  return {'file':name,'url':url,'ok':True,'sha256':hashlib.sha256(data).hexdigest()}
 except Exception as ex:return {'file':name,'url':url,'ok':False,'error':str(ex)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:res=list(ex.map(get,urls.items()))
(E/'extended_sources_manifest.json').write_text(json.dumps(res,indent=2))
for r in res:
 if r['ok'] and r['file'].endswith('_repo.json'):
  d=json.loads((E/r['file']).read_text());print(d['full_name'],d['archived'],d['pushed_at'],(d.get('license') or {}).get('spdx_id'))
