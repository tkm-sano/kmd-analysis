"""Additional preregistered demand bundles without rewriting frozen v1 inputs.

Only the frozen-demand provenance hook changes for new bundles. All common
physical checks still run through Problem.validate. The solver is unchanged.
"""
from dataclasses import dataclass
from pathlib import Path
from .contract import ROOT,read,digest,require,fingerprint


def load_registered_scenario(directory,case):
 from kmd_toc.common.models import Problem,Stop,Vehicle,Depot,Berth,Experiment,Snap
 from kmd_toc.common.od import load_od
 generation=case.get('generation_manifest',{})
 require(isinstance(generation,dict) and generation.get('path') and generation.get('sha256'),'GENERATION_MANIFEST_REQUIRED')
 require(digest(generation['path'])==generation['sha256'],'GENERATION_MANIFEST_HASH_MISMATCH')
 provenance=read(generation['path'])
 require(provenance.get('demand_seed')==case.get('demand_seed') and provenance.get('dataset_id') and provenance.get('candidate_source_hash'),'DEMAND_GENERATION_LINEAGE_REQUIRED')
 frozen=read(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json')
 reference=ROOT/frozen['inputs']['input_root']/'S1/input.json'
 require(digest(reference)==frozen['inputs']['scenarios']['S1']['files']['input.json'],'REFERENCE_DEPOT_HASH_MISMATCH')
 reference_depot=read(reference)['depot']
 @dataclass(frozen=True)
 class RegisteredScenarioProblem(Problem):
  def _validate_frozen(self,conditions):
   expected=conditions['scenarios'][case['scale']]
   require((len(self.stops),len(self.vehicles),len(self.berths))==
       (expected['stops'],expected['vehicles'],expected['berths']),'REGISTERED_SCENARIO_COUNTS')
   require(self.od.metadata['kind']=='osm_osrm' and self.od.metadata.get('table_distances_used') is False and
      self.od.metadata.get('directed') is True,'REGISTERED_ROUTE_REQUIRED')
   from dataclasses import asdict
   require(fingerprint(asdict(self.depot))==fingerprint(reference_depot),'REGISTERED_KEIHIN_DEPOT_REQUIRED')
   require(case.get('generation_manifest'),'REGISTERED_DEMAND_PROVENANCE_REQUIRED')
 p=Path(directory)
 require(p.resolve()==Path(case['input_dir']).resolve(),'FOREIGN_INPUT_DIRECTORY')
 for name,h in case['files'].items():require(digest(p/name)==h,'REGISTERED_INPUT_HASH_MISMATCH')
 data=read(p/'input.json')
 require(set(data)=={'schema_version','stops','vehicles','depot','berths','experiment','od_hash','problem_hash'} and data['schema_version']=='1.0','INPUT_SCHEMA')
 def located(cls,row):
  row=dict(row);s=dict(row.pop('snap'));s['node_ids']=tuple(s['node_ids'])
  return cls(**row,snap=Snap(**s))
 problem=RegisteredScenarioProblem(tuple(located(Stop,s) for s in data['stops']),
    tuple(Vehicle(**v) for v in data['vehicles']),located(Depot,data['depot']),
    tuple(Berth(**b) for b in data['berths']),load_od(p/'od'),Experiment(**data['experiment']))
 require(problem.fingerprint==data['problem_hash'] and problem.od.fingerprint==data['od_hash'],'REGISTERED_PROBLEM_HASH')
 return problem.validate()


def sampling_plan(*,dataset_id,candidate_manifest_hash,scenario_ids,seeds,scales=('S1','S2','S3')):
 """Prepare explicit generation requests, never generate/overwrite data or OD."""
 require(len(scenario_ids)==len(seeds) and len(set(scenario_ids))==len(scenario_ids),'SCENARIO_PLAN_IDENTITIES')
 require(all(type(s) is int and s>=0 for s in seeds),'DEMAND_SEED_REQUIRED')
 require(len(candidate_manifest_hash)==64,'CANDIDATE_MANIFEST_HASH_REQUIRED')
 return {'dataset_id':dataset_id,'candidate_manifest_hash':candidate_manifest_hash,
   'requests':[{'scenario_id':sid,'demand_seed':seed,'scale':scale,
      'required_counts':{'S1':[1000,10,2],'S2':[2000,20,4],'S3':[4000,40,8]}[scale],
      'status':'NEEDS_SEPARATE_DEMAND_AND_ROUTE_BUNDLE_PREPARATION'}
      for sid,seed in zip(scenario_ids,seeds) for scale in scales],
   'runtime_generation':False,'independence':'not established by seed alone; register generation and family relationships'}
