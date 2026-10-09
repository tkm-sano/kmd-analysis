"""Verify immutable runtime snapshots and their historical originals when present."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]

class FrozenRuntimeTests(unittest.TestCase):
    def test_snapshot_integrity(self):
        records = json.loads((ROOT / 'reproducibility/release/FROZEN_RUNTIME_SOURCES.json').read_text())['sources']
        for record in records:
            with self.subTest(path=record['runtime_path']):
                runtime = ROOT / record['runtime_path']
                self.assertFalse(runtime.is_symlink())
                self.assertEqual(runtime.stat().st_size, record['size_bytes'])
                self.assertEqual(hashlib.sha256(runtime.read_bytes()).hexdigest(), record['sha256'])
                original = ROOT / record['original_path']
                if original.exists():
                    self.assertEqual(runtime.read_bytes(), original.read_bytes())

if __name__ == '__main__':
    unittest.main()
