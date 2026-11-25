"""Pin the newly approved design without altering any old policy or entry."""
from pathlib import Path
import json
from .plans import sha,VERSION

POLICY=Path(__file__).resolve().parents[3]/'configs/common_initial_20261122_v1/policy.json'
EXPECTED='e8e73b466029c9cefb0e675a1bb27c6da9d9edb65ba6e8988a827df685d388e4'

def require_policy():
    if sha(POLICY)!=EXPECTED:raise ValueError('NEW_RESEARCH_DESIGN_POLICY_CHANGED')
    value=json.loads(POLICY.read_text())
    if value['version']!=VERSION:raise ValueError('DESIGN_POLICY_VERSION_MISMATCH')
    return value
