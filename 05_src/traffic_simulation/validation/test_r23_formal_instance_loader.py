from pathlib import Path

import pytest

from traffic_simulation.r23_qaoa_aer.schema import R23SchemaError, load_r22_instance

ROOT = Path(__file__).resolve().parents[3]
FORMAL_R22 = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1/r22"


@pytest.mark.parametrize("instance_id", ["routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"])
def test_formal_r22_instance_resolves_from_per_instance_authority(instance_id):
    data = load_r22_instance(FORMAL_R22 / instance_id, instance_id)
    assert data.instance_id == instance_id
    assert data.n == 4 and data.n_logical == 16
    assert data.lambda_value == 3.0
    assert data.payload["formal_instance_authority"].endswith(f"/r22/{instance_id}")
    assert data.payload["validation"]["status"] == "R22_FORMAL_INSTANCE_PASS"


def test_formal_r22_instances_are_distinct():
    values = [load_r22_instance(FORMAL_R22 / x, x) for x in ("routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05")]
    assert [x.instance_id for x in values] == ["routing_v18_n4_rank01", "routing_v18_n4_rank03", "routing_v18_n4_rank05"]
    assert len({x.ising_coefficient_hash for x in values}) == 3


def test_formal_r22_unknown_id_fails_closed():
    with pytest.raises(R23SchemaError):
        load_r22_instance(FORMAL_R22 / "routing_v18_n4_rank01", "routing_v18_n4_rank99")


def test_formal_r22_hash_mismatch_fails_closed(tmp_path):
    source = FORMAL_R22 / "routing_v18_n4_rank01"
    for name in ("r22_input.json", "validation.json", "manifest.json"):
        (tmp_path / name).write_bytes((source / name).read_bytes())
    (tmp_path / "validation.json").write_text((tmp_path / "validation.json").read_text().replace("R22_FORMAL_INSTANCE_PASS", "CORRUPTED"))
    with pytest.raises(R23SchemaError):
        load_r22_instance(tmp_path, "routing_v18_n4_rank01")
