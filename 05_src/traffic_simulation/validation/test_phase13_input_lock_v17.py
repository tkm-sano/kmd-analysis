from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from traffic_simulation.network.validate_v17_phase13_input_lock import (
    DEFAULT_LOCK,
    Phase13InputLockError,
    validate_input_lock,
)


def test_fixed_phase12_publication_is_valid_phase13_input() -> None:
    result = validate_input_lock()
    assert result == {
        "phase13_input_lock": "passed",
        "source_run": "run_1",
        "artifact_count": 7,
        "complete_blocker_inventory": "fixed",
    }


def test_unlocked_input_fails_closed(tmp_path: Path) -> None:
    lock = yaml.safe_load(DEFAULT_LOCK.read_text(encoding="utf-8"))
    changed = deepcopy(lock)
    changed["status"] = "draft"
    path = tmp_path / "input-lock.yml"
    path.write_text(yaml.safe_dump(changed, sort_keys=False), encoding="utf-8")
    with pytest.raises(Phase13InputLockError, match="not fixed"):
        validate_input_lock(path)
