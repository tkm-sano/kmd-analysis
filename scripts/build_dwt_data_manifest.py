"""Read-only provenance inventory for an already completed DWT cohort."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('root')
parser.add_argument('--preservation', default='output/toc_delivery/dwt_balance_20261113_v1/PRESERVATION_BEFORE.json')
args = parser.parse_args()
root = Path(args.root)
files = {}


def record(path, role, expected=None):
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if expected is not None and digest != expected:
        raise ValueError('PROVENANCE_HASH_MISMATCH:' + str(path))
    files[str(path)] = {'role': role, 'bytes': path.stat().st_size,
                        'sha256': digest, 'checked_now': True}


registered = json.loads((root / 'limited_REGISTERED.json').read_text())
config = json.loads(Path(registered['config_path']).read_text())
record(registered['config_path'], 'fixed execution conditions', registered['config_sha256'])
before = json.loads(Path(args.preservation).read_text())
for path, digest in before['files'].items():
    if '/frozen_demand/v1/' in path:
        record(path, 'protected frozen demand package', digest)
for scenario in ['S1', 'S2', 'S3', 'ROAD_N6', 'ROAD_N20']:
    source = Path(config['input_root']) / scenario
    record(source / 'input.json', 'common solver-independent input:' + scenario)
    for path in sorted((source / 'od').glob('*')):
        if path.is_file():
            record(path, 'adopted directed Route-v2 OD:' + scenario)
for path, digest in registered['code_hashes'].items():
    record(path, 'registered executable source', digest)
geometry = Path('output/toc_delivery/visualization_20261113_v1')
original = json.loads((geometry / 'DATA_MANIFEST.json').read_text())
record(geometry / 'DATA_MANIFEST.json', 'retained geometry source manifest')
record(geometry / 'data_access.py', 'retained road shape accessor')
index = json.loads((geometry / 'ARTIFACT_INDEX.json').read_text())['files']
for name in ['data/osm_node_ids.npy', 'data/osm_node_xy_e7.npy']:
    record(geometry / name, 'same-PBF OSM node-coordinate index', index[name]['sha256'])
for path, info in original['inputs'].items():
    if path.endswith('.osm.pbf'):
        record(path, 'pinned OSM PBF used to build retained node-coordinate index', info['sha256'])
for name in ['README.md', 'docs/research/A_TO_D_PIPELINE_FINAL_REPORT.md',
             'docs/research/A_TO_D_COMPARISON.csv', 'docs/research/INDEPENDENT_VALIDATION.md',
             'docs/research/REPRODUCE.md']:
    record(name, 'audited existing research source; not modified')
for path in Path('configs/toc_delivery').glob('*'):
    if path.is_file() and ('common_conditions' in path.name or 'human_route_time_reference' in path.name):
        record(path, 'common time assumptions or external human-time episode reference')
manifest = {'conditions': 'common-v1.1; research assumptions; not operator measurements',
            'frozen_preservation_reference': args.preservation,
            'road': original['road_version'], 'coordinates': 'WGS84 longitude/latitude degrees',
            'distance_unit': 'metres in OD; kilometres in D', 'time_unit': 'seconds in OD; minutes in W',
            'routing': 'saved directed OSRM Route-v2; no Table substitution, regeneration or online requests',
            'files': files, 'retained_geometry_cache': 'Route block responses checked against retained manifest on access',
            'S2_S3': 'input/OD preflight only; no delivery plans or performance values generated'}
(root / 'DATA_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('Verified input/source files:', len(files))
