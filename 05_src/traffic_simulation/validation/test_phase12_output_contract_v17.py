from __future__ import annotations

import copy
import hashlib
import json
import subprocess

import pytest
import yaml
import jsonschema

from traffic_simulation.network import execute_v17_phase12_full_population as phase12_runner
from traffic_simulation.network.validate_v17_phase12_output_contract import (
    CONTRACT_PATH,
    Phase12OutputContractError,
    validate_adoption_record,
    validate_output_contract,
)


def contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_fixed_contract_and_adoption_record_pass() -> None:
    result = validate_adoption_record()
    assert result["required_artifact_count"] == 8
    assert result["determinism_artifact_count"] == 5
    assert result["required_run_count"] == 2


def test_artifact_paths_are_unique() -> None:
    value = contract()
    value["artifact_catalog"][1]["path_template"] = value["artifact_catalog"][0][
        "path_template"
    ]
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_required_artifact_cannot_be_omitted() -> None:
    value = contract()
    value["artifact_catalog"] = value["artifact_catalog"][:-1]
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_formal_model_assumption_is_rejected() -> None:
    value = contract()
    value["profiles"]["formal"]["allow_model_assumed"] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_structural_profile_cannot_become_acceptance_eligible() -> None:
    value = contract()
    value["profiles"]["structural"]["acceptance_eligible"] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_cross_unit_simple_sum_is_rejected() -> None:
    value = contract()
    value["population_accounting"]["cross_unit_simple_sum_allowed"] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_upstream_and_permission_simple_sum_is_rejected() -> None:
    value = contract()
    value["population_accounting"][
        "upstream_and_permission_blockers_simple_sum_allowed"
    ] = True
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_determinism_set_must_match_catalog() -> None:
    value = contract()
    value["determinism"]["compare_artifact_ids"] = value["determinism"][
        "compare_artifact_ids"
    ][:-1]
    with pytest.raises(Phase12OutputContractError):
        validate_output_contract(value)


def test_contract_validation_does_not_mutate_input() -> None:
    value = contract()
    before = copy.deepcopy(value)
    validate_output_contract(value)
    assert value == before


def test_main_passes_actual_cli_arguments_to_run_manifest_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = [
        "--container-digest",
        "sha256:" + "a" * 64,
        "--run-id",
        "run_2",
        "--container-image",
        "tokyo-traffic-research-analysis",
    ]
    captured: dict[str, object] = {}

    def fake_execute_run(
        run_id: str,
        *,
        container_image: str,
        container_digest: str,
        arguments: list[str],
    ) -> dict[str, str]:
        captured.update(
            run_id=run_id,
            container_image=container_image,
            container_digest=container_digest,
            arguments=arguments,
        )
        return {"run_id": run_id}

    monkeypatch.setattr(phase12_runner, "execute_run", fake_execute_run)

    assert phase12_runner.main(actual) == 0
    assert captured == {
        "run_id": "run_2",
        "container_image": "tokyo-traffic-research-analysis",
        "container_digest": "sha256:" + "a" * 64,
        "arguments": actual,
    }


@pytest.mark.parametrize(
    "digest",
    [None, "", "local-unpinned", "sha256:abc", "sha256:" + "A" * 64],
)
def test_formal_run_rejects_unpinned_or_malformed_container_digest(
    digest: str | None,
) -> None:
    with pytest.raises(phase12_runner.Phase12ExecutionError):
        phase12_runner._validate_container_identity("research-analysis", digest)


def test_formal_run_accepts_and_normalizes_pinned_container_identity() -> None:
    digest = "sha256:" + "a" * 64
    assert phase12_runner._validate_container_identity(
        "  tokyo-traffic-research-analysis  ", f"  {digest}  "
    ) == ("tokyo-traffic-research-analysis", digest)


