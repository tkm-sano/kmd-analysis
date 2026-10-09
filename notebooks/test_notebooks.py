"""Execute all six notebooks with the current Python kernel; no production experiments."""
from pathlib import Path
import argparse, hashlib, json, os, sys, tempfile, time
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--save-outputs',action='store_true');parser.add_argument('--report',type=Path);args=parser.parse_args()
 deps=json.loads((ROOT/'notebooks/fixtures/dependencies.json').read_text());before={p:digest(ROOT/p) for p in deps}
 assert all(before[p]==r['sha256'] for p,r in deps.items())
 results=[]
 with tempfile.TemporaryDirectory(prefix='notebook-kernel-') as tmp:
  kd=Path(tmp)/'python3';kd.mkdir()
  (kd/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Notebook validation','language':'python','env':{'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}}))
  for path in sorted((ROOT/'notebooks').glob('[0-9][0-9]_*.ipynb')):
   start=time.monotonic();book=nbformat.read(path,as_version=4);nbformat.validate(book)
   client=NotebookClient(book,timeout=90,kernel_name='python3',resources={'metadata':{'path':str(ROOT/'notebooks')}})
   client.km=client.create_kernel_manager();client.km.kernel_spec_manager=KernelSpecManager(kernel_dirs=[tmp],ensure_native_kernel=False)
   try:
    client.execute()
    if args.save_outputs:nbformat.write(book,path)
    results.append({'notebook':path.name,'status':'PASS','cells':len(book.cells),'seconds':round(time.monotonic()-start,3),'code_cells':sum(c.cell_type=='code' for c in book.cells)})
   except Exception as e:
    results.append({'notebook':path.name,'status':'FAIL','error':str(e),'seconds':round(time.monotonic()-start,3)})
 after={p:digest(ROOT/p) for p in deps};assert before==after,'Canonical input modified'
 payload={'results':results,'dependency_hashes_unchanged':before==after,'dependency_count':len(deps),'scope':'Default cells only; optional optimizer false; not whole-model validation','python':sys.version.split()[0]}
 text=json.dumps(payload,ensure_ascii=False,indent=2)
 if args.report:
  if args.report.exists():raise FileExistsError('Refuse overwrite: '+str(args.report))
  args.report.write_text(text+'\n')
 print(text)
 return int(any(r['status']!='PASS' for r in results))
if __name__=='__main__':sys.exit(main())
