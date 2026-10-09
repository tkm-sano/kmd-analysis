"""Read the existing fixed mass-to-DC freeze; never update its authority."""
from pathlib import Path
import hashlib
import json
MODEL_RELATIVE = '01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'
EXPECTED_SHA256 = 'b37fd532a5a7daf84f07924d954d6f8e2584f51d218506eeb14e70c53538cf78'

def load_model():
    """Fresh dictionary of frozen stages, units, assumptions and physics parameters."""
    data = (Path(__file__).resolve().parents[3] / MODEL_RELATIVE).read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Controlled mass-to-DC model freeze hash mismatch')
    return json.loads(data)

def stage_inputs():
    """Frozen Energy inputs including running_mass_kg (vehicle plus 55 kg driver)."""
    return load_model()['stage_inputs']
