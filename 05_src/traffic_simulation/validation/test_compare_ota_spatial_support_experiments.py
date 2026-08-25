import importlib.util
import sys
from pathlib import Path


CALIBRATION = Path(__file__).parents[1] / "calibration"
sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = CALIBRATION / "compare_ota_spatial_support_experiments.py"
SPEC = importlib.util.spec_from_file_location("compare_spatial_support", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_experiment_order_is_fixed_and_ends_with_combined_general_improvement():
    assert MODULE.EXPERIMENTS[0] == "baseline"
    assert MODULE.EXPERIMENTS[-1] == "e7_stratified_16sector_paths20_maxalt20"
