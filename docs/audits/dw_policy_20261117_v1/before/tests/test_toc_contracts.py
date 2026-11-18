"""Toy contract tests only; no study data or scientific experiments."""

from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kmd_toc import HoldError, allocate_customers, compare_objectives, load_study, require_ready


class ToCContractsTests(unittest.TestCase):
    def load_modified(self, change):
        data = json.loads((ROOT / "configs/toc_delivery/study.json").read_text())
        change(data)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "study.json"
            path.write_text(json.dumps(data))
            return load_study(path)

    def test_adopted_scope_and_hold_gate(self):
        study = load_study(ROOT / "configs/toc_delivery/study.json")
        self.assertEqual(study["scope"]["vehicle_label"], "配送車両")
        self.assertEqual([x["N"] for x in study["cases"]], [1000, 2000, 4000])
        self.assertTrue(all(x is None for x in study["operations"].values()))
        with self.assertRaises(HoldError):
            require_ready(study)

    def test_unknown_fields_at_every_depth_are_rejected(self):
        for target in [(), ("scope",), ("operations",), ("demand", "population"),
                       ("demand", "geography"), ("comparisons",), ("metrics",), ("figures",)]:
            def change(data):
                for key in target:
                    data = data[key]
                data["battery_capacity"] = 42
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.load_modified(change)

    def test_case_scope_and_metric_drift_are_rejected(self):
        changes = [lambda d: d["cases"][0].update(N=True),
                   lambda d: d["cases"][0].update(N=3000),
                   lambda d: d["scope"].update(vehicle_label="EV"),
                   lambda d: d["metrics"].update(T="solver_only_seconds"),
                   lambda d: d["provisional_parameters"][0].update(name="charging_time"),
                   lambda d: d["operations"].update(loading_duration_s=-1)]
        for change in changes:
            with self.assertRaises(ValueError):
                self.load_modified(change)

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"scope": {}, "scope": {}}')
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_study(path)

    def test_allocation_exact_total_nonnegative_and_quota(self):
        populations = {f"r{i:02}": i for i in range(56)}
        for total in [0, 1, 17, 1000, 2000, 4000]:
            result = allocate_customers(populations, total)
            self.assertEqual(sum(result.values()), total)
            self.assertEqual(result["r00"], 0)
            for key, value in result.items():
                quota = Fraction(total * populations[key], sum(populations.values()))
                self.assertGreaterEqual(value, quota.numerator // quota.denominator)
                self.assertLessEqual(value, -(-quota.numerator // quota.denominator))

    def test_allocation_ties_fractional_values_and_input_order(self):
        self.assertEqual(allocate_customers({"b": 1, "a": 1}, 1), {"a": 1, "b": 0})
        self.assertEqual(allocate_customers({"b": "0.1", "a": "0.3"}, 4), {"a": 3, "b": 1})
        p = {"a": 7, "b": 3, "c": 2}
        self.assertEqual(allocate_customers(p, 11), allocate_customers(dict(reversed(list(p.items()))), 11))

    def test_allocation_invalid_inputs_fail(self):
        for population in [{}, {"a": 0}, {"a": -1}, {"a": True}, {"a": float("nan")},
                           {"a": float("inf")}, {"": 1}]:
            with self.assertRaises(ValueError):
                allocate_customers(population, 10)
        for total in [-1, True, 1.5]:
            with self.assertRaises(ValueError):
                allocate_customers({"a": 1}, total)

    def test_three_objectives_and_zero_baseline(self):
        self.assertEqual(compare_objectives([1, 0, 3], [2, 0, 3]), {
            "delta": [-1, 0, 0], "relative_delta": [-0.5, None, 0.0], "relation": "DOMINATES"})
        self.assertEqual(compare_objectives([1, 1, 4], [2, 2, 3])["relation"], "INCOMPARABLE")
        self.assertEqual(compare_objectives([2, 0, 3], [1, 0, 3])["relation"], "DOMINATED")
        self.assertEqual(compare_objectives([1, 0, 3], [1, 0, 3])["relation"], "EQUAL")
        for vector in [[1, None, 3], [1, float("nan"), 3], [1, -1, 3], [1, 2], [True, 2, 3]]:
            with self.assertRaises(ValueError):
                compare_objectives(vector, [1, 2, 3])

    def test_import_does_not_load_historical_or_solver_modules(self):
        script = ("import sys; sys.path.insert(0, 'src'); import kmd_toc; "
                  "assert not any(x.startswith(('kmd_quantitative', 'qiskit', 'ortools')) for x in sys.modules)")
        subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
