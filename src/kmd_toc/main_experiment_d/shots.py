"""Separate, hash-pinned protocol decision; never edits historical configurations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'configs/shots_freeze_20261120/main_experiment_d.json'
# Trust anchor for the approved file, not a hash calculated from an unchecked override.
CONFIG_SHA256 = 'deb46439a799800e42b96014e4027164f65a6225b40d12e14733d0533ffb3a4d'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same_json(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def frozen_config():
    raw = CONFIG.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ValueError('FROZEN_SHOTS_CONFIG_CHANGED')
    return json.loads(raw)


def check_overrides(overrides):
    """Only one canonical pair is accepted; even same-value aliases are forbidden."""
    if overrides is None:
        return
    expected = frozen_config()['qaoa_shots']
    if (set(overrides) != {'optimization', 'final_extraction'} or
            any(type(overrides[k]) is not int or overrides[k] != expected[k] for k in overrides)):
        raise ValueError('MAIN_D_SHOTS_OVERRIDE_FORBIDDEN')


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
        raise ValueError('SAFE_NONEMPTY_ID_REQUIRED')
    return value


def source_pins():
    files = sorted(Path(__file__).parent.glob('*.py'))
    files += [ROOT / 'scripts/large_n_20261119_v5/quantum.py',
              ROOT / 'scripts/p2_precision_20261120/sector_mps.py']
    return {str(p.relative_to(ROOT)): digest(p) for p in files}


def prepare_trial(out, trial_id, scale, branch_seeds, *, shots=None):
    """Save four branch contracts without loading inputs, generating demand or running D.

    Seeds are supplied by the future approved seed registry, never inferred from shots.
    Depth is separately approved; n, K, R, optimizer, T and J remain undecided.
    """
    config = frozen_config()
    from . import depth
    depth_config = depth.frozen_config()
    if depth_config['shots_freeze'] != {'path': str(CONFIG.relative_to(ROOT)), 'sha256': CONFIG_SHA256}:
        raise ValueError('DEPTH_SHOTS_FREEZE_REFERENCE_MISMATCH')
    check_overrides(shots)
    _identifier(trial_id)
    if scale not in ('S1', 'S2', 'S3'):
        raise ValueError('S1_S2_S3_REQUIRED')
    if len(branch_seeds) != 4 or any(type(s) is not int or s < 0 for s in branch_seeds):
        raise ValueError('FOUR_EXPLICIT_BRANCH_SEEDS_REQUIRED')
    manifest = {
        'trial_id': trial_id, 'scale': scale, 'method': 'D',
        'scope': 'MAIN_EXPERIMENT_D', 'status': 'PREPARED_MAIN_HOLD',
        'main_experiment_authorized': False,
        'HEAD': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'shots_config_path': str(CONFIG.relative_to(ROOT)),
        'shots_config_sha256': CONFIG_SHA256, 'shots_config': config,
        'qaoa_shots': deepcopy(config['qaoa_shots']), 'source_sha256': source_pins(),
        'depth_config_path': str(depth.CONFIG.relative_to(ROOT)),
        'depth_config_sha256': depth.CONFIG_SHA256, 'depth_config': depth_config,
        'qaoa': deepcopy(depth_config['qaoa']),
        'branches': [{'branch_id': i, 'optimizer_seed': seed, 'native_threads': 1,
                      'qaoa': deepcopy(depth_config['qaoa']),
                      'qaoa_shots': deepcopy(config['qaoa_shots'])}
                     for i, seed in enumerate(branch_seeds)],
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'MANIFEST.json').open('x') as stream:
        json.dump(manifest, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return out / 'MANIFEST.json'


def load_trial(path):
    """Replay reads the saved values and checks them against the approved pin."""
    config = frozen_config()
    manifest = json.loads(Path(path).read_text())
    from . import depth
    depth_config = depth.frozen_config()
    if (manifest.get('depth_config_path') != str(depth.CONFIG.relative_to(ROOT)) or
            manifest.get('depth_config_sha256') != depth.CONFIG_SHA256 or
            not same_json(manifest.get('depth_config'), depth_config) or
            not same_json(manifest.get('qaoa'), depth_config['qaoa'])):
        raise ValueError('MANIFEST_FROZEN_DEPTH_MISMATCH: a new depth-aware registration is required')
    if (manifest.get('method') != 'D' or manifest.get('scope') != 'MAIN_EXPERIMENT_D' or
            manifest.get('shots_config_path') != str(CONFIG.relative_to(ROOT)) or
            manifest.get('shots_config_sha256') != CONFIG_SHA256 or
            not same_json(manifest.get('shots_config'), config) or
            not same_json(manifest.get('qaoa_shots'), config['qaoa_shots'])):
        raise ValueError('MANIFEST_FROZEN_SHOTS_MISMATCH')
    if manifest.get('source_sha256') != source_pins():
        raise ValueError('REGISTERED_SOURCE_CHANGED')
    branches = manifest.get('branches', [])
    if (manifest.get('scale') not in ('S1', 'S2', 'S3') or len(branches) != 4 or
            [b.get('branch_id') for b in branches] != list(range(4)) or
            any(not same_json(b.get('qaoa'), depth_config['qaoa']) or
                not same_json(b.get('qaoa_shots'), config['qaoa_shots']) or b.get('native_threads') != 1 or
                type(b.get('optimizer_seed')) is not int or b['optimizer_seed'] < 0 for b in branches)):
        raise ValueError('FOUR_BRANCH_SHOTS_CONTRACT_MISMATCH')
    _identifier(manifest['trial_id'])
    return manifest


def run_main(path):
    load_trial(path)
    # Do not delegate to historical runners or silently promote a prepared contract.
    raise ValueError('MAIN_EXPERIMENT_HOLD: n/K/R_local, other QAOA parameters, T/J and launch approval unresolved')
