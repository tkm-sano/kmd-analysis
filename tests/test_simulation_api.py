"""Saved input projection and handoff only; never invoke SUMO or production energy."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,sys,tempfile,unittest
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kmd_quantitative.simulation import trajectory_io as api
class SimulationTests(unittest.TestCase):
 def test_original_projection(self):
  path=ROOT/'notebooks/fixtures/speed.csv';t,v=api.read_dc_input(path)
  df=pd.read_csv(path,usecols=['timestamp_s','speed_m_s'])
  np.testing.assert_array_equal(t,df.timestamp_s.to_numpy());np.testing.assert_array_equal(v,df.speed_m_s.to_numpy())
  x=json.loads((ROOT/'notebooks/fixtures/speed.json').read_text())
  np.testing.assert_array_equal(t,x['time_s']);np.testing.assert_array_equal(v,x['speed_m_s'])
 def test_gzip_extra_columns(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'trajectory.csv.gz'
   with gzip.open(p,'wt') as f:f.write('vehicle_id,timestamp_s,speed_m_s,position_m\nSYN,10,2,7\nSYN,11,3,1\n')
   t,v=api.read_dc_input(p);np.testing.assert_array_equal(t,[10,11]);np.testing.assert_array_equal(v,[2,3])
 def test_malformed_not_repaired(self):
  bad=['timestamp_s,speed_m_s\n0,1\n2,1\n','timestamp_s,speed_m_s\n1,1\n0,1\n','timestamp_s,speed_m_s\n0,1\n0,1\n','timestamp_s,speed_m_s\n0,-1\n1,1\n','timestamp_s,speed_m_s\n0,nan\n1,1\n','timestamp_s,speed_m_s\ninf,1\n1,1\n','timestamp_s,speed_m_s\n0,text\n1,1\n','timestamp_s,speed_m_s\n0,1\n','timestamp_s,speed_m_s\n','time_s,speed_m_s\n0,1\n1,1\n']
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.csv'
   for text in bad:
    p.write_text(text);h=hashlib.sha256(p.read_bytes()).hexdigest()
    with self.subTest(text=text),self.assertRaises(ValueError):api.read_dc_input(p)
    self.assertEqual(h,hashlib.sha256(p.read_bytes()).hexdigest())
 def test_hash_and_metadata(self):
  p=ROOT/'notebooks/fixtures/speed.csv';h=hashlib.sha256(p.read_bytes()).hexdigest()
  api.read_dc_input(p,expected_sha256=h,metadata={'sample_count':4,'integration_interval_count':3,'first_sample_s':0,'last_sample_s':3})
  with self.assertRaises(ValueError):api.read_dc_input(p,expected_sha256='0'*64)
  with self.assertRaises(ValueError):api.read_dc_input(p,metadata={'sample_count':5})
 def test_controlled_dc_exact_handoff(self):
  p=ROOT/'05_src/literature_analysis/run_full_controlled_dc.py';s=importlib.util.spec_from_file_location('phase4_dc',p);dc=importlib.util.module_from_spec(s);s.loader.exec_module(dc)
  m=json.loads((ROOT/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text());old=json.loads((ROOT/'notebooks/fixtures/speed.json').read_text());t,v=api.read_dc_input(ROOT/'notebooks/fixtures/speed.csv')
  for stage in m['stage_inputs']:
   for pressure in (4.5,2.6):
    out,arr=dc.evaluate(t,v,m,pressure,stage);ref,ra=dc.evaluate(np.array(old['time_s']),np.array(old['speed_m_s']),m,pressure,stage)
    self.assertEqual(out,ref)
    for k in arr:np.testing.assert_array_equal(arr[k],ra[k])
    self.assertEqual(out['observed_distance_m'],30);dc.scalar_check(t,v,m,pressure,stage,out)
 def test_guard_preserves_array_identity(self):
  t=np.array([4.,5.]);v=np.array([0.,1.]);a,b=api.validate_dc_input(t,v);self.assertIs(a,t);self.assertIs(b,v)
  with self.assertRaises(ValueError):api.validate_dc_input(t,np.array([1.]))
if __name__=='__main__':unittest.main()
