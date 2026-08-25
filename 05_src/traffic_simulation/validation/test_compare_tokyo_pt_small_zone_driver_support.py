import importlib.util
import sys
from pathlib import Path


CALIBRATION = Path(__file__).parents[1] / "calibration"
sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = CALIBRATION / "compare_tokyo_pt_small_zone_driver_support.py"
SPEC = importlib.util.spec_from_file_location("compare_small_zone_support", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_amount_counts_only_positive_assignment_on_selected_edges():
    support = {
        "a": {"route_count": 2, "assigned_amount": 3.5},
        "b": {"route_count": 1, "assigned_amount": 0.0},
    }
    assert MODULE.amount(["a", "b", "missing"], support) == 3.5
