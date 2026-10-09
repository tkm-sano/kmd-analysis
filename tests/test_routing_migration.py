"""Small regression/compatibility checks; never run the production experiment."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from kmd_quantitative.routing import solver, independent

OLD = ROOT / '01_research_design/scenario_evaluation/classical_vrptw_baseline_20261005'


def instance():
    data = json.loads((ROOT / 'notebooks/fixtures/three_customers.json').read_text())
    return {k: np.array(data[k]) for k in ('nodes', 'travel', 'distance', 'partition', 'ready', 'due', 'service', 'demand')}


def legacy(name):
    spec = importlib.util.spec_from_file_location('compat_' + name, OLD / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RoutingMigrationTests(unittest.TestCase):
    def test_source_bytes_and_legacy_links(self):
        freeze = json.loads((OLD / 'CLASSICAL_VRPTW_BASELINE_FREEZE.json').read_text())
        for module in (solver, independent):
            path = Path(module.__file__)
            old = OLD / path.name
            self.assertTrue(old.is_symlink(), 'Compatibility checkout must preserve symlinks')
            self.assertEqual(old.resolve(), path.resolve())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), freeze['code_hashes'][path.name])
            self.assertEqual(old.read_bytes(), path.read_bytes())

    def test_exact_and_independent_schedule(self):
        a = instance()
        route, count = solver.enumerate_exact(a)
        self.assertEqual(route, [0, 1, 2, 3, 0])
        self.assertEqual(count, {'feasible_permutations': 6, 'total_permutations': 6})
        self.assertEqual(str(solver.exact_cost(a, route)), '40')
        totals = independent.validate(a, route)['totals']
        self.assertEqual(totals['road_travel_seconds'], '40')
        self.assertEqual(totals['service_seconds'], '306')
        self.assertEqual(totals['route_duration_seconds'], '346')
        self.assertEqual(independent.exact_dfs(a)[:2], (route, '40'))

    def test_changed_time_window(self):
        a = instance()
        a['due'][2] = 120
        route, _ = solver.enumerate_exact(a)
        self.assertEqual(route, [0, 2, 1, 3, 0])
        self.assertEqual(independent.validate(a, route)['totals']['road_travel_seconds'], '130')

    def test_unavailable_route(self):
        a = instance()
        a['due'][1:] = 0
        route, count = solver.enumerate_exact(a)
        self.assertIsNone(route)
        self.assertEqual(count['feasible_permutations'], 0)
        with self.assertRaises(AssertionError):
            independent.validate(a, [0, 1, 2, 3, 0])

    def test_capacity_is_independently_checked(self):
        a = instance()
        a['demand'][1] = 217
        with self.assertRaises(AssertionError):
            independent.validate(a, [0, 1, 2, 3, 0])

    def test_dual_certificate_validation(self):
        a = instance()
        proof = {'u': ['0'] * 4, 'v': ['0'] * 4}
        self.assertEqual(independent.verify_dual(a, proof, '0')['admitted_arcs'], 12)
        with self.assertRaises(AssertionError):
            independent.verify_dual(a, {'u': ['1000'] * 4, 'v': ['0'] * 4}, '4000')

    def test_equal_cost_tie_break(self):
        a = instance()
        a['travel'][:] = 1
        np.fill_diagonal(a['travel'], 0)
        self.assertEqual(solver.enumerate_exact(a)[0], [0, 1, 2, 3, 0])

    def test_old_imports_have_same_results(self):
        a = instance()
        old_solver, old_validator = legacy('solver'), legacy('independent')
        self.assertEqual(old_solver.enumerate_exact(a), solver.enumerate_exact(a))
        route = [0, 1, 2, 3, 0]
        self.assertEqual(old_validator.validate(a, route), independent.validate(a, route))
        self.assertEqual(old_validator.exact_dfs(a), independent.exact_dfs(a))


if __name__ == '__main__':
    unittest.main(verbosity=2)
