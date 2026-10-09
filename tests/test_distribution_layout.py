"""Phase7 I/O layout/copy contracts; no new scientific calculations."""
from pathlib import Path
import csv,hashlib,json,sys,tempfile,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'notebooks'))
import adapters
from kmd_quantitative.analysis.result_io import artifacts
from kmd_quantitative.analysis import method_battery
class DistributionTests(unittest.TestCase):
 def test_copies(self):
  record=json.loads((R/'data/examples/PROVENANCE.json').read_text())
  self.assertEqual(len(record['copies']),3)
  for r in record['copies']:
   self.assertEqual((R/r['path']).read_bytes(),(R/r['source_path']).read_bytes())
   self.assertEqual(hashlib.sha256((R/r['path']).read_bytes()).hexdigest(),r['sha256'])
   self.assertEqual(r['sha256'],r['source_sha256'])
 def test_input_config(self):
  for k in ['routing_fixture','trajectory_fixture','expected_energy_fixture','battery_authority','results_index']:
   self.assertTrue(adapters.example_input(k).is_file())
  self.assertEqual(adapters.instance()['travel'].shape,(4,4))
 def test_missing_input_no_fallback(self):
  with patch.object(adapters,'read_json',return_value={'routing_fixture':'data/examples/missing.json'}):
   with self.assertRaises(ValueError):adapters.instance()
  with patch.object(adapters,'read_json',return_value={'routing_fixture':'../forbidden.json'}):
   with self.assertRaises(ValueError):adapters.instance()
 def test_result_index_and_explicit_root(self):
  idx=json.loads((R/'results/indexes/CANONICAL_RESULTS.json').read_text())
  self.assertEqual(idx['artifacts'],artifacts())
  self.assertEqual(method_battery.freeze(root=R),method_battery.freeze())
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError):method_battery.freeze(root=d)
 def test_config_references(self):
  with (R/'configs/CANONICAL_CONFIG_INDEX.csv').open() as f:rows=list(csv.DictReader(f))
  self.assertEqual(len(rows),19)
  for r in rows:
   self.assertEqual(r['reference_type'],'ORIGINAL_REFERENCE')
   self.assertFalse(Path(r['source_path']).is_absolute())
   # Full-science references are optional in the minimal runtime closure.
   p=R/r['source_path']
   if p.is_file():self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r['sha256'])
   self.assertEqual(r['distribution_status'],'RIGHTS_PENDING')
 def test_distribution_manifest(self):
  m=json.loads((R/'reproducibility/release/GITHUB_DISTRIBUTION_MANIFEST.json').read_text())
  self.assertEqual(m['approved_for_publication_count'],0)
  self.assertEqual(m['publication_status'],'BLOCKED_RIGHTS_PENDING')
  self.assertEqual(len(m['files']),len({r['distribution_path'] for r in m['files']}))
  for r in m['files']:
   p=R/r['distribution_path']
   if p.is_file():self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r['sha256'])
  self.assertTrue(all((R/p).is_file() for p in m['minimal_runtime_files']))
if __name__=='__main__':unittest.main()
