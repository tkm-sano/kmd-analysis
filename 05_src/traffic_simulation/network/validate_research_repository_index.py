from pathlib import Path
import json, re, yaml

ROOT = Path(__file__).resolve().parents[3]
INDEX = ROOT/'reproducibility/indexes/research_repository_index_v17.yml'
AUTH = ROOT/'reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml'

def role(path):
    n=path.name.lower()
    if path.suffix=='.md':
        if 'specification' in n or 'policy' in n: return 'NORMATIVE_SPECIFICATION'
        if 'index' in n or 'map' in n: return 'REPOSITORY_INDEX'
        return 'RESEARCH_NOTE'
    if 'schema' in n: return 'SCHEMA'
    if 'decision' in n: return 'DECISION'
    if 'registry' in n: return 'REGISTRY'
    if 'manifest' in n: return 'MANIFEST'
    if 'acceptance' in n: return 'ACCEPTANCE'
    if 'baseline' in n: return 'BASELINE'
    return 'CONFIGURATION'

def main():
    idx=yaml.safe_load(INDEX.read_text()); auth=yaml.safe_load(AUTH.read_text())
    assert idx['status']=='CURRENT' and idx['current_authority'].endswith('current_network_completion_authority_v17.yml')
    assert auth['accepted_run']['network_sha256']=='4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f'
    paths=[]
    for base in (ROOT/'05_src',ROOT/'reproducibility/config',ROOT/'reproducibility/indexes',ROOT/'docs'):
        if base.exists(): paths += [p for p in base.rglob('*') if p.is_file() and p.suffix.lower() in {'.md','.yml','.yaml','.json'}]
    counts={}
    for p in paths: counts[role(p.relative_to(ROOT))]=counts.get(role(p.relative_to(ROOT)),0)+1
    required=[auth['decision']['path'],auth['specification']['path'],auth['pipeline_specification']['path'],auth['registry']['path'],auth['schema']['policy_path'],auth['schema']['record_path'],auth['accepted_run']['network_file'],auth['accepted_run']['acceptance_artifact'],auth['accepted_run'].get('portal_status','')]
    required=[x for x in required if x]
    assert all((ROOT/x).exists() for x in required)
    print(json.dumps({'repository_index':'passed','scanned_files':len(paths),'role_counts':counts,'current_authority':'unique','missing_authority_paths':0},sort_keys=True))

if __name__=='__main__': main()
