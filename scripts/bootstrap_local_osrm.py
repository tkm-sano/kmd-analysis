"""Free, rootless official OSRM runtime; pinned amd64 image, verified layers.

No Docker daemon, package replacement, public routing service, or paid API.
"""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import shutil
import tarfile
from urllib.request import Request,urlopen

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rootfs',required=True);a=parser.parse_args()
    root=Path(a.rootfs).resolve();root.mkdir(parents=True,exist_ok=False)
    manifest=json.loads(Path('output/toc_delivery/ad_pipeline_20261112/sources/OSRM_RUNTIME_MANIFEST.json').read_text())
    token=json.load(urlopen('https://ghcr.io/token?service=ghcr.io&scope=repository:project-osrm/osrm-backend:pull'))['token']
    for layer in manifest['layers']:
        digest=layer['digest'];archive=root/(digest.split(':')[1]+'.tar.gz')
        req=Request('https://ghcr.io/v2/project-osrm/osrm-backend/blobs/'+digest,headers={'Authorization':'Bearer '+token})
        with urlopen(req) as r,archive.open('wb') as f:shutil.copyfileobj(r,f)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest.split(':')[1]:raise ValueError('LAYER_HASH')
        with tarfile.open(archive) as tar:
            for item in tar:
                path=PurePosixPath(item.name)
                if path.is_absolute() or '..' in path.parts:continue
                name=str(path)
                if not name.startswith(('usr/local/bin/','usr/local/lib/','opt/','usr/lib/x86_64-linux-gnu/')):continue
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                if item.isfile():
                    with tar.extractfile(item) as source,target.open('wb') as dest:shutil.copyfileobj(source,dest)
                    target.chmod(item.mode&0o777)
                elif item.issym():
                    link=PurePosixPath(item.linkname)
                    if link.is_absolute() or not (target.parent/item.linkname).resolve().is_relative_to(root):continue
                    if target.is_symlink():target.unlink()
                    target.symlink_to(item.linkname)
        archive.unlink()
    print('LD_LIBRARY_PATH='+str(root/'usr/local/lib')+':'+str(root/'usr/lib/x86_64-linux-gnu'))

if __name__=='__main__':main()
