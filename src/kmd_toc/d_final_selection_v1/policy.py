"""Fixed anchors for the explicitly approved final-selection version."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VERSION = 'D-final-Idual-20261121-v1'
CONFIG = 'configs/d_final_selection_20261121_v1/policy.json'
SPEC = 'docs/research/d_final_selection_20261121_v1/FREEZE_SPEC.md'
PINS = {
    CONFIG: '89f603a1b3c168886aa158ac993ece1edbb9ef3a6715b9e17d70a9ab8bd8c5f1',
    SPEC: '24a19b418ca0e3e928be3c02bb890f0b741d517257394570a984aaa5c49a6a29',
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('DUPLICATE_JSON_KEY:' + k)
        result[k] = v
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('NONFINITE_JSON:' + x)))


def require_frozen(root=ROOT):
    for name, expected in PINS.items():
        if digest(Path(root) / name) != expected:
            raise ValueError('FINAL_SELECTION_FROZEN_FILE_CHANGED:' + name)
    from kmd_toc.fcfs_v1.policy import require_frozen as fcfs
    from kmd_toc.main_experiment_d.depth import frozen_config as depth
    from kmd_toc.main_experiment_d.shots import frozen_config as shots
    fcfs()
    depth()
    shots()
    return read(Path(root) / CONFIG)
