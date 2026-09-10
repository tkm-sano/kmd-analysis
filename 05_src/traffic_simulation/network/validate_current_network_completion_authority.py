from pathlib import Path
import hashlib, json, yaml

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml'

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    m = yaml.safe_load(MANIFEST.read_text())
    assert m['status'] == 'CURRENT'
    assert m['decision']['id'] == 'DEC-P13-FORMAL-COMPLETION-THREE-TIER-001'
    assert m['accepted_run']['network_id'] == 'P13-THREE-TIER-RUN-2'
    paths = [m['decision']['path'], m['specification']['path'], m['pipeline_specification']['path'], m['registry']['path'], m['schema']['policy_path'], m['schema']['record_path'], m['accepted_run']['network_file'], m['accepted_run']['acceptance_artifact']]
    assert all((ROOT / p).exists() for p in paths)
    acceptance = json.loads((ROOT / m['accepted_run']['acceptance_artifact']).read_text())
    assert acceptance['FORMAL_NETWORK_ACCEPTED'] is True
    assert acceptance['network_id'] == m['accepted_run']['network_id']
    assert acceptance['decision_id'] == m['decision']['id']
    assert sha256(ROOT / m['accepted_run']['network_file']) == m['accepted_run']['network_sha256']
    print({'authority': 'passed', 'decision_id': m['decision']['id'], 'run_id': m['accepted_run']['run_id'], 'network_sha256': m['accepted_run']['network_sha256']})

if __name__ == '__main__':
    main()
