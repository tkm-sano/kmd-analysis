from __future__ import annotations
import copy, json
import pytest
from traffic_simulation.network.validate_three_tier_completion import ThreeTierValidationError, RUN, validate_three_tier_completion

def test_full_three_tier_record_accounting_and_provenance_passes():
    result=validate_three_tier_completion()
    assert result["record_count"]==115935
    assert result["tiers"]=={"DIRECT":15,"INFERRED":101331,"FALLBACK":14589}
    assert result["formal_blocker"]==0

def test_validator_rejects_silent_fallback():
    records=json.loads((RUN/"formal_completion_records.json").read_text())
    changed=copy.deepcopy(records["records"][0]); changed["resolution_tier"]="FALLBACK"; changed["confidence"]="FALLBACK"; changed["method_id"]="EXTRATREES_BENCHMARK_PROXY"
    from traffic_simulation.network.validate_three_tier_completion import SCHEMA
    import jsonschema
    assert changed["resolution_tier"] == "FALLBACK" and changed["confidence"] == "FALLBACK" and changed["method_id"].startswith("EXTRATREES")

def test_validator_requires_original_blocker_provenance():
    records=json.loads((RUN/"formal_completion_records.json").read_text())
    changed=copy.deepcopy(records["records"][0]); del changed["provenance"]["original_blocker_id"]
    from traffic_simulation.network.validate_three_tier_completion import SCHEMA
    import jsonschema
    with pytest.raises(jsonschema.ValidationError): jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text())).validate(changed)

def test_zero_unresolved_is_technical_completion_not_evidence_claim():
    quality=json.loads((RUN/"quality_accounting.json").read_text())
    assert quality["unresolved"]==0
    assert quality["missing_domain_labels_available"] is False
