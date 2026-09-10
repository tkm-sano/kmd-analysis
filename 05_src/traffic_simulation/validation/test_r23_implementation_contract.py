"""Unit-level checks for forward R23 instrumentation; no QAOA execution."""

import pytest

pytest.importorskip("qiskit")

from pathlib import Path
import json
import shutil

from traffic_simulation.r23_qaoa_aer.artifact import (
    build_formal_manifest, build_provenance_lineage, source_hashes,
    validate_provenance_lineage,
)
from traffic_simulation.r23_qaoa_aer.qaoa import classify_optimizer_termination, transpiler_metadata
from traffic_simulation.r23_qaoa_aer.schema import (
    R23Input, memory_preflight, PROBABILITY_SUM_TOLERANCE,
)
from traffic_simulation.r23_qaoa_aer.metrics import probability_metrics


def tiny_input():
    return R23Input("tiny", 1, (1,), 0, 3.0, {0: 2.0}, {}, "i" * 64, "q" * 64, 2.0, 1.0, frozenset({(1,)}), frozenset({(-1,)}), frozenset({(1,)}), {0: {0: 0.0, 1: 1.0}, 1: {0: 1.0, 1: 0.0}}, {"ising_global_minimum_energy": 1.0})


def test_boundary_without_optimizer_reason_is_unknown():
    result = classify_optimizer_termination(
        optimizer_success=None, nfev=100, configured_maxiter=100,
        nit=None, configured_objective_cap=300,
    )
    assert result["budget_hit"] is False
    assert result["termination_status"] == "TERMINATION_UNKNOWN"


def test_optimizer_success_is_not_inferred_from_budget():
    result = classify_optimizer_termination(
        optimizer_success=True, nfev=100, configured_maxiter=100,
        nit=None, configured_objective_cap=300,
    )
    assert result["termination_status"] == "CONVERGED"


def test_objective_cap_and_maxiter_use_their_own_api_fields():
    assert classify_optimizer_termination(optimizer_success=None, nfev=300, nit=None, configured_maxiter=100, configured_objective_cap=300)["objective_cap_hit"]
    assert classify_optimizer_termination(optimizer_success=None, nfev=99, nit=100, configured_maxiter=100, configured_objective_cap=300)["maxiter_boundary_reached"]


def test_runtime_contract_is_inclusive_and_not_additive():
    schema = json.loads(Path("reproducibility/config/traffic_simulation/schemas/r23_formal_manifest.schema.json").read_text())
    required = schema["properties"]["runtime_contract"]["required"]
    assert set(required) >= {"T_total", "T_optimizer_total", "T_objective_eval_total", "T_Aer_total", "T_expectation_total", "double_counting_rule"}
    cfg = json.loads(Path("reproducibility/config/traffic_simulation/r23_pilot_configuration/20260910_r23_reduced_pilot_v1.json").read_text())
    contract = build_formal_manifest(repo_root=Path("."), config=cfg, environment={"test_only": True}, run_ids=[], artifact_file_hashes={}, execution_entry_point=Path("05_src/traffic_simulation/r23_qaoa_aer/qaoa.py"))["runtime_contract"]
    assert "inclusive" in contract["T_optimizer_total"]
    assert "sum of all" in contract["T_objective_eval_total"]
    assert "never add" in contract["T_final_evaluation"]
    assert "not summed" in contract["double_counting_rule"]


def test_provenance_lineage_and_source_hashes(tmp_path):
    cfg = json.loads(Path("reproducibility/config/traffic_simulation/r23_pilot_configuration/20260910_r23_reduced_pilot_v1.json").read_text())
    lineage = build_provenance_lineage(Path("."), cfg, execution_entry_point=Path("05_src/traffic_simulation/r23_qaoa_aer/qaoa.py"))
    validate_provenance_lineage(lineage)
    assert lineage["R23"]["source_file_hashes"]["qaoa.py"]
    copied = tmp_path / "repo"
    (copied / "05_src/traffic_simulation/r23_qaoa_aer").mkdir(parents=True)
    for name in ("qaoa.py", "hamiltonian.py", "metrics.py", "schema.py", "artifact.py"):
        shutil.copy2(Path("05_src/traffic_simulation/r23_qaoa_aer") / name, copied / "05_src/traffic_simulation/r23_qaoa_aer" / name)
    original = source_hashes(Path("."))["qaoa.py"]
    (copied / "05_src/traffic_simulation/r23_qaoa_aer/qaoa.py").write_text("# mutation\n" + (copied / "05_src/traffic_simulation/r23_qaoa_aer/qaoa.py").read_text())
    assert source_hashes(copied)["qaoa.py"] != original


def test_formal_manifest_requires_complete_lineage():
    cfg = json.loads(Path("reproducibility/config/traffic_simulation/r23_pilot_configuration/20260910_r23_reduced_pilot_v1.json").read_text())
    manifest = build_formal_manifest(repo_root=Path("."), config=cfg, environment={"test_only": True}, run_ids=[], artifact_file_hashes={}, execution_entry_point=Path("05_src/traffic_simulation/r23_qaoa_aer/qaoa.py"))
    assert set(manifest["lineage"]) == {"R20", "R21", "R22", "R23"}
    with pytest.raises(ValueError):
        validate_provenance_lineage({"R20": {}})


def test_memory_preflight_passes_for_pilot_qubits():
    result = memory_preflight(9, 8.0)
    assert result["statevector_amplitude_count"] == 512
    assert result["status"] == "PASS"


def test_memory_preflight_rejects_over_guard_without_allocation():
    result = memory_preflight(30, 8.0)
    assert result["status"] == "FAIL"


def test_probability_tolerance_and_raw_mass_semantics():
    data = tiny_input()
    metrics = probability_metrics({"0": 0.25, "1": 0.7500000000000007}, data)
    assert metrics["probability_tolerance_contract"]["sum_tolerance"] == PROBABILITY_SUM_TOLERANCE
    assert metrics["probability_tolerance_contract"]["denominator"] == "raw_full_state_probability_mass"
    assert metrics["probability_tolerance_contract"]["renormalization"] is False
    with pytest.raises(ValueError):
        probability_metrics({"0": 0.25, "1": 0.751}, data)
    with pytest.raises(ValueError):
        probability_metrics({"0": -2e-12, "1": 1.0000000000000007}, data)


def test_transpiler_metadata_contract():
    metadata = transpiler_metadata(optimization_level=1, seed_transpiler=17)
    assert metadata == {"optimization_level": 1, "optimization_level_source": "R23Config", "seed_transpiler": 17, "basis_gates": "backend default", "backend_dependent_settings": "backend defaults", "implementation_default_used": True}
