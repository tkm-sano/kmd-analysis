"""Extract distro renderer packages locally; no system install or root privileges."""
from pathlib import Path
import shlex,urllib.request,concurrent.futures,hashlib,json,subprocess,time
O=Path(__file__).resolve().parents[1];base=O/'rendering_tools';pkg=base/'packages';root=base/'root';pkg.mkdir(exist_ok=True);root.mkdir(exist_ok=True)
items=[]
for line in (base/'APT_URIS.txt').read_text().splitlines():
 if line.startswith("'"):
  url,name,size,md5=shlex.split(line);items.append((url.replace('http://','https://'),name,int(size),md5.split(':',1)[1]))
def download(x):
 url,name,size,md5=x;p=pkg/name
 if not p.exists():
  for attempt in range(3):
   try:
    with urllib.request.urlopen(url,timeout=45) as r:p.write_bytes(r.read())
    break
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 data=p.read_bytes();assert len(data)==size and hashlib.md5(data).hexdigest()==md5
 return {'url':url,'path':str(p),'bytes':size,'sha256':hashlib.sha256(data).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:done=list(pool.map(download,items))
for x in done:subprocess.run(['dpkg-deb','-x',x['path'],str(root)],check=True)
(base/'PACKAGES.json').write_text(json.dumps(done,indent=2));print('Downloaded and extracted',len(done),'packages',sum(x['bytes'] for x in done),'bytes',flush=True)

# Debian post-install registry links are performed only inside this local extraction.
import shutil
for q in (root/'usr/lib/libreoffice/program').glob('*rc'):
 if q.is_file():
  old=q.read_text(errors='replace');new=old.replace('file:///usr/lib/libreoffice',(root/'usr/lib/libreoffice').resolve().as_uri()).replace('file:///etc/libreoffice',(root/'etc/libreoffice').resolve().as_uri())
  if new!=old:q.write_text(new)
for q in list(root.rglob('*')):
 if q.is_symlink():
  dst=q.readlink()
  if dst.is_absolute() and (root/str(dst).lstrip('/')).exists():q.unlink();q.symlink_to((root/str(dst).lstrip('/')).resolve())
shutil.copytree(root/'usr/lib/libreoffice/share/.registry',root/'etc/libreoffice/registry',dirs_exist_ok=True)
subprocess.run(['gcc','-shared','-fPIC','-o',str(base/'set_langtag.so'),str(base/'set_langtag.c'),'-ldl'],check=True)
