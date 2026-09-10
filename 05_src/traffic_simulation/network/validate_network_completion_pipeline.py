from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / 'reproducibility/config/traffic_simulation/network_completion_pipeline_v17.yml'

def main():
    c = yaml.safe_load(CFG.read_text())
    assert c['status'] == 'CURRENT'
    assert c['decision_id'] == 'DEC-P13-FORMAL-COMPLETION-THREE-TIER-001'
    stages = c['stages']
    assert [s['order'] for s in stages] == list(range(1, 8))
    assert [s['id'] for s in stages] == ['SOURCE','STRUCTURAL','THREE_TIER_FORMAL','SUMO','MAPPING','ROUTEABILITY','ACCEPTANCE']
    assert all(x['status'] == 'SUPERSEDED' for x in c['superseded_pipelines'])
    assert c['prohibited'] == ['stage_reordering','silent_fallback','historical_run_overwrite']
    print({'pipeline': 'passed', 'stages': len(stages), 'superseded': len(c['superseded_pipelines'])})

if __name__ == '__main__':
    main()
