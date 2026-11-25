"""Strict, version-specific integrity checks; never executes research algorithms.

Live guidance is not an immutable historical workspace. Approved successors
must match pre-existing release hashes AND preserve the original snapshot.
The original experiment execution guards and all old manifests stay unchanged.
"""
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
import json
from pathlib import Path

CATALOG_PATH = 'configs/hash_repair_20261120_v1/approved_versions.json'
CATALOG_SHA256 = '7956cc89470037314d360aab60cb6bbb2baac890e7142ca82606ccbee08e7546'
ORIGINAL_ROOT = '/home/takuma/kmd-analysis/'
P2_BASELINE = 'docs/research/p2_freeze_20261120/PRESERVATION_BEFORE.json'
P2_CONFIG_SHA256 = 'd478872fb810b5913cc1765cd6ecebe28080e293ac8a376c67073b35b4245e4d'
SHOTS_CONFIG_SHA256 = 'deb46439a799800e42b96014e4027164f65a6225b40d12e14733d0533ffb3a4d'
P2_SOURCE_SUCCESSORS = {'src/kmd_toc/main_experiment_d/shots.py',
                        'src/kmd_toc/main_experiment_d/quantum.py'}


class IntegrityError(ValueError):
    pass


def _unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise IntegrityError('DUPLICATE_JSON_KEY:' + key)
        obj[key] = value
    return obj


def _relative(name):
    if name.startswith(ORIGINAL_ROOT):
        name = name[len(ORIGINAL_ROOT):]
    path = Path(name)
    if path.is_absolute() or '..' in path.parts:
        raise IntegrityError('UNSAFE_PATH:' + name)
    return str(path)


@lru_cache(maxsize=64)
def _base_root(absolute_root):
    # Cache only the root spelling, never file contents or target resolutions.
    return Path(absolute_root).resolve()


def _path(root, name):
    base = _base_root(str(Path(root).absolute()))
    path = base / _relative(name)
    if not path.resolve().is_relative_to(base):
        raise IntegrityError('PATH_OUTSIDE_ROOT:' + name)
    return path


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _check(root, name, expected):
    actual = _sha(_path(root, name))
    if actual != expected:
        raise IntegrityError('SHA256_MISMATCH:' + _relative(name))
    return {'path': _relative(name), 'sha256': actual}


def _json(root, name):
    return json.loads(_path(root, name).read_text(encoding='utf-8'),
                      object_pairs_hook=_unique)


def _catalog(root):
    _check(root, CATALOG_PATH, CATALOG_SHA256)
    catalog = _json(root, CATALOG_PATH)
    if catalog['schema_version'] != 1 or catalog['catalog_version'] != 'approved-transitions-20261120-v1':
        raise IntegrityError('UNSUPPORTED_CATALOG_VERSION')
    for name, expected in catalog['evidence_sha256'].items():
        _check(root, name, expected)
    guidance = {item['file']: item for item in _json(root,
        'docs/audits/current_docs_alignment_20261120_v1/CHANGED_FILES.json')}
    fcfs_sources = _json(root, 'reports/fcfs_v1_20261120/SOURCE_HASHES.json')
    fcfs_before = _json(root, 'reports/fcfs_v1_20261120/BEFORE.json')
    for item in catalog['transitions']:
        name = item['path']
        if item['version'] == 'current-guidance-20261120-v1':
            previous = guidance[name]
            valid = (previous['before_sha256'] == item['before_sha256'] and
                     previous['after_sha256'] == item['after_sha256'])
        elif item['version'] == 'FCFS_v1-implementation-release':
            valid = (fcfs_sources[name] == item['after_sha256'] and
                     fcfs_before['sha256'][name] == item['before_sha256'] and
                     name in fcfs_before['authorized_edit_paths'])
        else:
            raise IntegrityError('UNSUPPORTED_SUCCESSOR_VERSION:' + name)
        if not valid:
            raise IntegrityError('TRANSITION_EVIDENCE_MISMATCH:' + name)
    return catalog


def _documents(root, catalog):
    checks = []
    for item in catalog['frozen_documents']:
        checks.append(_check(root, item['path'], item['sha256']))
        checks.append(_check(root, item['manifest'], item['manifest_sha256']))
        manifest = _json(root, item['manifest'])
        if manifest['sha256'] != item['sha256'] or manifest['file_path'] != item['path']:
            raise IntegrityError('MANIFEST_DOCUMENT_IDENTITY_MISMATCH:' + item['id'])
        if manifest['content_utf8'].encode('utf-8') != _path(root, item['path']).read_bytes():
            raise IntegrityError('MANIFEST_ORIGINAL_BYTES_MISMATCH:' + item['id'])
    return checks


def _fcfs_release(root):
    # The release record's own bytes are pinned by _catalog. Verify the whole
    # recorded dependency set, not just the six files in the reported drift.
    return [_check(root, name, expected) for name, expected in _json(root,
        'reports/fcfs_v1_20261120/SOURCE_HASHES.json').items()]


