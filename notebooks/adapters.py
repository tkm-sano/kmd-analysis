"""I/O/import adapters only. Scientific expressions come from hash-pinned original ASTs."""
from pathlib import Path
import ast, hashlib, importlib.util, json, math, sys
from decimal import Decimal as D
from itertools import combinations
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
S='01_research_design/scenario_evaluation/'
L='05_src/literature_analysis/'
Q='05_src/traffic_simulation/'
def verified_path(relative):
 p=ROOT/relative
 manifest=json.loads((ROOT/'notebooks/fixtures/dependencies.json').read_text())
 if relative not in manifest:raise ValueError('Unregistered dependency: '+relative)
 if not p.is_file():raise FileNotFoundError('Required repository-relative file missing: '+relative)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest[relative]['sha256']:raise ValueError('Hash mismatch: '+relative)
 return p

def load_module(relative,name):
 p=verified_path(relative);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def read_json(relative):return json.loads(verified_path(relative).read_text())
def read_csv(relative):
 import pandas as pd
 return pd.read_csv(verified_path(relative))
def instance():
 import numpy as np
 f=json.loads(example_input('routing_fixture').read_text())
 a={k:np.array(f[k]) for k in ['nodes','travel','distance','partition','ready','due','service','demand']}
 if a['travel'].shape!=(4,4) or not np.isfinite(a['travel']).all() or (a['travel']<0).any():raise ValueError('Expected finite nonnegative 4x4 travel seconds')
 return a

def candidate_functions():
 # Public src API delegates to unchanged V2 function ASTs, not a second PUBO.
 verified_path('src/kmd_quantitative/quantum/protocol_v2/science.py')
 module=load_module('src/kmd_quantitative/quantum/builder.py','nb_candidate_builder')
 return {name:getattr(module,name) for name in module.__all__}

def formal_quantum_api():
 verified_path('src/kmd_quantitative/quantum/protocol_v2/science.py')
 for path in ['src/kmd_quantitative/quantum/formal.py','src/kmd_quantitative/quantum/builder.py','src/kmd_quantitative/routing/independent.py']:
  verified_path(path)
 sys.path.insert(0,str(ROOT/'src'))
 from kmd_quantitative.quantum import formal
 return formal

def canonical_final_selection(routes):
 return formal_quantum_api().select_final_route(routes)

def battery_api():
 for p in ['src/kmd_quantitative/battery/mass.py','src/kmd_quantitative/battery/scenarios.py','src/kmd_quantitative/battery/frozen_sources/review_pack_specific_energy.py','01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json']:
  verified_path(p)
 sys.path.insert(0,str(ROOT/'src'))
 from kmd_quantitative.battery import mass, scenarios
 return mass, scenarios

def official_mass_stages():
 return battery_api()[0].official_mass_stages()

def mass_at_specific_energy(selected):
 return battery_api()[0].mass_at_specific_energy(selected)

def energy_api():
 for p in ['src/kmd_quantitative/energy/controlled_dc.py','src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py']:
  verified_path(p)
 sys.path.insert(0,str(ROOT/'src'))
 from kmd_quantitative.energy import controlled_dc
 return controlled_dc


def simulation_api():
 # I/O only: leave mass and Controlled-DC calculations at their original sources.
 for p in ['src/kmd_quantitative/simulation/trajectory_io.py', 'src/kmd_quantitative/simulation/frozen_sources/apply_r0_method_battery.py']:
  verified_path(p)
 sys.path.insert(0,str(ROOT/'src'))
 from kmd_quantitative.simulation import trajectory_io
 return trajectory_io


def analysis_api():
 for name in ['__init__.py','result_io.py','method_battery.py','scale_analysis.py']:
  verified_path('src/kmd_quantitative/analysis/'+name)
 sys.path.insert(0,str(ROOT/'src'))
 from kmd_quantitative.analysis import method_battery, scale_analysis
 return method_battery, scale_analysis


def example_input(key):
 config=read_json('configs/examples/NOTEBOOK_INPUTS.json')
 relative=config[key]
 if not isinstance(relative,str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
  raise ValueError('Example input must be repository-relative: '+key)
 return verified_path(relative)
