import hashlib
from pathlib import Path
from kmd_toc.common.config import ROOT,read_json

VERSION='descriptive-statistics-20261121-v1'
CONFIG='configs/statistical_scope_20261121_v1/policy.json'
SPEC='docs/research/statistical_scope_20261121_v1/FREEZE_SPEC.md'
PINS={CONFIG:'8bbb4d0d2d85cd18756d5dd8d06bebe0503ce3cb83e26c0d0693333e8888b496',
      SPEC:'de48843978d08b9ef52b5f50b650152027ac5bc7e4a821e28ca5151ce8c9ba5a'}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def require_frozen(root=ROOT):
    for name,expected in PINS.items():
        if digest(Path(root)/name)!=expected:raise ValueError('STATISTICAL_FREEZE_CHANGED:'+name)
    return read_json(Path(root)/CONFIG)