def _seals(root, catalog):
    for key in ('p2_seal', 'shots_seal'):
        item = catalog[key]
        _check(root, item['path'], item['sha256'])
    p2 = _json(root, catalog['p2_seal']['path'])
    shots = _json(root, catalog['shots_seal']['path'])
    if p2['prior_shots_seal_sha256'] != catalog['shots_seal']['sha256']:
        raise IntegrityError('P2_SHOTS_VERSION_CHAIN_MISMATCH')
    if p2['depth_config_sha256'] != P2_CONFIG_SHA256 or p2['shots_config_sha256'] != SHOTS_CONFIG_SHA256:
        raise IntegrityError('FROZEN_PARAMETER_ANCHOR_MISMATCH')
    checks = []
    for name, expected in {**p2['source_sha256'], **p2['artifact_sha256']}.items():
        checks.append(_check(root, name, expected))
    for name, expected in {**shots['source_sha256'], **shots['artifact_sha256']}.items():
        relative = _relative(name)
        if relative in P2_SOURCE_SUCCESSORS:
            # User-approved depth freeze superseded only these implementation
            # files; their shots-era hashes remain in the untouched old seal.
            expected = p2['source_sha256'][relative]
        checks.append(_check(root, name, expected))
    return p2, shots, checks


def _transition(root, catalog, name, expected):
    item = next((item for item in catalog['transitions'] if item['path'] == name), None)
    if item is None or item['before_sha256'] != expected:
        raise IntegrityError('UNREGISTERED_VERSION_CHANGE:' + name)
    _check(root, item['before_path'], expected)
    _check(root, name, item['after_sha256'])
    return {'path': name, 'expected_sha256': expected, 'status': 'VERIFIED_APPROVED_SUCCESSOR',
            'historical_path': item['before_path'], 'historical_sha256': expected,
            'active_sha256': item['after_sha256'], 'version': item['version']}


def _preserved_entry(root, catalog, p2, shots, name, expected):
    try:
        actual = _sha(_path(root, name))
        if actual == expected:
            return {'path': name, 'status': 'UNCHANGED', 'expected_sha256': expected}
        if name in P2_SOURCE_SUCCESSORS and expected == shots['source_sha256'][name]:
            _check(root, name, p2['source_sha256'][name])
            return {'path': name, 'status': 'VERIFIED_P2_IMPLEMENTATION_SUCCESSOR',
                    'expected_sha256': expected, 'active_sha256': p2['source_sha256'][name]}
        return _transition(root, catalog, name, expected)
    except (OSError, ValueError, KeyError) as error:
        return {'path': name, 'status': 'FAIL', 'error': str(error)}


def _result(profile, checks, errors=()):
    failed = [item for item in checks if item.get('status') == 'FAIL']
    return {'status': 'FAIL' if errors or failed else 'PASS', 'profile': profile,
            'scope': 'integrity of explicitly named versions only; no experiment eligibility promotion',
            'errors': list(errors), 'checks': checks, 'main_experiment_status': 'HOLD',
            'n_K_R_local': 'UNDECIDED', 'old_execution_guards_unchanged': True}


def verify_preservation(root):
    """Check the unchanged p2-era baseline using explicit approved versions."""
    try:
        catalog = _catalog(root)
        _documents(root, catalog)
        _fcfs_release(root)
        p2, shots, _ = _seals(root, catalog)
        # The baseline's exact hash is itself inside the unchanged p2 seal.
        expected = p2['artifact_sha256'][P2_BASELINE]
        _check(root, P2_BASELINE, expected)
        files = _json(root, P2_BASELINE)['files']
        with ThreadPoolExecutor(max_workers=8) as pool:
            checks = list(pool.map(lambda pair: _preserved_entry(root, catalog, p2, shots, *pair), files.items()))
        result = _result('historical-p2-preservation', checks)
        result['baseline_path'] = P2_BASELINE
        result['baseline_sha256'] = expected
        result['live_hash_differences'] = sum(item['status'] != 'UNCHANGED' for item in checks)
        result['resolved_by_explicit_version'] = sum(item['status'].startswith('VERIFIED_') for item in checks)
        return result
    except (OSError, ValueError, KeyError, TypeError) as error:
        return _result('historical-p2-preservation', [], [str(error)])


def verify_transition(root, name, expected):
    """Small isolated-test surface; the same rules used by full preservation."""
    try:
        catalog = _catalog(root)
        _documents(root, catalog)
        return _result('named-version-transition', [_transition(root, catalog, name, expected)])
    except (OSError, ValueError, KeyError, TypeError) as error:
        return _result('named-version-transition', [], [str(error)])


def verify_profile(root, profile='current-frozen-integrity'):
    if profile == 'historical-p2-preservation':
        return verify_preservation(root)
    try:
        catalog = _catalog(root)
        checks = _documents(root, catalog)
        if profile == 'current-frozen-integrity':
            checks.extend(_fcfs_release(root))
            _, _, seal_checks = _seals(root, catalog)
            checks.extend(seal_checks)
            for item in catalog['transitions']:
                checks.append(_transition(root, catalog, item['path'], item['before_sha256']))
        elif profile == 'historical-nkr':
            anchor = catalog['historical_nkr_manifest']
            _check(root, anchor['path'], anchor['sha256'])
            manifest = _json(root, anchor['path'])
            for name, expected in {**manifest['source_hashes'], **manifest['input_hashes']}.items():
                try:
                    checks.append(_check(root, name, expected))
                except IntegrityError:
                    checks.append(_transition(root, catalog, name, expected))
        else:
            raise IntegrityError('UNSUPPORTED_PROFILE:' + profile)
        result = _result(profile, checks)
        result['decisions_1_3'] = catalog['decisions_1_3']
        return result
    except (OSError, ValueError, KeyError, TypeError) as error:
        return _result(profile, [], [str(error)])