def test_each_completion_validator_records_actual_command_exit_log_and_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual_commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        actual_commands.append(command)
        validator_id = command[-1]
        run_id = command[command.index("--run-id") + 1]
        stdout = json.dumps(
            {
                "run_id": run_id,
                "validator_id": validator_id,
                "checks": {"required": 1, "completed": 1, "failed": 0},
                "result": "passed",
            },
            sort_keys=True,
        ) + "\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(phase12_runner.subprocess, "run", fake_run)
    result = phase12_runner._run_completion_validators("run_2")

    executions = result["validator_executions"]
    assert len(executions) == len(phase12_runner.VALIDATOR_IDS) == 8
    assert [item["command"] for item in executions] == actual_commands
    assert [item["validator_id"] for item in executions] == list(phase12_runner.VALIDATOR_IDS)
    for item in executions:
        assert item["exit_code"] == 0
        assert item["command"][-2:] == ["--validator", item["validator_id"]]
        assert item["log_sha256"] == hashlib.sha256(item["log"].encode("utf-8")).hexdigest()
        streams = json.loads(item["log"])
        assert streams["stderr"] == ""
        assert json.loads(streams["stdout"])["validator_id"] == item["validator_id"]


def test_failed_completion_validator_stops_run_and_retains_log_in_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 9, stdout="", stderr="validator failed\n")

    monkeypatch.setattr(phase12_runner.subprocess, "run", fake_run)
    with pytest.raises(phase12_runner.Phase12ExecutionError, match="validator failed"):
        phase12_runner._run_completion_validators("run_1")


def test_run_manifest_schema_requires_validator_execution_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        validator_id = command[-1]
        result = {
            "run_id": "run_1",
            "validator_id": validator_id,
            "checks": {"required": 1, "completed": 1, "failed": 0},
            "result": "passed",
        }
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps(result, sort_keys=True) + "\n", stderr=""
        )

    monkeypatch.setattr(phase12_runner.subprocess, "run", fake_run)
    executions = phase12_runner._run_completion_validators("run_1")["validator_executions"]
    artifact_ids = [
        "structural_full_population",
        "formal_full_population",
        "complete_blocker_inventory",
        "exclusion_manifest",
        "population_accounting",
        "environment_build_manifest",
    ]
    manifest = {
        "schema_version": 17,
        "manifest_id": "test-run-1",
        "contract_id": "OTA_WARD_V17_PHASE12_OUTPUT_CONTRACT",
        "contract_version": "1.0.0",
        "run_id": "run_1",
        "source_commit": "a" * 40,
        "dirty_tree": False,
        "configuration_id": "ota_ward_sumo_network_v17",
        "population_version": "ota_ward_relation_closure_v16",
        "input_hashes": {f"input_{index}": "b" * 64 for index in range(6)},
        "artifacts": [
            {
                "artifact_id": artifact_id,
                "path": f"runs/run_1/{artifact_id}.json",
                "schema": f"schemas/{artifact_id}.json",
                "byte_sha256": "c" * 64,
                "semantic_sha256": None,
            }
            for artifact_id in artifact_ids
        ],
        "validation_results": {
            "schema": "passed",
            "semantic": "passed",
            "population_accounting": "passed",
            "identity_uniqueness": "passed",
        },
        "validator_executions": executions,
        "result": "passed",
        "exit_code": 0,
    }
    schema_path = (
        phase12_runner.REPOSITORY_ROOT
        / "reproducibility/config/traffic_simulation/schemas/phase12_run_manifest_v17.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(manifest)
    without_evidence = copy.deepcopy(manifest)
    del without_evidence["validator_executions"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(without_evidence)


def test_run_result_is_derived_from_individual_validator_results() -> None:
    gate_results = [
        {
            "run_id": "run_1",
            "validator_id": validator_id,
            "checks": {"required": 1, "completed": 1, "failed": 0},
            "result": "passed",
        }
        for validator_id in phase12_runner.VALIDATOR_IDS
    ]
    population = next(
        item for item in gate_results if item["validator_id"] == "population_accounting"
    )
    population["checks"] = {"required": 1, "completed": 0, "failed": 1}
    population["result"] = "failed"

    result = phase12_runner.aggregate_gate_results("run_1", gate_results)

    assert result["result"] == "failed"
    assert result["phase12_run_completion"] == "failed"
    assert result["gates"]["population_accounting"] == "failed"
    assert result["validation_results"]["population_accounting"] == "failed"
